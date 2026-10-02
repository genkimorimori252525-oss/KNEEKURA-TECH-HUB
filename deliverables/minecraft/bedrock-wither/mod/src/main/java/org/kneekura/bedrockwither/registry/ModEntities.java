package org.kneekura.bedrockwither.registry;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;

public final class ModEntities {
    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, BedrockWitherMod.MOD_ID);

    public static final RegistryObject<EntityType<BedrockWitherEntity>> BEDROCK_WITHER =
            ENTITY_TYPES.register("bedrock_wither", () ->
                    EntityType.Builder.of(BedrockWitherEntity::new, MobCategory.MONSTER)
                            .sized(0.9F, 3.5F)
                            .clientTrackingRange(10)
                            .updateInterval(1)
                            .build(new ResourceLocation(
                                    BedrockWitherMod.MOD_ID,
                                    "bedrock_wither"
                            ).toString()));

    private ModEntities() {
    }
}
