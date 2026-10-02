package org.kneekura.bedrockwither.entity;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/**
 * Boundary for Bedrock's wither_random_attack_pos_goal.
 *
 * Current BDS proves:
 * - the goal derives from RandomStrollGoal;
 * - it owns an isPathing flag;
 * - WitherBoss separately owns wantsMove/pathing/movement counters.
 *
 * Historical native behavior corroborates:
 * - requires a live target;
 * - is phase-1/aerial only;
 * - requires wantsMove=true;
 * - start marks pathing;
 * - stop clears wantsMove/pathing and returns to firing flow.
 *
 * Exact current destination radius, vertical distribution, speed multiplier,
 * interval and stop-delay remain unresolved. This controller therefore requires
 * measured values to be supplied explicitly and never invents defaults.
 */
public final class BedrockWitherSpecialMovementController {
    private final BedrockWitherEntity owner;

    public BedrockWitherSpecialMovementController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public boolean canBegin() {
        LivingEntity target = owner.getTarget();
        return owner.isAlive()
                && target != null
                && target.isAlive()
                && owner.isAerialAttack()
                && !owner.runtimeState().charging()
                && !owner.deathController().isActive()
                && !owner.spawnController().isActive()
                && owner.getBedrockState() != BedrockWitherState.PHASE_TRANSITION
                && owner.runtimeState().wantsMove()
                && !owner.runtimeState().pathing();
    }

    public void requestMove() {
        if (!owner.isAerialAttack() || owner.phaseController().isSecondPhase()) {
            return;
        }
        owner.runtimeState().setWantsMove(true);
    }

    public void beginMeasuredPath(Vec3 destination, double measuredSpeedModifier) {
        if (!canBegin()) {
            throw new IllegalStateException("Bedrock special reposition preconditions are not met");
        }
        if (destination == null
                || !Double.isFinite(destination.x)
                || !Double.isFinite(destination.y)
                || !Double.isFinite(destination.z)) {
            throw new IllegalArgumentException("destination must be finite");
        }
        if (!Double.isFinite(measuredSpeedModifier) || measuredSpeedModifier < 0.0D) {
            throw new IllegalArgumentException("measuredSpeedModifier must be finite and >= 0");
        }

        boolean accepted = owner.getNavigation().moveTo(
                destination.x,
                destination.y,
                destination.z,
                measuredSpeedModifier
        );
        if (!accepted) {
            return;
        }

        owner.runtimeState().setPathing(true);
        owner.stateMachine().enter(BedrockWitherState.PHASE1_REPOSITION);
    }

    public void tick() {
        if (!owner.runtimeState().pathing()) {
            return;
        }

        if (!owner.isAerialAttack()
                || owner.phaseController().isSecondPhase()
                || owner.getTarget() == null
                || !owner.getTarget().isAlive()) {
            stopPath();
            return;
        }

        if (owner.getNavigation().isDone()) {
            stopPath();
        }
    }

    public void stopPath() {
        owner.getNavigation().stop();
        owner.runtimeState().setWantsMove(false);
        owner.runtimeState().setPathing(false);

        if (owner.isAlive() && owner.isAerialAttack()) {
            owner.stateMachine().enter(BedrockWitherState.PHASE1_BURST);
        }
    }
}
