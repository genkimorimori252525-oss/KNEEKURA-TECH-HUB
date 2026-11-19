package com.example.kirby_mod.network;

import com.example.kirby_mod.KirbyMod;
import com.example.kirby_mod.entity.KirbyEntity;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.simple.SimpleChannel;

public final class KirbyTelemetryNetwork {

    private static final String PROTOCOL_VERSION = "1";
    private static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            new ResourceLocation(KirbyMod.MODID, "tlm"),
            () -> PROTOCOL_VERSION,
            PROTOCOL_VERSION::equals,
            PROTOCOL_VERSION::equals);
    private static int packetId;
    private static boolean registered;

    private KirbyTelemetryNetwork() {}

    public static void register() {
        if (registered) return;
        CHANNEL.messageBuilder(KirbyTelemetryPacket.class, packetId++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(KirbyTelemetryPacket::encode)
                .decoder(KirbyTelemetryPacket::decode)
                .consumerMainThread(KirbyTelemetryPacket::handle)
                .add();
        CHANNEL.messageBuilder(KirbyHeldMobPresentationPacket.class, packetId++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(KirbyHeldMobPresentationPacket::encode)
                .decoder(KirbyHeldMobPresentationPacket::decode)
                .consumerMainThread(KirbyHeldMobPresentationPacket::handle)
                .add();
        registered = true;
    }

    public static void sendTo(ServerPlayer player, KirbyTelemetryPacket packet) {
        CHANNEL.send(PacketDistributor.PLAYER.with(() -> player), packet);
    }

    public static void sendHeldMobPresentation(KirbyEntity kirby, KirbyHeldMobPresentationPacket packet) {
        CHANNEL.send(PacketDistributor.TRACKING_ENTITY_AND_SELF.with(() -> kirby), packet);
    }

    public static void sendHeldMobPresentationTo(ServerPlayer player, KirbyHeldMobPresentationPacket packet) {
        CHANNEL.send(PacketDistributor.PLAYER.with(() -> player), packet);
    }
}
