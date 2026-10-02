package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.client.SimPoseCodec;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotSame;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * {@link SimPoseCodec} の 4 系統 (素通し / デデュープ / 上限 / 往復) を検証する。
 *
 * <p>{@link SimPoseCodec} は Minecraft のクラスを一切 import しないので、通常の JUnit で
 * そのまま回る —— このテストが green になること自体が「MC を起動せずに使える」の証明になる
 * (MC のクラス初期化が要るコードが混ざっていればテストが落ちる、09-01-PLAN の acceptance)。
 */
public class SimPoseCodecTest {

    @Rule
    public TemporaryFolder tmp = new TemporaryFolder();

    // =========================================================================
    // 素通し保証 (D-01 の insurance — 既定では何も変えないことを機械で守る)
    // =========================================================================

    @Test
    public void quantizeDigitsZeroPassesThroughExactly() {
        float[] v = {1.23456F, -9.87654F, 0.0F, 12345.6789F};
        float[] out = SimPoseCodec.quantize(v, 0);
        assertArrayEquals("digits<=0 は入力と要素が完全一致する配列を返す", v, out, 0.0F);
    }

    @Test
    public void quantizeNegativeDigitsAlsoPassesThrough() {
        float[] v = {3.14159F};
        float[] out = SimPoseCodec.quantize(v, -1);
        assertArrayEquals(v, out, 0.0F);
    }

    @Test
    public void quantizeRoundsToRequestedDigits() {
        float[] v = {1.23456F};
        float[] out = SimPoseCodec.quantize(v, 2);
        assertEquals(1.23F, out[0], 1.0e-6F);
    }

    @Test
    public void quantizeHandlesNegativeZeroAndLargeValues() {
        float[] v = {-1.239F, 0.0F, 12345.6789F};
        float[] out = SimPoseCodec.quantize(v, 2);
        assertEquals("負値でも桁が守られる", -1.24F, out[0], 1.0e-4F);
        assertEquals("0 は 0 のまま", 0.0F, out[1], 1.0e-6F);
        assertEquals("大きな値でも桁が守られる", 12345.68F, out[2], 1.0e-2F);
    }

    // =========================================================================
    // デデュープ
    // =========================================================================

    @Test
    public void slotForReturnsSameSlotForIdenticalFrame() {
        List<float[]> frames = new ArrayList<>();
        int a = SimPoseCodec.slotFor(frames, new float[]{1F, 2F, 3F}, 96);
        int b = SimPoseCodec.slotFor(frames, new float[]{1F, 2F, 3F}, 96);
        assertEquals("同じ配列は同じ slot になる", a, b);
        assertEquals(1, frames.size());
    }

    @Test
    public void slotForReturnsNewSlotWhenDifferenceExceedsEpsilon() {
        List<float[]> frames = new ArrayList<>();
        int a = SimPoseCodec.slotFor(frames, new float[]{1.0F}, 96);
        int b = SimPoseCodec.slotFor(frames, new float[]{1.0002F}, 96); // 差 2e-4 > 1e-4
        assertNotEquals("要素差が 1.0e-4 を超えれば新しい slot になる", a, b);
        assertEquals(2, frames.size());
    }

    @Test
    public void slotForReturnsSameSlotWhenDifferenceUnderEpsilon() {
        List<float[]> frames = new ArrayList<>();
        int a = SimPoseCodec.slotFor(frames, new float[]{1.0F}, 96);
        int b = SimPoseCodec.slotFor(frames, new float[]{1.00005F}, 96); // 差 5e-5 < 1e-4
        assertEquals("1.0e-4 未満の差なら同じ slot になる", a, b);
        assertEquals(1, frames.size());
    }

    @Test
    public void slotForReturnsNewSlotWhenLengthDiffers() {
        List<float[]> frames = new ArrayList<>();
        int a = SimPoseCodec.slotFor(frames, new float[]{1F, 2F}, 96);
        int b = SimPoseCodec.slotFor(frames, new float[]{1F, 2F, 3F}, 96);
        assertNotEquals("長さが違えば必ず新しい slot になる", a, b);
        assertEquals(2, frames.size());
    }

    // =========================================================================
    // 上限
    // =========================================================================

    @Test
    public void slotForReturnsMinusOneAtCapWithoutGrowingFrameList() {
        List<float[]> frames = new ArrayList<>();
        SimPoseCodec.slotFor(frames, new float[]{1F}, 2);
        SimPoseCodec.slotFor(frames, new float[]{2F}, 2);
        assertEquals(2, frames.size());

        int r = SimPoseCodec.slotFor(frames, new float[]{3F}, 2);
        assertEquals("maxFrames 到達後の新規フレームは -1", -1, r);
        assertEquals("上限到達後は既存フレームのリストを伸ばさない", 2, frames.size());
    }

    // =========================================================================
    // 末尾の未記録 tick の切り落とし (上限後も run を続けるための前提)
    // =========================================================================

    @Test
    public void trimDropsOnlyTheTrailingUnrecordedTicks() {
        List<Integer> slots = new ArrayList<>(Arrays.asList(0, -1, 1, 2, -1, -1, -1));

        assertEquals("末尾の -1 は3つ", 3, SimPoseCodec.trimTrailingUnrecorded(slots));
        assertEquals("範囲は最後に録れた tick で終わる", Arrays.asList(0, -1, 1, 2), slots);
    }

    @Test
    public void trimKeepsAListThatAlreadyEndsOnARecordedTick() {
        List<Integer> slots = new ArrayList<>(Arrays.asList(-1, 0, 1));

        assertEquals(0, SimPoseCodec.trimTrailingUnrecorded(slots));
        assertEquals("先頭の穴は落とさない (backfill 前提の既存挙動)", Arrays.asList(-1, 0, 1), slots);
    }

    @Test
    public void trimEmptiesAListThatNeverRecordedAnything() {
        List<Integer> slots = new ArrayList<>(Arrays.asList(-1, -1));

        assertEquals(2, SimPoseCodec.trimTrailingUnrecorded(slots));
        assertTrue("1枚も録れていない run は範囲ゼロ", slots.isEmpty());
        assertEquals(0, SimPoseCodec.trimTrailingUnrecorded(slots));
    }

    // =========================================================================
    // 往復
    // =========================================================================

    @Test
    public void roundTripThroughDiskPreservesHeaderSlotsAndFrames() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260817-000000.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260817-000000.pose.bin");

        float[] f0 = {0.1F, 0.2F, 0.3F};
        float[] f1 = {1.1F, 1.2F, 1.3F};
        float[] f2 = {2.1F, 2.2F, 2.3F};
        SimPoseCodec.appendFrame(bin, f0);
        SimPoseCodec.appendFrame(bin, f1);
        SimPoseCodec.appendFrame(bin, f2);

        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu",
                "touhou_little_maid:textures/entity/reimu.png",
                3, 1, 0, true, 3, bin.getFileName().toString());
        int[] slots = {0, 0, 1, -1, 2};
        SimPoseCodec.writeIndex(json, header, slots);

        SimPoseCodec.Index idx = SimPoseCodec.readIndex(json);
        assertEquals("Header の全フィールドが一致する", header, idx.header());
        assertArrayEquals("slots 配列の長さと中身が一致する", slots, idx.slots());

        List<float[]> frames = SimPoseCodec.readFrames(bin, 3, 3);
        assertEquals(3, frames.size());
        assertArrayEquals(f0, frames.get(0), 1.0e-6F);
        assertArrayEquals(f1, frames.get(1), 1.0e-6F);
        assertArrayEquals(f2, frames.get(2), 1.0e-6F);
    }

    // =========================================================================
    // 可変長フレーム (lens) — quick 260818-6cj: フレームごとに頂点数が違うトレースの分割
    // =========================================================================

    @Test
    public void variableLengthFramesRoundTripThroughLens() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260818-000000.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260818-000000.pose.bin");

        int stride = 3;
        float[] f0 = {0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F}; // 2 頂点
        float[] f1 = {1.1F, 1.2F, 1.3F, 1.4F, 1.5F, 1.6F, 1.7F, 1.8F, 1.9F}; // 3 頂点
        float[] f2 = {2.1F, 2.2F, 2.3F}; // 1 頂点
        SimPoseCodec.appendFrame(bin, f0);
        SimPoseCodec.appendFrame(bin, f1);
        SimPoseCodec.appendFrame(bin, f2);

        int[] lens = {2, 3, 1};
        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu",
                "touhou_little_maid:textures/entity/reimu.png",
                stride, 2, 0, true, 3, bin.getFileName().toString());
        int[] slots = {0, 1, 2};
        SimPoseCodec.writeIndex(json, header, slots, lens);

        SimPoseCodec.Index idx = SimPoseCodec.readIndex(json);
        assertArrayEquals("lens が書いた順のまま読み戻る", lens, idx.lens());

        List<float[]> framesOut = SimPoseCodec.readFrames(bin, lens, stride);
        assertEquals("可変長 readFrames は lens.length 本返す", 3, framesOut.size());
        assertArrayEquals(f0, framesOut.get(0), 1.0e-6F);
        assertArrayEquals(f1, framesOut.get(1), 1.0e-6F);
        assertArrayEquals(f2, framesOut.get(2), 1.0e-6F);
    }

    @Test
    public void variableLengthBinSizeMatchesSumOfLensTimesStride() throws Exception {
        Path bin = tmp.getRoot().toPath().resolve("20260818-size.pose.bin");
        int stride = 3;
        float[] f0 = {0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F}; // 2 頂点
        float[] f1 = {1.1F, 1.2F, 1.3F, 1.4F, 1.5F, 1.6F, 1.7F, 1.8F, 1.9F}; // 3 頂点
        float[] f2 = {2.1F, 2.2F, 2.3F}; // 1 頂点
        SimPoseCodec.appendFrame(bin, f0);
        SimPoseCodec.appendFrame(bin, f1);
        SimPoseCodec.appendFrame(bin, f2);

        // sum(lens) = 2+3+1 = 6 頂点, stride=3 -> 18 float -> 72 バイト。
        // この等式が、修正が正しいことの唯一の機械的証拠 (計画の言葉どおり)。
        long expectedBytes = 6L * stride * Float.BYTES;
        assertEquals(72L, expectedBytes);
        assertEquals("bin のバイト数は sum(lens) * stride * 4 と厳密に一致する",
                expectedBytes, java.nio.file.Files.size(bin));
    }

    @Test
    public void legacyIndexWithoutLensReadsBackAsNull() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260817-legacy.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260817-legacy.pose.bin");

        float[] f0 = {0.1F, 0.2F, 0.3F};
        SimPoseCodec.appendFrame(bin, f0);

        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu", null,
                3, 1, 0, true, 1, bin.getFileName().toString());
        int[] slots = {0};
        // 既存の 3 引数版 (旧形式) で書く — lens 無し
        SimPoseCodec.writeIndex(json, header, slots);

        SimPoseCodec.Index idx = SimPoseCodec.readIndex(json);
        assertNull("lens を持たない旧索引は lens=null で読める (例外を投げない)", idx.lens());
        assertEquals(header, idx.header());
        assertArrayEquals(slots, idx.slots());
    }

    @Test
    public void variableLengthReadFramesRejectsSizeMismatch() throws Exception {
        Path bin = tmp.getRoot().toPath().resolve("20260818-mismatch.pose.bin");
        float[] f0 = {0.1F, 0.2F, 0.3F}; // 1 頂点 (stride=3)
        SimPoseCodec.appendFrame(bin, f0);

        // lens の総和 (2 頂点) が bin の実サイズ (1 頂点) と食い違う
        int[] lens = {2};
        try {
            SimPoseCodec.readFrames(bin, lens, 3);
            fail("lens の総和と bin の実サイズが食い違えば IOException になるはず");
        } catch (IOException expected) {
            // 期待どおり: 黙って途中まで読んだ「それらしい」結果を返さない
        }
    }

    // =========================================================================
    // グループ表 (glens/gtex/textures) — quick 260818-oq4:
    // 全 RenderType グループを描画順に連結して記録する
    // =========================================================================

    @Test
    public void multiGroupIndexRoundTripsGlensGtexTextures() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260818-groups.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260818-groups.pose.bin");

        int stride = 3;
        // フレーム0: 2グループ (頂点2+1=3)、フレーム1: 1グループ (頂点2)
        float[] f0 = {0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F, 0.7F, 0.8F, 0.9F}; // 3 頂点
        float[] f1 = {1.1F, 1.2F, 1.3F, 1.4F, 1.5F, 1.6F}; // 2 頂点
        SimPoseCodec.appendFrame(bin, f0);
        SimPoseCodec.appendFrame(bin, f1);

        int[] lens = {3, 2};
        int[][] glens = {{2, 1}, {2}};
        int[][] gtex = {{0, 1}, {0}};
        String[] textures = {"ysm:textures/texture2.png", "ysm:textures/texture3.png"};
        SimPoseCodec.Groups groups = new SimPoseCodec.Groups(glens, gtex, textures);

        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu",
                "ysm:textures/texture2.png",
                stride, 3, 0, true, 2, bin.getFileName().toString());
        int[] slots = {0, 1};
        SimPoseCodec.writeIndex(json, header, slots, lens, groups);

        SimPoseCodec.Index idx = SimPoseCodec.readIndex(json);
        assertEquals("groups が読み戻れる", 2, idx.groups().glens().length);
        for (int i = 0; i < glens.length; i++) {
            assertArrayEquals("glens[" + i + "] が要素単位で一致する", glens[i], idx.groups().glens()[i]);
            assertArrayEquals("gtex[" + i + "] が要素単位で一致する", gtex[i], idx.groups().gtex()[i]);
        }
        assertArrayEquals("textures が要素単位で一致する", textures, idx.groups().textures());
    }

    @Test
    public void writeIndexRejectsGlensSumMismatchAndCreatesNoFile() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260818-badsum.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260818-badsum.pose.bin");
        float[] f0 = {0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F}; // 2 頂点
        SimPoseCodec.appendFrame(bin, f0);

        int[] lens = {2};
        // sum(glens[0]) = 1+1 = 2 のはずが、わざと 3 にする (不整合)
        int[][] glens = {{1, 2}};
        int[][] gtex = {{0, 0}};
        String[] textures = {"ysm:textures/texture2.png"};
        SimPoseCodec.Groups groups = new SimPoseCodec.Groups(glens, gtex, textures);

        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu", "ysm:textures/texture2.png",
                3, 2, 0, true, 1, bin.getFileName().toString());
        int[] slots = {0};
        try {
            SimPoseCodec.writeIndex(json, header, slots, lens, groups);
            fail("sum(glens[i]) != lens[i] なら IOException になるはず");
        } catch (IOException expected) {
            // 期待どおり
        }
        assertTrue("不整合な索引はファイルを一切作らない", !java.nio.file.Files.exists(json));
    }

    @Test
    public void writeIndexRejectsGtexLengthMismatchAndCreatesNoFile() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260818-badgtex.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260818-badgtex.pose.bin");
        float[] f0 = {0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F}; // 2 頂点
        SimPoseCodec.appendFrame(bin, f0);

        int[] lens = {2};
        int[][] glens = {{2}};      // グループ1個
        int[][] gtex = {{0, 1}};    // グループ2個分 — 長さが食い違う
        String[] textures = {"ysm:textures/texture2.png", "ysm:textures/texture3.png"};
        SimPoseCodec.Groups groups = new SimPoseCodec.Groups(glens, gtex, textures);

        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu", "ysm:textures/texture2.png",
                3, 2, 0, true, 1, bin.getFileName().toString());
        int[] slots = {0};
        try {
            SimPoseCodec.writeIndex(json, header, slots, lens, groups);
            fail("gtex[i].length != glens[i].length なら IOException になるはず");
        } catch (IOException expected) {
            // 期待どおり
        }
        assertTrue("不整合な索引はファイルを一切作らない", !java.nio.file.Files.exists(json));
    }

    @Test
    public void writeIndexRejectsNullTextureAndCreatesNoFile() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260818-nulltex.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260818-nulltex.pose.bin");
        float[] f0 = {0.1F, 0.2F, 0.3F}; // 1 頂点
        SimPoseCodec.appendFrame(bin, f0);

        int[] lens = {1};
        int[][] glens = {{1}};
        int[][] gtex = {{0}};
        String[] textures = {null}; // 不正: null 要素
        SimPoseCodec.Groups groups = new SimPoseCodec.Groups(glens, gtex, textures);

        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu", null,
                3, 1, 0, true, 1, bin.getFileName().toString());
        int[] slots = {0};
        try {
            SimPoseCodec.writeIndex(json, header, slots, lens, groups);
            fail("textures に null 要素があれば IOException になるはず");
        } catch (IOException expected) {
            // 期待どおり
        }
        assertTrue("不整合な索引はファイルを一切作らない", !java.nio.file.Files.exists(json));
    }

    @Test
    public void indexWithoutGroupsReadsGroupsAsNull() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260818-nogroups.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260818-nogroups.pose.bin");

        float[] f0 = {0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F}; // 2 頂点
        SimPoseCodec.appendFrame(bin, f0);

        int[] lens = {2};
        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu", "touhou_little_maid:textures/entity/reimu.png",
                3, 2, 0, true, 1, bin.getFileName().toString());
        int[] slots = {0};
        // 4 引数版 (旧形式、groups 無し) で書く
        SimPoseCodec.writeIndex(json, header, slots, lens);

        SimPoseCodec.Index idx = SimPoseCodec.readIndex(json);
        assertNull("glens/gtex/textures を持たない索引は groups=null で読める (例外を投げない)", idx.groups());
        assertArrayEquals("lens はそのまま読める", lens, idx.lens());
    }

    @Test
    public void multiGroupBinSizeStillMatchesSumOfLensTimesStride() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260818-groupsize.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260818-groupsize.pose.bin");

        int stride = 3;
        float[] f0 = {0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F, 0.7F, 0.8F, 0.9F}; // 3 頂点、2グループ
        SimPoseCodec.appendFrame(bin, f0);

        int[] lens = {3};
        int[][] glens = {{2, 1}};
        int[][] gtex = {{0, 0}};
        String[] textures = {"ysm:textures/texture2.png"};
        SimPoseCodec.Groups groups = new SimPoseCodec.Groups(glens, gtex, textures);

        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu", "ysm:textures/texture2.png",
                stride, 3, 0, true, 1, bin.getFileName().toString());
        int[] slots = {0};
        SimPoseCodec.writeIndex(json, header, slots, lens, groups);

        // グループ表の有無は bin のバイト数を変えない — lens の不変条件がそのまま生きる証拠。
        long expectedBytes = 3L * stride * Float.BYTES;
        assertEquals("bin のバイト数は sum(lens) * stride * 4 と厳密に一致する (グループ表があっても不変)",
                expectedBytes, java.nio.file.Files.size(bin));
    }

    // =========================================================================
    // 多方向撮影 (unrotateYaw / mergeDirectionB) — quick 260818-x0k:
    // 同一 tick 内で yaw=0/180 の 2 方向を撮り、180° 側を符号反転のみの厳密な逆回転で
    // yaw=0 の座標系へ戻して連結する。
    //
    // この節のテストは Minecraft も renderer.render() も一切呼ばない —— unrotateYaw /
    // mergeDirectionB が純粋関数であることが、この節が通常の JUnit で green になること
    // 自体で証明される (plan-checker 指摘の BLOCKER 対応で要求された性質)。
    // =========================================================================

    /** 1 頂点あたりの float 数 ({@code SimVertexRecorder.STRIDE} と同じ)。 */
    private static final int V11 = 11;

    /**
     * stride=11 の 2 頂点分のテストデータ。
     * index 0=x, 1=y, 2=z, 3=u, 4=v, 5=nx, 6=ny, 7=nz, 8=r, 9=g, 10=b。
     */
    private static float[] twoVerts11() {
        return new float[]{
                1.5F, 2.5F, 3.5F, 0.25F, 0.75F, 0.0F, 1.0F, -0.5F, 1.0F, 0.5F, 0.25F,
                -4.5F, 5.5F, -6.5F, 0.125F, 0.875F, 0.6F, 0.125F, 0.8F, 0.1F, 0.2F, 0.3F,
        };
    }

    @Test
    public void unrotateYawZeroReturnsExactCopy() {
        float[] v = twoVerts11();
        float[] out = SimPoseCodec.unrotateYaw(v, V11, 0F);
        assertArrayEquals("yaw=0 は恒等変換 (要素が完全一致する新しい配列)", v, out, 0.0F);
        assertNotSame("非破壊契約: 入力そのものを返さない", v, out);
    }

    @Test
    public void unrotateYaw180FlipsOnlyPositionAndNormalXZ() {
        float[] v = twoVerts11();
        float[] out = SimPoseCodec.unrotateYaw(v, V11, 180F);
        for (int b = 0; b < v.length; b += V11) {
            assertEquals("x は符号反転", -v[b], out[b], 0.0F);
            assertEquals("y は無変化", v[b + 1], out[b + 1], 0.0F);
            assertEquals("z は符号反転", -v[b + 2], out[b + 2], 0.0F);
            assertEquals("u は無変化", v[b + 3], out[b + 3], 0.0F);
            assertEquals("v は無変化", v[b + 4], out[b + 4], 0.0F);
            assertEquals("nx は符号反転", -v[b + 5], out[b + 5], 0.0F);
            assertEquals("ny は無変化", v[b + 6], out[b + 6], 0.0F);
            assertEquals("nz は符号反転", -v[b + 7], out[b + 7], 0.0F);
            assertEquals("r は無変化", v[b + 8], out[b + 8], 0.0F);
            assertEquals("g は無変化", v[b + 9], out[b + 9], 0.0F);
            assertEquals("b は無変化", v[b + 10], out[b + 10], 0.0F);
        }
        // 入力そのものを書き換えていないことも確認する (非破壊契約)。
        assertArrayEquals("入力は変更されない", twoVerts11(), v, 0.0F);
    }

    @Test
    public void unrotateYaw180AppliedTwiceIsBitwiseIdentity() {
        float[] v = twoVerts11();
        float[] once = SimPoseCodec.unrotateYaw(v, V11, 180F);
        float[] twice = SimPoseCodec.unrotateYaw(once, V11, 180F);
        // BRIEF の明示要求: 三角関数を使わない (符号反転のみ) ため丸め誤差がゼロ。
        assertArrayEquals("180° を 2 回適用したら delta=0.0F で入力へ戻る", v, twice, 0.0F);
        // delta=0.0F は -0.0F と 0.0F を等値扱いするので、生ビットでも一致することを別に見る。
        for (int i = 0; i < v.length; i++) {
            assertEquals("要素 " + i + " が生ビットまで一致する (丸め誤差ゼロの証明)",
                    Float.floatToRawIntBits(v[i]), Float.floatToRawIntBits(twice[i]));
        }
    }

    @Test
    public void unrotateYawRejectsNonElevenStride() {
        float[] v = {0.1F, 0.2F, 0.3F};
        try {
            SimPoseCodec.unrotateYaw(v, 3, 180F);
            fail("stride != 11 は IllegalArgumentException になるはず"
                    + " ([x,y,z,u,v,nx,ny,nz,r,g,b] 以外を安全に扱えないため)");
        } catch (IllegalArgumentException expected) {
            // 期待どおり: 誤ったレイアウト解釈で頂点データを黙って壊さない
        }
    }

    @Test
    public void unrotateYawNormalizesAngle() {
        float[] v = twoVerts11();
        float[] base = SimPoseCodec.unrotateYaw(v, V11, 180F);
        assertArrayEquals("-180° は 180° と完全に同じ結果", base, SimPoseCodec.unrotateYaw(v, V11, -180F), 0.0F);
        assertArrayEquals("540° は 180° と完全に同じ結果", base, SimPoseCodec.unrotateYaw(v, V11, 540F), 0.0F);
        assertArrayEquals("360° は 0° (恒等) と同じ結果", v, SimPoseCodec.unrotateYaw(v, V11, 360F), 0.0F);
    }

    @Test
    public void mergeDirectionBReturnsNullWhenRawArraysAreIdentical() {
        float[] rawA = twoVerts11();
        float[] rawB = twoVerts11(); // YSM が 2 枚目の render をキャッシュで潰した状況
        assertNull("方向Bが方向Aと完全一致したら合成に使わない合図 (null) を返す",
                SimPoseCodec.mergeDirectionB(rawA, rawB, V11, 180F));
    }

    @Test
    public void mergeDirectionBReturnsNullWhenRawArraysDifferWithinSameEps() {
        float[] rawA = twoVerts11();
        float[] rawB = twoVerts11();
        // same() の誤差 1.0e-4 以内のゆらぎは「同一」とみなす (新しい比較規則を発明しない)。
        rawB[0] += 5.0e-5F;
        rawB[13] -= 5.0e-5F;
        assertNull("1.0e-4 以内の差しかなければ衝突扱い (null)",
                SimPoseCodec.mergeDirectionB(rawA, rawB, V11, 180F));
    }

    @Test
    public void mergeDirectionBDelegatesToUnrotateYawWhenDirectionsDiffer() {
        float[] rawA = twoVerts11();
        float[] rawB = twoVerts11();
        rawB[0] += 1.0F; // 有意に異なる = 別の面が撮れている
        float[] merged = SimPoseCodec.mergeDirectionB(rawA, rawB, V11, 180F);
        assertArrayEquals("衝突でなければ unrotateYaw と完全に同じ結果を返す",
                SimPoseCodec.unrotateYaw(rawB, V11, 180F), merged, 0.0F);
    }

    @Test
    public void multiDirectionMergedGroupsKeepGlensAndBinInvariants() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260818-multidir.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260818-multidir.pose.bin");

        int stride = 3;
        // 多方向合成を模した 1 フレーム: 「方向Aの全グループ → 方向Bの全グループ」の順。
        //   方向A: グループ0 (2 頂点) + グループ1 (1 頂点)
        //   方向B: グループ2 (2 頂点)
        // 方向間でグループを畳まない (同じ RenderType の A/B を 1 グループにしない) ので
        // グループは 3 本のまま、合計 5 頂点になる。
        float[] f0 = {
                0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F,   // dirA グループ0 (2 頂点)
                0.7F, 0.8F, 0.9F,                     // dirA グループ1 (1 頂点)
                1.1F, 1.2F, 1.3F, 1.4F, 1.5F, 1.6F,   // dirB グループ2 (2 頂点、逆回転済み)
        };
        SimPoseCodec.appendFrame(bin, f0);

        int[] lens = {5};
        int[][] glens = {{2, 1, 2}};
        int[][] gtex = {{0, 1, 0}};
        String[] textures = {"ysm:textures/texture2.png", "ysm:textures/texture3.png"};
        SimPoseCodec.Groups groups = new SimPoseCodec.Groups(glens, gtex, textures);

        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, 1000L, 314, "touhou_little_maid:reimu", "ysm:textures/texture2.png",
                stride, 5, 0, true, 1, bin.getFileName().toString());
        int[] slots = {0};
        SimPoseCodec.writeIndex(json, header, slots, lens, groups);

        SimPoseCodec.Index idx = SimPoseCodec.readIndex(json);
        assertArrayEquals("方向A 2 本 + 方向B 1 本 = 3 グループがそのまま読み戻る",
                glens[0], idx.groups().glens()[0]);
        assertArrayEquals("gtex も要素単位で一致する", gtex[0], idx.groups().gtex()[0]);

        int sum = 0;
        for (int g : idx.groups().glens()[0]) {
            sum += g;
        }
        assertEquals("多方向でグループが増えても sum(glens[i]) == lens[i]", idx.lens()[0], sum);
        assertEquals("bin のバイト数は sum(lens) * stride * 4 と厳密に一致する (多方向でも不変)",
                5L * stride * Float.BYTES, java.nio.file.Files.size(bin));

        List<float[]> back = SimPoseCodec.readFrames(bin, idx.lens(), stride);
        assertEquals("フレーム 1 本が読み戻る", 1, back.size());
        assertArrayEquals("連結順 (方向A → 方向B) がそのまま保たれる", f0, back.get(0), 0.0F);
    }

    // =========================================================================
    // 形式 v2 — uuid (2026-08-24)
    // =========================================================================
    // **何を守るのか**: 姿勢 companion が「どの run の誰か」を自分で名乗ること。
    // これが無いと読み手は gt0 と gameTime の重なりでしか突き合わせられず、tank のように
    // 宣言 duration が 24 時間あるシナリオでは**過去のあらゆる companion が窓に入り、
    // 別 run の姿勢が黙って採用される** (実測: gameTime=1 のトレースに gt0=104870 の
    // companion が吸着し base=-104869、実機頂点が 1 フレームも使われていなかった)。

    @Test
    public void v2HeaderRoundTripsUuid() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260824-000000.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260824-000000.pose.bin");
        SimPoseCodec.appendFrame(bin, new float[]{0.1F, 0.2F, 0.3F});

        String uuid = "6b933a53-6ec6-4988-953b-b0d888317691";
        SimPoseCodec.Header header = new SimPoseCodec.Header(
                SimPoseCodec.V2, 1000L, 2, "touhou_little_maid:reimu", null,
                3, 1, 0, true, 1, bin.getFileName().toString(), uuid);
        SimPoseCodec.writeIndex(json, header, new int[]{0});

        SimPoseCodec.Index idx = SimPoseCodec.readIndex(json);
        assertEquals("uuid が往復する", uuid, idx.header().uuid());
        assertEquals("Header の全フィールドが一致する", header, idx.header());
    }

    @Test
    public void v1IndexStillReadsBackWithNullUuid() throws Exception {
        Path json = tmp.getRoot().toPath().resolve("20260824-v1.pose.json");
        Path bin = tmp.getRoot().toPath().resolve("20260824-v1.pose.bin");
        SimPoseCodec.appendFrame(bin, new float[]{0.1F, 0.2F, 0.3F});

        // 旧 11 引数の呼び出し —— **既存の書き手を 1 行も変えずに読めること**が条件。
        SimPoseCodec.Header header = new SimPoseCodec.Header(
                SimPoseCodec.V1, 1000L, 2, "touhou_little_maid:reimu", null,
                3, 1, 0, true, 1, bin.getFileName().toString());
        SimPoseCodec.writeIndex(json, header, new int[]{0});

        assertNull("v1 の uuid は null のまま", SimPoseCodec.readIndex(json).header().uuid());
        assertFalse("uuid を持たない索引に uuid キーを書かない (旧形式の出力を変えない)",
                new String(java.nio.file.Files.readAllBytes(json),
                        java.nio.charset.StandardCharsets.UTF_8).contains("uuid"));
    }
}
