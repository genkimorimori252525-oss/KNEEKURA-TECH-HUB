package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.io.IOException;
import java.nio.*;
import java.nio.charset.*;
import java.nio.file.*;
import java.util.*;
record KneekuraDebugOwnerInputs(Path runDir,String envelopeHash,JsonObject envelope,KneekuraDebugArenaOwnerGrant grant,JsonObject materials,JsonObject world,JsonObject request,JsonObject snapshot,JsonObject triggerConfig) {
 static final String CONTROL="BOUNDED_DIAGNOSTIC_CONTROL";
 static final Set<String> MODES=Set.of("PACKAGED_JAR_CODE_SOURCE_AND_CLASS_RESOURCE_LINKAGE","OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE");
 static KneekuraDebugOwnerInputs load(KneekuraDebugEnv.Config cfg)throws IOException{
  if(cfg==null||!cfg.enabled()||cfg.ownerSetup()==null)throw new IOException("OWNER_NOT_CONFIGURED");Path root=cfg.runDir().toRealPath();
  if(!cfg.ownerSetup().file().equals(root.resolve("control/owner-envelope.json")))throw new IOException("OWNER_ENVELOPE_PATH_MISMATCH");
  String eh=KneekuraDebugActionJournal.hash(cfg.ownerSetup().sha256());JsonObject e=KneekuraDebugOwnerFiles.json(root,"control/owner-envelope.json",eh,16*1024);
  JsonObject baseEnvelope=e.deepCopy();baseEnvelope.remove("triggerConfigHash");baseEnvelope.remove("tankRotationHash");
  KneekuraDebugActionJournal.keys(baseEnvelope,"schemaVersion","debugSessionId","runId","runSnapshotId","processEpoch","handshakeNonce","requestHash","grantHash","materialDescriptorHash","worldRegistrationHash","controlMode");
  if(n(e,"schemaVersion")!=1||!t(e,"debugSessionId").equals(cfg.debugSessionId())||!t(e,"runId").equals(cfg.runId())||!t(e,"runSnapshotId").equals(cfg.runSnapshotId())||n(e,"processEpoch")!=cfg.processEpoch()||!t(e,"handshakeNonce").equals(cfg.handshakeNonce())||!t(e,"controlMode").equals(CONTROL))throw new IOException("OWNER_ENVELOPE_IDENTITY_MISMATCH");
  JsonObject grantJson=KneekuraDebugOwnerFiles.json(root,"control/owner-grant.json",t(e,"grantHash"),32*1024);var grant=KneekuraDebugArenaOwnerGrant.parse(grantJson);var id=grant.identity();
  if(!id.debugSessionId().equals(cfg.debugSessionId())||!id.runId().equals(cfg.runId())||!id.runSnapshotId().equals(cfg.runSnapshotId())||id.processEpoch()!=cfg.processEpoch()||!id.handshakeNonce().equals(cfg.handshakeNonce())||!grant.requestHash().equals(t(e,"requestHash")))throw new IOException("OWNER_GRANT_IDENTITY_MISMATCH");
  JsonObject m=KneekuraDebugOwnerFiles.json(root,"control/owner-material-descriptor.json",t(e,"materialDescriptorHash"),16*1024);validateMaterials(m);
  JsonObject w=KneekuraDebugOwnerFiles.json(root,"control/owner-world-registration.json",t(e,"worldRegistrationHash"),16*1024);validateWorld(w,grant);
  JsonObject req=KneekuraDebugOwnerFiles.json(root,"control/owner-experiment-request.json",grant.requestHash(),128*1024);validateRequest(req,grant,m);
  JsonObject snapshot=KneekuraDebugOwnerFiles.json(root,"run-snapshot.json",null,2*1024*1024);String hash=t(snapshot,"snapshotHash");
  if(!hash.matches("sha256:[a-f0-9]{64}"))throw new IOException("OWNER_SNAPSHOT_HASH_MALFORMED");byte[] canonical=KneekuraDebugOwnerFiles.read(root,"run-snapshot.canonical.json",hash.substring(7),2*1024*1024);JsonObject body=snapshot.deepCopy();body.remove("snapshotHash");
  String canonicalText=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(canonical)).toString();if(!body.equals(KneekuraDebugActionJournal.parse(canonicalText)))throw new IOException("OWNER_SNAPSHOT_CANONICAL_MISMATCH");
  if(n(snapshot,"schemaVersion")!=1||!t(snapshot,"snapshotId").equals(cfg.runSnapshotId())||!t(snapshot,"debugSessionId").equals(cfg.debugSessionId())||!t(snapshot,"runId").equals(cfg.runId())||n(snapshot,"processEpoch")!=cfg.processEpoch()||!t(snapshot,"worldName").equals(cfg.worldName()))throw new IOException("OWNER_SNAPSHOT_IDENTITY_MISMATCH");
  JsonObject runtime=o(snapshot,"runtime");if(n(runtime,"pid")!=ProcessHandle.current().pid()||!t(o(runtime,"attestation"),"topology").equals("INTEGRATED_SERVER"))throw new IOException("OWNER_RUNTIME_PID_OR_TOPOLOGY_MISMATCH");
  JsonObject tech=o(snapshot,"techHub");if(!t(tech,"request_hash").equals(grant.requestHash())||!t(tech,"experiment_id").equals(id.experimentId())||n(tech,"generation")!=grant.generation()||!o(tech,"target").equals(o(req,"target"))||!t(tech,"arena_id").equals(grant.arena().arenaId())||!t(tech,"arena_baseline_hash").equals(grant.arena().baselineHash()))throw new IOException("OWNER_SNAPSHOT_TARGET_MISMATCH");
  JsonObject intent=o(o(snapshot,"bridge"),"ownerControlIntent");KneekuraDebugActionJournal.keys(intent,"envelopeHash","scope","fullTargetAttestation");if(!t(intent,"envelopeHash").equals(eh)||!t(intent,"scope").equals(CONTROL)||!t(intent,"fullTargetAttestation").equals("NOT_ESTABLISHED"))throw new IOException("OWNER_SNAPSHOT_INTENT_MISMATCH");
  JsonObject triggerConfig=e.has("triggerConfigHash")?KneekuraDebugOwnerTriggers.validateConfig(KneekuraDebugOwnerFiles.json(root,"control/owner-trigger-config.json",KneekuraDebugActionJournal.hash(t(e,"triggerConfigHash")),16*1024),grant):null;
  if(triggerConfig!=null&&!t(o(req,"visual_rig"),"mode").equals("cardinal-4-snapshot-v1"))throw new IOException("OWNER_TRIGGER_CARDINAL_RIG_REQUIRED");
  var result=new KneekuraDebugOwnerInputs(root,eh,e,grant,m,w,req,snapshot,triggerConfig);result.verifyDiskMaterials();result.tankRotation();return result;
 }
 KneekuraDebugTankRotationPlan.Validated tankRotation()throws IOException{
  if(!envelope.has("tankRotationHash"))return null;
  JsonObject plan=KneekuraDebugOwnerFiles.json(runDir,"control/owner-tank-rotation.json",KneekuraDebugActionJournal.hash(t(envelope,"tankRotationHash")),16384);
  byte[] predecessor=KneekuraDebugOwnerFiles.read(runDir,"control/owner-tank-predecessor.json",KneekuraDebugActionJournal.hash(t(plan,"previousOwnerFileSha256")),65536);
  return KneekuraDebugTankRotationPlan.parse(plan,grant,request,world,triggerConfig,predecessor);
 }
 void verifyDiskMaterials()throws IOException{
  KneekuraDebugOwnerFiles.read(runDir,"control/owner-materials/build.jar",t(materials,"buildArtifactHash"),64*1024*1024);
  KneekuraDebugOwnerFiles.read(runDir,"control/owner-materials/config.bin",t(materials,"configArtifactHash"),1024*1024);
  KneekuraDebugOwnerFiles.read(runDir,"control/owner-materials/resources.bin",t(materials,"resourceArtifactHash"),16*1024*1024);
 }
 static void validateMaterials(JsonObject m)throws IOException{
  KneekuraDebugActionJournal.keys(m,"schemaVersion","linkageMode","targetModId","buildArtifactHash","configArtifactHash","resourceArtifactHash","classResources");if(n(m,"schemaVersion")!=1||!MODES.contains(t(m,"linkageMode"))||!t(m,"targetModId").matches("[a-z][a-z0-9_]{1,63}"))throw new IOException("UNSUPPORTED_MATERIAL_DESCRIPTOR");for(String k:List.of("buildArtifactHash","configArtifactHash","resourceArtifactHash"))KneekuraDebugActionJournal.hash(t(m,k));
  JsonArray rows=a(m,"classResources",1,8);Set<String> names=new HashSet<>();for(JsonElement entry:rows){JsonObject row=KneekuraDebugActionJournal.object(entry);KneekuraDebugActionJournal.keys(row,"className","sha256");String name=t(row,"className");if(name.length()>256||!name.matches("[A-Za-z_$][A-Za-z0-9_$]*(\\.[A-Za-z_$][A-Za-z0-9_$]*)+")||!names.add(name))throw new IOException("INVALID_CLASS_MEMBER_MANIFEST");KneekuraDebugActionJournal.hash(t(row,"sha256"));}
 }
 static void validateWorld(JsonObject w,KneekuraDebugArenaOwnerGrant g)throws IOException{
  KneekuraDebugActionJournal.keys(w,"schemaVersion","registrationId","canonicalWorldRoot","worldName","dimensionId","permissions");KneekuraDebugArenaController.id(t(w,"registrationId"));Path p=Path.of(t(w,"canonicalWorldRoot"));if(n(w,"schemaVersion")!=1||!p.isAbsolute()||!p.normalize().equals(p)||!t(w,"worldName").equals("KNEEKURA_DEBUG_WORLD")||!t(w,"worldName").equals(g.disposableWorldName())||!t(w,"dimensionId").equals(g.dimensionId()))throw new IOException("INVALID_WORLD_REGISTRATION");Set<String> permissions=new HashSet<>();for(JsonElement item:a(w,"permissions",1,3)){if(!item.isJsonPrimitive()||!item.getAsJsonPrimitive().isString()||!Set.of(CONTROL,"CARDINAL_CAPTURE_PAUSE_CAMERA",KneekuraDebugTankRotationPlan.PERMISSION).contains(item.getAsString())||!permissions.add(item.getAsString()))throw new IOException("INVALID_OWNER_PERMISSION");}if(!permissions.contains(CONTROL))throw new IOException("DIAGNOSTIC_CONTROL_NOT_REGISTERED");
 }
 static void validateRequest(JsonObject r,KneekuraDebugArenaOwnerGrant g,JsonObject m)throws IOException{
  KneekuraDebugActionJournal.keys(r,"schema_version","experiment_id","generation","target","arena","subjects","initial_state","actions","observation_scopes","visual_rig","assertions","budgets");if(n(r,"schema_version")!=1||!t(r,"experiment_id").equals(g.identity().experimentId())||n(r,"generation")!=g.generation())throw new IOException("OWNER_REQUEST_IDENTITY_MISMATCH");
  JsonObject target=o(r,"target");if(!t(target,"build_artifact_hash").equals(t(m,"buildArtifactHash"))||!t(target,"config_hash").equals(t(m,"configArtifactHash"))||!t(target,"resource_hash").equals(t(m,"resourceArtifactHash")))throw new IOException("OWNER_REQUEST_MATERIAL_MISMATCH");JsonObject arena=o(r,"arena");var b=g.arena().bounds();JsonObject bounds=o(arena,"bounds");if(!t(arena,"arena_id").equals(g.arena().arenaId())||!t(arena,"baseline_hash").equals(g.arena().baselineHash())||!a(bounds,"min",3,3).equals(vector(b.minX(),b.minY(),b.minZ()))||!a(bounds,"max",3,3).equals(vector(b.maxX(),b.maxY(),b.maxZ())))throw new IOException("OWNER_REQUEST_ARENA_MISMATCH");
  Map<String,KneekuraDebugArenaController.Subject> subjects=new HashMap<>();for(JsonElement item:a(r,"subjects",1,16)){JsonObject s=KneekuraDebugActionJournal.object(item);KneekuraDebugActionJournal.keys(s,"subject_id","uuid","entity_type");if(subjects.put(t(s,"subject_id"),new KneekuraDebugArenaController.Subject(t(s,"uuid"),t(s,"entity_type")))!=null)throw new IOException("DUPLICATE_REQUEST_SUBJECT");}if(!subjects.equals(g.subjects()))throw new IOException("OWNER_REQUEST_SUBJECT_MISMATCH");
  JsonObject budgets=o(r,"budgets");if(n(budgets,"time_budget_ms")!=g.timeBudgetMs()||n(budgets,"max_actions")!=g.maxActions()||n(budgets,"max_captures")!=g.maxCaptures())throw new IOException("OWNER_REQUEST_BUDGET_MISMATCH");Set<String> types=new HashSet<>(),ids=new HashSet<>();JsonArray actions=new JsonArray();actions.addAll(a(r,"initial_state",0,32));actions.addAll(a(r,"actions",0,32));if(actions.size()>g.maxActions())throw new IOException("OWNER_REQUEST_ACTION_BUDGET");for(JsonElement entry:actions){JsonObject action=KneekuraDebugActionJournal.object(entry);String id=t(action,"action_id");KneekuraDebugArenaController.id(id);if(!ids.add(id))throw new IOException("DUPLICATE_ACTION_ID");String type=t(action,"operation");if(!Set.of("wait_ticks","teleport_subject","set_block").contains(type))throw new IOException("TYPED_ACTION_BACKEND_UNAVAILABLE");types.add(type);}if(!types.equals(g.allowedActions()))throw new IOException("OWNER_REQUEST_ACTION_SCOPE_MISMATCH");
 }
 static String t(JsonObject o,String key)throws IOException{return KneekuraDebugArenaController.text(o,key);}static long n(JsonObject o,String key)throws IOException{return KneekuraDebugArenaController.integer(o,key);}static JsonObject o(JsonObject o,String key)throws IOException{return KneekuraDebugActionJournal.object(o.get(key));}
 static JsonArray a(JsonObject o,String key,int min,int max)throws IOException{JsonElement e=o.get(key);if(e==null||!e.isJsonArray()||e.getAsJsonArray().size()<min||e.getAsJsonArray().size()>max)throw new IOException("INVALID_BOUNDED_ARRAY");return e.getAsJsonArray();}
 static JsonArray vector(int...n){JsonArray a=new JsonArray();for(int i:n)a.add(i);return a;}
 JsonArray actions()throws IOException{JsonArray actions=new JsonArray();actions.addAll(a(request,"initial_state",0,32));actions.addAll(a(request,"actions",0,32));return actions;}
 String snapshotHash()throws IOException{return t(snapshot,"snapshotHash");}
}
