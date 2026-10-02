package org.kneekura.bedrockwither.entity;

import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

/**
 * Center-head firing cycle reconstructed from Bedrock-origin evidence.
 *
 * Strong/current:
 * - 3 normal skulls then 1 dangerous skull.
 * - a long inter-cycle pause, currently observed at about 7 seconds.
 * - firing rate accelerates as the boss loses health.
 *
 * Historical-native corroboration:
 * - base mFireRate initializes to 20.
 * - mHealthIntervals initializes from maxHealth/3.
 * - crossing the next health interval halves mFireRate.
 *
 * Exact current binary timing remains a direct-measurement target, so all
 * provisional native-derived constants are isolated here.
 */
public final class BedrockWitherVolleyController {
    public static final int PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS = 20;
    public static final int OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS = 7 * 20;

    private final BedrockWitherEntity owner;

    public BedrockWitherVolleyController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public void initializeForCurrentDifficulty() {
        int maxHealth = Math.max(1, Math.round(owner.getMaxHealth()));

        owner.runtimeState().setFireRate(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setHealthIntervals(Math.max(1, maxHealth / 3));
        owner.runtimeState().setLastHealthValue(maxHealth);
        owner.runtimeState().setMainHeadAttackCountdown(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setTimeTillNextShot(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setTimeSinceLastShot(0);
    }

    public void onAcceptedDamage() {
        if (owner.phaseController().isSecondPhase()) {
            return;
        }

        Difficulty difficulty = owner.level().getDifficulty();
        if (difficulty == Difficulty.EASY || difficulty == Difficulty.PEACEFUL) {
            return;
        }

        int interval = owner.runtimeState().healthIntervals();
        int lastValue = owner.runtimeState().lastHealthValue();
        if (interval <= 0 || lastValue <= 0) {
            return;
        }

        int nextThreshold = lastValue - interval;
        if (owner.getHealth() < nextThreshold) {
            int currentRate = Math.max(1, owner.runtimeState().fireRate());
            owner.runtimeState().setFireRate(Math.max(1, currentRate / 2));
            owner.runtimeState().setLastHealthValue(nextThreshold);
        }
    }

    public void tick() {
        owner.runtimeState().setTimeSinceLastShot(
                Math.max(0, owner.runtimeState().timeSinceLastShot() + 1)
        );

        if (owner.phaseController().isSecondPhase()
                || owner.runtimeState().charging()
                || owner.getBedrockState() == BedrockWitherState.SPAWN_SEQUENCE
                || owner.getBedrockState() == BedrockWitherState.PHASE_TRANSITION) {
            return;
        }

        LivingEntity target = owner.getTarget();
        if (target == null || !target.isAlive()) {
            if (owner.getBedrockState() == BedrockWitherState.PHASE1_BURST) {
                owner.stateMachine().enter(BedrockWitherState.PHASE1_REPOSITION);
            }
            return;
        }

        if (owner.getBedrockState() == BedrockWitherState.PHASE1_REPOSITION) {
            owner.stateMachine().enter(BedrockWitherState.PHASE1_BURST);
            ensureCountdown();
            return;
        }

        int remaining = Math.max(0, owner.runtimeState().mainHeadAttackCountdown() - 1);
        owner.runtimeState().setMainHeadAttackCountdown(remaining);
        owner.runtimeState().setTimeTillNextShot(remaining);

        if (owner.getBedrockState() == BedrockWitherState.PHASE1_COOLDOWN) {
            if (remaining <= 0) {
                owner.stateMachine().enter(BedrockWitherState.PHASE1_BURST);
                armCountdown(owner.runtimeState().fireRate());
            }
            return;
        }

        if (owner.getBedrockState() != BedrockWitherState.PHASE1_BURST || remaining > 0) {
            return;
        }

        fireCenterHead(target);
    }

    private void fireCenterHead(LivingEntity target) {
        BedrockWitherSkullEntity.Kind kind = owner.attackController().nextCenterSkullKind();

        // Historical Bedrock getFiringPos() places center-head shots at body Y+3.
        // Current BDS retains a dedicated getFiringPos() virtual boundary.
        Vec3 origin = new Vec3(owner.getX(), owner.getY() + 3.0D, owner.getZ());
        owner.attackController().fireSkull(origin, target.getEyePosition(), kind);

        owner.runtimeState().setLastFiredHead(0);
        owner.runtimeState().setTimeSinceLastShot(0);

        if (kind == BedrockWitherSkullEntity.Kind.DANGEROUS) {
            owner.stateMachine().enter(BedrockWitherState.PHASE1_COOLDOWN);
            owner.runtimeState().setDelayShot(OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS);
            armCountdown(OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS);
        } else {
            owner.runtimeState().setDelayShot(0);
            armCountdown(owner.runtimeState().fireRate());
        }
    }

    private void ensureCountdown() {
        if (owner.runtimeState().mainHeadAttackCountdown() <= 0) {
            armCountdown(owner.runtimeState().fireRate());
        }
    }

    private void armCountdown(int ticks) {
        int bounded = Math.max(1, ticks);
        owner.runtimeState().setMainHeadAttackCountdown(bounded);
        owner.runtimeState().setTimeTillNextShot(bounded);
    }
}
