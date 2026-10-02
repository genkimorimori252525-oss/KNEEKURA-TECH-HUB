package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.google.gson.JsonObject;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.DynamicTexture;

import javax.annotation.Nullable;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Immutable CPU snapshot of the two auxiliary entity-shader textures for one real draw invocation.
 *
 * <p>The snapshot reads the already-resolved runtime textures. It never reconstructs overlay from
 * hurt state or lightmap color from world/biome/weather data. The private DynamicTexture inside each
 * public GameRenderer holder is located structurally by type and accepted only when exactly one
 * candidate exists. Field names are provenance-unsafe and are never used.
 *
 * <p>Coordinates are resolved with the Minecraft 1.20.1 entity vertex-shader rules at capture time:
 * overlay uses the integer UV1 texel directly; lightmap uses integer UV2 / 16. The resulting RGBA
 * values cross the runtime boundary as generic per-vertex colors, so the Thin Viewer never samples
 * Minecraft overlay/lightmap textures.
 */
final class SimAuxiliarySamplerState {
    private static final String STATUS = "resolved-per-vertex-rgba";
    private static final int CHANNELS = 4;

    private final ImageSnapshot overlay;
    private final ImageSnapshot lightmap;

    private SimAuxiliarySamplerState(ImageSnapshot overlay, ImageSnapshot lightmap) {
        this.overlay = overlay;
        this.lightmap = lightmap;
    }

    @Nullable
    static SimAuxiliarySamplerState capture() {
        try {
            Minecraft mc = Minecraft.getInstance();
            if (mc == null || mc.gameRenderer == null) return null;

            ImageSnapshot overlay = snapshotUniqueDynamicTexture(mc.gameRenderer.overlayTexture());
            ImageSnapshot lightmap = snapshotUniqueDynamicTexture(mc.gameRenderer.lightTexture());
            if (overlay == null || lightmap == null) return null;
            return new SimAuxiliarySamplerState(overlay, lightmap);
        } catch (Throwable ignored) {
            return null;
        }
    }

    boolean sameBits(@Nullable SimAuxiliarySamplerState other) {
        return other != null
                && this.overlay.sameBits(other.overlay)
                && this.lightmap.sameBits(other.lightmap);
    }

    @Nullable
    float[] resolveOverlay(int u, int v) {
        return this.overlay.sample(u, v);
    }

    @Nullable
    float[] resolveLightmap(int u, int v) {
        return this.lightmap.sample(u / 16, v / 16);
    }

    JsonObject toEvidenceJson() {
        JsonObject root = new JsonObject();
        root.addProperty("status", STATUS);
        root.addProperty("componentEncoding", "UNORM8_RGBA_TO_FLOAT32");

        JsonObject overlayEvidence = new JsonObject();
        overlayEvidence.addProperty("width", this.overlay.width);
        overlayEvidence.addProperty("height", this.overlay.height);
        overlayEvidence.addProperty("coordinateRule", "directIntegerTexel");
        root.add("overlay", overlayEvidence);

        JsonObject lightmapEvidence = new JsonObject();
        lightmapEvidence.addProperty("width", this.lightmap.width);
        lightmapEvidence.addProperty("height", this.lightmap.height);
        lightmapEvidence.addProperty("coordinateRule", "integerDivide16Texel");
        root.add("lightmap", lightmapEvidence);
        return root;
    }

    @Nullable
    private static ImageSnapshot snapshotUniqueDynamicTexture(Object holder) {
        if (holder == null) return null;
        try {
            List<DynamicTexture> candidates = new ArrayList<>();
            for (Class<?> type = holder.getClass();
                    type != null && type != Object.class;
                    type = type.getSuperclass()) {
                for (Field field : type.getDeclaredFields()) {
                    if (Modifier.isStatic(field.getModifiers())
                            || field.getType() != DynamicTexture.class) {
                        continue;
                    }
                    field.setAccessible(true);
                    Object value = field.get(holder);
                    if (value instanceof DynamicTexture texture) {
                        candidates.add(texture);
                    }
                }
            }
            if (candidates.size() != 1) return null;

            NativeImage image = candidates.get(0).getPixels();
            if (image == null) return null;
            int width = image.getWidth();
            int height = image.getHeight();
            if (width <= 0 || height <= 0) return null;
            long pixelCount = (long) width * (long) height;
            if (pixelCount > Integer.MAX_VALUE / CHANNELS) return null;

            byte[] rgba = new byte[(int) pixelCount * CHANNELS];
            int offset = 0;
            for (int y = 0; y < height; y++) {
                for (int x = 0; x < width; x++) {
                    rgba[offset++] = image.getRedOrLuminance(x, y);
                    rgba[offset++] = image.getGreenOrLuminance(x, y);
                    rgba[offset++] = image.getBlueOrLuminance(x, y);
                    rgba[offset++] = image.getLuminanceOrAlpha(x, y);
                }
            }
            return new ImageSnapshot(width, height, rgba);
        } catch (Throwable ignored) {
            return null;
        }
    }

    private static final class ImageSnapshot {
        private final int width;
        private final int height;
        private final byte[] rgba;

        private ImageSnapshot(int width, int height, byte[] rgba) {
            this.width = width;
            this.height = height;
            this.rgba = rgba.clone();
        }

        private boolean sameBits(ImageSnapshot other) {
            return other != null
                    && this.width == other.width
                    && this.height == other.height
                    && Arrays.equals(this.rgba, other.rgba);
        }

        @Nullable
        private float[] sample(int x, int y) {
            if (x < 0 || y < 0 || x >= this.width || y >= this.height) return null;
            int offset = (y * this.width + x) * CHANNELS;
            return new float[]{
                    Byte.toUnsignedInt(this.rgba[offset]) / 255.0F,
                    Byte.toUnsignedInt(this.rgba[offset + 1]) / 255.0F,
                    Byte.toUnsignedInt(this.rgba[offset + 2]) / 255.0F,
                    Byte.toUnsignedInt(this.rgba[offset + 3]) / 255.0F};
        }
    }
}
