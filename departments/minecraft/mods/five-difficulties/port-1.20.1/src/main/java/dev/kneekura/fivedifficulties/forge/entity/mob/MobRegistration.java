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
    }

    @SubscribeEvent
    public static void spawnPlacements(SpawnPlacementRegisterEvent event) {
        event.register(PortRegistries.TH_FAIRY.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                THFairyEntity::checkFairySpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(PortRegistries.SUNFLOWER_FAIRY.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                THFairyEntity::checkFairySpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
    }
}
