package dev.kneekura.fivedifficulties.core.x1;

public enum SakuyaControllerKind {
    WATCH_PERSISTENT,
    WATCH_LIMITED,
    SPELL_CARD,
    STOPWATCH;

    public boolean endsOnSneakAfterGrace() {
        return this != STOPWATCH;
    }
}
