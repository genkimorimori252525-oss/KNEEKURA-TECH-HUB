package org.kneekura.bedrockwither.entity;

import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

/**
 * Center-head 3-normal/1-dangerous cycle in both phases. The reported 7-second
 * inter-volley pause is independent of the per-projectile firing rate.
 *
 * Exact modern rates are not published. The explicitly provisional fallback is
 * PeratX/source@ea30a251: base 20, integer maxHealth/6 health interval (SMMUL with
 * 0x2AAAAAAB), strict threshold, one halving per accepted hit except on Easy,
 * and base-rate reset at phase change. Modern 75-HP NBT buckets are separate.
 */
public final class BedrockWitherVolleyController {
    public static final int PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS = 20;
    public static final int OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS = 7 * 20;
    public static final int CURRENT_LAST_HEALTH_INTERVAL_STEP = 75;

    private final BedrockWitherEntity owner;
    private int lowestHealthSeen;

    public BedrockWitherVolleyController(BedrockWitherEntity owner) { this.owner = owner; }

    public void initializeForCurrentDifficulty() {
        int maxHealth = Math.max(1, Math.round(owner.getMaxHealth()));
        owner.runtimeState().setFireRate(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setHealthIntervals(Math.max(1, maxHealth / 6));
        owner.runtimeState().setHistoricalRateHealthCursor(maxHealth);
        lowestHealthSeen = maxHealth;
        owner.runtimeState().setLastHealthValue(lastHealthIntervalFor(maxHealth));
        armCountdown(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setTimeSinceLastShot(0);
    }

    public void onAcceptedDamage() {
        int currentHealth = Math.max(0, Math.round(owner.getHealth()));
        if (currentHealth < lowestHealthSeen) {
            lowestHealthSeen = currentHealth;
            owner.runtimeState().setLastHealthValue(lastHealthIntervalFor(lowestHealthSeen));
        }
        int interval = Math.max(1, owner.runtimeState().healthIntervals());
        int threshold = owner.runtimeState().historicalRateHealthCursor() - interval;
        if (owner.level().getDifficulty() != Difficulty.EASY && currentHealth < threshold) {
            // Historical VCVTR follows native FPSCR rounding. Java's ties-to-even
            // plus minimum one tick is an explicit adapter for rates after 20/10/5.
            owner.runtimeState().setFireRate(Math.max(1,
                    (int) Math.rint(owner.runtimeState().fireRate() * 0.5D)));
            owner.runtimeState().setHistoricalRateHealthCursor(threshold);
        }
    }

    public void onHalfHealthTransition() {
        owner.runtimeState().setFireRate(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        owner.runtimeState().setSecondVolley(false);
        // Java stage-reset adapter: restart the historical interval cursor at
        // half health alongside the reported base-rate reset. Otherwise the
        // historical cursor can immediately re-halve at 299/600 HP. This does
        // not claim an exact modern acceleration formula for every difficulty.
        owner.runtimeState().setHistoricalRateHealthCursor(Math.round(owner.getMaxHealth()) / 2);
        // Do not carry a partial first-phase burst into the every-second-burst count.
        owner.runtimeState().setProjectileCounter(0);
        owner.runtimeState().setDelayShot(0);
        armCountdown(PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
    }

    public void restoreLastHealthInterval(int lastInterval) {
        int bounded = Math.max(0, lastInterval);
        owner.runtimeState().setLastHealthValue(bounded);
        lowestHealthSeen = bounded + 1;
    }

    public static int lastHealthIntervalFor(int lowestHealth) {
        return lowestHealth <= 0 ? 0 : ((lowestHealth - 1) / CURRENT_LAST_HEALTH_INTERVAL_STEP)
                * CURRENT_LAST_HEALTH_INTERVAL_STEP;
    }

    public void tick() {
        if (!owner.isAlive() || owner.deathController().isActive()
                || owner.spawnController().isActive() || owner.runtimeState().charging()) return;
        BedrockWitherState state = owner.getBedrockState();
        if (state == BedrockWitherState.PHASE_TRANSITION || state == BedrockWitherState.SPAWN_SEQUENCE
                || state == BedrockWitherState.PHASE2_DASH_PREP || state == BedrockWitherState.PHASE2_RECOVER) return;
        owner.runtimeState().setTimeSinceLastShot(Math.min(Integer.MAX_VALUE - 1,
                owner.runtimeState().timeSinceLastShot()) + 1);

        boolean cooldown = state == BedrockWitherState.PHASE1_COOLDOWN
                || state == BedrockWitherState.PHASE2_COOLDOWN;
        boolean burst = state == BedrockWitherState.PHASE1_BURST || state == BedrockWitherState.PHASE2_BURST;
        // Native shot-delay progression is independent of target availability.
        // This shared gate also blocks passive side heads, so losing a target
        // must not freeze it. Lifecycle/preparation/recovery gates above retain
        // their own timer ownership; decrement these combat timers only once.
        owner.runtimeState().setDelayShot(Math.max(0, owner.runtimeState().delayShot() - 1));
        int remaining = owner.runtimeState().mainHeadAttackCountdown();
        if (cooldown || burst) {
            remaining = Math.max(0, remaining - 1);
            owner.runtimeState().setMainHeadAttackCountdown(remaining);
            owner.runtimeState().setTimeTillNextShot(remaining);
        }

        LivingEntity target = owner.getTarget();
        if (!owner.isValidCombatTarget(target)) return;
        if (owner.runtimeState().pathing() || owner.runtimeState().wantsMove()) return;

        if (state == BedrockWitherState.PHASE1_REPOSITION) {
            // Controller-only adapters may call this after an externally completed
            // move. Ordinary entity AI always gives specialMovement.tick first turn.
            owner.stateMachine().enter(BedrockWitherState.PHASE1_BURST);
            armCountdown(Math.max(1, owner.runtimeState().fireRate()));
            return;
        }
        if (!cooldown && !burst) return;
        if (remaining > 0) return;
        if (cooldown) {
            if (owner.phaseController().isSecondPhase()) {
                owner.stateMachine().enter(BedrockWitherState.PHASE2_BURST);
                // The elapsed 140 ticks already are the whole inter-volley gap;
                // adding fireRate here made the observable pause 160/150 ticks.
                fireCenterHead(target);
                return;
            } else {
                owner.stateMachine().enter(BedrockWitherState.PHASE1_REPOSITION);
                owner.specialMovementController().requestMove();
            }
            armCountdown(owner.runtimeState().fireRate());
            return;
        }
        fireCenterHead(target);
    }

    private void fireCenterHead(LivingEntity target) {
        BedrockWitherSkullEntity.Kind kind = owner.attackController().nextCenterSkullKind();
        owner.attackController().fireSkull(new Vec3(owner.getX(), owner.getY() + 3.0D, owner.getZ()),
                target.getEyePosition(), kind);
        owner.runtimeState().setLastFiredHead(0);
        owner.runtimeState().setTimeSinceLastShot(0);
        if (kind != BedrockWitherSkullEntity.Kind.DANGEROUS) {
            armCountdown(owner.runtimeState().fireRate());
            return;
        }
        if (owner.phaseController().isSecondPhase()) {
            boolean chargeThisVolley = owner.runtimeState().secondVolley();
            owner.runtimeState().setSecondVolley(!chargeThisVolley);
            if (chargeThisVolley) {
                owner.dashController().prepareTargetCharge();
                return;
            }
        }
        owner.stateMachine().enter(owner.phaseController().isSecondPhase()
                ? BedrockWitherState.PHASE2_COOLDOWN : BedrockWitherState.PHASE1_COOLDOWN);
        owner.runtimeState().setDelayShot(OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS);
        armCountdown(OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS);
    }

    private void armCountdown(int ticks) {
        int bounded = Math.max(1, ticks);
        owner.runtimeState().setMainHeadAttackCountdown(bounded);
        owner.runtimeState().setTimeTillNextShot(bounded);
    }
}
