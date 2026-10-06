package dev.kneekura.fivedifficulties.mixin;

import dev.kneekura.fivedifficulties.forge.timestop.TimeStopHooks;
import net.minecraft.network.protocol.game.ClientboundMoveVehiclePacket;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.network.protocol.game.ServerboundMoveVehiclePacket;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * ServerPlayer is advanced by the connection tick path, not only by
 * ServerLevel.tickNonPassenger. Keep connection/keepalive ticking, but suppress
 * the actual player simulation and movement packets while X1 time policy says
 * this phase is frozen.
 */
@Mixin(ServerGamePacketListenerImpl.class)
public abstract class ServerGamePacketListenerTimeMixin {
    @Shadow public ServerPlayer player;

    @Redirect(
            method = "tick",
            at = @At(
                    value = "INVOKE",
                    target = "Lnet/minecraft/server/level/ServerPlayer;doTick()V"
            )
    )
    private void fiveDifficulties$gatePlayerDoTick(ServerPlayer player) {
        if (TimeStopHooks.shouldCancelNormalTick(player.serverLevel(), player)) {
            player.setOldPosAndRot();
            return;
        }
        player.doTick();
    }

    @Inject(method = "handleMovePlayer", at = @At("HEAD"), cancellable = true)
    private void fiveDifficulties$rejectFrozenPlayerMove(ServerboundMovePlayerPacket packet, CallbackInfo ci) {
        if (!TimeStopHooks.shouldCancelNormalTick(this.player.serverLevel(), this.player)) {
            return;
        }

        ServerGamePacketListenerImpl self = (ServerGamePacketListenerImpl) (Object) this;
        self.teleport(
                this.player.getX(),
                this.player.getY(),
                this.player.getZ(),
                this.player.getYRot(),
                this.player.getXRot()
        );
        ci.cancel();
    }

    @Inject(method = "handlePlayerInput", at = @At("HEAD"), cancellable = true)
    private void fiveDifficulties$rejectFrozenPlayerInput(ServerboundPlayerInputPacket packet, CallbackInfo ci) {
        if (!TimeStopHooks.shouldCancelNormalTick(this.player.serverLevel(), this.player)) {
            return;
        }
        this.player.setPlayerInput(0.0F, 0.0F, false, false);
        ci.cancel();
    }

    @Inject(method = "handleMoveVehicle", at = @At("HEAD"), cancellable = true)
    private void fiveDifficulties$rejectFrozenVehicleMove(ServerboundMoveVehiclePacket packet, CallbackInfo ci) {
        Entity vehicle = this.player.getRootVehicle();
        if (vehicle == this.player
                || !TimeStopHooks.shouldCancelNormalTick(this.player.serverLevel(), vehicle)) {
            return;
        }

        this.player.connection.send(new ClientboundMoveVehiclePacket(vehicle));
        ci.cancel();
    }
}
