package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.UpdateActivityFromSchedule;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(value=UpdateActivityFromSchedule.class,remap=false)
public abstract class KneekuraDebugScheduledActivityMixin {
    @Redirect(method="lambda$create$0(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)Z",
        at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/Brain;updateActivityFromSchedule(JJ)V"),require=1)
    private static void kneekura$originalUpdate(Brain<?> brain,long day,long game) {
        KneekuraDebugDecisionHooks.originalActivityUpdate(brain,day,game);
    }
}
