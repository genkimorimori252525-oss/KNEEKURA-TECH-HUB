package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.behavior.OneShot;
import net.minecraft.world.entity.ai.behavior.BehaviorControl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=OneShot.class,remap=false)
public abstract class KneekuraDebugOneShotDecisionMixin {
    @Inject(method="tryStart(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)Z",at=@At("RETURN"),require=1)
    private void kneekura$startResult(ServerLevel level,LivingEntity entity,long tick,CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.behaviorControlReturn((BehaviorControl<?>)(Object)this,entity,"BEHAVIOR_TRY_START_RETURN",result.getReturnValue());
    }
    @Inject(method="tickOrStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",at=@At("RETURN"),require=1)
    private void kneekura$tickResult(ServerLevel level,LivingEntity entity,long tick,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.behaviorControlReturn((BehaviorControl<?>)(Object)this,entity,"BEHAVIOR_TICK_OR_STOP_RETURN",null);
    }
    @Inject(method="doStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",at=@At("RETURN"),require=1)
    private void kneekura$stopResult(ServerLevel level,LivingEntity entity,long tick,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.behaviorControlReturn((BehaviorControl<?>)(Object)this,entity,"BEHAVIOR_STOP_RETURN",null);
    }
}
