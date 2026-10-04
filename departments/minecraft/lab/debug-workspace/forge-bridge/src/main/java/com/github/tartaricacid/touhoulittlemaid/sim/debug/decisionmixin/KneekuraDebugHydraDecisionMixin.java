package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Optional MOD target; a finite source-proven callback observes an original RETURN only. */
@Pseudo
@Mixin(targets="twilightforest.entity.boss.HydraHeadContainer",remap=false)
public abstract class KneekuraDebugHydraDecisionMixin {
    @Inject(method="advanceHeadState()V",at=@At("RETURN"),require=0)
    private void kneekura$headReturn(CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.modReturn(this,"advanceHeadState",null);
    }
}
