package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.sim.SimLab;
import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimNetworkTrace;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import javax.annotation.Nullable;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Formal M6 verifier for the actual Reimu packet -> handler -> YSM client-command path.
 *
 * <p>The proof window is:
 * <pre>
 * M3 handler
 *   -> ysm_molang_command_pre_dispatch (snapshot exact state before sendCommand)
 *   -> M5 handledByClient=true
 *   -> post-M5 exact state snapshot
 * </pre>
 *
 * <p>Formal M6 is emitted only when the same entity, variable and stable exact runtime candidate
 * changes from {@code before} to the literal assigned by the actual handled command.
 *
 * <p>Controlled /tlmsim toggle probes never pass this gate: they use the same command scheduler,
 * but do not have a preceding Reimu packet-handler M3 context.
 */
@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, value = Dist.CLIENT)
public final class SimYsmFormalM6Probe {
    private static final double TARGET_RADIUS = 1.50d;
    private static final int VERIFY_DELAY_TICKS = 2;
    private static final long MAX_HANDLER_AGE_TICKS = 80L;
    private static final long MAX_DISPATCH_AGE_TICKS = 40L;
    private static final int MAX_HANDLER_CONTEXTS = 64;
    private static final int MAX_DISPATCH_CONTEXTS = 64;
    private static final int MAX_PENDING_CHECKS = 64;

    private static final Object LOCK = new Object();
    private static final Deque<HandlerContext> handlers = new ArrayDeque<>();
    private static final Deque<DispatchContext> dispatches = new ArrayDeque<>();
    private static final Deque<PendingCheck> pending = new ArrayDeque<>();
    private static final SimYsmM6TransitionTracker tracker = new SimYsmM6TransitionTracker();

    @Nullable
    private static ClientLevel lastLevel;
    @Nullable
    private static String lastRunKey;

    private SimYsmFormalM6Probe() {}

    private record HandlerContext(
            long packetTraceId,
            String expression,
            double x,
            double y,
            double z,
            long gameTime
    ) {}

    private record PreState(
            String stableIdentity,
            double value
    ) {}

    private record DispatchContext(
            String expression,
            String packetTraceIds,
            int entityId,
            String entityUuid,
            Map<String, PreState> preStates,
            boolean preScanComplete,
            long handlerGameTime,
            long preDispatchGameTime
    ) {}

    private record PendingCheck(
            int entityId,
            String entityUuid,
            String expression,
            String packetTraceIds,
            String variable,
            double expectedValue,
            @Nullable PreState preState,
            boolean preScanComplete,
            long handlerGameTime,
            long preDispatchGameTime,
            long m5GameTime,
            long dueGameTime
    ) {}

    /**
     * Called reflectively by SimNetworkTrace only after the source semantic row has been flushed.
     */
    public static void onNetworkSemantic(String kind, Map<String, ?> payload) {
        if (!enabled() || kind == null || payload == null) {
            return;
        }
        synchronized (LOCK) {
            if (!ensureStateIdentity()) {
                return;
            }
            long now = gameTime();
            trimOldContexts(now);
            switch (kind) {
                case "reimu_spellcard_handler" -> recordHandler(payload, now);
                case "ysm_molang_command_pre_dispatch" -> recordPreDispatch(payload, now);
                case "ysm_client_command_result" -> recordM5(payload, now);
                default -> {
                    // The network companion retains the full M0-M5 stream independently.
                }
            }
        }
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) {
            return;
        }
        synchronized (LOCK) {
            if (!enabled() || !ensureStateIdentity()) {
                reset();
                return;
            }

            ClientLevel level = Minecraft.getInstance().level;
            if (level == null) {
                reset();
                return;
            }

            long now = level.getGameTime();
            trimOldContexts(now);
            while (!pending.isEmpty() && pending.peekFirst().dueGameTime() <= now) {
                verify(pending.removeFirst(), now);
            }
        }
    }

    private static void recordHandler(Map<String, ?> payload, long now) {
        String expression = stringValue(payload.get("molangExpression"));
        Long packetTraceId = SimYsmM6TraceIds.positiveLong(payload.get("packetTraceId"));
        Double x = numberValue(payload.get("x"));
        Double y = numberValue(payload.get("y"));
        Double z = numberValue(payload.get("z"));
        if (expression == null || packetTraceId == null || x == null || y == null || z == null) {
            // Old reimu-mod builds without exact trace identity are not formal-M6 eligible.
            return;
        }

        while (handlers.size() >= MAX_HANDLER_CONTEXTS) {
            handlers.removeFirst();
        }
        handlers.addLast(new HandlerContext(packetTraceId, expression, x, y, z, now));
    }

    /**
     * This semantic is emitted synchronously immediately before sendCommand() in reimu-mod.
     * Reading the graph here gives the real pre-command state rather than an earlier queue-time state.
     */
    private static void recordPreDispatch(Map<String, ?> payload, long now) {
        String expression = stringValue(payload.get("molangExpression"));
        Boolean packetHandlerOrigin = booleanValue(payload.get("packetHandlerOrigin"));
        String rawTraceIds = stringValue(payload.get("packetTraceIds"));
        List<Long> traceIds = SimYsmM6TraceIds.parse(rawTraceIds);
        String packetTraceIds = SimYsmM6TraceIds.canonical(traceIds);
        if (expression == null
                || !Boolean.TRUE.equals(packetHandlerOrigin)
                || traceIds.isEmpty()
                || packetTraceIds.isEmpty()) {
            // Old builds, controlled probes, mixed-origin queues and malformed IDs all fail closed.
            return;
        }

        List<HandlerContext> matches = matchingHandlers(expression, traceIds, now);
        if (matches.size() != traceIds.size()) {
            // Every pre-dispatch trace ID must resolve to exactly one durable M3 handler row.
            return;
        }
        handlers.removeAll(matches);

        EntityMaid target = resolveSingleTarget(matches);
        if (target == null) {
            return;
        }

        Map<String, SimMolangLiteralAssignments.Assignment> assignments =
                SimMolangLiteralAssignments.lastByVariable(expression);
        if (assignments.isEmpty()) {
            return;
        }

        // A newer command for the same entity/variable invalidates any older post-M5
        // verification window. Otherwise a later assignment could be misattributed to the
        // earlier command.
        invalidatePending(target.getUUID().toString(), assignments.keySet());

        SimYsmRuntimeRoot.Result runtime = SimYsmRuntimeRoot.findForMaid(target);
        if (!runtime.ok() || runtime.root() == null) {
            return;
        }

        SimYsmScalarProbe.Snapshot snapshot = SimYsmScalarProbe.snapshot(runtime.root());
        Map<String, PreState> preStates = new LinkedHashMap<>();
        for (String variable : assignments.keySet()) {
            List<SimYsmScalarProbe.Scalar> exact =
                    SimYsmToggleAnalyzer.exactNumericCandidates(snapshot, variable);
            if (exact.size() != 1) {
                continue;
            }
            SimYsmScalarProbe.Scalar scalar = exact.get(0);
            Double value = SimYsmToggleAnalyzer.numericValue(scalar);
            if (value != null) {
                preStates.put(variable, new PreState(scalar.stableIdentity(), value));
            }
        }

        long handlerGameTime = matches.stream()
                .mapToLong(HandlerContext::gameTime)
                .max()
                .orElse(-1L);

        while (dispatches.size() >= MAX_DISPATCH_CONTEXTS) {
            dispatches.removeFirst();
        }
        dispatches.addLast(new DispatchContext(
                expression,
                packetTraceIds,
                target.getId(),
                target.getUUID().toString(),
                Map.copyOf(preStates),
                snapshot.complete(),
                handlerGameTime,
                now));
    }

    private static void recordM5(Map<String, ?> payload, long now) {
        String expression = stringValue(payload.get("molangExpression"));
        if (expression == null) {
            return;
        }

        List<DispatchContext> matches = matchingDispatches(expression, now);
        if (matches.size() != 1) {
            // More than one pre-dispatch context for the same M5 is ambiguous.
            dispatches.removeAll(matches);
            return;
        }
        DispatchContext dispatch = matches.get(0);
        dispatches.remove(dispatch);

        Boolean handled = booleanValue(payload.get("handledByClient"));
        if (!Boolean.TRUE.equals(handled)) {
            return;
        }

        Map<String, SimMolangLiteralAssignments.Assignment> assignments =
                SimMolangLiteralAssignments.lastByVariable(expression);
        if (assignments.isEmpty()) {
            return;
        }

        for (SimMolangLiteralAssignments.Assignment assignment : assignments.values()) {
            if (pending.size() >= MAX_PENDING_CHECKS) {
                pending.removeFirst();
            }
            pending.addLast(new PendingCheck(
                    dispatch.entityId(),
                    dispatch.entityUuid(),
                    expression,
                    dispatch.packetTraceIds(),
                    assignment.variable(),
                    assignment.value(),
                    dispatch.preStates().get(assignment.variable()),
                    dispatch.preScanComplete(),
                    dispatch.handlerGameTime(),
                    dispatch.preDispatchGameTime(),
                    now,
                    now + VERIFY_DELAY_TICKS));
        }
    }

    private static void invalidatePending(
            String entityUuid, java.util.Set<String> variables) {
        if (entityUuid == null || variables == null || variables.isEmpty()) {
            return;
        }
        pending.removeIf(check ->
                entityUuid.equals(check.entityUuid()) && variables.contains(check.variable()));
    }

    private static List<HandlerContext> matchingHandlers(
            String expression, List<Long> traceIds, long now) {
        if (traceIds == null || traceIds.isEmpty()) {
            return List.of();
        }
        List<HandlerContext> matches = new ArrayList<>(traceIds.size());
        for (long traceId : traceIds) {
            HandlerContext found = null;
            int count = 0;
            for (HandlerContext context : handlers) {
                if (tooOld(now, context.gameTime(), MAX_HANDLER_AGE_TICKS)
                        || context.packetTraceId() != traceId) {
                    continue;
                }
                count++;
                found = context;
            }
            if (count != 1 || found == null
                    || !SimMolangLiteralAssignments.containsWholeExpression(
                            expression, found.expression())) {
                return List.of();
            }
            matches.add(found);
        }
        return List.copyOf(matches);
    }

    private static List<DispatchContext> matchingDispatches(String expression, long now) {
        List<DispatchContext> matches = new ArrayList<>();
        for (DispatchContext context : dispatches) {
            if (tooOld(now, context.preDispatchGameTime(), MAX_DISPATCH_AGE_TICKS)) {
                continue;
            }
            if (SimMolangLiteralAssignments.containsWholeExpression(
                    expression, context.expression())) {
                matches.add(context);
            }
        }
        return List.copyOf(matches);
    }

    @Nullable
    private static EntityMaid resolveSingleTarget(List<HandlerContext> matches) {
        EntityMaid selected = null;
        String uuid = null;
        for (HandlerContext context : matches) {
            EntityMaid maid = SimYsmRuntimeRoot.findReimuNear(
                    context.x(), context.y(), context.z(), TARGET_RADIUS);
            if (maid == null) {
                return null;
            }
            String candidateUuid = maid.getUUID().toString();
            if (uuid == null) {
                uuid = candidateUuid;
                selected = maid;
            } else if (!uuid.equals(candidateUuid)) {
                return null;
            }
        }
        return selected;
    }

    private static void verify(PendingCheck check, long now) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            return;
        }
        Entity entity = mc.level.getEntity(check.entityId());
        if (!(entity instanceof EntityMaid maid)
                || !maid.isAlive()
                || !check.entityUuid().equals(maid.getUUID().toString())) {
            return;
        }

        SimYsmRuntimeRoot.Result runtime = SimYsmRuntimeRoot.findForMaid(maid);
        if (!runtime.ok() || runtime.root() == null) {
            return;
        }

        SimYsmScalarProbe.Snapshot snapshot = SimYsmScalarProbe.snapshot(runtime.root());
        List<SimYsmScalarProbe.Scalar> exact = SimYsmToggleAnalyzer.exactNumericMatches(
                snapshot, check.variable(), check.expectedValue());
        if (exact.size() != 1) {
            TouhouLittleMaid.LOGGER.debug(
                    "[SIM-YSM-M6] exact post-state count {} for {}={} (no evidence)",
                    exact.size(), check.variable(), check.expectedValue());
            return;
        }

        SimYsmScalarProbe.Scalar scalar = exact.get(0);
        Double observed = SimYsmToggleAnalyzer.numericValue(scalar);
        if (observed == null) {
            return;
        }

        SimYsmM6TransitionTracker.State before = check.preState() == null
                ? null
                : new SimYsmM6TransitionTracker.State(
                        check.preState().stableIdentity(), check.preState().value());
        SimYsmM6TransitionTracker.State after =
                new SimYsmM6TransitionTracker.State(scalar.stableIdentity(), observed);

        SimYsmM6TransitionTracker.Decision decision = tracker.observeTransition(
                check.entityUuid(),
                check.variable(),
                before,
                after,
                check.expectedValue());

        String qualificationScope = qualificationScopeKey();
        boolean controlledQualified = qualificationScope != null
                && SimYsmM6QualificationRegistry.isQualified(
                        qualificationScope,
                        check.entityUuid(),
                        check.variable(),
                        scalar.stableIdentity());

        Map<String, Object> evidence = new LinkedHashMap<>();
        evidence.put("molangExpression", check.expression());
        evidence.put("packetTraceIds", check.packetTraceIds());
        evidence.put("variable", check.variable());
        evidence.put("expectedValue", check.expectedValue());
        evidence.put("observedValue", observed);
        evidence.put("entityId", check.entityId());
        evidence.put("entityUuid", check.entityUuid());
        evidence.put("candidatePathHash", pathHash(scalar.stableIdentity()));
        evidence.put("candidateOwnerClass", scalar.ownerClass());
        evidence.put("handlerGameTime", check.handlerGameTime());
        evidence.put("preDispatchGameTime", check.preDispatchGameTime());
        evidence.put("m5GameTime", check.m5GameTime());
        evidence.put("verificationGameTime", now);
        evidence.put("preScanComplete", check.preScanComplete());
        evidence.put("postScanComplete", snapshot.complete());
        evidence.put("exactVariableIdentity", true);
        evidence.put("handledByClient", true);
        evidence.put("packetHandlerOrigin", true);
        evidence.put("controlledE2Qualified", controlledQualified);
        evidence.put("matchedTransitionCount", decision.matchedTransitionCount());

        if (decision.applied() && controlledQualified) {
            if (decision.before() != null) {
                evidence.put("before", decision.before());
            }
            evidence.put("after", decision.after());
            evidence.put("evidenceLevel", "E2_ACTUAL_PRE_POST_TRANSITION");
            SimNetworkTrace.onSemantic("ysm_molang_state_applied", evidence);
        } else if (decision.correlated()) {
            if (decision.before() != null) {
                evidence.put("before", decision.before());
            }
            evidence.put("after", decision.after());
            evidence.put(
                    "evidenceLevel",
                    decision.applied()
                            ? "E2_ACTUAL_PRE_POST_TRANSITION_UNQUALIFIED"
                            : "E2_CORRELATED_POSTSTATE");
            SimNetworkTrace.onSemantic("ysm_state_correlated", evidence);
        }
    }

    private static void trimOldContexts(long now) {
        while (!handlers.isEmpty()
                && tooOld(now, handlers.peekFirst().gameTime(), MAX_HANDLER_AGE_TICKS)) {
            handlers.removeFirst();
        }
        while (!dispatches.isEmpty()
                && tooOld(now, dispatches.peekFirst().preDispatchGameTime(), MAX_DISPATCH_AGE_TICKS)) {
            dispatches.removeFirst();
        }
    }

    private static boolean tooOld(long now, long then, long maxAge) {
        return now >= 0 && then >= 0 && now - then > maxAge;
    }

    @Nullable
    private static String stringValue(Object value) {
        return value instanceof String s && !s.isBlank() ? s : null;
    }

    @Nullable
    private static Double numberValue(Object value) {
        return value instanceof Number n && Double.isFinite(n.doubleValue())
                ? n.doubleValue()
                : null;
    }

    @Nullable
    private static Boolean booleanValue(Object value) {
        return value instanceof Boolean b ? b : null;
    }

    private static String pathHash(String stableIdentity) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(stableIdentity.getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder(16);
            for (int i = 0; i < 8; i++) {
                out.append(String.format("%02x", digest[i]));
            }
            return out.toString();
        } catch (Throwable ignored) {
            return Integer.toHexString(stableIdentity.hashCode());
        }
    }

    private static long gameTime() {
        Minecraft mc = Minecraft.getInstance();
        return mc.level == null ? -1L : mc.level.getGameTime();
    }

    private static boolean enabled() {
        String scenario = System.getProperty(SimLab.PROP_SCENARIO);
        String run = System.getProperty(SimLab.PROP_RUN);
        return scenario != null && !scenario.isBlank() && run != null && !run.isBlank();
    }

    @Nullable
    private static String qualificationScopeKey() {
        String base = runKey();
        Minecraft mc = Minecraft.getInstance();
        if (base == null || mc.level == null) {
            return null;
        }
        return base + "|level@" + Integer.toHexString(System.identityHashCode(mc.level));
    }

    @Nullable
    private static String runKey() {
        if (!enabled()) {
            return null;
        }
        return System.getProperty(SimLab.PROP_SCENARIO).trim()
                + "|" + System.getProperty(SimLab.PROP_RUN).trim();
    }

    private static boolean ensureStateIdentity() {
        if (!enabled()) {
            return false;
        }
        ClientLevel level = Minecraft.getInstance().level;
        String key = runKey();
        if (level == null || key == null) {
            return false;
        }
        if (level != lastLevel || !key.equals(lastRunKey)) {
            clearEvidenceState();
            lastLevel = level;
            lastRunKey = key;
        }
        return true;
    }

    private static void clearEvidenceState() {
        handlers.clear();
        dispatches.clear();
        pending.clear();
        tracker.clear();
    }

    private static void reset() {
        clearEvidenceState();
        lastLevel = null;
        lastRunKey = null;
    }
}
