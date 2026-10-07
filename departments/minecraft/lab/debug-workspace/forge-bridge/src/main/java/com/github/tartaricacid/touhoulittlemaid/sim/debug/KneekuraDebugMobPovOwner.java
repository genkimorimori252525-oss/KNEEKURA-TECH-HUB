package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.*;
import java.io.IOException;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.CompletableFuture;

/** Real server-owned camera dispatch: exact grant/lease/subject and one capture reservation per PNG. */
final class KneekuraDebugMobPovOwner {
 private final KneekuraDebugEnv.Config config;private final MinecraftServer server;private final ServerLevel level;
 private final KneekuraDebugOwnerInputs input;private final KneekuraDebugScopedOwnerGate gate;
 private volatile boolean revoked,subjectValid=true;
 private int next;private CompletableFuture<JsonObject> pending;private KneekuraDebugMobPovCommands.Command command;private long dispatched;
 KneekuraDebugMobPovOwner(KneekuraDebugEnv.Config config,MinecraftServer server,ServerLevel level,KneekuraDebugOwnerInputs input,KneekuraDebugScopedOwnerGate gate){
  this.config=config;this.server=server;this.level=level;this.input=input;this.gate=gate;
 }
 CompletableFuture<Void> install(){
  CompletableFuture<Void> result=new CompletableFuture<>();JsonObject rig=input.request().getAsJsonObject("visual_rig").deepCopy();
  Minecraft.getInstance().execute(()->{if(result.isDone()||revoked){result.completeExceptionally(new IOException("MOB_POV_OWNER_CLOSED"));return;}
   try{KneekuraDebugMobPovCamera.install(config,()->!revoked&&subjectValid,rig);result.complete(null);}catch(Throwable error){result.completeExceptionally(error);}
  });return result;
 }
 boolean busy(){return pending!=null;}
 /** Validate existing view and finish accepted work; never admit a new camera operation. */
 boolean maintain()throws IOException{
  if(revoked)return false;
  UUID viewed=KneekuraDebugMobPovCamera.subject();if(viewed!=null)try{mob(viewed);subjectValid=true;}catch(IOException failure){subjectValid=false;}
  if(pending!=null){
   if(!pending.isDone()&&System.nanoTime()-dispatched>3_000_000_000L){pending.completeExceptionally(new IOException("MOB_POV_OPERATION_DEADLINE"));Minecraft.getInstance().execute(KneekuraDebugMobPovCamera::uninstall);revoked=true;}
   if(!pending.isDone())return true;
   complete();return true;
  }
  return false;
 }
 boolean tick(long tick,KneekuraDebugArenaController.Snapshot state)throws IOException{
  if(revoked)return false;if(maintain())return true;
  if(next>=32||!state.idle()||state.unsafe())return false;
  String dir=directory(next);if(!Files.exists(input.runDir().resolve(dir+"/request.json"),LinkOption.NOFOLLOW_LINKS))return false;
  JsonObject marker=KneekuraDebugOwnerFiles.json(input.runDir(),dir+"/request.json",null,16384);
  command=KneekuraDebugMobPovCommands.parse(input,marker,next,state);
  gate.revalidateBoundary();KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(state,command.operation().equals("return")?0:100);
  JsonObject reservation=base(command);reservation.addProperty("kind","mob_pov_operation_reservation");
  KneekuraDebugOwnerFiles.writeNew(input.runDir(),dir+"/native-reservation.json",reservation);
  next++;pending=new CompletableFuture<>();dispatched=System.nanoTime();CompletableFuture<JsonObject> exact=pending;
  try{
   var lease=KneekuraDebugArenaRuntime.presentationLeaseOwner(state);
   JsonObject identity=KneekuraDebugOwnerTriggers.identity(input,state);String operation=command.operation();
   if(operation.equals("attach")){
    Mob mob=mob(command.subject());subjectValid=true;UUID subject=mob.getUUID();String type=BuiltInRegistries.ENTITY_TYPE.getKey(mob.getType()).toString();
    long deadline=System.nanoTime()+Math.min(command.durationMs()*1_000_000L,Math.max(0,lease.deadlineNanos()-System.nanoTime()));
    String dimension=level.dimension().location().toString();
    dispatch(exact,()->KneekuraDebugMobPovCamera.attach(subject,type,dimension,deadline,identity));
   }else if(operation.equals("snapshot")){
    UUID subject=KneekuraDebugMobPovCamera.subject();if(subject==null)throw new IOException("MOB_POV_NOT_ATTACHED");Mob mob=mob(subject);
    var token=KneekuraDebugArenaRuntime.reserveCapturesOwner(state,input.grant().requestHash(),input.grant().generation(),1);
    KneekuraDebugArenaRuntime.validateCaptureOwner(token,state);gate.requireAuthorized(config,server,input.grant());
    JsonObject reference=new JsonObject();reference.add("identity",identity);reference.addProperty("serverTick",tick);reference.addProperty("serverGameTime",level.getGameTime());
    reference.addProperty("subjectUuid",subject.toString());reference.addProperty("validatedAtNanos",System.nanoTime());reference.addProperty("reservationToken",token.token());
    JsonArray position=new JsonArray();position.add(mob.getX());position.add(mob.getY());position.add(mob.getZ());reference.add("position",position);
    String captureId="mob-pov-"+command.index();dispatch(exact,()->KneekuraDebugMobPovCamera.snapshot(captureId,reference));
   }else dispatch(exact,KneekuraDebugMobPovCamera::returnView);
  }catch(Throwable error){exact.completeExceptionally(error);}
  return true;
 }
 @FunctionalInterface private interface ClientWork{CompletableFuture<JsonObject> run();}
 private void dispatch(CompletableFuture<JsonObject> exact,ClientWork work){
  Minecraft.getInstance().execute(()->{
   if(exact.isDone()||revoked){exact.completeExceptionally(new IOException("MOB_POV_OWNER_CLOSED"));return;}
   try{work.run().whenComplete((value,error)->{if(error!=null)exact.completeExceptionally(error);else exact.complete(value);});}
   catch(Throwable error){exact.completeExceptionally(error);}
  });
 }
 private Mob mob(UUID uuid)throws IOException{
  var registered=input.grant().subjects().values().stream().filter(s->s.uuid().equals(uuid.toString())).findFirst().orElseThrow(()->new IOException("MOB_POV_SUBJECT_NOT_REGISTERED"));
  Entity entity=level.getEntity(uuid);
  if(!(entity instanceof Mob mob)||entity.isRemoved()||!entity.isAlive()||!registered.entityType().equals(BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString())||
   !input.grant().arena().bounds().contains(entity.getX(),entity.getY(),entity.getZ()))throw new IOException("MOB_POV_SUBJECT_OUTSIDE_NATIVE_SCOPE");
  return mob;
 }
 private void complete()throws IOException{
  JsonObject receipt=base(command);receipt.addProperty("kind","mob_pov_operation_receipt");
  try{JsonObject result=pending.join();receipt.addProperty("status",result.get("status").getAsString());receipt.add("result",result.deepCopy());
   for(String key:List.of("restoration","imageHash","imageBytes","imagePath","observationPayloadHash"))if(result.has(key))receipt.add(key,result.get(key));
  }catch(Throwable error){receipt.addProperty("status",revoked?"OUTCOME_UNKNOWN":"REJECTED");receipt.addProperty("error",reason(error));}
  KneekuraDebugOwnerFiles.writeNew(input.runDir(),directory(command.index())+"/receipt.json",receipt);pending=null;command=null;
 }
 void close()throws IOException{
  revoked=true;Minecraft.getInstance().execute(KneekuraDebugMobPovCamera::uninstall);
  if(pending!=null){if(!pending.isDone())pending.completeExceptionally(new IOException("MOB_POV_OWNER_CLOSED"));complete();}
 }
 JsonObject status(){JsonObject s=new JsonObject();UUID subject=KneekuraDebugMobPovCamera.subject();s.addProperty("subjectUuid",subject==null?null:subject.toString());s.addProperty("active",subject!=null&&!revoked);s.addProperty("nextCommandIndex",next);s.addProperty("restoration",KneekuraDebugMobPovCamera.restoration());return s;}
 private JsonObject base(KneekuraDebugMobPovCommands.Command c)throws IOException{
  JsonObject b=new JsonObject();b.addProperty("schemaVersion",1);b.addProperty("ownerEnvelopeHash",input.envelopeHash());b.addProperty("runSnapshotHash",input.snapshotHash());b.addProperty("requestHash",input.grant().requestHash());
  b.addProperty("commandIndex",c.index());b.addProperty("operation",c.operation());b.addProperty("observedAt",Instant.now().toString());return b;
 }
 private static String directory(int index){return "control/mob-pov/"+String.format(Locale.ROOT,"%02d",index);}
 private static String reason(Throwable error){Throwable e=error;while(e.getCause()!=null&&e.getCause()!=e)e=e.getCause();String r=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();return r.length()>256?r.substring(0,256):r;}
}
