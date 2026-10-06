package dev.kneekura.fivedifficulties.forge.timestop;

import dev.kneekura.fivedifficulties.core.timestop.SubjectKind;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopDecision;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopSubject;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.projectile.Projectile;

import java.util.UUID;

/**
 * Forge/Minecraft adapter intended to be called by P1 Mixins.
 * It contains no tick cancellation by itself.
 */
public final class TimeStopHooks {
    private TimeStopHooks() {}

    public static TimeStopDecision decision(
            ServerLevel level,
            Entity entity,
            boolean createdDuringTimeStop
    ) {
        UUID owner = null;
        SubjectKind kind = SubjectKind.OTHER;

        if (entity instanceof Projectile projectile) {
            kind = SubjectKind.PROJECTILE;
            Entity projectileOwner = projectile.getOwner();
            if (projectileOwner != null) owner = projectileOwner.getUUID();
        } else if (entity instanceof LivingEntity) {
            kind = SubjectKind.LIVING;
        } else if (entity instanceof ItemEntity) {
            kind = SubjectKind.ITEM;
        }

        TimeStopSubject subject = new TimeStopSubject(
                entity.getUUID(),
                owner,
                kind,
                createdDuringTimeStop,
                SakuyaTimeStopRuntime.vec(entity)
        );
        return SakuyaTimeStopRuntime.service(level)
                .decision(subject, SakuyaTimeStopRuntime.logicalTick(level));
    }

    public static boolean shouldCancelNormalTick(
            ServerLevel level,
            Entity entity,
            boolean createdDuringTimeStop
    ) {
        return decision(level, entity, createdDuringTimeStop) == TimeStopDecision.FREEZE;
    }

    public static boolean shouldUseStoppedProjectileTick(
            ServerLevel level,
            Entity entity,
            boolean createdDuringTimeStop
    ) {
        return decision(level, entity, createdDuringTimeStop) == TimeStopDecision.SPECIAL_PROJECTILE;
    }
}
