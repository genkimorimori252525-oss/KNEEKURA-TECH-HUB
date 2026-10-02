package org.kneekura.bedrockwither.entity;

public record BedrockWitherHeadDebugSnapshot(
        int index,
        float yaw,
        float pitch,
        float oldYaw,
        float oldPitch,
        int nextUpdate,
        int idleUpdates
) {
}
