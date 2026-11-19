package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.KirbyMouthFullness;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;

/** Shared, behavior-preserving eligibility check for Kirby's inhale. */
public final class KirbyInhaleEligibility {

    private static final TagKey<EntityType<?>> INHALE_IMMUNE = TagKey.create(
            Registries.ENTITY_TYPE, new ResourceLocation("kirby_mod", "inhale_immune"));

    private KirbyInhaleEligibility() {}

    public static boolean canInhale(Entity entity) {
        return isEligibleMob(entity)
                && entity instanceof LivingEntity living
                && KirbyMouthFullness.fitsInMaximumMouth(living);
    }

    public static boolean isEligibleMob(Entity entity) {
        if (!(entity instanceof Mob)) return false;
        if (entity instanceof KirbyEntity) return false;
        return !entity.getType().is(INHALE_IMMUNE);
    }
}
