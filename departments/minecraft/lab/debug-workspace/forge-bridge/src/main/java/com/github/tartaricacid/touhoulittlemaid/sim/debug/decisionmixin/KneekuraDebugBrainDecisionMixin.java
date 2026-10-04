package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.Brain;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value=Brain.class,remap=false)
public abstract class KneekuraDebugBrainDecisionMixin {
    @Inject(method="tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",at=@At("RETURN"),require=1)
    private void kneekura$ticked(ServerLevel level,LivingEntity entity,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.brainReturn((Brain<?>)(Object)this,entity);
    }
}
