package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=ServerLevel.class,remap=false)
public abstract class KneekuraDebugProjectileLifecycleMixin {
    @Inject(method="addFreshEntity(Lnet/minecraft/world/entity/Entity;)Z",at=@At("RETURN"),require=1)
    private void kneekura$spawn(Entity entity,CallbackInfoReturnable<Boolean> result){
        KneekuraDebugDecisionHooks.projectileSpawnReturn(entity,result.getReturnValueZ());
    }
    @Inject(method="tickNonPassenger(Lnet/minecraft/world/entity/Entity;)V",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/Entity;tick()V",shift=At.Shift.AFTER),require=1)
    private void kneekura$ticked(Entity entity,CallbackInfo ignored){KneekuraDebugDecisionHooks.projectileTickReturn(entity);}
}
