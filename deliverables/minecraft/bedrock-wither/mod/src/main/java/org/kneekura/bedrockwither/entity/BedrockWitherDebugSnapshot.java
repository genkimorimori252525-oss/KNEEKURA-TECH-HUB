package org.kneekura.bedrockwither.entity;

public record BedrockWitherDebugSnapshot(
        int entityId,
        BedrockWitherState state,
        long ticksInState,
        float health,
        float maxHealth,
        String difficulty,
        double x,
        double y,
        double z,
        double velocityX,
        double velocityY,
        double velocityZ,
        int threatLedgerSize
) {
}
