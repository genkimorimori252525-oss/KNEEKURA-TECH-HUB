package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.io.IOException;
import java.util.*;

/** Strict Supervisor-owned linkage. Parsing this grant does not establish authorization/attestation. */
public record KneekuraDebugArenaOwnerGrant(String grantId,KneekuraDebugArenaController.Identity identity,
        String requestHash,int generation,KneekuraDebugArenaController.Arena arena,String dimensionId,String disposableWorldName,
        Map<String,KneekuraDebugArenaController.Subject> subjects,String leaseId,int timeBudgetMs,int maxActions,int maxCaptures,Set<String> allowedActions) {
    public KneekuraDebugArenaOwnerGrant { subjects=Map.copyOf(subjects);allowedActions=Set.copyOf(allowedActions); }
    public static KneekuraDebugArenaOwnerGrant parse(JsonObject g)throws IOException {
        KneekuraDebugActionJournal.keys(g,"schemaVersion","grantId","debugSessionId","runId","runSnapshotId","processEpoch","handshakeNonce","experimentId","requestHash","generation","arenaId","arenaEpoch","expectedArenaRevision","baselineHash","dimensionId","disposableWorldName","bounds","subjects","leaseId","timeBudgetMs","maxActions","maxCaptures","allowedActions");
        if(n(g,"schemaVersion")!=1)throw new IOException("INVALID_GRANT_VERSION");
        String grant=id(g,"grantId"),lease=id(g,"leaseId"),world=t(g,"disposableWorldName");
        if(!world.equals("KNEEKURA_DEBUG_WORLD"))throw new IOException("PRODUCTION_WORLD_FORBIDDEN");
        int process=(int)bounded(g,"processEpoch",1,Integer.MAX_VALUE);
        var identity=new KneekuraDebugArenaController.Identity(id(g,"debugSessionId"),id(g,"runId"),id(g,"runSnapshotId"),process,t(g,"handshakeNonce"),id(g,"experimentId"));
        String requestHash=KneekuraDebugActionJournal.hash(t(g,"requestHash"));int generation=(int)bounded(g,"generation",1,1000000);
        String dimension=t(g,"dimensionId");KneekuraDebugArenaController.resource(dimension);
        JsonObject bounds=KneekuraDebugActionJournal.object(g.get("bounds"));KneekuraDebugActionJournal.keys(bounds,"min","max");
        JsonArray min=KneekuraDebugArenaController.array(bounds.get("min"),3),max=KneekuraDebugArenaController.array(bounds.get("max"),3);
        int[] lo=new int[3],hi=new int[3];for(int i=0;i<3;i++){KneekuraDebugArenaController.number(min.get(i));KneekuraDebugArenaController.number(max.get(i));lo[i]=Math.toIntExact(KneekuraDebugActionJournal.integer(min.get(i)));hi[i]=Math.toIntExact(KneekuraDebugActionJournal.integer(max.get(i)));}
        var box=new KneekuraDebugArenaController.Bounds(lo[0],lo[1],lo[2],hi[0],hi[1],hi[2]);
        var arena=new KneekuraDebugArenaController.Arena(id(g,"arenaId"),n(g,"arenaEpoch"),n(g,"expectedArenaRevision"),KneekuraDebugActionJournal.hash(t(g,"baselineHash")),box);
        if(!g.get("subjects").isJsonArray()||g.getAsJsonArray("subjects").isEmpty()||g.getAsJsonArray("subjects").size()>16)throw new IOException("INVALID_SUBJECTS");
        Map<String,KneekuraDebugArenaController.Subject> subjects=new LinkedHashMap<>();Set<String> uuids=new HashSet<>();
        for(JsonElement e:g.getAsJsonArray("subjects")){JsonObject s=KneekuraDebugActionJournal.object(e);KneekuraDebugActionJournal.keys(s,"subjectId","uuid","entityType");String sid=id(s,"subjectId");var subject=new KneekuraDebugArenaController.Subject(t(s,"uuid"),t(s,"entityType"));if(subject.entityType().equals("minecraft:player"))throw new IOException("PLAYER_SUBJECT_FORBIDDEN");if(subjects.putIfAbsent(sid,subject)!=null||!uuids.add(subject.uuid()))throw new IOException("DUPLICATE_SUBJECT");}
        if(!g.get("allowedActions").isJsonArray())throw new IOException("INVALID_ALLOWED_ACTIONS");Set<String> allowed=new HashSet<>();
        for(JsonElement e:g.getAsJsonArray("allowedActions")){if(!e.isJsonPrimitive()||!e.getAsJsonPrimitive().isString()||!Set.of("wait_ticks","teleport_subject","set_block").contains(e.getAsString())||!allowed.add(e.getAsString()))throw new IOException("BACKEND_UNAVAILABLE");}
        if(n(g,"maxActions")==0&&!allowed.isEmpty())throw new IOException("INVALID_ALLOWED_ACTIONS");
        return new KneekuraDebugArenaOwnerGrant(grant,identity,requestHash,generation,arena,dimension,world,subjects,lease,(int)bounded(g,"timeBudgetMs",1,120000),(int)bounded(g,"maxActions",0,32),(int)bounded(g,"maxCaptures",0,16),allowed);
    }
    private static String t(JsonObject g,String k)throws IOException{return KneekuraDebugArenaController.text(g,k);}
    private static String id(JsonObject g,String k)throws IOException{String s=t(g,k);KneekuraDebugArenaController.id(s);return s;}
    private static long n(JsonObject g,String k)throws IOException{return KneekuraDebugArenaController.integer(g,k);}
    private static long bounded(JsonObject g,String k,long min,long max)throws IOException{long n=n(g,k);KneekuraDebugArenaController.range(n,min,max);return n;}
}
