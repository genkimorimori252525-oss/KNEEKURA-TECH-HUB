package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Standalone JDK-only regression for the YSM scalar snapshot probe. */
public final class SimYsmScalarProbeSelfTest {
    static final class DeepState {
        double value = 4.5d;
    }

    static final class Root {
        boolean getterCalled = false;
        int count = 7;
        String name = "root";
        Map<String, Object> vars = new LinkedHashMap<>();
        List<Object> nested = new ArrayList<>();

        Object getDangerousState() {
            getterCalled = true;
            return new Object();
        }
    }

    static final class EmptyLeaf {}

    static final class TruncatedRoot {
        List<Object> values = new ArrayList<>();
    }

    public static void main(String[] args) {
        Root root = new Root();
        root.vars.put("variable.wuqi", 0.0f);
        root.vars.put("note", "unchanged");
        String longKey = "x".repeat(SimYsmScalarProbe.MAX_TEXT_CHARS + 20);
        root.vars.put(longKey, 3);

        Map<String, Object> inner = new LinkedHashMap<>();
        inner.put("payload", new Object[]{null, new DeepState()});
        root.nested.add(inner);

        SimYsmScalarProbe.Snapshot before = SimYsmScalarProbe.snapshot(root);
        require(findField(before, "root.count", "7") != null, "field scalar was not captured");
        SimYsmScalarProbe.Scalar wuqi = findMap(before, "root.vars", "variable.wuqi");
        require(wuqi != null, "Map<String, scalar> entry was not captured");
        require("0.0".equals(wuqi.value()), "unexpected wuqi value: " + wuqi.value());
        require(wuqi.hasExactContainerKey(), "short variable key should be exact");
        SimYsmScalarProbe.Scalar clipped = findTruncatedMap(before, "root.vars");
        require(clipped != null, "long map key should still be visible as truncated discovery data");
        require(!clipped.hasExactContainerKey(), "truncated map key must not count as exact identity");
        require(!clipped.comparable(), "truncated map key must be excluded from stable diff evidence");
        require(findField(before, "root.nested[0].value[0][1].value", "4.5") != null,
                "nested List/Map/object[] scalar was not traversed");
        require(before.complete(), "small graph should be complete");
        require(!root.getterCalled, "probe invoked an unknown method");

        root.vars.put("variable.wuqi", 1.0f);
        root.vars.put(longKey, 4);
        SimYsmScalarProbe.Snapshot after = SimYsmScalarProbe.snapshot(root);
        List<SimYsmScalarProbe.Change> changes = SimYsmScalarProbe.diff(before, after);
        require(changes.size() == 1, "expected exactly one stable scalar change, got " + changes.size());
        require("variable.wuqi".equals(changes.get(0).after().containerKey()),
                "changed scalar should be variable.wuqi");
        require("0.0".equals(changes.get(0).before().value())
                        && "1.0".equals(changes.get(0).after().value()),
                "toggle values were not preserved");

        TruncatedRoot truncatedRoot = new TruncatedRoot();
        for (int i = 0; i < 65; i++) {
            truncatedRoot.values.add(new EmptyLeaf());
        }
        SimYsmScalarProbe.Snapshot truncated = SimYsmScalarProbe.snapshot(truncatedRoot);
        require(truncated.negative(), "empty leaves should yield no scalar candidates");
        require(truncated.truncatedContainers() == 1, "expected one truncated container");
        require(!truncated.complete(), "truncated scan must not be complete");
        require(!truncated.conclusiveNegative(), "incomplete negative must not be conclusive");

        System.out.println("SimYsmScalarProbeSelfTest OK");
    }

    private static SimYsmScalarProbe.Scalar findField(
            SimYsmScalarProbe.Snapshot snapshot, String path, String value) {
        for (SimYsmScalarProbe.Scalar scalar : snapshot.scalars()) {
            if (path.equals(scalar.path()) && value.equals(scalar.value())) {
                return scalar;
            }
        }
        return null;
    }

    private static SimYsmScalarProbe.Scalar findMap(
            SimYsmScalarProbe.Snapshot snapshot, String path, String key) {
        for (SimYsmScalarProbe.Scalar scalar : snapshot.scalars()) {
            if (path.equals(scalar.path()) && key.equals(scalar.containerKey())) {
                return scalar;
            }
        }
        return null;
    }

    private static SimYsmScalarProbe.Scalar findTruncatedMap(
            SimYsmScalarProbe.Snapshot snapshot, String path) {
        for (SimYsmScalarProbe.Scalar scalar : snapshot.scalars()) {
            if (path.equals(scalar.path()) && scalar.containerKeyTruncated()) {
                return scalar;
            }
        }
        return null;
    }

    private static void require(boolean ok, String message) {
        if (!ok) {
            throw new AssertionError(message);
        }
    }
}
