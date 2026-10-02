package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.*;
import java.util.zip.*;

/** Saved geometry is a display preference, never a world/action authority. */
public final class KneekuraDebugTankPresentationSelfTest {
    public static void main(String[] args) throws Exception {
        JsonObject saved = fixture();
        var view = KneekuraDebugTankPresentationRecipe.parse(saved);
        if (!view.bright() || view.geometry().y() != 224 || view.geometry().width() != 19) {
            throw new AssertionError("actual Tank geometry and bright preference");
        }
        int checks = 1;
        Object server = new Object();
        var context = new KneekuraDebugTankPresentationRecipe.Context(view, server, 100, 1100);
        if (context.viewFor(server, 100) != view || context.viewFor(server, 1099) != view) {
            throw new AssertionError("current server retains original finite lease");
        }
        checks++;
        for (long now : new long[]{99, 1100, 1101}) {
            if (context.viewFor(server, now) != null) throw new AssertionError("paused server cannot extend lease");
            checks++;
        }
        for (Object other : new Object[]{null, new Object()}) {
            if (context.viewFor(other, 101) != null) throw new AssertionError("disconnected or same-name foreign server");
            checks++;
        }
        var wrapped = new KneekuraDebugTankPresentationRecipe.Context(view, server, Long.MAX_VALUE - 10, Long.MIN_VALUE + 9);
        if (wrapped.viewFor(server, Long.MIN_VALUE) != view || wrapped.viewFor(server, Long.MIN_VALUE + 9) != null) {
            throw new AssertionError("monotonic elapsed time across signed long wrap");
        }
        checks++;
        for (long deadline : new long[]{100, 100 + 120_000_000_001L}) {
            try {
                new KneekuraDebugTankPresentationRecipe.Context(view, server, 100, deadline);
                throw new AssertionError("invalid presentation lease accepted");
            } catch (IllegalArgumentException expected) { checks++; }
        }
        var lightmap = new KneekuraDebugTankPresentationRecipe.LightmapTransition();
        if (lightmap.update(false, true) || !lightmap.update(true, true)
                || lightmap.update(true, true) || !lightmap.update(false, true)
                || lightmap.update(false, true)) {
            throw new AssertionError("lightmap recomputes only on activation or expiry even without server ticks");
        }
        checks++;
        if (!lightmap.update(true, true) || lightmap.update(false, false)
                || !lightmap.update(false, true) || lightmap.update(false, true)) {
            throw new AssertionError("disconnect retains invalidation until a client level exists");
        }
        checks++;
        JsonObject nativeView = saved.deepCopy();
        nativeView.addProperty("displayMode", "NATIVE");
        if (KneekuraDebugTankPresentationRecipe.parse(nativeView).bright()) {
            throw new AssertionError("NATIVE must preserve native lighting");
        }
        checks++;
        for (String change : new String[]{"unknown", "hash", "dimension", "width", "fraction",
                "height", "boundary", "mode", "grid", "recipe-kind", "schema", "numeric-string"}) {
            JsonObject altered = saved.deepCopy();
            var recipe = altered.getAsJsonObject("recipe");
            switch (change) {
                case "unknown" -> altered.addProperty("status", "OUTCOME_UNKNOWN");
                case "hash" -> altered.addProperty("recipeHash", "sha256:" + "0".repeat(64));
                case "dimension" -> recipe.addProperty("dimension", "minecraft:the_nether");
                case "width" -> recipe.getAsJsonObject("dimensions").addProperty("width", 65);
                case "fraction" -> recipe.getAsJsonObject("dimensions").addProperty("height", 1.5);
                case "height" -> recipe.getAsJsonObject("origin").addProperty("y", 319);
                case "boundary" -> recipe.getAsJsonObject("origin").addProperty("x", 30000000);
                case "mode" -> altered.addProperty("displayMode", "UNKNOWN");
                case "grid" -> recipe.getAsJsonObject("presentation").addProperty("gridSpacing", 0);
                case "recipe-kind" -> recipe.addProperty("kind", "arbitrary");
                case "schema" -> recipe.addProperty("v", true);
                case "numeric-string" -> recipe.getAsJsonObject("origin").addProperty("y", "224");
            }
            if (!change.equals("hash")) bind(altered);
            try {
                KneekuraDebugTankPresentationRecipe.parse(altered);
                throw new AssertionError("unsafe saved presentation accepted: " + change);
            } catch (IllegalArgumentException expected) {
                checks++;
            }
        }
        if (KneekuraDebugTankPresentationRecipe.fromRegisteredResource(new byte[]{1, 2}) != null) {
            throw new AssertionError("unregistered plain artifact enabled presentation");
        }
        checks++;
        byte[] capsule = saved.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        if (!view.equals(KneekuraDebugTankPresentationRecipe.fromRegisteredResource(pack(capsule, false)))) {
            throw new AssertionError("registered capsule round trip");
        }
        checks++;
        for (boolean oversized : new boolean[]{false, true}) {
            try {
                KneekuraDebugTankPresentationRecipe.fromRegisteredResource(pack(new byte[]{(byte) 0xff}, oversized));
                throw new AssertionError("unbounded entry or invalid UTF8 accepted");
            } catch (IOException expected) { checks++; }
        }
        if (!saved.equals(fixture())) throw new AssertionError("presentation parser changed source metadata");
        System.out.println("Tank presentation source contracts passed: " + (++checks));
    }

    private static byte[] pack(byte[] capsule, boolean oversized) throws IOException {
        var bytes = new ByteArrayOutputStream();
        try (var zip = new ZipOutputStream(bytes)) {
            if (oversized) {
                zip.putNextEntry(new ZipEntry("unused-before-capsule"));
                zip.write(new byte[64 * 1024 + 1]);
                zip.closeEntry();
            }
            zip.putNextEntry(new ZipEntry(KneekuraDebugTankPresentationRecipe.RESOURCE_ENTRY));
            zip.write(capsule);
            zip.closeEntry();
        }
        return bytes.toByteArray();
    }

    private static JsonObject fixture() {
        JsonObject root = JsonParser.parseString("""
                {"status":"GEOMETRY_VERIFIED","displayMode":"OBSERVATION_BRIGHT","recipe":{
                "v":1,"kind":"tank_recipe","dimension":"minecraft:overworld",
                "dimensions":{"width":19,"depth":19,"height":11},"origin":{"x":0,"y":224,"z":0},
                "presentation":{"mode":"OBSERVATION_BRIGHT","gridSpacing":1}}}
                """).getAsJsonObject();
        bind(root);
        return root;
    }

    private static void bind(JsonObject root) {
        root.addProperty("recipeHash", "sha256:" + KneekuraDebugActionJournal.sha256(
                KneekuraDebugActionJournal.canonical(root.getAsJsonObject("recipe"))));
    }
}
