package org.kneekura.bedrockwither.entity;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/**
 * Reachable Java adapter for wither_random_attack_pos_goal. PeratX/source
 * ea30a251 WitherRandomAttackPosGoal::canUse/start/stop corroborates a horizontal
 * random direction around the target, preserving Wither Y, flight speed x15,
 * and a 20-tick stop/shot delay. Current JSON supplies only priority/control flags.
 */
public final class BedrockWitherSpecialMovementController {
    // The inherited generic RandomStroll schema exposes XZ=10. Its use here is
    // PROVISIONAL_SCHEMA_ADAPTER, not proof of the modern Wither initializer.
    public static final double PROVISIONAL_REPOSITION_RADIUS = 10.0D;
    public static final double HISTORICAL_FLIGHT_SPEED_MULTIPLIER = 15.0D;
    public static final int HISTORICAL_STOP_SHOT_DELAY_TICKS = 20;
    // PeratX/source@ea30a251 WitherBoss::aiStep has a separate vertical
    // controller: Y damping 0.6, target-relative height 5, approach speed 0.5.
    // The Java integration is provisional, independent of destination selection.
    public static final double HISTORICAL_AERIAL_HEIGHT = 5.0D;
    public static final double HISTORICAL_VERTICAL_DAMPING = 0.6D;
    public static final double HISTORICAL_ASCENT_SPEED = 0.5D;
    // Finite Java navigation safety budget; not a claimed Bedrock timing value.
    public static final int ADAPTER_MAX_PATH_TICKS = 120;

    private final BedrockWitherEntity owner;

    public BedrockWitherSpecialMovementController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public boolean canBegin() {
        LivingEntity target = owner.getTarget();
        return owner.isAlive() && owner.isValidCombatTarget(target)
                && owner.isAerialAttack() && !owner.runtimeState().charging()
                && !owner.deathController().isActive() && !owner.spawnController().isActive()
                && owner.getBedrockState() != BedrockWitherState.PHASE_TRANSITION
                && owner.runtimeState().wantsMove() && !owner.runtimeState().pathing();
    }

    public void requestMove() {
        if (owner.isAerialAttack() && !owner.phaseController().isSecondPhase()) {
            owner.runtimeState().setWantsMove(true);
        }
    }

    /** Explicit override retained for future adapters; ordinary AI supplies defaults. */
    public void beginMeasuredPath(Vec3 destination, double measuredSpeedModifier) {
        if (!canBegin()) throw new IllegalStateException("Bedrock special reposition preconditions are not met");
        if (!finite(destination)) throw new IllegalArgumentException("destination must be finite");
        if (!Double.isFinite(measuredSpeedModifier) || measuredSpeedModifier < 0.0D) {
            throw new IllegalArgumentException("measuredSpeedModifier must be finite and >= 0");
        }
        if (!owner.getNavigation().moveTo(destination.x, destination.y, destination.z, measuredSpeedModifier)) {
            stopPath(); // Failed/unreachable path must still lead to a finite hover/fire cycle.
            return;
        }
        owner.runtimeState().setPathing(true);
        owner.runtimeState().setMovementTime(0);
        owner.stateMachine().enter(BedrockWitherState.PHASE1_REPOSITION);
    }

    public void tick() {
        if (!owner.isAlive() || owner.spawnController().isActive() || owner.deathController().isActive()
                || !owner.isAerialAttack() || owner.phaseController().isSecondPhase()
                || owner.getBedrockState() == BedrockWitherState.PHASE_TRANSITION) return;

        LivingEntity target = owner.getTarget();
        if (!owner.isValidCombatTarget(target)) {
            if (owner.runtimeState().pathing() || owner.runtimeState().wantsMove()) cancelPath();
            return;
        }
        updateAerialHeight(target);
        if (owner.runtimeState().pathing()) {
            int elapsed = owner.runtimeState().movementTime() + 1;
            owner.runtimeState().setMovementTime(elapsed);
            if (owner.getNavigation().isDone() || elapsed >= ADAPTER_MAX_PATH_TICKS) stopPath();
            return;
        }
        if (owner.getBedrockState() != BedrockWitherState.PHASE1_REPOSITION) return;
        requestMove();
        if (canBegin()) {
            // Java RNG distribution is an adaptation of the historical RandomPos
            // selection; destination shape and own-height preservation are retained.
            double angle = owner.getRandom().nextDouble() * Math.PI * 2.0D;
            Vec3 destination = new Vec3(
                    target.getX() + Math.cos(angle) * PROVISIONAL_REPOSITION_RADIUS,
                    owner.getY(),
                    target.getZ() + Math.sin(angle) * PROVISIONAL_REPOSITION_RADIUS);
            beginMeasuredPath(destination, HISTORICAL_FLIGHT_SPEED_MULTIPLIER);
        }
    }

    private void updateAerialHeight(LivingEntity target) {
        Vec3 motion = owner.getDeltaMovement();
        double vertical = motion.y * HISTORICAL_VERTICAL_DAMPING;
        if (owner.getY() < target.getY() + HISTORICAL_AERIAL_HEIGHT) {
            vertical = Math.max(0.0D, vertical);
            vertical += (HISTORICAL_ASCENT_SPEED - vertical) * HISTORICAL_VERTICAL_DAMPING;
        }
        owner.setDeltaMovement(motion.x, vertical, motion.z);
    }

    public void stopPath() {
        cancelPath();
        if (owner.isAlive() && owner.isAerialAttack() && !owner.spawnController().isActive()
                && !owner.deathController().isActive()
                && owner.getBedrockState() != BedrockWitherState.PHASE_TRANSITION) {
            owner.runtimeState().setDelayShot(HISTORICAL_STOP_SHOT_DELAY_TICKS);
            owner.runtimeState().setMainHeadAttackCountdown(HISTORICAL_STOP_SHOT_DELAY_TICKS);
            owner.runtimeState().setTimeTillNextShot(HISTORICAL_STOP_SHOT_DELAY_TICKS);
            owner.stateMachine().enter(BedrockWitherState.PHASE1_BURST);
        }
    }

    /** Cancel transient navigation without firing or changing the phase. */
    public void cancelPath() {
        owner.getNavigation().stop();
        owner.getMoveControl().setWantedPosition(owner.getX(), owner.getY(), owner.getZ(), 0.0D);
        owner.setDeltaMovement(Vec3.ZERO);
        owner.runtimeState().setWantsMove(false);
        owner.runtimeState().setPathing(false);
        owner.runtimeState().setMovementTime(0);
    }

    private static boolean finite(Vec3 v) {
        return v != null && Double.isFinite(v.x) && Double.isFinite(v.y) && Double.isFinite(v.z);
    }
}
