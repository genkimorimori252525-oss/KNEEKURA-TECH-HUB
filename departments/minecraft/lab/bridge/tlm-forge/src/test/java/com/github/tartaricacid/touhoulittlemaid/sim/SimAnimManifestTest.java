package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.client.SimAnimManifest;
import com.github.tartaricacid.touhoulittlemaid.sim.client.SimPoseCodec;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * {@link SimAnimManifest} (パック解決 / アニメ列挙 / {@code .anims.json} 往復) と、
 * {@code SimAnimSweep} が使う「デデュープしない逐次追記」経路でも
 * {@code sum(lens)*stride*4 == bin バイト数} が成り立つことを検証する (quick 260819-o9l)。
 *
 * <p>{@link SimAnimManifest} は {@link SimPoseCodec} と同じく<b>Minecraft のクラスを一切
 * import しない</b>ので、通常の JUnit でそのまま回る —— このテストが green になること自体が
 * 「Minecraft を起動せずに検証できる」ことの証明になる。
 */
public class SimAnimManifestTest {

    @Rule
    public TemporaryFolder tmp = new TemporaryFolder();

    /** {@code SimVertexRecorder.STRIDE} と同じ値 (MC を import しないので写している)。 */
    private static final int STRIDE = 11;

    // =========================================================================
    // パック解決
    // =========================================================================

    @Test
    public void resolvePackRootFindsPlainNamedDirectory() throws IOException {
        Path custom = tmp.newFolder("custom").toPath();
        Path pack = Files.createDirectories(custom.resolve("「博丽灵梦」2"));
        Files.writeString(pack.resolve("ysm.json"), "{}", StandardCharsets.UTF_8);

        Path found = SimAnimManifest.resolvePackRoot(custom, "「博丽灵梦」2");
        assertNotNull("素名ディレクトリを見つける", found);
        assertEquals(pack.toAbsolutePath(), found.toAbsolutePath());
    }

    @Test
    public void resolvePackRootFallsBackToYsmSuffixedDirectory() throws IOException {
        Path custom = tmp.newFolder("custom2").toPath();
        // 素名ディレクトリは作らない。拡張子つきディレクトリ形だけ用意する。
        Path pack = Files.createDirectories(custom.resolve("「博丽灵梦」2.ysm"));
        Files.writeString(pack.resolve("ysm.json"), "{}", StandardCharsets.UTF_8);

        Path found = SimAnimManifest.resolvePackRoot(custom, "「博丽灵梦」2");
        assertNotNull("拡張子つきディレクトリ形へ落ちる", found);
        assertEquals(pack.toAbsolutePath(), found.toAbsolutePath());
    }

    @Test
    public void resolvePackRootReturnsNullWhenNeitherCandidateHasYsmJson() throws IOException {
        Path custom = tmp.newFolder("custom3").toPath();
        // 名前だけ一致する空ディレクトリを置く —— ysm.json が無いので掴んではいけない。
        Files.createDirectories(custom.resolve("存在しないid"));

        assertNull(SimAnimManifest.resolvePackRoot(custom, "存在しないid"));
    }

    // =========================================================================
    // アニメ列挙
    // =========================================================================

    @Test
    public void listAnimationsDedupesAcrossFilesAndSorts() throws IOException {
        Path pack = twoFilePack("pack-ok");

        List<String> names = SimAnimManifest.listAnimations(pack);

        // main: zulu / alpha / shared, extra: shared / mike -> 重複 shared は 1 本に潰れる
        assertEquals(Arrays.asList("alpha", "mike", "shared", "zulu"), names);

        List<String> sorted = new ArrayList<>(names);
        sorted.sort(String::compareTo);
        assertEquals("アルファベット順に並んでいる", sorted, names);
    }

    @Test
    public void listAnimationLengthsReadsDeclaredAnimationLength() throws IOException {
        Path pack = twoFilePack("pack-len");

        Map<String, Double> lengths = SimAnimManifest.listAnimationLengths(pack);

        assertEquals(3.75, lengths.get("zulu"), 1.0e-9);
        assertEquals("animation_length が無いものは 0.0", 0.0, lengths.get("alpha"), 1.0e-9);
    }

    @Test
    public void listAnimationsThrowsWhenYsmJsonMissing() throws IOException {
        Path pack = tmp.newFolder("pack-no-index").toPath();
        try {
            SimAnimManifest.listAnimations(pack);
            fail("ysm.json が無いのに例外が出なかった (黙って空リストを返してはならない)");
        } catch (IOException e) {
            assertTrue("メッセージに ysm.json のパスを含む: " + e.getMessage(),
                    e.getMessage().contains("ysm.json"));
        }
    }

    @Test
    public void listAnimationsThrowsWhenReferencedAnimationFileMissing() throws IOException {
        Path pack = tmp.newFolder("pack-missing-anim").toPath();
        Files.writeString(pack.resolve("ysm.json"),
                "{\"files\":{\"player\":{\"animation\":{"
                        + "\"main\":\"animations/main.animation.json\"}}}}",
                StandardCharsets.UTF_8);
        // animations/main.animation.json をわざと作らない

        try {
            SimAnimManifest.listAnimations(pack);
            fail("参照先が無いのに例外が出なかった (途中まで読んだ結果を返してはならない)");
        } catch (IOException e) {
            assertTrue("メッセージに欠けているファイル名を含む: " + e.getMessage(),
                    e.getMessage().contains("main.animation.json"));
        }
    }

    // =========================================================================
    // .anims.json 往復
    // =========================================================================

    @Test
    public void animsCompanionRoundTripsExactly() throws IOException {
        Path out = tmp.newFolder("anims").toPath().resolve("nested").resolve("20260819.anims.json");
        List<SimAnimManifest.AnimRange> ranges = Arrays.asList(
                new SimAnimManifest.AnimRange("extra95", 0, 19, 3.75),
                // 1 フレームだけの範囲 (from == to)
                new SimAnimManifest.AnimRange("hold_mainhand:slashblade", 20, 20, 0.0),
                new SimAnimManifest.AnimRange("extra43", 21, 60, 1.5));

        SimAnimManifest.writeAnimsCompanion(out, ranges);
        List<SimAnimManifest.AnimRange> back = SimAnimManifest.readAnimsCompanion(out);

        assertEquals(ranges.size(), back.size());
        for (int i = 0; i < ranges.size(); i++) {
            SimAnimManifest.AnimRange a = ranges.get(i);
            SimAnimManifest.AnimRange b = back.get(i);
            assertEquals(a.anim(), b.anim());
            assertEquals(a.from(), b.from());
            assertEquals(a.to(), b.to());
            assertEquals(a.length(), b.length(), 1.0e-9);
        }
    }

    // =========================================================================
    // デデュープなしの逐次追記 (sweep 経路の不変条件)
    // =========================================================================

    /**
     * {@code SimAnimSweep} と同じ「重複判定を経由せず {@code appendFrame} を毎 tick 呼ぶ」
     * 経路を再現し、(1) 同一内容でも 1 本へ潰れないこと、(2) それでも
     * {@code sum(lens) * stride * 4 == bin バイト数} が厳密に成り立つことを示す。
     */
    @Test
    public void sequentialAppendWithoutDedupeKeepsEveryFrameAndBinSizeMatches() throws IOException {
        Path dir = tmp.newFolder("sweep").toPath();
        Path bin = dir.resolve("20260819.pose.bin");
        Path json = dir.resolve("20260819.pose.json");

        final int vertsPerFrame = 3;
        final int frames = 20;
        float[] one = new float[vertsPerFrame * STRIDE];
        for (int i = 0; i < one.length; i++) {
            one[i] = i * 0.5F;
        }
        // 同一内容 —— デデュープする収集器なら 1 本へ潰すはずの入力であることを先に固定する。
        assertTrue("入力は同一姿勢とみなされる", SimPoseCodec.same(one, one.clone()));

        int[] lens = new int[frames];
        int[] slots = new int[frames];
        int[][] glens = new int[frames][];
        int[][] gtex = new int[frames][];
        for (int f = 0; f < frames; f++) {
            SimPoseCodec.appendFrame(bin, one);
            lens[f] = vertsPerFrame;
            slots[f] = f;
            glens[f] = new int[]{vertsPerFrame};
            gtex[f] = new int[]{0};
        }

        assertEquals("デデュープしないので 20 フレームのまま (1 本へ潰れない)", frames, lens.length);

        long sumLens = 0L;
        for (int l : lens) {
            sumLens += l;
        }
        assertEquals("bin バイト数 == sum(lens) * stride * 4",
                sumLens * STRIDE * Float.BYTES, Files.size(bin));

        // 索引としても整合する (writeIndex は groups と lens の不整合を IOException で拒否する)。
        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 0L, 7, "touhou_little_maid:reimu", "tex", STRIDE, vertsPerFrame, 0,
                true, frames, bin.getFileName().toString());
        SimPoseCodec.writeIndex(json, header, slots, lens,
                new SimPoseCodec.Groups(glens, gtex, new String[]{"tex"}));

        SimPoseCodec.Index index = SimPoseCodec.readIndex(json);
        assertEquals(frames, index.header().frames());
        assertNotNull("lens が書かれている", index.lens());
        assertEquals("lens.length == frames", frames, index.lens().length);
    }

    // =========================================================================
    // fixture
    // =========================================================================

    /**
     * {@code files.player.animation} に 2 エントリを持ち、片方のキーが重複しているパックを作る。
     */
    private Path twoFilePack(String name) throws IOException {
        Path pack = tmp.newFolder(name).toPath();
        Path animDir = Files.createDirectories(pack.resolve("animations"));
        Files.writeString(pack.resolve("ysm.json"),
                "{\"files\":{\"player\":{\"animation\":{"
                        + "\"main\":\"animations/main.animation.json\","
                        + "\"extra\":\"animations/extra.animation.json\"}}}}",
                StandardCharsets.UTF_8);
        Files.writeString(animDir.resolve("main.animation.json"),
                "{\"format_version\":\"1.8.0\",\"animations\":{"
                        + "\"zulu\":{\"animation_length\":3.75},"
                        + "\"alpha\":{},"
                        + "\"shared\":{\"animation_length\":1.0}}}",
                StandardCharsets.UTF_8);
        Files.writeString(animDir.resolve("extra.animation.json"),
                "{\"format_version\":\"1.8.0\",\"animations\":{"
                        + "\"shared\":{\"animation_length\":2.0},"
                        + "\"mike\":{\"animation_length\":0.5}}}",
                StandardCharsets.UTF_8);
        return pack;
    }
}
