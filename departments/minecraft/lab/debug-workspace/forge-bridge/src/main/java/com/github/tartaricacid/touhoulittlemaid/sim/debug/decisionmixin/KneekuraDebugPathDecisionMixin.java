package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.core.BlockPos;
import net.minecraft.util.profiling.ProfilerFiller;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.PathNavigationRegion;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.NodeEvaluator;
import net.minecraft.world.level.pathfinder.BinaryHeap;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import java.util.Set;
import java.util.Map;

@Mixin(value=PathFinder.class,remap=false)
public abstract class KneekuraDebugPathDecisionMixin {
    @Redirect(method="findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;",
            at=@At(value="FIELD",target="Lnet/minecraft/world/level/pathfinder/Node;g:F",opcode=181,ordinal=1),require=1)
    private void kneekura$acceptedGWrite(Node node,float writtenG) {
        KneekuraDebugDecisionHooks.originalAcceptedGWrite((PathFinder)(Object)this,node,writtenG);
    }
    @Redirect(method="findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;",
            at=@At(value="INVOKE",target="Lnet/minecraft/world/level/pathfinder/BinaryHeap;insert(Lnet/minecraft/world/level/pathfinder/Node;)Lnet/minecraft/world/level/pathfinder/Node;",ordinal=0),require=1)
    private Node kneekura$originalStartInsert(BinaryHeap heap,Node node) {
        return KneekuraDebugDecisionHooks.originalHeapInsert((PathFinder)(Object)this,heap,node,true);
    }
    @Redirect(method="findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;",
            at=@At(value="INVOKE",target="Lnet/minecraft/world/level/pathfinder/BinaryHeap;insert(Lnet/minecraft/world/level/pathfinder/Node;)Lnet/minecraft/world/level/pathfinder/Node;",ordinal=1),require=1)
    private Node kneekura$originalRelaxationInsert(BinaryHeap heap,Node node) {
        return KneekuraDebugDecisionHooks.originalHeapInsert((PathFinder)(Object)this,heap,node,false);
    }
    @Redirect(method="findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;",
            at=@At(value="INVOKE",target="Lnet/minecraft/world/level/pathfinder/BinaryHeap;pop()Lnet/minecraft/world/level/pathfinder/Node;"),require=1)
    private Node kneekura$originalPop(BinaryHeap heap) {
        return KneekuraDebugDecisionHooks.originalHeapPop((PathFinder)(Object)this,heap);
    }
    @Inject(method="findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;",
            at=@At(value="FIELD",target="Lnet/minecraft/world/level/pathfinder/Node;closed:Z",opcode=181,ordinal=0,shift=At.Shift.AFTER),require=1)
    private void kneekura$closedWrite(ProfilerFiller profiler,Node start,Map<?,?> targets,float range,int accuracy,float multiplier,CallbackInfoReturnable<Path> ignored) {
        KneekuraDebugDecisionHooks.pathClosedWrite((PathFinder)(Object)this);
    }
    @Redirect(method="findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;",
            at=@At(value="INVOKE",target="Lnet/minecraft/world/level/pathfinder/BinaryHeap;changeCost(Lnet/minecraft/world/level/pathfinder/Node;F)V"),require=1)
    private void kneekura$originalChangeCost(BinaryHeap heap,Node node,float cost) {
        KneekuraDebugDecisionHooks.originalHeapChangeCost((PathFinder)(Object)this,heap,node,cost);
    }
    @Redirect(method="findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;",
            at=@At(value="INVOKE",target="Lnet/minecraft/world/level/pathfinder/NodeEvaluator;getNeighbors([Lnet/minecraft/world/level/pathfinder/Node;Lnet/minecraft/world/level/pathfinder/Node;)I"),require=1)
    private int kneekura$originalNeighbors(NodeEvaluator evaluator,Node[] output,Node current) {
        return KneekuraDebugDecisionHooks.originalNeighbors((PathFinder)(Object)this,evaluator,output,current);
    }
    @Inject(method="findPath(Lnet/minecraft/world/level/PathNavigationRegion;Lnet/minecraft/world/entity/Mob;Ljava/util/Set;FIF)Lnet/minecraft/world/level/pathfinder/Path;",at=@At("HEAD"),require=1)
    private void kneekura$begin(PathNavigationRegion region,Mob mob,Set<BlockPos> targets,float distance,int accuracy,float multiplier,CallbackInfoReturnable<Path> ignored) {
        KneekuraDebugDecisionHooks.pathBegin((PathFinder)(Object)this,mob);
    }
    @Inject(method="findPath(Lnet/minecraft/world/level/PathNavigationRegion;Lnet/minecraft/world/entity/Mob;Ljava/util/Set;FIF)Lnet/minecraft/world/level/pathfinder/Path;",at=@At(value="INVOKE",target="Lnet/minecraft/world/level/pathfinder/NodeEvaluator;done()V",shift=At.Shift.BEFORE),require=1)
    private void kneekura$state(PathNavigationRegion region,Mob mob,Set<BlockPos> targets,float distance,int accuracy,float multiplier,CallbackInfoReturnable<Path> ignored) {
        KneekuraDebugDecisionHooks.pathState((PathFinder)(Object)this,mob);
    }
    @Inject(method="findPath(Lnet/minecraft/world/level/PathNavigationRegion;Lnet/minecraft/world/entity/Mob;Ljava/util/Set;FIF)Lnet/minecraft/world/level/pathfinder/Path;",at=@At("RETURN"),require=1)
    private void kneekura$result(PathNavigationRegion region,Mob mob,Set<BlockPos> targets,float distance,int accuracy,float multiplier,CallbackInfoReturnable<Path> result) {
        PathFinder finder=(PathFinder)(Object)this;
        KneekuraDebugDecisionHooks.pathResult(finder,mob,result.getReturnValue());
        KneekuraDebugDecisionHooks.pathEnd(finder);
    }
}
