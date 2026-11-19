package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.forge.spellcard.cards.SpecialCards;
import com.mojang.authlib.GameProfile;
import dev.kneekura.fivedifficulties.core.x1.X1DanmakuPatterns;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.entity.mob.DanmakuMobEntity;
import dev.kneekura.fivedifficulties.forge.entity.mob.FamiliarEntity;
import dev.kneekura.fivedifficulties.forge.entity.mob.SunFlowerFairyEntity;
import dev.kneekura.fivedifficulties.forge.entity.mob.THFairyEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.UUID;

/** P17 dedicated-server scenario: the X1 danmaku mobs (FIVE_DIFFICULTIES_P17_RUNTIME_SCENARIO=1). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P17Scenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P17_RUNTIME_SCENARIO";
    private static ServerLevel level;
    private static double bx, by, bz;

    private P17Scenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        bx = spawn.getX() + 130 + 0.5D; // (+130, 0): beyond X1's 40-block danmaku clears from the others
        bz = spawn.getZ() + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX() + 130, spawn.getZ());
        try {
            runFairies();
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_RUNTIME_SCENARIO_PASS");
            ScenarioShutdown.finished(level.getServer(), ENV);
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P17_RUNTIME_SCENARIO_FAIL", failure);
            ScenarioShutdown.failed(level.getServer());
        }
    }

    private static <T extends Entity> T spawn(EntityType<T> type, double dx, double dy) {
        T e = type.create(level);
        e.moveTo(bx + dx, by + dy, bz, 0F, 0F);
        level.addFreshEntity(e);
        return e;
    }

    private static void runFairies() {
        // The pattern table follows the danmaku level (normal = 2).
        X1DanmakuPatterns.ensure(2);
        require(X1DanmakuPatterns.PATTERN.size() == 9 && X1DanmakuPatterns.TABLE.get("001").danmaku() == 2007
                && X1DanmakuPatterns.TABLE.get("064").form() == 64 * 8, "level-2 pattern table");

        // A fairy: X1 stats, a table pattern, and it fires at a visible target.
        THFairyEntity fairy = spawn(PortRegistries.TH_FAIRY.get(), 0, 2);
        require(fairy.getAttribute(Attributes.MAX_HEALTH).getBaseValue() == 2.0D && fairy.getSpeedValue() == 0.3D
                && fairy.getAttackDistance() == 8.0D && fairy.getFlyingHeight() == 2 && fairy.getForm() >= 0 && fairy.getForm() < 3,
                "fairy stats");
        Zombie target = EntityType.ZOMBIE.create(level);
        target.moveTo(bx + 6, by, bz, 0F, 0F);
        target.setNoAi(true);
        level.addFreshEntity(target);
        fairy.setDanmakuPattern(0);
        fairy.shotForm = 0;
        fairy.shotColor = 1;
        fairy.speedRate = 0.3F;
        fairy.danmakuSpan = 30;
        fairy.setTarget(target);
        fairy.attackCounter = 0;
        fairy.tickCount = 1;
        fairy.tick();
        int shots = level.getEntitiesOfClass(THShotEntity.class, fairy.getBoundingBox().inflate(4), s -> s.getOwner() == fairy).size();
        require(shots >= 1, "the fairy fired, saw " + shots);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_FAIRY_PASS shots={}", shots);

        // A dying fairy's death blast hurts other fairies nearby (at least 2).
        THFairyEntity near = spawn(PortRegistries.TH_FAIRY.get(), 2, 2);
        near.getAttribute(Attributes.MAX_HEALTH).setBaseValue(20.0D);
        near.setHealth(20.0F);
        DanmakuMobEntity.banishExplosion(fairy, 5.0F, 5.0F);
        require(near.getHealth() <= 18.0F, "banish explosion " + near.getHealth());
        fairy.discard();
        near.discard();
        target.discard();
        level.getEntitiesOfClass(THShotEntity.class, new net.minecraft.world.phys.AABB(bx - 16, by - 16, bz - 16, bx + 16, by + 16, bz + 16),
                s -> s.getOwner() == fairy).forEach(Entity::discard);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_BANISH_PASS");

        // A sunflower fairy spawns with a familiar riding it; the familiar's shooter is the sunflower fairy.
        SunFlowerFairyEntity sun = PortRegistries.SUNFLOWER_FAIRY.get().spawn(level, BlockPos.containing(bx + 3, by, bz), MobSpawnType.SPAWN_EGG);
        require(sun != null && sun.getMaxHealth() == 20.0F && sun.getForm() == 10, "sunflower fairy");
        var riders = sun.getPassengers();
        require(riders.size() == 1 && riders.get(0) instanceof FamiliarEntity f && f.getShooter() == sun,
                "a familiar rides it, riders " + riders);
        FamiliarEntity familiar = (FamiliarEntity) riders.get(0);
        sun.discard();
        familiar.tickCount = 5;
        familiar.stopRiding();
        familiar.tick();
        require(familiar.isRemoved(), "a familiar without a shooter vanishes");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_SUNFLOWER_PASS");

        // A phantom: X1 stats; it leaves no corpse.
        var phantom = spawn(PortRegistries.TH_PHANTOM.get(), -3, 3);
        require(phantom.getSpeedValue() == 0.18D && phantom.getAttackDistance() == 6.0D && phantom.getFlyingHeight() == 3
                && phantom.getForm() >= 0 && phantom.getForm() < 8, "phantom stats");
        phantom.setHealth(0.0F);
        phantom.deathTime = 0;
        phantom.tickDeath();
        require(phantom.isRemoved(), "the phantom vanishes at once");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_PHANTOM_PASS");

        // Rumia: two phases. Her first "death" declares card 28 at 44 HP; the second is final.
        var rumia = spawn(PortRegistries.RUMIA.get(), -6, 2);
        require(rumia.getMaxHealth() == 36.0F && rumia.getUsingSpellCardNo() == -1, "rumia phase 1");
        Zombie foe = EntityType.ZOMBIE.create(level);
        foe.moveTo(bx - 6, by, bz + 8, 0F, 0F);
        foe.setNoAi(true);
        level.addFreshEntity(foe);
        rumia.setTarget(foe);
        rumia.attackCounter = 1;
        int before = level.getEntitiesOfClass(THShotEntity.class, rumia.getBoundingBox().inflate(6), s -> s.getOwner() == rumia).size();
        rumia.patternForTest(2);
        int fired = level.getEntitiesOfClass(THShotEntity.class, rumia.getBoundingBox().inflate(6), s -> s.getOwner() == rumia).size() - before;
        require(fired == 3 * (12 + 3 * 2), "rumia opens with 3 blue circles of 18, saw " + fired);
        rumia.invulnerableTime = 0;
        rumia.hurt(level.damageSources().generic(), 100F);
        require(rumia.getHealth() <= 0.0F && rumia.deadFlag(), "phase 1 down");
        rumia.tickCount++;
        rumia.deathStepForTest();
        require(rumia.getUsingSpellCardNo() == 28 && rumia.getHealth() == 44.0F && !rumia.deadFlag() && rumia.attackInterval == 60,
                "phase 2: card 28 at 44 HP");
        rumia.attackInterval = 0;
        rumia.invulnerableTime = 0;
        rumia.hurt(level.damageSources().generic(), 100F);
        require(rumia.getHealth() <= 0.0F && rumia.deadFlag(), "phase 2 down");
        rumia.tickCount++;
        rumia.deathStepForTest();
        require(rumia.getDanmakuPattern() == DanmakuMobEntity.ATTACK_END, "the second death is final");
        rumia.discard();
        foe.discard();
        level.getEntitiesOfClass(THShotEntity.class, new net.minecraft.world.phys.AABB(bx - 30, by - 30, bz - 30, bx + 30, by + 30, bz + 30),
                s -> s.getOwner() == rumia).forEach(Entity::discard);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_RUMIA_PASS fired={}", fired);

        // Cirno: four phases 38 -> card 19 (46) -> 32 -> card 9 (58) -> end; normal 1 opens with 7 crystal rings.
        var cirno = spawn(PortRegistries.CIRNO.get(), 6, 2);
        require(cirno.getMaxHealth() == 38.0F && cirno.getUsingSpellCardNo() == -1 && cirno.getFlyingHeight() == 2, "cirno phase 1");
        Zombie foe2 = EntityType.ZOMBIE.create(level);
        foe2.moveTo(bx + 6, by, bz + 8, 0F, 0F);
        foe2.setNoAi(true);
        level.addFreshEntity(foe2);
        cirno.setTarget(foe2);
        cirno.attackCounter = 40;
        int cBefore = level.getEntitiesOfClass(THShotEntity.class, cirno.getBoundingBox().inflate(8), s -> s.getOwner() == cirno).size();
        cirno.patternForTest(2);
        int cFired = level.getEntitiesOfClass(THShotEntity.class, cirno.getBoundingBox().inflate(8), s -> s.getOwner() == cirno).size() - cBefore;
        require(cFired == 2 + 3 + 4 + 5 + 6 + 7 + 8, "cirno rings 2..8 = 35 crystals, saw " + cFired);
        int[] cards = {19, -1, 9};
        float[] hp = {46.0F, 32.0F, 58.0F};
        int[] wait = {60, 20, 60};
        for (int k = 0; k < 3; k++) {
            cirno.attackInterval = 0;
            cirno.invulnerableTime = 0;
            cirno.hurt(level.damageSources().generic(), 200F);
            require(cirno.getHealth() <= 0.0F && cirno.deadFlag(), "cirno phase " + (k + 1) + " down");
            cirno.tickCount++;
            cirno.deathStepForTest();
            require(cirno.getUsingSpellCardNo() == cards[k] && cirno.getHealth() == hp[k] && !cirno.deadFlag()
                    && cirno.attackInterval == wait[k], "cirno phase " + (k + 2) + ": card " + cards[k] + " at " + hp[k]);
        }
        cirno.invulnerableTime = 0;
        require(!cirno.hurt(level.damageSources().generic(), 10F) && cirno.getHealth() == 58.0F, "invulnerable between phases");
        cirno.attackInterval = 0;
        cirno.invulnerableTime = 0;
        cirno.hurt(level.damageSources().generic(), 200F);
        require(cirno.getHealth() <= 0.0F && cirno.deadFlag(), "cirno final phase down");
        cirno.tickCount++;
        cirno.deathStepForTest();
        require(cirno.getDanmakuPattern() == DanmakuMobEntity.ATTACK_END, "cirno's fourth death is final");
        cirno.discard();
        foe2.discard();
        level.getEntitiesOfClass(THShotEntity.class, new net.minecraft.world.phys.AABB(bx - 30, by - 30, bz - 30, bx + 30, by + 30, bz + 30),
                s -> s.getOwner() == cirno).forEach(Entity::discard);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_CIRNO_PASS fired={}", cFired);

        // Wriggle: 30 -> card 35 (36 HP, height 2) -> card 34 (42 HP, height 4) -> end. Rice with the bug-storm special.
        var wriggle = spawn(PortRegistries.WRIGGLE.get(), 10, 2);
        require(wriggle.getMaxHealth() == 30.0F && wriggle.getFlyingHeight() == 3 && wriggle.getUsingSpellCardNo() == -1, "wriggle phase 1");
        Zombie foe3 = EntityType.ZOMBIE.create(level);
        foe3.moveTo(bx + 10, by, bz + 8, 0F, 0F);
        foe3.setNoAi(true);
        level.addFreshEntity(foe3);
        wriggle.setTarget(foe3);
        java.util.function.Supplier<java.util.List<THShotEntity>> wShots = () -> level.getEntitiesOfClass(THShotEntity.class,
                wriggle.getBoundingBox().inflate(8), s -> s.getOwner() == wriggle);
        wriggle.attackCounter = 1;
        wriggle.patternForTest(2);
        var rice = wShots.get();
        require(rice.size() == 1 && rice.get(0).motion().special == SpecialCards.LittleBugStorm.SP_ATTACK01_01,
                "one yellow bug-storm rice at normal, saw " + rice.size());
        wriggle.attackCounter = 62;
        wriggle.patternForTest(2);
        int wFired = wShots.get().size() - 1;
        require(wFired == 5, "5-way slowing fan, saw " + wFired);
        int[] wCards = {35, 34};
        float[] wHp = {36.0F, 42.0F};
        int[] wWait = {40, 80};
        int[] wHeight = {2, 4};
        for (int k = 0; k < 2; k++) {
            wriggle.attackInterval = 0;
            wriggle.invulnerableTime = 0;
            wriggle.hurt(level.damageSources().generic(), 200F);
            require(wriggle.getHealth() <= 0.0F && wriggle.deadFlag(), "wriggle phase " + (k + 1) + " down");
            wriggle.tickCount++;
            wriggle.deathStepForTest();
            require(wriggle.getUsingSpellCardNo() == wCards[k] && wriggle.getHealth() == wHp[k] && wriggle.attackInterval == wWait[k]
                    && wriggle.getFlyingHeight() == wHeight[k], "wriggle card " + wCards[k]);
        }
        wriggle.attackInterval = 0;
        wriggle.invulnerableTime = 0;
        wriggle.hurt(level.damageSources().generic(), 200F);
        require(wriggle.getHealth() <= 0.0F && wriggle.deadFlag(), "wriggle final phase down");
        wriggle.tickCount++;
        wriggle.deathStepForTest();
        require(wriggle.getDanmakuPattern() == DanmakuMobEntity.ATTACK_END, "wriggle's third death is final");
        wriggle.discard();
        foe3.discard();
        level.getEntitiesOfClass(THShotEntity.class, new net.minecraft.world.phys.AABB(bx - 30, by - 30, bz - 30, bx + 30, by + 30, bz + 30),
                s -> s.getOwner() == wriggle).forEach(Entity::discard);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_WRIGGLE_PASS fan={}", wFired);

        // Spawn rules accept egg spawns.
        require(THFairyEntity.checkFairySpawnRules(PortRegistries.TH_FAIRY.get(), level, MobSpawnType.SPAWN_EGG,
                BlockPos.containing(bx, by, bz), level.random), "egg spawns allowed");
        FakePlayer p = FakePlayerFactory.get(level, new GameProfile(UUID.fromString("00000000-0000-0000-0000-0000f9170001"), "[FDP17]"));
        p.moveTo(bx, by, bz, 0F, 0F);
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P17 check failed: " + what);
    }
}
