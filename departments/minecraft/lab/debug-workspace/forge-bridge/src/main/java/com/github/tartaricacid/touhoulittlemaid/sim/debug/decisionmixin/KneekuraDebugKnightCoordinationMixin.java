package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import org.spongepowered.asm.mixin.injection.callback.LocalCapture;
import org.spongepowered.asm.mixin.injection.Coerce;
import java.util.List;
import java.util.Iterator;

@Pseudo
@Mixin(targets="twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal",remap=false)
public abstract class KneekuraDebugKnightCoordinationMixin {
    @Inject(method="broadcastMyFormation(Ljava/util/List;)V",at=@At("RETURN"),require=0,remap=false)
    private void kneekura$broadcastReturn(List<?> originalMembers,CallbackInfo callback) {
        KneekuraDebugDecisionHooks.knightCoordination(this,originalMembers);
    }
    @Inject(method="isThisTheLeader(Ljava/util/List;)Z",at=@At("RETURN"),require=0,remap=false)
    private void kneekura$leaderReturn(List<?> originalMembers,CallbackInfoReturnable<Boolean> callback) {
        KneekuraDebugDecisionHooks.knightLeader(this,originalMembers,callback.getReturnValue());
    }
    /** Observe the original returned call and retained loop local; no setter or eligibility is replayed. */
    @Inject(method="broadcastMyFormation(Ljava/util/List;)V",at=@At(value="INVOKE",
        target="Ltwilightforest/entity/boss/KnightPhantom;switchToFormation(Ltwilightforest/entity/boss/KnightPhantom$Formation;)V",
        shift=At.Shift.AFTER),locals=LocalCapture.CAPTURE_FAILSOFT,require=0,remap=false)
    private void kneekura$memberDispatch(List<?> originalMembers,CallbackInfo callback,Iterator<?> iterator,@Coerce Object member) {
        KneekuraDebugDecisionHooks.knightMemberDispatch(this,member);
    }
}
