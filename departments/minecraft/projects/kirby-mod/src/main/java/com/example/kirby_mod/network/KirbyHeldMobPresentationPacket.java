package com.example.kirby_mod.network;

import com.example.kirby_mod.client.HeldMobPresentationRegistry;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.function.Supplier;

public final class KirbyHeldMobPresentationPacket {

    private static final int MAX_HELD_MOBS = 5;

    private final int kirbyEntityId;
    private final int revision;
    private final List<UUID> heldMobIds;

    public KirbyHeldMobPresentationPacket(int kirbyEntityId, int revision, List<UUID> heldMobIds) {
        this.kirbyEntityId = kirbyEntityId;
        this.revision = revision;
        this.heldMobIds = List.copyOf(heldMobIds);
    }

    public static void encode(KirbyHeldMobPresentationPacket packet, FriendlyByteBuf buf) {
        buf.writeVarInt(packet.kirbyEntityId);
        buf.writeVarInt(packet.revision);
        int size = Math.min(packet.heldMobIds.size(), MAX_HELD_MOBS);
        buf.writeVarInt(size);
        for (int i = 0; i < size; i++) {
            buf.writeUUID(packet.heldMobIds.get(i));
        }
    }

    public static KirbyHeldMobPresentationPacket decode(FriendlyByteBuf buf) {
        int kirbyEntityId = buf.readVarInt();
        int revision = buf.readVarInt();
        int encodedSize = buf.readVarInt();
        List<UUID> heldMobIds = new ArrayList<>(Math.min(encodedSize, MAX_HELD_MOBS));
        for (int i = 0; i < encodedSize; i++) {
            UUID id = buf.readUUID();
            if (i < MAX_HELD_MOBS) {
                heldMobIds.add(id);
            }
        }
        return new KirbyHeldMobPresentationPacket(kirbyEntityId, revision, heldMobIds);
    }

    public static void handle(KirbyHeldMobPresentationPacket packet, Supplier<NetworkEvent.Context> context) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT,
                () -> () -> HeldMobPresentationRegistry.apply(packet.kirbyEntityId, packet.revision, packet.heldMobIds));
    }
}
