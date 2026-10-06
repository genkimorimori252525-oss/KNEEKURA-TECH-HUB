package dev.kneekura.fivedifficulties.core.legacy;

import java.util.List;

public record PatternFrame(int tick, List<ShotSpawn> shots, List<LaserSpawn> lasers) {
    public PatternFrame {
        if (tick < 0) throw new IllegalArgumentException("tick < 0");
        shots = List.copyOf(shots);
        lasers = List.copyOf(lasers);
    }
}
