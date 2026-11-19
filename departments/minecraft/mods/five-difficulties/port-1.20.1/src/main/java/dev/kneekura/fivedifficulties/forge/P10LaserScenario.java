package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1LaserSpawner;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.List;

/** P10 dedicated-server scenario for X1 lasers A / B and ItemTHLaser (FIVE_DIFFICULTIES_P10_RUNTIME_SCENARIO=1). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P10LaserScenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P10_RUNTIME_SCENARIO";

    private enum Phase { IDLE, GROWTH, HIT, CUT, SET_LASER, SET_REMOVED, DONE }

    private static Phase phase = Phase.IDLE;
    private static ServerLevel level;
    private static ArmorStand owner;
    private static THLaserEntity laser;
    private static Husk target;
    private static int ticks;
    private static double bx, by, bz;
    private static float startYaw;

    private P10LaserScenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        int x = spawn.getX() + 24, z = spawn.getZ();
        bx = x + 0.5D;
        bz = z + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
        owner = EntityType.ARMOR_STAND.create(level);
        owner.moveTo(bx, by, bz, 0F, 0F);
        owner.setNoGravity(true);
        require(level.addFreshEntity(owner), "owner");
        laser = laserA(new Vec3d(bx, by + 8.0D, bz), 0.6D, 5F, 0);
        phase = Phase.GROWTH;
    }

    private static THLaserEntity laserA(Vec3d pos, double speed, float length, int delay) {
        X1LaserData data = X1LaserData.laser(1, 0.1F, length, 5.0F, delay, 80);
        THLaserEntity l = new THLaserEntity(level, owner, owner, pos, new Vec3d(1, 0, 0), 0F, new Vec3d(0, 1, 0), 0F,
                9999, speed, speed, 0D, Vec3d.ZERO, data);
        require(level.addFreshEntity(l), "laser added");
        return l;
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!enabled() || event.phase != TickEvent.Phase.END || phase == Phase.IDLE || phase == Phase.DONE) return;
        try {
            ticks++;
            switch (phase) {
                case GROWTH -> tickGrowth();
                case HIT -> tickHit();
                case CUT -> tickCut();
                case SET_LASER -> tickSetLaser();
                case SET_REMOVED -> tickSetRemoved();
                default -> {}
            }
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P10_RUNTIME_SCENARIO_FAIL phase={}", phase, failure);
            phase = Phase.DONE;
            ScenarioShutdown.failed(level.getServer());
            throw failure;
        }
    }

    // 1. Length grows by speed * 2 (speed float-rounded) and is stored as (int) (length * 10000).
    private static void tickGrowth() {
        if (laser.tickCount == 2) require(laser.getLaserLength() == 2.4D, "length after 2 ticks " + laser.getLaserLength());
        if (laser.tickCount < 6) {
            require(ticks < 40, "growth laser stopped ticking");
            return;
        }
        require(laser.getLaserLength() == 5.0D, "length capped at max 5, got " + laser.getLaserLength());
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P10_GROWTH_PASS length={}", laser.getLaserLength());
        laser.discard();
        target = EntityType.HUSK.create(level);
        target.moveTo(bx + 3.0D, by, bz, 0F, 0F);
        target.setNoAi(true);
        require(level.addFreshEntity(target), "husk");
        laser = laserA(new Vec3d(bx + 0.5D, by + 1.0D, bz), 0.0D, 5F, 0);
        laser.setLaserLength(5.0D);
        next(Phase.HIT);
    }

    // 2. A stationary laser hurts the husk along its length (5 * EASY 0.7) and survives the hit.
    private static void tickHit() {
        float dealt = target.getMaxHealth() - target.getHealth();
        if (dealt <= 0F) {
            require(ticks < 30, "laser never hurt the husk");
            return;
        }
        float expected = laser.getShotDamageWithDifficulty();
        require(Math.abs(dealt - expected) < 1e-4F, "laser damage " + dealt + " expected " + expected);
        require(!laser.isRemoved(), "laser passes through the target");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P10_HIT_PASS damage={}", dealt);
        target.discard();
        laser.discard();
        level.setBlockAndUpdate(BlockPos.containing(bx + 3.0D, by + 1.0D, bz + 4.0D), Blocks.STONE.defaultBlockState());
        laser = laserA(new Vec3d(bx + 0.5D, by + 1.5D, bz + 4.0D), 0.0D, 8F, 0); // into the stone at x+3
        laser.setLaserLength(8.0D);
        next(Phase.CUT);
    }

    // 3. A block cuts the laser (length and max) at the hit distance.
    private static void tickCut() {
        if (ticks < 3) return;
        double max = laser.getMaxLaserLength();
        require(!laser.isRemoved() && max > 1.5D && max < 2.5D, "laser cut at the wall (2.0 away), max=" + max);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P10_CUT_PASS max={}", max);
        laser.discard();
        X1LaserData data = X1LaserData.laser(4, 0.2F, 10F, 2.0F, 0, 200);
        laser = X1LaserSpawner.createLaserB(level, owner, owner, new Vec3d(bx, by, bz), new Vec3d(1, 0, 0),
                new Vec3d(0, 1, 0), 10F, 9999, data, owner, 1.0D, 6.0D);
        startYaw = laser.getYRot();
        next(Phase.SET_LASER);
    }

    // 4. Laser B stays pinned to its set entity, grows to full length at once and sweeps 10 deg/tick.
    private static void tickSetLaser() {
        if (ticks < 5) return;
        require(laser instanceof THSetLaserEntity && !laser.isRemoved(), "set laser alive");
        require(laser.getLaserLength() == 10.0D, "set laser full length, got " + laser.getLaserLength());
        require(Math.abs(laser.getY() - (by + 6.0D)) < 1e-9, "pinned at set entity + yOffset");
        float swept = Math.abs(laser.getYRot() - startYaw);
        require(swept > 30F, "set laser should sweep about its rotate axis, swept " + swept);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P10_SET_LASER_PASS swept={} length={}", swept,
                laser.getLaserLength());
        owner.discard();
        next(Phase.SET_REMOVED);
    }

    // 5. The set laser dies with its set entity; then the item forms.
    private static void tickSetRemoved() {
        if (ticks < 3) return;
        require(laser.isRemoved(), "set laser should die with its set entity");
        FakePlayer player = FakePlayerFactory.get(level, new com.mojang.authlib.GameProfile(
                java.util.UUID.fromString("00000000-0000-0000-0000-00000000f910"), "[FiveDifficultiesP10]"));
        player.moveTo(bx, by + 20.0D, bz, 0F, 0F);
        int[][] cases = {{0, 3, 3}, {1, 5, 5}, {2, 4, 4}, {3, 4, 5}, {4, 8, 8}, {5, 6, 6}}; // form, Number, lasers
        for (int[] c : cases) {
            ItemStack stack = new ItemStack(PortRegistries.LASER.get(), 2);
            CompoundTag tag = stack.getOrCreateTag();
            tag.putByte("DanmakuForm", (byte) c[0]);
            tag.putShort("Number", (short) c[1]);
            tag.putByte("Color", (byte) 9);
            player.setItemInHand(InteractionHand.MAIN_HAND, stack);
            PortRegistries.LASER.get().use(level, player, InteractionHand.MAIN_HAND);
            List<THLaserEntity> spawned = level.getEntitiesOfClass(THLaserEntity.class,
                    player.getBoundingBox().inflate(4.0D), l -> l.getOwner() == player);
            require(spawned.size() == c[2], "laser form " + c[0] + " spawned " + spawned.size() + " expected " + c[2]);
            require(stack.getCount() == 1, "laser item consumed");
            spawned.forEach(THLaserEntity::discard);
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P10_ITEM_FORMS_PASS forms=6");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P10_RUNTIME_SCENARIO_PASS");
        phase = Phase.DONE;
        ScenarioShutdown.finished(level.getServer(), ENV);
    }

    private static void next(Phase p) {
        phase = p;
        ticks = 0;
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P10 scenario failed: " + what);
    }
}
