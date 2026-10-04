package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.MoveToTargetSink;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.pathfinder.Path;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.gen.Invoker;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import net.minecraft.world.entity.ai.memory.WalkTarget;

@Mixin(value=MoveToTargetSink.class,remap=false)
public abstract class KneekuraDebugBrainNavigationMixin {
    @Shadow protected abstract void start(ServerLevel level,Mob owner,long gameTime);
    @Shadow protected abstract void tick(ServerLevel level,Mob owner,long gameTime);
    @Shadow protected abstract void stop(ServerLevel level,Mob owner,long gameTime);

    // Pinned bridge/restart bytecode passes this as receiver; the Shadow preserves virtual dispatch.
    @Redirect(method="start(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;start(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V"),require=1)
    private void kneekura$startFromBridge(MoveToTargetSink receiver,ServerLevel level,Mob owner,long gameTime) {
        KneekuraDebugDecisionHooks.originalSinkCall(receiver,owner,gameTime,"START_FROM_BRIDGE",()->start(level,owner,gameTime));
    }
    @Redirect(method="tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V"),require=1)
    private void kneekura$tickFromBridge(MoveToTargetSink receiver,ServerLevel level,Mob owner,long gameTime) {
        KneekuraDebugDecisionHooks.originalSinkCall(receiver,owner,gameTime,"TICK_FROM_BRIDGE",()->tick(level,owner,gameTime));
    }
    @Redirect(method="tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;start(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V"),require=1)
    private void kneekura$startFromTick(MoveToTargetSink receiver,ServerLevel level,Mob owner,long gameTime) {
        KneekuraDebugDecisionHooks.originalSinkCall(receiver,owner,gameTime,"START_FROM_TICK",()->start(level,owner,gameTime));
    }
    @Redirect(method="start(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/Brain;setMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Ljava/lang/Object;)V"),require=1)
    private void kneekura$startPathWrite(Brain<?> brain,MemoryModuleType<?> module,Object value) {
        KneekuraDebugDecisionHooks.originalSinkPathWrite(brain,module,value,(MoveToTargetSink)(Object)this,"START_PATH_WRITE");
    }
    @Redirect(method="tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/Brain;setMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Ljava/lang/Object;)V"),require=1)
    private void kneekura$tickPathWrite(Brain<?> brain,MemoryModuleType<?> module,Object value) {
        KneekuraDebugDecisionHooks.originalSinkPathWrite(brain,module,value,(MoveToTargetSink)(Object)this,"TICK_PATH_RECONCILE");
    }
    @Redirect(method="start(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/navigation/PathNavigation;moveTo(Lnet/minecraft/world/level/pathfinder/Path;D)Z"),require=1)
    private boolean kneekura$navigationReturn(PathNavigation navigation,Path path,double speed) {
        return KneekuraDebugDecisionHooks.originalSinkMoveTo(navigation,path,speed,(MoveToTargetSink)(Object)this);
    }
    @Redirect(method="stop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;stop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V"),require=1)
    private void kneekura$stopFromBridge(MoveToTargetSink receiver,ServerLevel level,Mob owner,long gameTime) {
        KneekuraDebugDecisionHooks.originalSinkCall(receiver,owner,gameTime,"STOP_FROM_BRIDGE",()->stop(level,owner,gameTime));
    }
    @Redirect(method="stop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/navigation/PathNavigation;stop()V"),require=1)
    private void kneekura$navigationStop(PathNavigation navigation) {
        KneekuraDebugDecisionHooks.originalSinkNavigationStop(navigation,(MoveToTargetSink)(Object)this);
    }
    @Redirect(method="stop(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/Brain;eraseMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;)V"),require=2)
    private void kneekura$memoryErase(Brain<?> brain,MemoryModuleType<?> module) {
        KneekuraDebugDecisionHooks.originalSinkMemoryErase(brain,module,(MoveToTargetSink)(Object)this);
    }

    @Invoker(value="tryComputePath",remap=false)
    public abstract boolean kneekura$invokeCompute(Mob owner,WalkTarget target,long gameTime);

    @Redirect(method="checkExtraStartConditions(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;)Z",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;tryComputePath(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;J)Z"),require=1)
    private boolean kneekura$computeFromCheck(MoveToTargetSink receiver,Mob owner,WalkTarget target,long gameTime) {
        return KneekuraDebugDecisionHooks.originalBrainCompute(receiver,owner,target,gameTime,"CHECK_EXTRA_START",()->kneekura$invokeCompute(owner,target,gameTime));
    }
    @Redirect(method="tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;tryComputePath(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;J)Z"),require=1)
    private boolean kneekura$computeFromTick(MoveToTargetSink receiver,Mob owner,WalkTarget target,long gameTime) {
        return KneekuraDebugDecisionHooks.originalBrainCompute(receiver,owner,target,gameTime,"TICK_RECOMPUTE",()->kneekura$invokeCompute(owner,target,gameTime));
    }
    @Redirect(method="tryComputePath(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;J)Z",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/navigation/PathNavigation;createPath(Lnet/minecraft/core/BlockPos;I)Lnet/minecraft/world/level/pathfinder/Path;"),require=1)
    private Path kneekura$initialCreate(PathNavigation navigation,BlockPos target,int accuracy) {
        return KneekuraDebugDecisionHooks.originalBrainCreatePath(navigation,target,accuracy);
    }
    @Redirect(method="tryComputePath(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;J)Z",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/navigation/PathNavigation;createPath(DDDI)Lnet/minecraft/world/level/pathfinder/Path;"),require=1)
    private Path kneekura$fallbackCreate(PathNavigation navigation,double x,double y,double z,int accuracy) {
        return KneekuraDebugDecisionHooks.originalBrainFallbackPath(navigation,x,y,z,accuracy);
    }
    @Inject(method="tryComputePath(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;J)Z",
        at=@At(value="FIELD",target="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;path:Lnet/minecraft/world/level/pathfinder/Path;",opcode=181,ordinal=0,shift=At.Shift.AFTER),require=1)
    private void kneekura$initialStored(Mob owner,WalkTarget target,long gameTime,CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.brainComputePathWrite((MoveToTargetSink)(Object)this,owner,target,gameTime,"INITIAL");
    }
    @Inject(method="tryComputePath(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;J)Z",
        at=@At(value="FIELD",target="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;path:Lnet/minecraft/world/level/pathfinder/Path;",opcode=181,ordinal=1,shift=At.Shift.AFTER),require=1)
    private void kneekura$fallbackStored(Mob owner,WalkTarget target,long gameTime,CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.brainComputePathWrite((MoveToTargetSink)(Object)this,owner,target,gameTime,"FALLBACK");
    }
}
