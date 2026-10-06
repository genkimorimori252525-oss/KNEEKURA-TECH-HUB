package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.timestop.SakuyaTimeStopInstance;
import dev.kneekura.fivedifficulties.core.timestop.SubjectKind;
import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopDecision;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopFlags;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopPolicy;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopShape;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopSubject;
import dev.kneekura.fivedifficulties.forge.entity.HomingAmuletProjectile;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import dev.kneekura.fivedifficulties.forge.item.HomingAmuletItem;
import dev.kneekura.fivedifficulties.forge.item.SakuyaStopWatchItem;
import dev.kneekura.fivedifficulties.forge.item.SakuyaWatchItem;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.UUID;

/**
 * Small fail-fast runtime sanity check.
 *
 * This runs on a real Forge server after startup and verifies the P4 registry
 * surface plus a representative X1 time-policy decision. It deliberately does
 * not mutate the world or spawn test entities.
 */
@Mod.EventBusSubscriber(
        modid = FiveDifficultiesPort.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.FORGE
)
public final class RuntimeSmokeChecks {
    public static final String PASS_MARKER = "FIVE_DIFFICULTIES_P5_RUNTIME_SMOKE_PASS";

    private RuntimeSmokeChecks() {}

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        require(
                PortRegistries.HOMING_AMULET.get() instanceof HomingAmuletItem,
                "homing_amulet registry object"
        );
        require(
                PortRegistries.SAKUYA_WATCH.get() instanceof SakuyaWatchItem,
                "sakuya_watch registry object"
        );
        require(
                PortRegistries.SAKUYA_STOPWATCH.get() instanceof SakuyaStopWatchItem,
                "sakuya_stopwatch registry object"
        );
        var smokeLevel = event.getServer().overworld();
        var homingEntity = PortRegistries.HOMING_AMULET_PROJECTILE.get().create(smokeLevel);
        require(
                homingEntity instanceof HomingAmuletProjectile,
                "homing projectile EntityType factory"
        );
        var controllerEntity = PortRegistries.SAKUYA_TIME_CONTROLLER.get().create(smokeLevel);
        require(
                controllerEntity instanceof SakuyaTimeControllerEntity,
                "Sakuya controller EntityType factory"
        );

        requireRegistryPath(PortRegistries.HOMING_AMULET.get(), "homing_amulet");
        requireRegistryPath(PortRegistries.SAKUYA_WATCH.get(), "sakuya_watch");
        requireRegistryPath(PortRegistries.SAKUYA_STOPWATCH.get(), "sakuya_stopwatch");
        requireRegistryPath(PortRegistries.HOMING_AMULET_PROJECTILE.get(), "homing_amulet_projectile");
        requireRegistryPath(PortRegistries.SAKUYA_TIME_CONTROLLER.get(), "sakuya_time_controller");

        verifyX1PolicyCore();

        FiveDifficultiesPort.LOGGER.info(
                "{} serverVersion={} dedicated={}",
                PASS_MARKER,
                event.getServer().getServerVersion(),
                event.getServer().isDedicatedServer()
        );

        if ("1".equals(System.getenv("FIVE_DIFFICULTIES_RUNTIME_SMOKE_EXIT"))) {
            event.getServer().halt(false);
        }
    }

    private static void verifyX1PolicyCore() {
        UUID stopId = UUID.fromString("00000000-0000-0000-0000-00000000a001");
        UUID sourceId = UUID.fromString("00000000-0000-0000-0000-00000000a002");
        UUID targetId = UUID.fromString("00000000-0000-0000-0000-00000000a003");

        SakuyaTimeStopInstance fullStop = new SakuyaTimeStopInstance(
                stopId,
                sourceId,
                Vec3d.ZERO,
                40.0D,
                100,
                40,
                TimeStopFlags.x1EntityOnly(),
                TimeStopShape.AABB,
                TimeDomainMode.FULL_STOP
        );

        TimeStopPolicy policy = new TimeStopPolicy();

        TimeStopSubject matureTarget = new TimeStopSubject(
                targetId, null, SubjectKind.LIVING, false,
                new Vec3d(1.0D, 0.0D, 0.0D),
                2, false, false
        );
        require(
                policy.decide(fullStop, matureTarget, 100) == TimeStopDecision.FREEZE,
                "X1 full-stop mature living decision"
        );

        TimeStopSubject newbornTarget = new TimeStopSubject(
                targetId, null, SubjectKind.LIVING, true,
                new Vec3d(1.0D, 0.0D, 0.0D),
                1, false, false
        );
        require(
                policy.decide(fullStop, newbornTarget, 100) == TimeStopDecision.ALLOW,
                "X1 two-tick new-entity grace"
        );

        TimeStopSubject source = new TimeStopSubject(
                sourceId, null, SubjectKind.LIVING, false,
                Vec3d.ZERO,
                100, false, false
        );
        require(
                policy.decide(fullStop, source, 100) == TimeStopDecision.ALLOW,
                "X1 source exemption"
        );

        SakuyaTimeStopInstance halfSpeed = new SakuyaTimeStopInstance(
                UUID.fromString("00000000-0000-0000-0000-00000000a004"),
                sourceId,
                Vec3d.ZERO,
                40.0D,
                100,
                40,
                TimeStopFlags.x1EntityOnly(),
                TimeStopShape.AABB,
                TimeDomainMode.HALF_SPEED
        );
        require(
                policy.decide(halfSpeed, matureTarget, 100) == TimeStopDecision.HALF_SPEED,
                "X1 half-speed mature living decision"
        );
    }

    private static void requireRegistryPath(Object value, String expectedPath) {
        ResourceLocation key;
        if (value instanceof net.minecraft.world.item.Item item) {
            key = ForgeRegistries.ITEMS.getKey(item);
        } else if (value instanceof net.minecraft.world.entity.EntityType<?> type) {
            key = ForgeRegistries.ENTITY_TYPES.getKey(type);
        } else {
            throw new IllegalStateException("Unsupported registry smoke type: " + value);
        }

        require(key != null, expectedPath + " has registry key");
        require(
                FiveDifficultiesPort.MOD_ID.equals(key.getNamespace()) && expectedPath.equals(key.getPath()),
                expectedPath + " registry key is " + key
        );
    }

    private static void require(boolean condition, String description) {
        if (!condition) {
            throw new IllegalStateException("P5 runtime smoke failed: " + description);
        }
    }
}
