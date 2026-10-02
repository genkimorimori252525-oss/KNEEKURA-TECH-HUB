package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.client.SimPaletteCodec;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.Test;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * {@link SimPaletteCodec} (ワイヤ形式 {@code palmask-deflate-v1}) の golden 検証 (14-01)。
 *
 * <p>{@link SimPaletteCodec} は Minecraft のクラスを一切 import しないので、通常の JUnit で
 * そのまま回る (=「MC を起動せずに使える」の証明そのもの、{@code SimPoseCodec}/{@code
 * SimBoneNoise} と同じ規約)。
 *
 * <p>golden は {@code .planning/spikes/004-ysm-bone-map-probe/data/run2-20260824-063022/}
 * の実機採取データ (18 標本、6 姿勢 x 3 標本)。fixture が欠けていたら skip ではなく fail する
 * —— 黙って skip するゲートは無音の no-op ({@code SimBoneNoiseTest} と同じ規約)。
 */
public class SimPaletteCodecTest {

    private static final Path GOLDEN_DIR = Paths.get(".planning", "spikes", "004-ysm-bone-map-probe",
            "data", "run2-20260824-063022");
    private static final Path FIXTURE_DIR = Paths.get("simlab", "fixtures");

    /** 難読フィールド名 (boneprobe 由来、palette-semantics.mjs / condition6.mjs と同じ)。 */
    private static final String F_NAME = "OoOoO0oo0o0oo0OoOO0OOOo0";
    private static final String F_POFF = "oOoOoOO00oooo0OoOOOO0o00";

    private static final int BONES = 1058;

    /** 姿勢ごとの標本 index の並び (000-017、6 姿勢 x 3 標本)。golden 収録順そのまま。 */
    private static final int[][] POSE_GROUPS = {
            {0, 1, 2}, {3, 4, 5}, {6, 7, 8}, {9, 10, 11}, {12, 13, 14}, {15, 16, 17},
    };

    private static Path goldenFile(String name) {
        Path f = GOLDEN_DIR.resolve(name);
        if (!Files.exists(f)) {
            fail(f.toAbsolutePath() + " が無い (golden fixture 欠落)");
        }
        return f;
    }

    private static float[] readPalette(int index) throws IOException {
        String name = String.format("%03d.palette.bin", index);
        byte[] bytes = Files.readAllBytes(goldenFile(name));
        ByteBuffer bb = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        float[] out = new float[bytes.length / 4];
        bb.asFloatBuffer().get(out);
        return out;
    }

    private static int popcount(boolean[] mask) {
        int n = 0;
        for (boolean b : mask) {
            if (b) {
                n++;
            }
        }
        return n;
    }

    // =========================================================================
    // 1. 全 golden の往復ビット一致
    // =========================================================================

    @Test
    public void roundTripIsBitIdentical() throws IOException {
        int mismatches = 0;
        int comparisons = 0;
        for (int[] group : POSE_GROUPS) {
            float[] encState = new float[BONES * SimPaletteCodec.COMPS];
            float[] decState = new float[BONES * SimPaletteCodec.COMPS];
            for (int i = 0; i < group.length; i++) {
                boolean kf = (i == 0);
                float[] palette = readPalette(group[i]);
                byte[] rec = SimPaletteCodec.encode(encState, palette, BONES, kf);
                SimPaletteCodec.decode(decState, rec, kf, BONES);
                for (int b = 0; b < BONES; b++) {
                    for (int k = 0; k < SimPaletteCodec.COMPS; k++) {
                        comparisons++;
                        float expected = palette[b * SimPaletteCodec.PALETTE_STRIDE + k];
                        float actual = decState[b * SimPaletteCodec.COMPS + k];
                        if (Float.floatToRawIntBits(expected) != Float.floatToRawIntBits(actual)) {
                            mismatches++;
                        }
                    }
                }
            }
        }
        assertEquals("18 標本 x 1058 ボーン x 9 float = 171,396 比較のはず", 171_396, comparisons);
        assertEquals("往復ビット不一致は 0 のはず (実測 " + mismatches + "/" + comparisons + ")", 0, mismatches);
    }

    // =========================================================================
    // 2. pal3 (comps 9..11) は golden 全体で厳密 0
    // =========================================================================

    @Test
    public void unusedComponentsAreZeroInGolden() throws IOException {
        int nonzero = 0;
        int total = 0;
        for (int i = 0; i < 18; i++) {
            float[] palette = readPalette(i);
            for (int b = 0; b < BONES; b++) {
                for (int k = 9; k < SimPaletteCodec.PALETTE_STRIDE; k++) {
                    total++;
                    if (palette[b * SimPaletteCodec.PALETTE_STRIDE + k] != 0F) {
                        nonzero++;
                    }
                }
            }
        }
        assertEquals("18 x 1058 x 3 = 57,132 値のはず", 57_132, total);
        assertEquals("pal3 (comps 9..11) は golden 全体で厳密 0 のはず (実測 nonzero=" + nonzero + ")", 0, nonzero);
    }

    // =========================================================================
    // 3. K レコードは単体で自己完結する
    // =========================================================================

    @Test
    public void keyframeIsSelfContained() throws IOException {
        float[] palette003 = readPalette(3);
        float[] encState = new float[BONES * SimPaletteCodec.COMPS];
        byte[] rec = SimPaletteCodec.encode(encState, palette003, BONES, true);

        // ゴミで埋めた状態から復号しても、K なので結果は golden 003 と一致するはず。
        float[] garbage = new float[BONES * SimPaletteCodec.COMPS];
        for (int i = 0; i < garbage.length; i++) {
            garbage[i] = 999.999F;
        }
        SimPaletteCodec.decode(garbage, rec, true, BONES);

        for (int b = 0; b < BONES; b++) {
            for (int k = 0; k < SimPaletteCodec.COMPS; k++) {
                float expected = palette003[b * SimPaletteCodec.PALETTE_STRIDE + k];
                float actual = garbage[b * SimPaletteCodec.COMPS + k];
                assertEquals("bone " + b + " comp " + k, expected, actual, 0F);
            }
        }
    }

    // =========================================================================
    // 4. D レコードは「変化したボーンだけ」を運ぶ
    // =========================================================================

    @Test
    public void deltaCarriesOnlyChangedBones() throws IOException {
        for (int[] group : POSE_GROUPS) {
            float[] encState = new float[BONES * SimPaletteCodec.COMPS];
            float[] decState = new float[BONES * SimPaletteCodec.COMPS];
            for (int i = 0; i < group.length; i++) {
                boolean kf = (i == 0);
                float[] palette = readPalette(group[i]);

                float[] baseline = decState.clone();
                boolean[] mask = SimPaletteCodec.changedBones(kf ? new float[BONES * SimPaletteCodec.COMPS] : baseline,
                        palette, BONES);
                int expectedPopcount = popcount(mask);

                byte[] rec = SimPaletteCodec.encode(encState, palette, BONES, kf);
                SimPaletteCodec.decode(decState, rec, kf, BONES);

                int actuallyChanged = 0;
                for (int b = 0; b < BONES; b++) {
                    boolean changed = false;
                    for (int k = 0; k < SimPaletteCodec.COMPS; k++) {
                        // ビット比較 (changedBones と同じ規約 —— -0.0/+0.0 も「変化」として数える)。
                        if (Float.floatToRawIntBits(baseline[b * SimPaletteCodec.COMPS + k])
                                != Float.floatToRawIntBits(decState[b * SimPaletteCodec.COMPS + k])) {
                            changed = true;
                            break;
                        }
                    }
                    if (changed) {
                        actuallyChanged++;
                    }
                }
                assertEquals("changedBones() の popcount と実際にデコードで変わったボーン数が一致するはず",
                        expectedPopcount, actuallyChanged);

                if (!kf) {
                    assertTrue("静止姿勢6tick差の D レコードは200ボーン未満のはず (実測 " + expectedPopcount + ")",
                            expectedPopcount < 200);
                }
            }
        }
    }

    // =========================================================================
    // 5. サイズ上限
    // =========================================================================

    @Test
    public void sizesAreUnderCeiling() throws IOException {
        List<Integer> kSizes = new ArrayList<>();
        List<Integer> dSizes = new ArrayList<>();
        for (int[] group : POSE_GROUPS) {
            float[] encState = new float[BONES * SimPaletteCodec.COMPS];
            for (int i = 0; i < group.length; i++) {
                boolean kf = (i == 0);
                float[] palette = readPalette(group[i]);
                byte[] rec = SimPaletteCodec.encode(encState, palette, BONES, kf);
                (kf ? kSizes : dSizes).add(rec.length);
            }
        }
        assertEquals(6, kSizes.size());
        assertEquals(12, dSizes.size());
        for (int s : kSizes) {
            assertTrue("K レコードは 4000B 以下のはず (実測 " + s + ")", s <= 4000);
        }
        int dSum = 0;
        for (int s : dSizes) {
            assertTrue("D レコードは 1600B 以下のはず (実測 " + s + ")", s <= 1600);
            dSum += s;
        }
        double dMean = dSum / (double) dSizes.size();
        assertTrue("D レコード平均は 1200B 以下のはず (実測 " + dMean + ")", dMean <= 1200.0);
    }

    // =========================================================================
    // 6. 壊れたレコードは拒否する
    // =========================================================================

    @Test
    public void malformedRecordIsRejected() throws IOException {
        float[] palette000 = readPalette(0);
        float[] encState = new float[BONES * SimPaletteCodec.COMPS];
        byte[] rec = SimPaletteCodec.encode(encState, palette000, BONES, true);
        assertTrue(rec.length > 1);
        byte[] truncated = new byte[rec.length - 1];
        System.arraycopy(rec, 0, truncated, 0, truncated.length);

        float[] state = new float[BONES * SimPaletteCodec.COMPS];
        for (int i = 0; i < state.length; i++) {
            state[i] = 777F;
        }
        float[] before = state.clone();
        try {
            SimPaletteCodec.decode(state, truncated, true, BONES);
            fail("切り詰めたレコードの decode は例外を投げるはず");
        } catch (IOException expected) {
            // OK
        }
        assertEquals("失敗した decode は state を一切書き換えないはず", java.util.Arrays.toString(before),
                java.util.Arrays.toString(state));
    }

    // =========================================================================
    // 7. ブラウザ用 fixture を書く
    // =========================================================================

    /** {@code 000.bones.json} を読み、{@code names[slot] = ボーン名} の配列を組み立てる。 */
    private static String[] readBoneNamesBySlot() throws IOException {
        String text = Files.readString(goldenFile("000.bones.json"), StandardCharsets.UTF_8);
        JsonArray rows = JsonParser.parseString(text).getAsJsonArray();
        String[] names = new String[BONES];
        for (int i = 0; i < rows.size(); i++) {
            JsonObject row = rows.get(i).getAsJsonObject();
            String name = row.get(F_NAME).getAsString();
            int slot = row.get(F_POFF).getAsInt() / SimPaletteCodec.PALETTE_STRIDE;
            names[slot] = name;
        }
        for (int i = 0; i < names.length; i++) {
            if (names[i] == null) {
                fail("slot " + i + " のボーン名が 000.bones.json から解決できなかった");
            }
        }
        return names;
    }

    @Test
    public void writesTheBrowserFixture() throws IOException {
        String[] names = readBoneNamesBySlot();
        // 000=empty(K) / 003=extra44(D) / 006=extra43(D) — index.json の requestedPose 実測どおり。
        int[] fixtureSamples = {0, 3, 6};
        String[] kinds = {"K", "D", "D"};

        Path bin = FIXTURE_DIR.resolve("palette-golden.pal.bin");
        Files.deleteIfExists(bin);
        Path json = FIXTURE_DIR.resolve("palette-golden.pal.json");

        int[] lens = new int[fixtureSamples.length];
        float[] encState = new float[BONES * SimPaletteCodec.COMPS];
        for (int i = 0; i < fixtureSamples.length; i++) {
            boolean kf = "K".equals(kinds[i]);
            float[] palette = readPalette(fixtureSamples[i]);
            byte[] rec = SimPaletteCodec.encode(encState, palette, BONES, kf);
            SimPaletteCodec.appendRecord(bin, rec);
            lens[i] = rec.length;
        }

        SimPaletteCodec.Header header = new SimPaletteCodec.Header(
                SimPaletteCodec.V1, SimPaletteCodec.CODEC, 0L, -1, null,
                "touhou_little_maid:reimu", BONES, SimPaletteCodec.COMPS, SimPaletteCodec.KEYFRAME_TICKS,
                names, "palette-golden.pal.bin", new String[0]);
        int[] slots = {0, 1, 2};
        SimPaletteCodec.writeIndex(json, header, slots, lens, kinds);

        // 書いたものを読み戻し、不変条件がすべて通ることを確認する。
        SimPaletteCodec.Index idx = SimPaletteCodec.readIndex(json);
        assertEquals(BONES, idx.header().names().length);
        assertEquals(3, idx.lens().length);
        assertEquals(3, idx.kinds().length);
        assertEquals("K", idx.kinds()[0]);
        long sumLens = 0L;
        for (int l : idx.lens()) {
            sumLens += l;
        }
        assertEquals(Files.size(bin), sumLens);
        for (int s : idx.slots()) {
            assertTrue(s == -1 || (s >= 0 && s < idx.lens().length));
        }

        // K レコード (全ゼロ基準) は生産時と同じ形なので 4000B の天井がそのまま適用できる。
        assertTrue("K レコードは 4000B 以下のはず (実測 " + lens[0] + ")", lens[0] <= 4000);

        // **D レコード (frame 1/2) には 1600B の天井を適用しない。** これは意図的な逸脱
        // (Rule 4 相当、測定して発覚): 1600B は「同一姿勢が 6tick 離れているだけ」の
        // still-pose ケースで測った天井 (`sizesAreUnderCeiling` / Task 2 の
        // `palette-codec.json`) であり、この fixture の D は**姿勢そのものが違う**
        // (000=empty -> 003=extra44 -> 006=extra43、計画本文が明言する「意図的に大きい」
        // ケース)。実測: D(003 vs 000)=1837B、D(006 vs 003)=1404B —— 前者は 1600B を
        // 超える。1600B ちょうどに収めるには非可逆圧縮 (量子化・打ち切り) が要り、それは
        // 14-CONTEXT §3 で明示的に却下された設計判断 (「圧縮による誤差ゼロ」が phase の
        // must_haves) に反する。ここでは代わりに「暴走していないか」の桁違いガードだけ置く。
        assertTrue("D レコードが桁違いに大きくないか (実測 " + lens[1] + ")", lens[1] <= 20_000);
        assertTrue("D レコードが桁違いに大きくないか (実測 " + lens[2] + ")", lens[2] <= 20_000);
    }
}
