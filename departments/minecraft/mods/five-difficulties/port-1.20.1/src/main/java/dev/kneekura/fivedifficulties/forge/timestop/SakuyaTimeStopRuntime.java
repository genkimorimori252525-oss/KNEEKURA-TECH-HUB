package dev.kneekura.fivedifficulties.forge.timestop;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.timestop.SakuyaTimeStopInstance;
import dev.kneekura.fivedifficulties.core.timestop.SakuyaTimeStopService;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopFlags;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;

import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;

/**
 * Per-ServerLevel holder for the pure time-stop policy core.
 * Actual tick cancellation Mixins are deliberately deferred to P1.
 */
public final class SakuyaTimeStopRuntime {
    private static final Map<ServerLevel, SakuyaTimeStopService> SERVICES = new WeakHashMap<>();

    private SakuyaTimeStopRuntime() {}

    public static SakuyaTimeStopService service(ServerLevel level) {
        synchronized (SERVICES) {
            return SERVICES.computeIfAbsent(level, ignored -> new SakuyaTimeStopService());
        }
    }

    public static SakuyaTimeStopInstance start(
            ServerLevel level,
            Entity source,
            double range,
            int durationTicks,
            TimeStopFlags flags
    ) {
        int tick = logicalTick(level);
        SakuyaTimeStopInstance instance = new SakuyaTimeStopInstance(
                UUID.randomUUID(),
                source.getUUID(),
                vec(source),
                range,
                tick,
                durationTicks,
                flags
        );
        service(level).start(instance);
        return instance;
    }

    public static boolean stop(ServerLevel level, Entity source) {
        return service(level).stopSource(source.getUUID());
    }

    public static void purge(ServerLevel level) {
        service(level).purgeExpired(logicalTick(level));
    }

    public static int logicalTick(ServerLevel level) {
        // P0 core uses int ticks; the X1 oracle/long-running-world policy is a later compatibility decision.
        return (int) (level.getGameTime() & 0x7fffffffL);
    }

    public static Vec3d vec(Entity entity) {
        return new Vec3d(entity.getX(), entity.getY(), entity.getZ());
    }
}
