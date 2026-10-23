package kneekura.manual;

import com.google.gson.*;
import net.minecraft.client.Minecraft;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BooleanSupplier;

/** Explicit v3, read-only supplementary trace; never part of the manual event lane. */
public final class ManualMotionDiagnostics {
 private static final Gson GSON=new Gson();
 private static final class Context {
  final MinecraftServer server;final UUID subject,player;final String requestHash;final Path directory;
  final JsonObject limits;final long deadline;final BooleanSupplier live;final BufferedWriter stream;final ThreadPoolExecutor writer;
  final Map<String,Integer> counts=new LinkedHashMap<>();final List<String> errors=new CopyOnWriteArrayList<>();final AtomicInteger written=new AtomicInteger();
  volatile int entityId=-1;long bytes,sequence,tickStart,previousTick,previousFrame;int dropped,missing;boolean truncated,closed,activated;String reason="ACTIVE";
  Context(MinecraftServer server,JsonObject request,String hash,Path output,long began,BooleanSupplier live)throws Exception{
   this.server=server;subject=UUID.fromString(request.get("subjectUuid").getAsString());player=UUID.fromString(request.get("playerUuid").getAsString());requestHash=hash;directory=output;limits=request.getAsJsonObject("diagnostics").deepCopy();this.live=live;
   if(!server.getWorldPath(LevelResource.ROOT).toRealPath().equals(Path.of(request.get("worldDir").getAsString()).toRealPath()))throw new IOException("DIAGNOSTIC_WORLD_BINDING");
   deadline=began+Math.min(limits.get("maxWallMs").getAsLong(),request.get("maxWallMs").getAsLong())*1_000_000L;
   stream=Files.newBufferedWriter(output.resolve("motion.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
   writer=new ThreadPoolExecutor(1,1,0,TimeUnit.MILLISECONDS,new ArrayBlockingQueue<>(limits.get("maxQueue").getAsInt()),r->{var t=new Thread(r,"tank-motion-diagnostic-writer");t.setDaemon(true);return t;},new ThreadPoolExecutor.AbortPolicy());
  }
 }
 private static volatile Context context;
 public static synchronized void arm(MinecraftServer server,JsonObject request,String hash,Path output,long began,BooleanSupplier live)throws Exception{
  if(request.get("v").getAsInt()!=3)return;
  if(context!=null)throw new IllegalStateException("DIAGNOSTIC_ALREADY_ARMED");
  ManualDiagnosticsLimits.validate(request.getAsJsonObject("diagnostics"),request.get("maxWallMs").getAsLong());
  context=new Context(server,request,hash,output,began,live);
 }
 public static synchronized void activate(){if(context!=null)context.activated=true;}
 private static boolean active(Context c){
  if(c==null||c.closed||!c.activated)return false;
  if(!c.reason.equals("ACTIVE"))return false;
  if(!c.live.getAsBoolean()){c.reason="PARENT_WINDOW_ENDED";return false;}
  if(System.nanoTime()>=c.deadline){c.reason="SUBLEASE_EXPIRED";return false;}
  return true;
 }
 public static synchronized void clear(String reason){var c=context;if(c!=null&&c.reason.equals("ACTIVE"))c.reason=reason;}
 private static JsonObject vector(double x,double y,double z){var v=new JsonObject();v.addProperty("x",x);v.addProperty("y",y);v.addProperty("z",z);return v;}
 private static JsonObject entity(Entity e){
  var row=new JsonObject();row.addProperty("tick",e.level().getGameTime());row.addProperty("entityUuid",e.getUUID().toString());row.add("position",vector(e.getX(),e.getY(),e.getZ()));var v=e.getDeltaMovement();row.add("velocity",vector(v.x,v.y,v.z));row.addProperty("yaw",e.getYRot());row.addProperty("pitch",e.getXRot());row.addProperty("bodyYaw",e instanceof LivingEntity l?l.yBodyRot:e.getYRot());return row;
 }
 private static void emit(Context c,String kind,JsonObject row){
  String cap=switch(kind){case "SERVER"->"maxServerSamples";case "CLIENT"->"maxClientSamples";default->"maxFrameSamples";};
  int count=c.counts.getOrDefault(kind,0);if(count>=c.limits.get(cap).getAsInt()){c.truncated=true;return;}
  row.addProperty("side",kind);row.addProperty("nanoTime",System.nanoTime());row.addProperty("sequence",c.sequence+1);row.addProperty("requestHash",c.requestHash);row.addProperty("pid",ProcessHandle.current().pid());
  String line=GSON.toJson(row)+"\n";int bytes=line.getBytes(StandardCharsets.UTF_8).length;
  String admission=ManualDiagnosticsLimits.admission(c.limits,kind,count,c.bytes,bytes,System.nanoTime(),c.deadline);
  if(!admission.equals("ALLOW")){c.truncated=true;if(!admission.equals("SAMPLE_LIMIT"))c.reason=admission;return;}
  c.sequence++;c.bytes+=bytes;c.counts.put(kind,count+1);
  try{c.writer.execute(()->{try{c.stream.write(line);c.written.incrementAndGet();}catch(IOException e){c.errors.add(e.toString());}});}catch(RejectedExecutionException e){c.dropped++;c.truncated=true;}
 }
 private static void failed(Exception failure){var c=context;if(c!=null){c.errors.add(failure.toString());clear("SAMPLING_FAILED");}}
 private static Entity clientEntity(Context c){
  var mc=Minecraft.getInstance();
  if(mc.level==null||mc.getSingleplayerServer()!=c.server||!mc.level.dimension().equals(Level.OVERWORLD)||mc.player==null||!mc.player.getUUID().equals(c.player)||mc.getConnection()==null){clear("CLIENT_BINDING_LOST");return null;}
  var e=mc.level.getEntity(c.entityId);if(e==null||!e.getUUID().equals(c.subject)||!e.isAlive()){c.missing++;return null;}return e;
 }
 @SubscribeEvent public void server(TickEvent.ServerTickEvent event){synchronized(ManualMotionDiagnostics.class){try{
  var c=context;if(!active(c))return;if(!c.server.isSameThread())return;
  if(event.phase==TickEvent.Phase.START){c.tickStart=System.nanoTime();return;}
  var player=c.server.getPlayerList().getPlayer(c.player);
  if(player==null||player instanceof FakePlayer||player.connection==null||!player.connection.connection.isConnected()||!player.gameMode.isSurvival()||player.level()!=c.server.overworld()){clear("SERVER_BINDING_LOST");return;}
  var e=c.server.overworld().getEntity(c.subject);if(e==null||!e.isAlive()){clear("SERVER_SUBJECT_LOST");return;}
  c.entityId=e.getId();long now=System.nanoTime();var row=entity(e);row.addProperty("tickDurationNs",c.tickStart==0?-1:now-c.tickStart);row.addProperty("tickIntervalNs",c.previousTick==0?-1:now-c.previousTick);c.previousTick=now;emit(c,"SERVER",row);
 }catch(Exception failure){failed(failure);}}}
 @SubscribeEvent public void client(TickEvent.ClientTickEvent event){if(event.phase!=TickEvent.Phase.END)return;synchronized(ManualMotionDiagnostics.class){try{
  var c=context;if(!active(c))return;var e=clientEntity(c);if(e==null)return;var row=entity(e);row.addProperty("paused",Minecraft.getInstance().isPaused());emit(c,"CLIENT",row);
 }catch(Exception failure){failed(failure);}}}
 @SubscribeEvent public void frame(RenderLevelStageEvent event){if(event.getStage()!=RenderLevelStageEvent.Stage.AFTER_ENTITIES)return;synchronized(ManualMotionDiagnostics.class){try{
  var c=context;if(!active(c))return;var e=clientEntity(c);if(e==null)return;var mc=Minecraft.getInstance();long now=System.nanoTime();var row=entity(e);float partial=event.getPartialTick();var rendered=e.getPosition(partial);
  row.addProperty("partialTick",partial);row.add("interpolatedPosition",vector(rendered.x,rendered.y,rendered.z));row.addProperty("interpolatedBodyYaw",e instanceof LivingEntity l?net.minecraft.util.Mth.rotLerp(partial,l.yBodyRotO,l.yBodyRot):e.getViewYRot(partial));row.addProperty("frameIntervalNs",c.previousFrame==0?-1:now-c.previousFrame);c.previousFrame=now;row.addProperty("paused",mc.isPaused());emit(c,"FRAME",row);
 }catch(Exception failure){failed(failure);}}}
 public static JsonObject finish(){
  Context c;synchronized(ManualMotionDiagnostics.class){c=context;if(c==null)return null;clear("SERVER_STOPPED");c.closed=true;c.writer.shutdown();}
  boolean flushed=false;try{flushed=c.writer.awaitTermination(3,TimeUnit.SECONDS);if(flushed){c.stream.flush();c.stream.close();}else c.errors.add("DIAGNOSTIC_WRITER_TIMEOUT");}catch(Exception e){c.errors.add(e.toString());}
  var result=new JsonObject();result.addProperty("status",!flushed||!c.errors.isEmpty()?"FAILED":c.truncated||c.dropped>0?"PARTIAL":"CLOSED_TRACE");result.addProperty("remainingQueue",c.writer.getQueue().size());result.addProperty("schemaHash",ManualDiagnosticsLimits.SCHEMA_HASH);result.addProperty("requestHash",c.requestHash);result.addProperty("subjectUuid",c.subject.toString());result.addProperty("pid",ProcessHandle.current().pid());result.addProperty("reason",c.reason);result.addProperty("active",false);result.add("limits",c.limits);result.add("reservedSamples",GSON.toJsonTree(c.counts));result.addProperty("written",c.written.get());result.addProperty("bytesReserved",c.bytes);result.addProperty("dropped",c.dropped);result.addProperty("missingSubjectSamples",c.missing);result.addProperty("truncated",c.truncated);result.addProperty("flushed",flushed);result.add("errors",GSON.toJsonTree(c.errors));result.addProperty("scope","READ_ONLY_FINITE_SUPPLEMENT_NOT_MANUAL_EVENT_COMPLETENESS_OR_CAUSAL_PROOF");
  try{if(flushed){byte[] bytes=Files.readAllBytes(c.directory.resolve("motion.jsonl"));result.addProperty("fileSha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));}Files.writeString(c.directory.resolve("diagnostics-result.json"),GSON.toJson(result)+"\n",StandardOpenOption.CREATE_NEW);}catch(Exception e){c.errors.add(e.toString());result.add("errors",GSON.toJsonTree(c.errors));}
  return result;
 }
}
