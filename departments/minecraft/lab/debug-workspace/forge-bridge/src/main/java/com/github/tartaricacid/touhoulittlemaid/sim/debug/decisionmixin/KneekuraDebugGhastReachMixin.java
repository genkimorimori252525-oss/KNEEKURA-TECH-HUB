package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.world.entity.monster.Ghast;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(targets="net.minecraft.world.entity.monster.Ghast$GhastMoveControl")
public abstract class KneekuraDebugGhastReachMixin {
    @Shadow @Final private Ghast ghast;

    @Inject(method="canReach(Lnet/minecraft/world/phys/Vec3;I)Z",at=@At("RETURN"))
    private void kneekura$reachReturn(Vec3 direction,int stepCount,CallbackInfoReturnable<Boolean> callback) {
        KneekuraDebugDecisionHooks.ghastReachReturn(ghast,this,direction,stepCount,callback.getReturnValueZ());
    }
}
