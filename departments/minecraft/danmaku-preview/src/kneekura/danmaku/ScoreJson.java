package kneekura.danmaku;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Strict Score JSON v2 codec. Keeps Pattern JSON v1 untouched. */
public final class ScoreJson {
    private static final Set<String> ROOT_KEYS = Set.of("schemaVersion", "tickRate", "durationTicks", "tracks");
    private static final Set<String> TRACK_KEYS = Set.of("name", "startTick", "endTick", "hue", "radius",
        "pattern", "bullets", "speed", "intervalTicks", "fanAngleDeg", "rotationDegPerSecond",
        "elevationDeg", "lifetimeTicks");

    public static String write(Score.Config score) {
        StringBuilder b = new StringBuilder();
        b.append("{\n  \"schemaVersion\": 2,\n  \"tickRate\": 20,\n  \"durationTicks\": ")
            .append(score.durationTicks()).append(",\n  \"tracks\": [\n");
        for (int i = 0; i < score.tracks().size(); i++) {
            Score.Track t = score.tracks().get(i);
            Pattern.Config p = t.pattern();
            b.append("    {\n")
             .append("      \"name\": \"").append(t.name()).append("\",\n")
             .append("      \"startTick\": ").append(t.startTick()).append(",\n")
             .append("      \"endTick\": ").append(t.endTick()).append(",\n")
             .append("      \"hue\": ").append(Double.toString(t.hue())).append(",\n")
             .append("      \"radius\": ").append(Double.toString(t.radius())).append(",\n")
             .append("      \"pattern\": \"").append(p.pattern()).append("\",\n")
             .append("      \"bullets\": ").append(p.bullets()).append(",\n")
             .append("      \"speed\": ").append(Double.toString(p.speed())).append(",\n")
             .append("      \"intervalTicks\": ").append(p.intervalTicks()).append(",\n")
             .append("      \"fanAngleDeg\": ").append(Double.toString(p.fanAngleDeg())).append(",\n")
             .append("      \"rotationDegPerSecond\": ").append(Double.toString(p.rotationDegPerSecond())).append(",\n")
             .append("      \"elevationDeg\": ").append(Double.toString(p.elevationDeg())).append(",\n")
             .append("      \"lifetimeTicks\": ").append(p.lifetimeTicks()).append("\n")
             .append("    }");
            if (i + 1 < score.tracks().size()) b.append(',');
            b.append('\n');
        }
        return b.append("  ]\n}\n").toString();
    }

    public static Score.Config read(String json) {
        if (json == null || json.length() > 262144) throw new IllegalArgumentException("Score JSON size limit: 256KiB");
        Object rootValue = new Parser(json).parse();
        Map<String, Object> root = object(rootValue, "root");
        exactKeys(root, ROOT_KEYS, "root");
        if (integer(root, "schemaVersion") != 2) throw new IllegalArgumentException("schemaVersion must be 2");
        if (integer(root, "tickRate") != 20) throw new IllegalArgumentException("tickRate must be 20");
        int duration = integer(root, "durationTicks");
        Object tracksValue = root.get("tracks");
        if (!(tracksValue instanceof List<?> rawTracks)) throw new IllegalArgumentException("tracks must be an array");
        var tracks = new ArrayList<Score.Track>();
        for (Object value : rawTracks) {
            Map<String, Object> t = object(value, "track");
            exactKeys(t, TRACK_KEYS, "track");
            String name = string(t, "name");
            int start = integer(t, "startTick"), end = integer(t, "endTick");
            double hue = number(t, "hue"), radius = number(t, "radius");
            Pattern.Kind kind;
            try { kind = Pattern.Kind.valueOf(string(t, "pattern")); }
            catch (IllegalArgumentException ex) { throw new IllegalArgumentException("unknown pattern", ex); }
            int bullets = integer(t, "bullets"), interval = integer(t, "intervalTicks"), lifetime = integer(t, "lifetimeTicks");
            double speed = number(t, "speed"), fan = number(t, "fanAngleDeg"),
                rotation = number(t, "rotationDegPerSecond"), elevation = number(t, "elevationDeg");
            tracks.add(new Score.Track(name, start, end,
                new Pattern.Config(kind, bullets, speed, interval, fan, rotation, elevation, lifetime, end - start),
                hue, radius));
        }
        return new Score.Config(duration, tracks);
    }

    private static Map<String, Object> object(Object value, String label) {
        if (!(value instanceof Map<?, ?> map)) throw new IllegalArgumentException(label + " must be an object");
        var out = new LinkedHashMap<String, Object>();
        for (var entry : map.entrySet()) {
            if (!(entry.getKey() instanceof String key)) throw new IllegalArgumentException("object key must be string");
            out.put(key, entry.getValue());
        }
        return out;
    }
    private static void exactKeys(Map<String, Object> map, Set<String> keys, String label) {
        if (!map.keySet().equals(keys)) throw new IllegalArgumentException(label + " fields mismatch: " + map.keySet());
    }
    private static String string(Map<String, Object> map, String key) {
        Object v = map.get(key); if (!(v instanceof String s)) throw new IllegalArgumentException(key + " must be string"); return s;
    }
    private static double number(Map<String, Object> map, String key) {
        Object v = map.get(key); if (!(v instanceof Number n)) throw new IllegalArgumentException(key + " must be number");
        double d = n.doubleValue(); if (!Double.isFinite(d)) throw new IllegalArgumentException(key + " must be finite"); return d;
    }
    private static int integer(Map<String, Object> map, String key) {
        double d = number(map, key);
        if (d != Math.rint(d) || d < Integer.MIN_VALUE || d > Integer.MAX_VALUE)
            throw new IllegalArgumentException(key + " must be integer");
        return (int) d;
    }

    private static final class Parser {
        private final String s; private int p;
        Parser(String s) { this.s = s; }
        Object parse() {
            Object v = value(); ws();
            if (p != s.length()) throw error("trailing input");
            return v;
        }
        private Object value() {
            ws(); if (p >= s.length()) throw error("unexpected end");
            char c = s.charAt(p);
            if (c == '{') return object();
            if (c == '[') return array();
            if (c == '"') return string();
            if (c == '-' || Character.isDigit(c)) return number();
            throw error("unsupported JSON value");
        }
        private Map<String,Object> object() {
            expect('{'); ws(); var out = new LinkedHashMap<String,Object>();
            if (peek('}')) { p++; return out; }
            while (true) {
                String k = string(); ws(); expect(':'); Object v = value();
                if (out.put(k, v) != null) throw error("duplicate key: " + k);
                ws(); if (peek('}')) { p++; return out; } expect(',');
            }
        }
        private List<Object> array() {
            expect('['); ws(); var out = new ArrayList<Object>();
            if (peek(']')) { p++; return out; }
            while (true) {
                out.add(value()); ws();
                if (peek(']')) { p++; return out; } expect(',');
            }
        }
        private String string() {
            ws(); expect('"'); StringBuilder b = new StringBuilder();
            while (p < s.length()) {
                char c = s.charAt(p++);
                if (c == '"') return b.toString();
                if (c == '\\') {
                    if (p >= s.length()) throw error("bad escape");
                    char e = s.charAt(p++);
                    switch (e) {
                        case '"', '\\', '/' -> b.append(e);
                        case 'b' -> b.append('\b'); case 'f' -> b.append('\f'); case 'n' -> b.append('\n');
                        case 'r' -> b.append('\r'); case 't' -> b.append('\t');
                        case 'u' -> {
                            if (p + 4 > s.length()) throw error("bad unicode escape");
                            try { b.append((char) Integer.parseInt(s.substring(p, p + 4), 16)); }
                            catch (NumberFormatException ex) { throw error("bad unicode escape"); }
                            p += 4;
                        }
                        default -> throw error("bad escape");
                    }
                } else {
                    if (c < 0x20) throw error("control char in string");
                    b.append(c);
                }
            }
            throw error("unterminated string");
        }
        private Double number() {
            int start = p;
            if (peek('-')) p++;
            if (p >= s.length()) throw error("bad number");
            if (peek('0')) p++;
            else {
                if (!Character.isDigit(s.charAt(p))) throw error("bad number");
                while (p < s.length() && Character.isDigit(s.charAt(p))) p++;
            }
            if (peek('.')) {
                p++; int d = p; while (p < s.length() && Character.isDigit(s.charAt(p))) p++;
                if (p == d) throw error("bad fraction");
            }
            if (peek('e') || peek('E')) {
                p++; if (peek('+') || peek('-')) p++;
                int d = p; while (p < s.length() && Character.isDigit(s.charAt(p))) p++;
                if (p == d) throw error("bad exponent");
            }
            try {
                double v = Double.parseDouble(s.substring(start, p));
                if (!Double.isFinite(v)) throw error("non-finite number");
                return v;
            } catch (NumberFormatException ex) { throw error("bad number"); }
        }
        private void ws() { while (p < s.length() && Character.isWhitespace(s.charAt(p))) p++; }
        private boolean peek(char c) { return p < s.length() && s.charAt(p) == c; }
        private void expect(char c) { ws(); if (!peek(c)) throw error("expected " + c); p++; }
        private IllegalArgumentException error(String message) { return new IllegalArgumentException(message + " at " + p); }
    }
}
