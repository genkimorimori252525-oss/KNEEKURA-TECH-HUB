package org.kneekura.bedrockwither.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;

/**
 * Modern Bedrock spawn-sequence boundary.
 *
 * Current gameplay documentation: ~11 seconds of invulnerability -> 220 ticks.
 * Historical Bedrock native body used 200 ticks. The product targets current
 * behavior and preserves the old value only in research history.
 */
public final class BedrockWitherSpawnController {
    public static final int CURRENT_SPAWN_DURATION_TICKS = 220;
    public static final int JAVA_WITHER_SPAWN_LEVEL_EVENT = 1023;
    public static final float SPAWN_EXPLOSION_POWER = 7.0F;

    private final BedrockWitherEntity owner;
    private boolean completed;

    public BedrockWitherSpawnController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public void initializeNewEntity() {
        owner.setSpawningFrames(CURRENT_SPAWN_DURATION_TICKS);
        owner.setAerialAttack(true);
        owner.stateMachine().enter(BedrockWitherState.SPAWN_SEQUENCE);
        completed = false;
    }

    public void tick() {
        if (completed || owner.getBedrockState() != BedrockWitherState.SPAWN_SEQUENCE) {
            return;
        }

        int remaining = owner.runtimeState().spawningFrames();
        if (remaining > 0) {
            remaining--;
            owner.setSpawningFrames(remaining);
        }

        if (remaining <= 0) {
            completeSpawn();
        }
    }

    public boolean isActive() {
        return !completed
                && owner.getBedrockState() == BedrockWitherState.SPAWN_SEQUENCE
                && owner.runtimeState().spawningFrames() > 0;
    }

    public void restore(int spawningFrames, BedrockWitherState restoredState) {
        owner.setSpawningFrames(Math.max(0, spawningFrames));
        completed = restoredState != BedrockWitherState.SPAWN_SEQUENCE
                || owner.runtimeState().spawningFrames() <= 0;
    }

    private void completeSpawn() {
        if (completed) {
            return;
        }
        completed = true;
        owner.setSpawningFrames(0);

        if (owner.level() instanceof ServerLevel level) {
            level.explode(
                    owner,
                    owner.getX(),
                    owner.getY(),
                    owner.getZ(),
                    SPAWN_EXPLOSION_POWER,
                    false,
                    Level.ExplosionInteraction.MOB
            );
            if (!owner.isSilent()) {
                // Java's global Wither spawn event is a practical sound bridge
                // for the Bedrock spawn cue without reusing Java Wither AI.
                level.globalLevelEvent(JAVA_WITHER_SPAWN_LEVEL_EVENT, owner.blockPosition(), 0);
            }
        }

        owner.stateMachine().enter(BedrockWitherState.PHASE1_REPOSITION);
    }
}
