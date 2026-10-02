package org.kneekura.bedrockwither.entity;

import java.util.Optional;
import java.util.UUID;

public record BedrockWitherHeadDebugSnapshot(
        int index,
        float yaw,
        float pitch,
        float oldYaw,
        float oldPitch,
        int nextUpdate,
        int idleUpdates,
        Optional<UUID> targetUuid
) {
}
