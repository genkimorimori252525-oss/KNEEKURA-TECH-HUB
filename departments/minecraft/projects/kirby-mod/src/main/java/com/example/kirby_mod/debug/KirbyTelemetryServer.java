package com.example.kirby_mod.debug;

import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.network.KirbyTelemetryNetwork;
import com.example.kirby_mod.network.KirbyTelemetryPacket;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;

import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public final class KirbyTelemetryServer {

    private static final int SEND_PERIOD_TICKS = 5;
    private static final double SEARCH_RADIUS = 64.0D;
    private static final Map<UUID, UUID> TRACKED_KIRBIES = new HashMap<>();

    private KirbyTelemetryServer() {}

    public static int toggle(CommandSourceStack source) throws CommandSyntaxException {
        ServerPlayer player = source.getPlayerOrException();
        if (TRACKED_KIRBIES.containsKey(player.getUUID())) {
            return disable(source);
        }
        return enable(source);
    }

    public static int enable(CommandSourceStack source) throws CommandSyntaxException {
        ServerPlayer player = source.getPlayerOrException();
        KirbyEntity kirby = findNearestKirby(source);
        if (kirby == null) {
            source.sendFailure(Component.literal("No Kirby found within " + (int) SEARCH_RADIUS + " blocks."));
            KirbyTelemetryNetwork.sendTo(player,
                    KirbyTelemetryPacket.visible(KirbyTelemetryFormatter.noKirby("no Kirby within range")));
            return 0;
        }
        TRACKED_KIRBIES.put(player.getUUID(), kirby.getUUID());
        KirbyTelemetryNetwork.sendTo(player, KirbyTelemetryPacket.visible(KirbyTelemetryFormatter.format(kirby)));
        source.sendSuccess(() -> Component.literal("TLM enabled for nearest Kirby " + shortId(kirby.getUUID()) + "."), false);
        return 1;
    }

    public static int disable(CommandSourceStack source) throws CommandSyntaxException {
        ServerPlayer player = source.getPlayerOrException();
        TRACKED_KIRBIES.remove(player.getUUID());
        KirbyTelemetryNetwork.sendTo(player, KirbyTelemetryPacket.hidden());
        source.sendSuccess(() -> Component.literal("TLM disabled."), false);
        return 1;
    }

    public static int once(CommandSourceStack source) {
        KirbyEntity kirby = findNearestKirby(source);
        if (kirby == null) {
            source.sendFailure(Component.literal("No Kirby found within " + (int) SEARCH_RADIUS + " blocks."));
            return 0;
        }
        for (String line : KirbyTelemetryFormatter.format(kirby)) {
            source.sendSuccess(() -> Component.literal(line), false);
        }
        return 1;
    }

    public static void tick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        MinecraftServer server = event.getServer();
        if (server.getTickCount() % SEND_PERIOD_TICKS != 0) return;
        if (TRACKED_KIRBIES.isEmpty()) return;

        Iterator<Map.Entry<UUID, UUID>> iter = TRACKED_KIRBIES.entrySet().iterator();
        while (iter.hasNext()) {
            Map.Entry<UUID, UUID> entry = iter.next();
            ServerPlayer player = server.getPlayerList().getPlayer(entry.getKey());
            if (player == null) {
                iter.remove();
                continue;
            }

            KirbyEntity kirby = resolveTrackedKirby(player, entry.getValue());
            if (kirby == null) {
                kirby = findNearestKirby(player.createCommandSourceStack());
                if (kirby != null) {
                    entry.setValue(kirby.getUUID());
                }
            }

            List<String> lines = kirby == null
                    ? KirbyTelemetryFormatter.noKirby("tracked Kirby unavailable")
                    : KirbyTelemetryFormatter.format(kirby);
            KirbyTelemetryNetwork.sendTo(player, KirbyTelemetryPacket.visible(lines));
        }
    }

    private static KirbyEntity resolveTrackedKirby(ServerPlayer player, UUID kirbyId) {
        if (!(player.serverLevel().getEntity(kirbyId) instanceof KirbyEntity kirby)) return null;
        return kirby.isAlive() && !kirby.isRemoved() ? kirby : null;
    }

    private static KirbyEntity findNearestKirby(CommandSourceStack source) {
        ServerLevel level = source.getLevel();
        Vec3 pos = source.getPosition();
        AABB box = new AABB(pos, pos).inflate(SEARCH_RADIUS);
        List<KirbyEntity> candidates = level.getEntitiesOfClass(KirbyEntity.class, box,
                kirby -> kirby.isAlive() && !kirby.isRemoved());
        KirbyEntity closest = null;
        double bestDistSq = Double.MAX_VALUE;
        for (KirbyEntity kirby : candidates) {
            double distSq = kirby.distanceToSqr(pos);
            if (distSq < bestDistSq) {
                bestDistSq = distSq;
                closest = kirby;
            }
        }
        return closest;
    }

    private static String shortId(UUID uuid) {
        return uuid.toString().substring(0, 8);
    }
}
