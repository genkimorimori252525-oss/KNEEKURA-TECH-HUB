package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.sim.SimLab;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;
import net.minecraftforge.fml.loading.FMLPaths;

import javax.annotation.Nullable;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.regex.Pattern;

/**
 * Writes discovery-only YSM scalar snapshots for controlled Molang differential probing.
 *
 * <p>This is deliberately not an M6 producer. A snapshot proves only that scalar state was readable
 * at a runtime location. Repeated controlled mutation and variable identity must be established
 * later before any {@code ysm_molang_state_applied} semantic milestone is emitted.
 *
 * <p>Normal play is unaffected: both {@code tlm.sim.scenario} and {@code tlm.sim.run} must be
 * explicitly present before any artifact can be written.
 */
@OnlyIn(Dist.CLIENT)
public final class SimYsmMolangStateProbe {
    public static final int FORMAT_VERSION = 1;
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Pattern SAFE_SEGMENT = Pattern.compile("[^A-Za-z0-9._-]");
    private static final Pattern DOTS_ONLY = Pattern.compile("\\.+");
    private static final int RUN_MAX_LENGTH = 64;
    private static final int LABEL_MAX_LENGTH = 80;
    private static final DateTimeFormatter STAMP = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss-SSS");

    private SimYsmMolangStateProbe() {}

    public record CaptureResult(
            boolean ok,
            String message,
            @Nullable Path file,
            boolean complete,
            int scalarCount
    ) {}

    record DetailedCapture(
            CaptureResult result,
            @Nullable SimYsmScalarProbe.Snapshot snapshot
    ) {}

    public static CaptureResult capture(@Nullable String label) {
        return captureDetailed(label).result();
    }

    /**
     * Same on-disk capture as {@link #capture}, while retaining the exact in-memory snapshot used
     * for that artifact. Package-private so the controlled toggle driver can analyze the four
     * written artifacts without performing a second, potentially different graph scan.
     */
    static DetailedCapture captureDetailed(@Nullable String label) {
        return captureDetailed(label, null);
    }

    /**
     * Controlled-probe overload: resolve the artifact from the already-selected maid instead of
     * re-running nearest-entity selection at each sample.
     */
    static DetailedCapture captureDetailed(
            @Nullable String label, @Nullable EntityMaid selectedMaid) {
        Identity identity = identity();
        if (identity == null) {
            return new DetailedCapture(
                    new CaptureResult(
                            false,
                            "tlm.sim.scenario と tlm.sim.run の両方を明示した SimLab run でのみ使用できる",
                            null,
                            false,
                            0),
                    null);
        }

        SimYsmRuntimeRoot.Result runtime = selectedMaid == null
                ? SimYsmRuntimeRoot.findNearestReimu()
                : SimYsmRuntimeRoot.findForMaid(selectedMaid);
        if (!runtime.ok() || runtime.root() == null || runtime.maid() == null) {
            return new DetailedCapture(
                    new CaptureResult(false, runtime.message(), null, false, 0),
                    null);
        }

        SimYsmScalarProbe.Snapshot snapshot = SimYsmScalarProbe.snapshot(runtime.root());
        String rawLabel = label == null || label.isBlank() ? "snapshot" : label.trim();
        long observedGameTime = gameTime();

        Path dir = outputRoot()
                .resolve(safeSegment(identity.scenario(), "scenario", LABEL_MAX_LENGTH))
                .resolve("_ysmprobe")
                .resolve(identity.run());
        String fileName = LocalDateTime.now().format(STAMP)
                + "-gt" + observedGameTime
                + "-" + safeSegment(rawLabel, "snapshot", LABEL_MAX_LENGTH)
                + ".ysmprobe.json";
        Path file = dir.resolve(fileName);

        try {
            Files.createDirectories(dir);
            JsonObject root = toJson(identity, rawLabel, observedGameTime, runtime, snapshot);
            writeArtifact(file, root);
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM-YSM-PROBE] snapshot write failed: {}", file, t);
            return new DetailedCapture(
                    new CaptureResult(
                            false,
                            "YSM scalar snapshot の書き出しに失敗: " + t,
                            null,
                            snapshot.complete(),
                            snapshot.scalars().size()),
                    snapshot);
        }

        String completeness = snapshot.complete() ? "complete" : "incomplete";
        String message = "YSM scalar snapshot: " + snapshot.scalars().size()
                + " scalars / " + completeness + " -> " + file;
        TouhouLittleMaid.LOGGER.info("[SIM-YSM-PROBE] {}", message);
        return new DetailedCapture(
                new CaptureResult(true, message, file, snapshot.complete(), snapshot.scalars().size()),
                snapshot);
    }

    private static JsonObject toJson(
            Identity identity,
            String label,
            long observedGameTime,
            SimYsmRuntimeRoot.Result runtime,
            SimYsmScalarProbe.Snapshot snapshot) {
        JsonObject root = new JsonObject();
        root.addProperty("v", FORMAT_VERSION);
        root.addProperty("ch", "ysm_probe_snapshot");
        root.addProperty("note",
                "discovery only; this artifact is not OBSERVED_YSM_MOLANG_STATE_APPLIED and does not prove M6");
        root.addProperty("scenario", identity.scenario());
        root.addProperty("run", identity.run());
        root.addProperty("label", label);
        root.addProperty("gameTime", observedGameTime);

        EntityMaid maid = runtime.maid();
        root.addProperty("entityId", maid == null ? -1 : maid.getId());
        if (maid != null) {
            root.addProperty("entityUuid", maid.getUUID().toString());
        }
        root.addProperty("rootRoute", runtime.route());
        root.addProperty("rootRouteNote", runtime.routeNote());
        root.addProperty("rootClass", runtime.root() == null ? "" : runtime.root().getClass().getName());

        JsonArray hashes = new JsonArray();
        for (String hash : SimBoneProbeHashes.modJarHashes()) {
            hashes.add(hash);
        }
        root.add("modJarHashes", hashes);

        root.addProperty("scalarCount", snapshot.scalars().size());
        root.addProperty("scanComplete", snapshot.complete());
        root.addProperty("negative", snapshot.negative());
        root.addProperty("negativeConclusive", snapshot.conclusiveNegative());
        root.addProperty("visited", snapshot.visited());
        root.addProperty("depthReached", snapshot.depthReached());
        root.addProperty("truncatedContainers", snapshot.truncatedContainers());
        root.addProperty("depthBudgetExhausted", snapshot.depthBudgetExhausted());
        root.addProperty("visitBudgetExhausted", snapshot.visitBudgetExhausted());

        JsonArray scalars = new JsonArray();
        for (SimYsmScalarProbe.Scalar scalar : snapshot.scalars()) {
            JsonObject s = new JsonObject();
            s.addProperty("path", scalar.path());
            s.addProperty("ownerClass", scalar.ownerClass());
            if (scalar.fieldName() != null) {
                s.addProperty("fieldName", scalar.fieldName());
            }
            if (scalar.containerKey() != null) {
                s.addProperty("containerKey", scalar.containerKey());
                s.addProperty("containerKeyTruncated", scalar.containerKeyTruncated());
            }
            s.addProperty("type", scalar.type());
            s.addProperty("value", scalar.value());
            s.addProperty("valueTruncated", scalar.valueTruncated());
            s.addProperty("comparable", scalar.comparable());
            if (scalar.comparable()) {
                s.addProperty("stableIdentity", scalar.stableIdentity());
            }
            scalars.add(s);
        }
        root.add("scalars", scalars);
        return root;
    }

    @Nullable
    private static Identity identity() {
        String rawScenario = System.getProperty(SimLab.PROP_SCENARIO);
        String rawRun = System.getProperty(SimLab.PROP_RUN);
        if (rawScenario == null || rawScenario.isBlank() || rawRun == null || rawRun.isBlank()) {
            return null;
        }

        String run = sanitizeRun(rawRun);
        if (run == null) {
            return null;
        }
        return new Identity(rawScenario.trim(), run);
    }

    @Nullable
    static String sanitizeRun(String raw) {
        String trimmed = raw == null ? "" : raw.trim();
        String sanitized = SAFE_SEGMENT.matcher(trimmed).replaceAll("_");
        if (sanitized.length() > RUN_MAX_LENGTH) {
            sanitized = sanitized.substring(0, RUN_MAX_LENGTH);
        }
        if (sanitized.isEmpty() || DOTS_ONLY.matcher(sanitized).matches()) {
            return null;
        }
        return sanitized;
    }

    private static String safeSegment(String raw, String fallback, int maxLength) {
        String sanitized = SAFE_SEGMENT.matcher(raw == null ? "" : raw.trim()).replaceAll("_");
        if (sanitized.length() > maxLength) {
            sanitized = sanitized.substring(0, maxLength);
        }
        if (sanitized.isEmpty() || DOTS_ONLY.matcher(sanitized).matches()) {
            return fallback;
        }
        return sanitized;
    }

    private static Path outputRoot() {
        String explicit = System.getProperty(SimLab.PROP_OUT);
        if (explicit != null && !explicit.isBlank()) {
            return Path.of(explicit);
        }
        return FMLPaths.GAMEDIR.get().resolve("simlab-out");
    }

    private static long gameTime() {
        Minecraft mc = Minecraft.getInstance();
        return mc.level == null ? -1L : mc.level.getGameTime();
    }

    static void writeArtifact(Path file, JsonObject root) throws Exception {
        writeAtomically(file, GSON.toJson(root));
    }

    private static void writeAtomically(Path file, String content) throws Exception {
        Path tmp = file.resolveSibling(file.getFileName() + ".tmp");
        Files.writeString(tmp, content, StandardCharsets.UTF_8);
        try {
            Files.move(tmp, file, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } catch (AtomicMoveNotSupportedException ignored) {
            Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private record Identity(String scenario, String run) {}
}
