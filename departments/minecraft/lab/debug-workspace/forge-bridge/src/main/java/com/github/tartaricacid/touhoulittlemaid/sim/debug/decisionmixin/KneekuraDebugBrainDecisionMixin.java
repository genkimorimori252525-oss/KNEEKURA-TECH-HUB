package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.BehaviorControl;
import net.minecraft.world.entity.ai.behavior.Behavior;
import net.minecraft.world.entity.schedule.Activity;
import net.minecraft.world.entity.schedule.Schedule;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.gen.Invoker;
import java.util.Set;
import java.util.Map;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=Brain.class,remap=false)
public abstract class KneekuraDebugBrainDecisionMixin {
    @Redirect(method="checkMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;)Z",
        at=@At(value="INVOKE",target="Ljava/util/Map;get(Ljava/lang/Object;)Ljava/lang/Object;"),require=1)
    private Object kneekura$memorySourceGet(Map<?,?> map,Object key,MemoryModuleType<?> module,MemoryStatus requested) {
        return KneekuraDebugDecisionHooks.originalMemorySourceGet((Brain<?>)(Object)this,map,key,module,requested);
    }
    @Redirect(method="checkMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;)Z",
        at=@At(value="INVOKE",target="Ljava/util/Optional;isPresent()Z",ordinal=0),require=1)
    private boolean kneekura$memorySourcePresent(java.util.Optional<?> slot,MemoryModuleType<?> module,MemoryStatus requested) {
        return KneekuraDebugDecisionHooks.originalMemorySourcePresence((Brain<?>)(Object)this,slot,module,requested,"VALUE_PRESENT");
    }
    @Redirect(method="checkMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;)Z",
        at=@At(value="INVOKE",target="Ljava/util/Optional;isPresent()Z",ordinal=1),require=1)
    private boolean kneekura$memorySourceAbsent(java.util.Optional<?> slot,MemoryModuleType<?> module,MemoryStatus requested) {
        return KneekuraDebugDecisionHooks.originalMemorySourcePresence((Brain<?>)(Object)this,slot,module,requested,"VALUE_ABSENT");
    }
    @Inject(method="checkMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;)Z",at=@At("RETURN"),require=2)
    private void kneekura$memorySourceReturn(MemoryModuleType<?> module,MemoryStatus requested,CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.memorySourceBaseReturn((Brain<?>)(Object)this,module,requested,result.getReturnValue());
    }
    @Invoker(value="activityRequirementsAreMet",remap=false)
    public abstract boolean kneekura$invokeActivityRequirement(Activity requested);

    @Redirect(method="setActiveActivityIfPossible(Lnet/minecraft/world/entity/schedule/Activity;)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/Brain;activityRequirementsAreMet(Lnet/minecraft/world/entity/schedule/Activity;)Z"),require=1)
    private boolean kneekura$requirementIfPossible(Brain<?> brain,Activity requested) {
        return KneekuraDebugDecisionHooks.originalActivityRequirement(brain,requested,"IF_POSSIBLE",()->kneekura$invokeActivityRequirement(requested));
    }
    @Redirect(method="setActiveActivityToFirstValid(Ljava/util/List;)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/Brain;activityRequirementsAreMet(Lnet/minecraft/world/entity/schedule/Activity;)Z"),require=1)
    private boolean kneekura$requirementFirstValid(Brain<?> brain,Activity requested) {
        return KneekuraDebugDecisionHooks.originalActivityRequirement(brain,requested,"FIRST_VALID",()->kneekura$invokeActivityRequirement(requested));
    }
    @Redirect(method="activityRequirementsAreMet(Lnet/minecraft/world/entity/schedule/Activity;)Z",
        at=@At(value="INVOKE",target="Ljava/util/Map;containsKey(Ljava/lang/Object;)Z"),require=1)
    private boolean kneekura$requirementContains(Map<?,?> map,Object key,Activity requested) {
        return KneekuraDebugDecisionHooks.originalActivityRequirementContains((Brain<?>)(Object)this,map,key,requested);
    }
    @Redirect(method="activityRequirementsAreMet(Lnet/minecraft/world/entity/schedule/Activity;)Z",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/Brain;checkMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;)Z"),require=1)
    private boolean kneekura$requirementCheck(Brain<?> brain,MemoryModuleType<?> module,MemoryStatus status,Activity requested) {
        return KneekuraDebugDecisionHooks.originalActivityRequirementCheck(brain,module,status,requested);
    }
    @Invoker(value="startEachNonRunningBehavior",remap=false)
    public abstract void kneekura$invokeStartEach(ServerLevel level,LivingEntity owner);

    @Redirect(method="tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/Brain;startEachNonRunningBehavior(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V"),require=1)
    private void kneekura$originalStartLoop(Brain<?> brain,ServerLevel level,LivingEntity owner) {
        KneekuraDebugDecisionHooks.originalBrainStartLoop(brain,level,owner,()->kneekura$invokeStartEach(level,owner));
    }
    @Redirect(method="startEachNonRunningBehavior(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",
        at=@At(value="INVOKE",target="Ljava/util/Set;contains(Ljava/lang/Object;)Z"),require=1)
    private boolean kneekura$originalStartActivity(Set<?> activities,Object requested,ServerLevel level,LivingEntity owner) {
        return KneekuraDebugDecisionHooks.originalBrainStartActivity((Brain<?>)(Object)this,activities,requested,level,owner);
    }
    @Redirect(method="startEachNonRunningBehavior(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/BehaviorControl;getStatus()Lnet/minecraft/world/entity/ai/behavior/Behavior$Status;"),require=1)
    private Behavior.Status kneekura$originalStartStatus(BehaviorControl<?> control,ServerLevel level,LivingEntity owner) {
        return KneekuraDebugDecisionHooks.originalBrainStartStatus((Brain<?>)(Object)this,control,level,owner);
    }
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
