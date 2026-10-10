package org.kneekura.sporeobserver.core;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Owned, bounded JSONL output. No Minecraft/Forge/Spore dependency. */
public final class TraceSink implements AutoCloseable {
    public static final long MAX_BYTES = 8_000_000;
    public static final int MAX_EVENTS = 49_998;
    private final BufferedWriter output;
    private final String runId, scenario, worldId, dimension;
    private long seq = 0, lastTick = -1, bytes = 0;
    private boolean closed;

    public TraceSink(Path file, Map<String, Object> meta) throws IOException {
        Objects.requireNonNull(file); Objects.requireNonNull(meta);
        require(meta.get("ch").equals("spore_meta"), "meta channel");
        for (String field : List.of("run_id", "scenario", "world_id", "dimension")) {
            require(meta.get(field) instanceof String && !((String) meta.get(field)).isBlank(), "missing " + field);
        }
        this.runId = (String)meta.get("run_id");
        this.scenario = (String)meta.get("scenario");
        this.worldId = (String)meta.get("world_id");
        this.dimension = (String)meta.get("dimension");
        this.output = Files.newBufferedWriter(file, StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        try { write(mapToJson(meta) + "\n"); }
        catch (Exception failure) { output.close(); throw failure; }
    }

    public synchronized void event(long tick, String actualDimension, String kind, Map<String, ?> data) throws IOException {
        require(!closed, "event after close");
        require(tick >= lastTick && tick >= 0, "ticks must not decrease");
        require(actualDimension.equals(dimension) || dimension.equals("MULTI_DIMENSION"), "dimension mismatch");
        require(kind != null && kind.length() <= 64 && !kind.isBlank(), "invalid event kind");
        String payload = mapToJson(data);
        require(payload.getBytes(StandardCharsets.UTF_8).length <= 4096, "payload too large");
        require(seq < MAX_EVENTS, "trace event limit");
        String row = mapToJson(Map.of("ch", "spore_observation", "run_id", runId,
                "scenario", scenario, "world_id", worldId, "dimension", actualDimension,
                "seq", seq + 1, "tick", tick, "kind", kind, "data", data)) + "\n";
        require(bytes + row.getBytes(StandardCharsets.UTF_8).length + 512 < MAX_BYTES, "trace byte limit");
        write(row);
        lastTick = tick;
        seq++;
    }

    public synchronized long eventCount() { return seq; }

    public synchronized void finish(String reason) throws IOException {
        if (closed) return;
        require(List.of("completed", "aborted", "timeout", "error").contains(reason), "end reason");
        String end = mapToJson(Map.of("ch", "spore_end", "run_id", runId,
                "scenario", scenario, "reason", reason, "observation_count", seq)) + "\n";
        try { write(end); } finally { closed = true; output.close(); }
    }

    private void write(String s) throws IOException {
        output.write(s);
        output.flush();
        bytes += s.getBytes(StandardCharsets.UTF_8).length;
    }

    @Override public void close() throws IOException { finish("aborted"); }

    public static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }

    /** Valid JSON for owned scalar/array/object values only; fail closed for unsupported data. */
    public static String mapToJson(Object object) {
        StringBuilder sb = new StringBuilder();
        append(sb, object, 0);
        return sb.toString();
    }
    private static void append(StringBuilder sb, Object o, int depth) {
        require(depth <= 8, "JSON nesting too deep");
        if (o == null) { sb.append("null"); return; }
        if (o instanceof String s) { quote(sb,s); return; }
        if (o instanceof Boolean b) { sb.append(b); return; }
        if (o instanceof Number n) {
            double d=n.doubleValue();
            require(Double.isFinite(d), "non-finite number");
            sb.append(n);
            return;
        }
        if (o instanceof Map<?,?> m) {
            sb.append('{'); boolean first=true;
            for (var pair : m.entrySet()) {
                require(pair.getKey() instanceof String, "non-string JSON key");
                if (!first) sb.append(','); first=false;
                quote(sb,(String)pair.getKey()); sb.append(':'); append(sb,pair.getValue(),depth+1);
            }
            sb.append('}'); return;
        }
        if (o instanceof List<?> li) {
            sb.append('['); boolean first=true;
            for (Object v:li) { if (!first) sb.append(','); first=false; append(sb,v,depth+1); }
            sb.append(']'); return;
        }
        throw new IllegalArgumentException("unsupported JSON value " + o.getClass().getName());
    }
    private static void quote(StringBuilder sb, String s) {
        sb.append('"');
        for (int i=0; i<s.length(); i++) {
            char c=s.charAt(i);
            switch(c) {
                case '"' -> sb.append("\\\"");
                case '\\' -> sb.append("\\\\");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                case '\b' -> sb.append("\\b");
                case '\f' -> sb.append("\\f");
                default -> { if (c < 0x20) sb.append(String.format("\\u%04x", (int)c)); else sb.append(c); }
            }
        }
        sb.append('"');
    }
}
