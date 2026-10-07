package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.CameraType;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderHandEvent;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.slf4j.Logger;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** One-client sequential scene capture. Inert until installed by the existing authorized runtime owner. */
@Mod.EventBusSubscriber(modid = "touhou_little_maid", value = Dist.CLIENT)
public final class KneekuraDebugCardinalCapture {
    /** Trusted owner implementation checks its live grant, actual loaded attestation and Arena lease. */
    public interface OwnerGate {
        void assertAuthorized(KneekuraDebugEnv.Config config, KneekuraDebugCaptureSession.Request request);
        ServerLevel level(MinecraftServer server, KneekuraDebugCaptureSession.Request request);
        void assertIdleArena(KneekuraDebugCaptureSession.Request request);
    }
    /** Implemented by the existing EvidenceWriter queue; completion means durable artifact + row. */
    public interface EvidenceSink {
        CompletableFuture<String> frame(KneekuraDebugEnv.Config config, long arenaEpoch,
                                        long clientTick, Long gameTime, byte[] png, JsonObject metadata);
        CompletableFuture<String> manifest(KneekuraDebugEnv.Config config, long arenaEpoch,
                                           long clientTick, Long gameTime, JsonObject metadata);
    }
    private record Installation(KneekuraDebugEnv.Config config, OwnerGate gate, EvidenceSink sink) {}
    private record ServerState(long tick, long gameTime, String hash, JsonObject facts) {}
    private static final Gson GSON = new Gson();
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final long ORIGIN = System.nanoTime();
    private static volatile Installation installation;
    private static volatile Active active;
    private static long clientTick;
    private static long renderFrame;
    private static final List<String> usedCaptureIds = new ArrayList<>();
    private static String attemptIdentity;

    private KneekuraDebugCardinalCapture() {}
    public static void install(KneekuraDebugEnv.Config config, OwnerGate gate, EvidenceSink sink) {
        mainThread();
        if (config == null || !config.enabled() || gate == null || sink == null || installation != null)
            throw new IllegalStateException("CAPTURE_OWNER_INSTALL_REJECTED");
        installation = new Installation(config, gate, sink);
        if (!config.identityKey().equals(attemptIdentity)) {
            usedCaptureIds.clear(); attemptIdentity = config.identityKey();
        }
    }
    public static void uninstall() {
        mainThread();
        if (active != null) active.abort("OWNER_UNINSTALLED");
        installation = null;
    }
    public static boolean installed() { return installation != null; }
    /** Actual client attempt quiescence, including the final durable manifest acknowledgement. */
    static boolean quiescent() { mainThread(); return active == null; }
    public static CompletableFuture<JsonObject> request(KneekuraDebugCaptureSession.Request request) {
        mainThread();
        Installation owner = installation;
        if (owner == null) throw new IllegalStateException("CAPTURE_NOT_CONFIGURED");
        if (active != null || usedCaptureIds.contains(request.captureId()) || usedCaptureIds.size() >= 16)
            throw new IllegalStateException("CAPTURE_BUSY_OR_ALREADY_ATTEMPTED");
        var id = request.identity();
        if (!owner.config().debugSessionId().equals(id.debugSessionId()) ||
                !owner.config().runId().equals(id.runId()) ||
                !owner.config().runSnapshotId().equals(id.runSnapshotId()) ||
                owner.config().processEpoch() != id.processEpoch())
            throw new IllegalStateException("STALE_CAPTURE_IDENTITY");
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null || mc.getCameraEntity() == null || mc.isPaused() || mc.screen != null || mc.getOverlay() != null ||
                mc.getSingleplayerServer() == null || mc.getSingleplayerServer().isPublished() ||
                !owner.config().worldName().equals(mc.getSingleplayerServer().getWorldData().getLevelName()) ||
                mc.gameRenderer.currentEffect() != null || mc.mouseHandler.isLeftPressed() ||
                mc.mouseHandler.isMiddlePressed() || mc.mouseHandler.isRightPressed())
            throw new IllegalStateException("CAPTURE_PRESENTATION_NOT_SUPPORTED");
        for (KeyMapping key : mc.options.keyMappings)
            if (key.isDown()) throw new IllegalStateException("CAPTURE_REQUIRES_IDLE_INPUT");
        if (mc.getMainRenderTarget().width != request.width() || mc.getMainRenderTarget().height != request.height())
            throw new IllegalStateException("CAPTURE_VIEWPORT_UNAVAILABLE");
        Active next = new Active(owner, request, mc);
        if (!KneekuraDebugCameraOwnership.claim(next)) throw new IllegalStateException("CAMERA_ALREADY_OWNED");
        usedCaptureIds.add(request.captureId()); // A failed or uncertain attempt is never replayed.
        active = next;
        mc.getSingleplayerServer().execute(() -> {
            try {
                if (active != next || installation != owner) throw new IllegalStateException("CAPTURE_OWNER_CHANGED");
                owner.gate().assertAuthorized(owner.config(), request);
                owner.gate().assertIdleArena(request);
                next.authorization.complete(null);
            } catch (Throwable error) { next.authorization.completeExceptionally(error); }
        });
        return next.result;
    }
    /** Private owned completion facts; these are not additions to the durable manifest schema. */
    record OwnedCompletion(JsonObject manifest, boolean serverBarrierReleased, boolean serverBarrierExpired) {
        OwnedCompletion { manifest = manifest.deepCopy(); }
        @Override public JsonObject manifest() { return manifest.deepCopy(); }
    }
    static CompletableFuture<OwnedCompletion> requestOwned(KneekuraDebugCaptureSession.Request request) {
        CompletableFuture<JsonObject> future = request(request);
        Active exact = active; // request has just installed this concrete client-owned attempt.
        return future.thenApply(manifest -> new OwnedCompletion(manifest, !exact.barrier.isHeld(), exact.barrier.expired()));
    }
    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        clientTick++;
        Active capture = active;
        if (capture != null) capture.progress();
    }
    @SubscribeEvent
    public static void onRender(TickEvent.RenderTickEvent event) {
        if (event.phase != TickEvent.Phase.START) return;
        renderFrame++;
        Active capture = active;
        if (capture != null) capture.progress();
    }
    @SubscribeEvent
    public static void onFov(ViewportEvent.ComputeFov event) {
        Active capture = active;
        if (capture != null && capture.camera != null && !capture.restored)
            event.setFOV(capture.request.fov());
    }
    @SubscribeEvent
    public static void onHand(RenderHandEvent event) {
        Active capture = active;
        if (capture != null && capture.camera != null && !capture.restored) event.setCanceled(true);
    }
    @SubscribeEvent
    public static void onLevelRendered(RenderLevelStageEvent event) {
        Active capture = active;
        if (capture == null) return;
        if (event.getStage() == RenderLevelStageEvent.Stage.AFTER_ENTITIES) capture.rememberViewMatrix(event);
        if (event.getStage() == RenderLevelStageEvent.Stage.AFTER_LEVEL) capture.capture(event);
    }
    private static final class PauseScreen extends Screen {
        PauseScreen() { super(Component.literal("KNEEKURA bounded evidence capture")); }
        @Override public boolean isPauseScreen() { return true; }
        @Override public boolean shouldCloseOnEsc() { return false; }
        @Override public void render(GuiGraphics graphics, int x, int y, float partialTick) {}
    }
    private static final class Active {
        final Installation owner;
        final KneekuraDebugCaptureSession.Request request;
        final KneekuraDebugCaptureSession protocol;
        final CompletableFuture<JsonObject> result = new CompletableFuture<>();
        final KneekuraDebugCaptureBarrier<ServerState> barrier = new KneekuraDebugCaptureBarrier<>();
        final CompletableFuture<Void> authorization = new CompletableFuture<>();
        final PauseScreen pauseScreen = new PauseScreen();
        final ClientLevel level;
        final Entity oldCamera;
        final CameraType oldCameraType;
        final boolean oldHideGui;
        final boolean oldBob;
        final boolean oldMouseGrabbed;
        final int oldFov;
        final List<JsonObject> frameMetadata = new ArrayList<>();
        boolean serverRequested;
        boolean presentationChanged;
        boolean restored;
        boolean restorationRecorded;
        boolean restorationFieldsExact;
        KneekuraDebugCaptureRestoration.State restorationExpected;
        KneekuraDebugCaptureRestoration.State restorationObserved;
        boolean writingManifest;
        ArmorStand camera;
        Vec3 oldCameraPosition;
        float oldCameraYaw;
        float oldCameraPitch;
        String clientStateHash;
        KneekuraDebugCaptureClock renderClock;
        ServerState state;
        int warmupFrames;
        long startedFrame;
        long startedTick;
        long barrierStart;
        long barrierEnd;
        double eyeOffset;
        float[] observedViewMatrix;
        long viewMatrixFrame = -1;
        Active(Installation owner, KneekuraDebugCaptureSession.Request request, Minecraft mc) {
            this.owner = owner; this.request = request;
            protocol = new KneekuraDebugCaptureSession(request, now());
            level = mc.level; oldCamera = mc.getCameraEntity(); oldCameraType = mc.options.getCameraType();
            oldHideGui = mc.options.hideGui; oldBob = mc.options.bobView().get(); oldFov = mc.options.fov().get();
            oldMouseGrabbed = mc.mouseHandler.isMouseGrabbed();
        }
        void progress() {
            if (writingManifest) {
                if (!result.isDone() && protocol.expired(now(), false)) {
                    result.completeExceptionally(new IllegalStateException("CAPTURE_MANIFEST_WRITE_UNKNOWN"));
                    if (active == this) active = null;
                }
                return;
            }
            try {
                if (restored) {
                    if (!restorationRecorded) {
                        if (protocol.expired(now(), barrier.isHeld()) || barrier.expired()) {
                            protocol.abort("RESTORATION_DEADLINE"); completeRestoration(false);
                        } else if (!restorationFieldsExact) completeRestoration(false);
                        else {
                            restorationObserved = presentation(Minecraft.getInstance());
                            if (KneekuraDebugCaptureRestoration.exact(restorationExpected, restorationObserved)) completeRestoration(true);
                        }
                    }
                    if (protocol.expired(now(), false) && !protocol.isTerminal()) protocol.abort("FRAME_ACK_DEADLINE");
                    if (protocol.readyToFinish()) finish();
                    return;
                }
                if (protocol.expired(now(), barrier.isHeld()) || barrier.expired()) { abort("DEADLINE_EXPIRED"); return; }
                Minecraft mc = Minecraft.getInstance();
                if (mc.level != level || installation != owner) throw new IllegalStateException("CAPTURE_CONTEXT_CHANGED");
                if (!presentationChanged) {
                    if (!authorization.isDone()) return;
                    try { authorization.join(); }
                    catch (Throwable denied) {
                        result.completeExceptionally(new IllegalStateException("CAPTURE_OWNER_DENIED", denied));
                        protocol.abort("CAPTURE_OWNER_DENIED"); barrier.release();
                        if (active == this) active = null;
                        KneekuraDebugCameraOwnership.release(this);
                        return;
                    }
                    if (mc.screen != null || mc.getCameraEntity() != oldCamera || mc.options.getCameraType() != oldCameraType ||
                            mc.options.hideGui != oldHideGui || mc.options.bobView().get() != oldBob ||
                            mc.options.fov().get() != oldFov || mc.mouseHandler.isMouseGrabbed() != oldMouseGrabbed)
                        throw new IllegalStateException("PRESENTATION_CHANGED");
                    for (KeyMapping key : mc.options.keyMappings) if (key.isDown()) throw new IllegalStateException("INPUT_CHANGED");
                    presentationChanged = true;
                    mc.setScreen(pauseScreen);
                    return;
                }
                if (mc.screen != pauseScreen) throw new IllegalStateException("CAPTURE_SCREEN_CHANGED");
                if (!mc.isPaused()) return; // Observe the actual public pause API, never infer from a screen alone.
                if (!serverRequested) {
                    serverRequested = true;
                    mc.getSingleplayerServer().execute(this::holdServer);
                    return;
                }
                if (state == null && barrier.ready().isDone()) {
                    state = barrier.ready().join();
                    if (!barrier.isHeld() || barrier.expired()) throw new IllegalStateException("BARRIER_UNAVAILABLE");
                    protocol.acquire(now(), state.tick(), state.gameTime(), state.hash());
                    barrierStart = now(); startedFrame = renderFrame; startedTick = clientTick;
                    // Minecraft.runTick reads this paused clock after RenderTick.START,
                    // before passing the real interpolation value into GameRenderer.
                    renderClock = new KneekuraDebugCaptureClock(mc::isPaused,
                            KneekuraDebugCaptureClock.field(mc, Minecraft.class),
                            KneekuraDebugCaptureClock.eventField(mc, Minecraft.class));
                    renderClock.acquire();
                    oldCameraPosition = oldCamera.position(); oldCameraYaw = oldCamera.getYRot(); oldCameraPitch = oldCamera.getXRot();
                    restorationExpected = new KneekuraDebugCaptureRestoration.State(oldCamera.getUUID().toString(),
                            oldCameraType.name(), oldHideGui, oldBob, oldFov, false, oldMouseGrabbed, "NONE",
                            oldCameraPosition.x, oldCameraPosition.y, oldCameraPosition.z, oldCameraYaw, oldCameraPitch);
                    clientStateHash = hash(GSON.toJson(clientFacts(mc, request.subjects())).getBytes(StandardCharsets.UTF_8));
                    camera = new ArmorStand(level, 0, 0, 0); // Detached: never added to any Level/entity registry.
                    camera.setInvisible(true); camera.setNoGravity(true);
                    mc.options.setCameraType(CameraType.FIRST_PERSON); mc.options.hideGui = true;
                    mc.options.bobView().set(false);
                    mc.setCameraEntity(camera);
                    placeNext();
                }
            } catch (Throwable error) { abort("BARRIER_OR_IDENTITY_FAILED"); }
        }
        void holdServer() {
            barrier.hold(() -> {
                MinecraftServer server = Minecraft.getInstance().getSingleplayerServer();
                if (server == null || installation != owner || active != this)
                    throw new IllegalStateException("OWNER_UNAVAILABLE");
                owner.gate().assertAuthorized(owner.config(), request);
                owner.gate().assertIdleArena(request);
                ServerLevel serverLevel = owner.gate().level(server, request);
                if (serverLevel == null || !serverLevel.dimension().equals(level.dimension()) ||
                        !owner.config().worldName().equals(server.getWorldData().getLevelName()))
                    throw new IllegalStateException("WORLD_MISMATCH");
                JsonObject facts = serverFacts(serverLevel, request.subjects());
                JsonObject bounds = new JsonObject();
                bounds.add("min", GSON.toJsonTree(request.arenaMin())); bounds.add("max", GSON.toJsonTree(request.arenaMax()));
                facts.add("arenaBounds", bounds);
                return new ServerState(server.getTickCount(), serverLevel.getGameTime(),
                        hash(GSON.toJson(facts).getBytes(StandardCharsets.UTF_8)), facts);
            }, request.barrierBudgetMs());
        }
        void placeNext() {
            if (protocol.nextViewIndex() >= 4) return;
            List<Double> pose = request.pose(KneekuraDebugCaptureSession.VIEWS.get(protocol.nextViewIndex()));
            camera.moveTo(pose.get(0), pose.get(1) - eyeOffset, pose.get(2),
                    pose.get(3).floatValue(), pose.get(4).floatValue());
            // Camera.setup reads LivingEntity.getViewYRot, which interpolates
            // head rotation rather than the body's yaw changed by moveTo.
            camera.setYHeadRot(pose.get(3).floatValue());
            camera.yHeadRotO = pose.get(3).floatValue();
            camera.setOldPosAndRot();
            warmupFrames = 0;
        }
        void rememberViewMatrix(RenderLevelStageEvent event) {
            if (camera == null || restored || event.getCamera().getEntity() != camera) return;
            observedViewMatrix = new float[16];
            event.getPoseStack().last().pose().get(observedViewMatrix);
            viewMatrixFrame = renderFrame;
        }
        void capture(RenderLevelStageEvent event) {
            if (camera == null || restored || writingManifest) return;
            try {
                Minecraft mc = Minecraft.getInstance();
                if (!mc.isPaused() || !barrier.isHeld() || barrier.expired() || mc.level != level ||
                        mc.getCameraEntity() != camera || mc.screen != pauseScreen ||
                        protocol.expired(now(), true) || mc.gameRenderer.currentEffect() != null) throw new IllegalStateException("CAPTURE_BARRIER_LOST");
                if (!clientStateHash.equals(hash(GSON.toJson(clientFacts(mc, request.subjects())).getBytes(StandardCharsets.UTF_8))))
                    throw new IllegalStateException("CLIENT_STATE_CHANGED");
                if (mc.getMainRenderTarget().width != request.width() || mc.getMainRenderTarget().height != request.height())
                    throw new IllegalStateException("VIEWPORT_CHANGED");
                if (observedViewMatrix == null || viewMatrixFrame != renderFrame)
                    throw new IllegalStateException("VIEW_MATRIX_NOT_OBSERVED_THIS_FRAME");
                if (renderClock == null || !renderClock.frozen() || Float.compare(event.getPartialTick(), 0) != 0)
                    throw new IllegalStateException("RENDER_INTERPOLATION_NOT_ESTABLISHED");
                String view = KneekuraDebugCaptureSession.VIEWS.get(protocol.nextViewIndex());
                List<Double> desired = request.pose(view);
                Vec3 actual = event.getCamera().getPosition();
                // Camera keeps interpolated eye-height state. Calibrate one uncaptured frame, then verify exact pose.
                if (Math.abs(actual.y - desired.get(1)) > 0.00001) {
                    if (++warmupFrames > 2) throw new IllegalStateException("CAMERA_POSE_UNSTABLE");
                    eyeOffset += actual.y - desired.get(1);
                    camera.moveTo(desired.get(0), desired.get(1) - eyeOffset, desired.get(2),
                            desired.get(3).floatValue(), desired.get(4).floatValue());
                    camera.setOldPosAndRot();
                    return;
                }
                if (Math.abs(actual.x - desired.get(0)) > .00001 || Math.abs(actual.z - desired.get(2)) > .00001 ||
                        Math.abs(event.getCamera().getXRot() - desired.get(4)) > .001 ||
                        Math.abs(Math.IEEEremainder(event.getCamera().getYRot() - desired.get(3), 360)) > .001)
                    throw new IllegalStateException("CAMERA_POSE_MISMATCH");
                double actualFov = Math.toDegrees(2 * Math.atan(1.0 / event.getProjectionMatrix().m11()));
                if (!Double.isFinite(actualFov) || Math.abs(actualFov - request.fov()) > .001)
                    throw new IllegalStateException("FOV_CHANGED");
                long start = System.nanoTime();
                byte[] bytes;
                try (NativeImage image = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                    if (image.getWidth() != request.width() || image.getHeight() != request.height())
                        throw new IllegalStateException("IMAGE_DIMENSIONS_CHANGED");
                    bytes = image.asByteArray();
                }
                if (bytes.length > KneekuraDebugCaptureSession.MAX_PNG_BYTES) throw new IllegalStateException("IMAGE_BUDGET");
                String imageHash = hash(bytes);
                JsonObject metadata = frameMetadata(event, view, actual, imageHash, bytes.length, System.nanoTime() - start);
                protocol.frame(view, renderFrame, imageHash);
                frameMetadata.add(metadata);
                CompletableFuture<String> durable = owner.sink().frame(owner.config(), request.identity().arenaEpoch(),
                        clientTick, state.gameTime(), bytes, metadata.deepCopy());
                durable.whenComplete((rowHash, error) -> mc.execute(() -> {
                    if (active != this || protocol.isTerminal()) return;
                    if (error != null) { abort("FRAME_WRITE_UNKNOWN"); return; }
                    try { protocol.durable(view, rowHash); progress(); }
                    catch (Throwable invalid) { abort("FRAME_ACK_INVALID"); }
                }));
                if (protocol.nextViewIndex() == 4) restore();
                else placeNext();
            } catch (Throwable error) {
                LOGGER.warn("[KNEEKURA-DEBUG] cardinal capture failed", error);
                abort("CAPTURE_OR_PERSIST_FAILED");
            }
        }
        JsonObject frameMetadata(RenderLevelStageEvent event, String view, Vec3 position,
                                 String imageHash, int bytes, long durationNanos) {
            JsonObject out = common("cardinal4_raw_frame");
            out.addProperty("view", view); out.addProperty("frameIndex", protocol.nextViewIndex());
            out.addProperty("renderFrame", renderFrame); out.addProperty("clientTick", clientTick);
            out.addProperty("serverTick", state.tick()); out.addProperty("serverGameTime", state.gameTime());
            out.addProperty("partialTick", event.getPartialTick());
            out.addProperty("imageHash", imageHash); out.addProperty("imageBytes", bytes);
            out.addProperty("artifactRole", "RAW_SCENE_RGB");
            out.addProperty("captureStage", "AFTER_LEVEL_BEFORE_HAND_HUD");
            out.addProperty("imagePath", "evidence/raw/visual/" + imageHash + ".png");
            out.addProperty("captureDurationNanos", durationNanos);
            JsonObject cameraInfo = new JsonObject();
            cameraInfo.add("position", GSON.toJsonTree(List.of(position.x, position.y, position.z)));
            var rotation = event.getCamera().rotation();
            cameraInfo.add("quaternion", GSON.toJsonTree(List.of(rotation.x(), rotation.y(), rotation.z(), rotation.w())));
            cameraInfo.addProperty("yaw", event.getCamera().getYRot()); cameraInfo.addProperty("pitch", event.getCamera().getXRot());
            cameraInfo.addProperty("fov", Math.toDegrees(2 * Math.atan(1.0 / event.getProjectionMatrix().m11()))); cameraInfo.addProperty("projection", "PERSPECTIVE");
            float[] matrix = new float[16]; event.getProjectionMatrix().get(matrix);
            cameraInfo.add("projectionMatrix", GSON.toJsonTree(matrix));
            // Forge AFTER_LEVEL receives the projection PoseStack; the real view stack was observed at AFTER_ENTITIES.
            cameraInfo.add("viewMatrix", GSON.toJsonTree(observedViewMatrix));
            cameraInfo.addProperty("matrixConvention", "JOML_COLUMN_MAJOR_CAMERA_RELATIVE");
            cameraInfo.add("viewport", GSON.toJsonTree(List.of(request.width(), request.height())));
            out.add("camera", cameraInfo);
            return out;
        }
        JsonObject common(String kind) {
            JsonObject out = new JsonObject();
            out.addProperty("schemaVersion", 1); out.addProperty("kind", kind);
            out.addProperty("captureId", request.captureId()); out.addProperty("rig", KneekuraDebugCaptureSession.RIG);
            out.add("identity", GSON.toJsonTree(request.identity()));
            out.add("subjects", GSON.toJsonTree(request.subjects()));
            out.addProperty("controlledStateHash", state == null ? null : state.hash());
            out.addProperty("sameFrame", false);
            return out;
        }
        void restore() {
            if (restored) return;
            restored = true;
            Minecraft mc = Minecraft.getInstance();
            boolean clockRestored = renderClock == null || renderClock.restore();
            try {
                boolean sameLevel = mc.level == level;
                if (sameLevel) mc.setCameraEntity(oldCamera);
                mc.options.setCameraType(oldCameraType); mc.options.hideGui = oldHideGui;
                mc.options.bobView().set(oldBob); mc.options.fov().set(oldFov);
                boolean ownedScreen = mc.screen == pauseScreen;
                if (ownedScreen) {
                    mc.setScreen(null);
                    if (oldMouseGrabbed) mc.mouseHandler.grabMouse(); else mc.mouseHandler.releaseMouse();
                }
                restorationFieldsExact = clockRestored && sameLevel && ownedScreen && mc.getCameraEntity() == oldCamera &&
                        mc.gameRenderer.currentEffect() == null;
                if (restorationExpected == null) {
                    Vec3 p = oldCamera.position();
                    restorationExpected = new KneekuraDebugCaptureRestoration.State(oldCamera.getUUID().toString(),
                            oldCameraType.name(), oldHideGui, oldBob, oldFov, false, oldMouseGrabbed, "NONE",
                            p.x, p.y, p.z, oldCamera.getYRot(), oldCamera.getXRot());
                }
                restorationObserved = presentation(mc);
                // setScreen(null) does not synchronously clear Minecraft.isPaused(). Wait for observed readback.
                if (!restorationFieldsExact) completeRestoration(false);
                else if (KneekuraDebugCaptureRestoration.exact(restorationExpected, restorationObserved)) completeRestoration(true);
            } catch (Throwable error) { completeRestoration(false); }
            if (protocol.readyToFinish()) finish();
        }
        void completeRestoration(boolean exact) {
            if (restorationRecorded) return;
            restorationRecorded = true;
            protocol.restored(exact);
            barrierEnd = now(); barrier.release();
        }
        KneekuraDebugCaptureRestoration.State presentation(Minecraft mc) {
            Entity current = mc.getCameraEntity();
            if (current == null) return null;
            Vec3 p = current.position();
            return new KneekuraDebugCaptureRestoration.State(current.getUUID().toString(), mc.options.getCameraType().name(),
                    mc.options.hideGui, mc.options.bobView().get(), mc.options.fov().get(), mc.isPaused(),
                    mc.mouseHandler.isMouseGrabbed(), mc.screen == null ? "NONE" : "OTHER",
                    p.x, p.y, p.z, current.getYRot(), current.getXRot());
        }
        void abort(String reason) {
            if (writingManifest) return;
            if (!presentationChanged) {
                protocol.abort(reason); barrier.release();
                result.completeExceptionally(new IllegalStateException(reason));
                if (active == this) active = null;
                KneekuraDebugCameraOwnership.release(this);
                return;
            }
            protocol.abort(reason);
            restore();
            // Restore uses the same bounded API readback after an abort: pause
            // state changes on the next client update, never synchronously.
            if (protocol.readyToFinish()) finish();
        }
        void finish() {
            if (writingManifest || barrier.isHeld()) return;
            writingManifest = true;
            var outcome = protocol.finish(now());
            JsonObject manifest = common("cardinal4_capture_manifest");
            manifest.add("result", GSON.toJsonTree(outcome));
            manifest.add("frames", GSON.toJsonTree(frameMetadata));
            manifest.add("structuredState", state == null ? null : state.facts());
            JsonObject restorationProof = new JsonObject();
            restorationProof.add("expected", GSON.toJsonTree(restorationExpected));
            restorationProof.add("observed", GSON.toJsonTree(restorationObserved));
            restorationProof.addProperty("basis", "MINECRAFT_API_READBACK");
            manifest.add("restorationProof", restorationProof);
            manifest.addProperty("renderFrameStart", startedFrame); manifest.addProperty("renderFrameEnd", renderFrame);
            manifest.addProperty("clientTickStart", startedTick); manifest.addProperty("clientTickEnd", clientTick);
            manifest.addProperty("barrierDurationMs", barrier.durationMs());
            manifest.addProperty("runtimeAttestation", "OWNER_GATE_REQUIRED_NOT_INFERRED_FROM_CAPTURE");
            manifest.addProperty("visualVerdict", "NOT_RUN"); manifest.addProperty("behaviorVerdict", "INCONCLUSIVE_CAPTURE_PERTURBATION");
            try {
                owner.sink().manifest(owner.config(), request.identity().arenaEpoch(), clientTick,
                        state == null ? null : state.gameTime(), manifest.deepCopy()).whenComplete((hash, error) ->
                        Minecraft.getInstance().execute(() -> {
                    if (result.isDone()) return;
                    if (error != null) result.completeExceptionally(new IllegalStateException("CAPTURE_MANIFEST_WRITE_UNKNOWN", error));
                    else {
                        try { KneekuraDebugCaptureSession.hash(hash); result.complete(manifest.deepCopy()); }
                        catch (Throwable invalid) { result.completeExceptionally(invalid); }
                    }
                    if (active == this) active = null;
                    KneekuraDebugCameraOwnership.release(this);
                }));
            } catch (Throwable error) {
                result.completeExceptionally(error);
                if (active == this) active = null;
                KneekuraDebugCameraOwnership.release(this);
            }
        }
    }
    private static JsonObject serverFacts(ServerLevel level, List<UUID> subjects) {
        JsonObject facts = new JsonObject();
        facts.addProperty("dimension", level.dimension().location().toString());
        facts.addProperty("gameTime", level.getGameTime());
        JsonArray entities = new JsonArray();
        for (UUID id : subjects) {
            Entity entity = level.getEntity(id);
            if (entity == null || entity.isRemoved()) throw new IllegalStateException("SUBJECT_NOT_LOADED");
            entities.add(entityFact(entity));
        }
        facts.add("subjects", entities);
        return facts;
    }
    private static JsonObject clientFacts(Minecraft mc, List<UUID> subjects) {
        JsonObject facts = new JsonObject(); JsonArray entities = new JsonArray();
        for (UUID id : subjects) {
            Entity match = null;
            for (Entity entity : mc.level.entitiesForRendering()) if (entity.getUUID().equals(id)) {
                if (match != null) throw new IllegalStateException("DUPLICATE_SUBJECT");
                match = entity;
            }
            if (match == null || match.isRemoved()) throw new IllegalStateException("SUBJECT_NOT_TRACKED");
            entities.add(entityFact(match));
        }
        facts.add("subjects", entities); facts.addProperty("gameTime", mc.level.getGameTime());
        return facts;
    }
    private static JsonObject entityFact(Entity entity) {
        JsonObject fact = new JsonObject();
        fact.addProperty("uuid", entity.getUUID().toString());
        Vec3 p = entity.position(), v = entity.getDeltaMovement();
        fact.add("position", GSON.toJsonTree(List.of(p.x, p.y, p.z)));
        fact.add("velocity", GSON.toJsonTree(List.of(v.x, v.y, v.z)));
        fact.addProperty("yaw", entity.getYRot()); fact.addProperty("pitch", entity.getXRot());
        var box = entity.getBoundingBox();
        fact.add("bounds", GSON.toJsonTree(List.of(box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ)));
        return fact;
    }
    private static long now() { return TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - ORIGIN); }
    private static String hash(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (Exception error) { throw new IllegalStateException(error); }
    }
    private static void mainThread() {
        if (!Minecraft.getInstance().isSameThread()) throw new IllegalStateException("CLIENT_OWNER_THREAD_REQUIRED");
    }
}
