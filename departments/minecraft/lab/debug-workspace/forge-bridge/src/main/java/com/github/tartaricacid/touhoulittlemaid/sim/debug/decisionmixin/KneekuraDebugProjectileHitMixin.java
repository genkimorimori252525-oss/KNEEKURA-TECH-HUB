package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.phys.HitResult;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value=Projectile.class,remap=false)
public abstract class KneekuraDebugProjectileHitMixin {
    @Inject(method="onHit(Lnet/minecraft/world/phys/HitResult;)V",at=@At("RETURN"),require=1)
    private void kneekura$hit(HitResult hit,CallbackInfo ignored){KneekuraDebugDecisionHooks.projectileHitReturn((Projectile)(Object)this,hit);}
}
