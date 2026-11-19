package com.example.kirby_mod.client;

import com.example.kirby_mod.network.KirbyTelemetryPacket;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraftforge.client.event.RegisterGuiOverlaysEvent;
import net.minecraftforge.client.gui.overlay.ForgeGui;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class KirbyTelemetryOverlay {

    private static final long STALE_AFTER_MS = 1500L;
    private static final int X = 8;
    private static final int Y = 8;
    private static boolean visible;
    private static List<String> lines = Collections.emptyList();
    private static long lastUpdateMs;

    private KirbyTelemetryOverlay() {}

    public static void register(RegisterGuiOverlaysEvent event) {
        event.registerAboveAll("tlm", KirbyTelemetryOverlay::render);
    }

    public static void accept(KirbyTelemetryPacket packet) {
        visible = packet.visible();
        lines = visible ? List.copyOf(packet.lines()) : Collections.emptyList();
        lastUpdateMs = System.currentTimeMillis();
    }

    private static void render(ForgeGui gui, GuiGraphics guiGraphics, float partialTick,
                               int screenWidth, int screenHeight) {
        Minecraft minecraft = Minecraft.getInstance();
        if (!visible || lines.isEmpty() || minecraft.options.hideGui) return;

        Font font = minecraft.font;
        List<String> drawLines = new ArrayList<>(lines);
        long ageMs = System.currentTimeMillis() - lastUpdateMs;
        if (ageMs > STALE_AFTER_MS) {
            drawLines.add("WARN stale telemetry ageMs=" + ageMs);
        }

        int maxWidth = 0;
        for (String line : drawLines) {
            maxWidth = Math.max(maxWidth, font.width(line));
        }
        int panelWidth = Math.min(maxWidth + 8, screenWidth - X - 4);
        int panelHeight = drawLines.size() * 10 + 6;
        guiGraphics.fill(X - 4, Y - 4, X + panelWidth, Y + panelHeight, 0xAA000000);

        int y = Y;
        for (String line : drawLines) {
            guiGraphics.drawString(font, line, X, y, colorFor(line), false);
            y += 10;
        }
    }

    private static int colorFor(String line) {
        if (line.startsWith("WARN")) return 0xFFFF5555;
        if (line.startsWith("[")) return 0xFFFFD166;
        if (line.startsWith("thought=") || line.contains(" thought=")) return 0xFF8BE9FD;
        return 0xFFE6E6E6;
    }
}
