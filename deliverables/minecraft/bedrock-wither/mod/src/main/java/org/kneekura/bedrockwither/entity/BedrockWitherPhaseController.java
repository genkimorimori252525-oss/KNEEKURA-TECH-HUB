package org.kneekura.bedrockwither.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.WitherSkeleton;
import net.minecraft.world.level.Level;

public final class BedrockWitherPhaseController {
    /**
     * Historical Bedrock native body uses 7.0 for the wants-to-explode transition.
     * Current Bedrock documentation describes the half-health explosion as equivalent
     * to the spawn explosion. Keep this isolated as HISTORICAL_CORROBORATED until
     * current BDS runtime measurement confirms the exact power.
     */
    public static final float PROVISIONAL_TRANSITION_EXPLOSION_POWER = 7.0F;

    // Native aiStep applies downward acceleration while wantsToExplode. This
    // bounded constant-speed Java descent is an adapter, not modern parity data.
    public static final double ADAPTER_DESCENT_SPEED = 1.0D;
    public static final int ADAPTER_MAX_DESCENT_TICKS = 100;

    private static final int SECOND_PHASE_NATIVE_ID = 0;
    private static final int FIRST_PHASE_NATIVE_ID = 1;
    private static final int PHASE_TWO_SKELETON_COUNT = 3;

    private final BedrockWitherEntity owner;

    public BedrockWitherPhaseController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public void initializeForCurrentDifficulty() {
        int maxHealth = Math.round(owner.getMaxHealth());
        owner.runtimeState().setNativeMaxHealth(maxHealth);
        owner.runtimeState().setHealthThreshold(maxHealth / 2);

        // Historical Bedrock initializes Phase=1 and changePhase() decrements it
        // to 0. Current BDS still exposes mPhase, and current gameplay still has
        // the same two-stage half-health transition.
        if (owner.runtimeState().nativePhase() != SECOND_PHASE_NATIVE_ID) {
            owner.runtimeState().setNativePhase(FIRST_PHASE_NATIVE_ID);
        }
    }

    public void tick() {
        if (!owner.isAlive() || owner.spawnController().isActive() || owner.deathController().isActive()) return;
        if (owner.runtimeState().nativePhase() == FIRST_PHASE_NATIVE_ID
                && owner.getHealth() <= owner.runtimeState().healthThreshold()) beginHalfHealthTransition();
        if (owner.getBedrockState() != BedrockWitherState.PHASE_TRANSITION) return;
        if (!owner.runtimeState().wantsToExplode()) {
            // Completed or older save with no pending one-shot work must recover.
            owner.stateMachine().enter(BedrockWitherState.PHASE2_RECOVER);
            return;
        }
        owner.runtimeState().setTransitionTicks(owner.runtimeState().transitionTicks() + 1);
        boolean grounded = owner.onGround()
                || owner.level().getBlockCollisions(owner,
                        owner.getBoundingBox().move(0.0D, -0.1D, 0.0D)).iterator().hasNext();
        boolean boundedFallback = owner.runtimeState().transitionTicks() >= ADAPTER_MAX_DESCENT_TICKS
                || owner.getY() <= owner.level().getMinBuildHeight() + 2.0D;
        if (grounded || boundedFallback) {
            owner.setDeltaMovement(net.minecraft.world.phys.Vec3.ZERO);
            performHalfHealthTransition();
        } else {
            owner.setDeltaMovement(0.0D, -ADAPTER_DESCENT_SPEED, 0.0D);
            owner.hasImpulse = true;
        }
    }

    public boolean isSecondPhase() {
        return owner.runtimeState().nativePhase() == SECOND_PHASE_NATIVE_ID;
    }

    private void beginHalfHealthTransition() {
        owner.specialMovementController().cancelPath();
        owner.runtimeState().setTransitionTicks(0);
        owner.runtimeState().setNativePhase(SECOND_PHASE_NATIVE_ID);
        owner.setAerialAttack(false);
        owner.volleyController().onHalfHealthTransition();
        owner.runtimeState().setWantsToExplode(true);
        owner.stateMachine().enter(BedrockWitherState.PHASE_TRANSITION);
    }

    private void performHalfHealthTransition() {
        if (!(owner.level() instanceof ServerLevel level)) {
            return;
        }

        // Consume before side effects so reentrant save/event code cannot replay
        // the explosion and skeletons. Tick-thread saves are otherwise serialized.
        owner.runtimeState().setWantsToExplode(false);
        level.explode(
                owner,
                owner.getX(),
                owner.getY(),
                owner.getZ(),
                PROVISIONAL_TRANSITION_EXPLOSION_POWER,
                false,
                Level.ExplosionInteraction.MOB
        );

        int desiredSkeletons = switch (level.getDifficulty()) {
            case PEACEFUL, EASY -> 0;
            case NORMAL, HARD -> PHASE_TWO_SKELETON_COUNT;
        };

        int spawned = 0;
        LivingEntity target = owner.getTarget();
        for (int i = 0; i < desiredSkeletons; i++) {
            WitherSkeleton skeleton = EntityType.WITHER_SKELETON.create(level);
            if (skeleton == null) {
                continue;
            }

            double angle = (Math.PI * 2.0D * i) / Math.max(1, desiredSkeletons);
            skeleton.moveTo(
                    owner.getX() + Math.cos(angle) * 1.5D,
                    owner.getY(),
                    owner.getZ() + Math.sin(angle) * 1.5D,
                    owner.getYRot(),
                    0.0F
            );
            if (owner.isValidCombatTarget(target)) {
                skeleton.setTarget(target);
            }

            if (level.addFreshEntity(skeleton)) {
                spawned++;
            }
        }

        owner.runtimeState().setMaxSkeletons(desiredSkeletons);
        owner.runtimeState().setNumSkeletons(spawned);
        owner.runtimeState().setWantsToExplode(false);
        owner.stateMachine().enter(BedrockWitherState.PHASE2_BURST);
    }

    public static int firstPhaseNativeId() {
        return FIRST_PHASE_NATIVE_ID;
    }

    public static int secondPhaseNativeId() {
        return SECOND_PHASE_NATIVE_ID;
    }
}
