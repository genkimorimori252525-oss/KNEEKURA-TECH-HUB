package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

public final class SimPacketSnapshotSelfTest {
    private enum Mode { CLIENT }

    public static final class Packet {
        public static final String STATIC = "ignore";
        public final double x = 1.25;
        public final int id = 7;
        public final boolean enabled = true;
        public final String molangExpression = "(v.wuqi = 1)";
        public final Mode mode = Mode.CLIENT;
        public final UUID uuid = UUID.fromString("11111111-2222-3333-4444-555555555555");
        public final Object nested = new Object();
        public final int[] array = {1, 2, 3};
        private final String secret = "ignore";
    }

    public static final class LongStringPacket {
        public final String value = "x".repeat(SimPacketSnapshot.MAX_STRING_CHARS + 100);
    }

    public static void main(String[] args) {
        Map<String, Object> m = SimPacketSnapshot.capture(new Packet());
        require(m.size() == 6, "expected exactly six safe scalar fields, got " + m);
        require(Double.valueOf(1.25).equals(m.get("x")), "double field");
        require(Integer.valueOf(7).equals(m.get("id")), "int field");
        require(Boolean.TRUE.equals(m.get("enabled")), "boolean field");
        require("(v.wuqi = 1)".equals(m.get("molangExpression")), "molang expression");
        require("CLIENT".equals(m.get("mode")), "enum field");
        require("11111111-2222-3333-4444-555555555555".equals(m.get("uuid")), "uuid field");
        require(!m.containsKey("STATIC"), "static must be ignored");
        require(!m.containsKey("secret"), "private must be ignored");
        require(!m.containsKey("nested"), "nested object must be ignored");
        require(!m.containsKey("array"), "array must be ignored");

        Map<String, Object> longString = SimPacketSnapshot.capture(new LongStringPacket());
        String value = (String) longString.get("value");
        require(value != null && value.length() == SimPacketSnapshot.MAX_STRING_CHARS, "string cap");

        require(SimPacketSnapshot.capture(null).isEmpty(), "null packet");

        Map<String, Object> semantic = new LinkedHashMap<>();
        semantic.put("molangExpression", "(v.roaming.zui = 1)");
        semantic.put("count", 3);
        semantic.put("nested", new Object());
        semantic.put("missing", null);
        Map<String, Object> sanitized = SimPacketSnapshot.sanitize(semantic);
        require(sanitized.size() == 2, "semantic sanitizer keeps only safe scalars: " + sanitized);
        require("(v.roaming.zui = 1)".equals(sanitized.get("molangExpression")), "semantic string");
        require(Integer.valueOf(3).equals(sanitized.get("count")), "semantic number");
        require(!sanitized.containsKey("nested"), "semantic nested object ignored");
        require(!sanitized.containsKey("missing"), "semantic null ignored");

        System.out.println("SimPacketSnapshotSelfTest OK");
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
}
