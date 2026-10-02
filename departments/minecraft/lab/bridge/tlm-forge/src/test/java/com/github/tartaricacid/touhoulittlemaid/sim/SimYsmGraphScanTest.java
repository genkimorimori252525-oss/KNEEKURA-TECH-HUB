package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.client.SimYsmGraphScan;
import org.junit.Test;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/**
 * {@link SimYsmGraphScan} の検証 (14-04 Task 1)。
 *
 * <p>{@link SimYsmGraphScan#scan} は普通の Java オブジェクトを反射で歩くだけなので、
 * Minecraft を起動せずに合成オブジェクトで検証できる ({@code SimBonePaletteTest} と同じ規約)。
 * 実モデルの cube 数 (6634) と bone 数 (1058) は spike 004 README の実測値をそのまま
 * テストの引数として使う (パラメータであってコードに焼き込まれた定数ではないことの確認も兼ねる)。
 */
public class SimYsmGraphScanTest {

    private static final int CUBE_COUNT = 6634;
    private static final int BONE_COUNT = 1058;

    // =========================================================================
    // findsMultiplesOfCubeCount
    // =========================================================================

    static final class CubeMultiplesOwner {
        float[] a = new float[CUBE_COUNT * 3];
        float[] b = new float[CUBE_COUNT * 24];
        float[] c = new float[500];
    }

    @Test
    public void findsMultiplesOfCubeCount() {
        CubeMultiplesOwner owner = new CubeMultiplesOwner();
        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);

        SimYsmGraphScan.Candidate ca = findByPath(report, "root.a");
        SimYsmGraphScan.Candidate cb = findByPath(report, "root.b");
        assertNotNull("float[6634*3] は候補として見つかるはず", ca);
        assertNotNull("float[6634*24] は候補として見つかるはず", cb);
        assertTrue("6634*3 は cube 数の倍数", ca.size().cubeMultiple());
        assertEquals(3, ca.size().cubeMultipleValue());
        assertTrue("6634*24 は cube 数の倍数", cb.size().cubeMultiple());
        assertEquals(24, cb.size().cubeMultipleValue());

        assertNull("float[500] はどちらのリストにも出ない (floor 未満)", findByPath(report, "root.c"));
    }

    // =========================================================================
    // findsMultiplesOfBoneCount
    // =========================================================================

    static final class BoneMultipleOwner {
        float[] d = new float[BONE_COUNT * 6];
    }

    @Test
    public void findsMultiplesOfBoneCount() {
        BoneMultipleOwner owner = new BoneMultipleOwner();
        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);

        SimYsmGraphScan.Candidate cd = findByPath(report, "root.d");
        assertNotNull("1058*6 は候補として見つかるはず", cd);
        assertTrue("1058*6 は bone 数の倍数", cd.size().boneMultiple());
        assertEquals(6, cd.size().boneMultipleValue());
        assertFalse("1058*6 は cube 数の倍数ではない", cd.size().cubeMultiple());
    }

    // =========================================================================
    // reportsCollectionsToo
    // =========================================================================

    static final class CubeLike {
        float x;
        float y;
        float z;
    }

    static final class CollectionOwner {
        List<CubeLike> cubes = new ArrayList<>();
        Map<Integer, CubeLike> bones = new LinkedHashMap<>();
    }

    @Test
    public void reportsCollectionsToo() {
        CollectionOwner owner = new CollectionOwner();
        for (int i = 0; i < CUBE_COUNT; i++) {
            owner.cubes.add(new CubeLike());
        }
        for (int i = 0; i < BONE_COUNT; i++) {
            owner.bones.put(i, new CubeLike());
        }

        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);

        SimYsmGraphScan.Candidate list = findByPath(report, "root.cubes");
        SimYsmGraphScan.Candidate map = findByPath(report, "root.bones");
        assertNotNull("6634 要素の List は候補になるはず (データが配列でなくオブジェクトかもしれないため)", list);
        assertNotNull("1058 要素の Map は候補になるはず", map);
        assertNotNull("List 候補は最初の要素のクラスを持つ", list.elementInfo());
        assertEquals(CubeLike.class.getName(), list.elementInfo().className());
        assertNotNull("Map 候補も最初の要素のクラスを持つ", map.elementInfo());
        assertEquals(CubeLike.class.getName(), map.elementInfo().className());
        assertTrue("List 候補の element field 一覧に x/y/z が含まれる",
                list.elementInfo().fieldNames().stream().anyMatch(f -> f.startsWith("x:")));
    }

    // =========================================================================
    // reportsLargeNonMultiplesSeparately
    // =========================================================================

    static final class LargeNonMultipleOwner {
        float[] weird = new float[100000];
    }

    @Test
    public void reportsLargeNonMultiplesSeparately() {
        LargeNonMultipleOwner owner = new LargeNonMultipleOwner();
        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);

        assertNull("倍数でないので exactMultiples には出ない", findByPath(report.exactMultiples(), "root.weird"));
        SimYsmGraphScan.Candidate c = findByPath(report.largeNonMultiples(), "root.weird");
        assertNotNull("大きいのに割り切れない候補は別区画に残る", c);
        assertEquals(100000, c.length());
        assertEquals(100000 % CUBE_COUNT, c.size().remainderVsCube());
        assertEquals(100000 % BONE_COUNT, c.size().remainderVsBone());
        assertFalse(c.size().exactMultiple());
    }

    // =========================================================================
    // survivesCyclesAndDepth
    // =========================================================================

    static final class ChainNode {
        ChainNode next;
    }

    @Test
    public void survivesCyclesAndDepth() {
        // 20 本のチェーンを作り、末尾を先頭へ戻して循環させる。深さ上限より長い。
        ChainNode root = new ChainNode();
        ChainNode cur = root;
        List<ChainNode> all = new ArrayList<>();
        all.add(root);
        for (int i = 0; i < 20; i++) {
            ChainNode next = new ChainNode();
            cur.next = next;
            cur = next;
            all.add(next);
        }
        cur.next = root; // cycle

        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(root, CUBE_COUNT, BONE_COUNT);

        assertNotNull("循環があっても止まって結果を返す", report);
        assertTrue("深さ上限を超えて辿っていない", report.depthReached() <= 6);
        assertTrue("循環で無限に膨らんでいない", report.visited() <= 10);
    }

    // =========================================================================
    // neverInvokesMethods
    // =========================================================================

    static final class GetterFlagOwner {
        boolean flagCalled = false;
        int dummy = 42;

        // 反射で呼ばれたら flagCalled を立てる「getter」。scan() はこれを一切呼んではいけない。
        Object getSomething() {
            flagCalled = true;
            return "x";
        }
    }

    @Test
    public void neverInvokesMethods() {
        GetterFlagOwner owner = new GetterFlagOwner();
        SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);
        assertFalse("フィールドだけを読み、メソッドは一切呼ばない", owner.flagCalled);
    }

    // =========================================================================
    // emptyGraphYieldsNegativeReport
    // =========================================================================

    static final class BoringOwner {
        String name = "no arrays or collections here";
        int number = 1;
    }

    @Test
    public void emptyGraphYieldsNegativeReport() {
        BoringOwner owner = new BoringOwner();
        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);

        assertNotNull(report);
        assertTrue("候補が1件も無いことが明示される", report.negative());
        assertTrue("root は少なくとも1件訪問済み", report.visited() >= 1);
        assertEquals(0, report.depthReached());
        assertTrue(report.exactMultiples().isEmpty());
        assertTrue(report.largeNonMultiples().isEmpty());
    }

    // =========================================================================
    // nestedContainersAreTraversed
    // =========================================================================

    static final class DeepPayload {
        float[] values = new float[CUBE_COUNT * 3];
    }

    static final class NestedContainerOwner {
        List<Object> outer = new ArrayList<>();
    }

    @Test
    public void nestedContainersAreTraversed() {
        NestedContainerOwner owner = new NestedContainerOwner();
        Map<String, Object> inner = new LinkedHashMap<>();
        Object[] array = new Object[]{null, new DeepPayload()};
        inner.put("payload", array);
        owner.outer.add(inner);

        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);
        SimYsmGraphScan.Candidate candidate = findByPath(
                report, "root.outer[0].value[0][1].values");

        assertNotNull("small List -> Map -> object[] の奥まで辿る", candidate);
        assertTrue(candidate.size().cubeMultiple());
        assertEquals(3, candidate.size().cubeMultipleValue());
        assertTrue("小さいcontainerだけならscanは完全", report.complete());
    }

    // =========================================================================
    // collectionElementInfoSkipsLeadingNull
    // =========================================================================

    static final class LeadingNullOwner {
        List<CubeLike> values = new ArrayList<>();
    }

    @Test
    public void collectionElementInfoSkipsLeadingNull() {
        LeadingNullOwner owner = new LeadingNullOwner();
        owner.values.add(null);
        owner.values.add(new CubeLike());
        while (owner.values.size() < BONE_COUNT) {
            owner.values.add(null);
        }

        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);
        SimYsmGraphScan.Candidate candidate = findByPath(report, "root.values");
        assertNotNull(candidate);
        assertNotNull("先頭nullでも次のnon-null要素の形を拾う", candidate.elementInfo());
        assertEquals(CubeLike.class.getName(), candidate.elementInfo().className());
    }

    // =========================================================================
    // truncatedContainerMakesNegativeInconclusive
    // =========================================================================

    static final class SmallLeaf {
        int value = 1;
    }

    static final class TruncatedOwner {
        List<Object> values = new ArrayList<>();
    }

    @Test
    public void truncatedContainerMakesNegativeInconclusive() {
        TruncatedOwner owner = new TruncatedOwner();
        for (int i = 0; i < 65; i++) {
            owner.values.add(new SmallLeaf());
        }

        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(owner, CUBE_COUNT, BONE_COUNT);
        assertTrue("candidate shapeは無い", report.negative());
        assertEquals(1, report.truncatedContainers());
        assertFalse("containerを切ったscanは完全ではない", report.complete());
        assertFalse("未探索があるnegativeを不在確定にしない", report.conclusiveNegative());
    }

    // =========================================================================

    private static SimYsmGraphScan.Candidate findByPath(SimYsmGraphScan.Report report, String path) {
        SimYsmGraphScan.Candidate c = findByPath(report.exactMultiples(), path);
        if (c != null) {
            return c;
        }
        return findByPath(report.largeNonMultiples(), path);
    }

    private static SimYsmGraphScan.Candidate findByPath(List<SimYsmGraphScan.Candidate> list, String path) {
        for (SimYsmGraphScan.Candidate c : list) {
            if (c.path().equals(path)) {
                return c;
            }
        }
        return null;
    }
}
