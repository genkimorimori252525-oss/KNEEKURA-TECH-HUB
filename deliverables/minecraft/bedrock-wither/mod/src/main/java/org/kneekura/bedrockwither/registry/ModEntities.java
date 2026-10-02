package org.kneekura.bedrockwither.registry;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

public final class ModEntities {
    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, BedrockWitherMod.MOD_ID);

    public static final RegistryObject<EntityType<BedrockWitherEntity>> BEDROCK_WITHER =
            ENTITY_TYPES.register("bedrock_wither", () ->
                    EntityType.Builder.of(BedrockWitherEntity::new, MobCategory.MONSTER)
                            // Mojang Bedrock behavior_pack/entities/wither.json: collision_box 1 x 3.
                            .sized(1.0F, 3.0F)
                            .fireImmune()
                            .clientTrackingRange(10)
                            .updateInterval(1)
                            .build(new ResourceLocation(
                                    BedrockWitherMod.MOD_ID,
                                    "bedrock_wither"
                            ).toString()));

    public static final RegistryObject<EntityType<BedrockWitherSkullEntity>> BEDROCK_WITHER_SKULL =
            ENTITY_TYPES.register("bedrock_wither_skull", () ->
                    EntityType.Builder.<BedrockWitherSkullEntity>of(BedrockWitherSkullEntity::new, MobCategory.MISC)
                            // Mojang Bedrock projectile definitions expose a 0.15 x 0.15 collision box.
                            .sized(0.15F, 0.15F)
                            .clientTrackingRange(8)
                            .updateInterval(1)
                            .build(new ResourceLocation(
                                    BedrockWitherMod.MOD_ID,
                                    "bedrock_wither_skull"
                            ).toString()));

    private ModEntities() {
    }
}
