package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import javax.annotation.Nullable;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;

/**
 * Exact-UUID client tracking for G2.
 *
 * <p>No automatic "first Reimu" selection is allowed. A target must be chosen
 * explicitly through the run-bound target control file.
 *
 * <p>The client entity collection is scanned only when the target changes or
 * the client level instance changes. Normal tracking thereafter is event-driven.
 */
public final class KneekuraDebugTargetTracker {
    private static final long TARGET_FILE_POLL_TICKS = 20L;
    private static final long KEYFRAME_TICKS = 100L;
    private static final long STATE_SAMPLE_TICKS = 5L;
    private static final long STATE_KEYFRAME_TICKS = 100L;

    private static final double POSITION_EPSILON_SQR = 0.05D * 0.05D;
    private static final double VELOCITY_EPSILON_SQR = 0.02D * 0.02D;
    private static final float ROTATION_EPSILON_DEG = 2.0F;
    private static final float HEALTH_EPSILON = 0.01F;

    @Nullable
    private static KneekuraDebugEnv.Config config;
    @Nullable
    private static UUID targetUuid;
    @Nullable
    private static Entity trackedEntity;
    @Nullable
    private static ClientLevel lastLevel;

    private static long targetRevision;
    private static long lastPollTick = Long.MIN_VALUE;
    private static long lastEmitTick = Long.MIN_VALUE;
    private static long lastStateSampleTick = Long.MIN_VALUE;
    private static long lastStateEmitTick = Long.MIN_VALUE;
    private static long localClientTick;
    private static boolean lastTracked;
    private static boolean emittedOnce;
    @Nullable
    private static EntityStateSnapshot lastStateSnapshot;

    private KneekuraDebugTargetTracker() {
    }

    public static void configure(KneekuraDebugEnv.Config value) {
        config = value;
    }

    public static void onClientTick(
            KneekuraDebugEnv.Config value,
            Minecraft mc,
            long tickCounter
    ) {
        config = value;
        localClientTick = tickCounter;

        if (value == null || !value.enabled()) {
            return;
        }

        ClientLevel level = mc.level;
        if (level != lastLevel) {
            ClientLevel previousLevel = lastLevel;
            lastLevel = level;
            trackedEntity = null;

            if (targetUuid != null && previousLevel != null) {
                emitTracked(false, null, "client_level_changed", true);
            }

            if (targetUuid != null && level != null) {
                Entity existing = findOnce(level, targetUuid);
                trackedEntity = existing;
                emitTracked(existing != null, existing, "client_level_scan", true);
            }
        }

        if (lastPollTick == Long.MIN_VALUE
                || tickCounter - lastPollTick >= TARGET_FILE_POLL_TICKS) {
            lastPollTick = tickCounter;
            pollTargetFile(mc);
        }

        if (targetUuid != null
                && emittedOnce
                && tickCounter - lastEmitTick >= KEYFRAME_TICKS) {
            Entity current = trackedEntity;
            if (current != null && current.isRemoved()) {
                trackedEntity = null;
                resetStateSnapshot();
                emitTracked(false, null, "removed_without_leave_event", true);
            } else {
                emitTracked(current != null, current, "keyframe", true);
            }
        }

        sampleEntityStateIfNeeded();
    }

    public static void onEntityJoin(Entity entity) {
        UUID target = targetUuid;
        if (target == null || entity == null || !target.equals(entity.getUUID())) {
            return;
        }
        trackedEntity = entity;
        resetStateSnapshot();
        emitTracked(true, entity, "entity_join", false);
    }

    public static void onEntityLeave(Entity entity) {
        UUID target = targetUuid;
        if (target == null || entity == null || !target.equals(entity.getUUID())) {
            return;
        }
        trackedEntity = null;
        resetStateSnapshot();
        emitTracked(false, entity, "entity_leave", false);
    }

    private static void pollTargetFile(Minecraft mc) {
        KneekuraDebugEnv.Config cfg = config;
        if (cfg == null || !cfg.enabled()) {
            return;
        }

        Path file = cfg.targetFile();
        try {
            if (!Files.exists(file)) {
                return;
            }

            String raw = Files.readString(file, StandardCharsets.UTF_8);
            JsonObject root = JsonParser.parseString(raw).getAsJsonObject();

            if (root.get("v").getAsInt() != 1) {
                throw new IllegalArgumentException("target control v must be 1");
            }
            if (!cfg.debugSessionId().equals(root.get("debugSessionId").getAsString())) {
                throw new IllegalArgumentException("target control debugSessionId mismatch");
            }
            if (!cfg.runId().equals(root.get("runId").getAsString())) {
                throw new IllegalArgumentException("target control runId mismatch");
            }
            if (!cfg.runSnapshotId().equals(
                    root.get("runSnapshotId").getAsString())) {
                throw new IllegalArgumentException(
                        "target control runSnapshotId mismatch");
            }
            if (cfg.processEpoch() != root.get("processEpoch").getAsInt()) {
                throw new IllegalArgumentException("target control processEpoch mismatch");
            }

            long revision = root.get("revision").getAsLong();
            if (revision <= 0) {
                throw new IllegalArgumentException("target control revision must be positive");
            }
            if (revision < targetRevision) {
                TouhouLittleMaid.LOGGER.warn(
                        "[KNEEKURA-DEBUG] stale target revision ignored current={} received={}",
                        targetRevision,
                        revision);
                return;
            }
            if (revision == targetRevision) {
                return;
            }

            UUID next = null;
            JsonElement targetElement = root.get("targetUuid");
            if (targetElement != null && !targetElement.isJsonNull()) {
                next = UUID.fromString(targetElement.getAsString());
            }

            UUID previous = targetUuid;
            if (previous != null && !previous.equals(next)) {
                emitTracked(false, trackedEntity, next == null ? "target_cleared" : "target_changed", true);
            }

            targetRevision = revision;
            targetUuid = next;
            trackedEntity = null;
            emittedOnce = false;
            lastEmitTick = Long.MIN_VALUE;
            resetStateSnapshot();

            if (next == null) {
                TouhouLittleMaid.LOGGER.info(
                        "[KNEEKURA-DEBUG] exact target cleared revision={}",
                        revision);
                return;
            }

            Entity existing = mc.level == null ? null : findOnce(mc.level, next);
            trackedEntity = existing;
            emitTracked(existing != null, existing, "target_selected", true);

            TouhouLittleMaid.LOGGER.info(
                    "[KNEEKURA-DEBUG] exact target selected uuid={} revision={} tracked={}",
                    next,
                    revision,
                    existing != null);
        } catch (Throwable e) {
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] target control read rejected: {}",
                    file,
                    e);
        }
    }

    private static void sampleEntityStateIfNeeded() {
        KneekuraDebugEnv.Config cfg = config;
        UUID target = targetUuid;
        Entity entity = trackedEntity;

        if (cfg == null || !cfg.enabled() || target == null || entity == null) {
            return;
        }

        if (lastStateSampleTick != Long.MIN_VALUE
                && localClientTick - lastStateSampleTick < STATE_SAMPLE_TICKS) {
            return;
        }
        lastStateSampleTick = localClientTick;

        EntityStateSnapshot current = EntityStateSnapshot.capture(entity);
        boolean keyframe = lastStateEmitTick == Long.MIN_VALUE
                || localClientTick - lastStateEmitTick >= STATE_KEYFRAME_TICKS;
        boolean changed = lastStateSnapshot == null
                || current.meaningfullyDiffers(lastStateSnapshot);

        if (!changed && !keyframe) {
            return;
        }

        JsonObject payload = current.toJson();
        payload.addProperty("reason", changed ? "changed" : "keyframe");
        payload.addProperty("targetRevision", targetRevision);

        Long gameTime = lastLevel == null ? null : lastLevel.getGameTime();
        try {
            KneekuraDebugEvidenceWriter.recordEntityObserved(
                    cfg,
                    localClientTick,
                    gameTime,
                    "L1",
                    "ENTITY_STATE",
                    "KneekuraDebugTargetTracker.entity_state",
                    target,
                    payload);
            lastStateSnapshot = current;
            lastStateEmitTick = localClientTick;
        } catch (Throwable e) {
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] entity state evidence write failed uuid={}",
                    target,
                    e);
        }
    }

    private static void resetStateSnapshot() {
        lastStateSnapshot = null;
        lastStateSampleTick = Long.MIN_VALUE;
        lastStateEmitTick = Long.MIN_VALUE;
    }

    private record EntityStateSnapshot(
            double x,
            double y,
            double z,
            double vx,
            double vy,
            double vz,
            float yaw,
            float pitch,
            boolean onGround,
            boolean alive,
            boolean removed,
            boolean noGravity,
            @Nullable Float health,
            @Nullable Float maxHealth
    ) {
        static EntityStateSnapshot capture(Entity entity) {
            Vec3 velocity = entity.getDeltaMovement();
            Float health = null;
            Float maxHealth = null;
            if (entity instanceof LivingEntity living) {
                health = living.getHealth();
                maxHealth = living.getMaxHealth();
            }

            return new EntityStateSnapshot(
                    entity.getX(),
                    entity.getY(),
                    entity.getZ(),
                    velocity.x,
                    velocity.y,
                    velocity.z,
                    entity.getYRot(),
                    entity.getXRot(),
                    entity.onGround(),
                    entity.isAlive(),
                    entity.isRemoved(),
                    entity.isNoGravity(),
                    health,
                    maxHealth);
        }

        boolean meaningfullyDiffers(EntityStateSnapshot previous) {
            if (distanceSquared(x, y, z, previous.x, previous.y, previous.z)
                    > POSITION_EPSILON_SQR) {
                return true;
            }
            if (distanceSquared(vx, vy, vz, previous.vx, previous.vy, previous.vz)
                    > VELOCITY_EPSILON_SQR) {
                return true;
            }
            if (angleDelta(yaw, previous.yaw) > ROTATION_EPSILON_DEG
                    || angleDelta(pitch, previous.pitch) > ROTATION_EPSILON_DEG) {
                return true;
            }
            if (onGround != previous.onGround
                    || alive != previous.alive
                    || removed != previous.removed
                    || noGravity != previous.noGravity) {
                return true;
            }
            return floatChanged(health, previous.health)
                    || floatChanged(maxHealth, previous.maxHealth);
        }

        JsonObject toJson() {
            JsonObject out = new JsonObject();
            out.addProperty("x", x);
            out.addProperty("y", y);
            out.addProperty("z", z);
            out.addProperty("vx", vx);
            out.addProperty("vy", vy);
            out.addProperty("vz", vz);
            out.addProperty("yaw", yaw);
            out.addProperty("pitch", pitch);
            out.addProperty("onGround", onGround);
            out.addProperty("alive", alive);
            out.addProperty("removed", removed);
            out.addProperty("noGravity", noGravity);
            if (health != null) {
                out.addProperty("health", health);
            }
            if (maxHealth != null) {
                out.addProperty("maxHealth", maxHealth);
            }
            return out;
        }

        private static boolean floatChanged(@Nullable Float a, @Nullable Float b) {
            if (a == null || b == null) {
                return a != b;
            }
            return Math.abs(a - b) > HEALTH_EPSILON;
        }

        private static double distanceSquared(
                double ax, double ay, double az,
                double bx, double by, double bz
        ) {
            double dx = ax - bx;
            double dy = ay - by;
            double dz = az - bz;
            return dx * dx + dy * dy + dz * dz;
        }

        private static float angleDelta(float a, float b) {
            float delta = (a - b) % 360.0F;
            if (delta > 180.0F) {
                delta -= 360.0F;
            } else if (delta < -180.0F) {
                delta += 360.0F;
            }
            return Math.abs(delta);
        }
    }

    @Nullable
    private static Entity findOnce(ClientLevel level, UUID uuid) {
        for (Entity entity : level.entitiesForRendering()) {
            if (uuid.equals(entity.getUUID())) {
                return entity;
            }
        }
        return null;
    }

    private static void emitTracked(
            boolean tracked,
            @Nullable Entity entity,
            String reason,
            boolean force
    ) {
        KneekuraDebugEnv.Config cfg = config;
        UUID target = targetUuid;

        if (cfg == null || !cfg.enabled() || target == null) {
            return;
        }
        if (!force && emittedOnce && lastTracked == tracked) {
            return;
        }

        JsonObject payload = new JsonObject();
        payload.addProperty("tracked", tracked);
        payload.addProperty("reason", reason);
        payload.addProperty("targetRevision", targetRevision);

        if (entity != null) {
            payload.addProperty("entityId", entity.getId());
            payload.addProperty(
                    "type",
                    BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString());
            payload.addProperty("alive", entity.isAlive());
            payload.addProperty("x", entity.getX());
            payload.addProperty("y", entity.getY());
            payload.addProperty("z", entity.getZ());
        }

        Long gameTime = lastLevel == null ? null : lastLevel.getGameTime();

        try {
            KneekuraDebugEvidenceWriter.recordEntityObserved(
                    cfg,
                    localClientTick,
                    gameTime,
                    "L1",
                    "TARGET_TRACKED",
                    "KneekuraDebugTargetTracker." + reason,
                    target,
                    payload);
            lastTracked = tracked;
            emittedOnce = true;
            lastEmitTick = localClientTick;
        } catch (Throwable e) {
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] target tracking evidence write failed uuid={}",
                    target,
                    e);
        }
    }
}
