package kneekura.danmaku;

import java.util.List;

public final class ScoreTest {
    private static int checks;
    public static void main(String[] args) {
        var a = Score.track("halo", 10, 110, Pattern.Kind.RING, 4, 0.5, 10, 360, 0, 0, 30, 40, 0.12);
        var b = Score.track("spiral", 40, 140, Pattern.Kind.SPIRAL, 2, 0.25, 10, 360, 90, 0, 40, 210, 0.16);
        var score = new Score.Config(160, List.of(a, b));
        equal(Score.at(score, 0).size(), 0, "before tracks");
        equal(Score.at(score, 10).size(), 4, "track starts at absolute tick");
        equal(Score.at(score, 40).size(), 14, "overlap combines tracks");
        truth(Score.at(score, 40).stream().anyMatch(x -> x.track().equals("spiral")), "track identity");
        var first = Score.at(score, 20);
        truth(first.equals(Score.at(score, 20)), "score rewind deterministic");
        truth(Score.at(score, 40.5).size() >= Score.at(score, 40).size(), "fractional time");
        equal(Score.liveCount(a, 9), 0, "live count pre-start");
        equal(Score.liveCount(a, 10), 4, "live count start");
        rejects(() -> new Score.Config(160, List.of(
            Score.track("bad", 0, 100, Pattern.Kind.RING, 300, 1, 1, 360, 0, 0, 20, 10, 0.1),
            Score.track("bad2", 0, 100, Pattern.Kind.RING, 300, 1, 1, 360, 0, 0, 20, 20, 0.1)
        )), "combined budget");
        rejects(() -> new Score.Track("x", 20, 10,
            new Pattern.Config(Pattern.Kind.FAN, 1, 1, 1, 0, 0, 0, 5, 1), 0, 0.1), "invalid range");
        rejects(() -> Score.at(score, -1), "negative time");
        rejects(() -> Score.at(score, 161), "beyond duration");
        String json = ScoreJson.write(score);
        truth(ScoreJson.read(json).equals(score), "score JSON round trip");
        truth(ScoreJson.read(json.replace("\n", "\r\n")).equals(score), "CRLF score JSON");
        rejects(() -> ScoreJson.read(json.replace("\"schemaVersion\": 2", "\"schemaVersion\": 3")), "score schema mismatch");
        rejects(() -> ScoreJson.read(json.replaceFirst("\"tracks\"", "\"extra\": 1, \"tracks\"")), "unknown root field");
        rejects(() -> ScoreJson.read(json.replaceFirst("\"name\": \"halo\"", "\"name\": \"halo\", \"extra\": 1")), "unknown track field");
        if (args.length == 1) {
            try {
                var preset = ScoreJson.read(java.nio.file.Files.readString(java.nio.file.Path.of(args[0])));
                truth(preset.tracks().size() >= 3, "bundled score tracks");
                truth(Score.at(preset, 100).size() > 0, "bundled score active");
            } catch (java.io.IOException ex) { throw new AssertionError("preset read", ex); }
        }
        System.out.println("PASS: " + checks + " score/JSON assertions");
    }
    static void truth(boolean value, String message) {
        checks++; if (!value) throw new AssertionError(message);
    }
    static void equal(long got, long want, String message) { truth(got == want, message + ": " + got + " != " + want); }
    static void rejects(Runnable action, String message) {
        checks++;
        try { action.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("must reject: " + message);
    }
}
