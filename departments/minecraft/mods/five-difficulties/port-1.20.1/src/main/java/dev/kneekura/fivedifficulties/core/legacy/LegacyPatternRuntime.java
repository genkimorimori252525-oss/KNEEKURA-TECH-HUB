package dev.kneekura.fivedifficulties.core.legacy;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * A deliberately tiny 20-TPS-compatible pattern clock.
 * It does not skip or interpolate ticks; the caller owns the Minecraft-side schedule.
 */
public final class LegacyPatternRuntime {
    private final LegacyPattern pattern;
    private int tick;

    public LegacyPatternRuntime(LegacyPattern pattern) {
        this.pattern = Objects.requireNonNull(pattern, "pattern");
    }

    public int tick() {
        return tick;
    }

    public PatternFrame step(PatternContext context) {
        Objects.requireNonNull(context, "context");
        List<ShotSpawn> shots = new ArrayList<>();
        List<LaserSpawn> lasers = new ArrayList<>();
        PatternSink sink = new PatternSink() {
            @Override public void shot(ShotSpawn shot) { shots.add(Objects.requireNonNull(shot)); }
            @Override public void laser(LaserSpawn laser) { lasers.add(Objects.requireNonNull(laser)); }
        };
        pattern.emit(tick, context, sink);
        PatternFrame frame = new PatternFrame(tick, shots, lasers);
        tick++;
        return frame;
    }

    public void reset() {
        tick = 0;
    }
}
