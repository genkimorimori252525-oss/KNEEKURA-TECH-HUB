package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.LargeFireball;
import net.minecraft.world.entity.projectile.SmallFireball;
import net.minecraft.world.entity.projectile.Projectile;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** Exactly one existing Entity.hurt site in each inspected ANCHOR class; explosion damage is separate. */
@Mixin(value={AbstractArrow.class,LargeFireball.class,SmallFireball.class},remap=false)
public abstract class KneekuraDebugProjectileHurtMixin {
    @Redirect(method="onHitEntity(Lnet/minecraft/world/phys/EntityHitResult;)V",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/Entity;hurt(Lnet/minecraft/world/damagesource/DamageSource;F)Z"),require=1)
    private boolean kneekura$hurt(Entity target,DamageSource source,float amount){
        return KneekuraDebugDecisionHooks.projectileHurt((Projectile)(Object)this,target,source,amount);
    }
}
