package dev.kneekura.fivedifficulties.forge;

import com.mojang.authlib.GameProfile;
import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity;
import dev.kneekura.fivedifficulties.forge.entity.THItemEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardDeclaration;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.UUID;

/** P14 dedicated-server scenario: config, player power, bonus items, extend, bombs (FIVE_DIFFICULTIES_P14_RUNTIME_SCENARIO=1). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P14BonusScenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P14_RUNTIME_SCENARIO";

    private enum Phase { IDLE, ITEMS, DONE }

    private static Phase phase = Phase.IDLE;
    private static ServerLevel level;
    private static double bx, by, bz;
    private static int ticks;
    private static FakePlayer walker, stander;
    private static THItemEntity drifting, homing;
    private static double homingMin = Double.MAX_VALUE;
    private static THShotEntity lastShot;

    private P14BonusScenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    @SubscribeEvent
    public static void onJoin(EntityJoinLevelEvent event) {
        if (!enabled() || event.getLevel().isClientSide || phase == Phase.DONE) return;
        Entity e = event.getEntity();
        if (Math.abs(e.getX() - bx) > 48 || Math.abs(e.getZ() - bz) > 48) return;
        if (e instanceof THShotEntity s) lastShot = s;
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        bx = spawn.getX() + 70 + 0.5D;
        bz = spawn.getZ() - 70 + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX() + 70, spawn.getZ() - 70);
        try {
            checkConfig();
            checkPower();
            checkExtend();
            checkBombs();
            startItems();
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P14_RUNTIME_SCENARIO_FAIL phase=START", failure);
            phase = Phase.DONE;
            ScenarioShutdown.failed(level.getServer());
        }
    }

    private static FakePlayer player(int n) {
        FakePlayer p = FakePlayerFactory.get(level, new GameProfile(
                UUID.fromString(String.format("00000000-0000-0000-0000-0000f914%04d", n)), "[FDP14-" + n + "]"));
        p.moveTo(bx, by, bz, 0F, 0F);
        p.getInventory().clearContent();
        p.experienceLevel = 0;
        return p;
    }

    private static void checkConfig() {
        require(X1Config.SPEC.isLoaded(), "the X1 common config is loaded");
        require(X1Config.spellCardVol() == 0.5F && X1Config.masterSparkVol() == 0.5F && X1Config.downVol() == 0.5F
                && X1Config.hisoutenVol() == 0.2F, "SE volume defaults");
        require(X1Config.usingMasterSpark() && X1Config.masterSparkDestroysBlocks() && X1Config.useDefaultGapSE()
                && X1Config.danmakuLevel() == 2 && X1Config.shotMaxNumber() == 32 && X1Config.laserMaxNumber() == 8
                && X1Config.fairySpawnRate() == 50 && !X1Config.spawnHanabeeper(), "X1 defaults");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P14_CONFIG_PASS danmakuLevel={} spellCardVol={}",
                X1Config.danmakuLevel(), X1Config.spellCardVol());
    }

    // Power: small 1, big 10, at most 400; a shot item adds power / 400 to its damage.
    private static void checkPower() {
        FakePlayer p = player(1);
        p.getInventory().add(new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 3));
        p.getInventory().add(new ItemStack(PortRegistries.POWER_ITEM_BIG.get(), 2));
        require(X1PlayerEvents.getPlayerPower(p) == 23.0F, "3 small + 2 big = 23, got " + X1PlayerEvents.getPlayerPower(p));
        for (int i = 0; i < 4; i++) p.getInventory().add(new ItemStack(PortRegistries.POWER_ITEM_BIG.get(), 64));
        require(X1PlayerEvents.getPlayerPower(p) == 400.0F, "power is capped at 400");
        p.getInventory().clearContent();
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(PortRegistries.SHOT_ITEMS.get(0).get()));
        p.getInventory().add(new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 40)); // after the hand: slot 0 is taken
        lastShot = null;
        p.getMainHandItem().use(level, p, InteractionHand.MAIN_HAND);
        require(lastShot != null, "the shot item fired");
        float base = X1ShotTables.DAMAGE[lastShot.getShotForm()];
        require(lastShot.shotDamage == base + 40.0F / 400.0F, "damage " + lastShot.shotDamage + " = " + base + " + 0.1");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P14_POWER_PASS small3big2=23 cap=400 shotBonus=0.1");
    }

    // Extend: a dying player with an extend item is saved at full health inside a purple circle.
    private static void checkExtend() {
        FakePlayer p = player(2);
        level.addNewPlayer(p);
        p.getInventory().add(new ItemStack(PortRegistries.EXTEND_ITEM.get(), 2));
        int circlesBefore = level.getEntitiesOfClass(SpellCardCircleEntity.class, p.getBoundingBox().inflate(8)).size();
        p.setHealth(0.0F);
        // FakePlayer.die() is a no-op: post the event a real player's die() fires.
        var death = new net.minecraftforge.event.entity.living.LivingDeathEvent(p, level.damageSources().generic());
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.post(death);
        require(death.isCanceled(), "the extend cancels the death");
        require(p.getHealth() == p.getMaxHealth(), "healed to full, health " + p.getHealth());
        require(p.getInventory().countItem(PortRegistries.EXTEND_ITEM.get()) == 1, "one extend used");
        require(p.invulnerableTime == 100, "100 ticks of invulnerability");
        int circles = level.getEntitiesOfClass(SpellCardCircleEntity.class, p.getBoundingBox().inflate(8)).size();
        require(circles == circlesBefore + 1, "a spell-card circle around the saved player");
        level.removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P14_EXTEND_PASS extendsLeft=1 invulnerable=100");
    }

    // Bombs pay a spell card's level cost first (Mishaguji-sama needs 3).
    private static void checkBombs() {
        FakePlayer p = player(3);
        Husk target = EntityType.HUSK.create(level);
        target.moveTo(bx, by, bz + 6.0D, 180F, 0F);
        target.setNoAi(true);
        target.setInvulnerable(true);
        require(level.addFreshEntity(target), "bomb target");
        ItemStack card = new ItemStack(PortRegistries.SPELL_CARD_ITEMS.get(22).get());
        require(!X1SpellCardDeclaration.check(level, card, p, 22, X1SpellCardDeclaration.NORMAL, true),
                "no levels, no bombs: refused");
        p.getInventory().add(new ItemStack(PortRegistries.BOMB_ITEM.get(), 5));
        require(X1SpellCardDeclaration.check(level, card, p, 22, X1SpellCardDeclaration.NORMAL, true),
                "five bombs pay for a level-3 card");
        require(p.getInventory().countItem(PortRegistries.BOMB_ITEM.get()) == 2 && p.experienceLevel == 0,
                "three bombs used, levels untouched");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P14_BOMB_PASS bombsLeft=2 levels=0");
    }

    // Bonus items: an unattracted one drifts down and vanishes on landing; a sneaking player draws one in.
    private static void startItems() {
        walker = player(4);
        walker.moveTo(bx + 12.0D, by, bz + 12.0D, 0F, 0F);
        level.addNewPlayer(walker);
        // a standing (not sneaking) player 30 blocks from the walker: its bonus is not drawn in and keeps drifting
        stander = player(5);
        stander.moveTo(bx - 18.0D, by, bz + 12.0D, 0F, 0F);
        level.addNewPlayer(stander);
        drifting = new THItemEntity(level, bx - 14.0D, by + 3.0D, bz + 12.0D, new Vec3d(0, 1, 0), THItemEntity.ITEM_ID_SMALLPOWER);
        require(level.addFreshEntity(drifting), "drifting bonus");
        walker.setShiftKeyDown(true);
        homing = new THItemEntity(level, bx + 12.0D, by + 3.0D, bz + 4.0D, new Vec3d(0, 1, 0), THItemEntity.ITEM_ID_BOMB);
        require(level.addFreshEntity(homing), "homing bonus");
        phase = Phase.ITEMS;
        ticks = 0;
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!enabled() || event.phase != TickEvent.Phase.END || phase != Phase.ITEMS) return;
        try {
            ticks++;
            if (!homing.isRemoved()) homingMin = Math.min(homingMin, homing.position().distanceTo(walker.position()));
            if (ticks < 60) return;
            require(drifting.isRemoved(), "an unattracted bonus vanishes when it lands");
            require(homingMin < 1.5D, "a sneaking player draws the bonus in, closest " + homingMin);
            if (!homing.isRemoved()) homing.playerTouch(walker); // a fake player never ticks its own touch
            require(walker.getInventory().countItem(PortRegistries.BOMB_ITEM.get()) == 1, "the bomb is picked up");
            level.removePlayerImmediately(walker, Entity.RemovalReason.DISCARDED);
            require(stander.getInventory().countItem(PortRegistries.POWER_ITEM_SMALL.get()) == 0, "nothing for the stander");
            level.removePlayerImmediately(stander, Entity.RemovalReason.DISCARDED);
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P14_ITEMS_PASS homingMin={}", String.format("%.2f", homingMin));
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P14_RUNTIME_SCENARIO_PASS");
            phase = Phase.DONE;
            ScenarioShutdown.finished(level.getServer(), ENV);
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P14_RUNTIME_SCENARIO_FAIL phase={}", phase, failure);
            phase = Phase.DONE;
            ScenarioShutdown.failed(level.getServer());
            throw failure;
        }
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P14 scenario failed: " + what);
    }
}
