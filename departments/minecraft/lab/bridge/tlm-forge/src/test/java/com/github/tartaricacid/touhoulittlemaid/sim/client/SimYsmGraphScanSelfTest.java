package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Standalone JDK-only regression for the YSM graph walker. */
public final class SimYsmGraphScanSelfTest {
    private static final int CUBES = 120;
    private static final int BONES = 20;

    static final class Payload {
        float[] data = new float[CUBES * 3];
    }

    static final class Root {
        List<Object> outer = new ArrayList<>();
    }

    static final class Leaf {
        int x = 1;
    }

    public static void main(String[] args) {
        Root root = new Root();
        Map<String, Object> inner = new LinkedHashMap<>();
        inner.put("payload", new Object[]{null, new Payload()});
        root.outer.add(inner);

        SimYsmGraphScan.Report nested = SimYsmGraphScan.scan(root, CUBES, BONES);
        require(find(nested, "root.outer[0].value[0][1].data") != null,
                "nested List/Map/object[] payload was not traversed");
        require(nested.complete(), "small nested graph should be complete");

        Root truncatedRoot = new Root();
        for (int i = 0; i < 65; i++) truncatedRoot.outer.add(new Leaf());
        SimYsmGraphScan.Report truncated = SimYsmGraphScan.scan(truncatedRoot, 1000, 1000);
        require(truncated.negative(), "small leaves should produce no candidates");
        require(truncated.truncatedContainers() == 1, "expected one truncated container");
        require(!truncated.complete(), "truncated scan must not be complete");
        require(!truncated.conclusiveNegative(), "truncated negative must not be conclusive");

        System.out.println("SimYsmGraphScanSelfTest OK");
    }

    private static SimYsmGraphScan.Candidate find(SimYsmGraphScan.Report report, String path) {
        for (SimYsmGraphScan.Candidate c : report.exactMultiples()) if (c.path().equals(path)) return c;
        for (SimYsmGraphScan.Candidate c : report.largeNonMultiples()) if (c.path().equals(path)) return c;
        return null;
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
}
