package com.example.kirby_mod.network;

import com.example.kirby_mod.client.KirbyTelemetryOverlay;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Supplier;

public final class KirbyTelemetryPacket {

    private static final int MAX_LINES = 80;
    private static final int MAX_LINE_LENGTH = 180;

    private final boolean visible;
    private final List<String> lines;

    private KirbyTelemetryPacket(boolean visible, List<String> lines) {
        this.visible = visible;
        this.lines = List.copyOf(lines);
    }

    public static KirbyTelemetryPacket visible(List<String> lines) {
        return new KirbyTelemetryPacket(true, lines);
    }

    public static KirbyTelemetryPacket hidden() {
        return new KirbyTelemetryPacket(false, Collections.emptyList());
    }

    public boolean visible() {
        return visible;
    }

    public List<String> lines() {
        return lines;
    }

    public static void encode(KirbyTelemetryPacket packet, FriendlyByteBuf buf) {
        buf.writeBoolean(packet.visible);
        int size = Math.min(packet.lines.size(), MAX_LINES);
        buf.writeVarInt(size);
        for (int i = 0; i < size; i++) {
            String line = packet.lines.get(i);
            if (line.length() > MAX_LINE_LENGTH) {
                line = line.substring(0, MAX_LINE_LENGTH);
            }
            buf.writeUtf(line, MAX_LINE_LENGTH);
        }
    }

    public static KirbyTelemetryPacket decode(FriendlyByteBuf buf) {
        boolean visible = buf.readBoolean();
        int encodedSize = buf.readVarInt();
        List<String> lines = new ArrayList<>(Math.min(encodedSize, MAX_LINES));
        for (int i = 0; i < encodedSize; i++) {
            String line = buf.readUtf(MAX_LINE_LENGTH);
            if (i < MAX_LINES) {
                lines.add(line);
            }
        }
        return new KirbyTelemetryPacket(visible, lines);
    }

    public static void handle(KirbyTelemetryPacket packet, Supplier<NetworkEvent.Context> context) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> KirbyTelemetryOverlay.accept(packet));
    }
}
