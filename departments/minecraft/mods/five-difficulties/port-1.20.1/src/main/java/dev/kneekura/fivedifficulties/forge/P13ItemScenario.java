package dev.kneekura.fivedifficulties.forge;

import com.mojang.authlib.GameProfile;
import dev.kneekura.fivedifficulties.forge.entity.DragonNeckJewelEntity;
import dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity;
import dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.EXPLOSION01;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.FORM_LIGHT;

/** P13 dedicated-server scenario for the danmaku-weapon items (FIVE_DIFFICULTIES_P13_RUNTIME_SCENARIO=1). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P13ItemScenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P13_RUNTIME_SCENARIO";

    private enum Phase { IDLE, HAKKERO, ROD, JEWEL, DONE }

    private static Phase phase = Phase.IDLE;
    private static ServerLevel level;
    private static double bx, by, bz;
    private static int ticks;
    private static final Map<String, Integer> SEEN = new HashMap<>();
    private static FakePlayer player;
    private static MiniHakkeroEntity hakkero;
    private static NuclearShotEntity nuclear;
    private static double nuclearStartDistance;

    private P13ItemScenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    private static int count(String key) {
        return SEEN.getOrDefault(key, 0);
    }

    @SubscribeEvent
    public static void onJoin(EntityJoinLevelEvent event) {
        if (!enabled() || event.getLevel().isClientSide || phase == Phase.IDLE || phase == Phase.DONE) return;
        Entity e = event.getEntity();
        if (Math.abs(e.getX() - bx) > 48 || Math.abs(e.getZ() - bz) > 48) return; // P11 / P12 run at the same time
        String key = null;
        if (e instanceof MiniHakkeroEntity h) {
            key = "hakkero";
            hakkero = h;
        } else if (e instanceof NuclearShotEntity n) {
            key = "nuclear";
            nuclear = n;
        } else if (e instanceof DragonNeckJewelEntity) key = "jewel";
        else if (e instanceof THSetLaserEntity s && s.getShotId() == 24 && s.motion() != null && s.motion().special == EXPLOSION01) key = "spark";
        else if (e instanceof THLaserEntity) key = "laser";
        else if (e instanceof THShotEntity s && s.getShotForm() == FORM_LIGHT) key = "light";
        if (key != null) SEEN.merge(key, 1, Integer::sum);
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        // 70 blocks out on the -Z side (P11 is at -X+Z, P12 at +X+Z).
        bx = spawn.getX() + 0.5D;
        bz = spawn.getZ() - 70 + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX(), spawn.getZ() - 70);
        player = FakePlayerFactory.get(level, new GameProfile(UUID.fromString("00000000-0000-0000-0000-0000f9130001"), "[FDP13]"));
        player.moveTo(bx, by, bz, -90F, 0F); // facing +X, away from everything
        try {
            startHakkero();
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P13_RUNTIME_SCENARIO_FAIL phase=START", failure);
            phase = Phase.DONE;
            ScenarioShutdown.failed(level.getServer());
        }
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!enabled() || event.phase != TickEvent.Phase.END || phase == Phase.IDLE || phase == Phase.DONE) return;
        try {
            ticks++;
            switch (phase) {
                case HAKKERO -> tickHakkero();
                case ROD -> tickRod();
                case JEWEL -> tickJewel();
                default -> {}
            }
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P13_RUNTIME_SCENARIO_FAIL phase={}", phase, failure);
            phase = Phase.DONE;
            ScenarioShutdown.failed(level.getServer());
            throw failure;
        }
    }

    private static void hold(ItemStack stack) {
        player.getInventory().clearContent();
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
    }

    // ---- 1. Mini Hakkero: 32 fire charges, an explosive Master Spark, the item comes back ----

    private static void startHakkero() {
        phase = Phase.HAKKERO;
        hold(new ItemStack(PortRegistries.MINI_HAKKERO_ITEM.get()));
        player.getInventory().add(new ItemStack(Items.FIRE_CHARGE, 20));
        ItemStack held = player.getMainHandItem();
        held.use(level, player, InteractionHand.MAIN_HAND);
        require(count("hakkero") == 0 && !held.isEmpty(), "20 fire charges are not enough");
        player.getInventory().add(new ItemStack(Items.FIRE_CHARGE, 20));
        held.use(level, player, InteractionHand.MAIN_HAND);
        require(count("hakkero") == 1 && held.isEmpty(), "hakkero placed and the item spent");
        require(player.getInventory().countItem(Items.FIRE_CHARGE) == 8, "32 of 40 fire charges used, left "
                + player.getInventory().countItem(Items.FIRE_CHARGE));
        require(count("spark") == 1, "explosive ID-24 Master Spark");
        phase = Phase.HAKKERO;
        ticks = 0;
    }

    private static void tickHakkero() {
        if (!hakkero.isRemoved()) {
            require(ticks < 130, "hakkero still there after 130 ticks (its tickCount " + hakkero.tickCount + ", at "
                    + hakkero.blockPosition() + ", entity ticking " + level.isPositionEntityTicking(hakkero.blockPosition())
                    + ", user " + hakkero.user + ")");
            return;
        }
        require(player.getInventory().countItem(PortRegistries.MINI_HAKKERO_ITEM.get()) == 1,
                "the hakkero returns to the user's inventory");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_HAKKERO_PASS chargesLeft=8 returnedAfter={}", ticks);
        startRod();
    }

    // ---- 2. Nuclear Control Rod: charge (grow), release (fire, durability), drop the rod (explode) ----

    private static int rodStep;

    private static void startRod() {
        SEEN.clear();
        hold(new ItemStack(PortRegistries.NUCLEAR_CONTROL_ROD.get()));
        player.getMainHandItem().use(level, player, InteractionHand.MAIN_HAND);
        require(count("nuclear") == 1 && player.isUsingItem(), "holding the rod grows a nuclear shot");
        rodStep = 0;
        phase = Phase.ROD;
        ticks = 0;
    }

    private static void tickRod() {
        if (rodStep == 0 && ticks == 20) {
            require(!nuclear.isRemoved() && nuclear.getShotSize() > 1.0F, "charged size " + nuclear.getShotSize());
            require(nuclear.position().distanceTo(player.position()) < 3.0D, "the charge stays in front of the player");
            player.releaseUsingItem();
            require(player.getMainHandItem().getDamageValue() == 1, "release costs 1 durability");
            nuclearStartDistance = nuclear.position().distanceTo(player.position());
            rodStep = 1;
            ticks = 0;
        } else if (rodStep == 1 && ticks == 10) {
            double d = nuclear.isRemoved() ? Double.MAX_VALUE : nuclear.position().distanceTo(player.position());
            require(d > nuclearStartDistance + 2.0D, "released shot flies off, distance " + d);
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_ROD_FIRE_PASS size={} flown={}",
                    String.format("%.2f", nuclear.getShotSize()), String.format("%.2f", d));
            nuclear.discard();
            SEEN.clear();
            player.getMainHandItem().use(level, player, InteractionHand.MAIN_HAND);
            require(count("nuclear") == 1, "second charge");
            rodStep = 2;
            ticks = 0;
        } else if (rodStep == 2 && ticks == 3) {
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY); // the rod leaves the hand
            rodStep = 3;
            ticks = 0;
        } else if (rodStep == 3 && ticks == 3) {
            require(nuclear.isRemoved(), "without the rod in hand the charge explodes");
            player.stopUsingItem();
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_ROD_EXPLODE_PASS");
            startJewel();
        }
    }

    // ---- 3. Dragon Neck Jewel: charge, single throw, burst on landing, five-colour throw ----

    private static void startJewel() {
        SEEN.clear();
        hold(new ItemStack(PortRegistries.DRAGON_NECK_JEWEL_ITEM.get()));
        player.moveTo(bx, by, bz, -90F, 30F); // look a little down so it lands nearby
        ItemStack jewel = player.getMainHandItem();
        jewel.use(level, player, InteractionHand.MAIN_HAND);
        require(count("jewel") == 1 && jewel.getDamageValue() == 70, "one throw costs 70, damage " + jewel.getDamageValue());
        player.setShiftKeyDown(true);
        jewel.use(level, player, InteractionHand.MAIN_HAND);
        require(count("jewel") == 1, "the five-colour throw needs a full charge");
        jewel.inventoryTick(level, player, 0, true); // tickCount 0: a recharge tick
        require(jewel.getDamageValue() == 50, "recharge 20, damage " + jewel.getDamageValue());
        jewel.setDamageValue(0);
        jewel.use(level, player, InteractionHand.MAIN_HAND);
        player.setShiftKeyDown(false);
        require(count("jewel") == 6 && jewel.getDamageValue() == 299, "five at once cost 299, damage " + jewel.getDamageValue());
        phase = Phase.JEWEL;
        ticks = 0;
    }

    private static void tickJewel() {
        if (ticks < 60) return;
        int lasers = count("laser"), lights = count("light");
        require(lasers >= 30 && lasers % 5 == 0, "each landing fires five lasers (twice on a forward block hit), got " + lasers);
        require(lights == lasers * 2, "ten light shots per five lasers, got " + lights + " / " + lasers);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_JEWEL_PASS jewels=6 lasers={} lights={}", lasers, lights);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_RUNTIME_SCENARIO_PASS");
        phase = Phase.DONE;
        ScenarioShutdown.finished(level.getServer(), ENV);
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P13 scenario failed: " + what);
    }
}
