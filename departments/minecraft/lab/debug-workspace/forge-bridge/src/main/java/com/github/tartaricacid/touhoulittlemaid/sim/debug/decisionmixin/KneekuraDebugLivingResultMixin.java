package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(LivingEntity.class)
public abstract class KneekuraDebugLivingResultMixin {
    @Inject(method="randomTeleport(DDDZ)Z",at=@At("RETURN"))
    private void kneekura$teleportReturn(double x,double y,double z,boolean particles,CallbackInfoReturnable<Boolean> callback) {
        KneekuraDebugDecisionHooks.teleportReturn((LivingEntity)(Object)this,x,y,z,callback.getReturnValueZ());
    }
}
