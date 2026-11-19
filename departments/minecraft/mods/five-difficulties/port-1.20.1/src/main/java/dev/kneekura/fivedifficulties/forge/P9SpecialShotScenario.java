package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.List;

/**
 * P9 dedicated-server scenario for X1 special shots and the literal Homing / Diffusion Amulet items,
 * enabled by FIVE_DIFFICULTIES_P9_RUNTIME_SCENARIO=1. Needs no private assets.
 */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P9SpecialShotScenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P9_RUNTIME_SCENARIO";

    private enum Phase { IDLE, HOMING, DIFFUSION, BOUND, FIRE, WIND, DONE }

    private static Phase phase = Phase.IDLE;
    private static ServerLevel level;
    private static FakePlayer player;
    private static Husk target;
    private static float startHealth;
    private static THShotEntity shot;
    private static int ticks;
    private static int bounces;
    private static double lastVy;
    private static double bx, by, bz;

    private P9SpecialShotScenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        int x = spawn.getX(), z = spawn.getZ() - 32;
        bx = x + 0.5D;
        bz = z + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
        player = FakePlayerFactory.get(level, new com.mojang.authlib.GameProfile(
                java.util.UUID.fromString("00000000-0000-0000-0000-00000000f909"), "[FiveDifficultiesP9]"));
        player.moveTo(bx, by, bz, 0F, 0F); // facing +Z
        startHoming();
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!enabled() || event.phase != TickEvent.Phase.END || phase == Phase.IDLE || phase == Phase.DONE) return;
        try {
            ticks++;
            switch (phase) {
                case HOMING -> tickHoming();
                case DIFFUSION -> tickDiffusion();
                case BOUND -> tickBound();
                case FIRE -> tickFire();
                case WIND -> tickWind();
                default -> {}
            }
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P9_RUNTIME_SCENARIO_FAIL phase={}", phase, failure);
            phase = Phase.DONE;
            ScenarioShutdown.failed(level.getServer());
            throw failure;
        }
    }

    private static Husk husk(double x, double z) {
        Husk h = EntityType.HUSK.create(level);
        h.moveTo(x, by, z, 0F, 0F);
        h.setNoAi(true);
        require(level.addFreshEntity(h), "husk added");
        return h;
    }

    private static List<THShotEntity> playerShots() {
        return level.getEntitiesOfClass(THShotEntity.class, player.getBoundingBox().inflate(48.0D),
                s -> s.getOwner() == player);
    }

    private static void next(Phase p) {
        playerShots().forEach(THShotEntity::discard);
        phase = p;
        ticks = 0;
    }

    private static THShotEntity control;
    private static double homingMin, controlMin;

    // 1. ItemHomingAmulet fires five X1 THShot amulets with HOMING01; then a homing amulet and an
    //    identical non-homing control fly the 25-degree ray past a target at 37 degrees.
    private static void startHoming() {
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(PortRegistries.HOMING_AMULET.get(), 2));
        PortRegistries.HOMING_AMULET.get().use(level, player, InteractionHand.MAIN_HAND);
        List<THShotEntity> fired = playerShots();
        require(fired.size() == 5, "homing amulet fan of 5, got " + fired.size());
        for (THShotEntity s : fired) {
            require(s.getShotForm() == X1ShotTables.FORM_AMULET && s.motion().special == X1ShotTables.HOMING01
                            && s.getShotSize() == 0.4F && s.shotDamage == 5.0F,
                    "THShot amulet with HOMING01, size 0.4, damage 5");
        }
        require(player.getMainHandItem().getCount() == 1, "one amulet consumed");
        fired.forEach(THShotEntity::discard);

        target = husk(bx + 6.0D, bz + 8.0D);
        Vec3d start = new Vec3d(bx, by + 1.2D, bz);
        Vec3d ray = new Vec3d(Math.sin(Math.toRadians(25)), 0, Math.cos(Math.toRadians(25)));
        shot = amulet(start, ray, X1ShotTables.HOMING01);
        control = amulet(start.add(new Vec3d(0, 0.6D, 0)), ray, 0);
        homingMin = controlMin = Double.MAX_VALUE;
        phase = Phase.HOMING;
        ticks = 0;
    }

    private static THShotEntity amulet(Vec3d pos, Vec3d dir, int special) {
        X1ShotData data = X1ShotData.shot(X1ShotTables.FORM_AMULET, X1ShotTables.RED, 0.4F, 5.0F, 0, 90, special);
        THShotEntity s = new THShotEntity(level, player, pos, dir, 0F, new Vec3d(0, 1, 0), 0F, 9999, 0.7D, 0.7D, 0.7D,
                Vec3d.ZERO, data);
        require(level.addFreshEntity(s), "amulet added");
        return s;
    }

    private static double horizontalDistance(THShotEntity s) {
        return Math.hypot(s.getX() - target.getX(), s.getZ() - target.getZ());
    }

    private static void tickHoming() {
        if (!shot.isRemoved()) homingMin = Math.min(homingMin, horizontalDistance(shot));
        else if (target.getHealth() < target.getMaxHealth()) homingMin = 0.0D; // it hit
        if (!control.isRemoved()) controlMin = Math.min(controlMin, horizontalDistance(control));
        if (ticks < 30) return;
        require(controlMin > 1.5D, "control should miss the 37-degree target, min=" + controlMin);
        require(homingMin < controlMin - 0.3D, "HOMING01 did not bend toward the target: homing="
                + homingMin + " control=" + controlMin);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P9_HOMING_PASS homingMin={} controlMin={} hit={}",
                String.format("%.3f", homingMin), String.format("%.3f", controlMin), homingMin == 0.0D);
        target.discard();
        next(Phase.DIFFUSION);
        player.moveTo(bx, by + 10.0D, bz, 0F, 0F); // keep the burst clear of the floor
        diffusionPeak = 0;
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(PortRegistries.DIFFUSION_AMULET.get(), 1));
        PortRegistries.DIFFUSION_AMULET.get().use(level, player, InteractionHand.MAIN_HAND);
        require(playerShots().size() == 2, "diffusion amulet fires 2");
    }

    // 2. DIFFUSION01: at tick 16 each amulet bursts into spheres of 20 + 16 + 8 blue amulets.
    private static int diffusionPeak;

    private static void tickDiffusion() {
        int blue = (int) playerShots().stream().filter(s -> s.getShotForm() == X1ShotTables.FORM_AMULET
                && s.getShotColor() == X1ShotTables.BLUE && s.getShotEndTime() == 60).count();
        diffusionPeak = Math.max(diffusionPeak, blue);
        if (ticks < 24) return;
        require(diffusionPeak == 88, "diffusion burst expected 88 blue amulets, peak " + diffusionPeak);
        List<THShotEntity> shots = playerShots();
        player.moveTo(bx, by, bz, 0F, 0F);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P9_DIFFUSION_PASS peak={} aliveAtTick24={}", diffusionPeak, shots.size());
        next(Phase.BOUND);
        X1ShotData data = X1ShotData.shot(X1ShotTables.FORM_SMALL, X1ShotTables.YELLOW, X1ShotTables.SIZE[0],
                X1ShotTables.DAMAGE[0], 0, 400, X1ShotTables.BOUND02);
        shot = new THShotEntity(level, player, new Vec3d(bx + 3.5D, by + 4.0D, bz), new Vec3d(0, -1, 0), 0F,
                new Vec3d(1, 0, 0), 0F, 9999, 0.5D, 0.5D, 0D, new Vec3d(0, -0.03D, 0), data);
        require(level.addFreshEntity(shot), "bound shot added");
        bounces = 0;
        lastVy = -1;
    }

    // 3. BOUND02 bounces off the floor (0.9 restitution) and is removed once its bounces are spent.
    private static void tickBound() {
        if (!shot.isRemoved()) {
            double vy = shot.getDeltaMovement().y;
            if (lastVy < 0 && vy > 0) bounces++;
            lastVy = vy;
            require(ticks < 300, "bound shot never finished");
            return;
        }
        require(bounces >= 1, "bound shot never bounced");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P9_BOUND_PASS bounces={} removedAtTick={}", bounces,
                shot.tickCount);
        next(Phase.FIRE);
        target = husk(bx + 6.5D, bz);
        X1ShotData data = X1ShotData.shot(X1ShotTables.FORM_SMALL, X1ShotTables.ORANGE, 0, 80, X1ShotTables.FIRE);
        shot = new THShotEntity(level, player, new Vec3d(bx + 1.5D, by + 1.0D, bz), new Vec3d(1, 0, 0), 0F,
                new Vec3d(0, 1, 0), 0F, 9999, 0.5D, 0.5D, 0D, Vec3d.ZERO, data);
        require(level.addFreshEntity(shot), "fire shot added");
    }

    // 4. FIRE sets the target on fire for (int) damage seconds.
    private static void tickFire() {
        if (!shot.isRemoved()) {
            require(ticks < 40, "fire shot never hit");
            return;
        }
        require(target.getRemainingFireTicks() > 0, "FIRE shot did not ignite the target");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P9_FIRE_PASS fireTicks={}", target.getRemainingFireTicks());
        target.discard();
        next(Phase.WIND);
        target = husk(bx + 6.5D, bz + 4.0D);
        startHealth = target.getHealth();
        X1ShotData data = X1ShotData.shot(X1ShotTables.FORM_SMALL, X1ShotTables.AQUA, 0, 80, X1ShotTables.WIND01);
        shot = new THShotEntity(level, player, new Vec3d(bx + 1.5D, by + 1.0D, bz + 4.0D), new Vec3d(1, 0, 0), 0F,
                new Vec3d(0, 1, 0), 0F, 9999, 0.5D, 0.5D, 0D, Vec3d.ZERO, data);
        require(level.addFreshEntity(shot), "wind shot added");
    }

    // 5. WIND01 adds motion * 1.7 plus 2.0 upward.
    private static void tickWind() {
        if (!shot.isRemoved()) {
            require(ticks < 40, "wind shot never hit");
            return;
        }
        double vy = target.getDeltaMovement().y;
        require(vy > 1.0D, "WIND01 launch expected, vy=" + vy);
        require(startHealth - target.getHealth() > 0F, "wind shot also damages");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P9_WIND_PASS vy={}", vy);
        target.discard();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P9_RUNTIME_SCENARIO_PASS");
        phase = Phase.DONE;
        ScenarioShutdown.finished(level.getServer(), ENV);
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P9 scenario failed: " + what);
    }
}
