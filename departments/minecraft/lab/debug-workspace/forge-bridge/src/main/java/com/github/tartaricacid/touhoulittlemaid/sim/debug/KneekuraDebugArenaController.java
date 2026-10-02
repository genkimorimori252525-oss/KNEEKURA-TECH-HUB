package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.IOException;
import java.util.*;
import java.util.function.LongSupplier;

/** One server-thread owner, finite lease, shared durable journal, no request ingress. */
public final class KneekuraDebugArenaController {
    public static final String SCOPE = "BOUNDED_BLOCKS_AND_SUBJECT_POSE";
    private static final Set<String> ACTIONS = Set.of("wait_ticks","teleport_subject","set_block");
    public record Identity(String debugSessionId,String runId,String runSnapshotId,int processEpoch,String handshakeNonce,String experimentId) {
        public Identity { id(debugSessionId);id(runId);id(runSnapshotId);id(experimentId);
            if(processEpoch<1||handshakeNonce==null||handshakeNonce.length()<16||handshakeNonce.length()>128) throw new IllegalArgumentException("INVALID_IDENTITY"); }
    }
    public record Bounds(int minX,int minY,int minZ,int maxX,int maxY,int maxZ) {
        public Bounds { if(minX < -30000000 || maxX > 30000000 || minZ < -30000000 || maxZ > 30000000 || minY < -64 || maxY > 320 ||
                maxX<=minX||maxY<=minY||maxZ<=minZ||maxX-minX>64||maxY-minY>64||maxZ-minZ>64||
                (long)(maxX-minX)*(maxY-minY)*(maxZ-minZ)>4096) throw new IllegalArgumentException("INVALID_BACKEND_BOUNDS"); }
        public boolean contains(double x,double y,double z) { return Double.isFinite(x)&&Double.isFinite(y)&&Double.isFinite(z)&&x>=minX&&x<maxX&&y>=minY&&y<maxY&&z>=minZ&&z<maxZ; }
    }
    public record Subject(String uuid,String entityType) {
        public Subject { if(uuid==null||!uuid.matches("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")||!UUID.fromString(uuid).toString().equals(uuid)) throw new IllegalArgumentException("INVALID_UUID"); resource(entityType); }
    }
    public record Arena(String arenaId,long arenaEpoch,long arenaRevision,String baselineHash,Bounds bounds) {
        public Arena { id(arenaId); safe(arenaEpoch);safe(arenaRevision);if(baselineHash==null||!baselineHash.matches("[a-f0-9]{64}")||bounds==null)throw new IllegalArgumentException("INVALID_ARENA"); }
    }
    public record Lease(String leaseId,Identity identity,long issuedNanos,long deadlineNanos,int maxActions,Set<String> allowedActions) {
        public Lease { id(leaseId); Objects.requireNonNull(identity); allowedActions=Set.copyOf(allowedActions);
            long duration=deadlineNanos-issuedNanos;if(duration<=0||duration>120_000_000_000L||maxActions<0||maxActions>32||(maxActions==0&&!allowedActions.isEmpty())||!ACTIONS.containsAll(allowedActions)) throw new IllegalArgumentException("INVALID_LEASE"); }
    }
    public record Command(JsonObject action,String handshakeNonce,String leaseId) {
        public Command { action=Objects.requireNonNull(action).deepCopy(); }
        @Override public JsonObject action() { return action.deepCopy(); }
    }
    public record Snapshot(Identity identity,String arenaId,long arenaEpoch,long arenaRevision,String leaseId,boolean idle,boolean unsafe) { }
    public record Result(String status,String classification,long arenaEpoch,long arenaRevision,String error) { }
    public interface Backend {
        void requireOwnerThread() throws IOException;
        void guard() throws IOException;
        void preflight(JsonObject action) throws IOException;
        JsonObject apply(JsonObject action) throws IOException;
        String stateHash() throws IOException;
        void restoreBaseline() throws IOException;
        /** Returns hash only after this exact observation is persisted durably in the existing writer. */
        String observe(long epoch,long tick,String kind,JsonObject payload) throws IOException;
    }
    private final Identity identity; private Arena arena; private final Lease lease; private final Map<String,Subject> subjects;
    private final Backend backend; private final KneekuraDebugActionJournal journal; private final LongSupplier clock;
    private boolean unsafe; private int acceptedActions; private int cleanupResets; private Pending pending;
    private record Pending(Command command,KneekuraDebugActionJournal.Handle handle,long startTick,long lastTick,int ticks) { }
    public KneekuraDebugArenaController(Identity identity,Arena arena,Lease lease,Map<String,Subject> subjects,Backend backend,KneekuraDebugActionJournal journal,LongSupplier monotonicClock) throws IOException {
        this.identity=Objects.requireNonNull(identity);this.arena=Objects.requireNonNull(arena);this.lease=Objects.requireNonNull(lease);
        this.subjects=Map.copyOf(subjects);this.backend=Objects.requireNonNull(backend);this.journal=Objects.requireNonNull(journal);this.clock=Objects.requireNonNull(monotonicClock);
        if(!identity.equals(lease.identity())||subjects.size()>16||new HashSet<>(subjects.values().stream().map(Subject::uuid).toList()).size()!=subjects.size())throw new IllegalArgumentException("OWNER_IDENTITY_MISMATCH");
        subjects.keySet().forEach(KneekuraDebugArenaController::id); checkLease();backend.guard();
        if(!arena.baselineHash().equals(backend.stateHash()))throw new IOException("ARENA_BASELINE_MISMATCH");
    }
    public Snapshot snapshot(){ return new Snapshot(identity,arena.arenaId(),arena.arenaEpoch(),arena.arenaRevision(),lease.leaseId(),pending==null,unsafe); }
    public void validateLeaseAndRevision(Snapshot expected) throws IOException {
        backend.guard();checkLease();if(unsafe||pending!=null||!snapshot().equals(expected))throw new IOException("ARENA_CONTEXT_CHANGED");
    }
    public void requireLeaseRemaining(Snapshot expected,long minRemainingMs)throws IOException {
        validateLeaseAndRevision(expected);if(minRemainingMs<0||minRemainingMs>120000||lease.deadlineNanos()-clock.getAsLong()<minRemainingMs*1_000_000L)throw new IOException("INSUFFICIENT_CAPTURE_LEASE_REMAINING");
    }
    public Result submit(Command command,long tick) throws IOException { return execute(command,tick,false); }
    /** Source-owner reset, not a TECH action or command channel. */
    public Result reset(Command command,long tick) throws IOException { return execute(command,tick,true); }
    private Result execute(Command command,long tick,boolean reset) throws IOException {
        backend.guard();checkLease();if(tick<0)throw new IOException("INVALID_SERVER_TICK");
        JsonObject action=command.action();validateBase(command,action,reset);
        String previous;
        if(reset) journal.reserveOwnerReset(action);
        try { previous=journal.lookup(action); } catch(IOException e) { unsafe=true;throw e; }
        if(!"REQUESTED".equals(previous)) { if("OUTCOME_UNKNOWN".equals(previous))unsafe=true;return result(previous,null); }
        if(unsafe&&!reset)throw new IOException("ARENA_UNSAFE");if(pending!=null)throw new IOException("ARENA_BUSY");
        if(reset ? cleanupResets>=1 : acceptedActions>=lease.maxActions())throw new IOException(reset?"CLEANUP_RESET_BUDGET_EXHAUSTED":"ACTION_BUDGET_EXHAUSTED");
        if(integer(action,"arenaEpoch")!=arena.arenaEpoch())throw new IOException("STALE_COMMAND_REJECTED");
        if(integer(action,"expectedArenaRevision")!=arena.arenaRevision())throw new IOException("ARENA_REVISION_CONFLICT");
        if(arena.arenaRevision()>=9007199254740991L||(reset&&arena.arenaEpoch()>=9007199254740991L))throw new IOException("ARENA_COUNTER_EXHAUSTED");
        backend.preflight(action);checkLease();
        var acceptance=journal.accept(action);
        if(!"ACCEPTED".equals(acceptance.status())||acceptance.handle()==null)return result(acceptance.status(),null);
        if(reset)cleanupResets++;else acceptedActions++;var handle=acceptance.handle();
        if(action.get("type").getAsString().equals("wait_ticks")) {
            pending=new Pending(command,handle,tick,tick,(int)integer(action.getAsJsonObject("args"),"ticks"));return result("ACCEPTED",null);
        }
        try {
            checkLease();backend.guard();
            JsonObject measured;
            if(reset) { backend.restoreBaseline();measured=new JsonObject();String hash=backend.stateHash();measured.addProperty("measuredBaselineHash",hash);
                if(!hash.equals(arena.baselineHash()))throw new IOException("ARENA_NOT_CLEAN");measured.addProperty("supportedScopeBaselineMatch",true); }
            else { measured=backend.apply(action);if(!measured.has("postconditionMatched")||!measured.get("postconditionMatched").getAsBoolean())throw new IOException("POSTCONDITION_MISMATCH"); }
            finish(command,handle,tick,measured,reset);
            return result("VERIFIED",null);
        } catch(Exception e) { return unknown(handle,e); }
        finally { handle.close(); }
    }
    public Result onTick(long tick) throws IOException {
        if(pending==null){backend.guard();return result(unsafe?"OUTCOME_UNKNOWN":"IDLE",null);}
        Pending p=pending;
        try {
            backend.guard();checkLease();if(tick!=p.lastTick()+1)throw new IOException("SERVER_TICK_DISCONTINUITY");
            backend.preflight(p.command().action());
            if(tick-p.startTick()<p.ticks()) { pending=new Pending(p.command(),p.handle(),p.startTick(),tick,p.ticks());return result("ACCEPTED",null); }
            JsonObject measured=new JsonObject();measured.addProperty("elapsedServerTicks",tick-p.startTick());measured.addProperty("postconditionMatched",true);
            finish(p.command(),p.handle(),tick,measured,false);pending=null;p.handle().close();return result("VERIFIED",null);
        } catch(Exception e) { pending=null;Result result=unknown(p.handle(),e);p.handle().close();return result; }
    }
    public void revoke() throws IOException {
        backend.requireOwnerThread();unsafe=true;if(pending!=null){ Pending p=pending;pending=null;unknown(p.handle(),new IOException("OWNER_UNINSTALLED"));p.handle().close(); }
    }
    private void finish(Command c,KneekuraDebugActionJournal.Handle handle,long tick,JsonObject measured,boolean reset) throws IOException {
        checkLease();backend.guard();JsonObject payload=measured.deepCopy();payload.addProperty("scope",SCOPE);payload.addProperty("actionId",c.action().get("actionId").getAsString());
        payload.addProperty("idempotencyKey",c.action().get("idempotencyKey").getAsString());payload.addProperty("leaseId",lease.leaseId());payload.addProperty("arenaId",arena.arenaId());
        payload.addProperty("beforeEpoch",arena.arenaEpoch());payload.addProperty("beforeRevision",arena.arenaRevision());
        boolean mutation=!c.action().get("type").getAsString().equals("wait_ticks");
        long epoch=arena.arenaEpoch()+(reset?1:0),revision=arena.arenaRevision()+(mutation?1:0);
        payload.addProperty("afterEpoch",epoch);payload.addProperty("afterRevision",revision);
        payload.addProperty("classification","INCONCLUSIVE");payload.add("resetClasses",resetClasses());
        String hash=KneekuraDebugActionJournal.hash(backend.observe(epoch,tick,reset?"ARENA_RESET":"ACTION_APPLIED",payload));
        checkLease();backend.guard();handle.append("APPLIED",List.of(hash));checkLease();backend.guard();handle.append("VERIFIED",List.of(hash));
        arena=new Arena(arena.arenaId(),epoch,revision,arena.baselineHash(),arena.bounds());
    }
    private Result unknown(KneekuraDebugActionJournal.Handle handle,Exception error) {
        unsafe=true;try { handle.append("OUTCOME_UNKNOWN",List.of()); }catch(Exception suppressed){error.addSuppressed(suppressed);}
        return result("OUTCOME_UNKNOWN",error.getMessage());
    }
    private Result result(String status,String error){ return new Result(status,"INCONCLUSIVE",arena.arenaEpoch(),arena.arenaRevision(),error); }
    private void checkLease() throws IOException { long elapsed=clock.getAsLong()-lease.issuedNanos();if(elapsed<0||elapsed>=lease.deadlineNanos()-lease.issuedNanos())throw new IOException("LEASE_EXPIRED_OR_CLOCK_CHANGED"); }
    private void validateBase(Command command,JsonObject action,boolean reset) throws IOException {
        KneekuraDebugActionJournal.keys(action,"schemaVersion","debugSessionId","runId","runSnapshotId","processEpoch","arenaId","arenaEpoch","expectedArenaRevision","experimentId","actionId","idempotencyKey","type","args");
        if(integer(action,"schemaVersion")!=1||!identity.debugSessionId().equals(text(action,"debugSessionId"))||!identity.runId().equals(text(action,"runId"))||!identity.runSnapshotId().equals(text(action,"runSnapshotId"))||identity.processEpoch()!=integer(action,"processEpoch")||!identity.experimentId().equals(text(action,"experimentId"))||!identity.handshakeNonce().equals(command.handshakeNonce())||!lease.leaseId().equals(command.leaseId())||!arena.arenaId().equals(text(action,"arenaId")))throw new IOException("ACTION_IDENTITY_MISMATCH");
        id(text(action,"actionId"));id(text(action,"idempotencyKey"));safe(integer(action,"arenaEpoch"));safe(integer(action,"expectedArenaRevision"));
        String type=text(action,"type");JsonObject args=KneekuraDebugActionJournal.object(action.get("args"));
        if(reset){if(!type.equals("reset_arena"))throw new IOException("OWNER_RESET_ONLY");KneekuraDebugActionJournal.keys(args);return;}
        if(!lease.allowedActions().contains(type))throw new IOException("BACKEND_UNAVAILABLE");
        switch(type){
            case "wait_ticks" -> { KneekuraDebugActionJournal.keys(args,"ticks");range(integer(args,"ticks"),1,1200); }
            case "set_block" -> { KneekuraDebugActionJournal.keys(args,"position","block");position(args.get("position"),true);String block=text(args,"block");if(!Set.of("minecraft:air","minecraft:stone","minecraft:glass","minecraft:barrier").contains(block))throw new IOException("BLOCK_BACKEND_UNAVAILABLE"); }
            case "teleport_subject" -> { KneekuraDebugActionJournal.keys(args,"subject_id","position","rotation");if(!subjects.containsKey(text(args,"subject_id")))throw new IOException("UNKNOWN_SUBJECT");position(args.get("position"),false);
                JsonArray rotation=array(args.get("rotation"),2);double yaw=number(rotation.get(0)),pitch=number(rotation.get(1));if(yaw < -180||yaw >180||pitch < -90||pitch >90)throw new IOException("INVALID_ROTATION"); }
            default -> throw new IOException("BACKEND_UNAVAILABLE");
        }
    }
    private void position(JsonElement e,boolean integer) throws IOException { JsonArray a=array(e,3);double x=number(a.get(0)),y=number(a.get(1)),z=number(a.get(2));if(!arena.bounds().contains(x,y,z))throw new IOException("ACTION_OUT_OF_BOUNDS");if(integer&&(x!=Math.rint(x)||y!=Math.rint(y)||z!=Math.rint(z)))throw new IOException("BLOCK_INTEGER_REQUIRED"); }
    static JsonArray array(JsonElement e,int size)throws IOException {if(e==null||!e.isJsonArray()||e.getAsJsonArray().size()!=size)throw new IOException("INVALID_VECTOR");return e.getAsJsonArray();}
    static double number(JsonElement e)throws IOException {if(e==null||!e.isJsonPrimitive()||!e.getAsJsonPrimitive().isNumber())throw new IOException("NUMBER_REQUIRED");double n=e.getAsDouble();if(!Double.isFinite(n)||Math.abs(n)>9007199254740991D)throw new IOException("INVALID_NUMBER");return n;}
    static long integer(JsonObject o,String key)throws IOException {JsonElement e=o.get(key);number(e);return KneekuraDebugActionJournal.integer(e);}
    static String text(JsonObject o,String key)throws IOException {JsonElement e=o.get(key);if(e==null||!e.isJsonPrimitive()||!e.getAsJsonPrimitive().isString())throw new IOException("STRING_REQUIRED");return e.getAsString();}
    static void range(long n,long min,long max)throws IOException {if(n<min||n>max)throw new IOException("INTEGER_RANGE");}
    static void safe(long n){if(n<0||n>9007199254740991L)throw new IllegalArgumentException("INVALID_SAFE_INTEGER");}
    static void id(String s){if(s==null||!s.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"))throw new IllegalArgumentException("INVALID_IDENTIFIER");}
    static void resource(String s){if(s==null||s.length()>128||!s.matches("[a-z0-9_]+:[a-z0-9_./-]+")||Arrays.stream(s.substring(s.indexOf(':')+1).split("/",-1)).anyMatch(p->p.isEmpty()||p.equals(".")||p.equals("..")))throw new IllegalArgumentException("INVALID_RESOURCE");}
    public static JsonObject resetClasses(){JsonObject c=new JsonObject();c.addProperty("blocks","RESETTABLE");c.addProperty("block_entities","EXTERNAL");c.addProperty("entities","UNKNOWN");c.addProperty("effects","UNKNOWN");c.addProperty("target_state","UNKNOWN");c.addProperty("scheduled_ticks","EXTERNAL");c.addProperty("game_rules","EXTERNAL");c.addProperty("time_weather","EXTERNAL");c.addProperty("chunk_tickets","EXTERNAL");c.addProperty("probe_state","PERSISTENT_BY_DESIGN");return c;}
}
