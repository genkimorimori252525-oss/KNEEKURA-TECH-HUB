package kneekura.danmaku;

import java.util.List;
import java.util.ArrayList;

/** Pure draft coordinates: blocks, Y up, +Z heading, 20 ticks/second. */
public final class Pattern {
    public enum Kind { FAN, RING, SPIRAL }
    public record Config(Kind pattern, int bullets, double speed, int intervalTicks,
                         double fanAngleDeg, double rotationDegPerSecond, double elevationDeg,
                         int lifetimeTicks, int durationTicks) {
        public Config {
            if (pattern == null) throw new IllegalArgumentException("pattern is required");
            range(bullets, 1, 1000, "bullets");
            range(speed, 0, 4, "speed");
            range(intervalTicks, 1, 1200, "intervalTicks");
            range(fanAngleDeg, 0, 360, "fanAngleDeg");
            range(rotationDegPerSecond, -720, 720, "rotationDegPerSecond");
            range(elevationDeg, -90, 90, "elevationDeg");
            range(lifetimeTicks, 1, 1200, "lifetimeTicks");
            range(durationTicks, 1, 1200, "durationTicks");
            int bursts = (Math.min(lifetimeTicks, durationTicks) + intervalTicks - 1) / intervalTicks;
            if ((long) bullets * bursts > 3000)
                throw new IllegalArgumentException("同時弾数は3,000以下にしてください（弾数・間隔・寿命）");
        }
    }
    public record Bullet(long id, int bornTick, double x, double y, double z) {}
    public static Config defaults() { return new Config(Kind.FAN, 12, 0.18, 10, 90, 60, 0, 80, 400); }

    public static List<Bullet> at(Config config, double tick) {
        range(tick, 0, config.durationTicks(), "tick");
        int last = Math.min((int) Math.floor(tick / config.intervalTicks()),
                            (config.durationTicks() - 1) / config.intervalTicks());
        int first = Math.max(0, (int) Math.floor((tick - config.lifetimeTicks()) / config.intervalTicks()) + 1);
        var result = new ArrayList<Bullet>();
        double elevation = Math.toRadians(config.elevationDeg());
        for (int burst = first; burst <= last; burst++) {
            int born = burst * config.intervalTicks();
            double age = tick - born;
            for (int index = 0; index < config.bullets(); index++) {
                double heading = config.pattern() == Kind.FAN
                    ? (config.bullets() == 1 ? 0 : -config.fanAngleDeg() / 2
                       + config.fanAngleDeg() * index / (config.bullets() - 1))
                    : 360.0 * index / config.bullets();
                if (config.pattern() == Kind.SPIRAL)
                    heading += config.rotationDegPerSecond() * born / 20.0;
                double yaw = Math.toRadians(heading);
                double distance = config.speed() * age;
                result.add(new Bullet((long) burst * config.bullets() + index, born,
                    Math.sin(yaw) * Math.cos(elevation) * distance,
                    2 + Math.sin(elevation) * distance,
                    Math.cos(yaw) * Math.cos(elevation) * distance));
            }
        }
        return List.copyOf(result);
    }

    private static void range(double value, double min, double max, String name) {
        if (!Double.isFinite(value) || value < min || value > max)
            throw new IllegalArgumentException(name + " must be " + min + ".." + max);
    }
}
