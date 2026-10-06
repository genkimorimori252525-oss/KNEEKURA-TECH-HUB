package dev.kneekura.fivedifficulties.core.timestop;

/** Pure policy: no Minecraft/Forge or JoJo classes. */
public final class TimeStopPolicy {
    public TimeStopDecision decide(SakuyaTimeStopInstance stop, TimeStopSubject subject, int tick) {
        if (!stop.isActiveAt(tick) || !stop.contains(subject.position())) return TimeStopDecision.ALLOW;
        if (subject.entityId().equals(stop.sourceEntityId())) return TimeStopDecision.ALLOW;

        TimeStopFlags flags = stop.flags();
        return switch (subject.kind()) {
            case LIVING -> flags.freezeLivingEntities() ? TimeStopDecision.FREEZE : TimeStopDecision.ALLOW;
            case ITEM -> flags.freezeItemEntities() ? TimeStopDecision.FREEZE : TimeStopDecision.ALLOW;
            case PROJECTILE -> projectileDecision(stop, subject, flags);
            case OTHER -> TimeStopDecision.ALLOW;
        };
    }

    private TimeStopDecision projectileDecision(
            SakuyaTimeStopInstance stop,
            TimeStopSubject subject,
            TimeStopFlags flags
    ) {
        boolean sourceOwned = stop.sourceEntityId().equals(subject.ownerId());
        if (sourceOwned && subject.createdDuringTimeStop() && flags.specialMoveNewProjectiles()) {
            return TimeStopDecision.SPECIAL_PROJECTILE;
        }
        return flags.freezeExistingProjectiles() ? TimeStopDecision.FREEZE : TimeStopDecision.ALLOW;
    }
}
