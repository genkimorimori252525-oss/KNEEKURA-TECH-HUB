package org.kneekura.bedrockwither.entity;

import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

/**
 * Bedrock side-head idle/dangerous-skull scheduler.
 *
 * Historical native aiStep and current BDS field layout agree on per-head
 * next-update and idle-update counters. The historical body:
 * - updates each side head on a 10..19 tick schedule;
 * - on Normal/Hard increments an idle counter;
 * - at 16 idle updates fires one dangerous skull at a random nearby point and
 *   resets the counter.
 *
 * Current Bedrock technical observation independently reports a passive
 * dangerous skull roughly every ~15 seconds in stage 1. The random timing makes
 * that observation consistent with the native 16 * (10..19) tick mechanism.
 */
public final class BedrockWitherSideHeadController {
    public static final int HISTORICAL_MIN_UPDATE_DELAY = 10;
    public static final int HISTORICAL_UPDATE_DELAY_SPAN = 10;
    public static final int CORROBORATED_IDLE_DANGEROUS_THRESHOLD = 16;

    private final BedrockWitherEntity owner;

    public BedrockWitherSideHeadController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public void tick() {
        if (!canRun()) {
            return;
        }

        processHead(1);
        processHead(2);
    }

    public static boolean passiveDangerousEnabled(Difficulty difficulty) {
        return difficulty == Difficulty.NORMAL || difficulty == Difficulty.HARD;
    }

    private boolean canRun() {
        return owner.isAlive()
                && owner.isAerialAttack()
                && !owner.spawnController().isActive()
                && !owner.deathController().isActive()
                && !owner.runtimeState().charging()
                && owner.getBedrockState() != BedrockWitherState.PHASE_TRANSITION;
    }

    private void processHead(int headIndex) {
        BedrockWitherHeadRuntime head = owner.runtimeState().head(headIndex);
        int now = owner.tickCount;

        if (head.nextUpdate() <= 0) {
            head.setNextUpdate(now + nextUpdateDelay());
            return;
        }
        if (now < head.nextUpdate()) {
            return;
        }

        head.setNextUpdate(now + nextUpdateDelay());

        if (!passiveDangerousEnabled(owner.level().getDifficulty())) {
            head.setIdleUpdates(0);
            return;
        }

        int idle = head.idleUpdates() + 1;
        head.setIdleUpdates(idle);
        if (idle < CORROBORATED_IDLE_DANGEROUS_THRESHOLD) {
            return;
        }

        head.setIdleUpdates(0);
        firePassiveDangerous(headIndex);
    }

    private int nextUpdateDelay() {
        return HISTORICAL_MIN_UPDATE_DELAY
                + owner.getRandom().nextInt(HISTORICAL_UPDATE_DELAY_SPAN);
    }

    private void firePassiveDangerous(int headIndex) {
        // Historical native target box:
        // X/Z: owner +/- 10 blocks, Y: owner +/- 5 blocks.
        // Current Wiki reports a passive dangerous shot but does not expose the
        // random-box constants; retain these as historical-corroborated values.
        Vec3 target = new Vec3(
                owner.getX() - 10.0D + owner.getRandom().nextDouble() * 20.0D,
                owner.getY() - 5.0D + owner.getRandom().nextDouble() * 10.0D,
                owner.getZ() - 10.0D + owner.getRandom().nextDouble() * 20.0D
        );

        owner.attackController().fireSkull(
                firingPosition(headIndex),
                target,
                BedrockWitherSkullEntity.Kind.DANGEROUS
        );
        owner.runtimeState().setLastFiredHead(headIndex);
    }

    private Vec3 firingPosition(int headIndex) {
        // Historical WitherBoss::getFiringPos(), matching the current BDS
        // dedicated firing-position boundary: side heads sit 1.3 blocks from the
        // center around body yaw and 2.2 blocks above the entity origin.
        float angleDegrees = owner.getYRot() + 180.0F * headIndex - 180.0F;
        float angleRadians = angleDegrees * Mth.DEG_TO_RAD;

        return new Vec3(
                owner.getX() + Mth.cos(angleRadians) * 1.3D,
                owner.getY() + 2.2D,
                owner.getZ() + Mth.sin(angleRadians) * 1.3D
        );
    }
}
