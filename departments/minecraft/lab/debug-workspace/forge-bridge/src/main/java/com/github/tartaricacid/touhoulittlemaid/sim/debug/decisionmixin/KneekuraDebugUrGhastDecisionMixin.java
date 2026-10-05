package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets="twilightforest.entity.boss.UrGhast",remap=false)
public abstract class KneekuraDebugUrGhastDecisionMixin {
    @Inject(method="setInTantrum(Z)V",at=@At("RETURN"),require=0)
    private void kneekura$tantrumReturn(boolean requested,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.modReturn(this,"setInTantrum",requested);
    }
}
