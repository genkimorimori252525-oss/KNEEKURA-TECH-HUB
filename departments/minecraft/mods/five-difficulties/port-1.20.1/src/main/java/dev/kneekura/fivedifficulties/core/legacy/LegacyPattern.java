package dev.kneekura.fivedifficulties.core.legacy;

@FunctionalInterface
public interface LegacyPattern {
    void emit(int tick, PatternContext context, PatternSink sink);
}
