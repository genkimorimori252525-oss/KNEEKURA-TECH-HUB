package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.world.entity.ai.goal.WrappedGoal;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=WrappedGoal.class,remap=false)
public abstract class KneekuraDebugWrappedGoalDecisionMixin {
    @Inject(method="canUse()Z",at=@At("RETURN"),require=1)
    private void kneekura$eligibility(CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.goalReturn((WrappedGoal)(Object)this,false,result.getReturnValue());
    }
    @Inject(method="canContinueToUse()Z",at=@At("RETURN"),require=1)
    private void kneekura$continuation(CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.goalReturn((WrappedGoal)(Object)this,true,result.getReturnValue());
    }
    @Inject(method="start()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/goal/Goal;start()V",shift=At.Shift.AFTER),require=1)
    private void kneekura$started(CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.goalLifecycle((WrappedGoal)(Object)this,true);
    }
    @Inject(method="stop()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/goal/Goal;stop()V",shift=At.Shift.AFTER),require=1)
    private void kneekura$stopped(CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.goalLifecycle((WrappedGoal)(Object)this,false);
    }
}
