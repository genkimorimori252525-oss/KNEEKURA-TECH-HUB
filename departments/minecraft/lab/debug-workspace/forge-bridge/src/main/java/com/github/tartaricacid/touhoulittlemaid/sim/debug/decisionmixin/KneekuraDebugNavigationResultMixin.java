package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.pathfinder.Path;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=PathNavigation.class,remap=false)
public abstract class KneekuraDebugNavigationResultMixin {
    @Inject(method="moveTo(Lnet/minecraft/world/level/pathfinder/Path;D)Z",at=@At("RETURN"),require=1)
    private void kneekura$moveReturned(Path requested,double speed,CallbackInfoReturnable<Boolean> result) {
        KneekuraDebugDecisionHooks.navigationMoveReturn((PathNavigation)(Object)this,requested,speed,result.getReturnValueZ());
    }
}
