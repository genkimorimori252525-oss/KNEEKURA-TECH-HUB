package dev.kneekura.fivedifficulties.mixin;

import dev.kneekura.fivedifficulties.forge.timestop.TimeStopHooks;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ClientLevel.class)
public abstract class ClientLevelTimeMixin {
    @Inject(method = "tickNonPassenger", at = @At("HEAD"), cancellable = true)
    private void fiveDifficulties$freezeNonPassenger(Entity entity, CallbackInfo ci) {
        ClientLevel level = (ClientLevel) (Object) this;
        if (TimeStopHooks.shouldCancelNormalTick(level, entity)) {
            entity.setOldPosAndRot();
            ci.cancel();
        }
    }

    @Inject(method = "tickPassenger", at = @At("HEAD"), cancellable = true)
    private void fiveDifficulties$freezePassenger(Entity vehicle, Entity passenger, CallbackInfo ci) {
        ClientLevel level = (ClientLevel) (Object) this;
        if (TimeStopHooks.shouldCancelNormalTick(level, passenger)) {
            passenger.setOldPosAndRot();
            ci.cancel();
        }
    }
}
