package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets="twilightforest.entity.boss.KnightPhantom",remap=false)
public abstract class KneekuraDebugKnightDecisionMixin {
    @Inject(method="switchToFormation(Ltwilightforest/entity/boss/KnightPhantom$Formation;)V",at=@At("RETURN"),require=0)
    private void kneekura$formationReturn(@Coerce Object requested,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.modReturn(this,"switchToFormation",requested);
    }
}
