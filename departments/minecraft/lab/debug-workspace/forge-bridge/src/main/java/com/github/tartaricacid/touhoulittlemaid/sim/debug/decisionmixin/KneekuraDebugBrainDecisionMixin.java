package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.BehaviorControl;
import net.minecraft.world.entity.schedule.Activity;
import net.minecraft.world.entity.schedule.Schedule;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=Brain.class,remap=false)
public abstract class KneekuraDebugBrainDecisionMixin {
    @Redirect(method="startEachNonRunningBehavior(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/BehaviorControl;tryStart(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)Z"),require=1)
    private boolean kneekura$originalTryStart(BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long tick) {
        return KneekuraDebugDecisionHooks.originalBrainTryStart((Brain<?>)(Object)this,control,level,owner,tick);
    }
    @Redirect(method="tickEachRunningBehavior(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/BehaviorControl;tickOrStop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V"),require=1)
    private void kneekura$originalTickOrStop(BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long tick) {
        KneekuraDebugDecisionHooks.originalBrainTickOrStop((Brain<?>)(Object)this,control,level,owner,tick);
    }
    @Redirect(method="updateActivityFromSchedule(JJ)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/schedule/Schedule;getActivityAt(I)Lnet/minecraft/world/entity/schedule/Activity;"),require=1)
    private Activity kneekura$originalActivityQuery(Schedule schedule,int tick) {
        return KneekuraDebugDecisionHooks.originalActivityQuery((Brain<?>)(Object)this,schedule,tick);
    }
    @Inject(method="activityRequirementsAreMet(Lnet/minecraft/world/entity/schedule/Activity;)Z",at=@At("RETURN"),require=1)
    private void kneekura$activityRequirements(Activity requested,CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.activityRequirementsReturn((Brain<?>)(Object)this,requested,result.getReturnValue());
    }
    @Inject(method="setActiveActivity(Lnet/minecraft/world/entity/schedule/Activity;)V",at=@At("RETURN"),require=1)
    private void kneekura$activeActivity(Activity requested,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.activeActivityReturn((Brain<?>)(Object)this,requested);
    }
    @Inject(method="tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",at=@At("RETURN"),require=1)
    private void kneekura$ticked(ServerLevel level,LivingEntity entity,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.brainReturn((Brain<?>)(Object)this,entity);
    }
}
