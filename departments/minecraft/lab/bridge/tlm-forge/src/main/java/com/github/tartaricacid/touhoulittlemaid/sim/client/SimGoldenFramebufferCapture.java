package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Camera;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.joml.Matrix4f;
import org.joml.Quaternionf;

import javax.annotation.Nullable;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Comparator;
import java.util.UUID;

/**
 * Same-frame Golden Oracle framebuffer capture.
 *
 * <p>The real YSM renderer is never invoked here. The state machine captures the main render target
 * at two Forge render stages around normal entity rendering:
 *
 * <ul>
 *   <li>AFTER_CUTOUT_BLOCKS: background-before-entities.png</li>
 *   <li>AFTER_ENTITIES: golden-after-entities.png</li>
 * </ul>
 *
 * <p>The matching final-vertex raw frame is attached by {@link SimFinalVertexCapture#after}. Only
 * after both screenshots and the raw frame belong to the same render tick/camera contract is
 * capture.json committed. This keeps GUI, particles, weather and later level stages outside the
 * comparison target without forcing or repeating a YSM render.
 */
@Mod.EventBusSubscriber(
        modid = TouhouLittleMaid.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.FORGE,
        value = Dist.CLIENT)
public final class SimGoldenFramebufferCapture {
    public static final String SCHEMA = "kneekura.real-client-golden-capture";
    public static final int VERSION = 2;
    private static final String BACKGROUND_FILE = "background-before-entities.png";
    private static final String BACKGROUND_DEPTH_FILE = "background-before-entities.depth-f32le";
    private static final String GOLDEN_FILE = "golden-after-entities.png";

    private enum Phase {
        IDLE,
        ARMED,
        BACKGROUND_READY,
        RAW_READY
    }

    private static Phase phase = Phase.IDLE;
    @Nullable private static UUID targetUuid;
    @Nullable private static NativeImage backgroundBefore;
    @Nullable private static byte[] backgroundDepth;
    @Nullable private static CameraContract beforeContract;
    @Nullable private static Path rawDir;
    @Nullable private static JsonObject rawRoot;
    private static boolean dispatcherSuppressed;
    private static boolean previousHitBoxes;
    private static boolean restoreEntityShadows;

    private SimGoldenFramebufferCapture() {}

    public static synchronized boolean arm(UUID target) {
        if (target == null) {
            return false;
        }
        reset(false);
        targetUuid = target;
        phase = Phase.ARMED;
        return true;
    }

    public static synchronized boolean isBackgroundReadyFor(UUID target) {
        return phase == Phase.BACKGROUND_READY
                && targetUuid != null
                && targetUuid.equals(target)
                && backgroundBefore != null
                && backgroundDepth != null
                && beforeContract != null;
    }

    /**
     * Called after the exact YSM geoRender has produced final-vertex raw evidence.
     * The JSON file itself is deliberately not written yet; AFTER_ENTITIES must still prove the
     * matching framebuffer/camera contract.
     */
    public static synchronized boolean attachRaw(UUID target, Path dir, JsonObject root) {
        if (!isBackgroundReadyFor(target) || dir == null || root == null) {
            return false;
        }
        rawDir = dir;
        rawRoot = root;
        phase = Phase.RAW_READY;
        return true;
    }

    public static synchronized void cancel(String reason) {
        fail(reason, true);
    }

    @SubscribeEvent
    public static void onRenderStage(RenderLevelStageEvent event) {
        if (event.getStage() == RenderLevelStageEvent.Stage.AFTER_CUTOUT_BLOCKS) {
            captureBackground(event);
        } else if (event.getStage() == RenderLevelStageEvent.Stage.AFTER_ENTITIES) {
            captureGolden(event);
        }
    }

    private static synchronized void captureBackground(RenderLevelStageEvent event) {
        if (phase != Phase.ARMED || targetUuid == null) {
            return;
        }

        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            fail("Golden: world/player が無いので中止", false);
            return;
        }
        if (mc.options.getCameraType() != CameraType.FIRST_PERSON) {
            fail("Golden: v1 は一人称カメラのみ対応 (player 自身の描画混入を防ぐ)", false);
            return;
        }
        if (hasOtherRenderableEntity(mc, targetUuid)) {
            fail("Golden: 対象霊夢以外の renderable entity が存在するため中止", false);
            return;
        }
        EntityMaid target = findTargetMaid(mc, targetUuid);
        if (target == null) {
            fail("Golden: 対象霊夢を renderable entity として再取得できない", false);
            return;
        }
        if (!isYsmOnlyFallbackSafe(target)) {
            fail("Golden: chat bubble または追加描画が生存中/判定不能", false);
            return;
        }
        if (target.displayFireAnimation()) {
            fail("Golden: dispatcher fire overlay が描画対象なので不可", false);
            return;
        }
        if (mc.shouldEntityAppearGlowing(target)) {
            fail("Golden: Minecraft が glowing outline 対象と判定したため不可", false);
            return;
        }
        suppressDispatcherExtras(mc);

        CameraContract contract = CameraContract.capture(event);
        if (contract == null) {
            fail("Golden: camera/projection contract を観測できないため中止", false);
            return;
        }

        NativeImage image = null;
        try {
            byte[] depth = captureBackgroundDepth(mc, contract.framebufferWidth, contract.framebufferHeight);
            if (depth == null) {
                fail("Golden: background depth buffer を取得できないため中止", false);
                return;
            }
            image = Screenshot.takeScreenshot(mc.getMainRenderTarget());
            if (image == null || image.getWidth() <= 0 || image.getHeight() <= 0) {
                if (image != null) image.close();
                fail("Golden: background framebuffer を取得できないため中止", false);
                return;
            }
            if (contract.framebufferWidth != image.getWidth()
                    || contract.framebufferHeight != image.getHeight()) {
                image.close();
                fail("Golden: screenshot と main render target の寸法が一致しない", false);
                return;
            }
            backgroundBefore = image;
            backgroundDepth = depth;
            beforeContract = contract;
            phase = Phase.BACKGROUND_READY;
        } catch (Throwable t) {
            if (image != null) {
                try { image.close(); } catch (Throwable ignored) {}
            }
            TouhouLittleMaid.LOGGER.error("[SIM] Golden background capture failed", t);
            fail("Golden: background capture 失敗: " + t.getClass().getSimpleName(), false);
        }
    }

    private static synchronized void captureGolden(RenderLevelStageEvent event) {
        if (phase == Phase.IDLE || phase == Phase.ARMED) {
            return;
        }
        if (phase == Phase.BACKGROUND_READY) {
            fail("Golden: 同一フレームで対象霊夢の YSM geoRender が観測されなかった", false);
            return;
        }
        if (phase != Phase.RAW_READY
                || targetUuid == null
                || backgroundBefore == null
                || backgroundDepth == null
                || beforeContract == null
                || rawDir == null
                || rawRoot == null) {
            fail("Golden: internal state 不整合", true);
            return;
        }

        CameraContract afterContract = CameraContract.capture(event);
        if (afterContract == null || !beforeContract.sameFrameContract(afterContract)) {
            fail("Golden: entities 前後で camera/projection/framebuffer contract が変化した", true);
            return;
        }

        Minecraft mc = Minecraft.getInstance();
        NativeImage goldenAfter = null;
        try {
            goldenAfter = Screenshot.takeScreenshot(mc.getMainRenderTarget());
            if (goldenAfter == null
                    || goldenAfter.getWidth() != backgroundBefore.getWidth()
                    || goldenAfter.getHeight() != backgroundBefore.getHeight()) {
                fail("Golden: entities 後 framebuffer の寸法が一致しない", true);
                return;
            }

            Files.createDirectories(rawDir);
            backgroundBefore.writeToFile(rawDir.resolve(BACKGROUND_FILE));
            Files.write(rawDir.resolve(BACKGROUND_DEPTH_FILE), backgroundDepth,
                    StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
            goldenAfter.writeToFile(rawDir.resolve(GOLDEN_FILE));

            JsonObject golden = new JsonObject();
            golden.addProperty("schema", SCHEMA);
            golden.addProperty("schemaVersion", VERSION);
            golden.addProperty("backgroundFile", BACKGROUND_FILE);
            golden.addProperty("backgroundDepthFile", BACKGROUND_DEPTH_FILE);
            golden.addProperty("goldenFile", GOLDEN_FILE);
            JsonObject depthEvidence = new JsonObject();
            depthEvidence.addProperty("encoding", "FLOAT32_LE");
            depthEvidence.addProperty("origin", "bottom-left");
            depthEvidence.addProperty("range", "OPENGL_DEPTH_0_1");
            depthEvidence.addProperty("width", beforeContract.framebufferWidth);
            depthEvidence.addProperty("height", beforeContract.framebufferHeight);
            golden.add("backgroundDepth", depthEvidence);
            golden.addProperty("preStage", "AFTER_CUTOUT_BLOCKS");
            golden.addProperty("postStage", "AFTER_ENTITIES");
            golden.addProperty("scope", "main-render-target-before-vs-after-entity-stage");
            golden.addProperty("targetEntityUuid", targetUuid.toString());
            golden.addProperty("requiresIsolatedEntityScene", true);
            golden.addProperty("requiresYsmOnlyFallbackInactive", true);
            golden.addProperty("preYsmChatBubbleIncluded", false);
            golden.addProperty("postYsmFallbackEffectsIncluded", false);
            golden.addProperty("dispatcherShadowSuppressed", true);
            golden.addProperty("dispatcherHitboxSuppressed", true);
            golden.addProperty("dispatcherFireOverlayIncluded", false);
            golden.addProperty("glowingOutlineIncluded", false);
            golden.addProperty("guiIncluded", false);
            golden.addProperty("particlesIncluded", false);
            golden.addProperty("weatherIncluded", false);
            golden.addProperty("viewerComposition",
                    "draw matching RenderFrameIR over background-before-entities.png");
            golden.add("camera", beforeContract.toJson());
            rawRoot.add("golden", golden);

            Path json = rawDir.resolve("capture.json");
            Files.writeString(json, rawRoot.toString(), StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);

            say(ChatFormatting.GREEN,
                    "[SIM] Golden: 同一フレーム実機証拠 -> " + json);
            reset(false);
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM] Golden framebuffer capture failed", t);
            fail("Golden: framebuffer commit 失敗: " + t.getClass().getSimpleName(), true);
        } finally {
            if (goldenAfter != null) {
                try { goldenAfter.close(); } catch (Throwable ignored) {}
            }
        }
    }

    @Nullable
    private static byte[] captureBackgroundDepth(Minecraft mc, int width, int height) {
        try {
            if (width <= 0 || height <= 0) return null;
            int count = Math.multiplyExact(width, height);
            int byteCount = Math.multiplyExact(count, Float.BYTES);
            mc.getMainRenderTarget().bindWrite(false);
            while (org.lwjgl.opengl.GL11.glGetError() != org.lwjgl.opengl.GL11.GL_NO_ERROR) {}
            ByteBuffer nativeBytes = ByteBuffer.allocateDirect(byteCount).order(ByteOrder.nativeOrder());
            FloatBuffer values = nativeBytes.asFloatBuffer();
            org.lwjgl.opengl.GL11.glReadPixels(0, 0, width, height,
                    org.lwjgl.opengl.GL11.GL_DEPTH_COMPONENT, org.lwjgl.opengl.GL11.GL_FLOAT, values);
            if (org.lwjgl.opengl.GL11.glGetError() != org.lwjgl.opengl.GL11.GL_NO_ERROR) return null;
            ByteBuffer out = ByteBuffer.allocate(byteCount).order(ByteOrder.LITTLE_ENDIAN);
            for (int i = 0; i < count; i++) {
                float value = values.get(i);
                if (!Float.isFinite(value) || value < 0.0F || value > 1.0F) return null;
                out.putFloat(value);
            }
            return out.array();
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM] Golden background depth capture failed", t);
            return null;
        }
    }
    private static void suppressDispatcherExtras(Minecraft mc) {
        if (dispatcherSuppressed) {
            return;
        }
        var dispatcher = mc.getEntityRenderDispatcher();
        previousHitBoxes = dispatcher.shouldRenderHitBoxes();
        restoreEntityShadows = mc.options.entityShadows().get();
        dispatcher.setRenderHitBoxes(false);
        dispatcher.setRenderShadow(false);
        dispatcherSuppressed = true;
    }

    private static void restoreDispatcherExtras() {
        if (!dispatcherSuppressed) {
            return;
        }
        try {
            Minecraft mc = Minecraft.getInstance();
            var dispatcher = mc.getEntityRenderDispatcher();
            dispatcher.setRenderHitBoxes(previousHitBoxes);
            dispatcher.setRenderShadow(restoreEntityShadows);
        } catch (Throwable ignored) {
            // A client teardown can race cleanup; next normal render re-applies option state.
        } finally {
            dispatcherSuppressed = false;
            previousHitBoxes = false;
            restoreEntityShadows = false;
        }
    }

    @Nullable
    private static EntityMaid findTargetMaid(Minecraft mc, UUID target) {
        for (Entity entity : mc.level.entitiesForRendering()) {
            if (entity instanceof EntityMaid maid
                    && maid.isAlive()
                    && maid.getUUID().equals(target)) {
                return maid;
            }
        }
        return null;
    }

    /**
     * Ask reimu-mod for exact side-effect-free fallback-effect state. Absence of the bridge method
     * is UNKNOWN and therefore false: Golden evidence must never guess that extra pixels are idle.
     */
    private static boolean isYsmOnlyFallbackSafe(EntityMaid maid) {
        try {
            Class<?> bridge = Class.forName(
                    "com.github.tartaricacid.touhoulittlemaid.mixin.sim.SimRenderFrameProbeBridge",
                    false,
                    SimGoldenFramebufferCapture.class.getClassLoader());
            Object value = bridge.getMethod("goldenYsmOnlySafe", EntityMaid.class)
                    .invoke(null, maid);
            return Boolean.TRUE.equals(value);
        } catch (Throwable ignored) {
            return false;
        }
    }

    private static boolean hasOtherRenderableEntity(Minecraft mc, UUID target) {
        for (Entity entity : mc.level.entitiesForRendering()) {
            if (entity == null || !entity.isAlive()) {
                continue;
            }
            if (entity.getUUID().equals(target)) {
                continue;
            }
            if (entity == mc.player) {
                continue;
            }
            return true;
        }
        return false;
    }

    private static void fail(String reason, boolean deleteRaw) {
        Path doomed = deleteRaw ? rawDir : null;
        SimFinalVertexCapture.cancelGoldenArmFromFramebuffer();
        say(ChatFormatting.RED, "[SIM] " + reason + " (fail closed)");
        reset(false);
        if (doomed != null) {
            deleteTree(doomed);
        }
    }

    private static void reset(boolean deleteRaw) {
        Path doomed = deleteRaw ? rawDir : null;
        restoreDispatcherExtras();
        if (backgroundBefore != null) {
            try { backgroundBefore.close(); } catch (Throwable ignored) {}
        }
        phase = Phase.IDLE;
        targetUuid = null;
        backgroundBefore = null;
        backgroundDepth = null;
        beforeContract = null;
        rawDir = null;
        rawRoot = null;
        if (doomed != null) {
            deleteTree(doomed);
        }
    }

    private static void deleteTree(Path dir) {
        try {
            if (!Files.exists(dir)) return;
            try (var stream = Files.walk(dir)) {
                stream.sorted(Comparator.reverseOrder()).forEach(path -> {
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

    private record CameraContract(
            int renderTick,
            float partialTick,
            int framebufferWidth,
            int framebufferHeight,
            int viewportWidth,
            int viewportHeight,
            int windowWidth,
            int windowHeight,
            int guiScaledWidth,
            int guiScaledHeight,
            double cameraX,
            double cameraY,
            double cameraZ,
            float cameraXRot,
            float cameraYRot,
            float quaternionX,
            float quaternionY,
            float quaternionZ,
            float quaternionW,
            float[] projectionMatrix) {

        @Nullable
        static CameraContract capture(RenderLevelStageEvent event) {
            try {
                Minecraft mc = Minecraft.getInstance();
                Camera camera = event.getCamera();
                if (camera == null || !camera.isInitialized()) {
                    return null;
                }
                Matrix4f projection = new Matrix4f(event.getProjectionMatrix());
                float det = projection.determinant();
                if (!Float.isFinite(det) || Math.abs(det) < 1.0e-12F) {
                    return null;
                }
                float[] projectionValues = new float[16];
                projection.get(projectionValues);

                Vec3 pos = camera.getPosition();
                Quaternionf rotation = new Quaternionf(camera.rotation());
                if (!finite(pos.x) || !finite(pos.y) || !finite(pos.z)
                        || !Float.isFinite(camera.getXRot())
                        || !Float.isFinite(camera.getYRot())
                        || !Float.isFinite(rotation.x())
                        || !Float.isFinite(rotation.y())
                        || !Float.isFinite(rotation.z())
                        || !Float.isFinite(rotation.w())) {
                    return null;
                }

                var target = mc.getMainRenderTarget();
                if (target.width <= 0 || target.height <= 0
                        || target.viewWidth <= 0 || target.viewHeight <= 0) {
                    return null;
                }

                return new CameraContract(
                        event.getRenderTick(),
                        event.getPartialTick(),
                        target.width,
                        target.height,
                        target.viewWidth,
                        target.viewHeight,
                        mc.getWindow().getWidth(),
                        mc.getWindow().getHeight(),
                        mc.getWindow().getGuiScaledWidth(),
                        mc.getWindow().getGuiScaledHeight(),
                        pos.x, pos.y, pos.z,
                        camera.getXRot(), camera.getYRot(),
                        rotation.x(), rotation.y(), rotation.z(), rotation.w(),
                        projectionValues);
            } catch (Throwable t) {
                return null;
            }
        }

        boolean sameFrameContract(CameraContract other) {
            if (other == null
                    || renderTick != other.renderTick
                    || Float.floatToIntBits(partialTick) != Float.floatToIntBits(other.partialTick)
                    || framebufferWidth != other.framebufferWidth
                    || framebufferHeight != other.framebufferHeight
                    || viewportWidth != other.viewportWidth
                    || viewportHeight != other.viewportHeight
                    || windowWidth != other.windowWidth
                    || windowHeight != other.windowHeight
                    || guiScaledWidth != other.guiScaledWidth
                    || guiScaledHeight != other.guiScaledHeight
                    || Double.doubleToLongBits(cameraX) != Double.doubleToLongBits(other.cameraX)
                    || Double.doubleToLongBits(cameraY) != Double.doubleToLongBits(other.cameraY)
                    || Double.doubleToLongBits(cameraZ) != Double.doubleToLongBits(other.cameraZ)
                    || Float.floatToIntBits(cameraXRot) != Float.floatToIntBits(other.cameraXRot)
                    || Float.floatToIntBits(cameraYRot) != Float.floatToIntBits(other.cameraYRot)
                    || Float.floatToIntBits(quaternionX) != Float.floatToIntBits(other.quaternionX)
                    || Float.floatToIntBits(quaternionY) != Float.floatToIntBits(other.quaternionY)
                    || Float.floatToIntBits(quaternionZ) != Float.floatToIntBits(other.quaternionZ)
                    || Float.floatToIntBits(quaternionW) != Float.floatToIntBits(other.quaternionW)
                    || projectionMatrix.length != other.projectionMatrix.length) {
                return false;
            }
            for (int i = 0; i < projectionMatrix.length; i++) {
                if (Float.floatToIntBits(projectionMatrix[i])
                        != Float.floatToIntBits(other.projectionMatrix[i])) {
                    return false;
                }
            }
            return true;
        }

        JsonObject toJson() {
            JsonObject out = new JsonObject();
            out.addProperty("renderTick", renderTick);
            out.addProperty("partialTick", partialTick);
            out.addProperty("framebufferWidth", framebufferWidth);
            out.addProperty("framebufferHeight", framebufferHeight);
            out.addProperty("viewportWidth", viewportWidth);
            out.addProperty("viewportHeight", viewportHeight);
            out.addProperty("windowWidth", windowWidth);
            out.addProperty("windowHeight", windowHeight);
            out.addProperty("guiScaledWidth", guiScaledWidth);
            out.addProperty("guiScaledHeight", guiScaledHeight);

            JsonArray position = new JsonArray();
            position.add(cameraX);
            position.add(cameraY);
            position.add(cameraZ);
            out.add("position", position);
            out.addProperty("xRot", cameraXRot);
            out.addProperty("yRot", cameraYRot);

            JsonArray rotation = new JsonArray();
            rotation.add(quaternionX);
            rotation.add(quaternionY);
            rotation.add(quaternionZ);
            rotation.add(quaternionW);
            out.add("rotationQuaternion", rotation);

            JsonArray projection = new JsonArray();
            for (float value : projectionMatrix) {
                projection.add(value);
            }
            out.add("projectionMatrix", projection);
            out.addProperty("matrixConvention", "JOML_COLUMN_MAJOR_COLUMN_VECTOR");
            return out;
        }

        private static boolean finite(double value) {
            return Double.isFinite(value);
        }
    }
}