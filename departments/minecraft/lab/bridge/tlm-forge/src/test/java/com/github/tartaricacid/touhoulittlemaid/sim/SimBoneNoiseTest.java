package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.client.SimBoneNoise;
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

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * {@link SimBoneNoise} の golden 再生検証 (260824-bnz)。
 *
 * <p>{@link SimBoneNoise} は Minecraft のクラスを一切 import しないので、通常の JUnit で
 * そのまま回る —— この green 自体が「MC を起動せずに使える」の証明になる (M8)。
 *
 * <p>golden は {@code .planning/spikes/004-ysm-bone-map-probe/data/run2-20260824-063022/}
 * の実機採取データ ({@code *.palette.bin} + {@code index.json})。標本 000 が基準の 1 枚目、
 * 001/002 が基準の 2・3 枚目 (揺らぎを導くのに必要)、003/006/009/012/015 が各姿勢の先頭標本。
 * fixture が欠けていたら skip ではなく fail する ── 黙って skip するゲートは無音の no-op。
 */
public class SimBoneNoiseTest {

    private static final Path DIR = Paths.get(".planning", "spikes", "004-ysm-bone-map-probe",
            "data", "run2-20260824-063022");

    private static float[] readPalette(String name) throws IOException {
        Path f = DIR.resolve(name);
        if (!Files.exists(f)) {
            fail(f.toAbsolutePath() + " が無い(golden fixture 欠落)");
        }
        byte[] bytes = Files.readAllBytes(f);
        ByteBuffer bb = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        float[] out = new float[bytes.length / 4];
        bb.asFloatBuffer().get(out);
        return out;
    }

    /** 000/001/002 から積み上げたボーンごとの揺らぎ。全テストで使い回す。 */
    private static float[] perBoneNoise() throws IOException {
        float[] p000 = readPalette("000.palette.bin");
        float[] p001 = readPalette("001.palette.bin");
        float[] p002 = readPalette("002.palette.bin");
        float[] perBone = SimBoneNoise.newPerBone(p000.length);
        SimBoneNoise.accumulate(perBone, p000, p001);
        SimBoneNoise.accumulate(perBone, p000, p002);
        return perBone;
    }

    // =========================================================================
    // (1) 揺らぎはボーンごと ── M1
    // =========================================================================

    @Test
    public void perBoneNoiseHasOneLoudBone() throws IOException {
        float[] perBone = perBoneNoise();
        assertEquals("揺らぎ配列の長さは 12696/12 = 1058 本", 1058, perBone.length);

        int quiet = 0;
        for (float v : perBone) {
            if (v < 0.01F) {
                quiet++;
            }
        }
        assertEquals("揺らぎ<0.01 のボーン数は 989 本(streaming 形。総当たりの.mjsは988 ── "
                + "既知の差で、直さない)", 989, quiet);
        assertEquals("中央値は 0", 0.0F, SimBoneNoise.median(perBone), 1.0e-6F);
        assertEquals("p99 は 1.5452", 1.5452F, SimBoneNoise.quantile(perBone, 0.99F), 1.0e-3F);
        assertEquals("最大は旧スカラー閾値 37.87015 と一致する ── 1本の物理ボーンが"
                + "1057本を隠していたことの物証", 37.8702F, SimBoneNoise.max(perBone), 1.0e-3F);
    }

    // =========================================================================
    // (2) 基準標本そのものは誤検知しない ── M6
    // =========================================================================

    @Test
    public void baselineSamplesDoNotTakeEffect() throws IOException {
        float[] perBone = perBoneNoise();
        float[] p000 = readPalette("000.palette.bin");

        float[] up1 = SimBoneNoise.takeUp(p000, readPalette("001.palette.bin"), perBone);
        assertEquals("標本001(基準そのもの)は changedBones==0", 0, (int) up1[0]);

        float[] up2 = SimBoneNoise.takeUp(p000, readPalette("002.palette.bin"), perBone);
        assertEquals("標本002(基準そのもの)は changedBones==0", 0, (int) up2[0]);
    }

    // =========================================================================
    // (3) golden 5 姿勢すべてが「効いた」になる ── M3
    // =========================================================================

    @Test
    public void goldenPosesTakeEffect() throws IOException {
        float[] perBone = perBoneNoise();
        float[] p000 = readPalette("000.palette.bin");

        String[] samples = {"003", "006", "009", "012", "015"};
        int[] expectedChanged = {117, 87, 44, 55, 53};
        String[] poseNames = {"extra44", "extra43", "sneaking_1", "use_offhand:bow", "extra95"};

        for (int i = 0; i < samples.length; i++) {
            float[] palette = readPalette(samples[i] + ".palette.bin");
            float[] up = SimBoneNoise.takeUp(p000, palette, perBone);
            int changed = (int) up[0];
            assertEquals("姿勢 " + poseNames[i] + " (標本" + samples[i] + ") の changedBones",
                    expectedChanged[i], changed);
            assertTrue("姿勢 " + poseNames[i] + " は tookEffect (changed>=3) になるはず", changed >= 3);
        }
    }

    // =========================================================================
    // (4) 旧ロジック(共有スカラー)では 5 姿勢とも RED ── M4、テストがRED を出せることの証明
    // =========================================================================

    @Test
    public void scalarNoiseMasksEveryPose() throws IOException {
        // 旧実装は 1058 本を共有スカラー 1 個(37.87015)で代表していた。
        // 同じ配列の全要素をその値で埋めれば、旧ロジックを SimBoneNoise.takeUp で再現できる。
        float[] scalarPerBone = new float[1058];
        java.util.Arrays.fill(scalarPerBone, 37.87015F);

        float[] p000 = readPalette("000.palette.bin");
        String[] samples = {"003", "006", "009", "012", "015"};
        String[] poseNames = {"extra44", "extra43", "sneaking_1", "use_offhand:bow", "extra95"};

        for (int i = 0; i < samples.length; i++) {
            float[] palette = readPalette(samples[i] + ".palette.bin");
            float[] up = SimBoneNoise.takeUp(p000, palette, scalarPerBone);
            assertEquals("共有スカラーの閾値では姿勢 " + poseNames[i] + " は changedBones==0 になる"
                    + " (旧ロジックの誤判定をこのテストが再現できることの証明)", 0, (int) up[0]);
        }
    }

    // =========================================================================
    // (5) 生データの数値は一切変わらない ── M5
    // =========================================================================

    @Test
    public void maxDeltaUnchanged() throws IOException {
        Path idxPath = DIR.resolve("index.json");
        if (!Files.exists(idxPath)) {
            fail(idxPath.toAbsolutePath() + " が無い(golden fixture 欠落)");
        }
        String text = new String(Files.readAllBytes(idxPath), StandardCharsets.UTF_8);
        JsonObject index = JsonParser.parseString(text).getAsJsonObject();
        JsonArray sampleArr = index.getAsJsonArray("samples");

        float[] perBone = perBoneNoise();
        float[] p000 = readPalette("000.palette.bin");

        int checked = 0;
        for (int i = 0; i < sampleArr.size(); i++) {
            JsonObject s = sampleArr.get(i).getAsJsonObject();
            if (!s.has("maxDelta")) {
                continue;
            }
            int idx = s.get("index").getAsInt();
            float recordedMax = s.get("maxDelta").getAsFloat();
            float[] palette = readPalette(String.format(java.util.Locale.ROOT, "%03d", idx) + ".palette.bin");
            float[] up = SimBoneNoise.takeUp(p000, palette, perBone);
            assertEquals("標本" + idx + " の maxDelta は index.json の記録と一致するはず"
                    + " (生データの数値は一切変えていない)", recordedMax, up[1], 1.0e-4F);
            checked++;
        }
        assertTrue("index.json に maxDelta を持つ標本が1件も無いのはおかしい", checked > 0);
    }
}
