package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.*;
import java.util.Set;
import java.util.zip.ZipInputStream;

/** Bounded, opt-in display metadata; this never grants world/action authority. */
public final class KneekuraDebugTankPresentationRecipe {
    public static final String RESOURCE_ENTRY = "kneekura/tank-presentation.json";
    public record Geometry(int x, int y, int z, int width, int height, int depth) {}
    public record View(Geometry geometry, boolean bright, String recipeHash) {}

    /** Immutable display context uses the original owner lease, never a new display deadline. */
    record Context(View view, Object server, long issuedNanos, long deadlineNanos) {
        Context {
            long duration = deadlineNanos - issuedNanos;
            if (view == null || server == null || duration <= 0 || duration > 120_000_000_000L) {
                throw new IllegalArgumentException("INVALID_TANK_PRESENTATION_LEASE");
            }
        }
        View viewFor(Object currentServer, long nowNanos) {
            long elapsed = nowNanos - issuedNanos;
            return currentServer == server && elapsed >= 0 && elapsed < deadlineNanos - issuedNanos ? view : null;
        }
    }

    /** Retains a dirty lightmap across disconnect until a client level can recompute it. */
    static final class LightmapTransition {
        private boolean bright;
        private boolean dirty;
        boolean update(boolean currentBright, boolean levelAvailable) {
            if (currentBright != bright) { bright = currentBright; dirty = true; }
            if (!dirty || !levelAvailable) return false;
            dirty = false;
            return true;
        }
    }

    private KneekuraDebugTankPresentationRecipe() {}

    public static View parse(JsonObject saved) {
        if (!"GEOMETRY_VERIFIED".equals(text(saved, "status"))) fail();
        JsonObject recipe = object(saved, "recipe");
        if (integer(recipe, "v") != 1 || !"tank_recipe".equals(text(recipe, "kind"))
                || !"minecraft:overworld".equals(text(recipe, "dimension"))) fail();
        String hash = text(saved, "recipeHash");
        if (hash.startsWith("sha256:")) hash = hash.substring(7);
        if (!hash.matches("[a-f0-9]{64}")) fail();
        if (!hash.equals(KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(recipe)))) fail();
        JsonObject sizes = object(recipe, "dimensions"), origin = object(recipe, "origin");
        int width = integer(sizes, "width"), height = integer(sizes, "height"), depth = integer(sizes, "depth");
        int x = integer(origin, "x"), y = integer(origin, "y"), z = integer(origin, "z");
        if (width < 1 || width > 64 || height < 1 || height > 64 || depth < 1 || depth > 64
                || (long) width * height * depth > 65536 || y < -63 || (long) y + height > 319
                || x < -29999983 || (long) x + width > 29999984
                || z < -29999983 || (long) z + depth > 29999984) fail();
        JsonObject presentation = object(recipe, "presentation");
        if (integer(presentation, "gridSpacing") != 1
                || !Set.of("OBSERVATION_BRIGHT", "NATIVE").contains(text(presentation, "mode"))) fail();
        String mode = text(saved, "displayMode");
        if (!Set.of("OBSERVATION_BRIGHT", "NATIVE").contains(mode)) fail();
        return new View(new Geometry(x, y, z, width, height, depth), mode.equals("OBSERVATION_BRIGHT"), hash);
    }

    /** All scanned entries are bounded, including those preceding the optional capsule. */
    public static View fromRegisteredResource(byte[] artifact) throws IOException {
        if (artifact.length < 4 || artifact[0] != 'P' || artifact[1] != 'K') return null;
        View found = null;
        try (var zip = new ZipInputStream(new ByteArrayInputStream(artifact))) {
            int entries = 0, total = 0;
            for (var entry = zip.getNextEntry(); entry != null; entry = zip.getNextEntry()) {
                if (++entries > 16) throw new IOException("TANK_PRESENTATION_RESOURCE_ENTRY_LIMIT");
                byte[] bytes = zip.readNBytes(64 * 1024 + 1);
                if (bytes.length > 64 * 1024 || (total += bytes.length) > 256 * 1024) {
                    throw new IOException("TANK_PRESENTATION_RESOURCE_SIZE_LIMIT");
                }
                if (!entry.getName().equals(RESOURCE_ENTRY)) continue;
                if (found != null || entry.isDirectory()) throw new IOException("TANK_PRESENTATION_RESOURCE_DUPLICATE");
                String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
                found = parse(KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(text)));
            }
        }
        return found;
    }

    private static JsonObject object(JsonObject value, String key) {
        JsonElement field = value.get(key);
        if (field == null || !field.isJsonObject()) throw new IllegalArgumentException("INVALID_TANK_PRESENTATION");
        return field.getAsJsonObject();
    }
    private static String text(JsonObject value, String key) {
        JsonElement field = value.get(key);
        if (field == null || !field.isJsonPrimitive() || !field.getAsJsonPrimitive().isString()) {
            throw new IllegalArgumentException("INVALID_TANK_PRESENTATION");
        }
        return field.getAsString();
    }
    private static int integer(JsonObject value, String key) {
        JsonElement field = value.get(key);
        if (field == null || !field.isJsonPrimitive() || !field.getAsJsonPrimitive().isNumber()) {
            throw new IllegalArgumentException("INVALID_TANK_PRESENTATION");
        }
        try { return field.getAsBigDecimal().intValueExact(); }
        catch (ArithmeticException error) { throw new IllegalArgumentException("INVALID_TANK_PRESENTATION", error); }
    }
    private static void fail() { throw new IllegalArgumentException("INVALID_TANK_PRESENTATION"); }
}
