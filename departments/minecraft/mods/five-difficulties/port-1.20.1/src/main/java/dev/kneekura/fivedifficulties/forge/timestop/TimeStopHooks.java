package dev.kneekura.fivedifficulties.forge.timestop;

import dev.kneekura.fivedifficulties.core.timestop.SubjectKind;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopDecision;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopPolicy;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopSubject;
import dev.kneekura.fivedifficulties.core.x1.SakuyaWatchContract;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.decoration.ItemFrame;
import net.minecraft.world.entity.decoration.Painting;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.Level;

import java.util.UUID;

/**
 * Minecraft adapter used by ServerLevel/ClientLevel tick Mixins.
 *
 * All policy comes from canonical X1 contracts. Roundabout-specific stand,
 * damage-storage and projectile-deceleration rules are intentionally absent.
 */
public final class TimeStopHooks {
    private static final TimeStopPolicy POLICY = new TimeStopPolicy();

    private TimeStopHooks() {}

    public static TimeStopDecision decision(Level level, Entity entity) {
        if (level == null || entity == null || entity.isRemoved()) {
            return TimeStopDecision.ALLOW;
        }
        if (entity instanceof SakuyaTimeControllerEntity) {
            return TimeStopDecision.ALLOW;
        }

        int logicalTick = SakuyaTimeStopRuntime.logicalTick(level);
        TimeStopDecision result = TimeStopDecision.ALLOW;

        double searchRange = SakuyaWatchContract.FIELD_RANGE_BLOCKS + 2.0D;
        for (SakuyaTimeControllerEntity controller : level.getEntitiesOfClass(
                SakuyaTimeControllerEntity.class,
                entity.getBoundingBox().inflate(searchRange),
                candidate -> candidate.isAlive() && candidate.isActiveAt(logicalTick)
        )) {
            LivingEntity source = controller.getSourceEntity();
            if (source == null || !source.isAlive()) {
                continue;
            }

            boolean explicitExempt =
                    entity == source
                    || entity instanceof ItemFrame
                    || entity instanceof Painting
                    || entity.getPassengers().contains(source);

            boolean movableSpell = false;
            if (entity instanceof X1TimeStopMovable movable && movable.canMoveInX1TimeStop(source)) {
                movableSpell = true;
                if (!level.isClientSide) {
                    movable.onX1TimeStopFieldTick(source);
                }
            }

            UUID ownerId = null;
            SubjectKind kind = SubjectKind.OTHER;
            if (entity instanceof Projectile projectile) {
                kind = SubjectKind.PROJECTILE;
                Entity owner = projectile.getOwner();
                if (owner != null) ownerId = owner.getUUID();
            } else if (entity instanceof LivingEntity) {
                kind = SubjectKind.LIVING;
            } else if (entity instanceof ItemEntity) {
                kind = SubjectKind.ITEM;
            }

            TimeStopSubject subject = new TimeStopSubject(
                    entity.getUUID(),
                    ownerId,
                    kind,
                    false,
                    SakuyaTimeStopRuntime.vec(entity),
                    Math.max(0, entity.tickCount),
                    explicitExempt,
                    movableSpell
            );

            TimeStopDecision next = POLICY.decide(controller.toCoreInstance(source), subject, logicalTick);
            if (next == TimeStopDecision.FREEZE) return TimeStopDecision.FREEZE;
            if (next == TimeStopDecision.HALF_SPEED) result = TimeStopDecision.HALF_SPEED;
            else if (next == TimeStopDecision.SPECIAL_PROJECTILE && result == TimeStopDecision.ALLOW) {
                result = TimeStopDecision.SPECIAL_PROJECTILE;
            }
        }

        return result;
    }

    public static boolean shouldCancelNormalTick(Level level, Entity entity) {
        if (level == null || entity == null || entity.isRemoved()) return false;
        if (entity instanceof SakuyaTimeControllerEntity) return false;

        int logicalTick = SakuyaTimeStopRuntime.logicalTick(level);
        double searchRange = SakuyaWatchContract.FIELD_RANGE_BLOCKS + 2.0D;

        for (SakuyaTimeControllerEntity controller : level.getEntitiesOfClass(
                SakuyaTimeControllerEntity.class,
                entity.getBoundingBox().inflate(searchRange),
                candidate -> candidate.isAlive() && candidate.isActiveAt(logicalTick)
        )) {
            LivingEntity source = controller.getSourceEntity();
            if (source == null || !source.isAlive()) continue;

            boolean explicitExempt =
                    entity == source
                    || entity instanceof ItemFrame
                    || entity instanceof Painting
                    || entity.getPassengers().contains(source);

            boolean movableSpell = entity instanceof X1TimeStopMovable movable
                    && movable.canMoveInX1TimeStop(source);
            if (movableSpell && !level.isClientSide) {
                ((X1TimeStopMovable) entity).onX1TimeStopFieldTick(source);
            }

            UUID ownerId = null;
            SubjectKind kind = SubjectKind.OTHER;
            if (entity instanceof Projectile projectile) {
                kind = SubjectKind.PROJECTILE;
                Entity owner = projectile.getOwner();
                if (owner != null) ownerId = owner.getUUID();
            } else if (entity instanceof LivingEntity) {
                kind = SubjectKind.LIVING;
            } else if (entity instanceof ItemEntity) {
                kind = SubjectKind.ITEM;
            }

            TimeStopSubject subject = new TimeStopSubject(
                    entity.getUUID(),
                    ownerId,
                    kind,
                    false,
                    SakuyaTimeStopRuntime.vec(entity),
                    Math.max(0, entity.tickCount),
                    explicitExempt,
                    movableSpell
            );

            var instance = controller.toCoreInstance(source);
            TimeStopDecision next = POLICY.decide(instance, subject, logicalTick);
            if (next == TimeStopDecision.FREEZE) return true;
            if (next == TimeStopDecision.HALF_SPEED && instance.shouldCancelEntityTickForMode(logicalTick)) {
                return true;
            }
        }

        return false;
    }
}
