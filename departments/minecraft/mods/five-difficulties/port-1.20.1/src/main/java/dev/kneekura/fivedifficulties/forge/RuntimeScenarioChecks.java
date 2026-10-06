package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.forge.entity.HomingAmuletProjectile;
import dev.kneekura.fivedifficulties.forge.timestop.SakuyaTimeStopRuntime;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * P6 world-mutating dedicated-server scenario.
 *
 * Activated only by FIVE_DIFFICULTIES_P6_RUNTIME_SCENARIO=1.
 */
@Mod.EventBusSubscriber(
        modid = FiveDifficultiesPort.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.FORGE
)
public final class RuntimeScenarioChecks {
    public static final String PASS_MARKER = "FIVE_DIFFICULTIES_P6_RUNTIME_SCENARIO_PASS";

    private enum Phase {
        IDLE,
        WARMUP,
        FULL_OBSERVE,
        RESUME_AFTER_FULL,
        HALF_OBSERVE,
        HOMING_OBSERVE,
        DONE
    }

    private static Phase phase = Phase.IDLE;
    private static MinecraftServer server;
    private static ServerLevel level;
    private static FakePlayer source;
    private static Zombie target;
    private static HomingAmuletProjectile projectile;
    private static int phaseTicks;

    private static int fullBaselineTick;
    private static Vec3 fullBaselinePos;

    private static int halfBaselineTick;

    private static float homingStartHealth;
    private static Vec3 homingStartPos;
    private static boolean homingMoved;

    private RuntimeScenarioChecks() {}

    private static boolean enabled() {
        return "1".equals(System.getenv("FIVE_DIFFICULTIES_P6_RUNTIME_SCENARIO"));
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;

        server = event.getServer();
        level = server.overworld();

        BlockPos spawn = level.getSharedSpawnPos();
        double x = spawn.getX() + 0.5D;
        double y = spawn.getY() + 2.0D;
        double z = spawn.getZ() + 0.5D;

        source = FakePlayerFactory.getMinecraft(level);
        source.moveTo(x, y, z, 0.0F, 0.0F);
        source.setDeltaMovement(Vec3.ZERO);

        if (level.getEntity(source.getId()) != source) {
            level.addNewPlayer(source);
        }

        target = newZombie(x, y, z + 4.0D);
        require(level.addFreshEntity(target), "warmup zombie added");

        phase = Phase.WARMUP;
        phaseTicks = 0;

        FiveDifficultiesPort.LOGGER.info(
                "FIVE_DIFFICULTIES_P6_SCENARIO_START sourceId={} targetId={} pos={},{},{}",
                source.getId(),
                target.getId(),
                x, y, z
        );
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!enabled() || phase == Phase.IDLE || phase == Phase.DONE || event.phase != TickEvent.Phase.END) {
            return;
        }

        try {
            switch (phase) {
                case WARMUP -> tickWarmup();
                case FULL_OBSERVE -> tickFull();
                case RESUME_AFTER_FULL -> tickResumeAfterFull();
                case HALF_OBSERVE -> tickHalf();
                case HOMING_OBSERVE -> tickHoming();
                default -> {
                }
            }
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error(
                    "FIVE_DIFFICULTIES_P6_RUNTIME_SCENARIO_FAIL phase={} phaseTicks={}",
                    phase,
                    phaseTicks,
                    failure
            );
            phase = Phase.DONE;
            cleanupControllersAndEntities();
            server.halt(false);
            if (failure instanceof RuntimeException runtime) throw runtime;
            throw new IllegalStateException("P6 runtime scenario failed", failure);
        }
    }

    private static void tickWarmup() {
        phaseTicks++;
        if (target.tickCount < 4) return;

        fullBaselineTick = target.tickCount;
        fullBaselinePos = target.position();

        require(
                SakuyaTimeStopRuntime.startX1(
                        level,
                        source,
                        TimeDomainMode.FULL_STOP,
                        8,
                        SakuyaControllerKind.SPELL_CARD
                ) != null,
                "FULL controller started"
        );

        phase = Phase.FULL_OBSERVE;
        phaseTicks = 0;
    }

    private static void tickFull() {
        phaseTicks++;
        if (phaseTicks < 4) return;

        require(target.tickCount == fullBaselineTick,
                "FULL_STOP tickCount frozen: expected=" + fullBaselineTick + " actual=" + target.tickCount);
        require(target.position().distanceToSqr(fullBaselinePos) < 1.0e-10D,
                "FULL_STOP position frozen");

        FiveDifficultiesPort.LOGGER.info(
                "FIVE_DIFFICULTIES_P6_FULL_PASS baselineTick={} observedTick={} pos={}",
                fullBaselineTick,
                target.tickCount,
                target.position()
        );

        SakuyaTimeStopRuntime.stopX1(level, source);
        phase = Phase.RESUME_AFTER_FULL;
        phaseTicks = 0;
    }

    private static void tickResumeAfterFull() {
        phaseTicks++;
        if (phaseTicks < 2) return;

        require(target.tickCount > fullBaselineTick, "entity resumed after FULL_STOP");

        halfBaselineTick = target.tickCount;
        require(
                SakuyaTimeStopRuntime.startX1(
                        level,
                        source,
                        TimeDomainMode.HALF_SPEED,
                        10,
                        SakuyaControllerKind.SPELL_CARD
                ) != null,
                "HALF controller started"
        );

        phase = Phase.HALF_OBSERVE;
        phaseTicks = 0;
    }

    private static void tickHalf() {
        phaseTicks++;
        if (phaseTicks < 6) return;

        int delta = target.tickCount - halfBaselineTick;
        require(delta == 3, "HALF_SPEED expected 3 entity ticks across 6 server ticks, got " + delta);

        FiveDifficultiesPort.LOGGER.info(
                "FIVE_DIFFICULTIES_P6_HALF_PASS baselineTick={} observedTick={} delta={}",
                halfBaselineTick,
                target.tickCount,
                delta
        );

        SakuyaTimeStopRuntime.stopX1(level, source);
        target.discard();

        target = newZombie(source.getX(), source.getY(), source.getZ() + 8.0D);
        require(level.addFreshEntity(target), "Homing target zombie added");

        Vec3 origin = new Vec3(source.getX(), source.getEyeY(), source.getZ());
        Vec3 initialDirection = new Vec3(0.18D, 0.0D, 1.0D).normalize();

        projectile = new HomingAmuletProjectile(
                level,
                source,
                origin,
                initialDirection,
                false
        );
        homingStartPos = projectile.position();
        homingStartHealth = target.getHealth();
        homingMoved = false;

        require(level.addFreshEntity(projectile), "Homing projectile added");

        phase = Phase.HOMING_OBSERVE;
        phaseTicks = 0;
    }

    private static void tickHoming() {
        phaseTicks++;

        if (projectile != null && !projectile.isRemoved()
                && projectile.position().distanceToSqr(homingStartPos) > 0.04D) {
            homingMoved = true;
        }

        if (target.getHealth() < homingStartHealth) {
            require(homingMoved, "Homing projectile moved before hit");

            FiveDifficultiesPort.LOGGER.info(
                    "FIVE_DIFFICULTIES_P6_HOMING_PASS ticks={} startHealth={} endHealth={} targetPos={}",
                    phaseTicks,
                    homingStartHealth,
                    target.getHealth(),
                    target.position()
            );

            completeScenario();
            return;
        }

        require(phaseTicks <= 60,
                "Homing projectile did not damage target within 60 server ticks; projectileRemoved="
                        + (projectile == null || projectile.isRemoved()));
    }

    private static Zombie newZombie(double x, double y, double z) {
        Zombie zombie = EntityType.ZOMBIE.create(level);
        require(zombie != null, "Zombie EntityType factory");
        zombie.moveTo(x, y, z, 180.0F, 0.0F);
        zombie.setNoAi(true);
        zombie.setNoGravity(true);
        zombie.setPersistenceRequired();
        zombie.setDeltaMovement(Vec3.ZERO);
        zombie.setHealth(zombie.getMaxHealth());
        return zombie;
    }

    private static void completeScenario() {
        FiveDifficultiesPort.LOGGER.info(
                "{} fullFrozenTicks={} halfObservedDelta={} homingTicks={} homingHealthDelta={}",
                PASS_MARKER,
                4,
                target == null ? -1 : 3,
                phaseTicks,
                homingStartHealth - (target == null ? homingStartHealth : target.getHealth())
        );

        phase = Phase.DONE;
        cleanupControllersAndEntities();
        server.halt(false);
    }

    private static void cleanupControllersAndEntities() {
        if (level != null && source != null) {
            SakuyaTimeStopRuntime.stopX1(level, source);
        }
        if (projectile != null && !projectile.isRemoved()) projectile.discard();
        if (target != null && !target.isRemoved()) target.discard();
    }

    private static void require(boolean condition, String description) {
        if (!condition) {
            throw new IllegalStateException("P6 runtime scenario failed: " + description);
        }
    }
}
