package org.kneekura.bedrockwither;

import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;
import org.kneekura.bedrockwither.registry.ModEntities;

@Mod(BedrockWitherMod.MOD_ID)
public final class BedrockWitherMod {
    public static final String MOD_ID = "kneekura_bedrock_wither";

    public BedrockWitherMod() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        ModEntities.ENTITY_TYPES.register(modBus);
        modBus.addListener(this::registerAttributes);
    }

    private void registerAttributes(EntityAttributeCreationEvent event) {
        event.put(ModEntities.BEDROCK_WITHER.get(), BedrockWitherEntity.createAttributes().build());
    }
}
