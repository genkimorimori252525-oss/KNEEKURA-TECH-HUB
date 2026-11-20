package kneekura.manual;

import com.google.gson.*;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.Level;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import org.joml.Vector3f;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.function.BooleanSupplier;

/**
 * Opt-in client trails (KNEEKURA_TANK_TRAILS=1) of positions actually sampled on the server thread for every Mob and
 * Projectile near the bound Player. Generic: no per-MOD hooks. Presentation only: no camera, input, entity, AI or world
 * change, no interpolation between samples. Style follows the legacy Motion overlay (NEW → yellow MIDDLE → fading red OLD,
 * projectiles hue-coded by UUID, mobs cyan). Bounded: 64 live entities, 128 retained traces, 100-tick age, 4096 lines/frame.
 */
public final class ManualTrails {
 static final int AGE_TICKS=100,MAX_LIVE=64,MAX_TRACES=128,MAX_LINES=4096,MOB_EVERY=2;static final double RANGE_XZ=48,RANGE_Y=32,GAP_BLOCKS=8;
 record Sample(long tick,double x,double y,double z){}
 record Trace(UUID id,boolean projectile,String type,List<Sample> samples){}
 private static final class Context {
  final MinecraftServer server;final UUID player;final String requestHash;final Path output;final long deadline;final BooleanSupplier live;
  final Map<UUID,ArrayDeque<Sample>> traces=new LinkedHashMap<>();final Map<UUID,Boolean> projectile=new HashMap<>();final Map<UUID,String> type=new HashMap<>();
  final Set<String> types=new TreeSet<>();final List<String> errors=new ArrayList<>();
  long sampledTicks,samples,overflowEntities,evictedTraces,renders,renderNanos,renderMaxNanos,truncatedFrames;int maxLive,maxLines;String reason="ACTIVE";boolean firstReceipt;
  volatile List<Trace> snapshot=List.of();
  Context(MinecraftServer server,UUID player,String requestHash,Path output,long deadline,BooleanSupplier live){this.server=server;this.player=player;this.requestHash=requestHash;this.output=output;this.deadline=deadline;this.live=live;}
 }
 private static volatile Context active;private static Context last;
 public static boolean requested(){return "1".equals(System.getenv("KNEEKURA_TANK_TRAILS"));}
 public static synchronized void arm(MinecraftServer server,UUID player,String requestHash,Path output,long began,long maxWallMs,BooleanSupplier live)throws Exception{
  if(!requested())return;if(active!=null||last!=null)throw new IllegalStateException("MANUAL_TRAILS_ALREADY_ARMED");
  var c=new Context(server,player,requestHash,output,began+maxWallMs*1_000_000L,live);Files.writeString(output.resolve("trails-armed.json"),facts(c)+"\n",StandardOpenOption.CREATE_NEW);active=c;last=c;
 }
 public static synchronized void clear(String reason){if(active!=null){active.reason=reason;active=null;}}
 public static synchronized JsonObject finish(){clear("SERVER_STOPPED");if(last==null)return null;var f=facts(last);try{Files.writeString(last.output.resolve("trails-result.json"),f+"\n",StandardOpenOption.CREATE_NEW);}catch(Exception e){last.errors.add(e.toString());}return f;}
 private static JsonObject facts(Context c){
  var x=new JsonObject();x.addProperty("renderer","tank-trails-v1");x.addProperty("requestHash",c.requestHash);x.addProperty("reason",c.reason);x.addProperty("at",Instant.now().toString());
  x.addProperty("scope","CLIENT_PRESENTATION_OF_SERVER_THREAD_POSITION_SAMPLES_NOT_EVIDENCE_NO_INTERPOLATION");
  x.addProperty("selection","Mob_OR_Projectile_WITHIN_48XZ_32Y_OF_BOUND_PLAYER_NEAREST_64");x.addProperty("ageTicks",AGE_TICKS);x.addProperty("mobSampleEveryTicks",MOB_EVERY);
  x.addProperty("sampledTicks",c.sampledTicks);x.addProperty("samples",c.samples);x.addProperty("maxLiveEntities",c.maxLive);x.addProperty("overflowEntities",c.overflowEntities);x.addProperty("evictedTraces",c.evictedTraces);
  x.addProperty("renderedFrames",c.renders);x.addProperty("maxLinesPerFrame",c.maxLines);x.addProperty("truncatedFrames",c.truncatedFrames);
  x.addProperty("renderCpuMeanNanos",c.renders==0?0:c.renderNanos/c.renders);x.addProperty("renderCpuMaxNanos",c.renderMaxNanos);x.addProperty("rawPixelsVerified",false);
  var t=new JsonArray();c.types.stream().limit(32).forEach(t::add);x.add("entityTypes",t);x.add("errors",new Gson().toJsonTree(c.errors));return x;
 }

 @SubscribeEvent public void sample(TickEvent.ServerTickEvent event){long t0=System.nanoTime();try{sample0(event);}finally{ManualScenario.overhead(System.nanoTime()-t0);}}
 private void sample0(TickEvent.ServerTickEvent event){
  var c=active;if(c==null||event.phase!=TickEvent.Phase.END)return;
  try{
   if(System.nanoTime()>=c.deadline||!c.live.getAsBoolean()){clear("WINDOW_ENDED");return;}
   var p=c.server.getPlayerList().getPlayer(c.player);if(p==null)return;var level=p.serverLevel();long tick=level.getGameTime();
   var near=level.getEntities((Entity)null,p.getBoundingBox().inflate(RANGE_XZ,RANGE_Y,RANGE_XZ),e->e instanceof Mob||e instanceof Projectile);
   near.sort(Comparator.comparingDouble((Entity e)->e.distanceToSqr(p)).thenComparing(e->e.getUUID().toString()));
   if(near.size()>MAX_LIVE){c.overflowEntities+=near.size()-MAX_LIVE;near=near.subList(0,MAX_LIVE);}c.maxLive=Math.max(c.maxLive,near.size());
   for(var e:near){
    boolean shot=e instanceof Projectile;if(!shot&&tick%MOB_EVERY!=0)continue;var id=e.getUUID();
    var d=c.traces.computeIfAbsent(id,k->new ArrayDeque<>());c.projectile.put(id,shot);var type=net.minecraft.world.entity.EntityType.getKey(e.getType()).toString();c.type.put(id,type);c.types.add(type);
    d.addLast(new Sample(tick,e.getX(),e.getY()+e.getBbHeight()*0.5,e.getZ()));c.samples++;
   }
   for(var it=c.traces.entrySet().iterator();it.hasNext();){var d=it.next().getValue();while(!d.isEmpty()&&tick-d.peekFirst().tick()>=AGE_TICKS)d.removeFirst();if(d.isEmpty())it.remove();}
   while(c.traces.size()>MAX_TRACES){var oldest=c.traces.entrySet().stream().min(Comparator.comparingLong(en->en.getValue().peekLast().tick())).orElseThrow().getKey();c.traces.remove(oldest);c.evictedTraces++;}
   var snap=new ArrayList<Trace>(c.traces.size());c.traces.forEach((id,d)->snap.add(new Trace(id,c.projectile.get(id),c.type.get(id),List.copyOf(d))));c.snapshot=List.copyOf(snap);c.sampledTicks++;
  }catch(Exception e){synchronized(ManualTrails.class){c.errors.add(e.toString());}clear("SAMPLE_FAILED");}
 }

 @SubscribeEvent public void render(RenderLevelStageEvent event){if(event.getStage()==RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS)draw(event);}
 private static void draw(RenderLevelStageEvent event){
  var c=active;if(c==null)return;var mc=Minecraft.getInstance();
  if(mc.level==null||mc.getSingleplayerServer()!=c.server||!mc.level.dimension().equals(Level.OVERWORLD))return;
  var traces=c.snapshot;if(traces.isEmpty())return;long started=System.nanoTime();var pose=event.getPoseStack();boolean pushed=false;
  try{
   var camera=event.getCamera().getPosition();long now=mc.level.getGameTime();pose.pushPose();pushed=true;pose.translate(-camera.x,-camera.y,-camera.z);
   var buffers=mc.renderBuffers().bufferSource();var out=buffers.getBuffer(RenderType.lines());int lines=0;boolean truncated=false;
   outer:for(var t:traces){
    var s=t.samples();int hash=0x811c9dc5;for(char ch:t.id().toString().toCharArray())hash=(hash^ch)*16777619;
    for(int i=0;i<s.size();i++){
     var b=s.get(i);int[] style=style(t.projectile(),hash,now-b.tick());if(style==null)continue;
     if(lines+3>MAX_LINES){truncated=true;break outer;}
     double r=t.projectile()?0.05:0.08;line(out,pose.last(),b.x()-r,b.y(),b.z(),b.x()+r,b.y(),b.z(),style);line(out,pose.last(),b.x(),b.y(),b.z()-r,b.x(),b.y(),b.z()+r,style);lines+=2;
     if(i==0)continue;var a=s.get(i-1);double dx=b.x()-a.x(),dy=b.y()-a.y(),dz=b.z()-a.z();double dist=Math.sqrt(dx*dx+dy*dy+dz*dz);
     if(dist==0||dist>GAP_BLOCKS*(b.tick()-a.tick()))continue; // teleport/respawn: never draw an invented connection
     if(t.projectile()){line(out,pose.last(),a.x(),a.y(),a.z(),a.x()+dx*0.6,a.y()+dy*0.6,a.z()+dz*0.6,style);} // dashed: projectile samples are per tick
     else line(out,pose.last(),a.x(),a.y(),a.z(),b.x(),b.y(),b.z(),style);
     lines++;
    }
   }
   buffers.endBatch(RenderType.lines());
   long cost=Math.max(0,System.nanoTime()-started);
   synchronized(ManualTrails.class){c.renders++;c.renderNanos+=cost;c.renderMaxNanos=Math.max(c.renderMaxNanos,cost);c.maxLines=Math.max(c.maxLines,lines);if(truncated)c.truncatedFrames++;
    if(!c.firstReceipt&&lines>0){c.firstReceipt=true;Files.writeString(c.output.resolve("trails-rendered.json"),facts(c)+"\n",StandardOpenOption.CREATE_NEW);}}
  }catch(Exception e){synchronized(ManualTrails.class){c.errors.add(e.toString());}clear("RENDER_FAILED");}finally{if(pushed)pose.popPose();}
 }
 /** Legacy age bands: <33 ticks NEW, <66 MIDDLE (blend to yellow), else OLD (blend to red, fading). Null when expired. */
 static int[] style(boolean projectile,int hash,long age){
  if(age<0||age>=AGE_TICKS)return null;int band=(int)(age*3/AGE_TICKS);int[] yellow={255,211,83},red={255,96,83},rgb={105,215,255};
  if(projectile){double hue=(100+Integer.remainderUnsigned(hash,180))/60.0;int sector=(int)Math.floor(hue);double f=hue-sector,low=76.5,up=low+178.5*f,down=255-178.5*f;
   double[] base=switch(sector){case 1->new double[]{down,255,low};case 2->new double[]{low,255,up};case 3->new double[]{low,down,255};default->new double[]{up,low,255};};
   for(int i=0;i<3;i++){rgb[i]=(int)Math.round(base[i]);if(band>0)rgb[i]=(int)Math.round(rgb[i]*(band==1?.5:.18)+(band==1?yellow:red)[i]*(band==1?.5:.82));}}
  else if(band>0)rgb=band==1?yellow.clone():red.clone();
  int alpha=band==0?255:band==1?210:(int)Math.round(180.0*(AGE_TICKS-age)/33);return new int[]{rgb[0],rgb[1],rgb[2],Math.max(0,Math.min(255,alpha))};
 }
 private static void line(VertexConsumer out,PoseStack.Pose pose,double x,double y,double z,double a,double b,double c,int[] s){
  var n=new Vector3f((float)(a-x),(float)(b-y),(float)(c-z));if(n.lengthSquared()==0)n.set(0,1,0);n.normalize();
  out.vertex(pose.pose(),(float)x,(float)y,(float)z).color(s[0],s[1],s[2],s[3]).normal(pose.normal(),n.x,n.y,n.z).endVertex();
  out.vertex(pose.pose(),(float)a,(float)b,(float)c).color(s[0],s[1],s[2],s[3]).normal(pose.normal(),n.x,n.y,n.z).endVertex();
 }
}
