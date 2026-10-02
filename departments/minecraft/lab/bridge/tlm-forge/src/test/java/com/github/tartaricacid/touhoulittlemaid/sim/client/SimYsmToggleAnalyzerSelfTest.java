package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Standalone JDK-only regression for controlled YSM scalar toggle analysis. */
public final class SimYsmToggleAnalyzerSelfTest {
    static final class Root {
        int constant = 9;
        Map<String, Object> vars = new LinkedHashMap<>();
    }

    public static void main(String[] args) {
        Root root = new Root();
        String longKey = "z".repeat(SimYsmScalarProbe.MAX_TEXT_CHARS + 50);
        List<SimYsmScalarProbe.Snapshot> snapshots = new ArrayList<>();

        int[] sequence = {0, 1, 0, 1};
        for (int value : sequence) {
            root.vars.put("variable.wuqi", (float) value);
            root.vars.put("mystery", (double) value);
            root.vars.put(longKey, value);
            snapshots.add(SimYsmScalarProbe.snapshot(root));
        }

        SimYsmToggleAnalyzer.Analysis analysis = SimYsmToggleAnalyzer.analyze("wuqi", snapshots);
        require(analysis.sequenceObserved(), "controlled sequence should produce candidates");
        require(analysis.candidates().size() == 2,
                "expected exact + mystery candidates only, got " + analysis.candidates().size());
        require(analysis.e2Count() == 1, "exact variable key should produce exactly one E2");
        require(analysis.e1Count() == 1, "mystery correlation should remain E1");

        require(SimYsmToggleAnalyzer.exactNumericMatches(snapshots.get(1), "wuqi", 1.0d).size() == 1,
                "formal verifier helper must find exactly one exact wuqi=1 candidate");
        require(SimYsmToggleAnalyzer.exactNumericMatches(snapshots.get(1), "wuqi", 0.0d).isEmpty(),
                "formal verifier helper must not accept wrong expected value");

        SimYsmToggleAnalyzer.Candidate exact = analysis.candidates().get(0);
        require(exact.exactVariableIdentity(), "E2 candidate should sort first");
        require("variable.wuqi".equals(exact.containerKey()), "wrong exact identity candidate");
        require(List.of("0.0", "1.0", "0.0", "1.0").equals(exact.observedValues()),
                "exact candidate did not preserve the toggle sequence");

        SimYsmToggleAnalyzer.Analysis invalid = SimYsmToggleAnalyzer.analyze("wuqi;bad", snapshots);
        require(!invalid.sequenceObserved(), "invalid variable syntax must fail closed");

        List<SimYsmScalarProbe.Snapshot> missing = new ArrayList<>(snapshots);
        Root empty = new Root();
        missing.set(2, SimYsmScalarProbe.snapshot(empty));
        SimYsmToggleAnalyzer.Analysis incompleteIdentity = SimYsmToggleAnalyzer.analyze("wuqi", missing);
        require(!incompleteIdentity.sequenceObserved(),
                "candidate missing from one snapshot must not be correlated by guess");

        System.out.println("SimYsmToggleAnalyzerSelfTest OK");
    }

    private static void require(boolean ok, String message) {
        if (!ok) {
            throw new AssertionError(message);
        }
    }
}
