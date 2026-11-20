package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.event.entity.SpawnPlacementRegisterEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Attributes and spawn rules of the X1 danmaku mobs (spawn weights and biomes are biome modifiers in data/). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class MobRegistration {
    private MobRegistration() {}

    @SubscribeEvent
    public static void attributes(EntityAttributeCreationEvent event) {
        event.put(PortRegistries.TH_FAIRY.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.SUNFLOWER_FAIRY.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.FAMILIAR.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.TH_PHANTOM.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.RUMIA.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.CIRNO.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.WRIGGLE.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.TOZIKO.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.SAKUYA.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.SANAE.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.REIMU.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.MIKO.get(), DanmakuMobEntity.createDanmakuAttributes().build());
        event.put(PortRegistries.RINNOSUKE.get(), RinnosukeEntity.createAttributes().build());
    }

    @SubscribeEvent
    public static void spawnPlacements(SpawnPlacementRegisterEvent event) {
        event.register(PortRegistries.TH_FAIRY.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                THFairyEntity::checkFairySpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.SUNFLOWER_FAIRY.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                THFairyEntity::checkFairySpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.TH_PHANTOM.get(), SpawnPlacements.Type.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                PhantomEntity::checkPhantomSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.RUMIA.get(), SpawnPlacements.Type.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                RumiaEntity::checkRumiaSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.CIRNO.get(), SpawnPlacements.Type.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                CirnoEntity::checkCirnoSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.WRIGGLE.get(), SpawnPlacements.Type.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                WriggleEntity::checkWriggleSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.TOZIKO.get(), SpawnPlacements.Type.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                TozikoEntity::checkTozikoSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.SAKUYA.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                SakuyaEntity::checkTraderSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.SANAE.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                SanaeEntity::checkTraderSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.REIMU.get(), SpawnPlacements.Type.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                ReimuEntity::checkNoSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.MIKO.get(), SpawnPlacements.Type.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                MikoEntity::checkNoSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.RINNOSUKE.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                RinnosukeEntity::checkRinnosukeSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
    }
}
