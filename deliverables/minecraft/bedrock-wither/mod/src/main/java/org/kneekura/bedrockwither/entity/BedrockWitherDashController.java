package org.kneekura.bedrockwither.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

public final class BedrockWitherDashController {
    /**
     * Current Bedrock runtime observation reports ~1 second / 20 game ticks.
     * Historical native body also carries a dedicated charge frame counter.
     */
    public static final int ACCEPTED_DASH_DURATION_TICKS = 20;

    /**
     * Historical Bedrock native body applies 15 entity damage during charge,
     * matching maintained current gameplay documentation.
     */
    public static final float ACCEPTED_DASH_DAMAGE = 15.0F;

    // PeratX/source@ea30a251 newServerAiStep sets preparingCharge=20;
    // aiStep doubles X/Z direction. Vertical/native steering is not fully recovered.
    public static final int HISTORICAL_PREPARATION_TICKS = 20;
    public static final double PROVISIONAL_HORIZONTAL_SPEED_PER_TICK = 2.0D;
    public static final int HISTORICAL_RECOVERY_TICKS = 20;

    private final BedrockWitherEntity owner;
    private double activeSpeedPerTick;

    public BedrockWitherDashController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    /** Explicit speed override retained; ordinary AI uses the named historical fallback. */
    public void beginMeasuredDash(Vec3 direction, double measuredSpeedPerTick) {
        if (!owner.isAlive() || owner.spawnController().isActive() || owner.deathController().isActive()
                || owner.getBedrockState() == BedrockWitherState.PHASE_TRANSITION
                || !owner.phaseController().isSecondPhase()) {
            throw new IllegalStateException("Dash requires phase-2 combat outside lifecycle transitions");
        }
        if (measuredSpeedPerTick < 0.0D || !Double.isFinite(measuredSpeedPerTick)) {
            throw new IllegalArgumentException("measuredSpeedPerTick must be finite and >= 0");
        }

        if (direction == null || !Double.isFinite(direction.x)
                || !Double.isFinite(direction.y) || !Double.isFinite(direction.z)) {
            throw new IllegalArgumentException("dash direction must be finite");
        }
        Vec3 normalized = direction.normalize();
        if (normalized.lengthSqr() < 1.0E-8D) {
            throw new IllegalArgumentException("dash direction must be non-zero");
        }

        owner.specialMovementController().cancelPath();
        activeSpeedPerTick = measuredSpeedPerTick;
        owner.runtimeState().setChargeDirection(normalized);
        owner.runtimeState().setChargeFrames(ACCEPTED_DASH_DURATION_TICKS);
        owner.runtimeState().setCharging(true);
        owner.runtimeState().setPreparingCharge(0);
        owner.stateMachine().enter(BedrockWitherState.PHASE2_DASH);
    }

    public void prepareTargetCharge() {
        if (!owner.phaseController().isSecondPhase() || !owner.isAlive()
                || owner.spawnController().isActive() || owner.deathController().isActive()
                || owner.getBedrockState() == BedrockWitherState.PHASE_TRANSITION
                || !owner.isValidCombatTarget(owner.getTarget())) return;
        owner.specialMovementController().cancelPath();
        owner.runtimeState().setPreparingCharge(HISTORICAL_PREPARATION_TICKS);
        owner.runtimeState().setDelayShot(0);
        owner.stateMachine().enter(BedrockWitherState.PHASE2_DASH_PREP);
    }

    public void tick() {
        if (!owner.isAlive() || owner.deathController().isActive() || owner.spawnController().isActive()) return;
        if (owner.getBedrockState() == BedrockWitherState.PHASE2_RECOVER) {
            owner.setDeltaMovement(Vec3.ZERO);
            int remaining = Math.max(0, owner.runtimeState().delayShot() - 1);
            owner.runtimeState().setDelayShot(remaining);
            if (remaining == 0) {
                owner.stateMachine().enter(BedrockWitherState.PHASE2_BURST);
                owner.runtimeState().setMainHeadAttackCountdown(Math.max(1, owner.runtimeState().fireRate()));
                owner.runtimeState().setTimeTillNextShot(Math.max(1, owner.runtimeState().fireRate()));
            }
            return;
        }
        if (owner.getBedrockState() == BedrockWitherState.PHASE2_DASH_PREP) {
            LivingEntity target = owner.getTarget();
            if (!owner.isValidCombatTarget(target)) { stopDash(); return; }
            owner.setDeltaMovement(Vec3.ZERO);
            int remaining = Math.max(0, owner.runtimeState().preparingCharge() - 1);
            owner.runtimeState().setPreparingCharge(remaining);
            if (remaining == 0) {
                // Horizontal projection is a Java steering adapter. The native
                // source normalizes 3D then doubles X/Z; its Y branch is incomplete.
                Vec3 toward = target.position().subtract(owner.position());
                Vec3 horizontal = new Vec3(toward.x, 0.0D, toward.z);
                if (horizontal.lengthSqr() < 1.0E-8D) { stopDash(); return; }
                beginMeasuredDash(horizontal, PROVISIONAL_HORIZONTAL_SPEED_PER_TICK);
            }
            return;
        }
        if (!owner.runtimeState().charging()) return;
        if (!owner.phaseController().isSecondPhase()) { stopDash(); return; }

        Vec3 velocity = owner.runtimeState().chargeDirection().scale(activeSpeedPerTick);
        owner.destructionController().destroyAroundSelf(2, BedrockWitherAttackType.CHARGE);
        // Honor Java collision after authorized destruction. Unbreakable blocks
        // terminate the charge finitely instead of tunnelling or waiting forever.
        if (!owner.level().noCollision(owner, owner.getBoundingBox().move(velocity))) {
            stopDash();
            return;
        }
        owner.setDeltaMovement(velocity);
        owner.hasImpulse = true;
        damageEntitiesInChargeVolume();
        int remaining = owner.runtimeState().chargeFrames() - 1;
        owner.runtimeState().setChargeFrames(Math.max(remaining, 0));
        if (remaining <= 0) {
            // Mob.customServerAiStep runs BEFORE LivingEntity.travel. Keep the
            // twentieth velocity through travel, then clear it in the entity's
            // post-tick hook; stopping here would execute only nineteen steps.
            clearChargeState();
            owner.runtimeState().setDelayShot(HISTORICAL_RECOVERY_TICKS);
            owner.stateMachine().enter(BedrockWitherState.PHASE2_RECOVER);
        }
    }

    public void afterEntityMovement() {
        if (owner.getBedrockState() == BedrockWitherState.PHASE2_RECOVER) {
            owner.setDeltaMovement(Vec3.ZERO);
        }
    }

    private void clearChargeState() {
        owner.runtimeState().setCharging(false);
        owner.runtimeState().setChargeFrames(0);
        owner.runtimeState().setPreparingCharge(0);
        owner.runtimeState().setChargeDirection(Vec3.ZERO);
        activeSpeedPerTick = 0.0D;
    }

    public void stopDash() {
        clearChargeState();
        owner.specialMovementController().cancelPath();
        if (owner.isAlive() && owner.phaseController().isSecondPhase()
                && !owner.deathController().isActive()) {
            owner.runtimeState().setDelayShot(HISTORICAL_RECOVERY_TICKS);
            owner.stateMachine().enter(BedrockWitherState.PHASE2_RECOVER);
        }
    }

    private void damageEntitiesInChargeVolume() {
        if (!(owner.level() instanceof ServerLevel level)) {
            return;
        }

        // Historical native body grows the boss AABB by 1 horizontally and 4
        // vertically while charging before applying 15 damage.
        AABB hitVolume = owner.getBoundingBox().inflate(1.0D, 4.0D, 1.0D);
        for (LivingEntity living : level.getEntitiesOfClass(
                LivingEntity.class,
                hitVolume,
                candidate -> candidate != owner && candidate.isAlive()
        )) {
            living.hurt(level.damageSources().mobAttack(owner), ACCEPTED_DASH_DAMAGE);
        }
    }

    public double activeSpeedPerTick() {
        return activeSpeedPerTick;
    }
}
