package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.timestop.*;
import java.util.UUID;

public final class SakuyaTimeStopCoreRegression {
    public static void main(String[] args) {
        UUID stopId = UUID.fromString("00000000-0000-0000-0000-000000000001");
        UUID sakuya = UUID.fromString("00000000-0000-0000-0000-000000000002");
        UUID mob = UUID.fromString("00000000-0000-0000-0000-000000000003");
        UUID projectile = UUID.fromString("00000000-0000-0000-0000-000000000004");

        TimeStopFlags flags = TimeStopFlags.p0EngineeringDefault();
        SakuyaTimeStopInstance stop = new SakuyaTimeStopInstance(
                stopId, sakuya, Vec3d.ZERO, 10.0, 100, 40, flags
        );
        SakuyaTimeStopService service = new SakuyaTimeStopService();
        service.start(stop);

        TimeStopSubject source = new TimeStopSubject(sakuya, null, SubjectKind.LIVING, false, Vec3d.ZERO);
        check(service.decision(source, 100) == TimeStopDecision.ALLOW, "source must move in own stop");

        TimeStopSubject target = new TimeStopSubject(mob, null, SubjectKind.LIVING, false, new Vec3d(3, 0, 0));
        check(service.decision(target, 100) == TimeStopDecision.FREEZE, "living target must freeze");

        TimeStopSubject oldProjectile = new TimeStopSubject(projectile, null, SubjectKind.PROJECTILE, false, new Vec3d(4, 0, 0));
        check(service.decision(oldProjectile, 101) == TimeStopDecision.FREEZE, "existing projectile must freeze in P0 policy");

        TimeStopSubject newKnife = new TimeStopSubject(projectile, sakuya, SubjectKind.PROJECTILE, true, new Vec3d(4, 0, 0));
        check(service.decision(newKnife, 101) == TimeStopDecision.SPECIAL_PROJECTILE, "new Sakuya projectile uses special mover");

        TimeStopSubject droppedItem = new TimeStopSubject(UUID.randomUUID(), null, SubjectKind.ITEM, false, Vec3d.ZERO);
        check(service.decision(droppedItem, 101) == TimeStopDecision.ALLOW, "P0 does not assert X1 item freeze");

        TimeStopSubject outside = new TimeStopSubject(mob, null, SubjectKind.LIVING, false, new Vec3d(20, 0, 0));
        check(service.decision(outside, 101) == TimeStopDecision.ALLOW, "outside range");

        service.purgeExpired(140);
        check(service.activeStops(140).isEmpty(), "expiration boundary");
        check(service.decision(target, 140) == TimeStopDecision.ALLOW, "expired stop no longer freezes");

        StoppedProjectileState state = StoppedProjectileState.create(Vec3d.ZERO, new Vec3d(2, 0, 0), ProjectileStopMode.ROUNDABOUT_DECELERATE);
        StoppedProjectileState slowed = state.advance(true, true, false);
        close(slowed.position().x(), 0.84, "0.7*0.6 velocity application");
        close(slowed.speedMultiplier(), 0.3654, "post-step 0.87 decay");
        check(!slowed.held(), "not held yet");
        check(slowed.resumeVelocity().equals(new Vec3d(2, 0, 0)), "resume velocity preserved");

        StoppedProjectileState collided = slowed.advance(false, false, true);
        check(collided.held(), "collision holds projectile");
        close(collided.speedMultiplier(), 0.0, "held multiplier");

        StoppedProjectileState placed = StoppedProjectileState.create(Vec3d.ZERO, new Vec3d(1, 0, 0), ProjectileStopMode.PLACE_AND_HOLD);
        check(placed.held(), "place-and-hold begins held");
        check(placed.advance(false, false, false).equals(placed), "place-and-hold remains fixed");

        boolean unresolvedThrown = false;
        try {
            StoppedProjectileState.create(Vec3d.ZERO, new Vec3d(1, 0, 0), ProjectileStopMode.LEGACY_X1_UNRESOLVED)
                    .advance(false, false, false);
        } catch (UnsupportedOperationException expected) {
            unresolvedThrown = true;
        }
        check(unresolvedThrown, "unknown X1 behavior must not be guessed");

        System.out.println("SAKUYA_TIMESTOP_CORE_REGRESSION_PASS");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void close(double actual, double expected, String message) {
        if (Math.abs(actual - expected) > 1.0e-9) {
            throw new AssertionError(message + ": " + actual + " != " + expected);
        }
    }
}
