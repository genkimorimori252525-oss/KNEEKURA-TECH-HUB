package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.entity.EntityTypeTest;
import net.minecraft.world.phys.AABB;
import java.io.IOException;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.CompletableFuture;

/** Owner-wide numbered one-shot snapshots; loaded entities only, no world writes. */
final class KneekuraDebugTankRosterOwner {
 private final KneekuraDebugEnv.Config config;private final MinecraftServer server;private final ServerLevel level;
 private final KneekuraDebugOwnerInputs input;private final KneekuraDebugScopedOwnerGate gate;private final KneekuraDebugTankObservation scope;
 private int next;private CompletableFuture<String> pending;private JsonObject receipt;private long started;
 KneekuraDebugTankRosterOwner(KneekuraDebugEnv.Config config,MinecraftServer server,ServerLevel level,KneekuraDebugOwnerInputs input,KneekuraDebugScopedOwnerGate gate)throws IOException{
  this.config=config;this.server=server;this.level=level;this.input=input;this.gate=gate;scope=input.tankObservation();verifyScope();
 }
 private void verifyScope()throws IOException{
  if(!server.isSameThread()||scope==null||scope.minY()<level.getMinBuildHeight()||scope.maxY()>level.getMaxBuildHeight())throw new IOException("TANK_ROSTER_NATIVE_SCOPE");
  var current=input.tankObservation();if(current==null||!current.json().equals(scope.json()))throw new IOException("TANK_ROSTER_SCOPE_CHANGED");
  scope.verifySaved(KneekuraDebugOwnerFiles.json(Path.of(KneekuraDebugOwnerInputs.t(input.world(),"canonicalWorldRoot")),"kneekura-tank-owner.json",null,65536));
 }
 boolean tick(long tick,KneekuraDebugArenaController.Snapshot state)throws IOException{
  if(pending!=null){
   if(!pending.isDone()&&System.nanoTime()-started<3_000_000_000L)return true;
   if(!pending.isDone())pending.completeExceptionally(new IOException("TANK_ROSTER_EVIDENCE_DEADLINE"));
   complete();return true;
  }
  if(next>=scope.maxSamples()||!state.idle()||state.unsafe())return false;
  String dir=directory(next);if(!Files.exists(input.runDir().resolve(dir+"/request.json"),LinkOption.NOFOLLOW_LINKS))return false;
  JsonObject m=KneekuraDebugOwnerFiles.json(input.runDir(),dir+"/request.json",null,16384);
  KneekuraDebugActionJournal.keys(m,"schemaVersion","sampleIndex","ownerEnvelopeHash","runSnapshotId","runSnapshotHash","requestHash","handshakeNonce","leaseId","expectedArenaEpoch","expectedArenaRevision","tankObservationHash");
  if(KneekuraDebugOwnerInputs.n(m,"schemaVersion")!=1||KneekuraDebugOwnerInputs.n(m,"sampleIndex")!=next||!KneekuraDebugOwnerInputs.t(m,"ownerEnvelopeHash").equals(input.envelopeHash())||!KneekuraDebugOwnerInputs.t(m,"runSnapshotId").equals(config.runSnapshotId())||
   !KneekuraDebugOwnerInputs.t(m,"runSnapshotHash").equals(input.snapshotHash())||!KneekuraDebugOwnerInputs.t(m,"requestHash").equals(input.grant().requestHash())||!KneekuraDebugOwnerInputs.t(m,"handshakeNonce").equals(config.handshakeNonce())||!KneekuraDebugOwnerInputs.t(m,"leaseId").equals(input.grant().leaseId())||
   !KneekuraDebugOwnerInputs.t(m,"tankObservationHash").equals(KneekuraDebugOwnerInputs.t(input.envelope(),"tankObservationHash"))||KneekuraDebugOwnerInputs.n(m,"expectedArenaEpoch")!=state.arenaEpoch()||KneekuraDebugOwnerInputs.n(m,"expectedArenaRevision")!=state.arenaRevision())throw new IOException("TANK_ROSTER_MARKER_IDENTITY");
  gate.revalidateBoundary();verifyScope();KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(state,100);
  receipt=base(next);receipt.addProperty("markerHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(m)));
  KneekuraDebugOwnerFiles.writeNew(input.runDir(),dir+"/native-reservation.json",receipt);next++;started=System.nanoTime();
  try{
   JsonObject roster=sample(tick,state,next-1);
   gate.revalidateBoundary();verifyScope();KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(KneekuraDebugArenaRuntime.snapshotOwner(),0);
   receipt.addProperty("status",KneekuraDebugOwnerInputs.t(roster,"status"));receipt.add("roster",roster);
   pending=KneekuraDebugEvidenceWriter.recordArenaObservedAsync(config,state.arenaEpoch(),tick,level.getGameTime(),"TANK_ROOM_ROSTER","KneekuraDebugTankRosterOwner.sample",roster);
  }catch(Exception error){receipt.addProperty("status","REJECTED");receipt.addProperty("error",reason(error));pending=CompletableFuture.completedFuture(null);}
  return true;
 }
 private JsonObject sample(long tick,KneekuraDebugArenaController.Snapshot state,int index)throws IOException{
  JsonObject p=new JsonObject();p.addProperty("schemaVersion",1);p.addProperty("kind","tank_room_roster");p.add("identity",KneekuraDebugOwnerTriggers.identity(input,state));
  p.addProperty("ownerEnvelopeHash",input.envelopeHash());p.addProperty("tankObservationHash",KneekuraDebugOwnerInputs.t(input.envelope(),"tankObservationHash"));p.addProperty("sampleIndex",index);p.addProperty("dimension",level.dimension().location().toString());
  p.addProperty("boundsSemantics","MIN_INCLUSIVE_MAX_EXCLUSIVE");p.add("min",scope.json().get("min").deepCopy());p.add("max",scope.json().get("max").deepCopy());p.addProperty("serverTick",tick);p.addProperty("gameTime",level.getGameTime());
  JsonArray missing=new JsonArray();
  for(int x=Math.floorDiv(scope.minX(),16);x<=Math.floorDiv(scope.maxX()-1,16);x++)for(int z=Math.floorDiv(scope.minZ(),16);z<=Math.floorDiv(scope.maxZ()-1,16);z++)if(!level.getChunkSource().hasChunk(x,z))missing.add(vector(x,z));
  AABB box=new AABB(scope.minX(),scope.minY(),scope.minZ(),scope.maxX(),scope.maxY(),scope.maxZ());List<Entity> entities=new ArrayList<>();
  level.getEntities(EntityTypeTest.forClass(Entity.class),box,e->!e.isRemoved(),entities,scope.maxEntities()+1);
  LinkedHashMap<UUID,Entity> found=new LinkedHashMap<>();Set<String> reasons=new TreeSet<>();
  Set<UUID> visited=new HashSet<>();for(Entity e:entities)collect(e,0,box,found,visited,reasons);
  if(found.size()>scope.maxEntities())reasons.add("ENTITY_LIMIT");
  JsonArray rows=new JsonArray();found.values().stream().limit(scope.maxEntities()).sorted(Comparator.comparing(e->e.getUUID().toString())).forEach(e->rows.add(row(e,reasons)));
  JsonObject coverage=new JsonObject();coverage.addProperty("allChunksLoaded",missing.isEmpty());coverage.add("missingChunks",missing);p.add("coverage",coverage);
  JsonObject limits=new JsonObject();limits.addProperty("maxEntities",scope.maxEntities());limits.addProperty("maxSamples",scope.maxSamples());limits.addProperty("maxPassengerDepth",8);limits.addProperty("maxPacketBytes",65536);p.add("limits",limits);p.add("entities",rows);
  coverage(p,coverage,reasons,missing.isEmpty());
  while(KneekuraDebugActionJournal.canonical(p).getBytes(java.nio.charset.StandardCharsets.UTF_8).length>61440){
   if(rows.isEmpty())throw new IOException("TANK_ROSTER_PACKET_METADATA_LIMIT");rows.remove(rows.size()-1);reasons.add("BYTE_LIMIT");coverage(p,coverage,reasons,missing.isEmpty());
  }
  return p;
 }
 private void collect(Entity e,int depth,AABB box,Map<UUID,Entity> found,Set<UUID> path,Set<String> reasons){
  if(depth>8){reasons.add("PASSENGER_DEPTH");return;}
  if(path.contains(e.getUUID()))return;if(path.size()>=scope.maxEntities()+1){reasons.add("ENTITY_LIMIT");return;}path.add(e.getUUID());
  if(!e.isRemoved()&&e.level()==level&&box.intersects(e.getBoundingBox())){
   found.putIfAbsent(e.getUUID(),e);if(found.size()>scope.maxEntities()){reasons.add("ENTITY_LIMIT");return;}
  }
  int scanned=0;for(Entity child:e.getPassengers()){
   if(++scanned>scope.maxEntities()+1){reasons.add("ENTITY_LIMIT");break;}collect(child,depth+1,box,found,path,reasons);
   if(found.size()>scope.maxEntities())break;
  }
 }
 private JsonObject row(Entity e,Set<String> reasons){
  JsonObject r=new JsonObject();r.addProperty("uuid",e.getUUID().toString());String type=BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString();r.addProperty("entityType",type);
  r.add("world",vector(e.getX(),e.getY(),e.getZ()));r.add("local",vector(e.getX()-scope.minX(),e.getY()-scope.minY(),e.getZ()-scope.minZ()));AABB b=e.getBoundingBox();r.add("aabbMin",vector(b.minX,b.minY,b.minZ));r.add("aabbMax",vector(b.maxX,b.maxY,b.maxZ));
  r.addProperty("living",e instanceof LivingEntity);r.addProperty("mob",e instanceof Mob);r.addProperty("player",e instanceof Player);String known=null;
  for(var entry:input.grant().subjects().entrySet())if(entry.getValue().uuid().equals(e.getUUID().toString())&&entry.getValue().entityType().equals(type))known=entry.getKey();r.addProperty("knownSubjectId",known);
  r.addProperty("vehicleUuid",e.getVehicle()==null?null:e.getVehicle().getUUID().toString());JsonArray passengers=new JsonArray();int count=0;for(Entity child:e.getPassengers()){if(++count>65){reasons.add("ENTITY_LIMIT");break;}passengers.add(child.getUUID().toString());}r.add("passengerUuids",passengers);
  r.addProperty("fullyContained",scope.contains(b.minX,b.minY,b.minZ,b.maxX,b.maxY,b.maxZ));return r;
 }
 private static void coverage(JsonObject p,JsonObject c,Set<String> reasons,boolean loaded){JsonArray a=new JsonArray();reasons.forEach(a::add);c.add("truncationReasons",a);boolean complete=loaded&&reasons.isEmpty();p.addProperty("status",complete?"COMPLETE":"PARTIAL");p.addProperty("missingEntityNotAbsent",!complete);p.addProperty("subsetSelection",complete?"COMPLETE_SCOPE_UUID_SORTED":"NATIVE_ENUMERATION_SUBSET_UUID_SORTED");}
 private void complete()throws IOException{
  try{String hash=pending.join();if(hash!=null)receipt.addProperty("observationLineHash",hash);}catch(Exception e){receipt.remove("roster");receipt.addProperty("status","OUTCOME_UNKNOWN");receipt.addProperty("error",reason(e));}
  KneekuraDebugOwnerFiles.writeNew(input.runDir(),directory(next-1)+"/receipt.json",receipt);pending=null;receipt=null;
 }
 void close()throws IOException{if(pending!=null){if(!pending.isDone())pending.completeExceptionally(new IOException("TANK_ROSTER_OWNER_CLOSED"));complete();}}
 private JsonObject base(int index)throws IOException{JsonObject r=new JsonObject();r.addProperty("schemaVersion",1);r.addProperty("kind","tank_roster_receipt");r.addProperty("sampleIndex",index);r.addProperty("ownerEnvelopeHash",input.envelopeHash());r.addProperty("runSnapshotHash",input.snapshotHash());r.addProperty("requestHash",input.grant().requestHash());r.addProperty("observedAt",Instant.now().toString());return r;}
 private static String directory(int index){return "control/tank-roster/"+String.format(Locale.ROOT,"%02d",index);}
 private static JsonArray vector(double... values){JsonArray a=new JsonArray();for(double n:values){if(!Double.isFinite(n))throw new IllegalStateException("TANK_ROSTER_NON_FINITE");a.add(n);}return a;}
 private static String reason(Throwable e){while(e.getCause()!=null&&e.getCause()!=e)e=e.getCause();String s=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();return s.substring(0,Math.min(256,s.length()));}
}
