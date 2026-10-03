package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.sensing.Sensor;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value=Sensor.class,remap=false)
public abstract class KneekuraDebugSensorDecisionMixin {
    @Inject(method="tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/ai/sensing/Sensor;doTick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",shift=At.Shift.AFTER),require=1)
    private void kneekura$scanResult(ServerLevel level,LivingEntity entity,CallbackInfo ignored) {
        KneekuraDebugDecisionHooks.sensorReturn(this,entity);
    }
}
