package kneekura.manual;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugEnv;
import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugReadyWriter;
import com.google.gson.*;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.client.Minecraft;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.entity.player.AttackEntityEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;

/** Opt-in canonical-supervisor adapter, not an Arena controller or input provider. */
@Mod(ManualNativeAdapter.MOD_ID)
public final class ManualNativeAdapter {
 public static final String MOD_ID="kneekura_manual_adapter";
 private static final Gson GSON=new Gson();
 private static final long PID=ProcessHandle.current().pid();
 private static final String JVM=Instant.ofEpochMilli(ManagementFactory.getRuntimeMXBean().getStartTime()).toString();
 private static volatile String forgeAt;
 public ManualNativeAdapter(){
  FMLJavaModLoadingContext.get().getModEventBus().addListener((FMLClientSetupEvent e)->forgeAt=Instant.now().toString());
  MinecraftForge.EVENT_BUS.register(new Client());MinecraftForge.EVENT_BUS.register(new Server());
 }
 private static KneekuraDebugEnv.Config env;
 private static JsonObject request;
 private static Path output,raw;
 private static UUID playerId,subjectId;
 private static String requestHash;
 private static volatile boolean disabled,ready,ended,closing,worldStopped,stopRequested;
 private static long beganNanos;
 private static long initializedNanos;
 private static int startupDiagnostics;
 private static String previousScreen="UNOBSERVED";
 private static int ticks,stable;
 private static long sequence,dropped;
 private static String reason="NOT_RUN";
 private static final List<String> errors=new CopyOnWriteArrayList<>();
 private static final ThreadPoolExecutor writer=new ThreadPoolExecutor(1,1,0,TimeUnit.MILLISECONDS,new ArrayBlockingQueue<>(128),r->{var t=new Thread(r,"manual-event-writer");t.setDaemon(true);return t;},new ThreadPoolExecutor.AbortPolicy());
 private static BufferedWriter stream;
 private static final Map<UUID,Projectile> shots=new LinkedHashMap<>();
 private static final Map<UUID,String> shotStates=new HashMap<>();
 private record Pending(LivingEntity entity,float health,UUID direct){}
 private static final List<Pending> pending=new ArrayList<>();
 private static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
 private static void exclusive(Path p,JsonObject value)throws IOException{Files.createDirectories(p.getParent());Files.writeString(p,GSON.toJson(value)+"\n",StandardOpenOption.CREATE_NEW);}
 private static void atomicExclusive(Path p,JsonObject value)throws IOException{Files.createDirectories(p.getParent());Path pending=p.resolveSibling(p.getFileName()+".pending-"+PID);Files.writeString(pending,GSON.toJson(value)+"\n",StandardOpenOption.CREATE_NEW);try(var f=FileChannel.open(pending,StandardOpenOption.WRITE)){f.force(true);}Files.createLink(p,pending);Files.delete(pending);}
 private static boolean initialize(){
  if(env!=null)return !disabled;
  if(!"1".equals(System.getenv("KNEEKURA_MANUAL_ENABLED")))return false;
  try{
   env=KneekuraDebugEnv.fromSystemEnvironment();if(!env.enabled()||env.ownerSetup()!=null)throw new IOException("MANUAL_NO_SCOPED_OWNER");
   Path file=Path.of(System.getenv("KNEEKURA_MANUAL_REQUEST")).toRealPath();byte[] bytes=Files.readAllBytes(file);if(bytes.length>16384)throw new IOException("MANUAL_REQUEST_SIZE");
   requestHash=sha(bytes);if(!requestHash.equals(System.getenv("KNEEKURA_MANUAL_REQUEST_SHA256")))throw new IOException("MANUAL_REQUEST_HASH");
   request=JsonParser.parseString(new String(bytes,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
   ManualRequest.validate(request);
   if(!requestHash.equals(System.getProperty("kneekura.tank.requestSha256"))||!request.get("installHash").getAsString().equals(System.getProperty("kneekura.tank.installSha256"))||!request.get("worldDir").getAsString().equals(System.getProperty("kneekura.tank.world")))throw new IOException("MANUAL_PROCESS_ARGUMENT_BINDING");
   Path trial=Path.of(request.get("trialDir").getAsString()).toRealPath();
   if(!file.equals(trial.resolve("inputs/manual-request.json"))||!env.runDir().toRealPath().startsWith(trial))throw new IOException("MANUAL_REQUEST_PATH");
   Path container=ModList.get().getModFileById(MOD_ID).getFile().getFilePath().toRealPath();
   if(!container.equals(trial.resolve("inputs/manual-adapter.jar"))||!sha(Files.readAllBytes(container)).equals(request.get("adapterHash").getAsString()))throw new IOException("MANUAL_ADAPTER_CONTAINER_HASH");
   try(var jar=new java.util.jar.JarFile(container.toFile());var archived=jar.getInputStream(jar.getJarEntry("kneekura/manual/ManualNativeAdapter.class"));var actual=ManualNativeAdapter.class.getResourceAsStream("ManualNativeAdapter.class")){if(!sha(archived.readAllBytes()).equals(sha(actual.readAllBytes())))throw new IOException("MANUAL_CLASS_RESOURCE_LINK");}
   for(var material:request.getAsJsonArray("materials")){var m=material.getAsJsonObject();var loaded=ModList.get().getModFileById(m.get("id").getAsString());if(loaded==null||!sha(Files.readAllBytes(loaded.getFile().getFilePath())).equals(m.get("sha256").getAsString()))throw new IOException("MANUAL_LOADED_MATERIAL_HASH_"+m.get("id").getAsString());}
   playerId=UUID.fromString(request.get("playerUuid").getAsString());subjectId=UUID.fromString(request.get("subjectUuid").getAsString());
   output=env.runDir().resolve("evidence/derived/manual-interaction");Files.createDirectories(output);
   var claim=new JsonObject();claim.addProperty("v",1);claim.addProperty("debugSessionId",env.debugSessionId());claim.addProperty("runId",env.runId());claim.addProperty("runSnapshotId",env.runSnapshotId());claim.addProperty("processEpoch",env.processEpoch());claim.addProperty("requestHash",requestHash);claim.addProperty("pid",PID);claim.addProperty("jvmStartedAtEpochMs",ManagementFactory.getRuntimeMXBean().getStartTime());claim.addProperty("commandHint",ProcessHandle.current().info().command().orElseThrow());for(String key:List.of("nonce","installHash","adapterHash"))claim.add(key,request.get(key).deepCopy());atomicExclusive(trial.resolve("manual-claim.json"),claim);initializedNanos=System.nanoTime();
   raw=env.evidenceRawDir().resolve("manual-"+PID+".jsonl");Files.createDirectories(raw.getParent());stream=Files.newBufferedWriter(raw,StandardOpenOption.CREATE_NEW);
   return true;
  }catch(Exception failure){errors.add(failure.toString());disabled=true;System.err.println("MANUAL_ADAPTER_DISABLED "+failure);return false;}
 }
 private static ServerPlayer bound(){
  var server=Minecraft.getInstance().getSingleplayerServer();if(server==null)return null;
  var player=server.getPlayerList().getPlayer(playerId);if(player==null||player instanceof FakePlayer||player.connection==null||!player.connection.connection.isConnected()||!player.gameMode.isSurvival())return null;
  try{if(!server.getWorldPath(LevelResource.ROOT).toRealPath().equals(Path.of(request.get("worldDir").getAsString()).toRealPath())||!server.getWorldData().getLevelName().equals(env.worldName()))return null;}catch(IOException failure){return null;}
  return player;
 }
 private static boolean allowed(){return ready&&!ended&&!closing&&bound()!=null;}
 private static synchronized void observation(String method,Entity subject,JsonObject payload){
  if(closing||ended&& !method.equals("SESSION_END"))return;
  if(sequence>=request.get("maxEvents").getAsInt()){end("EVENT_BUDGET");return;}
  var row=new JsonObject();long seq=++sequence;
  row.addProperty("v",1);row.addProperty("kind","observation");row.addProperty("observationId",env.runId()+"-manual-"+seq);
  row.addProperty("debugSessionId",env.debugSessionId());row.addProperty("runId",env.runId());row.addProperty("runSnapshotId",env.runSnapshotId());row.addProperty("processEpoch",env.processEpoch());
  row.addProperty("arenaEpoch",1);row.addProperty("resourceEpoch",1);row.addProperty("writerId","manual-"+PID);row.addProperty("writerSeq",seq);row.addProperty("writerDroppedTotal",dropped);row.addProperty("writerQueueDepth",writer.getQueue().size());
  row.addProperty("level","L1");row.addProperty("lane","MANUAL_INTERACTION");row.addProperty("observedAt",Instant.now().toString());row.addProperty("epistemicStatus","OBSERVED");
  var scope=new JsonObject();scope.addProperty("kind","ENTITY_UUID");scope.addProperty("entityUuid",subject==null?playerId.toString():subject.getUUID().toString());row.add("scope",scope);
  var source=new JsonObject();source.addProperty("side","SERVER");source.addProperty("method",method);row.add("source",source);
  payload.addProperty("requestHash",requestHash);payload.addProperty("tick",subject==null?-1:subject.level().getGameTime());payload.addProperty("pid",PID);row.add("payload",payload);
  var complete=new JsonObject();complete.addProperty("complete",false);complete.addProperty("status","PARTIAL");row.add("completeness",complete);
  String line=GSON.toJson(row)+"\n";try{writer.execute(()->{try{stream.write(line);stream.flush();}catch(IOException e){errors.add(e.toString());}});}catch(RejectedExecutionException e){dropped++;}
 }
 private static JsonObject shotState(Projectile shot){var x=new JsonObject();x.addProperty("uuid",shot.getUUID().toString());x.addProperty("owner",shot.getOwner()==null?null:shot.getOwner().getUUID().toString());x.addProperty("removed",shot.isRemoved());x.addProperty("x",shot.getX());x.addProperty("y",shot.getY());x.addProperty("z",shot.getZ());x.addProperty("scope","VANILLA_PROJECTILE_OWNER_NOT_TARGET_SPECIFIC_RALLY_STATE");return x;}
 private static void end(String why){if(!ended){reason=why;ended=true;observation("SESSION_END",bound(),new JsonObject());try{var x=new JsonObject();x.addProperty("reason",reason);x.addProperty("requestHash",requestHash);exclusive(output.resolve("window-end.json"),x);}catch(IOException e){errors.add(e.toString());}}}
 public static final class Client {
  @SubscribeEvent public void tick(TickEvent.ClientTickEvent event){
   if(event.phase!=TickEvent.Phase.END||!initialize()||disabled)return;
   var mc=Minecraft.getInstance();
   if(!ready&&startupDiagnostics<8){String screen=mc.screen==null?"NONE":mc.screen.getClass().getName();if(!screen.equals(previousScreen)){previousScreen=screen;startupDiagnostics++;var diagnostic=new JsonObject();diagnostic.addProperty("at",Instant.now().toString());diagnostic.addProperty("requestHash",requestHash);diagnostic.addProperty("screenClass",screen);diagnostic.addProperty("screenTitle",mc.screen==null?"":mc.screen.getTitle().getString().substring(0,Math.min(256,mc.screen.getTitle().getString().length())));diagnostic.addProperty("clientWorld",mc.level!=null);diagnostic.addProperty("clientPlayer",mc.player!=null);diagnostic.addProperty("integratedServer",mc.getSingleplayerServer()!=null);try{Files.writeString(output.resolve("startup-diagnostics.jsonl"),GSON.toJson(diagnostic)+"\n",StandardOpenOption.CREATE,StandardOpenOption.APPEND);}catch(IOException failure){errors.add(failure.toString());}}}
   if(!stopRequested&&Files.exists(env.shutdownRequestFile()))try{
    var stop=JsonParser.parseString(Files.readString(env.shutdownRequestFile())).getAsJsonObject();if(!ManualRequest.stopMatches(stop,env))throw new IOException("MANUAL_STOP_IDENTITY");stopRequested=true;
    ManualShutdown.request(()->{if(ready)end("SUPERVISOR_STOP");else{var x=new JsonObject();x.addProperty("requestHash",requestHash);x.addProperty("status","STOP_BEFORE_READY_NOT_WORLD_ACCEPTANCE");exclusive(output.resolve("bootstrap-stop.json"),x);}},mc::stop,failure->errors.add(failure.toString()));return;
   }catch(Exception e){errors.add(e.toString());}
   if(!ready&&!stopRequested&&(System.nanoTime()-initializedNanos)/1_000_000>=180000){stopRequested=true;try{var x=new JsonObject();x.addProperty("requestHash",requestHash);x.addProperty("status","STARTUP_TIMEOUT_NOT_WORLD_ACCEPTANCE");exclusive(output.resolve("bootstrap-timeout.json"),x);}catch(IOException failure){errors.add(failure.toString());}mc.stop();return;}
   if(!ready){
    if(mc.level==null||mc.player==null||mc.getConnection()==null||forgeAt==null||bound()==null||mc.getSingleplayerServer().overworld().getEntity(subjectId)==null||!mc.getSingleplayerServer().overworld().getEntity(subjectId).isAlive()){stable=0;return;}
    if(++stable<5)return;
    try{
     String now=Instant.now().toString();List<String> mods=ModList.get().getMods().stream().map(m->m.getModId()+"@"+m.getVersion()).sorted().toList();String probe;
     try(var in=ManualNativeAdapter.class.getResourceAsStream("ManualNativeAdapter.class")){probe="sha256:"+sha(in.readAllBytes());}
     var runtime=new KneekuraDebugReadyWriter.RuntimeInfo(net.minecraft.SharedConstants.getCurrentVersion().getName(),net.minecraftforge.versions.forge.ForgeVersion.getVersion(),System.getProperty("java.version"),"integrated-singleplayer",probe,ProcessHandle.current().info().command().orElseThrow(),mods);
     var milestones=new KneekuraDebugReadyWriter.Milestones(JVM,forgeAt,now,now,now,now);
     var binding=new JsonObject();binding.addProperty("playerUuid",bound().getUUID().toString());binding.addProperty("worldDir",request.get("worldDir").getAsString());binding.addProperty("requestHash",requestHash);binding.addProperty("pid",PID);binding.addProperty("runSnapshotId",env.runSnapshotId());exclusive(output.resolve("binding.json"),binding);
     beganNanos=System.nanoTime();ready=true;observation("NATIVE_PLAYER_BOUND",bound(),binding.deepCopy());
     KneekuraDebugReadyWriter.write(env,new KneekuraDebugReadyWriter.ReadyState(PID,milestones,runtime));
    }catch(Exception e){errors.add(e.toString());disabled=true;System.err.println("MANUAL_READY_FAILED "+e);}
   }
   if(ready&&!ended&&(System.nanoTime()-beganNanos)/1_000_000>=request.get("maxWallMs").getAsLong())end("WALL_LIMIT");
   if(ready&&!ended&&bound()==null)end("PLAYER_BINDING_LOST");
   if(ready&&ended&&!stopRequested){stopRequested=true;mc.stop();}
  }
 }
 public static final class Server {
  @SubscribeEvent public void joined(EntityJoinLevelEvent e){if(!ready||e.getLevel().isClientSide()||!allowed()||!(e.getEntity() instanceof Projectile shot)||shot.getOwner()==null||!subjectId.equals(shot.getOwner().getUUID()))return;if(shots.size()<32){shots.put(shot.getUUID(),shot);var x=shotState(shot);observation("PROJECTILE_JOIN",shot,x);shotStates.put(shot.getUUID(),String.valueOf(x.get("owner")));}else errors.add("PROJECTILE_TRACKING_TRUNCATED");}
  @SubscribeEvent(priority=EventPriority.LOWEST,receiveCanceled=true) public void attack(AttackEntityEvent e){if(!allowed()||e.getEntity()!=bound()||!(e.getTarget() instanceof Projectile shot)||!shots.containsKey(shot.getUUID()))return;var x=shotState(shot);x.addProperty("canceledAtLowest",e.isCanceled());x.addProperty("playerUuid",e.getEntity().getUUID().toString());observation("AttackEntityEvent_LOWEST",shot,x);}
  @SubscribeEvent(priority=EventPriority.LOWEST,receiveCanceled=true) public void hurt(LivingHurtEvent e){if(!allowed()||e.getEntity().level().isClientSide()||!Set.of(playerId,subjectId).contains(e.getEntity().getUUID()))return;var x=new JsonObject();x.addProperty("healthBefore",e.getEntity().getHealth());x.addProperty("amountBeforeFinalListeners",e.getAmount());x.addProperty("canceledAtLowest",e.isCanceled());var direct=e.getSource().getDirectEntity();x.addProperty("directUuid",direct==null?null:direct.getUUID().toString());observation("LivingHurtEvent_LOWEST",e.getEntity(),x);if(pending.size()<8)pending.add(new Pending(e.getEntity(),e.getEntity().getHealth(),direct==null?null:direct.getUUID()));else errors.add("HURT_PREFIX_TRUNCATED");}
  @SubscribeEvent public void tick(TickEvent.ServerTickEvent e){if(e.phase!=TickEvent.Phase.END||!ready||closing)return;
   if(!ended){ticks++;if(ticks>=request.get("maxTicks").getAsInt())end("TICK_LIMIT");}
   if(!allowed())return;
   for(var p:pending){var x=new JsonObject();x.addProperty("healthBeforeEvent",p.health());x.addProperty("healthAtEnd",p.entity().getHealth());x.addProperty("directUuid",p.direct()==null?null:p.direct().toString());x.addProperty("multipleCausesPossible",true);observation("POST_HURT_END",p.entity(),x);}pending.clear();
   for(var it=shots.entrySet().iterator();it.hasNext();){var shot=it.next().getValue();String state=String.valueOf(shotState(shot).get("owner"));if(!state.equals(shotStates.get(shot.getUUID()))||shot.isRemoved())observation(shot.isRemoved()?"PROJECTILE_REMOVED_NOT_IMPACT_PROOF":"OWNERSHIP_CHANGE_END",shot,shotState(shot));shotStates.put(shot.getUUID(),state);if(shot.isRemoved()){it.remove();shotStates.remove(shot.getUUID());}}
  }
  @SubscribeEvent public void stopping(ServerStoppingEvent e){if(ready)end("USER_OR_NATIVE_STOP");}
  @SubscribeEvent public void stopped(ServerStoppedEvent e){if(env==null||disabled)return;worldStopped=true;closing=true;writer.shutdown();boolean clean=false;try{clean=writer.awaitTermination(3,TimeUnit.SECONDS);stream.flush();stream.close();try(var f=FileChannel.open(raw,StandardOpenOption.WRITE)){f.force(true);}clean&=errors.isEmpty()&&dropped==0;}catch(Exception failure){errors.add(failure.toString());}
   try{var result=new JsonObject();result.addProperty("scope","FINITE_MANUAL_EVENTS_NOT_COMPLETE_RALLY");result.addProperty("requestHash",requestHash);result.addProperty("reason",reason);result.addProperty("ticks",ticks);result.addProperty("pid",PID);result.addProperty("worldStopped",worldStopped);result.addProperty("events",sequence);result.addProperty("dropped",dropped);result.add("errors",GSON.toJsonTree(errors));exclusive(output.resolve("result.json"),result);
    var ack=new JsonObject();ack.addProperty("v",1);ack.addProperty("debugSessionId",env.debugSessionId());ack.addProperty("runId",env.runId());ack.addProperty("runSnapshotId",env.runSnapshotId());ack.addProperty("processEpoch",env.processEpoch());ack.addProperty("clean",clean);ack.addProperty("status",clean?"CLEAN_EVIDENCE_SHUTDOWN":"MANUAL_EVIDENCE_UNCLEAN");ack.addProperty("ackedAt",Instant.now().toString());ack.addProperty("finalWriterSeq",sequence);ack.addProperty("writerDroppedTotal",dropped);ack.addProperty("remainingQueue",writer.getQueue().size());ack.addProperty("worldStopped",true);exclusive(env.shutdownAckFile(),ack);
   }catch(IOException failure){System.err.println("MANUAL_CLOSE_FAILED "+failure);}
  }
 }
}
