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

    private enum Phase { IDLE, HAKKERO, ROD, JEWEL, GOHEI, WIND, GAP, DONE }

    private static Phase phase = Phase.IDLE;
    private static ServerLevel level;
    private static double bx, by, bz;
    private static int ticks;
    private static final Map<String, Integer> SEEN = new HashMap<>();
    private static FakePlayer player;
    private static MiniHakkeroEntity hakkero;
    private static NuclearShotEntity nuclear;
    private static double nuclearStartDistance;
    private static dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity orb;
    private static int goheiStep;
    private static double orbMaxDistance;
    private static dev.kneekura.fivedifficulties.forge.entity.SanaeWindEntity wind;
    private static net.minecraft.world.entity.monster.Husk windTarget;
    private static int windStep;
    private static dev.kneekura.fivedifficulties.forge.entity.SukimaEntity gapA, gapB;
    private static net.minecraft.world.entity.monster.Husk traveller;
    private static THShotEntity travellingShot;
    private static int gapStep;

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
        else if (e instanceof dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity o) {
            key = "orb";
            orb = o;
        } else if (e instanceof dev.kneekura.fivedifficulties.forge.entity.MiracleCircleEntity) key = "circle";
        else if (e instanceof dev.kneekura.fivedifficulties.forge.entity.SukimaEntity g) key = "gap" + g.getColor();
        else if (e instanceof dev.kneekura.fivedifficulties.forge.entity.SanaeWindEntity w) {
            key = "wind";
            wind = w;
        }
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
                case GOHEI -> tickGohei();
                case WIND -> tickWind();
                case GAP -> tickGap();
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
        startGohei();
    }

    // ---- 4. Hakurei gohei: charge a Yin-Yang Orb, throw it; it bounces (BOUND04) ----

    private static void startGohei() {
        SEEN.clear();
        player.moveTo(bx, by, bz, -90F, -20F); // a little upward, away from everything
        hold(new ItemStack(PortRegistries.HAKUREI_MIKO_STICK.get()));
        player.getMainHandItem().use(level, player, InteractionHand.MAIN_HAND);
        require(count("orb") == 1, "charging makes a Yin-Yang Orb");
        goheiStep = 0;
        orbMaxDistance = 0;
        phase = Phase.GOHEI;
        ticks = 0;
    }

    private static void tickGohei() {
        if (goheiStep == 0 && ticks == 10) {
            require(!orb.isRemoved() && orb.getShotSize() > 0.8F, "charged orb size " + orb.getShotSize());
            require(orb.position().distanceTo(player.getEyePosition()) < 2.5D, "the charge stays in front of the player");
            player.releaseUsingItem();
            require(player.getMainHandItem().getDamageValue() == 1, "a throw costs 1 durability");
            goheiStep = 1;
            ticks = 0;
        } else if (goheiStep == 1) {
            if (!orb.isRemoved()) orbMaxDistance = Math.max(orbMaxDistance, orb.position().distanceTo(player.position()));
            if (ticks == 60) {
                require(!orb.isRemoved(), "the orb keeps bouncing (BOUND04)");
                require(orbMaxDistance > 8.0D, "the orb flew off, max distance " + orbMaxDistance);
                require(orb.getY() > by - 0.5D, "the orb stays above the ground, y " + (orb.getY() - by));
                FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_GOHEI_PASS size={} maxDistance={}",
                        String.format("%.2f", orb.getShotSize()), String.format("%.2f", orbMaxDistance));
                orb.discard();
                SEEN.clear();
                player.getMainHandItem().use(level, player, InteractionHand.MAIN_HAND);
                goheiStep = 2;
                ticks = 0;
            }
        } else if (goheiStep == 2 && ticks == 3) {
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            goheiStep = 3;
            ticks = 0;
        } else if (goheiStep == 3 && ticks == 3) {
            require(orb.isRemoved(), "without the gohei in hand the charge vanishes");
            player.stopUsingItem();
            startWind();
        }
    }

    // ---- 5. Wind gohei: pentagrams while held, a quick release blows a knock-back wind,
    //         a long one charges the miracle cards ----

    private static void startWind() {
        SEEN.clear();
        player.moveTo(bx, by, bz, -90F, 0F);
        windTarget = net.minecraft.world.entity.EntityType.HUSK.create(level);
        windTarget.moveTo(bx + 3.0D, by, bz, 90F, 0F);
        windTarget.setNoAi(true);
        windTarget.setInvulnerable(true);
        require(level.addFreshEntity(windTarget), "wind target");
        hold(new ItemStack(PortRegistries.WIND_MIKO_STICK.get()));
        player.getMainHandItem().use(level, player, InteractionHand.MAIN_HAND);
        require(count("circle") == 1, "holding draws the first pentagram");
        windStep = 0;
        phase = Phase.WIND;
        ticks = 0;
    }

    private static void tickWind() {
        if (windStep == 0 && ticks == 35) {
            require(count("circle") == 2, "a second pentagram after 30 ticks, got " + count("circle"));
            // The fake player never ticks its use counter: releasing now is a release at 0 ticks.
            player.releaseUsingItem();
            require(count("wind") == 1 && player.getMainHandItem().getDamageValue() == 1, "a quick release blows a wind");
            windStep = 1;
            ticks = 0;
        } else if (windStep == 1) {
            double vy = windTarget.getDeltaMovement().y;
            if (vy > 1.0D) {
                int circles = level.getEntitiesOfClass(dev.kneekura.fivedifficulties.forge.entity.MiracleCircleEntity.class,
                        player.getBoundingBox().inflate(16)).size();
                require(circles == 0, "pentagrams vanish when the player stops using the gohei, left " + circles);
                FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_WIND_PASS hitAfter={} knockUp={}", ticks,
                        String.format("%.2f", vy));
                windStep = 2;
                ticks = 0;
            } else {
                require(ticks < 20, "the wind never knocked the husk up (wind removed " + wind.isRemoved() + " at "
                        + wind.position().subtract(windTarget.position()) + " from the husk, husk vy " + vy
                        + ", husk alive " + windTarget.isAlive() + ")");
            }
        } else if (windStep == 2) {
            ItemStack gohei = player.getMainHandItem();
            gohei.setDamageValue(40);
            player.experienceLevel = 40;
            for (int n = 14; n <= 18; n++) {
                player.getInventory().add(new ItemStack(PortRegistries.SPELL_CARD_ITEMS.get(n).get()));
            }
            gohei.releaseUsing(level, player, 72000 - 160); // 160 ticks: all five pentagrams
            int charged = 0;
            for (ItemStack st : player.getInventory().items) {
                if (st.getItem() instanceof dev.kneekura.fivedifficulties.forge.spellcard.SpellCardItem
                        && st.hasTag() && st.getTag().getInt("Charge") == 1000) charged++;
            }
            require(charged == 5, "five miracle cards charged, got " + charged);
            require(gohei.getDamageValue() == 0, "charging repairs the gohei, damage " + gohei.getDamageValue());
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_MIRACLE_CHARGE_PASS cards=5");
            startGap();
        }
    }

    // ---- 6. Gap: place, warp a husk and a shot, re-dye, pick up; the sneak pair; the folding umbrella ----

    private static void startGap() {
        SEEN.clear();
        player.experienceLevel = 0;
        player.moveTo(bx, by, bz + 20.0D, -90F, 0F); // facing +X over open ground: the gap goes 2 ahead in the air
        hold(new ItemStack(PortRegistries.GAP.get(), 2));
        player.getMainHandItem().use(level, player, InteractionHand.MAIN_HAND);
        require(count("gap1") == 1 && player.getMainHandItem().getCount() == 1, "a placed gap uses up one Gap");
        gapA = level.getEntitiesOfClass(dev.kneekura.fivedifficulties.forge.entity.SukimaEntity.class,
                player.getBoundingBox().inflate(4)).get(0);
        gapB = dev.kneekura.fivedifficulties.forge.entity.SukimaEntity.placed(level, player,
                gapA.getX() + 20.0D, gapA.getY(), gapA.getZ(), gapA.getYRot());
        require(level.addFreshEntity(gapB), "second gap");
        traveller = net.minecraft.world.entity.EntityType.HUSK.create(level);
        traveller.moveTo(gapA.getX(), gapA.getY() - 1.0D, gapA.getZ(), 0F, 0F);
        traveller.setNoAi(true);
        traveller.setNoGravity(true);
        traveller.setInvulnerable(true);
        require(level.addFreshEntity(traveller), "traveller");
        travellingShot = dev.kneekura.fivedifficulties.forge.shot.X1Danmaku.createShotEntity(player, player,
                new dev.kneekura.fivedifficulties.core.math.Vec3d(gapA.getX() + 0.3D, gapA.getY(), gapA.getZ()),
                new dev.kneekura.fivedifficulties.core.math.Vec3d(0, 0, 1), 0F,
                new dev.kneekura.fivedifficulties.core.math.Vec3d(0, 1, 0), 0F, 9999, 0.01D, 0.01D, 0.0D,
                dev.kneekura.fivedifficulties.core.math.Vec3d.ZERO,
                dev.kneekura.fivedifficulties.core.x1.X1ShotData.shot(0, 0, 0.3F, 1.0F, 0, 200, 0));
        gapStep = 0;
        phase = Phase.GAP;
        ticks = 0;
    }

    private static void tickGap() {
        if (gapStep == 0 && ticks == 3) {
            require(traveller.position().distanceTo(gapB.position()) < 3.0D,
                    "the husk warps to the other gap, still " + String.format("%.1f", traveller.position().distanceTo(gapB.position())));
            require(travellingShot.position().distanceTo(gapB.position()) < 3.0D, "the shot warps too");
            require(traveller.isOnPortalCooldown(), "a warped entity is immune for a while");
            // re-dye A blue: blue dye is 1.7.10 dye damage 4
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.BLUE_DYE));
            gapA.interact(player, InteractionHand.MAIN_HAND);
            require(gapA.getColor() == 4, "blue dye recolours the gap to 4, got " + gapA.getColor());
            player.setShiftKeyDown(true);
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            gapA.interact(player, InteractionHand.MAIN_HAND);
            require(gapA.isRemoved(), "sneak-use picks the gap up");
            // the direct pair: a wall 20 blocks ahead at eye height
            for (int y = 0; y < 4; y++) {
                level.setBlockAndUpdate(BlockPos.containing(player.getX() + 20.0D, by + y, player.getZ()),
                        net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
            }
            SEEN.clear();
            hold(new ItemStack(PortRegistries.GAP.get(), 64));
            player.getMainHandItem().use(level, player, InteractionHand.MAIN_HAND);
            player.setShiftKeyDown(false);
            require(count("gap16") == 2, "sneak opens a pair of direct gaps, got " + count("gap16"));
            gapStep = 1;
            ticks = 0;
        } else if (gapStep == 1 && ticks == 30) {
            int open = level.getEntitiesOfClass(dev.kneekura.fivedifficulties.forge.entity.SukimaEntity.class,
                    player.getBoundingBox().inflate(40), g -> g.getColor() == 16).size();
            require(open == 0, "direct gaps close after 24 ticks, open " + open);
            // folding umbrella: sneak cycles the colour, use opens 32 + c, the 30th use folds it into a Gap
            SEEN.clear();
            hold(new ItemStack(PortRegistries.GAP_FOLDING_UMBRELLA.get()));
            player.setShiftKeyDown(true);
            ItemStack umbrella = player.getMainHandItem();
            umbrella.use(level, player, InteractionHand.MAIN_HAND);
            umbrella.use(level, player, InteractionHand.MAIN_HAND);
            player.setShiftKeyDown(false);
            require(umbrella.getTag().getByte("GapColor") == 1, "two sneak-uses: colour 1");
            umbrella.use(level, player, InteractionHand.MAIN_HAND);
            require(count("gap33") == 1 && umbrella.getDamageValue() == 1, "umbrella gap of colour 33, damage 1");
            umbrella.setDamageValue(29);
            var result = umbrella.use(level, player, InteractionHand.MAIN_HAND);
            require(result.getObject().is(PortRegistries.GAP.get()), "the 30th use folds the umbrella into a Gap");
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_GAP_PASS warp=husk+shot dye=4 pair=2 umbrella=33");
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_RUNTIME_SCENARIO_PASS");
            phase = Phase.DONE;
            ScenarioShutdown.finished(level.getServer(), ENV);
        }
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P13 scenario failed: " + what);
    }
}
