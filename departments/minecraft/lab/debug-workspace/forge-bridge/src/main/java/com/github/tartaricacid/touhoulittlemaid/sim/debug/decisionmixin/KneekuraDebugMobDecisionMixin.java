package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(value=Mob.class,remap=false)
public abstract class KneekuraDebugMobDecisionMixin {
    @Inject(method="serverAiStep()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/control/MoveControl;tick()V",shift=At.Shift.AFTER),require=1)
    private void kneekura$moved(CallbackInfo ignored) { KneekuraDebugDecisionHooks.controlReturn((Mob)(Object)this,"move"); }
    @Inject(method="serverAiStep()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/control/LookControl;tick()V",shift=At.Shift.AFTER),require=1)
    private void kneekura$looked(CallbackInfo ignored) { KneekuraDebugDecisionHooks.controlReturn((Mob)(Object)this,"look"); }
    @Inject(method="serverAiStep()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/control/JumpControl;tick()V",shift=At.Shift.AFTER),require=1)
    private void kneekura$jumped(CallbackInfo ignored) { KneekuraDebugDecisionHooks.controlReturn((Mob)(Object)this,"jump"); }
    @Inject(method="getPathfindingMalus(Lnet/minecraft/world/level/pathfinder/BlockPathTypes;)F",at=@At("RETURN"),require=1)
    private void kneekura$malus(BlockPathTypes type,CallbackInfoReturnable<Float> result) {
        KneekuraDebugDecisionHooks.malusReturn((Mob)(Object)this,type,result.getReturnValue());
    }
}
