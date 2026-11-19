package org.kneekura.bedrockwither.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Bedrock side-head target/idle scheduler.
 *
 * Current BDS preserves per-head next-update and idle counters plus three
 * alternative target slots. Historical Bedrock native aiStep provides the
 * still-corresponding execution shape (including phase-independent head firing,
 * gated during pathing, charge preparation/execution and shot delays):
 * - side heads update on 10..19 tick idle cadence;
 * - Normal/Hard idle counter >15 emits a dangerous random skull;
 * - a valid alternative target on Normal/Hard gets a normal skull and next
 *   update moves to 40..59 ticks;
 * - if there is no side target, choose a random eligible Player in range.
 *
 * A 2024 Bedrock bug report independently observed that side heads track but do
 * not fire at the player on Easy, while Normal/Hard causes side-head firing.
 *
 * The historical native constructor stores attack range 30. Current BDS still
 * exposes mAttackRange, but the current binary initializer is not public, so 30
 * remains HISTORICAL_NATIVE_PROVISIONAL and isolated here.
 */
public final class BedrockWitherSideHeadController {
    public static final int HISTORICAL_MIN_IDLE_UPDATE_DELAY = 10;
    public static final int HISTORICAL_IDLE_UPDATE_DELAY_SPAN = 10;
    public static final int HISTORICAL_MIN_TARGETED_UPDATE_DELAY = 40;
    public static final int HISTORICAL_TARGETED_UPDATE_DELAY_SPAN = 20;
    public static final int CORROBORATED_IDLE_DANGEROUS_THRESHOLD = 16;
    public static final float PROVISIONAL_NATIVE_ATTACK_RANGE = 30.0F;

    private final BedrockWitherEntity owner;

    public BedrockWitherSideHeadController(BedrockWitherEntity owner) {
        this.owner = owner;
        if (owner.runtimeState().attackRange() <= 0.0F) {
            owner.runtimeState().setAttackRange(PROVISIONAL_NATIVE_ATTACK_RANGE);
        }
    }

    public void tick() {
        if (!canRun() || !(owner.level() instanceof ServerLevel level)) {
            return;
        }

        processHead(level, 1);
        processHead(level, 2);
    }

    public static boolean passiveDangerousEnabled(Difficulty difficulty) {
        return difficulty == Difficulty.NORMAL || difficulty == Difficulty.HARD;
    }

    private boolean canRun() {
        return owner.isAlive()
                && !owner.spawnController().isActive()
                && !owner.deathController().isActive()
                && !owner.runtimeState().charging()
                && !owner.runtimeState().pathing()
                && !owner.runtimeState().wantsMove()
                && owner.runtimeState().delayShot() <= 0
                && owner.getBedrockState() != BedrockWitherState.PHASE2_DASH_PREP
                && owner.getBedrockState() != BedrockWitherState.PHASE_TRANSITION;
    }

    private void processHead(ServerLevel level, int headIndex) {
        BedrockWitherHeadRuntime head = owner.runtimeState().head(headIndex);
        int now = owner.tickCount;

        if (head.nextUpdate() <= 0) {
            head.setNextUpdate(now + idleUpdateDelay());
            return;
        }
        if (now < head.nextUpdate()) {
            return;
        }

        head.setNextUpdate(now + idleUpdateDelay());

        Difficulty difficulty = owner.level().getDifficulty();
        if (passiveDangerousEnabled(difficulty)) {
            int idle = head.idleUpdates() + 1;
            head.setIdleUpdates(idle);
            if (idle >= CORROBORATED_IDLE_DANGEROUS_THRESHOLD) {
                head.setIdleUpdates(0);
                firePassiveDangerous(headIndex);
            }
        } else {
            head.setIdleUpdates(0);
        }

        LivingEntity target = resolveAlternative(level, owner.getAlternativeHeadTarget(headIndex));
        if (target != null) {
            if (!isValidTarget(target)) {
                owner.clearAlternativeHeadTarget(headIndex);
                return;
            }

            if (passiveDangerousEnabled(difficulty)) {
                owner.attackController().fireSkull(
                        firingPosition(headIndex),
                        target.getEyePosition(),
                        BedrockWitherSkullEntity.Kind.NORMAL
                );
                owner.runtimeState().setLastFiredHead(headIndex);
                head.setNextUpdate(now + targetedUpdateDelay());
                head.setIdleUpdates(0);
            }
            return;
        }

        acquirePlayerTarget(level, headIndex);
    }

    private void acquirePlayerTarget(ServerLevel level, int headIndex) {
        float range = owner.runtimeState().attackRange();
        if (!(range > 0.0F)) {
            return;
        }

        AABB area = owner.getBoundingBox().inflate(range, 8.0D, range);
        LivingEntity mainTarget = owner.getTarget();

        List<Player> candidates = level.getEntitiesOfClass(
                Player.class,
                area,
                player -> player.isAlive()
                        && !player.isCreative()
                        && !player.isSpectator()
                        && player != mainTarget
                        && owner.hasLineOfSight(player)
        );

        if (candidates.isEmpty()) {
            owner.clearAlternativeHeadTarget(headIndex);
            return;
        }

        Player selected = candidates.get(owner.getRandom().nextInt(candidates.size()));
        owner.setAlternativeHeadTarget(headIndex, selected.getUUID());
    }

    private boolean isValidTarget(LivingEntity target) {
        float range = owner.runtimeState().attackRange();
        return target.isAlive()
                && owner.distanceToSqr(target) <= (double) range * (double) range
                && owner.hasLineOfSight(target)
                && (!(target instanceof Player player)
                || (!player.isCreative() && !player.isSpectator()));
    }

    private LivingEntity resolveAlternative(ServerLevel level, Optional<UUID> targetUuid) {
        if (targetUuid.isEmpty()) {
            return null;
        }
        Entity entity = level.getEntity(targetUuid.get());
        return entity instanceof LivingEntity living && living.isAlive() ? living : null;
    }

    private int idleUpdateDelay() {
        return HISTORICAL_MIN_IDLE_UPDATE_DELAY
                + owner.getRandom().nextInt(HISTORICAL_IDLE_UPDATE_DELAY_SPAN);
    }

    private int targetedUpdateDelay() {
        return HISTORICAL_MIN_TARGETED_UPDATE_DELAY
                + owner.getRandom().nextInt(HISTORICAL_TARGETED_UPDATE_DELAY_SPAN);
    }

    private void firePassiveDangerous(int headIndex) {
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
        float angleDegrees = owner.getYRot() + 180.0F * headIndex - 180.0F;
        float angleRadians = angleDegrees * Mth.DEG_TO_RAD;

        return new Vec3(
                owner.getX() + Mth.cos(angleRadians) * 1.3D,
                owner.getY() + 2.2D,
                owner.getZ() + Mth.sin(angleRadians) * 1.3D
        );
    }
}
