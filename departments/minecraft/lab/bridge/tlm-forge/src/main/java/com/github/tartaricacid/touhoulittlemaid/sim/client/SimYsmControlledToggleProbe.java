package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.ai.reimu.net.client.YsmReimuNaianClientRunner;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.sim.SimLab;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import javax.annotation.Nullable;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Controlled YSM scalar discovery: send 0 -> 1 -> 0 -> 1 through the same Reimu/YSM scheduler
 * used by SimPoseDump, wait for command settlement, and retain the exact snapshot written to disk.
 *
 * <p>This discovers E1/E2 candidates only. It never claims formal M6 because this controlled
 * direct scheduler is not the real M0-M5 packet causal chain.
 */
@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, value = Dist.CLIENT)
public final class SimYsmControlledToggleProbe {
    private static final int SETTLE_TICKS = 8;
    private static final int[] SEQUENCE = {0, 1, 0, 1};
    private static final DateTimeFormatter STAMP =
            DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss-SSS");

    private static boolean active;
    @Nullable private static EntityMaid target;
    @Nullable private static String variable;
    @Nullable private static String session;
    private static int index;
    private static int wait;
    private static boolean awaitingCapture;
    private static boolean allSnapshotsComplete;
    private static boolean requestActualAfterQualification;

    private static final List<String> expressions = new ArrayList<>();
    private static final List<Path> files = new ArrayList<>();
    private static final List<SimYsmScalarProbe.Snapshot> snapshots = new ArrayList<>();

    private SimYsmControlledToggleProbe() {}

    @Nullable
    public static String start(String variableInput) {
        return start(variableInput, false);
    }

    @Nullable
    public static String startAcceptance(String variableInput) {
        return start(variableInput, true);
    }

    @Nullable
    private static String start(String variableInput, boolean requestActual) {
        if (active) {
            return "controlled YSM probe はすでに実行中";
        }

        String bare = SimYsmToggleAnalyzer.normalizeVariable(variableInput);
        if (bare == null) {
            return "variable は英数字/underscoreの単純名だけ指定すること (例: wuqi)";
        }

        String scenario = System.getProperty(SimLab.PROP_SCENARIO);
        String run = System.getProperty(SimLab.PROP_RUN);
        if (scenario == null || scenario.isBlank() || run == null || run.isBlank()) {
            return "tlm.sim.scenario と tlm.sim.run の両方を明示したrunでのみ実行できる";
        }

        SimYsmRuntimeRoot.Result runtime = SimYsmRuntimeRoot.findNearestReimu();
        if (!runtime.ok() || runtime.maid() == null || runtime.root() == null) {
            return runtime.message();
        }

        target = runtime.maid();
        variable = bare;
        session = "toggle-" + bare + "-" + LocalDateTime.now().format(STAMP);
        index = 0;
        wait = 0;
        awaitingCapture = false;
        allSnapshotsComplete = true;
        requestActualAfterQualification = requestActual;
        expressions.clear();
        files.clear();
        snapshots.clear();
        active = true;

        say(ChatFormatting.GRAY,
                "[SIM] YSM controlled probe: v." + bare
                        + " = 0 -> 1 -> 0 -> 1 (各 " + SETTLE_TICKS + " tick 待機)"
                        + (requestActual ? " / E2後にactual packet acceptanceへ接続" : ""));
        return null;
    }

    public static boolean stop() {
        if (!active) {
            return false;
        }
        active = false;
        say(ChatFormatting.YELLOW, "[SIM] YSM controlled probe を中止");
        clearTransient();
        return true;
    }

    public static boolean active() {
        return active;
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (!active || event.phase != TickEvent.Phase.END) {
            return;
        }
        try {
            step();
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM-YSM-PROBE] controlled toggle failed", t);
            fail("controlled probe 例外: " + t);
        }
    }

    private static void step() {
        if (target == null || !target.isAlive() || variable == null || session == null) {
            fail("対象またはprobe stateが失われた");
            return;
        }

        if (wait > 0) {
            wait--;
            return;
        }

        if (!awaitingCapture) {
            if (index >= SEQUENCE.length) {
                finish();
                return;
            }
            int value = SEQUENCE[index];
            String expression = "(v." + variable + " = " + value + ")";
            YsmReimuNaianClientRunner.scheduleSpellCardMolang(
                    target.getX(), target.getY(), target.getZ(), expression);
            expressions.add(expression);
            awaitingCapture = true;
            wait = SETTLE_TICKS;
            return;
        }

        int expected = SEQUENCE[index];
        String label = session + "-" + index + "-" + expected;
        SimYsmMolangStateProbe.DetailedCapture detailed =
                SimYsmMolangStateProbe.captureDetailed(label, target);
        SimYsmMolangStateProbe.CaptureResult result = detailed.result();

        if (!result.ok() || result.file() == null || detailed.snapshot() == null) {
            fail("snapshot " + index + " 失敗: " + result.message());
            return;
        }

        files.add(result.file());
        snapshots.add(detailed.snapshot());
        allSnapshotsComplete &= result.complete();

        say(ChatFormatting.DARK_GRAY,
                "[SIM] YSM controlled probe " + (index + 1) + "/" + SEQUENCE.length
                        + ": v." + variable + "=" + expected
                        + " / " + result.scalarCount() + " scalars");

        index++;
        awaitingCapture = false;
        if (index >= SEQUENCE.length) {
            finish();
        }
    }

    private static void finish() {
        if (variable == null || session == null
                || snapshots.size() != SEQUENCE.length || files.isEmpty()) {
            fail("4 snapshot が揃わず解析できない");
            return;
        }

        SimYsmToggleAnalyzer.Analysis analysis =
                SimYsmToggleAnalyzer.analyze(variable, List.copyOf(snapshots));
        SimYsmToggleAnalyzer.Candidate qualificationCandidate =
                uniqueE2Candidate(analysis);
        Path summaryFile = files.get(0).getParent().resolve(session + ".ysmprobe-sequence.json");

        try {
            SimYsmMolangStateProbe.writeArtifact(
                    summaryFile, summaryJson(analysis, qualificationCandidate));
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error(
                    "[SIM-YSM-PROBE] controlled summary write failed: {}", summaryFile, t);
            fail("sequence summary 書き出し失敗: " + t);
            return;
        }

        boolean qualified = registerQualification(qualificationCandidate);
        boolean actualRequested = qualified
                && requestActualAfterQualification
                && requestActualServerSequence();
        active = false;
        String msg = "[SIM] YSM controlled probe 完了: E2=" + analysis.e2Count()
                + " / E1-only=" + analysis.e1Count()
                + " / controlled E2 qualified=" + (qualified ? "YES" : "NO")
                + (requestActualAfterQualification
                        ? " / actual packet request=" + (actualRequested ? "SENT" : "NOT SENT")
                        : "")
                + " / formal M6=NO -> " + summaryFile;
        say(analysis.e2Count() > 0 ? ChatFormatting.GREEN : ChatFormatting.YELLOW, msg);
        TouhouLittleMaid.LOGGER.info("[SIM-YSM-PROBE] {}", msg);
        clearTransient();
    }

    private static JsonObject summaryJson(
            SimYsmToggleAnalyzer.Analysis analysis,
            @Nullable SimYsmToggleAnalyzer.Candidate qualificationCandidate) {
        JsonObject root = new JsonObject();
        root.addProperty("v", 1);
        root.addProperty("ch", "ysm_probe_sequence");
        root.addProperty("note",
                "controlled discovery only; direct scheduleSpellCardMolang route is not formal M0-M5 causal evidence");
        root.addProperty("variable", analysis.variable());
        root.addProperty("molangVariable", "v." + analysis.variable());
        root.addProperty("settleTicks", SETTLE_TICKS);
        root.addProperty("targetEntityId", target == null ? -1 : target.getId());
        if (target != null) {
            root.addProperty("targetEntityUuid", target.getUUID().toString());
        }
        root.addProperty("allSnapshotsComplete", allSnapshotsComplete);
        root.addProperty("sequenceObserved", analysis.sequenceObserved());
        root.addProperty("e1OnlyCount", analysis.e1Count());
        root.addProperty("e2Count", analysis.e2Count());
        root.addProperty("controlledE2QualificationEligible", qualificationCandidate != null);
        if (qualificationCandidate != null) {
            root.addProperty("qualificationStableIdentity", qualificationCandidate.stableIdentity());
        }
        root.addProperty("formalM6", false);
        root.addProperty("formalM6Reason",
                "controlled scheduler discovery qualifies a candidate but is separate from the actual packet/handler/command causal chain");

        JsonArray expected = new JsonArray();
        for (int value : SEQUENCE) {
            expected.add(value);
        }
        root.add("expectedSequence", expected);

        JsonArray expr = new JsonArray();
        expressions.forEach(expr::add);
        root.add("expressions", expr);

        JsonArray snapshotRows = new JsonArray();
        for (int i = 0; i < files.size(); i++) {
            JsonObject row = new JsonObject();
            row.addProperty("index", i);
            row.addProperty("expectedValue", SEQUENCE[i]);
            row.addProperty("file", files.get(i).getFileName().toString());
            SimYsmScalarProbe.Snapshot snapshot = snapshots.get(i);
            row.addProperty("scanComplete", snapshot.complete());
            row.addProperty("scalarCount", snapshot.scalars().size());
            row.addProperty("truncatedContainers", snapshot.truncatedContainers());
            row.addProperty("depthBudgetExhausted", snapshot.depthBudgetExhausted());
            row.addProperty("visitBudgetExhausted", snapshot.visitBudgetExhausted());
            snapshotRows.add(row);
        }
        root.add("snapshots", snapshotRows);

        JsonArray candidates = new JsonArray();
        for (SimYsmToggleAnalyzer.Candidate candidate : analysis.candidates()) {
            JsonObject row = new JsonObject();
            row.addProperty("evidenceLevel", candidate.evidenceLevel());
            row.addProperty("stableIdentity", candidate.stableIdentity());
            row.addProperty("path", candidate.path());
            row.addProperty("ownerClass", candidate.ownerClass());
            if (candidate.fieldName() != null) {
                row.addProperty("fieldName", candidate.fieldName());
            }
            if (candidate.containerKey() != null) {
                row.addProperty("containerKey", candidate.containerKey());
            }
            row.addProperty("type", candidate.type());
            row.addProperty("exactVariableIdentity", candidate.exactVariableIdentity());
            JsonArray values = new JsonArray();
            candidate.observedValues().forEach(values::add);
            row.add("observedValues", values);
            candidates.add(row);
        }
        root.add("candidates", candidates);
        return root;
    }

    @Nullable
    private static SimYsmToggleAnalyzer.Candidate uniqueE2Candidate(
            SimYsmToggleAnalyzer.Analysis analysis) {
        SimYsmToggleAnalyzer.Candidate found = null;
        for (SimYsmToggleAnalyzer.Candidate candidate : analysis.candidates()) {
            if (!candidate.exactVariableIdentity()) {
                continue;
            }
            if (found != null) {
                return null;
            }
            found = candidate;
        }
        return found;
    }

    private static boolean registerQualification(
            @Nullable SimYsmToggleAnalyzer.Candidate candidate) {
        if (candidate == null || target == null || variable == null) {
            return false;
        }
        String scopeKey = currentQualificationScope();
        if (scopeKey == null) {
            return false;
        }
        return SimYsmM6QualificationRegistry.qualify(
                scopeKey,
                target.getUUID().toString(),
                variable,
                candidate.stableIdentity());
    }

    @Nullable
    private static String currentQualificationScope() {
        String scenario = System.getProperty(SimLab.PROP_SCENARIO);
        String run = System.getProperty(SimLab.PROP_RUN);
        Minecraft mc = Minecraft.getInstance();
        if (scenario == null || scenario.isBlank()
                || run == null || run.isBlank()
                || mc.level == null) {
            return null;
        }
        return scenario.trim()
                + "|" + run.trim()
                + "|level@" + Integer.toHexString(System.identityHashCode(mc.level));
    }

    private static boolean requestActualServerSequence() {
        if (target == null || variable == null) {
            return false;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.player.connection == null) {
            return false;
        }
        String command = "tlmsimserver m6toggle "
                + target.getUUID() + " " + variable;
        try {
            mc.player.connection.sendCommand(command);
            say(ChatFormatting.GRAY,
                    "[SIM] controlled E2 qualified -> actual packet sequence をserverへ要求: "
                            + command);
            return true;
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error(
                    "[SIM-YSM-PROBE] failed to request actual M6 sequence: {}", command, t);
            return false;
        }
    }

    private static void fail(String message) {
        active = false;
        say(ChatFormatting.RED, "[SIM] YSM controlled probe 失敗: " + message);
        TouhouLittleMaid.LOGGER.error("[SIM-YSM-PROBE] controlled probe failed: {}", message);
        clearTransient();
    }

    private static void clearTransient() {
        target = null;
        variable = null;
        session = null;
        index = 0;
        wait = 0;
        awaitingCapture = false;
        allSnapshotsComplete = true;
        requestActualAfterQualification = false;
        expressions.clear();
        files.clear();
        snapshots.clear();
    }

    private static void say(ChatFormatting color, String message) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(message).withStyle(color), false);
        }
    }
}
