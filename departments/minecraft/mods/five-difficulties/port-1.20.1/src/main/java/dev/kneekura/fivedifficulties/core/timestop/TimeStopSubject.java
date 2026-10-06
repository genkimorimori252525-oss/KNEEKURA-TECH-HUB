package dev.kneekura.fivedifficulties.core.timestop;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import java.util.UUID;

public record TimeStopSubject(
        UUID entityId,
        UUID ownerId,
        SubjectKind kind,
        boolean createdDuringTimeStop,
        Vec3d position
) {
    public TimeStopSubject {
        if (entityId == null || kind == null || position == null) throw new NullPointerException();
    }
}
