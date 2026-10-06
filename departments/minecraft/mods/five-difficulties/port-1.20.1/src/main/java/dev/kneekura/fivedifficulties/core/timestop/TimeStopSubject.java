package dev.kneekura.fivedifficulties.core.timestop;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import java.util.UUID;

public record TimeStopSubject(
        UUID entityId,
        UUID ownerId,
        SubjectKind kind,
        boolean createdDuringTimeStop,
        Vec3d position,
        int ageTicks,
        boolean x1ExplicitExempt,
        boolean x1MovableSameOwnerSpellCard
) {
    public TimeStopSubject {
        if (entityId == null || kind == null || position == null) throw new NullPointerException();
        if (ageTicks < 0) throw new IllegalArgumentException("ageTicks");
    }

    /** Backward-compatible P0 constructor. */
    public TimeStopSubject(
            UUID entityId,
            UUID ownerId,
            SubjectKind kind,
            boolean createdDuringTimeStop,
            Vec3d position
    ) {
        this(entityId, ownerId, kind, createdDuringTimeStop, position, 2, false, false);
    }
}
