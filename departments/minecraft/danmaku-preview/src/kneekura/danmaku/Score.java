package kneekura.danmaku;

import java.util.ArrayList;
import java.util.List;

/** Deterministic multi-track score built on the existing Pattern model. */
public final class Score {
    public static final int MAX_TRACKS = 32;
    public static final int MAX_LIVE_BULLETS = 3000;
    public static final int MAX_DURATION_TICKS = 1200;

    public enum Frame {
        /** Preserve Pattern's original world-oriented X/Y/Z coordinates. */
        WORLD,
        /**
         * Reinterpret Pattern's yaw plane as the player's screen plane:
         * Pattern X -> screen-right, Pattern Z -> screen-up, while forwardSpeed advances toward the player.
         */
        PLAYER_VIEW
    }

    public record Track(String name, int startTick, int endTick, Pattern.Config pattern,
                        Frame frame, double forwardSpeed, double hue, double radius) {
        public Track {
            if (name == null || !name.matches("[A-Za-z0-9_-]{1,32}"))
                throw new IllegalArgumentException("track name must be 1..32 safe ASCII chars");
            range(startTick, 0, MAX_DURATION_TICKS, "startTick");
            range(endTick, 1, MAX_DURATION_TICKS, "endTick");
            if (endTick <= startTick) throw new IllegalArgumentException("endTick must be > startTick");
            if (pattern == null) throw new IllegalArgumentException("pattern is required");
            if (pattern.durationTicks() != endTick - startTick)
                throw new IllegalArgumentException("pattern duration must equal endTick-startTick");
            if (frame == null) throw new IllegalArgumentException("frame is required");
            range(forwardSpeed, 0, 4, "forwardSpeed");
            range(hue, 0, 360, "hue");
            range(radius, 0.04, 1.0, "radius");
        }
    }

    public record Config(int durationTicks, List<Track> tracks) {
        public Config {
            range(durationTicks, 1, MAX_DURATION_TICKS, "durationTicks");
            if (tracks == null || tracks.isEmpty()) throw new IllegalArgumentException("at least one track is required");
            if (tracks.size() > MAX_TRACKS) throw new IllegalArgumentException("too many tracks");
            tracks = List.copyOf(tracks);
            for (Track track : tracks) {
                if (track.endTick() > durationTicks)
                    throw new IllegalArgumentException("track exceeds score duration: " + track.name());
            }
            for (int tick = 0; tick <= durationTicks; tick++) {
                int live = 0;
                for (Track track : tracks) live += liveCount(track, tick);
                if (live > MAX_LIVE_BULLETS)
                    throw new IllegalArgumentException("combined live bullets exceed " + MAX_LIVE_BULLETS + " at tick " + tick);
            }
        }
    }

    public record Bullet(long id, String track, int trackIndex, int bornTick,
                         double x, double y, double z, double hue, double radius) {}

    public static Config defaults() {
        var halo = track("halo", 20, 120, Pattern.Kind.RING, 24, 0.16, 12, 360, 0, 0, 70,
            Frame.PLAYER_VIEW, 0.11, 36, 0.14);
        var spiralA = track("spiral_a", 80, 220, Pattern.Kind.SPIRAL, 8, 0.18, 6, 360, 115, 0, 90,
            Frame.PLAYER_VIEW, 0.12, 205, 0.12);
        var spiralB = track("spiral_b", 80, 220, Pattern.Kind.SPIRAL, 8, 0.18, 6, 360, -115, 0, 90,
            Frame.PLAYER_VIEW, 0.12, 325, 0.12);
        return new Config(240, List.of(halo, spiralA, spiralB));
    }

    public static Track track(String name, int start, int end, Pattern.Kind kind, int bullets, double speed,
                              int interval, double fan, double rotation, double elevation, int lifetime,
                              Frame frame, double forwardSpeed, double hue, double radius) {
        return new Track(name, start, end,
            new Pattern.Config(kind, bullets, speed, interval, fan, rotation, elevation, lifetime, end - start),
            frame, forwardSpeed, hue, radius);
    }

    public static List<Bullet> at(Config score, double tick) {
        range(tick, 0, score.durationTicks(), "tick");
        var out = new ArrayList<Bullet>();
        for (int ti = 0; ti < score.tracks().size(); ti++) {
            Track track = score.tracks().get(ti);
            if (tick < track.startTick() || tick > track.endTick()) continue;
            double localTick = tick - track.startTick();
            for (Pattern.Bullet bullet : Pattern.at(track.pattern(), localTick)) {
                int bornTick = track.startTick() + bullet.bornTick();
                double age = tick - bornTick;
                double x = bullet.x(), y = bullet.y(), z = bullet.z();
                if (track.frame() == Frame.PLAYER_VIEW) {
                    double screenX = bullet.x();
                    double screenY = bullet.z();
                    double elevationForward = bullet.y() - 2.0;
                    x = screenX;
                    y = 2.0 + screenY;
                    z = track.forwardSpeed() * age + elevationForward;
                }
                long id = ((long) ti << 32) | (bullet.id() & 0xffffffffL);
                out.add(new Bullet(id, track.name(), ti, bornTick, x, y, z, track.hue(), track.radius()));
            }
        }
        if (out.size() > MAX_LIVE_BULLETS)
            throw new IllegalStateException("validated score exceeded live bullet budget");
        return List.copyOf(out);
    }

    public static int liveCount(Track track, double tick) {
        if (tick < track.startTick() || tick > track.endTick()) return 0;
        double local = tick - track.startTick();
        Pattern.Config c = track.pattern();
        int last = Math.min((int) Math.floor(local / c.intervalTicks()),
                            (c.durationTicks() - 1) / c.intervalTicks());
        int first = Math.max(0, (int) Math.floor((local - c.lifetimeTicks()) / c.intervalTicks()) + 1);
        return last < first ? 0 : (last - first + 1) * c.bullets();
    }

    private static void range(double value, double min, double max, String name) {
        if (!Double.isFinite(value) || value < min || value > max)
            throw new IllegalArgumentException(name + " must be " + min + ".." + max);
    }
}
