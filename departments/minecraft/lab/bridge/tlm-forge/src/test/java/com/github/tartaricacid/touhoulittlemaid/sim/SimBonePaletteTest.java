package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.client.SimBonePalette;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * {@link SimBonePalette} の検証 (14-02 Task 1)。
 *
 * <p>{@link SimBonePalette#find} は普通の Java オブジェクトを反射で歩くだけなので、
 * Minecraft を起動せずに合成オブジェクトで検証できる ({@code SimBoneNoise}/{@code
 * SimPaletteCodec} と同じ「MC を import しない」規約の反射版)。
 * {@link SimBonePalette#classifySlot} は反射型を一切取らない純関数なので、golden の
 * {@code 000.bones.json} からオフラインで 1058 本すべてを検算できる。
 */
public class SimBonePaletteTest {

    private static final Path GOLDEN = Paths.get(".planning", "spikes", "004-ysm-bone-map-probe",
            "data", "run2-20260824-063022", "000.bones.json");

    // =========================================================================
    // find() — 「Map + N*12 の float[]」を形で探す (SimBoneCapture から移動した経路)
    // =========================================================================

    /** find() の探索対象になる、実機の「ボーンマップの持ち主」の形を模した合成オーナー。 */
    static final class SyntheticOwner {
        Map<Integer, Object> bones;
        float[] palette;
        float[] quats;
    }

    @Test
    public void findsPaletteByShape() {
        SyntheticOwner owner = new SyntheticOwner();
        Map<Integer, Object> bones = new LinkedHashMap<>();
        bones.put(1, "b1");
        bones.put(2, "b2");
        bones.put(3, "b3");
        bones.put(4, "b4");
        owner.bones = bones;
        owner.palette = new float[48]; // 4 * 12
        owner.quats = new float[16];   // 4 * 4

        SimBonePalette.Found found = SimBonePalette.find(owner);
        assertNotNull("形が合う owner から見つかるはず", found);
        assertTrue("palette は N*12 要素の配列そのもの (参照同一)", found.palette() == owner.palette);
        assertTrue("quats は N*4 要素の配列そのもの (参照同一)", found.quats() == owner.quats);
        assertEquals(4, found.bones().size());
    }

    /** 長さが合わない float[] しか無ければ、find() は黙って何かを掴まず null を返す。 */
    static final class WrongLengthOwner {
        Map<Integer, Object> bones;
        float[] onlyArray;
    }

    @Test
    public void ignoresWrongLengthArrays() {
        WrongLengthOwner owner = new WrongLengthOwner();
        Map<Integer, Object> bones = new LinkedHashMap<>();
        bones.put(1, "b1");
        bones.put(2, "b2");
        bones.put(3, "b3");
        bones.put(4, "b4");
        owner.bones = bones;
        owner.onlyArray = new float[47]; // N*12=48 にも N*4=16 にも一致しない

        SimBonePalette.Found found = SimBonePalette.find(owner);
        assertNull("N*12 (または N*4) に一致する float[] が無ければ何も掴まない (fail closed)", found);
    }

    // =========================================================================
    // classifySlot() — 反射型を一切取らない純関数
    // =========================================================================

    @Test
    public void rejectsAmbiguousBones() {
        // 1本の bone の int 集合が (p=36,q=12)->k=3 と (p=60,q=20)->k=5 の両方を満たす。
        List<Integer> ints = List.of(36, 12, 60, 20);
        SimBonePalette.SlotClassification c = SimBonePalette.classifySlot("ambiguous", ints, 10);
        assertFalse("食い違う複数候補は成功にしない — 1つ目へ黙って解決しない", c.ok());
        assertTrue("失敗理由に 'ambiguous' が出る: " + c.reason(), c.reason().contains("ambiguous"));
    }

    @Test
    public void classifySlotWithNoValidPairFails() {
        List<Integer> ints = List.of(1, 2, 3);
        SimBonePalette.SlotClassification c = SimBonePalette.classifySlot("none", ints, 10);
        assertFalse("12 の倍数も 4 の倍数の組も無ければ失敗するはず", c.ok());
    }

    // =========================================================================
    // slotNames() — 反射で bone 名 -> slot を解決する
    // =========================================================================

    /** 実機の bone の形を模した合成 bone: name + (array, その添字int) の組を2つ持つ。 */
    static final class Bone {
        final String name;
        final float[] pal;
        final int p;
        final float[] quat;
        final int q;

        Bone(String name, float[] pal, int p, float[] quat, int q) {
            this.name = name;
            this.pal = pal;
            this.p = p;
            this.quat = quat;
            this.q = q;
        }
    }

    private static SimBonePalette.Found syntheticFound(
            int boneCount, int[] mapKeys, String[] names, int[] ps, int[] qs) {
        float[] palette = new float[boneCount * 12];
        float[] quats = new float[boneCount * 4];
        Map<Integer, Object> bones = new LinkedHashMap<>();
        for (int i = 0; i < mapKeys.length; i++) {
            bones.put(mapKeys[i], new Bone(names[i], palette, ps[i], quats, qs[i]));
        }
        return new SimBonePalette.Found(bones, palette, quats, "synthetic", "root");
    }

    @Test
    public void resolvesSlotsFromTheIntPair() {
        int n = 6;
        int[] mapKeys = new int[n];
        String[] names = new String[n];
        int[] ps = new int[n];
        int[] qs = new int[n];
        for (int k = 0; k < n; k++) {
            // map key は slot と無関係な値にする — 実機でも Int2ReferenceMap のキーは
            // YSM 自身のボーン id であって slot ではない (map の反復順を信じてはいけない、
            // という SimBonePalette.slotNames の前提そのものを検証する)。
            mapKeys[k] = 1000 + k * 37;
            names[k] = "bone" + k;
            ps[k] = 12 * k;
            qs[k] = 4 * k;
        }
        SimBonePalette.Found found = syntheticFound(n, mapKeys, names, ps, qs);
        SimBonePalette.SlotResult r = SimBonePalette.slotNames(found);
        assertTrue("解決できるはず: " + r.reason(), r.ok());
        for (int k = 0; k < n; k++) {
            assertEquals("slot " + k + " の名前", "bone" + k, r.names()[k]);
        }
    }

    @Test
    public void rejectsIncompleteSlotCover() {
        // 3本のうち2本 (a, b) が同じ slot 0 を指す。pigeonhole により、必ずどこかの slot
        // (この場合 1) が空いたまま残る — 「distinct 本数」で失敗を報告するはず。
        int n = 3;
        int[] mapKeys = {10, 20, 30};
        String[] names = {"a", "b", "c"};
        int[] ps = {0, 0, 24};  // a, b とも slot 0 (p/12==0)。c は slot 2 (24/12==2)
        int[] qs = {0, 0, 8};   // a, b とも slot 0 (q/4==0)。c は slot 2 (8/4==2)
        SimBonePalette.Found found = syntheticFound(n, mapKeys, names, ps, qs);
        SimBonePalette.SlotResult r = SimBonePalette.slotNames(found);
        assertFalse("2本が同じ slot、slot 1 が空くので失敗するはず", r.ok());
        assertTrue("distinct 本数 (2/3) を含む理由になっているはず: " + r.reason(),
                r.reason().contains("2/3"));
    }

    // =========================================================================
    // golden — 実機 1058 本すべてが解決する (spike 004 の実測データで検算)
    // =========================================================================

    @Test
    public void goldenBoneNamesResolve() throws IOException {
        if (!Files.exists(GOLDEN)) {
            fail(GOLDEN.toAbsolutePath() + " が無い (golden fixture 欠落)");
        }
        String text = new String(Files.readAllBytes(GOLDEN), StandardCharsets.UTF_8);
        JsonArray rows = JsonParser.parseString(text).getAsJsonArray();
        int boneCount = rows.size();
        assertEquals("golden の bone 本数", 1058, boneCount);

        String[] resolved = new String[boneCount];
        boolean[] filled = new boolean[boneCount];
        int distinct = 0;
        for (int i = 0; i < rows.size(); i++) {
            JsonObject b = rows.get(i).getAsJsonObject();
            // 難読フィールド名 (spike 004 boneprobe 由来。palette-semantics.mjs と同じ)。
            String name = b.get("OoOoO0oo0o0oo0OoOO0OOOo0").getAsString();
            List<Integer> ints = new ArrayList<>();
            ints.add(b.get("O000OooO00oOoO0oOOoOOooo").getAsInt()); // id (map key と同じ値)
            ints.add(b.get("oOoOoOO00oooo0OoOOOO0o00").getAsInt()); // palette 配列への添字
            ints.add(b.get("OOo0OoO0oOOOOO0ooO0O000O").getAsInt()); // quat 配列への添字

            SimBonePalette.SlotClassification c = SimBonePalette.classifySlot(name, ints, boneCount);
            assertTrue("row " + i + " ('" + name + "') は解決できるはず: "
                    + (c.ok() ? "" : c.reason()), c.ok());
            int slot = c.slot();
            assertFalse("slot " + slot + " が重複 (" + name + ")", filled[slot]);
            filled[slot] = true;
            resolved[slot] = name;
            distinct++;
        }
        assertEquals("1058 本すべてが distinct な slot を得るはず", 1058, distinct);
        for (boolean f : filled) {
            assertTrue("0..1057 を過不足なく覆うはず", f);
        }
        assertEquals("LeftForeArm2 は slot 661", "LeftForeArm2", resolved[661]);
        assertEquals("LLRight_BackHair3 は slot 470", "LLRight_BackHair3", resolved[470]);
    }
}
