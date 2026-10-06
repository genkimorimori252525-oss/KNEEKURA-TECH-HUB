package dev.kneekura.fivedifficulties.mixin;

import dev.kneekura.fivedifficulties.forge.timestop.TimeStopHooks;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerLevel.class)
public abstract class ServerLevelTimeMixin {
    @Inject(method = "tickNonPassenger", at = @At("HEAD"), cancellable = true)
    private void fiveDifficulties$freezeNonPassenger(Entity entity, CallbackInfo ci) {
        ServerLevel level = (ServerLevel) (Object) this;
        if (TimeStopHooks.shouldCancelNormalTick(level, entity)) {
            entity.setOldPosAndRot();
            ci.cancel();
        }
    }

    @Inject(method = "tickPassenger", at = @At("HEAD"), cancellable = true)
    private void fiveDifficulties$freezePassenger(Entity vehicle, Entity passenger, CallbackInfo ci) {
        ServerLevel level = (ServerLevel) (Object) this;
        if (TimeStopHooks.shouldCancelNormalTick(level, passenger)) {
            passenger.setOldPosAndRot();
            ci.cancel();
        }
    }
}
