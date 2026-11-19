package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Pure-JDK analyzer for a controlled 0 -> 1 -> 0 -> 1 YSM scalar probe.
 *
 * <p>This class only recognizes correlation. It does not emit runtime semantic evidence and does not
 * promote a candidate to M6. A caller must still connect the discovered identity to the real M0-M5
 * packet/handler/command chain.
 */
public final class SimYsmToggleAnalyzer {
    private static final double[] EXPECTED = {0.0d, 1.0d, 0.0d, 1.0d};

    private SimYsmToggleAnalyzer() {}

    public record Candidate(
            String stableIdentity,
            String path,
            String ownerClass,
            String fieldName,
            String containerKey,
            String type,
            List<String> observedValues,
            boolean exactVariableIdentity,
            String evidenceLevel
    ) {}

    public record Analysis(
            String variable,
            List<Candidate> candidates,
            int e1Count,
            int e2Count,
            boolean sequenceObserved
    ) {}

    public static Analysis analyze(
            String variable,
            List<SimYsmScalarProbe.Snapshot> snapshots) {
        String bare = normalizeVariable(variable);
        if (bare == null || snapshots == null || snapshots.size() != EXPECTED.length) {
            return new Analysis(variable == null ? "" : variable, List.of(), 0, 0, false);
        }

        List<Map<String, SimYsmScalarProbe.Scalar>> indexed = new ArrayList<>();
        for (SimYsmScalarProbe.Snapshot snapshot : snapshots) {
            if (snapshot == null) {
                return new Analysis(bare, List.of(), 0, 0, false);
            }
            indexed.add(index(snapshot));
        }

        List<Candidate> candidates = new ArrayList<>();
        Map<String, SimYsmScalarProbe.Scalar> first = indexed.get(0);
        for (Map.Entry<String, SimYsmScalarProbe.Scalar> entry : first.entrySet()) {
            String identity = entry.getKey();
            SimYsmScalarProbe.Scalar exemplar = entry.getValue();
            List<String> values = new ArrayList<>(EXPECTED.length);
            boolean matches = true;

            for (int i = 0; i < EXPECTED.length; i++) {
                SimYsmScalarProbe.Scalar scalar = indexed.get(i).get(identity);
                if (scalar == null || !exemplar.type().equals(scalar.type())) {
                    matches = false;
                    break;
                }
                Double numeric = numericValue(scalar);
                if (numeric == null || Double.compare(numeric, EXPECTED[i]) != 0) {
                    matches = false;
                    break;
                }
                values.add(scalar.value());
            }

            if (!matches) {
                continue;
            }

            boolean exact = exactIdentity(exemplar, bare);
            candidates.add(new Candidate(
                    identity,
                    exemplar.path(),
                    exemplar.ownerClass(),
                    exemplar.fieldName(),
                    exemplar.containerKey(),
                    exemplar.type(),
                    List.copyOf(values),
                    exact,
                    exact ? "E2" : "E1"));
        }

        candidates.sort(Comparator
                .comparing((Candidate c) -> !c.exactVariableIdentity())
                .thenComparing(Candidate::stableIdentity));

        int e2 = 0;
        for (Candidate candidate : candidates) {
            if (candidate.exactVariableIdentity()) {
                e2++;
            }
        }
        int e1 = candidates.size() - e2;
        return new Analysis(
                bare,
                List.copyOf(candidates),
                e1,
                e2,
                !candidates.isEmpty());
    }

    private static Map<String, SimYsmScalarProbe.Scalar> index(
            SimYsmScalarProbe.Snapshot snapshot) {
        Map<String, SimYsmScalarProbe.Scalar> out = new LinkedHashMap<>();
        for (SimYsmScalarProbe.Scalar scalar : snapshot.scalars()) {
            if (scalar != null && scalar.comparable()) {
                out.putIfAbsent(scalar.stableIdentity(), scalar);
            }
        }
        return out;
    }

    static boolean exactIdentity(SimYsmScalarProbe.Scalar scalar, String bare) {
        Set<String> accepted = Set.of(bare, "v." + bare, "variable." + bare);
        String key = scalar.containerKey();
        if (key != null && accepted.contains(key)) {
            return true;
        }
        return bare.equals(scalar.fieldName());
    }

    static Double numericValue(SimYsmScalarProbe.Scalar scalar) {
        String type = scalar.type();
        if (!(Byte.class.getName().equals(type)
                || Short.class.getName().equals(type)
                || Integer.class.getName().equals(type)
                || Long.class.getName().equals(type)
                || Float.class.getName().equals(type)
                || Double.class.getName().equals(type))) {
            return null;
        }
        try {
            return Double.parseDouble(scalar.value());
        } catch (NumberFormatException ignored) {
            return null;
        }
    }

    /**
     * Unique exact-identity candidates matching one expected numeric post-command value.
     * The caller must fail closed when this returns anything other than one element.
     */
    static List<SimYsmScalarProbe.Scalar> exactNumericCandidates(
            SimYsmScalarProbe.Snapshot snapshot, String variable) {
        String bare = normalizeVariable(variable);
        if (snapshot == null || bare == null) {
            return List.of();
        }
        List<SimYsmScalarProbe.Scalar> matches = new ArrayList<>();
        for (SimYsmScalarProbe.Scalar scalar : snapshot.scalars()) {
            if (scalar == null || !scalar.comparable() || !exactIdentity(scalar, bare)) {
                continue;
            }
            if (numericValue(scalar) != null) {
                matches.add(scalar);
            }
        }
        return List.copyOf(matches);
    }

    static List<SimYsmScalarProbe.Scalar> exactNumericMatches(
            SimYsmScalarProbe.Snapshot snapshot, String variable, double expected) {
        if (!Double.isFinite(expected)) {
            return List.of();
        }
        List<SimYsmScalarProbe.Scalar> matches = new ArrayList<>();
        for (SimYsmScalarProbe.Scalar scalar : exactNumericCandidates(snapshot, variable)) {
            Double value = numericValue(scalar);
            if (value != null && Double.compare(value, expected) == 0) {
                matches.add(scalar);
            }
        }
        return List.copyOf(matches);
    }

    static String normalizeVariable(String variable) {
        if (variable == null) {
            return null;
        }
        String value = variable.trim();
        if (value.startsWith("variable.")) {
            value = value.substring("variable.".length());
        } else if (value.startsWith("v.")) {
            value = value.substring(2);
        }
        if (!value.matches("[A-Za-z_][A-Za-z0-9_]*")) {
            return null;
        }
        return value;
    }
}
