package com.example.kirby_mod.mixin;

import com.example.kirby_mod.client.HeldMobPresentationRegistry;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(LivingEntity.class)
public abstract class LivingEntityEffectParticleMixin {

    @Redirect(
            method = "tickEffects",
            at = @At(
                    value = "INVOKE",
                    target = "Lnet/minecraft/world/level/Level;addParticle(Lnet/minecraft/core/particles/ParticleOptions;DDDDDD)V"
            )
    )
    private void suppressHeldMobEffectParticles(Level level, ParticleOptions options,
                                                double x, double y, double z,
                                                double red, double green, double blue) {
        LivingEntity self = (LivingEntity) (Object) this;
        if (!level.isClientSide || !HeldMobPresentationRegistry.shouldHide(self.getUUID())) {
            level.addParticle(options, x, y, z, red, green, blue);
        }
    }
}
