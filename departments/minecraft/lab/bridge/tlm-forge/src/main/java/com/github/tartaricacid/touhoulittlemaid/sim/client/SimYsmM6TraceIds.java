package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Pure-JDK parser for exact M3 -> pre-dispatch diagnostic trace identities. */
public final class SimYsmM6TraceIds {
    private static final int MAX_IDS = 32;

    private SimYsmM6TraceIds() {}

    /**
     * Parse a comma-separated scalar string of positive unique trace IDs.
     *
     * <p>Malformed, duplicate, empty or over-budget input fails closed as an empty list.
     */
    public static List<Long> parse(String raw) {
        if (raw == null || raw.isBlank()) {
            return List.of();
        }
        String[] parts = raw.split(",", -1);
        if (parts.length == 0 || parts.length > MAX_IDS) {
            return List.of();
        }

        List<Long> out = new ArrayList<>(parts.length);
        Set<Long> seen = new HashSet<>();
        for (String part : parts) {
            String value = part.trim();
            if (value.isEmpty()) {
                return List.of();
            }
            final long id;
            try {
                id = Long.parseLong(value);
            } catch (NumberFormatException ignored) {
                return List.of();
            }
            if (id <= 0L || !seen.add(id)) {
                return List.of();
            }
            out.add(id);
        }
        return List.copyOf(out);
    }

    /** Accept only exact positive integral Number payloads. */
    public static Long positiveLong(Object value) {
        if (!(value instanceof Number n)) {
            return null;
        }
        if (n instanceof Byte || n instanceof Short || n instanceof Integer || n instanceof Long) {
            long id = n.longValue();
            return id > 0L ? id : null;
        }
        double d = n.doubleValue();
        if (!Double.isFinite(d)
                || d <= 0.0d
                || d > Long.MAX_VALUE
                || Math.rint(d) != d) {
            return null;
        }
        long id = (long) d;
        return id > 0L ? id : null;
    }

    public static String canonical(List<Long> ids) {
        if (ids == null || ids.isEmpty() || ids.size() > MAX_IDS) {
            return "";
        }
        StringBuilder out = new StringBuilder();
        Set<Long> seen = new HashSet<>();
        for (Long id : ids) {
            if (id == null || id <= 0L || !seen.add(id)) {
                return "";
            }
            if (!out.isEmpty()) out.append(',');
            out.append(id);
        }
        return out.toString();
    }
}
