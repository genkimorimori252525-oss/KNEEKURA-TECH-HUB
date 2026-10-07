package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.UUID;

/** Pure bounded capture protocol. The Forge owner alone supplies observed barrier/restoration facts. */
public final class KneekuraDebugCaptureSession {
    public static final List<String> VIEWS = List.of("north", "east", "south", "west");
    public static final String RIG = "cardinal-4-snapshot-v1";
    public static final String TANK_RIG = "tank-cardinal-4-snapshot-v2";
    public static final int MAX_PNG_BYTES = 4 * 1024 * 1024;
    public record Identity(String debugSessionId, String runId, String runSnapshotId,
                           int processEpoch, String experimentId, int generation,
                           String requestHash, String arenaId, long arenaEpoch,
                           long arenaRevision, String baselineHash) {
        public Identity {
            id(debugSessionId); id(runId); id(runSnapshotId); id(experimentId); id(arenaId);
            hash(requestHash); hash(baselineHash);
            require(processEpoch > 0 && generation > 0 && generation <= 1_000_000,
                    "INVALID_GENERATION");
            require(arenaEpoch >= 0 && arenaEpoch <= 9_007_199_254_740_991L &&
                    arenaRevision >= 0 && arenaRevision <= 9_007_199_254_740_991L, "INVALID_ARENA_EPOCH");
        }
    }
    public record Request(String captureId, Identity identity, List<UUID> subjects,
                          List<String> behaviorAssertionIds, List<Integer> arenaMin,
                          List<Integer> arenaMax, double fov, int width, int height,
                          long barrierBudgetMs, long totalBudgetMs,
                          boolean allowPause, boolean allowCameraTakeover,
                          String rig, String tankObservationHash, List<Integer> observationMin, List<Integer> observationMax) {
        public Request(String captureId, Identity identity, List<UUID> subjects, List<String> behaviorAssertionIds,
                       List<Integer> arenaMin, List<Integer> arenaMax, double fov, int width, int height,
                       long barrierBudgetMs, long totalBudgetMs, boolean allowPause, boolean allowCameraTakeover) {
            this(captureId,identity,subjects,behaviorAssertionIds,arenaMin,arenaMax,fov,width,height,barrierBudgetMs,totalBudgetMs,allowPause,allowCameraTakeover,RIG,null,List.of(),List.of());
        }
        public Request {
            id(captureId);
            require(captureId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"), "SAFE_CAPTURE_ID_REQUIRED");
            require(identity != null, "MISSING_IDENTITY");
            subjects = List.copyOf(subjects);
            behaviorAssertionIds = List.copyOf(behaviorAssertionIds);
            arenaMin = List.copyOf(arenaMin); arenaMax = List.copyOf(arenaMax);
            require(!subjects.isEmpty() && subjects.size() <= 16 &&
                    new HashSet<>(subjects).size() == subjects.size(), "INVALID_SUBJECTS");
            require(behaviorAssertionIds.size() <= 32 &&
                    new HashSet<>(behaviorAssertionIds).size() == behaviorAssertionIds.size(), "INVALID_ASSERTIONS");
            behaviorAssertionIds.forEach(KneekuraDebugCaptureSession::id);
            require(arenaMin.size() == 3 && arenaMax.size() == 3, "INVALID_BOUNDS");
            for (int i = 0; i < 3; i++) {
                long edge = (long) arenaMax.get(i) - arenaMin.get(i);
                require(Math.abs((long) arenaMin.get(i)) <= 30_000_000 &&
                        Math.abs((long) arenaMax.get(i)) <= 30_000_000 && edge > 0 && edge <= 64,
                        "INVALID_BOUNDS");
            }
            require(arenaMin.get(1) >= -64 && arenaMax.get(1) <= 320, "INVALID_HEIGHT");
            require(Double.isFinite(fov) && fov >= 30 && fov <= 100 &&
                    width >= 64 && width <= 2048 && height >= 64 && height <= 2048, "INVALID_RIG");
            require(barrierBudgetMs >= 100 && barrierBudgetMs <= 2000 &&
                    totalBudgetMs >= barrierBudgetMs && totalBudgetMs <= 5000, "INVALID_BUDGET");
            require(allowPause && allowCameraTakeover, "CAPTURE_PERTURBATION_NOT_AUTHORIZED");
            require(RIG.equals(rig)||TANK_RIG.equals(rig),"INVALID_RIG_VERSION");
            observationMin=List.copyOf(observationMin);observationMax=List.copyOf(observationMax);
            if(TANK_RIG.equals(rig)){
                hash(tankObservationHash);require(observationMin.size()==3&&observationMax.size()==3,"INVALID_OBSERVATION_BOUNDS");
                long volume=1;for(int i=0;i<3;i++){long edge=(long)observationMax.get(i)-observationMin.get(i);require(edge>0&&edge<=64&&Math.abs((long)observationMin.get(i))<=30000000&&Math.abs((long)observationMax.get(i))<=30000000,"INVALID_OBSERVATION_BOUNDS");volume*=edge;}
                require(volume<=65536&&observationMin.get(1)>=-63&&observationMax.get(1)<=319,"INVALID_OBSERVATION_BOUNDS");
                require(observationMax.get(0)-observationMin.get(0)>3&&observationMax.get(2)-observationMin.get(2)>3,"OBSERVATION_ROOM_TOO_SMALL");
            }else require(tankObservationHash==null&&observationMin.isEmpty()&&observationMax.isEmpty(),"LEGACY_RIG_SCOPE_CONFLICT");
        }
        /** Deterministic [x,y,z,yaw,pitch] around the exact half-open Arena bounds. */
        public List<Double> pose(String view) {
            int index = VIEWS.indexOf(view);
            require(index >= 0, "INVALID_VIEW");
            if(TANK_RIG.equals(rig)){
                double x=((double)observationMin.get(0)+observationMax.get(0))/2,y=((double)observationMin.get(1)+observationMax.get(1))/2,z=((double)observationMin.get(2)+observationMax.get(2))/2;
                return List.of(index==1?observationMax.get(0)-1.5:index==3?observationMin.get(0)+1.5:x,y,index==0?observationMin.get(2)+1.5:index==2?observationMax.get(2)-1.5:z,index==3?-90.0:index*90.0,0.0);
            }
            double x = ((double) arenaMin.get(0) + arenaMax.get(0)) / 2;
            double y = ((double) arenaMin.get(1) + arenaMax.get(1)) / 2;
            double z = ((double) arenaMin.get(2) + arenaMax.get(2)) / 2;
            double radius = Math.max(arenaMax.get(0) - arenaMin.get(0),
                    arenaMax.get(2) - arenaMin.get(2)) * 1.5 + 2;
            double elevation = Math.max(2, (arenaMax.get(1) - arenaMin.get(1)) * .25);
            return List.of(x + (index == 1 ? radius : index == 3 ? -radius : 0),
                    y + elevation, z + (index == 0 ? -radius : index == 2 ? radius : 0),
                    index == 3 ? -90.0 : index * 90.0, Math.toDegrees(Math.atan2(elevation, radius)));
        }
    }
    public record Frame(String view, String status, Long renderFrame, String imageHash, String observationHash) {}
    public record Result(String status, boolean sameFrame, String restoration,
                         List<String> perturbations, List<String> invalidatedAssertions,
                         List<Frame> frames, List<String> gaps) {}

    private final Request request;
    private final long startedMs;
    private final List<Frame> frames = new ArrayList<>();
    private final List<String> gaps = new ArrayList<>();
    private boolean acquired;
    private boolean restorationAttempted;
    private boolean restorationExact;
    private boolean terminal;
    private long acquiredMs;
    private long serverTick = -1;
    private long serverGameTime = -1;
    private String stateHash;
    private Result finalResult;

    public KneekuraDebugCaptureSession(Request request, long startedMs) {
        require(request != null && startedMs >= 0, "INVALID_SESSION");
        this.request = request; this.startedMs = startedMs;
    }
    public Request request() { return request; }
    public long serverTick() { return serverTick; }
    public long serverGameTime() { return serverGameTime; }
    public String stateHash() { return stateHash; }
    public int nextViewIndex() { return frames.size(); }
    public boolean isTerminal() { return terminal; }
    public void acquire(long nowMs, long tick, long gameTime, String hash) {
        require(!terminal && !acquired && tick >= 0 && gameTime >= 0, "BARRIER_STATE");
        hash(hash);
        require(nowMs >= startedMs && nowMs - startedMs < request.totalBudgetMs(), "DEADLINE_EXPIRED");
        acquired = true; acquiredMs = nowMs; serverTick = tick; serverGameTime = gameTime; stateHash = hash;
    }
    public boolean expired(long nowMs, boolean barrierHeld) {
        return nowMs < startedMs || nowMs - startedMs >= request.totalBudgetMs() ||
                (barrierHeld && acquired && nowMs - acquiredMs >= request.barrierBudgetMs());
    }
    public void frame(String view, long renderFrame, String imageHash) {
        require(acquired && !terminal && !restorationAttempted && frames.size() < 4 &&
                VIEWS.get(frames.size()).equals(view) && renderFrame >= 0, "FRAME_ORDER");
        hash(imageHash);
        require(frames.isEmpty() || frames.get(frames.size() - 1).renderFrame() < renderFrame,
                "SEQUENTIAL_FRAME_REQUIRED");
        frames.add(new Frame(view, "WRITE_PENDING", renderFrame, imageHash, null));
    }
    public void durable(String view, String observationHash) {
        hash(observationHash);
        if (terminal) return; // Completion after timeout is historical, never adopted automatically.
        int index = VIEWS.indexOf(view);
        require(index >= 0 && index < frames.size(), "UNREQUESTED_FRAME");
        Frame frame = frames.get(index);
        require(frame.status().equals("WRITE_PENDING"), "DUPLICATE_FRAME_ACK");
        frames.set(index, new Frame(view, "PRESENT", frame.renderFrame(), frame.imageHash(), observationHash));
    }
    public void restored(boolean exact) {
        require(!restorationAttempted, "RESTORE_ALREADY_ATTEMPTED");
        restorationAttempted = true; restorationExact = exact;
        if (!exact) gaps.add("RESTORATION_FAILED");
    }
    public void abort(String reason) {
        id(reason);
        if (terminal) return;
        gaps.add(reason);
        terminal = true;
    }
    public boolean readyToFinish() {
        return restorationAttempted && (terminal || !restorationExact ||
                (frames.size() == 4 && frames.stream().allMatch(f -> f.status().equals("PRESENT"))));
    }
    public Result finish(long nowMs) {
        if (finalResult != null) return finalResult;
        if (!restorationAttempted) {
            gaps.add("RESTORATION_NOT_ESTABLISHED");
        }
        if (expired(nowMs, false) && !gaps.contains("DEADLINE_EXPIRED")) gaps.add("DEADLINE_EXPIRED");
        List<Frame> finalFrames = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            if (i >= frames.size()) finalFrames.add(new Frame(VIEWS.get(i), "MISSING", null, null, null));
            else {
                Frame frame = frames.get(i);
                finalFrames.add(frame.status().equals("WRITE_PENDING") ?
                        new Frame(frame.view(), "WRITE_UNKNOWN", frame.renderFrame(), frame.imageHash(), null) : frame);
            }
        }
        boolean complete = acquired && !terminal && gaps.isEmpty() && restorationExact &&
                finalFrames.stream().allMatch(f -> f.status().equals("PRESENT"));
        terminal = true;
        finalResult = new Result(!restorationExact ? "UNKNOWN" : complete ? "COMPLETE" : "PARTIAL",
                false, restorationExact ? "RESTORED" : "UNKNOWN",
                List.of("SERVER_TICK_HOLD", "CLIENT_PAUSE", "CAMERA_TAKEOVER", "RENDER_ELIGIBILITY_CHANGED"),
                request.behaviorAssertionIds(), List.copyOf(finalFrames), List.copyOf(gaps));
        return finalResult;
    }
    public static void id(String value) {
        require(value != null && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,159}"), "INVALID_ID");
    }
    public static void hash(String value) {
        require(value != null && value.matches("[a-f0-9]{64}"), "INVALID_HASH");
    }
    private static void require(boolean condition, String reason) {
        if (!condition) throw new IllegalArgumentException(reason);
    }
}
