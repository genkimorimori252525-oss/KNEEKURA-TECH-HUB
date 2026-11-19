package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexFormat;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import org.joml.Matrix3f;
import org.joml.Matrix4f;

import javax.annotation.Nullable;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

/**
 * Captures the next actual Reimu geoRender invocation as a raw authoritative final-vertex frame.
 *
 * <p>This class never calls render itself. The renderer wraps its real MultiBufferSource with the
 * returned tee for the already-occurring geoRender, then calls {@link #after}. Therefore capture
 * cannot advance YSM animation/controller state by introducing a second render.
 *
 * <p>Raw capture intentionally has no packHash/layoutHash. Those identities belong to a compiled
 * Render Pack and are bound later by the Node normalizer, which fails closed on group/model
 * mismatch before producing RenderFrameIR.
 */
public final class SimFinalVertexCapture {
    public static final String RAW_SCHEMA = "kneekura.runtime-final-vertex-capture";
    public static final int RAW_VERSION = 2;
    public static final String PROP_OUT = "tlm.sim.renderframe.out";

    private static boolean armed;
    private static boolean goldenRequested;
    @Nullable private static UUID targetUuid;
    private static final Map<String, Long> NEXT_SEQUENCE = new LinkedHashMap<>();

    private SimFinalVertexCapture() {}

    /**
     * Arm one capture. The nearest visible Reimu host is fixed now so another maid rendered first
     * cannot steal the request.
     */
    public static String requestNext() {
        return armNearest(false);
    }

    public static String requestNextGolden() {
        if ("unbound".equals(runId())) {
            return "Golden capture には -Dtlm.sim.run=<runId> が必要";
        }
        return armNearest(true);
    }

    private static String armNearest(boolean golden) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return "ワールドに入ってから実行すること";
        }
        EntityMaid target = nearestReimu(mc);
        if (target == null) {
            return "近くに霊夢が居ない";
        }
        if (golden && !SimGoldenFramebufferCapture.arm(target.getUUID())) {
            return "Golden framebuffer capture を arm できない";
        }
        targetUuid = target.getUUID();
        goldenRequested = golden;
        armed = true;
        return golden
                ? "[SIM] golden: 次の同一フレームを entities 前後で記録する。霊夢以外の entity を除去し、一人称で画面内に保つこと (uuid="
                    + targetUuid + ")"
                : "[SIM] renderframe: 次の実描画 1 回を記録する。霊夢を画面内に保つこと (uuid="
                    + targetUuid + ")";
    }

    public static boolean isArmed() {
        return armed;
    }

    static void cancelGoldenArmFromFramebuffer() {
        if (!goldenRequested) {
            return;
        }
        armed = false;
        goldenRequested = false;
        targetUuid = null;
    }

    /**
     * Renderer hook before geoRender.
     *
     * @return tee to pass to geoRender, or null when this invocation is not the armed target.
     */
    @Nullable
    public static SimFinalVertexTeeBuffer before(
            EntityMaid maid,
            MultiBufferSource real,
            PoseStack poseStack) {
        if (!armed || maid == null || real == null || poseStack == null || targetUuid == null) {
            return null;
        }
        if (!targetUuid.equals(maid.getUUID())) {
            return null;
        }
        if (goldenRequested && !SimGoldenFramebufferCapture.isBackgroundReadyFor(targetUuid)) {
            // Golden v1 waits for the AFTER_CUTOUT_BLOCKS background snapshot of this same frame.
            return null;
        }

        Matrix4f modelToWorld = new Matrix4f(poseStack.last().pose());
        Matrix3f modelNormalToWorld = new Matrix3f(poseStack.last().normal());
        float det4 = modelToWorld.determinant();
        float det3 = modelNormalToWorld.determinant();
        if (!Float.isFinite(det4) || !Float.isFinite(det3)
                || Math.abs(det4) < 1.0e-12F || Math.abs(det3) < 1.0e-12F) {
            boolean golden = goldenRequested;
            armed = false;
            goldenRequested = false;
            targetUuid = null;
            if (golden) SimGoldenFramebufferCapture.cancel("Golden: outer PoseStack が特異行列");
            say(ChatFormatting.RED,
                    "[SIM] renderframe: outer PoseStack が特異行列なので記録中止 (fail closed)");
            return null;
        }

        SimGlobalShaderState globalShaderState = SimGlobalShaderState.capture();
        if (globalShaderState == null) {
            boolean golden = goldenRequested;
            armed = false;
            goldenRequested = false;
            targetUuid = null;
            if (golden) SimGoldenFramebufferCapture.cancel(
                    "Golden: global shader state を実測できない");
            say(ChatFormatting.RED,
                    "[SIM] renderframe: RenderSystem global shader state を実測できないので記録中止"
                            + " (fail closed)");
            return null;
        }

        SimAuxiliarySamplerState auxiliarySamplerState = SimAuxiliarySamplerState.capture();
        if (auxiliarySamplerState == null) {
            boolean golden = goldenRequested;
            armed = false;
            goldenRequested = false;
            targetUuid = null;
            if (golden) SimGoldenFramebufferCapture.cancel(
                    "Golden: overlay/lightmap runtime texture を実測できない");
            say(ChatFormatting.RED,
                    "[SIM] renderframe: overlay/lightmap runtime texture を実測できないので記録中止"
                            + " (fail closed)");
            return null;
        }

        Matrix4f positionToModel = new Matrix4f(modelToWorld).invert();
        Matrix3f normalToModel = new Matrix3f(modelNormalToWorld).invert();
        return new SimFinalVertexTeeBuffer(
                real, positionToModel, normalToModel, modelToWorld, modelNormalToWorld,
                globalShaderState, auxiliarySamplerState);
    }

    /** Renderer hook immediately after the same geoRender invocation. */
    @SuppressWarnings({"rawtypes", "unchecked"})
    public static void after(
            EntityMaid maid,
            @Nullable SimFinalVertexTeeBuffer tee,
            float partialTick) {
        if (tee == null) {
            return;
        }
        boolean golden = goldenRequested;
        armed = false;
        goldenRequested = false;
        targetUuid = null;
        boolean handedToGolden = false;

        try {
            if (tee.hasNonContiguousTypeReentry()) {
                say(ChatFormatting.RED,
                        "[SIM] renderframe: RenderType が非連続で再登場したため draw-call 境界を保持できない"
                                + " (fail closed)");
                return;
            }
            SimGlobalShaderState globalAfter = SimGlobalShaderState.capture();
            if (globalAfter == null || !tee.globalShaderState().sameBits(globalAfter)) {
                say(ChatFormatting.RED,
                        "[SIM] renderframe: geoRender 前後で global shader state が変化/観測不能"
                                + " のため記録中止 (fail closed)");
                return;
            }
            SimAuxiliarySamplerState auxiliaryAfter = SimAuxiliarySamplerState.capture();
            if (auxiliaryAfter == null
                    || !tee.auxiliarySamplerState().sameBits(auxiliaryAfter)) {
                say(ChatFormatting.RED,
                        "[SIM] renderframe: geoRender 前後で overlay/lightmap texture が変化/観測不能"
                                + " のため記録中止 (fail closed)");
                return;
            }
            if (!tee.auxiliaryResolutionValid()) {
                say(ChatFormatting.RED,
                        "[SIM] renderframe: overlay/lightmap texel を全頂点で解決できなかった"
                                + " ため記録中止 (fail closed)");
                return;
            }
            if (tee.recorders().isEmpty()) {
                say(ChatFormatting.RED,
                        "[SIM] renderframe: geoRender は完了したが頂点が 0 件だった (fail closed)");
                return;
            }
            Path dir = outputDir().resolve(
                    new SimpleDateFormat("yyyyMMdd-HHmmss-SSS", Locale.ROOT).format(new Date())
                            + "-" + maid.getUUID());
            Files.createDirectories(dir);

            Minecraft mc = Minecraft.getInstance();
            EntityRenderer renderer = mc.getEntityRenderDispatcher().getRenderer(maid);
            JsonArray groups = new JsonArray();
            int order = 0;
            int totalVertices = 0;

            for (Map.Entry<RenderType, SimFinalVertexRecorder> entry : tee.recorders().entrySet()) {
                SimFinalVertexRecorder recorder = entry.getValue();
                if (recorder.isEmpty()) {
                    continue;
                }
                RenderType renderType = entry.getKey();
                float[] vertices = recorder.toArray();
                String file = String.format(Locale.ROOT, "group-%04d.f32le", order);
                writeFloats(dir.resolve(file), vertices);

                JsonObject group = new JsonObject();
                String groupId = String.valueOf(renderType);
                group.addProperty("groupId", groupId);
                group.addProperty("order", order);
                group.addProperty("file", file);
                group.addProperty("strideFloats", SimFinalVertexRecorder.STRIDE);
                group.addProperty("vertexCount", recorder.vertexCount());
                group.addProperty("primitiveMode", primitiveMode(renderType));
                group.addProperty("sourceRenderType", groupId);
                group.addProperty("textureResourceId",
                        SimModelDump.resolveTextureId(maid, renderType, renderer));
                group.add("material", SimRenderTypeMaterialProbe.capture(renderType));
                groups.add(group);

                totalVertices += recorder.vertexCount();
                order++;
            }

            if (groups.size() == 0) {
                say(ChatFormatting.RED,
                        "[SIM] renderframe: 非空 group が無かったのでartifactを書かない");
                deleteTree(dir);
                return;
            }

            String runId = runId();
            JsonObject root = new JsonObject();
            root.addProperty("schema", RAW_SCHEMA);
            root.addProperty("schemaVersion", RAW_VERSION);
            root.addProperty("runId", runId);
            root.addProperty("runBound", !"unbound".equals(runId));
            root.addProperty("entityUuid", maid.getUUID().toString());
            root.addProperty("renderSequence", nextSequence(runId, maid.getUUID()));
            root.addProperty("gameTime", maid.level().getGameTime());
            root.addProperty("partialTick", partialTick);
            root.addProperty("modelId",
                    String.valueOf(BuiltInRegistries.ENTITY_TYPE.getKey(maid.getType())));
            root.addProperty("coordinateSystem", "KNEEKURA_RH_Y_UP_BLOCK");
            root.addProperty("matrixConvention", "JOML_COLUMN_MAJOR_COLUMN_VECTOR");
            root.addProperty("vertexFormat", "KNEEKURA_FINAL_VERTEX_V2");
            root.addProperty("strideFloats", SimFinalVertexRecorder.STRIDE);
            root.addProperty("vertexCount", totalVertices);

            JsonObject source = new JsonObject();
            source.addProperty("type", "runtimeFinalVertex");
            source.addProperty("authority", "authoritative");
            source.addProperty("fidelityTier", 0);
            source.addProperty("capturePoint", "same-geoRender-VertexConsumer-tee");
            source.addProperty("outerPoseNormalization", "inverse-observed-PoseStack");
            source.addProperty("bufferRequestCount", tee.bufferRequestCount());
            source.addProperty(
                    "auxiliarySamplerInputs",
                    "resolved-per-vertex-rgba");
            root.add("source", source);

            JsonArray matrix = new JsonArray();
            for (float value : tee.modelToWorld()) {
                matrix.add(value);
            }
            root.add("modelToWorldMatrix", matrix);

            JsonArray normalMatrix = new JsonArray();
            for (float value : tee.modelNormalToWorld()) {
                normalMatrix.add(value);
            }
            root.add("modelNormalToWorldMatrix", normalMatrix);

            JsonArray color = new JsonArray();
            for (float value : tee.globalColorMultiplier()) {
                color.add(value);
            }
            root.add("globalColorMultiplier", color);
            root.add("globalShaderState", tee.globalShaderState().toJson());
            root.add("auxiliarySamplerEvidence", tee.auxiliarySamplerState().toEvidenceJson());
            root.add("groups", groups);

            if (golden) {
                if (!SimGoldenFramebufferCapture.attachRaw(maid.getUUID(), dir, root)) {
                    deleteTree(dir);
                    say(ChatFormatting.RED,
                            "[SIM] Golden: raw frame と background frame を結合できない (fail closed)");
                    return;
                }
                handedToGolden = true;
                say(ChatFormatting.DARK_GREEN,
                        "[SIM] Golden: raw frame 取得済み。AFTER_ENTITIES framebuffer commit 待ち");
            } else {
                Path json = dir.resolve("capture.json");
                Files.writeString(json, root.toString(), StandardCharsets.UTF_8,
                        StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
                say(ChatFormatting.GREEN,
                        "[SIM] renderframe: authoritative raw frame -> " + json);
            }
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM] renderframe capture failed", t);
            say(ChatFormatting.RED,
                    "[SIM] renderframe 失敗: " + t.getClass().getSimpleName() + ": " + t.getMessage());
        } finally {
            if (golden && !handedToGolden) {
                SimGoldenFramebufferCapture.cancel("Golden: final-vertex raw capture が完了しなかった");
            }
        }
    }

    private static EntityMaid nearestReimu(Minecraft mc) {
        EntityMaid best = null;
        double bestDistance = Double.MAX_VALUE;
        for (net.minecraft.world.entity.Entity entity : mc.level.entitiesForRendering()) {
            if (!(entity instanceof EntityMaid maid) || !maid.isAlive()) {
                continue;
            }
            if (!(maid.isReimuMaid() || maid.isNamedReimu())) {
                continue;
            }
            double distance = mc.player.distanceToSqr(maid);
            if (distance < bestDistance) {
                bestDistance = distance;
                best = maid;
            }
        }
        return best;
    }

    private static String primitiveMode(RenderType type) {
        VertexFormat.Mode found = null;
        for (Class<?> c = type.getClass(); c != null && c != Object.class; c = c.getSuperclass()) {
            for (Field field : c.getDeclaredFields()) {
                if (Modifier.isStatic(field.getModifiers())
                        || field.getType() != VertexFormat.Mode.class) {
                    continue;
                }
                try {
                    field.setAccessible(true);
                    VertexFormat.Mode value = (VertexFormat.Mode) field.get(type);
                    if (value == null) {
                        continue;
                    }
                    if (found != null && found != value) {
                        return "UNKNOWN";
                    }
                    found = value;
                } catch (Throwable ignored) {
                    return "UNKNOWN";
                }
            }
        }
        return found == null ? "UNKNOWN" : found.name();
    }

    private static synchronized long nextSequence(String runId, UUID uuid) {
        String key = runId + "|" + uuid;
        long next = NEXT_SEQUENCE.getOrDefault(key, 0L);
        NEXT_SEQUENCE.put(key, next + 1L);
        return next;
    }

    private static String runId() {
        String raw = System.getProperty("tlm.sim.run");
        return raw == null || raw.isBlank() ? "unbound" : raw.trim();
    }

    private static Path outputDir() {
        String explicit = System.getProperty(PROP_OUT);
        if (explicit != null && !explicit.isBlank()) {
            return Path.of(explicit);
        }
        return Minecraft.getInstance().gameDirectory.toPath()
                .resolve("simlab").resolve("renderframes").resolve("raw");
    }

    private static void writeFloats(Path file, float[] values) throws Exception {
        ByteBuffer buffer = ByteBuffer.allocate(values.length * 4).order(ByteOrder.LITTLE_ENDIAN);
        for (float value : values) {
            buffer.putFloat(value);
        }
        Files.write(file, buffer.array(),
                StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    }

    private static void deleteTree(Path dir) {
        try {
            if (!Files.exists(dir)) return;
            try (var stream = Files.walk(dir)) {
                stream.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                    try { Files.deleteIfExists(path); } catch (Exception ignored) {}
                });
            }
        } catch (Exception ignored) {
        }
    }

    private static void say(ChatFormatting color, String message) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(message).withStyle(color), false);
        }
    }
}