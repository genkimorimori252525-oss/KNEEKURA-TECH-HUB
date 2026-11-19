package com.example.kirby_mod.entity;

import com.example.kirby_mod.KirbyMod;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModEntities {

    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, KirbyMod.MODID);

    public static final RegistryObject<EntityType<KirbyEntity>> KIRBY = ENTITY_TYPES.register("kirby",
            () -> EntityType.Builder.of(KirbyEntity::new, MobCategory.CREATURE)
                    .sized(0.9F, 0.9F)
                    .clientTrackingRange(10)
                    .build(new ResourceLocation(KirbyMod.MODID, "kirby").toString()));

    private ModEntities() {}
}
