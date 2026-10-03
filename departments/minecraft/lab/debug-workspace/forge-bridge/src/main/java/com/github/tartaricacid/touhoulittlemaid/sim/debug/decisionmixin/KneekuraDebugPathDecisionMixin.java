package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.PathNavigationRegion;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.level.pathfinder.PathFinder;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import java.util.Set;

@Mixin(value=PathFinder.class,remap=false)
public abstract class KneekuraDebugPathDecisionMixin {
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
