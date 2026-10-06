package dev.kneekura.fivedifficulties.forge.timestop;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.core.x1.SakuyaWatchContract;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.AABB;

import javax.annotation.Nullable;

/** Server-side lifecycle entry points for X1 time controllers. */
public final class SakuyaTimeStopRuntime {
    private SakuyaTimeStopRuntime() {}

    @Nullable
    public static SakuyaTimeControllerEntity startX1(
            ServerLevel level,
            LivingEntity source,
            TimeDomainMode mode,
            int durationTicks,
            SakuyaControllerKind kind
    ) {
        if (level == null || source == null || mode == null || kind == null) throw new NullPointerException();

        AABB duplicateBox = source.getBoundingBox().inflate(SakuyaWatchContract.DUPLICATE_PRECHECK_RANGE_BLOCKS);
        if (!level.getEntitiesOfClass(
                SakuyaTimeControllerEntity.class,
                duplicateBox,
                controller -> controller.isAlive()
        ).isEmpty()) {
            return null;
        }

        int tick = logicalTick(level);
        SakuyaTimeControllerEntity controller = new SakuyaTimeControllerEntity(
                level,
                source,
                mode,
                durationTicks,
                kind,
                tick
        );
        return level.addFreshEntity(controller) ? controller : null;
    }

    public static boolean stopX1(ServerLevel level, LivingEntity source) {
        boolean stopped = false;
        AABB search = source.getBoundingBox().inflate(SakuyaWatchContract.FIELD_RANGE_BLOCKS + 2.0D);
        for (SakuyaTimeControllerEntity controller : level.getEntitiesOfClass(
                SakuyaTimeControllerEntity.class,
                search,
                candidate -> candidate.isAlive() && candidate.getSourceEntity() == source
        )) {
            controller.discard();
            stopped = true;
        }
        return stopped;
    }

    public static int logicalTick(net.minecraft.world.level.Level level) {
        return (int) (level.getGameTime() & 0x7fffffffL);
    }

    public static Vec3d vec(net.minecraft.world.entity.Entity entity) {
        return new Vec3d(entity.getX(), entity.getY(), entity.getZ());
    }
}
