package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import java.util.List;

@Pseudo
@Mixin(targets="twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal",remap=false)
public abstract class KneekuraDebugKnightCoordinationMixin {
    @Inject(method="broadcastMyFormation(Ljava/util/List;)V",at=@At("RETURN"),require=0,remap=false)
    private void kneekura$broadcastReturn(List<?> originalMembers,CallbackInfo callback) {
        KneekuraDebugDecisionHooks.knightCoordination(this,originalMembers);
    }
}
