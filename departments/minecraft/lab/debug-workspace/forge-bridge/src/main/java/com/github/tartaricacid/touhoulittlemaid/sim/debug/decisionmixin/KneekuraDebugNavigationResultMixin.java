package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.pathfinder.Path;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.PathNavigationRegion;
import net.minecraft.world.entity.Mob;
import net.minecraft.core.BlockPos;
import java.util.Set;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=PathNavigation.class,remap=false)
public abstract class KneekuraDebugNavigationResultMixin {
    @Inject(method="moveTo(Lnet/minecraft/world/level/pathfinder/Path;D)Z",at=@At("RETURN"),require=1)
    private void kneekura$moveReturned(Path requested,double speed,CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.navigationMoveReturn((PathNavigation)(Object)this,requested,speed,result.getReturnValueZ());
    }

    @Redirect(method="createPath(Ljava/util/Set;IZIF)Lnet/minecraft/world/level/pathfinder/Path;",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/level/pathfinder/PathFinder;findPath(Lnet/minecraft/world/level/PathNavigationRegion;Lnet/minecraft/world/entity/Mob;Ljava/util/Set;FIF)Lnet/minecraft/world/level/pathfinder/Path;"),require=1)
    private Path kneekura$finderReturn(PathFinder finder,PathNavigationRegion region,Mob owner,Set<BlockPos> targets,float range,int accuracy,float multiplier) {
        return KneekuraDebugDecisionHooks.originalBrainFinder((PathNavigation)(Object)this,finder,region,owner,targets,range,accuracy,multiplier);
    }
}
