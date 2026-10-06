package dev.kneekura.fivedifficulties.forge.timestop;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.core.x1.SakuyaWatchContract;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;

import javax.annotation.Nullable;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.WeakHashMap;

/** Level-scoped controller index and server lifecycle entry points. */
public final class SakuyaTimeStopRuntime {
    private static final WeakHashMap<Level, LinkedHashSet<SakuyaTimeControllerEntity>> CONTROLLERS =
            new WeakHashMap<>();

    private SakuyaTimeStopRuntime() {}

    public static void registerController(SakuyaTimeControllerEntity controller) {
        synchronized (CONTROLLERS) {
            CONTROLLERS
                    .computeIfAbsent(controller.level(), ignored -> new LinkedHashSet<>())
                    .add(controller);
        }
    }

    public static void unregisterController(SakuyaTimeControllerEntity controller) {
        synchronized (CONTROLLERS) {
            LinkedHashSet<SakuyaTimeControllerEntity> set = CONTROLLERS.get(controller.level());
            if (set == null) return;
            set.remove(controller);
            if (set.isEmpty()) CONTROLLERS.remove(controller.level());
        }
    }

    public static Set<SakuyaTimeControllerEntity> controllers(Level level) {
        synchronized (CONTROLLERS) {
            LinkedHashSet<SakuyaTimeControllerEntity> set = CONTROLLERS.get(level);
            if (set == null || set.isEmpty()) return Collections.emptySet();
            set.removeIf(controller -> controller.isRemoved() || !controller.isAlive());
            return Set.copyOf(set);
        }
    }

    @Nullable
    public static SakuyaTimeControllerEntity startX1(
            ServerLevel level,
            LivingEntity source,
            TimeDomainMode mode,
            int durationTicks,
            SakuyaControllerKind kind
    ) {
        if (level == null || source == null || mode == null || kind == null) throw new NullPointerException();

        double maxAxis = SakuyaWatchContract.DUPLICATE_PRECHECK_RANGE_BLOCKS;
        for (SakuyaTimeControllerEntity controller : controllers(level)) {
            if (controller.isAlive()
                    && Math.abs(controller.getX() - source.getX()) <= maxAxis
                    && Math.abs(controller.getY() - source.getY()) <= maxAxis
                    && Math.abs(controller.getZ() - source.getZ()) <= maxAxis) {
                return null;
            }
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
        for (SakuyaTimeControllerEntity controller : controllers(level)) {
            if (controller.getSourceEntity() == source) {
                controller.discard();
                stopped = true;
            }
        }
        return stopped;
    }

    public static int logicalTick(Level level) {
        return (int) (level.getGameTime() & 0x7fffffffL);
    }

    public static Vec3d vec(net.minecraft.world.entity.Entity entity) {
        return new Vec3d(entity.getX(), entity.getY(), entity.getZ());
    }
}
