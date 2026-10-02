package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.google.gson.JsonObject;
import net.minecraft.client.renderer.RenderStateShard;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import javax.annotation.Nullable;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.List;

/**
 * RenderType の CompositeState から直接証明できる MaterialIR state だけを取り出す。
 *
 * <p>重要な境界:
 * <ul>
 *   <li>RenderType#toString() は provenance/debug にしか使わない。</li>
 *   <li>標準 state の意味は、dummy texture で生成した Minecraft 標準 RenderType の
 *       shard object identity と比較して校正する。文字列名分類はしない。</li>
 *   <li>WriteMask / TextureState の boolean は constructor 入力を反転した calibration
 *       instance で field の意味を自己校正する。難読化された field 名には依存しない。</li>
 *   <li>custom/ambiguous state は UNKNOWN のまま残す。</li>
 * </ul>
 */
@OnlyIn(Dist.CLIENT)
final class SimRenderTypeMaterialProbe {
    private static final ResourceLocation CALIBRATION_TEXTURE =
            new ResourceLocation("kneekura", "material_probe_calibration");

    private SimRenderTypeMaterialProbe() {}

    static JsonObject capture(@Nullable RenderType type) {
        JsonObject out = unknownMaterial();
        JsonObject evidence = new JsonObject();
        evidence.addProperty(
                "method",
                "CompositeState observation + canonical shard identity + constructor calibration");
        out.add("capture", evidence);

        if (type == null) {
            evidence.addProperty("status", "UNKNOWN");
            evidence.addProperty("reason", "RenderType is null");
            return out;
        }

        // Provenance only. Never branch/classify on this text.
        evidence.addProperty("renderType", String.valueOf(type));
        Object state = findCompositeState(type);
        if (state == null) {
            evidence.addProperty("status", "UNKNOWN");
            evidence.addProperty("reason", "CompositeState-shaped object was not found");
            return out;
        }

        evidence.addProperty("compositeStateClass", state.getClass().getName());
        Shards shards = readShards(state);
        int measured = 0;

        Boolean cull = singleBoolean(shards.cull());
        if (cull != null) {
            out.addProperty("cullMode", cull ? "back" : "none");
            measured++;
        }

        Boolean lightmap = singleBoolean(shards.lightmap());
        if (lightmap != null) {
            out.addProperty("lightmap", lightmap);
            measured++;
        }

        Boolean overlay = singleBoolean(shards.overlay());
        if (overlay != null) {
            out.addProperty("overlay", overlay);
            measured++;
        }

        String depthFunction = depthFunction(shards.depthTest());
        if (depthFunction != null && !depthFunction.isBlank()) {
            out.getAsJsonObject("depth").addProperty("testFunction", depthFunction);
            measured++;
        }

        Boolean depthWrite = calibratedWriteDepth(shards.writeMask());
        if (depthWrite != null) {
            out.getAsJsonObject("depth").addProperty("write", depthWrite);
            measured++;
        }

        SamplerState sampler = calibratedSampler(shards.texture());
        if (sampler != null) {
            JsonObject value = out.getAsJsonObject("sampler");
            value.addProperty("status", "measured");
            value.addProperty("bilinear", sampler.bilinear());
            value.addProperty("mipmap", sampler.mipmap());
            value.addProperty("authority", "TextureStateShard constructor-calibrated");
            measured++;
        }

        BlendState blend = canonicalBlend(shards.transparency());
        if (blend != null) {
            JsonObject value = out.getAsJsonObject("blend");
            value.addProperty("enabled", blend.enabled());
            if (blend.enabled()) {
                value.addProperty("equation", blend.equation());
                value.addProperty("srcFactor", blend.srcFactor());
                value.addProperty("dstFactor", blend.dstFactor());
            }
            evidence.addProperty("blendAuthority", blend.authority());
            measured++;
        }

        ShaderProfile profile = canonicalShaderProfile(shards.shader());
        if (profile != null) {
            out.addProperty("shaderProfile", profile.id());
            out.addProperty("alphaMode", profile.alphaMode());
            if (profile.alphaCutoff() != null) {
                out.addProperty("alphaCutoff", profile.alphaCutoff());
            }
            out.addProperty("emissive", profile.emissive());
            out.addProperty("fullbright", profile.fullbright());
            out.addProperty("fogMode", profile.fogMode());
            out.addProperty("vertexTint", "vertexColor");
            if (profile.replay() != null) {
                out.add("replay", replayJson(profile.replay()));
                measured++;
            }
            evidence.addProperty("shaderProfileAuthority", "canonical ShaderStateShard identity");
            measured += 4;
        }

        addShardEvidence(evidence, "transparencyShard", shards.transparency());
        addShardEvidence(evidence, "writeMaskShard", shards.writeMask());
        addShardEvidence(evidence, "textureShard", shards.texture());
        addShardEvidence(evidence, "shaderShard", shards.shader());

        String status = measured == 0 ? "provenance-only" : "partial-measured";
        if (replayCriticalKnown(out)) {
            status = "replay-critical-measured";
        }
        evidence.addProperty("status", status);
        out.addProperty("captureStatus", status);
        return out;
    }

    private static boolean replayCriticalKnown(JsonObject out) {
        if ("UNKNOWN".equals(out.get("alphaMode").getAsString())) return false;
        if ("UNKNOWN".equals(out.get("cullMode").getAsString())) return false;
        JsonObject depth = out.getAsJsonObject("depth");
        if ("UNKNOWN".equals(depth.get("testFunction").getAsString())) return false;
        if (!depth.get("write").isJsonPrimitive()
                || !depth.get("write").getAsJsonPrimitive().isBoolean()) return false;
        JsonObject blend = out.getAsJsonObject("blend");
        if (!blend.get("enabled").isJsonPrimitive()
                || !blend.get("enabled").getAsJsonPrimitive().isBoolean()) return false;
        if (blend.get("enabled").getAsBoolean()) {
            for (String key : new String[]{"equation", "srcFactor", "dstFactor"}) {
                if ("UNKNOWN".equals(blend.get(key).getAsString())) return false;
            }
        }
        JsonObject sampler = out.getAsJsonObject("sampler");
        JsonObject replay = out.getAsJsonObject("replay");
        return replay != null
                && "measured".equals(replay.get("status").getAsString())
                && !"UNKNOWN".equals(sampler.get("status").getAsString())
                && out.get("emissive").isJsonPrimitive()
                && out.get("emissive").getAsJsonPrimitive().isBoolean()
                && out.get("fullbright").isJsonPrimitive()
                && out.get("fullbright").getAsJsonPrimitive().isBoolean()
                && !"UNKNOWN".equals(out.get("fogMode").getAsString())
                && !"UNKNOWN".equals(out.get("vertexTint").getAsString())
                && out.get("lightmap").isJsonPrimitive()
                && out.get("lightmap").getAsJsonPrimitive().isBoolean()
                && out.get("overlay").isJsonPrimitive()
                && out.get("overlay").getAsJsonPrimitive().isBoolean();
    }

    private static JsonObject unknownMaterial() {
        JsonObject out = new JsonObject();
        out.addProperty("alphaMode", "UNKNOWN");

        JsonObject blend = new JsonObject();
        blend.addProperty("enabled", "UNKNOWN");
        blend.addProperty("equation", "UNKNOWN");
        blend.addProperty("srcFactor", "UNKNOWN");
        blend.addProperty("dstFactor", "UNKNOWN");
        out.add("blend", blend);

        out.addProperty("cullMode", "UNKNOWN");

        JsonObject depth = new JsonObject();
        depth.addProperty("testFunction", "UNKNOWN");
        depth.addProperty("write", "UNKNOWN");
        out.add("depth", depth);

        out.addProperty("emissive", "UNKNOWN");
        out.addProperty("fullbright", "UNKNOWN");
        out.addProperty("fogMode", "UNKNOWN");

        JsonObject sampler = new JsonObject();
        sampler.addProperty("status", "UNKNOWN");
        out.add("sampler", sampler);

        out.addProperty("vertexTint", "UNKNOWN");
        out.addProperty("lightmap", "UNKNOWN");
        out.addProperty("overlay", "UNKNOWN");

        JsonObject replay = new JsonObject();
        replay.addProperty("status", "UNKNOWN");
        out.add("replay", replay);

        out.addProperty("captureStatus", "provenance-only");
        return out;
    }

    @Nullable
    private static Object findCompositeState(RenderType type) {
        for (Field f : allFields(type.getClass())) {
            if (Modifier.isStatic(f.getModifiers())) continue;
            Object value = read(f, type);
            if (value != null && countKnownShards(value) >= 4) return value;
        }
        return null;
    }

    private static int countKnownShards(Object owner) {
        int count = 0;
        for (Field f : allFields(owner.getClass())) {
            if (Modifier.isStatic(f.getModifiers())) continue;
            Object value = read(f, owner);
            if (isKnownShard(value)) count++;
        }
        return count;
    }

    private static boolean isKnownShard(@Nullable Object value) {
        return value instanceof RenderStateShard.CullStateShard
                || value instanceof RenderStateShard.LightmapStateShard
                || value instanceof RenderStateShard.OverlayStateShard
                || value instanceof RenderStateShard.DepthTestStateShard
                || value instanceof RenderStateShard.TransparencyStateShard
                || value instanceof RenderStateShard.WriteMaskStateShard
                || value instanceof RenderStateShard.EmptyTextureStateShard
                || value instanceof RenderStateShard.ShaderStateShard;
    }

    private record Shards(
            @Nullable RenderStateShard.CullStateShard cull,
            @Nullable RenderStateShard.LightmapStateShard lightmap,
            @Nullable RenderStateShard.OverlayStateShard overlay,
            @Nullable RenderStateShard.DepthTestStateShard depthTest,
            @Nullable RenderStateShard.TransparencyStateShard transparency,
            @Nullable RenderStateShard.WriteMaskStateShard writeMask,
            @Nullable RenderStateShard.EmptyTextureStateShard texture,
            @Nullable RenderStateShard.ShaderStateShard shader) {}

    private static Shards readShards(Object state) {
        RenderStateShard.CullStateShard cull = null;
        RenderStateShard.LightmapStateShard lightmap = null;
        RenderStateShard.OverlayStateShard overlay = null;
        RenderStateShard.DepthTestStateShard depth = null;
        RenderStateShard.TransparencyStateShard transparency = null;
        RenderStateShard.WriteMaskStateShard writeMask = null;
        RenderStateShard.EmptyTextureStateShard texture = null;
        RenderStateShard.ShaderStateShard shader = null;

        for (Field f : allFields(state.getClass())) {
            if (Modifier.isStatic(f.getModifiers())) continue;
            Object value = read(f, state);
            if (value instanceof RenderStateShard.CullStateShard x) cull = x;
            else if (value instanceof RenderStateShard.LightmapStateShard x) lightmap = x;
            else if (value instanceof RenderStateShard.OverlayStateShard x) overlay = x;
            else if (value instanceof RenderStateShard.DepthTestStateShard x) depth = x;
            else if (value instanceof RenderStateShard.TransparencyStateShard x) transparency = x;
            else if (value instanceof RenderStateShard.WriteMaskStateShard x) writeMask = x;
            else if (value instanceof RenderStateShard.EmptyTextureStateShard x) texture = x;
            else if (value instanceof RenderStateShard.ShaderStateShard x) shader = x;
        }
        return new Shards(cull, lightmap, overlay, depth, transparency, writeMask, texture, shader);
    }

    @Nullable
    private static Boolean singleBoolean(@Nullable Object shard) {
        if (shard == null) return null;
        List<Boolean> values = new ArrayList<>();
        for (Field f : booleanFields(shard.getClass())) {
            try {
                values.add(f.getBoolean(shard));
            } catch (Throwable ignored) {
                return null;
            }
        }
        return values.size() == 1 ? values.get(0) : null;
    }

    @Nullable
    private static String depthFunction(@Nullable RenderStateShard.DepthTestStateShard shard) {
        if (shard == null) return null;
        List<String> values = new ArrayList<>();
        for (Field f : RenderStateShard.DepthTestStateShard.class.getDeclaredFields()) {
            if (Modifier.isStatic(f.getModifiers()) || f.getType() != String.class) continue;
            Object value = read(f, shard);
            if (value instanceof String s) values.add(s);
        }
        return values.size() == 1 ? values.get(0) : null;
    }

    @Nullable
    private static Boolean calibratedWriteDepth(@Nullable RenderStateShard.WriteMaskStateShard shard) {
        if (shard == null) return null;
        try {
            RenderStateShard.WriteMaskStateShard a =
                    new RenderStateShard.WriteMaskStateShard(false, true);
            RenderStateShard.WriteMaskStateShard b =
                    new RenderStateShard.WriteMaskStateShard(true, false);
            Field depthField = calibratedBooleanField(a, b, true, false);
            return depthField == null ? null : depthField.getBoolean(shard);
        } catch (Throwable ignored) {
            return null;
        }
    }

    private record SamplerState(boolean bilinear, boolean mipmap) {}

    @Nullable
    private static SamplerState calibratedSampler(
            @Nullable RenderStateShard.EmptyTextureStateShard shard) {
        if (!(shard instanceof RenderStateShard.TextureStateShard texture)) return null;
        try {
            RenderStateShard.TextureStateShard a =
                    new RenderStateShard.TextureStateShard(CALIBRATION_TEXTURE, true, false);
            RenderStateShard.TextureStateShard b =
                    new RenderStateShard.TextureStateShard(CALIBRATION_TEXTURE, false, true);
            Field bilinear = calibratedBooleanField(a, b, true, false);
            Field mipmap = calibratedBooleanField(a, b, false, true);
            if (bilinear == null || mipmap == null || bilinear.equals(mipmap)) return null;
            return new SamplerState(
                    bilinear.getBoolean(texture),
                    mipmap.getBoolean(texture));
        } catch (Throwable ignored) {
            return null;
        }
    }

    @Nullable
    private static Field calibratedBooleanField(
            Object a,
            Object b,
            boolean expectedA,
            boolean expectedB) {
        Field found = null;
        for (Field f : booleanFields(a.getClass())) {
            try {
                if (f.getBoolean(a) != expectedA || f.getBoolean(b) != expectedB) continue;
                if (found != null) return null;
                found = f;
            } catch (Throwable ignored) {
                return null;
            }
        }
        return found;
    }

    private record BlendState(
            boolean enabled,
            String equation,
            String srcFactor,
            String dstFactor,
            String authority) {}

    @Nullable
    private static BlendState canonicalBlend(
            @Nullable RenderStateShard.TransparencyStateShard actual) {
        if (actual == null) return null;
        Canonical c = Canonical.INSTANCE;
        if (actual == c.noTransparency) {
            return new BlendState(false, "UNKNOWN", "UNKNOWN", "UNKNOWN",
                    "canonical NO_TRANSPARENCY shard identity");
        }
        if (actual == c.translucentTransparency) {
            return new BlendState(true, "add", "srcAlpha", "oneMinusSrcAlpha",
                    "canonical TRANSLUCENT_TRANSPARENCY shard identity");
        }
        if (actual == c.additiveTransparency) {
            return new BlendState(true, "add", "one", "one",
                    "canonical ADDITIVE_TRANSPARENCY shard identity");
        }
        return null;
    }

    private record ReplayProfile(
            String vertexLightingMode,
            float lightingPower,
            float ambientLight,
            float lightingClampMax,
            String fogDistance,
            String textureCombine,
            String alphaDiscardSource,
            String overlayCombine,
            String lightmapCombine) {}

    private record ShaderProfile(
            String id,
            RenderStateShard.ShaderStateShard shader,
            String alphaMode,
            @Nullable Float alphaCutoff,
            boolean emissive,
            boolean fullbright,
            String fogMode,
            @Nullable ReplayProfile replay) {}

    private static JsonObject replayJson(ReplayProfile profile) {
        JsonObject out = new JsonObject();
        out.addProperty("status", "measured");
        JsonObject lighting = new JsonObject();
        lighting.addProperty("mode", profile.vertexLightingMode());
        lighting.addProperty("power", profile.lightingPower());
        lighting.addProperty("ambient", profile.ambientLight());
        lighting.addProperty("clampMax", profile.lightingClampMax());
        out.add("vertexLighting", lighting);
        out.addProperty("fogDistance", profile.fogDistance());
        out.addProperty("textureCombine", profile.textureCombine());
        out.addProperty("alphaDiscardSource", profile.alphaDiscardSource());
        out.addProperty("overlayCombine", profile.overlayCombine());
        out.addProperty("lightmapCombine", profile.lightmapCombine());
        return out;
    }

    private static ReplayProfile standardEntityReplay(String alphaDiscardSource) {
        return new ReplayProfile(
                "dualDirectionalDiffuse", 0.6F, 0.4F, 1.0F,
                "modelViewInverseViewRotationShape",
                "sample0TimesVertexTimesShaderColor",
                alphaDiscardSource,
                "rgbMixByOverlayAlpha",
                "multiplyRgba");
    }

    private static ReplayProfile emissiveEntityReplay() {
        return new ReplayProfile(
                "dualDirectionalDiffuse", 0.6F, 0.4F, 1.0F,
                "modelViewLength",
                "sample0TimesVertexTimesShaderColor",
                "sampler0Alpha",
                "rgbMixByOverlayAlpha",
                "none");
    }

    @Nullable
    private static ShaderProfile canonicalShaderProfile(
            @Nullable RenderStateShard.ShaderStateShard actual) {
        if (actual == null) return null;
        for (ShaderProfile profile : Canonical.INSTANCE.shaderProfiles) {
            if (actual == profile.shader()) return profile;
        }
        return null;
    }

    /**
     * Standard-state calibration is intentionally based on public RenderType factories and shard
     * object identity, never on RenderType/String or shader-name classification.
     */
    private static final class Canonical {
        static final Canonical INSTANCE = new Canonical();

        final RenderStateShard.TransparencyStateShard noTransparency;
        final RenderStateShard.TransparencyStateShard translucentTransparency;
        final RenderStateShard.TransparencyStateShard additiveTransparency;
        final List<ShaderProfile> shaderProfiles;

        private Canonical() {
            Shards solid = canonical(RenderType.entitySolid(CALIBRATION_TEXTURE));
            Shards cutout = canonical(RenderType.entityCutout(CALIBRATION_TEXTURE));
            Shards cutoutNoCull = canonical(RenderType.entityCutoutNoCull(CALIBRATION_TEXTURE));
            Shards cutoutNoCullZ =
                    canonical(RenderType.entityCutoutNoCullZOffset(CALIBRATION_TEXTURE));
            Shards smoothCutout = canonical(RenderType.entitySmoothCutout(CALIBRATION_TEXTURE));
            Shards translucent = canonical(RenderType.entityTranslucent(CALIBRATION_TEXTURE));
            Shards translucentCull =
                    canonical(RenderType.entityTranslucentCull(CALIBRATION_TEXTURE));
            Shards translucentEmissive =
                    canonical(RenderType.entityTranslucentEmissive(CALIBRATION_TEXTURE));
            Shards eyes = canonical(RenderType.eyes(CALIBRATION_TEXTURE));

            this.noTransparency = require(solid.transparency(), "solid transparency");
            this.translucentTransparency =
                    require(translucent.transparency(), "translucent transparency");
            this.additiveTransparency = require(eyes.transparency(), "eyes transparency");

            List<ShaderProfile> profiles = new ArrayList<>();
            ReplayProfile opaqueReplay = standardEntityReplay("none");
            ReplayProfile alphaReplay = standardEntityReplay("sampler0Alpha");
            ReplayProfile emissiveReplay = emissiveEntityReplay();
            addProfile(profiles, "minecraft:entity_solid_1_20_1", solid,
                    "opaque", null, false, false, "colorMixPreserveAlpha", opaqueReplay);
            addProfile(profiles, "minecraft:entity_cutout_1_20_1", cutout,
                    "mask", 0.1F, false, false, "colorMixPreserveAlpha", alphaReplay);
            addProfile(profiles, "minecraft:entity_cutout_no_cull_1_20_1", cutoutNoCull,
                    "mask", 0.1F, false, false, "colorMixPreserveAlpha", alphaReplay);
            addProfile(profiles, "minecraft:entity_cutout_no_cull_z_offset_1_20_1", cutoutNoCullZ,
                    "mask", 0.1F, false, false, "colorMixPreserveAlpha", alphaReplay);
            addProfile(profiles, "minecraft:entity_smooth_cutout_1_20_1", smoothCutout,
                    "mask", 0.1F, false, false, "colorMixPreserveAlpha", alphaReplay);
            addProfile(profiles, "minecraft:entity_translucent_1_20_1", translucent,
                    "blend", 0.1F, false, false, "colorMixPreserveAlpha", alphaReplay);
            addProfile(profiles, "minecraft:entity_translucent_cull_1_20_1", translucentCull,
                    "blend", 0.1F, false, false, "colorMixPreserveAlpha", alphaReplay);
            addProfile(profiles, "minecraft:entity_translucent_emissive_1_20_1",
                    translucentEmissive, "blend", 0.1F, true, true, "rgbaFade", emissiveReplay);
            // Keep this profile provenance-only until its exact 1.20.1 vertex replay is pinned.
            addProfile(profiles, "minecraft:eyes_1_20_1", eyes,
                    "blend", null, true, true, "rgbaFade", null);
            this.shaderProfiles = List.copyOf(profiles);
        }

        private static Shards canonical(RenderType type) {
            Object state = findCompositeState(type);
            if (state == null) {
                throw new IllegalStateException("canonical RenderType has no CompositeState");
            }
            return readShards(state);
        }

        private static void addProfile(
                List<ShaderProfile> out,
                String id,
                Shards shards,
                String alphaMode,
                @Nullable Float alphaCutoff,
                boolean emissive,
                boolean fullbright,
                String fogMode,
                @Nullable ReplayProfile replay) {
            RenderStateShard.ShaderStateShard shader =
                    require(shards.shader(), id + " shader");
            out.add(new ShaderProfile(
                    id, shader, alphaMode, alphaCutoff, emissive, fullbright, fogMode, replay));
        }

        private static <T> T require(@Nullable T value, String label) {
            if (value == null) throw new IllegalStateException("missing canonical " + label);
            return value;
        }
    }

    private static void addShardEvidence(
            JsonObject evidence,
            String key,
            @Nullable Object shard) {
        if (shard == null) return;
        JsonObject value = new JsonObject();
        value.addProperty("class", shard.getClass().getName());
        String name = shardName(shard);
        if (name != null) value.addProperty("name", name);
        evidence.add(key, value);
    }

    @Nullable
    private static String shardName(Object shard) {
        List<String> values = new ArrayList<>();
        for (Field f : RenderStateShard.class.getDeclaredFields()) {
            if (Modifier.isStatic(f.getModifiers()) || f.getType() != String.class) continue;
            Object value = read(f, shard);
            if (value instanceof String s) values.add(s);
        }
        return values.size() == 1 ? values.get(0) : null;
    }

    private static List<Field> booleanFields(Class<?> type) {
        List<Field> fields = new ArrayList<>();
        for (Field f : allFields(type)) {
            if (!Modifier.isStatic(f.getModifiers()) && f.getType() == boolean.class) {
                fields.add(f);
            }
        }
        return fields;
    }

    private static List<Field> allFields(Class<?> type) {
        List<Field> fields = new ArrayList<>();
        for (Class<?> c = type; c != null && c != Object.class; c = c.getSuperclass()) {
            for (Field f : c.getDeclaredFields()) {
                if (Modifier.isStatic(f.getModifiers())) continue;
                try {
                    f.setAccessible(true);
                    fields.add(f);
                } catch (Throwable ignored) {
                    // inaccessible fields are omitted; callers leave the value UNKNOWN
                }
            }
        }
        return fields;
    }

    @Nullable
    private static Object read(Field field, Object owner) {
        try {
            field.setAccessible(true);
            return field.get(owner);
        } catch (Throwable ignored) {
            return null;
        }
    }
}