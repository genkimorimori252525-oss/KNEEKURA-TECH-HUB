package org.kneekura.bedrockwither.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;

/**
 * Bedrock Wither death lifecycle boundary.
 *
 * Current BDS 1.26.51.1 separates DeathTicking, Swell, OverlayAlpha and
 * ShieldFlicker components. Historical Bedrock native code initializes a
 * 200-frame Wither death countdown, increments swell by 1 and overlay alpha by
 * 0.005 per tick, then performs a power-7 final explosion before removal.
 *
 * The 200-tick duration is therefore HISTORICAL_NATIVE_CORROBORATED rather than
 * claimed current-binary exact until direct current-Bedrock measurement closes it.
 *
 * Semantic death remains owned by LivingEntity.die(); this controller only owns
 * the extended Wither-specific ticking/visual state and final removal.
 */
public final class BedrockWitherDeathController {
    public static final int PROVISIONAL_DEATH_DURATION_TICKS = 200;
    public static final float PROVISIONAL_FINAL_EXPLOSION_POWER = 7.0F;
    public static final float HISTORICAL_OVERLAY_ALPHA_STEP = 0.005F;
    public static final float HISTORICAL_SWELL_STEP = 1.0F;
    public static final float HISTORICAL_SWELL_NORMALIZER = 28.0F;

    private final BedrockWitherEntity owner;
    private boolean finalized;

    public BedrockWitherDeathController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public void begin() {
        if (owner.getDeathTicksRemaining() > 0 || finalized) {
            return;
        }

        owner.setDeathTicksRemaining(PROVISIONAL_DEATH_DURATION_TICKS);
        owner.setDeathOldSwell(0.0F);
        owner.setDeathSwell(0.0F);
        owner.setDeathOverlayAlpha(0.0F);
        owner.setDeathShieldFlicker(0);
        owner.setAerialAttack(false);
        owner.runtimeState().setCharging(false);
        owner.runtimeState().setChargeFrames(0);
        owner.stateMachine().enter(BedrockWitherState.DEATH_SEQUENCE);
    }

    public void tickServer() {
        if (finalized) {
            return;
        }

        int remaining = owner.getDeathTicksRemaining();
        if (remaining <= 0) {
            begin();
            remaining = owner.getDeathTicksRemaining();
        }

        // Java's ordinary deathTime drives a 20-tick side-fall animation/removal.
        // Bedrock owns a separate Wither death visual, so keep that timer from
        // becoming the removal authority while the semantic dead flag remains set.
        owner.deathTime = 0;

        float currentSwell = owner.getDeathSwell();
        owner.setDeathOldSwell(currentSwell);
        owner.setDeathSwell(currentSwell + HISTORICAL_SWELL_STEP);
        owner.setDeathOverlayAlpha(Math.min(
                1.0F,
                owner.getDeathOverlayAlpha() + HISTORICAL_OVERLAY_ALPHA_STEP
        ));

        remaining--;
        owner.setDeathTicksRemaining(Math.max(remaining, 0));

        if (remaining <= 0) {
            finishServer();
        }
    }

    public void restore(
            int remainingTicks,
            float oldSwell,
            float swell,
            float overlayAlpha,
            int shieldFlicker,
            BedrockWitherState restoredState
    ) {
        owner.setDeathTicksRemaining(Math.max(remainingTicks, 0));
        owner.setDeathOldSwell(Math.max(0.0F, oldSwell));
        owner.setDeathSwell(Math.max(0.0F, swell));
        owner.setDeathOverlayAlpha(Math.max(0.0F, Math.min(1.0F, overlayAlpha)));
        owner.setDeathShieldFlicker(Math.max(0, shieldFlicker));

        // A persisted entity has not executed terminal removal in this lifetime.
        // Zero remaining ticks on a living save means death has not begun, not
        // that it already finished. Keep both later death and pending death usable.
        finalized = false;
    }

    public float swellAmount(float partialTick) {
        float clampedPartial = Math.max(0.0F, Math.min(1.0F, partialTick));
        float interpolated = owner.getDeathOldSwell()
                + (owner.getDeathSwell() - owner.getDeathOldSwell()) * clampedPartial;
        return interpolated / HISTORICAL_SWELL_NORMALIZER;
    }

    public boolean isActive() {
        return !finalized
                && owner.getBedrockState() == BedrockWitherState.DEATH_SEQUENCE
                && owner.getDeathTicksRemaining() > 0;
    }

    private void finishServer() {
        if (finalized) {
            return;
        }
        finalized = true;

        if (owner.level() instanceof ServerLevel level) {
            level.explode(
                    owner,
                    owner.getX(),
                    owner.getY(),
                    owner.getZ(),
                    PROVISIONAL_FINAL_EXPLOSION_POWER,
                    false,
                    Level.ExplosionInteraction.MOB
            );
            level.broadcastEntityEvent(owner, (byte) 60);
        }

        owner.remove(Entity.RemovalReason.KILLED);
    }
}
