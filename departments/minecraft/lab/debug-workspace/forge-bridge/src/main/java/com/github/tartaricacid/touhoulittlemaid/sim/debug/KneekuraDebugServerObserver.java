package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.init.InitEntities;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.phys.Vec3;

import javax.annotation.Nullable;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Server-authoritative exact-target observer for G2.
 *
 * <p>No world/entity scan is performed. The selected UUID is resolved through
 * ServerLevel#getEntity(UUID) across the small set of loaded dimensions.
 * State lanes are sampled every five server ticks and emitted only on change
 * or at a bounded keyframe interval.
 */
public final class KneekuraDebugServerObserver {
    private static final long TARGET_FILE_POLL_TICKS = 20L;
    private static final long SAMPLE_TICKS = 5L;
    private static final long KEYFRAME_TICKS = 100L;

    @Nullable
    private static KneekuraDebugEnv.Config config;
    @Nullable
    private static UUID targetUuid;
    private static long targetRevision;
    private static long observationArenaEpoch;
    private static long lastTargetPollTick = Long.MIN_VALUE;
    private static long lastSampleTick = Long.MIN_VALUE;

    private static final Map<String, String> LAST_PAYLOAD = new HashMap<>();
    private static final Map<String, Long> LAST_EMIT_TICK = new HashMap<>();
    private static List<BehaviorIdentity> lastRunningBehaviors = List.of();
    private static boolean runningBehaviorBaselineSeen;
    private static final IdentityHashMap<Object, String> BEHAVIOR_TOKENS =
            new IdentityHashMap<>();
    private static long nextBehaviorToken;
    private static boolean decisionSnapshotEnabled;
    private static KneekuraDebugDecisionBurstRequest decisionBurst;
    private static KneekuraDebugTerrainQueryRequest decisionTerrain;
    private static final KneekuraDebugDecisionSnapshot DECISION_SNAPSHOT = new KneekuraDebugDecisionSnapshot();

    private KneekuraDebugServerObserver() {
    }

    public static void onServerTick(
            KneekuraDebugEnv.Config value,
            MinecraftServer server,
            long localServerTick
    ) {
        config = value;
        if (value == null || !value.enabled() || server == null) {
            KneekuraDebugDecisionBurstRuntime.stop();
            KneekuraDebugMotionOverlayRuntime.clear();
            return;
        }

        if (lastTargetPollTick == Long.MIN_VALUE
                || localServerTick - lastTargetPollTick >= TARGET_FILE_POLL_TICKS) {
            lastTargetPollTick = localServerTick;
            pollTargetFile(value);
        }

        try {
            long epoch=KneekuraDebugArenaRuntime.observationEpoch(value,server);
            if(epoch!=observationArenaEpoch){LAST_PAYLOAD.clear();LAST_EMIT_TICK.clear();KneekuraDebugMotionOverlayRuntime.clear();}
            observationArenaEpoch=epoch;
            KneekuraDebugMotionOverlayRuntime.select(value,epoch,targetRevision,targetUuid);
        }catch(Exception error){KneekuraDebugMotionOverlayRuntime.clear();KneekuraDebugDecisionBurstRuntime.stop();return;}

        KneekuraDebugDecisionBurstRuntime.onTick(value,server,localServerTick,targetUuid,
                targetRevision,decisionBurst,DECISION_SNAPSHOT);
        KneekuraDebugTerrainRuntime.onTick(value,server,localServerTick,targetUuid,targetRevision,decisionTerrain);

        UUID selected = targetUuid;
        if (selected == null) {
            return;
        }

        if (lastSampleTick != Long.MIN_VALUE
                && localServerTick - lastSampleTick < SAMPLE_TICKS) {
            return;
        }
        lastSampleTick = localServerTick;

        ResolvedTarget resolved = resolveExact(server, selected);
        long gameTime = resolved.level != null
                ? resolved.level.getGameTime()
                : server.overworld().getGameTime();

        JsonObject tracking = new JsonObject();
        tracking.addProperty("tracked", resolved.entity != null);
        tracking.addProperty("targetRevision", targetRevision);
        if (resolved.entity == null) {
            tracking.addProperty("reason", "not_loaded_or_absent");
            emitIfChanged(
                    localServerTick,
                    gameTime,
                    selected,
                    "SERVER_TARGET_TRACKED",
                    "KneekuraDebugServerObserver.resolve_exact_uuid",
                    tracking);
            return;
        }

        Entity entity = resolved.entity;
        ServerLevel level = resolved.level;

        tracking.addProperty("reason", "resolved_exact_uuid");
        tracking.addProperty("entityId", entity.getId());
        tracking.addProperty(
                "type",
                BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString());
        tracking.addProperty("dimension", level.dimension().location().toString());
        emitIfChanged(
                localServerTick,
                gameTime,
                selected,
                "SERVER_TARGET_TRACKED",
                "KneekuraDebugServerObserver.resolve_exact_uuid",
                tracking);

        emitServerEntityState(
                localServerTick,
                gameTime,
                selected,
                level,
                entity);

        if (entity instanceof Mob mob) {
            emitAiTarget(localServerTick, gameTime, selected, mob);
            emitNavigation(localServerTick, gameTime, selected, mob);
            if (decisionSnapshotEnabled) {
                long started = System.nanoTime();
                JsonObject snapshot = DECISION_SNAPSHOT.capture(mob);
                snapshot.addProperty("observerCostNanos", Math.max(0L, System.nanoTime() - started));
                snapshot.addProperty("observerCostScope", "SNAPSHOT_CAPTURE_ONLY_EXCLUDES_WRITER_AND_VIEWER");
                snapshot.addProperty("sampleTick", gameTime);
                emitIfChanged(localServerTick, gameTime, selected, "AI_DECISION",
                        "KneekuraDebugDecisionSnapshot.capture_cached_components",
                        snapshot);
                KneekuraDebugDecisionAdapterRegistry.captureSelected(value,server,mob,targetRevision,localServerTick);
            }
        }

        if (entity instanceof EntityMaid maid) {
            emitTlmState(localServerTick, gameTime, selected, maid);
            emitBrainMemory(localServerTick, gameTime, selected, maid);
            emitRunningBehaviors(localServerTick, gameTime, selected, maid);
            if (maid.isReimuMaid()) {
                emitReimuState(localServerTick, gameTime, selected, maid);
            }
        }
    }

    private static void pollTargetFile(KneekuraDebugEnv.Config cfg) {
        java.nio.file.Path file = cfg.targetFile();
        try {
            if (!Files.exists(file)) {
                return;
            }

            JsonObject root = JsonParser.parseString(
                    Files.readString(file, StandardCharsets.UTF_8)
            ).getAsJsonObject();

            if (root.get("v").getAsInt() != 1) {
                throw new IllegalArgumentException("target control v must be 1");
            }
            if (!cfg.debugSessionId().equals(
                    root.get("debugSessionId").getAsString())) {
                throw new IllegalArgumentException(
                        "target control debugSessionId mismatch");
            }
            if (!cfg.runId().equals(root.get("runId").getAsString())) {
                throw new IllegalArgumentException(
                        "target control runId mismatch");
            }
            if (!cfg.runSnapshotId().equals(
                    root.get("runSnapshotId").getAsString())) {
                throw new IllegalArgumentException(
                        "target control runSnapshotId mismatch");
            }
            if (cfg.processEpoch() != root.get("processEpoch").getAsInt()) {
                throw new IllegalArgumentException(
                        "target control processEpoch mismatch");
            }

            long revision = root.get("revision").getAsLong();
            if (revision <= 0) {
                throw new IllegalArgumentException(
                        "target control revision must be positive");
            }
            if (revision <= targetRevision) {
                return;
            }

            UUID next = null;
            JsonElement targetElement = root.get("targetUuid");
            if (targetElement != null && !targetElement.isJsonNull()) {
                next = UUID.fromString(targetElement.getAsString());
            }

            JsonElement snapshotElement = root.get("decisionSnapshot");
            if (snapshotElement != null && (!snapshotElement.isJsonPrimitive()
                    || !snapshotElement.getAsJsonPrimitive().isBoolean())) {
                throw new IllegalArgumentException("decisionSnapshot must be boolean");
            }
            boolean nextSnapshot = snapshotElement != null && snapshotElement.getAsBoolean();
            if (nextSnapshot && next == null) {
                throw new IllegalArgumentException("decisionSnapshot requires a target");
            }
            KneekuraDebugDecisionBurstRequest nextBurst=KneekuraDebugDecisionBurstRequest.parse(root.get("decisionBurst"));
            KneekuraDebugDecisionBurstRuntime.validateRequest(nextBurst,next);
            KneekuraDebugTerrainQueryRequest nextTerrain=KneekuraDebugTerrainQueryRequest.parse(root.get("decisionTerrain"));
            if(nextTerrain!=null&&next==null)throw new IllegalArgumentException("decisionTerrain requires a target");

            KneekuraDebugDecisionBurstRuntime.selectionChanged();
            KneekuraDebugMotionOverlayRuntime.clear();
            KneekuraDebugTerrainRuntime.clear();
            targetRevision = revision;
            targetUuid = next;
            lastSampleTick = Long.MIN_VALUE;
            LAST_PAYLOAD.clear();
            LAST_EMIT_TICK.clear();
            lastRunningBehaviors = List.of();
            runningBehaviorBaselineSeen = false;
            BEHAVIOR_TOKENS.clear();
            nextBehaviorToken = 0L;
            decisionSnapshotEnabled = nextSnapshot;
            decisionBurst=nextBurst;
            decisionTerrain=nextTerrain;
            DECISION_SNAPSHOT.reset(revision);

            TouhouLittleMaid.LOGGER.info(
                    "[KNEEKURA-DEBUG] server exact target revision={} uuid={}",
                    revision,
                    next);
        } catch (Throwable e) {
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] server target control read rejected: {}",
                    file,
                    e);
        }
    }

    static void stop() {
        KneekuraDebugDecisionBurstRuntime.stop();
        KneekuraDebugMotionOverlayRuntime.clear();observationArenaEpoch=0;
        KneekuraDebugTerrainRuntime.clear();decisionTerrain=null;
        targetUuid=null;targetRevision=0;decisionSnapshotEnabled=false;decisionBurst=null;
        lastTargetPollTick=Long.MIN_VALUE;lastSampleTick=Long.MIN_VALUE;
        LAST_PAYLOAD.clear();LAST_EMIT_TICK.clear();BEHAVIOR_TOKENS.clear();
        lastRunningBehaviors=List.of();runningBehaviorBaselineSeen=false;nextBehaviorToken=0;
        DECISION_SNAPSHOT.reset(0);
    }

    private static ResolvedTarget resolveExact(
            MinecraftServer server,
            UUID uuid
    ) {
        for (ServerLevel level : server.getAllLevels()) {
            Entity entity = level.getEntity(uuid);
            if (entity != null) {
                return new ResolvedTarget(level, entity);
            }
        }
        return new ResolvedTarget(null, null);
    }

    private static void emitServerEntityState(
            long tick,
            long gameTime,
            UUID selected,
            ServerLevel level,
            Entity entity
    ) {
        Vec3 velocity = entity.getDeltaMovement();
        JsonObject payload = new JsonObject();
        payload.addProperty("dimension", level.dimension().location().toString());
        payload.addProperty("motionTraceClass",entity instanceof Projectile ? "PROJECTILE_ACTUAL" : entity instanceof Mob ? "MOB_ACTUAL" : "NOT_APPLICABLE");
        payload.addProperty("x", entity.getX());
        payload.addProperty("y", entity.getY());
        payload.addProperty("z", entity.getZ());
        payload.addProperty("vx", velocity.x);
        payload.addProperty("vy", velocity.y);
        payload.addProperty("vz", velocity.z);
        payload.addProperty("yaw", entity.getYRot());
        payload.addProperty("pitch", entity.getXRot());
        payload.addProperty("onGround", entity.onGround());
        payload.addProperty("alive", entity.isAlive());
        payload.addProperty("removed", entity.isRemoved());
        payload.addProperty("noGravity", entity.isNoGravity());

        if (entity instanceof LivingEntity living) {
            payload.addProperty("health", living.getHealth());
            payload.addProperty("maxHealth", living.getMaxHealth());
        }

        emitIfChanged(
                tick,
                gameTime,
                selected,
                "SERVER_ENTITY_STATE",
                "KneekuraDebugServerObserver.entity_state",
                payload);
    }

    private static void emitAiTarget(
            long tick,
            long gameTime,
            UUID selected,
            Mob mob
    ) {
        LivingEntity target = mob.getTarget();
        JsonObject payload = new JsonObject();
        payload.addProperty("present", target != null);

        if (target != null) {
            payload.addProperty("targetUuid", target.getUUID().toString());
            payload.addProperty("targetEntityId", target.getId());
            payload.addProperty(
                    "targetType",
                    BuiltInRegistries.ENTITY_TYPE.getKey(
                            target.getType()).toString());
            payload.addProperty("targetAlive", target.isAlive());
            payload.addProperty("distanceSqr", mob.distanceToSqr(target));
            payload.addProperty("lineOfSight", mob.hasLineOfSight(target));
        }

        emitIfChanged(
                tick,
                gameTime,
                selected,
                "AI_TARGET",
                "Mob.getTarget",
                payload);
    }

    private static void emitNavigation(
            long tick,
            long gameTime,
            UUID selected,
            Mob mob
    ) {
        Path path = mob.getNavigation().getPath();
        JsonObject payload = new JsonObject();
        payload.addProperty("navigationDone", mob.getNavigation().isDone());
        payload.addProperty("pathPresent", path != null);

        if (path != null) {
            payload.addProperty("pathDone", path.isDone());
            payload.addProperty("canReach", path.canReach());
            payload.addProperty("nodeCount", path.getNodeCount());
            payload.addProperty("nextNodeIndex", path.getNextNodeIndex());

            if (!path.isDone()) {
                Node next = path.getNextNode();
                if (next != null) {
                    payload.addProperty("nextNodeX", next.x);
                    payload.addProperty("nextNodeY", next.y);
                    payload.addProperty("nextNodeZ", next.z);
                }
            }
        }

        emitIfChanged(
                tick,
                gameTime,
                selected,
                "NAVIGATION",
                "PathNavigation.getPath",
                payload);
    }

    private static void emitTlmState(
            long tick,
            long gameTime,
            UUID selected,
            EntityMaid maid
    ) {
        JsonObject payload = new JsonObject();
        payload.addProperty("taskUid", maid.getTask().getUid().toString());
        payload.addProperty("schedule", maid.getSchedule().name());
        payload.addProperty("tame", maid.isTame());
        payload.addProperty("homeMode", maid.isHomeModeEnable());

        UUID owner = maid.getOwnerUUID();
        if (owner != null) {
            payload.addProperty("ownerUuid", owner.toString());
        }

        maid.getBrain().getActiveNonCoreActivity().ifPresent(
                activity -> payload.addProperty(
                        "activeNonCoreActivity",
                        activity.toString()));

        emitIfChanged(
                tick,
                gameTime,
                selected,
                "TLM_STATE",
                "EntityMaid.public_state",
                payload);
    }

    private static void emitBrainMemory(
            long tick,
            long gameTime,
            UUID selected,
            EntityMaid maid
    ) {
        var brain = maid.getBrain();
        JsonObject payload = new JsonObject();

        var attackTarget = brain.getMemory(MemoryModuleType.ATTACK_TARGET);
        payload.addProperty("attackTargetPresent", attackTarget.isPresent());
        attackTarget.ifPresent(target -> {
            payload.addProperty("attackTargetUuid", target.getUUID().toString());
            payload.addProperty("attackTargetEntityId", target.getId());
            payload.addProperty(
                    "attackTargetType",
                    BuiltInRegistries.ENTITY_TYPE.getKey(
                            target.getType()).toString());
        });

        var walkTarget = brain.getMemory(MemoryModuleType.WALK_TARGET);
        payload.addProperty("walkTargetPresent", walkTarget.isPresent());
        walkTarget.ifPresent(target -> {
            var block = target.getTarget().currentBlockPosition();
            payload.addProperty("walkTargetX", block.getX());
            payload.addProperty("walkTargetY", block.getY());
            payload.addProperty("walkTargetZ", block.getZ());
            payload.addProperty("walkTargetSpeedModifier", target.getSpeedModifier());
            payload.addProperty(
                    "walkTargetCloseEnoughDist",
                    target.getCloseEnoughDist());
        });

        var lookTarget = brain.getMemory(MemoryModuleType.LOOK_TARGET);
        payload.addProperty("lookTargetPresent", lookTarget.isPresent());
        lookTarget.ifPresent(target -> {
            var block = target.currentBlockPosition();
            payload.addProperty("lookTargetX", block.getX());
            payload.addProperty("lookTargetY", block.getY());
            payload.addProperty("lookTargetZ", block.getZ());
        });

        var pathMemory = brain.getMemory(MemoryModuleType.PATH);
        payload.addProperty("pathMemoryPresent", pathMemory.isPresent());
        pathMemory.ifPresent(path -> {
            payload.addProperty("pathMemoryDone", path.isDone());
            payload.addProperty("pathMemoryCanReach", path.canReach());
            payload.addProperty("pathMemoryNodeCount", path.getNodeCount());
            payload.addProperty(
                    "pathMemoryNextNodeIndex",
                    path.getNextNodeIndex());
        });

        var cantReach = brain.getMemory(
                MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE);
        payload.addProperty("cantReachSincePresent", cantReach.isPresent());
        cantReach.ifPresent(value ->
                payload.addProperty("cantReachSinceGameTime", value));

        payload.addProperty(
                "attackCoolingDown",
                brain.hasMemoryValue(MemoryModuleType.ATTACK_COOLING_DOWN));

        var targetPos = brain.getMemory(InitEntities.TARGET_POS.get());
        payload.addProperty("tlmTargetPosPresent", targetPos.isPresent());
        targetPos.ifPresent(target -> {
            var block = target.currentBlockPosition();
            payload.addProperty("tlmTargetPosX", block.getX());
            payload.addProperty("tlmTargetPosY", block.getY());
            payload.addProperty("tlmTargetPosZ", block.getZ());
        });

        emitIfChanged(
                tick,
                gameTime,
                selected,
                "BRAIN_MEMORY",
                "Brain.public_memory",
                payload);
    }

    private static void emitRunningBehaviors(
            long tick,
            long gameTime,
            UUID selected,
            EntityMaid maid
    ) {
        JsonObject payload = new JsonObject();
        JsonArray running = new JsonArray();
        Map<String, Integer> classCounts = new HashMap<>();
        List<BehaviorIdentity> current = new ArrayList<>();

        int index = 0;
        for (var behavior : maid.getBrain().getRunningBehaviors()) {
            String className = behavior.getClass().getName();
            String instanceIdentity = BEHAVIOR_TOKENS.computeIfAbsent(
                    behavior,
                    ignored -> "behavior:" + (++nextBehaviorToken));
            classCounts.merge(className, 1, Integer::sum);
            current.add(new BehaviorIdentity(
                    className,
                    instanceIdentity));

            JsonObject entry = new JsonObject();
            entry.addProperty("index", index++);
            entry.addProperty("className", className);
            entry.addProperty(
                    "instanceIdentity",
                    instanceIdentity);
            running.add(entry);
        }

        JsonObject duplicateClasses = new JsonObject();
        classCounts.entrySet().stream()
                .filter(entry -> entry.getValue() > 1)
                .sorted(Map.Entry.comparingByKey())
                .forEach(entry -> duplicateClasses.addProperty(
                        entry.getKey(),
                        entry.getValue()));

        payload.addProperty("count", running.size());
        payload.addProperty(
                "instanceIdentityScope",
                "JVM_PROCESS_TARGET_REVISION_REFERENCE_IDENTITY");
        payload.add("running", running);
        payload.add("duplicateClassCounts", duplicateClasses);

        if (runningBehaviorBaselineSeen) {
            emitBehaviorTransition(
                    tick,
                    gameTime,
                    selected,
                    lastRunningBehaviors,
                    current);
        }
        lastRunningBehaviors = List.copyOf(current);
        runningBehaviorBaselineSeen = true;

        emitIfChanged(
                tick,
                gameTime,
                selected,
                "RUNNING_BEHAVIORS",
                "Brain.getRunningBehaviors",
                payload);
    }

    private static void emitBehaviorTransition(
            long tick,
            long gameTime,
            UUID selected,
            List<BehaviorIdentity> previous,
            List<BehaviorIdentity> current
    ) {
        Map<BehaviorIdentity, Integer> before = counts(previous);
        Map<BehaviorIdentity, Integer> after = counts(current);
        JsonArray started = new JsonArray();
        JsonArray stopped = new JsonArray();

        for (var entry : after.entrySet()) {
            int delta = entry.getValue() - before.getOrDefault(entry.getKey(), 0);
            for (int i = 0; i < delta; i++) {
                started.add(behaviorJson(entry.getKey()));
            }
        }

        for (var entry : before.entrySet()) {
            int delta = entry.getValue() - after.getOrDefault(entry.getKey(), 0);
            for (int i = 0; i < delta; i++) {
                stopped.add(behaviorJson(entry.getKey()));
            }
        }

        if (started.size() == 0 && stopped.size() == 0) {
            return;
        }

        JsonObject payload = new JsonObject();
        payload.addProperty(
                "transitionSemantics",
                "RUNNING_SET_CHANGED_BETWEEN_SAMPLES");
        payload.addProperty("sampleIntervalTicks", SAMPLE_TICKS);
        payload.addProperty(
                "exactTransitionTickKnown",
                false);
        payload.addProperty(
                "reasonKnown",
                false);
        payload.addProperty(
                "instanceIdentityScope",
                "JVM_PROCESS_TARGET_REVISION_REFERENCE_IDENTITY");
        payload.add("started", started);
        payload.add("stopped", stopped);

        try {
            KneekuraDebugEvidenceWriter.recordEntityObserved(
                    config,
                    tick,
                    gameTime,
                    "L2",
                    "BEHAVIOR_TRANSITION",
                    "SERVER",
                    "Brain.getRunningBehaviors.delta",
                    selected,
                    payload);
        } catch (Throwable e) {
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] behavior transition write failed uuid={}",
                    selected,
                    e);
        }
    }

    private static Map<BehaviorIdentity, Integer> counts(
            List<BehaviorIdentity> values
    ) {
        Map<BehaviorIdentity, Integer> out = new LinkedHashMap<>();
        for (BehaviorIdentity value : values) {
            out.merge(value, 1, Integer::sum);
        }
        return out;
    }

    private static JsonObject behaviorJson(BehaviorIdentity value) {
        JsonObject out = new JsonObject();
        out.addProperty("className", value.className());
        out.addProperty("instanceIdentity", value.instanceIdentity());
        return out;
    }

    private static void emitReimuState(
            long tick,
            long gameTime,
            UUID selected,
            EntityMaid maid
    ) {
        JsonObject payload = new JsonObject();
        payload.addProperty(
                "secondFormActive",
                maid.isReimuSecondFormActive());
        payload.addProperty(
                "secondFormMode",
                maid.getReimuSecondFormMode().name());
        payload.addProperty(
                "currentPhase",
                maid.getReimuCurrentPhase());
        payload.addProperty(
                "damageReactionActive",
                maid.isReimuDamageReactionActive());
        payload.addProperty(
                "damageReactionHoldTicks",
                maid.getReimuDamageReactionHoldTicks());
        payload.addProperty(
                "blueRedOrbCooldownTicks",
                maid.getReimuBlueRedOrbCooldownTicks());
        payload.addProperty(
                "redOrbCooldownTicks",
                maid.getReimuRedOrbCooldownTicks());
        payload.addProperty(
                "effectivelyGrounded",
                maid.isReimuEffectivelyGrounded());

        emitIfChanged(
                tick,
                gameTime,
                selected,
                "REIMU_STATE",
                "EntityMaid.reimu_public_state",
                payload);
    }

    private static void emitIfChanged(
            long tick,
            long gameTime,
            UUID selected,
            String lane,
            String method,
            JsonObject payload
    ) {
        KneekuraDebugEnv.Config cfg = config;
        if (cfg == null || !cfg.enabled()) {
            return;
        }

        String current = payload.toString();
        String previous = LAST_PAYLOAD.get(lane);
        Long lastEmit = LAST_EMIT_TICK.get(lane);
        boolean changed = previous == null || !previous.equals(current);
        boolean keyframe = lastEmit == null || tick - lastEmit >= KEYFRAME_TICKS;

        if (!changed && !keyframe) {
            return;
        }

        try {
            JsonObject rowPayload = payload.deepCopy();
            rowPayload.addProperty("reason", changed ? "changed" : "keyframe");
            rowPayload.addProperty("targetRevision", targetRevision);

            KneekuraDebugEvidenceWriter.recordServerSelectedObserved(
                    cfg,
                    observationArenaEpoch,
                    tick,
                    gameTime,
                    lane,
                    method,
                    selected,
                    rowPayload);

            LAST_PAYLOAD.put(lane, current);
            LAST_EMIT_TICK.put(lane, tick);
        } catch (Throwable e) {
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] server observer write failed lane={} uuid={}",
                    lane,
                    selected,
                    e);
        }
    }

    private record BehaviorIdentity(
            String className,
            String instanceIdentity
    ) {
    }

    private record ResolvedTarget(
            @Nullable ServerLevel level,
            @Nullable Entity entity
    ) {
    }
}
