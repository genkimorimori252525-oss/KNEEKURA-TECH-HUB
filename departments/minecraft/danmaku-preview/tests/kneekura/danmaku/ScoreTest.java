package kneekura.danmaku;

import java.util.List;

public final class ScoreTest {
    private static int checks;
    public static void main(String[] args) {
        var a = Score.track("halo", 10, 110, Pattern.Kind.RING, 4, 0.5, 10, 360, 0, 0, 30,
            Score.Frame.WORLD, 0, 0, 40, 0.12);
        var b = Score.track("spiral", 40, 140, Pattern.Kind.SPIRAL, 2, 0.25, 10, 360, 90, 0, 40,
            Score.Frame.WORLD, 0, 0, 210, 0.16);
        var score = new Score.Config(160, List.of(a, b));
        equal(Score.at(score, 0).size(), 0, "before tracks");
        equal(Score.at(score, 10).size(), 4, "track starts at absolute tick");
        equal(Score.at(score, 40).size(), 14, "overlap combines tracks");
        truth(Score.at(score, 40).stream().anyMatch(x -> x.track().equals("spiral")), "track identity");
        var first = Score.at(score, 20);
        truth(first.equals(Score.at(score, 20)), "score rewind deterministic");
        truth(Score.at(score, 40.5).size() >= Score.at(score, 40).size(), "fractional time");

        var view = Score.track("view", 0, 20, Pattern.Kind.RING, 4, 1, 20, 360, 0, 0, 20,
            Score.Frame.PLAYER_VIEW, 0.25, 0, 10, 0.1);
        var viewBullets = Score.at(new Score.Config(20, List.of(view)), 1);
        near(viewBullets.get(0).x(), 0, "player frame ring top x");
        near(viewBullets.get(0).y(), 3, "player frame Pattern Z maps to screen up");
        near(viewBullets.get(0).z(), 0.25, "player frame forward travel");

        var phased = Score.track("phase", 0, 20, Pattern.Kind.RING, 4, 1, 20, 360, 0, 0, 20,
            Score.Frame.PLAYER_VIEW, 0.25, 90, 10, 0.1);
        var phasedBullet = Score.at(new Score.Config(20, List.of(phased)), 1).get(0);
        near(phasedBullet.x(), 1, "phase rotates screen-up to screen-right");
        near(phasedBullet.y(), 2, "phase rotates screen-up away from up");
        near(phasedBullet.z(), 0.25, "phase does not change forward travel");

        rejects(() -> new Score.Config(160, List.of(
            Score.track("bad", 0, 100, Pattern.Kind.RING, 100, 1, 1, 360, 0, 0, 20,
                Score.Frame.WORLD, 0, 0, 10, 0.1),
            Score.track("bad2", 0, 100, Pattern.Kind.RING, 100, 1, 1, 360, 0, 0, 20,
                Score.Frame.WORLD, 0, 0, 20, 0.1)
        )), "combined budget");
        rejects(() -> new Score.Track("x", 20, 10,
            new Pattern.Config(Pattern.Kind.FAN, 1, 1, 1, 0, 0, 0, 5, 1),
            Score.Frame.WORLD, 0, 0, 0, 0.1), "invalid range");
        rejects(() -> Score.at(score, -1), "negative time");
        rejects(() -> Score.at(score, 161), "beyond duration");

        String json = ScoreJson.write(score);
        truth(ScoreJson.read(json).equals(score), "score JSON round trip");
        String legacyV2 = json.replaceAll("\\s*\"phaseDeg\": [-0-9.]+,\\n", "");
        truth(ScoreJson.read(legacyV2).tracks().stream().allMatch(t -> t.phaseDeg() == 0),
            "legacy v2 without phase defaults to zero");
        rejects(() -> ScoreJson.read(json.replace("\"schemaVersion\": 2", "\"schemaVersion\": 3")), "score schema mismatch");
        rejects(() -> ScoreJson.read(json.replaceFirst("\"tracks\"", "\"extra\": 1, \"tracks\"")), "unknown root field");
        rejects(() -> ScoreJson.read(json.replaceFirst("\"name\": \"halo\"", "\"name\": \"halo\", \"extra\": 1")), "unknown track field");

        if (args.length == 1) {
            try {
                var preset = ScoreJson.read(java.nio.file.Files.readString(java.nio.file.Path.of(args[0])));
                truth(preset.tracks().size() >= 10, "bundled Grand Danmaku is multi-motif");
                truth(Score.at(preset, 140).size() >= 250, "petal section is visibly dense");
                truth(Score.at(preset, 140).size() <= Score.MAX_LIVE_BULLETS, "preset budget");
                truth(preset.tracks().stream().allMatch(t -> t.frame() == Score.Frame.PLAYER_VIEW),
                    "grand danmaku preset uses player-view frame");
            } catch (java.io.IOException ex) { throw new AssertionError("preset read", ex); }
        }
        System.out.println("PASS: " + checks + " score/JSON assertions");
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
