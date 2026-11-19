package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.Registries;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import java.io.IOException;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;

/** Existing tick-owner connection only: sealed Supervisor inputs, typed journal intents, no daemon. */
public final class KneekuraDebugOwnerConnection {
 private static volatile Session current;
 private KneekuraDebugOwnerConnection(){}
 public static void onServerTick(KneekuraDebugEnv.Config config,MinecraftServer server,long tick,Class<?> bootstrapAnchor)throws IOException{
  if(config==null||config.ownerSetup()==null)return;if(!server.isSameThread())throw new IOException("SERVER_THREAD_REQUIRED");
  if(current==null)current=new Session(config,server,bootstrapAnchor);
  if(current.config!=config||current.server!=server){current.close("OWNER_CONTEXT_CHANGED",true);return;}
  current.tick(tick);
 }
 /** Client shutdown waits for actual owner-thread detach before the existing writer can seal. */
 public static boolean prepareShutdownClient(KneekuraDebugEnv.Config config){
  if(config==null||config.ownerSetup()==null)return true;Session exact=current;if(exact==null)return true;
  if(exact.config!=config)return false;
  if(exact.shutdownDetach==null){
   KneekuraDebugCardinalCapture.uninstall();CompletableFuture<Void> detached=new CompletableFuture<>();exact.shutdownDetach=detached;
   exact.server.execute(()->{try{exact.close("OWNER_SHUTDOWN_REQUESTED",false);detached.complete(null);}catch(Throwable error){detached.completeExceptionally(error);}});
  }
  return KneekuraDebugOwnerLifetime.shutdownReady(exact.shutdownDetach.isDone(),exact.shutdownDetach.isCompletedExceptionally(),KneekuraDebugCardinalCapture.quiescent());
 }
 private static final class Session {
  final KneekuraDebugEnv.Config config;final MinecraftServer server;final Class<?> bootstrap;final KneekuraDebugOwnerLifetime life=new KneekuraDebugOwnerLifetime();
  KneekuraDebugOwnerInputs input;KneekuraDebugScopedOwnerGate gate;ServerLevel level;String installedHash;String lastError;int nextAction;boolean cleanupUsed;KneekuraDebugOwnerTriggers.ExitDetector triggerSource;
  final Set<Integer> usedCaptures=new HashSet<>();final Set<String> usedActions=new HashSet<>();String pendingAction;
  KneekuraDebugTankRotationController rotation;KneekuraDebugForgeTankRotationBackend rotationBackend;
  volatile CompletableFuture<Void> shutdownDetach;CompletableFuture<Void> captureInstall;CompletableFuture<KneekuraDebugCardinalCapture.OwnedCompletion> captureResult;Path captureDirectory;JsonObject captureMarker;long captureStartedNanos;long installationStartedNanos;long lastStatusNanos;
  Session(KneekuraDebugEnv.Config config,MinecraftServer server,Class<?> bootstrap){this.config=config;this.server=server;this.bootstrap=bootstrap;}
  void tick(long tick)throws IOException{
   if(Files.exists(config.shutdownRequestFile(),LinkOption.NOFOLLOW_LINKS)){close("OWNER_SHUTDOWN_REQUESTED",false);return;}
   if(life.phase()==KneekuraDebugOwnerLifetime.Phase.WAITING){
    if(!Files.isRegularFile(config.runDir().resolve("run-snapshot.json"),LinkOption.NOFOLLOW_LINKS))return;
    if(!life.reserve(config.ownerSetup().sha256()))return;
    try{JsonObject reservation=new JsonObject();reservation.addProperty("schemaVersion",1);reservation.addProperty("ownerEnvelopeHash",config.ownerSetup().sha256());reservation.addProperty("processId",ProcessHandle.current().pid());reservation.addProperty("observedAt",Instant.now().toString());KneekuraDebugOwnerFiles.writeNew(config.runDir(),"control/owner-install-reservation.json",reservation);install();}
    catch(Exception error){lastError=reason(error);life.blocked();try{KneekuraDebugArenaRuntime.uninstallOwner();}catch(Exception ignored){}writeInstalled("BLOCKED",lastError);writeStatus(true);return;}
   }
   if(life.phase()==KneekuraDebugOwnerLifetime.Phase.RESERVED){
    if(captureInstall!=null&&!captureInstall.isDone()){if(System.nanoTime()-installationStartedNanos>5_000_000_000L){close("CAPTURE_INSTALL_DEADLINE",true);}return;}
    try{if(captureInstall!=null)captureInstall.join();var installedState=KneekuraDebugArenaRuntime.snapshotOwner();KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(installedState,0);life.active();writeInstalled("INSTALLED_SCOPED_CONTROL",null);if(rotationBackend!=null)rotationBackend.bindInstallationReceipt(installedHash);writeStatus(true);}
    catch(Exception error){close(reason(error),true);return;}
   }
   if(life.phase()!=KneekuraDebugOwnerLifetime.Phase.ACTIVE)return;
   try{
    KneekuraDebugArenaRuntime.onServerTick(config,server,tick);
    if(rotation!=null){
      rotationBackend.tick(tick);var outcome=rotation.onTick(tick);
      if(outcome.phase()==KneekuraDebugTankRotationController.Phase.VERIFIED){rotationBackend.complete(outcome);close("TANK_ROTATION_VERIFIED_FRESH_RUN_REQUIRED",false);}
      else if(outcome.phase()==KneekuraDebugTankRotationController.Phase.OUTCOME_UNKNOWN)close("TANK_ROTATION_OUTCOME_UNKNOWN",true);
      else writeStatus(false);
      return; // Maintenance never dispatches ordinary actions, cleanup, triggers or captures.
    }
    if(pendingAction!=null){JsonObject stored=storedAction(pendingAction);var recorded=new KneekuraDebugActionJournal(config.runDir()).lookup(stored);
      if(recorded.equals("VERIFIED")){nextAction++;pendingAction=null;}else if(!recorded.equals("OUTCOME_UNKNOWN")){pendingAction=null;lastError="ACTION_TERMINAL_"+recorded;}
      else if(KneekuraDebugArenaRuntime.snapshotOwner().unsafe()){pendingAction=null;lastError="ACTION_OUTCOME_UNKNOWN";}
    }
    completeCapture();
    var state=KneekuraDebugArenaRuntime.snapshotOwner();
    if(state.idle()&&!state.unsafe()&&!captureBusy())observeTrigger(tick,state);
    if(state.idle()&&!captureBusy()){
      if(!cleanupUsed&&tryCleanup(tick)){}
      else if(!state.unsafe()&&!tryAction(tick))tryCapture();
    }
    writeStatus(false);
   }catch(Exception error){close(reason(error),true);}
  }
  void install()throws IOException{
   input=KneekuraDebugOwnerInputs.load(config);level=server.getLevel(ResourceKey.create(Registries.DIMENSION,ResourceLocation.tryParse(input.grant().dimensionId())));if(level==null)throw new IOException("OWNER_DIMENSION_NOT_LOADED");
   gate=new KneekuraDebugScopedOwnerGate(config,server,level,input,bootstrap);
   Path actions=input.runDir().resolve("control/actions");if(!Files.exists(actions,LinkOption.NOFOLLOW_LINKS))Files.createDirectory(actions);if(Files.isSymbolicLink(actions)||!Files.isDirectory(actions,LinkOption.NOFOLLOW_LINKS))throw new IOException("OWNER_ACTION_DIRECTORY_UNSAFE");
   KneekuraDebugArenaRuntime.installOwner(config,server,level,input.grant(),gate,(epoch,tick,time,lane,payload)->{
    JsonObject row=payload.deepCopy();row.addProperty("ownerEnvelopeHash",input.envelopeHash());row.addProperty("ownerInstallationReceiptHash",installedHash);row.addProperty("materialDescriptorHash",KneekuraDebugOwnerInputs.t(input.envelope(),"materialDescriptorHash"));row.addProperty("worldRegistrationHash",KneekuraDebugOwnerInputs.t(input.envelope(),"worldRegistrationHash"));row.addProperty("fullTargetAttestation","NOT_ESTABLISHED");row.addProperty("transformedClassCertainty","NOT_ESTABLISHED");
    return KneekuraDebugEvidenceWriter.recordArenaObserved(config,epoch,tick,time,lane,"KneekuraDebugOwnerConnection.scoped_control",row);
   });
   var tank=input.tankRotation();
   if(tank!=null){
    var state=KneekuraDebugArenaRuntime.snapshotOwner();var lease=KneekuraDebugArenaRuntime.presentationLeaseOwner(state);
    rotationBackend=new KneekuraDebugForgeTankRotationBackend(config,server,level,input,gate,tank,state);
    rotation=new KneekuraDebugTankRotationController(tank.controllerPlan(lease),rotationBackend,System::nanoTime);
    KneekuraDebugTankPresentation.clear();return;
   }
   if(input.triggerConfig()!=null)triggerSource=new KneekuraDebugOwnerTriggers.ExitDetector(input.grant().arena().bounds(),(int)KneekuraDebugOwnerInputs.n(input.triggerConfig(),"maxWindows"),KneekuraDebugOwnerInputs.n(input.triggerConfig(),"cooldownMs"));
   if(captureAllowed()){
    JsonObject rig=KneekuraDebugOwnerInputs.o(input.request(),"visual_rig");JsonArray viewport=rig.getAsJsonArray("viewport");Set<String> behavior=new HashSet<>();for(JsonElement e:input.request().getAsJsonArray("assertions")){JsonObject assertion=e.getAsJsonObject();if(!KneekuraDebugOwnerInputs.t(assertion,"kind").equals("visual"))behavior.add(KneekuraDebugOwnerInputs.t(assertion,"assertion_id"));}
    var policy=new KneekuraDebugCapturePolicy(input.grant().requestHash(),input.grant().generation(),rig.get("fov").getAsDouble(),viewport.get(0).getAsInt(),viewport.get(1).getAsInt(),Math.min(5000,input.grant().timeBudgetMs()),true,true,behavior);
    var owner=new KneekuraDebugCaptureOwner(input.grant(),policy);installationStartedNanos=System.nanoTime();captureInstall=new CompletableFuture<>();CompletableFuture<Void> installed=captureInstall;Minecraft.getInstance().execute(()->{if(installed.isDone())return;try{KneekuraDebugCardinalCapture.install(config,owner,new KneekuraDebugCaptureEvidenceSink());installed.complete(null);}catch(Throwable error){installed.completeExceptionally(error);}});
   }
  }
  boolean tryAction(long tick)throws IOException{
   JsonArray actions=input.actions();if(nextAction>=actions.size())return false;String id=KneekuraDebugOwnerInputs.t(actions.get(nextAction).getAsJsonObject(),"action_id"),key=KneekuraDebugOwnerDispatch.actionKey(input,id),dir="control/actions/"+KneekuraDebugActionJournal.sha256(key);
   scanBoundedDirectories(input.runDir().resolve("control/actions"),33);
   if(!Files.exists(input.runDir().resolve(dir+"/dispatch.json"),LinkOption.NOFOLLOW_LINKS)||usedActions.contains(id))return false;
   JsonObject marker=KneekuraDebugOwnerFiles.json(input.runDir(),dir+"/dispatch.json",null,16*1024);byte[] canonical=KneekuraDebugOwnerFiles.read(input.runDir(),dir+"/canonical-action.json",null,128*1024);JsonObject action=KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(new String(canonical,java.nio.charset.StandardCharsets.UTF_8)));KneekuraDebugOwnerDispatch.validate(input,marker,action,canonical,nextAction);
   gate.revalidateBoundary();var budgetState=KneekuraDebugArenaRuntime.snapshotOwner();
   KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(budgetState,KneekuraDebugOwnerDispatch.requiredRemainingMs(marker));
   Path reservation=input.runDir().resolve(dir+"/native-dispatch-reservation.json");usedActions.add(id);JsonObject reserved=base();reserved.addProperty("selectedActionId",id);reserved.addProperty("idempotencyKey",key);KneekuraDebugOwnerFiles.writeNew(input.runDir(),dir+"/native-dispatch-reservation.json",reserved);
   gate.revalidateBoundary();KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(KneekuraDebugArenaRuntime.snapshotOwner(),KneekuraDebugOwnerDispatch.requiredRemainingMs(marker));var result=KneekuraDebugArenaRuntime.submitOwner(new KneekuraDebugArenaController.Command(action,config.handshakeNonce(),input.grant().leaseId()),tick);
   if(result.status().equals("VERIFIED"))nextAction++;else if(result.status().equals("ACCEPTED"))pendingAction=id;else lastError="ACTION_"+result.status();return true;
  }
  JsonObject storedAction(String id)throws IOException{String key=KneekuraDebugOwnerDispatch.actionKey(input,id),dir="control/actions/"+KneekuraDebugActionJournal.sha256(key);return KneekuraDebugOwnerFiles.json(input.runDir(),dir+"/canonical-action.json",null,128*1024);}
  boolean tryCleanup(long tick)throws IOException{
   String file="control/owner-cleanup/request.json";if(!Files.exists(input.runDir().resolve(file),LinkOption.NOFOLLOW_LINKS))return false;JsonObject marker=KneekuraDebugOwnerFiles.json(input.runDir(),file,null,16*1024);KneekuraDebugOwnerDispatch.validateCleanup(input,marker);var state=KneekuraDebugArenaRuntime.snapshotOwner();if(KneekuraDebugOwnerInputs.n(marker,"expectedArenaEpoch")!=state.arenaEpoch()||KneekuraDebugOwnerInputs.n(marker,"expectedArenaRevision")!=state.arenaRevision())throw new IOException("CLEANUP_CONTEXT_CHANGED");
   cleanupUsed=true;KneekuraDebugOwnerFiles.writeNew(input.runDir(),"control/owner-cleanup/native-reservation.json",base());gate.revalidateBoundary();JsonObject action=baseAction("owner_cleanup_reset",KneekuraDebugOwnerDispatch.cleanupKey(input),"reset_arena",state);action.add("args",new JsonObject());var outcome=KneekuraDebugArenaRuntime.resetOwner(new KneekuraDebugArenaController.Command(action,config.handshakeNonce(),input.grant().leaseId()),tick);lastError=outcome.status().equals("VERIFIED")?null:"CLEANUP_"+outcome.status();if(KneekuraDebugOwnerLifetime.requiresCleanupClose(outcome.status()))close("OWNER_CLEANUP_COMPLETE",false);return true;
  }
  void observeTrigger(long tick,KneekuraDebugArenaController.Snapshot state)throws IOException{
   if(triggerSource==null)return;
   for(var entry:input.grant().subjects().entrySet()){
    var subject=entry.getValue();Entity entity=level.getEntity(UUID.fromString(subject.uuid()));
    if(entity==null||entity.isRemoved()||entity.level()!=level||!BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString().equals(subject.entityType())){triggerSource.missing(entry.getKey());continue;}
    JsonObject event=triggerSource.sample(entry.getKey(),List.of(entity.getX(),entity.getY(),entity.getZ()),System.nanoTime()/1_000_000L);if(event==null)continue;
    event.addProperty("kind","owner_trigger_event");event.addProperty("triggerKind","ARENA_EXIT");event.addProperty("subjectId",entry.getKey());event.addProperty("uuid",subject.uuid());event.add("identity",KneekuraDebugOwnerTriggers.identity(input,state));event.addProperty("ownerEnvelopeHash",input.envelopeHash());event.addProperty("triggerConfigHash",KneekuraDebugOwnerInputs.t(input.envelope(),"triggerConfigHash"));event.addProperty("basis","DECLARED_SUBJECT_POINT_SAMPLED_INSIDE_TO_OUTSIDE_NOT_CAUSAL_PROOF");
    KneekuraDebugEvidenceWriter.recordOwnedEntityObserved(config,state.arenaEpoch(),tick,level.getGameTime(),"KneekuraDebugOwnerConnection.arena_exit",entity.getUUID(),event);
   }
  }
  void expiredCapture(JsonObject marker,String dir)throws IOException{
   JsonObject receipt=base();receipt.addProperty("kind","owner_capture_receipt");for(String key:List.of("captureKey","captureId","captureIndex","trigger"))if(marker.has(key))receipt.add(key,marker.get(key));receipt.addProperty("status","EXPIRED_NOT_DISPATCHED");receipt.addProperty("error","TRIGGER_DEADLINE");receipt.addProperty("receiptHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(receipt)));KneekuraDebugOwnerFiles.writeNew(input.runDir(),dir+"/receipt.json",receipt);
  }
  void tryCapture()throws IOException{
   if(!captureAllowed())return;for(int index=0;index<input.grant().maxCaptures()/4;index++){
    if(usedCaptures.contains(index))continue;String key=KneekuraDebugOwnerDispatch.captureKey(input,index),dir="control/captures/"+key;
    if(!Files.exists(input.runDir().resolve(dir+"/request.json"),LinkOption.NOFOLLOW_LINKS))continue;scanBoundedDirectories(input.runDir().resolve("control/captures"),4);JsonObject marker=KneekuraDebugOwnerFiles.json(input.runDir(),dir+"/request.json",null,16*1024);KneekuraDebugOwnerDispatch.validateCapture(input,marker,usedCaptures);var state=KneekuraDebugArenaRuntime.snapshotOwner();if(KneekuraDebugOwnerInputs.n(marker,"expectedArenaEpoch")!=state.arenaEpoch()||KneekuraDebugOwnerInputs.n(marker,"expectedArenaRevision")!=state.arenaRevision())throw new IOException("CAPTURE_CONTEXT_CHANGED");
    usedCaptures.add(index);KneekuraDebugOwnerFiles.writeNew(input.runDir(),dir+"/native-reservation.json",base());gate.revalidateBoundary();long absoluteDeadline=KneekuraDebugOwnerTriggers.deadline(marker);long allowedMillis=KneekuraDebugOwnerTriggers.remainingMillis(absoluteDeadline,System.currentTimeMillis(),Math.min(5000,input.grant().timeBudgetMs()));if(allowedMillis<100){expiredCapture(marker,dir);continue;}long dispatchDeadlineNanos=System.nanoTime()+allowedMillis*1_000_000L;captureMarker=marker;captureDirectory=input.runDir().resolve(dir);captureStartedNanos=System.nanoTime();captureResult=new CompletableFuture<>();
    JsonObject rig=KneekuraDebugOwnerInputs.o(input.request(),"visual_rig");JsonArray viewport=rig.getAsJsonArray("viewport");List<UUID> subjects=input.grant().subjects().values().stream().map(s->UUID.fromString(s.uuid())).sorted().toList();List<String> assertions=new ArrayList<>();for(JsonElement e:input.request().getAsJsonArray("assertions")){JsonObject a=e.getAsJsonObject();if(!KneekuraDebugOwnerInputs.t(a,"kind").equals("visual"))assertions.add(KneekuraDebugOwnerInputs.t(a,"assertion_id"));}
    long total=allowedMillis,barrier=Math.min(2000,total);if(total<100)throw new IOException("CAPTURE_TIME_BUDGET_UNSUPPORTED");var identity=new KneekuraDebugCaptureSession.Identity(config.debugSessionId(),config.runId(),config.runSnapshotId(),config.processEpoch(),input.grant().identity().experimentId(),input.grant().generation(),input.grant().requestHash(),state.arenaId(),state.arenaEpoch(),state.arenaRevision(),input.grant().arena().baselineHash());var b=input.grant().arena().bounds();var request=new KneekuraDebugCaptureSession.Request(KneekuraDebugOwnerInputs.t(marker,"captureId"),identity,subjects,assertions,List.of(b.minX(),b.minY(),b.minZ()),List.of(b.maxX(),b.maxY(),b.maxZ()),rig.get("fov").getAsDouble(),viewport.get(0).getAsInt(),viewport.get(1).getAsInt(),barrier,total,true,true);
    CompletableFuture<KneekuraDebugCardinalCapture.OwnedCompletion> future=captureResult;Minecraft.getInstance().execute(()->{if(future.isDone())return;try{long remaining=Math.min((dispatchDeadlineNanos-System.nanoTime())/1_000_000L,KneekuraDebugOwnerTriggers.remainingMillis(absoluteDeadline,System.currentTimeMillis(),total));if(remaining<100)throw new IOException("TRIGGER_DISPATCH_DEADLINE");var bounded=new KneekuraDebugCaptureSession.Request(request.captureId(),request.identity(),request.subjects(),request.behaviorAssertionIds(),request.arenaMin(),request.arenaMax(),request.fov(),request.width(),request.height(),Math.min(request.barrierBudgetMs(),remaining),remaining,true,true);KneekuraDebugCardinalCapture.requestOwned(bounded).whenComplete((manifest,error)->{if(error!=null)future.completeExceptionally(error);else future.complete(manifest);});}catch(Throwable error){future.completeExceptionally(error);}});return;
   }
  }
  void completeCapture()throws IOException{
   if(captureResult==null)return;if(!captureResult.isDone()&&System.nanoTime()-captureStartedNanos>6_000_000_000L){Minecraft.getInstance().execute(KneekuraDebugCardinalCapture::uninstall);captureResult.completeExceptionally(new IOException("CAPTURE_OWNER_DEADLINE"));}
   if(!captureResult.isDone())return;boolean restored=false;JsonObject receipt=base();receipt.addProperty("kind","owner_capture_receipt");for(String key:List.of("captureKey","captureId","captureIndex"))receipt.add(key,captureMarker.get(key));
   try{var completion=captureResult.join();JsonObject manifest=completion.manifest();restored=KneekuraDebugOwnerLifetime.captureRestored(manifest,completion.serverBarrierReleased(),completion.serverBarrierExpired());receipt.addProperty("status",KneekuraDebugOwnerInputs.t(KneekuraDebugOwnerInputs.o(manifest,"result"),"status"));receipt.addProperty("manifestPayloadHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(manifest)));receipt.addProperty("linkageBasis","DURABLE_CAPTURE_API_COMPLETION_AND_CANONICAL_PAYLOAD_HASH");receipt.add("manifest",manifest);}
   catch(Exception error){receipt.addProperty("status","OUTCOME_UNKNOWN");receipt.addProperty("error",reason(error));lastError="CAPTURE_OUTCOME_UNKNOWN";}
   receipt.addProperty("receiptHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(receipt)));KneekuraDebugOwnerFiles.writeNew(input.runDir(),input.runDir().relativize(captureDirectory.resolve("receipt.json")).toString().replace('\\','/'),receipt);captureResult=null;captureDirectory=null;captureMarker=null;if(!restored)throw new IOException("CAPTURE_RESTORATION_NOT_ESTABLISHED");
  }
  boolean captureBusy(){return captureResult!=null||captureInstall!=null&&!captureInstall.isDone();}
  boolean captureAllowed()throws IOException{if(input.grant().maxCaptures()<4||!KneekuraDebugOwnerInputs.t(KneekuraDebugOwnerInputs.o(input.request(),"visual_rig"),"mode").equals("cardinal-4-snapshot-v1"))return false;for(JsonElement p:input.world().getAsJsonArray("permissions"))if(p.getAsString().equals("CARDINAL_CAPTURE_PAUSE_CAMERA"))return true;return false;}
  void writeInstalled(String status,String error)throws IOException{
   JsonObject r=base();r.addProperty("kind","owner_installation_receipt");r.addProperty("status",status);r.addProperty("scope",KneekuraDebugOwnerInputs.CONTROL);r.addProperty("grantHash",input==null?null:KneekuraDebugOwnerInputs.t(input.envelope(),"grantHash"));r.addProperty("baselineHash",input==null?null:input.grant().arena().baselineHash());r.add("materialLinkage",gate==null?JsonNull.INSTANCE:gate.linkage());r.add("worldObservation",gate==null?JsonNull.INSTANCE:gate.world());if(error==null)r.add("error",JsonNull.INSTANCE);else r.addProperty("error",error);String hash=KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(r));r.addProperty("receiptHash",hash);KneekuraDebugOwnerFiles.writeNew(config.runDir(),"control/owner-installed.json",r);installedHash=hash;
  }
  JsonObject base()throws IOException{JsonObject b=new JsonObject();b.addProperty("schemaVersion",1);b.addProperty("debugSessionId",config.debugSessionId());b.addProperty("runId",config.runId());b.addProperty("runSnapshotId",config.runSnapshotId());b.addProperty("processEpoch",config.processEpoch());b.addProperty("ownerEnvelopeHash",config.ownerSetup().sha256());b.addProperty("observedAt",Instant.now().toString());if(input!=null){b.addProperty("runSnapshotHash",input.snapshotHash());b.addProperty("requestHash",input.grant().requestHash());b.addProperty("leaseId",input.grant().leaseId());b.addProperty("arenaId",input.grant().arena().arenaId());b.addProperty("arenaEpoch",input.grant().arena().arenaEpoch());b.addProperty("arenaRevision",input.grant().arena().arenaRevision());}return b;}
  void writeStatus(boolean force)throws IOException{
   long now=System.nanoTime();if(!force&&now-lastStatusNanos<1_000_000_000L)return;JsonObject b=base();b.addProperty("installedReceiptHash",installedHash);boolean idle=false,unsafe=true;String status=life.phase()==KneekuraDebugOwnerLifetime.Phase.CLOSED?"OWNER_CLOSED":life.phase()==KneekuraDebugOwnerLifetime.Phase.UNKNOWN?"OUTCOME_UNKNOWN":"BLOCKED";
   if(life.phase()==KneekuraDebugOwnerLifetime.Phase.ACTIVE){var s=KneekuraDebugArenaRuntime.snapshotOwner();b.addProperty("arenaEpoch",s.arenaEpoch());b.addProperty("arenaRevision",s.arenaRevision());idle=s.idle()&&!captureBusy();unsafe=s.unsafe();status=unsafe?"OUTCOME_UNKNOWN":"ACTIVE_SCOPED_CONTROL";
    if(idle&&!unsafe){var lease=KneekuraDebugArenaRuntime.presentationLeaseOwner(s);b.add("runtimeClock",KneekuraDebugEvidenceWriter.currentClockSample());b.addProperty("leaseRemainingMs",Math.max(0L,(lease.deadlineNanos()-System.nanoTime())/1_000_000L));}}
   if(rotation!=null){var r=rotation.snapshot();b.addProperty("tankRotationPhase",life.phase()==KneekuraDebugOwnerLifetime.Phase.UNKNOWN?"OUTCOME_UNKNOWN":r.phase().name());b.addProperty("nextTankEpoch",r.nextEpoch());
    if(life.phase()==KneekuraDebugOwnerLifetime.Phase.ACTIVE){status="TANK_ROTATION_IN_PROGRESS";idle=false;unsafe=true;}}
   b.addProperty("status",status);b.addProperty("idle",idle);b.addProperty("unsafe",unsafe);JsonArray actions=input==null?new JsonArray():input.actions();b.addProperty("nextActionId",nextAction<actions.size()?KneekuraDebugOwnerInputs.t(actions.get(nextAction).getAsJsonObject(),"action_id"):null);b.addProperty("error",lastError);KneekuraDebugOwnerFiles.writeStatus(config.runDir(),b);lastStatusNanos=now;
  }
  void close(String reason,boolean failed)throws IOException{
   if(life.phase()==KneekuraDebugOwnerLifetime.Phase.CLOSED||life.phase()==KneekuraDebugOwnerLifetime.Phase.BLOCKED||life.phase()==KneekuraDebugOwnerLifetime.Phase.UNKNOWN)return;
   lastError=reason;
   if(rotation!=null){
    var before=rotation.snapshot();rotation.revoke(reason);
    if(failed && before.phase()==KneekuraDebugTankRotationController.Phase.VERIFIED)try{rotationBackend.unknown(new KneekuraDebugTankRotationController.Snapshot(KneekuraDebugTankRotationController.Phase.OUTCOME_UNKNOWN,before.cursor(),before.preflightCells(),before.generationCells(),before.verifiedCells(),before.nextEpoch(),before.geometryFingerprint(),reason,false));}catch(Exception error){lastError=reason(error);}
    if(rotation.snapshot().phase()==KneekuraDebugTankRotationController.Phase.OUTCOME_UNKNOWN)failed=true;
   }
   if(captureInstall!=null&&!captureInstall.isDone())captureInstall.completeExceptionally(new IOException("OWNER_CLOSED"));try{KneekuraDebugArenaRuntime.uninstallOwner();}catch(Exception error){lastError=reason(error);failed=true;}
   Minecraft.getInstance().execute(KneekuraDebugCardinalCapture::uninstall);if(captureResult!=null&&!captureResult.isDone())captureResult.completeExceptionally(new IOException("OWNER_CLOSED"));try{completeCapture();}catch(Exception ignored){failed=true;}
   if(failed)life.unknown();else life.close();writeStatus(true);
  }
  JsonObject baseAction(String id,String key,String type,KneekuraDebugArenaController.Snapshot state){var g=input.grant().identity();JsonObject a=new JsonObject();a.addProperty("schemaVersion",1);a.addProperty("debugSessionId",g.debugSessionId());a.addProperty("runId",g.runId());a.addProperty("runSnapshotId",g.runSnapshotId());a.addProperty("processEpoch",g.processEpoch());a.addProperty("experimentId",g.experimentId());a.addProperty("arenaId",state.arenaId());a.addProperty("arenaEpoch",state.arenaEpoch());a.addProperty("expectedArenaRevision",state.arenaRevision());a.addProperty("actionId",id);a.addProperty("idempotencyKey",key);a.addProperty("type",type);return a;}
 }
 private static void scanBoundedDirectories(Path root,int max)throws IOException{if(Files.isSymbolicLink(root)||!Files.isDirectory(root,LinkOption.NOFOLLOW_LINKS))throw new IOException("CONTROL_DIRECTORY_UNSAFE");int count=0;try(DirectoryStream<Path> paths=Files.newDirectoryStream(root)){for(Path p:paths){if(++count>max||Files.isSymbolicLink(p)||!Files.isDirectory(p,LinkOption.NOFOLLOW_LINKS)||!p.getFileName().toString().matches("[a-f0-9]{64}"))throw new IOException("CONTROL_DIRECTORY_LIMIT_OR_UNSAFE");}}}
 private static String reason(Throwable error){Throwable e=error;while(e.getCause()!=null&&e!=e.getCause())e=e.getCause();String r=e instanceof FileSystemException fs?e.getClass().getSimpleName()+":"+String.valueOf(fs.getReason()):e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();return r.length()>256?r.substring(0,256):r;}
}
