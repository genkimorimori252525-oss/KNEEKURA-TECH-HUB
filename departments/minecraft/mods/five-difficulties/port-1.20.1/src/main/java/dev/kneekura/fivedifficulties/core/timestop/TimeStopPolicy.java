package dev.kneekura.fivedifficulties.core.timestop;

/** Pure policy: no Minecraft/Forge or JoJo classes. */
public final class TimeStopPolicy {
    public TimeStopDecision decide(SakuyaTimeStopInstance stop, TimeStopSubject subject, int tick) {
        if (!stop.isActiveAt(tick) || !stop.contains(subject.position())) return TimeStopDecision.ALLOW;
        if (subject.entityId().equals(stop.sourceEntityId())) return TimeStopDecision.ALLOW;
        if (subject.x1ExplicitExempt() || subject.x1MovableSameOwnerSpellCard()) return TimeStopDecision.ALLOW;

        TimeStopFlags flags = stop.flags();
        if (subject.ageTicks() < flags.minimumEntityAgeTicks()) return TimeStopDecision.ALLOW;

        boolean affected = switch (subject.kind()) {
            case LIVING -> flags.freezeLivingEntities();
            case ITEM -> flags.freezeItemEntities();
            case PROJECTILE -> flags.freezeExistingProjectiles();
            case OTHER -> flags.freezeOtherEntities();
        };
        if (!affected) return TimeStopDecision.ALLOW;

        if (stop.mode() == TimeDomainMode.HALF_SPEED) {
            return TimeStopDecision.HALF_SPEED;
        }

        if (subject.kind() == SubjectKind.PROJECTILE) {
            boolean sourceOwned = stop.sourceEntityId().equals(subject.ownerId());
            if (sourceOwned && subject.createdDuringTimeStop() && flags.specialMoveNewProjectiles()) {
                return TimeStopDecision.SPECIAL_PROJECTILE;
            }
        }

        return TimeStopDecision.FREEZE;
    }
}
