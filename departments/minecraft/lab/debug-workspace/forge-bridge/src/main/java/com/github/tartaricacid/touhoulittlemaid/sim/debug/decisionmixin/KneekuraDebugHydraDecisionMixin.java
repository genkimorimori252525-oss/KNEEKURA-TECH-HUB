package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import net.minecraft.world.entity.Entity;
import org.objectweb.asm.Opcodes;

/** Optional MOD target; a finite source-proven callback observes an original RETURN only. */
@Pseudo
@Mixin(targets="twilightforest.entity.boss.HydraHeadContainer",remap=false)
public abstract class KneekuraDebugHydraDecisionMixin {
    @Inject(method="advanceHeadState()V",at=@At("RETURN"),require=0)
    private void kneekura$headReturn(CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.modReturn(this,"advanceHeadState",null);
    }
    @Inject(method="setTargetEntity(Lnet/minecraft/world/entity/Entity;)V",at=@At("RETURN"),require=0)
    private void kneekura$assignedTarget(Entity requested,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.hydraTargetReturn(this,requested);
    }
    @Inject(method="advanceHeadState()V",at=@At(value="FIELD",
        target="Ltwilightforest/entity/boss/HydraHeadContainer;currentState:Ltwilightforest/entity/boss/HydraHeadContainer$State;",
        opcode=Opcodes.PUTFIELD,shift=At.Shift.AFTER),require=0)
    private void kneekura$stateWrite(CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.hydraStateWrite(this);
    }
}
