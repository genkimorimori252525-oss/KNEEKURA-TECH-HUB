package kneekura.danmaku;

import java.util.List;

public final class PatternTest {
    private static int checks;
    public static void main(String[] args) {
        var fan = config(Pattern.Kind.FAN, 3, 0.5, 10, 90, 90, 0, 20, 100);
        var first = Pattern.at(fan, 2);
        equal(first.size(), 3, "first burst");
        near(first.get(0).x(), -Math.sqrt(0.5), "fan left x");
        near(first.get(0).z(), Math.sqrt(0.5), "fan left z");
        near(first.get(1).x(), 0, "fan middle x");
        near(first.get(1).z(), 1, "block/tick speed");
        near(first.get(1).y(), 2, "emitter height");
        equal(Pattern.at(fan, 9).size(), 3, "before second burst");
        equal(Pattern.at(fan, 10).size(), 6, "interval boundary");
        var expiry = Pattern.at(fan, 20);
        equal(expiry.size(), 6, "expired first burst removed");
        equal(expiry.get(0).bornTick(), 10, "lifetime boundary");
        equal(Pattern.at(fan, 100).size(), 3, "no burst at duration endpoint");
        truth(first.equals(Pattern.at(fan, 2)), "rewind deterministic");
        var ring = config(Pattern.Kind.RING, 4, 1, 20, 90, 0, 0, 40, 100);
        var points = Pattern.at(ring, 1);
        near(points.get(0).z(), 1, "ring +Z");
        near(points.get(1).x(), 1, "ring +X");
        near(points.get(2).z(), -1, "ring -Z");
        near(points.get(3).x(), -1, "ring -X");
        var rotating = config(Pattern.Kind.SPIRAL, 1, 1, 20, 90, 90, 0, 40, 100);
        var rotated = Pattern.at(rotating, 21).get(1);
        near(rotated.x(), 1, "90 degrees/sec second burst");
        near(rotated.z(), 0, "rotation uses birth time");
        var up = config(Pattern.Kind.FAN, 1, 1, 20, 0, 0, 30, 40, 100);
        near(Pattern.at(up, 2).get(0).y(), 3, "elevation uses Y up");
        near(Pattern.at(up, 2).get(0).z(), Math.sqrt(3), "elevation horizontal speed");
        truth(Pattern.at(fan, 2.5).get(1).z() > first.get(1).z(), "fractional render time");
        rejects(() -> Pattern.at(fan, -1), "negative time");
        rejects(() -> Pattern.at(fan, Double.NaN), "NaN time");
        rejects(() -> Pattern.at(fan, 101), "beyond duration");
        rejects(() -> config(Pattern.Kind.FAN, 0, 1, 1, 90, 0, 0, 20, 100), "zero count");
        rejects(() -> config(Pattern.Kind.FAN, 256, 1, 1, 90, 0, 0, 20, 100), "live budget");
        rejects(() -> config(Pattern.Kind.FAN, 1, Double.NaN, 1, 90, 0, 0, 20, 100), "NaN speed");
        equal(Pattern.at(config(Pattern.Kind.FAN, 300, 0, 1, 0, 0, 0, 10, 100), 10).size(), 3000, "exact budget allowed");
        var json = PatternJson.write(fan);
        truth(PatternJson.read(json).equals(fan), "JSON round trip");
        truth(PatternJson.read(json.replace("\n", "\r\n")).equals(fan), "CRLF JSON");
        rejects(() -> PatternJson.read(json + "x"), "trailing input");
        rejects(() -> PatternJson.read(json.strip().replaceFirst("}\\s*$", ",}")), "trailing comma");
        rejects(() -> PatternJson.read(json.replace("\"schemaVersion\": 1", "\"schemaVersion\": 2")), "schema mismatch");
        rejects(() -> PatternJson.read(json.replace("\"speed\": 0.5", "\"speed\": null")), "null numeric");
        rejects(() -> PatternJson.read(json.replace("\"speed\": 0.5", "\"speed\": 1e999")), "overflow numeric");
        rejects(() -> PatternJson.read(json.replace("\"bullets\": 3", "\"bullets\": 3.5")), "fractional count");
        rejects(() -> PatternJson.read(json.replace("\"bullets\": 3", "\"bullets\": 3.0000000000000001")), "fraction lost by double rounding");
        rejects(() -> PatternJson.read(json.replace("\"pattern\": \"FAN\"", "\"pattern\": \"UNKNOWN\"")), "unknown pattern");
        rejects(() -> PatternJson.read(json.replaceFirst("\\{", "{\"speed\": 1,")), "duplicate key");
        rejects(() -> PatternJson.read(json.replaceFirst("\\{", "{\"extra\": 1,")), "unknown key");
        rejects(() -> PatternJson.read(json.replace("\"speed\": 0.5,", "")), "missing key");
        rejects(() -> PatternJson.read(json.replace("\"speed\": 0.5", "\"speed\": 01")), "invalid JSON number");
        rejects(() -> PatternJson.read(json.replace("\"speed\": 0.5", "\"speed\": \"0.5\"")), "wrong numeric type");
        if (args.length == 1) {
            try {
                var preset = PatternJson.read(java.nio.file.Files.readString(java.nio.file.Path.of(args[0])));
                equal(preset.bullets(), 12, "bundled fan preset count");
                near(preset.speed(), 0.18, "bundled fan preset speed");
                truth(preset.pattern() == Pattern.Kind.FAN, "bundled fan preset kind");
            } catch (java.io.IOException ex) { throw new AssertionError("preset read", ex); }
        }
        System.out.println("PASS: " + checks + " pattern/JSON assertions");
    }
    static Pattern.Config config(Pattern.Kind kind, int count, double speed, int interval,
                                  double fan, double rotation, double elevation, int life, int duration) {
        return new Pattern.Config(kind, count, speed, interval, fan, rotation, elevation, life, duration);
    }
    static void truth(boolean value, String message) {
        checks++; if (!value) throw new AssertionError(message);
    }
    static void equal(long got, long want, String message) { truth(got == want, message + ": " + got + " != " + want); }
    static void near(double got, double want, String message) { truth(Math.abs(got - want) < 1e-9, message + ": " + got); }
    static void rejects(Runnable action, String message) {
        checks++;
        try { action.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("must reject: " + message);
    }
}