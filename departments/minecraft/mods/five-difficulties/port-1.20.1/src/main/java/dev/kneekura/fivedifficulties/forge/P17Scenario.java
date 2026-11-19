package dev.kneekura.fivedifficulties.forge;

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
        rumia.hurt(level.damageSources().generic(), 100F);
        require(rumia.getHealth() <= 0.0F && rumia.deadFlag(), "phase 1 down");
        rumia.tickCount++;
        rumia.deathStepForTest();
        require(rumia.getUsingSpellCardNo() == 28 && rumia.getHealth() == 44.0F && !rumia.deadFlag() && rumia.attackInterval == 60,
                "phase 2: card 28 at 44 HP");
        rumia.attackInterval = 0;
        rumia.hurt(level.damageSources().generic(), 100F);
        rumia.tickCount++;
        rumia.deathStepForTest();
        require(rumia.getDanmakuPattern() == DanmakuMobEntity.ATTACK_END, "the second death is final");
        rumia.discard();
        foe.discard();
        level.getEntitiesOfClass(THShotEntity.class, new net.minecraft.world.phys.AABB(bx - 30, by - 30, bz - 30, bx + 30, by + 30, bz + 30),
                s -> s.getOwner() == rumia).forEach(Entity::discard);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_RUMIA_PASS fired={}", fired);

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
