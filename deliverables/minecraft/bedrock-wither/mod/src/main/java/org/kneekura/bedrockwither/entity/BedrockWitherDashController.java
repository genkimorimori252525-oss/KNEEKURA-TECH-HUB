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

    private final BedrockWitherEntity owner;
    private double activeSpeedPerTick;

    public BedrockWitherDashController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    /**
     * Starts only the evidence-backed execution phase.
     *
     * The exact current Bedrock speed and preparation duration are not yet
     * resolved. Callers must supply a measured speed explicitly; there is
     * intentionally no default that could silently become "the Bedrock speed".
     */
    public void beginMeasuredDash(Vec3 direction, double measuredSpeedPerTick) {
        if (!owner.phaseController().isSecondPhase()) {
            throw new IllegalStateException("Bedrock Wither dash is phase-2 only");
        }
        if (measuredSpeedPerTick < 0.0D || !Double.isFinite(measuredSpeedPerTick)) {
            throw new IllegalArgumentException("measuredSpeedPerTick must be finite and >= 0");
        }

        Vec3 normalized = direction.normalize();
        if (normalized.lengthSqr() < 1.0E-8D) {
            throw new IllegalArgumentException("dash direction must be non-zero");
        }

        activeSpeedPerTick = measuredSpeedPerTick;
        owner.runtimeState().setChargeDirection(normalized);
        owner.runtimeState().setChargeFrames(ACCEPTED_DASH_DURATION_TICKS);
        owner.runtimeState().setCharging(true);
        owner.runtimeState().setPreparingCharge(0);
        owner.stateMachine().enter(BedrockWitherState.PHASE2_DASH);
    }

    public void tick() {
        if (!owner.runtimeState().charging()) {
            return;
        }

        if (!owner.phaseController().isSecondPhase() || !owner.isAlive()) {
            stopDash();
            return;
        }

        Vec3 direction = owner.runtimeState().chargeDirection();
        owner.setDeltaMovement(direction.scale(activeSpeedPerTick));
        owner.hasImpulse = true;

        owner.destructionController().destroyAroundSelf(
                2,
                BedrockWitherAttackType.CHARGE
        );
        damageEntitiesInChargeVolume();

        int remaining = owner.runtimeState().chargeFrames() - 1;
        owner.runtimeState().setChargeFrames(Math.max(remaining, 0));
        if (remaining <= 0) {
            stopDash();
        }
    }

    public void stopDash() {
        owner.runtimeState().setCharging(false);
        owner.runtimeState().setChargeFrames(0);
        activeSpeedPerTick = 0.0D;

        if (owner.isAlive() && owner.phaseController().isSecondPhase()) {
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
