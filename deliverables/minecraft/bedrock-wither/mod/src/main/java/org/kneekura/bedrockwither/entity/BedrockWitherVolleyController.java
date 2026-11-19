package org.kneekura.bedrockwither.entity;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

/**
 * Center-head firing cycle reconstructed from Bedrock-origin evidence.
 *
 * Accepted/current:
 * - 3 normal skulls then 1 dangerous skull.
 * - roughly 7 seconds between completed firing cycles.
 * - firing accelerates around current-observed health points 500/400,
 *   resets to the original rate at half health, then accelerates again at 200/100.
 * - Bedrock NBT lastHealthInterval tracks the greatest multiple of 75 below
 *   the lowest health reached and does not increase after healing.
 *
 * Not yet current-quantified:
 * - exact ticks-per-shot at each acceleration stage.
 *
 * Therefore KNEEKURA keeps the known base/native-shaped fire-rate state but does
 * NOT invent the accelerated tick values. The health bucket is tracked separately
 * so a later Bedrock measurement can bind the exact rate table without changing
 * targeting/projectile/state architecture.
 */
public final class BedrockWitherVolleyController {
    public static final int PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS = 20;
    public static final int OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS = 7 * 20;
    public static final int CURRENT_LAST_HEALTH_INTERVAL_STEP = 75;

    private final BedrockWitherEntity owner;
    private int lowestHealthSeen;

    public BedrockWitherVolleyController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public void initializeForCurrentDifficulty() {
        int maxHealth = Math.max(1, Math.round(owner.getMaxHealth()));

        owner.runtimeState().setFireRate(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        // Current BDS exposes mHealthIntervals, but its exact initialization is
        // unresolved. Do not reuse the historical maxHealth/3 value as current.
        owner.runtimeState().setHealthIntervals(0);

        lowestHealthSeen = maxHealth;
        owner.runtimeState().setLastHealthValue(lastHealthIntervalFor(maxHealth));
        owner.runtimeState().setMainHeadAttackCountdown(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setTimeTillNextShot(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setTimeSinceLastShot(0);
    }

    public void onAcceptedDamage() {
        int currentHealth = Math.max(0, Math.round(owner.getHealth()));
        if (currentHealth < lowestHealthSeen) {
            lowestHealthSeen = currentHealth;
            owner.runtimeState().setLastHealthValue(lastHealthIntervalFor(lowestHealthSeen));
        }

        // Current observation gives health thresholds where firing accelerates,
        // but not the exact current ticks-per-shot for every stage. Deliberately
        // leave mFireRate unchanged until direct measurement binds those values.
    }

    public void onHalfHealthTransition() {
        // Current behavior: the second phase begins firing at the original rate.
        owner.runtimeState().setFireRate(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setMainHeadAttackCountdown(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setTimeTillNextShot(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
    }

    public void restoreLastHealthInterval(int lastInterval) {
        int bounded = Math.max(0, lastInterval);
        owner.runtimeState().setLastHealthValue(bounded);

        // Exact minimum HP is not recoverable from the interval alone. The lowest
        // value that would produce this strict-lower bucket is interval+1, which
        // safely prevents healing from increasing the saved interval.
        lowestHealthSeen = bounded + 1;
    }

    public static int lastHealthIntervalFor(int lowestHealth) {
        if (lowestHealth <= 0) {
            return 0;
        }
        // Greatest multiple of 75 strictly lower than the lowest health.
        return ((lowestHealth - 1) / CURRENT_LAST_HEALTH_INTERVAL_STEP)
                * CURRENT_LAST_HEALTH_INTERVAL_STEP;
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
