package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.timestop.*;
import dev.kneekura.fivedifficulties.core.x1.SakuyaWatchContract;
import java.util.UUID;

public final class X1SakuyaTimePolicyRegression {
    public static void main(String[] args) {
        UUID stopId = UUID.fromString("10000000-0000-0000-0000-000000000001");
        UUID sakuya = UUID.fromString("10000000-0000-0000-0000-000000000002");
        UUID target = UUID.fromString("10000000-0000-0000-0000-000000000003");

        TimeStopFlags flags = TimeStopFlags.x1EntityOnly();

        SakuyaTimeStopInstance full = new SakuyaTimeStopInstance(
                stopId,
                sakuya,
                Vec3d.ZERO,
                SakuyaWatchContract.FIELD_RANGE_BLOCKS,
                100,
                SakuyaWatchContract.LIMITED_STOP_PROCESSING_TICKS,
                flags,
                TimeStopShape.AABB,
                TimeDomainMode.FULL_STOP
        );

        SakuyaTimeStopService service = new SakuyaTimeStopService();
        service.start(full);

        TimeStopSubject diagonalInside = subject(target, SubjectKind.OTHER, new Vec3d(39, 39, 39), 2, false, false);
        check(service.decision(diagonalInside, 100) == TimeStopDecision.FREEZE,
                "AABB diagonal must be inside even though a 40-radius sphere would exclude it");

        TimeStopSubject outsideX = subject(target, SubjectKind.OTHER, new Vec3d(40.001, 0, 0), 2, false, false);
        check(service.decision(outsideX, 100) == TimeStopDecision.ALLOW, "outside AABB");

        TimeStopSubject source = subject(sakuya, SubjectKind.LIVING, Vec3d.ZERO, 100, false, false);
        check(service.decision(source, 100) == TimeStopDecision.ALLOW, "source exempt");

        TimeStopSubject newborn = subject(target, SubjectKind.PROJECTILE, Vec3d.ZERO, 1, false, false);
        check(service.decision(newborn, 100) == TimeStopDecision.ALLOW, "ticksExisted < 2 grace");

        TimeStopSubject oldProjectile = subject(target, SubjectKind.PROJECTILE, Vec3d.ZERO, 2, false, false);
        check(service.decision(oldProjectile, 100) == TimeStopDecision.FREEZE, "projectile freezes at age 2");

        TimeStopSubject item = subject(target, SubjectKind.ITEM, Vec3d.ZERO, 2, false, false);
        check(service.decision(item, 100) == TimeStopDecision.FREEZE, "ItemEntity is an affected Entity");

        TimeStopSubject other = subject(target, SubjectKind.OTHER, Vec3d.ZERO, 2, false, false);
        check(service.decision(other, 100) == TimeStopDecision.FREEZE, "non-living Entity also freezes");

        TimeStopSubject itemFrameEquivalent = subject(target, SubjectKind.OTHER, Vec3d.ZERO, 2, true, false);
        check(service.decision(itemFrameEquivalent, 100) == TimeStopDecision.ALLOW, "explicit X1 exclusion");

        TimeStopSubject movableSpell = subject(target, SubjectKind.OTHER, Vec3d.ZERO, 20, false, true);
        check(service.decision(movableSpell, 100) == TimeStopDecision.ALLOW, "same-owner movable spell card");

        check(service.shouldCancelNormalTick(oldProjectile, 100), "full stop cancels normal tick");

        service.stopSource(sakuya);
        SakuyaTimeStopInstance half = new SakuyaTimeStopInstance(
                UUID.fromString("10000000-0000-0000-0000-000000000004"),
                sakuya,
                Vec3d.ZERO,
                40.0,
                200,
                SakuyaWatchContract.LIMITED_HALF_PROCESSING_TICKS,
                flags,
                TimeStopShape.AABB,
                TimeDomainMode.HALF_SPEED
        );
        service.start(half);

        TimeStopSubject living = subject(target, SubjectKind.LIVING, Vec3d.ZERO, 20, false, false);
        check(service.decision(living, 200) == TimeStopDecision.HALF_SPEED, "half-speed decision");
        check(service.shouldCancelNormalTick(living, 200), "X1 count=0 phase cancels");
        check(!service.shouldCancelNormalTick(living, 201), "next half-speed phase runs");
        check(service.shouldCancelNormalTick(living, 202), "alternate phase cancels again");

        check(half.isActiveAt(360), "limited half includes processing tick 161 window");
        check(!half.isActiveAt(361), "limited half expires after 161 scheduler ticks");

        System.out.println("X1_SAKUYA_TIME_POLICY_REGRESSION_PASS");
    }

    private static TimeStopSubject subject(
            UUID id,
            SubjectKind kind,
            Vec3d pos,
            int age,
            boolean explicitExempt,
            boolean movableSpell
    ) {
        return new TimeStopSubject(id, null, kind, false, pos, age, explicitExempt, movableSpell);
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
