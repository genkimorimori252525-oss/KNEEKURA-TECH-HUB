package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.behavior.Behavior;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=Behavior.class,remap=false)
public abstract class KneekuraDebugBehaviorDecisionMixin {
    @Shadow protected abstract boolean timedOut(long tick);
    @Shadow protected abstract boolean canStillUse(ServerLevel level,LivingEntity owner,long tick);
    @Shadow protected abstract void tick(ServerLevel level,LivingEntity owner,long tick);
    @Redirect(method="tickOrStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/Behavior;timedOut(J)Z"),require=1)
    private boolean kneekura$originalTimedOut(Behavior<?> behavior,long tick) {
        return KneekuraDebugDecisionHooks.originalBrainCondition(behavior,tick,"TIMED_OUT",null,null,()->timedOut(tick));
    }
    @Redirect(method="tickOrStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/Behavior;canStillUse(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)Z"),require=1)
    private boolean kneekura$originalCanStillUse(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long tick) {
        return KneekuraDebugDecisionHooks.originalBrainCondition(behavior,tick,"CAN_STILL_USE",level,owner,()->canStillUse(level,owner,tick));
    }
    @Redirect(method="tickOrStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/Behavior;tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V"),require=1)
    private void kneekura$originalTick(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long tick) {
        KneekuraDebugDecisionHooks.originalBrainDispatch(behavior,level,owner,tick,"TICK",()->tick(level,owner,tick));
    }
    @SuppressWarnings({"rawtypes","unchecked"})
    @Redirect(method="tickOrStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/Behavior;doStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V"),require=1)
    private void kneekura$originalStop(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long tick) {
        KneekuraDebugDecisionHooks.originalBrainDispatch(behavior,level,owner,tick,"STOP",()->((Behavior)behavior).doStop(level,owner,tick));
    }
    @Inject(method="tryStart(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)Z",at=@At("RETURN"),require=1)
    private void kneekura$startResult(ServerLevel level,LivingEntity entity,long tick,CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.behaviorReturn((Behavior<?>)(Object)this,entity,"BEHAVIOR_TRY_START_RETURN",result.getReturnValue());
    }
    @Inject(method="tickOrStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",at=@At("RETURN"),require=1)
    private void kneekura$tickResult(ServerLevel level,LivingEntity entity,long tick,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.behaviorReturn((Behavior<?>)(Object)this,entity,"BEHAVIOR_TICK_OR_STOP_RETURN",null);
    }
    @Inject(method="doStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",at=@At("RETURN"),require=1)
    private void kneekura$stopResult(ServerLevel level,LivingEntity entity,long tick,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.behaviorReturn((Behavior<?>)(Object)this,entity,"BEHAVIOR_STOP_RETURN",null);
    }
}
