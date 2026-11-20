package kneekura.manual;

import com.google.gson.*;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.entity.schedule.Activity;
import net.minecraft.world.level.Level;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import org.joml.Vector3f;
import java.io.BufferedWriter;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.BooleanSupplier;
import java.util.regex.Pattern;

/**
 * Opt-in generic AI lens (KNEEKURA_TANK_AI=1): WHAT each nearby Mob's AI is doing, read only through public vanilla
 * surfaces (running Goals of goalSelector/targetSelector, Brain activities/behaviors, getTarget, the navigation path) plus
 * a read-only, cached scan of state-like fields that the MOD's own entity classes declare (enum fields, EntityDataAccessor
 * values, boolean/int fields named like phase/state/mode). No per-MOD hooks, no mixins, nothing is written to the world.
 * It does not show WHY (scores, private conditions). Server thread samples every 5 ticks; ai.jsonl records changes only.
 */
public final class ManualAiLens {
 static final int EVERY=5,MAX_MOBS=32,MAX_LABELS=16,MAX_LABEL_LINES=5,MAX_WHY=8,MAX_PATH=32,MAX_FIELDS=8,MAX_RECORDS=10000,MAX_LINES=2048;
 static final double RANGE_XZ=48,RANGE_Y=32,LABEL_RANGE=24,LABEL_MIN=3,GROUP=4;
 static final Pattern STATE_NAME=Pattern.compile("(?i)phase|state|stage|mode"),FLAG_NAME=Pattern.compile("(?i)phase|state|stage|mode|attack|charg|cast|enrag|angry|aggro");
 record Probe(String name,Field field,EntityDataAccessor<?> accessor){}
 record View(UUID id,List<String> labels,UUID target,double[] path){}
 private static final Map<Class<?>,List<Probe>> PROBES=new ConcurrentHashMap<>();
 private static final class Context {
  final MinecraftServer server;final UUID player;final String requestHash;final Path output;final long deadline;final BooleanSupplier live;final BufferedWriter log;
  final Map<UUID,String> lastKey=new HashMap<>(),lastType=new HashMap<>();final Map<UUID,Map<String,String>> lastFields=new HashMap<>();final Map<String,long[]> churn=new HashMap<>();final Set<String> types=new TreeSet<>(),goals=new TreeSet<>(),explained=new TreeSet<>();final List<String> errors=new ArrayList<>();
  long whyErrors,sampledTicks,records,droppedRecords,overflowMobs,renders,renderNanos,renderMaxNanos,truncatedFrames;int maxMobs,maxLines,maxLabels,stateProbes;String reason="ACTIVE";boolean firstReceipt,closed;
  volatile List<View> snapshot=List.of();
  Context(MinecraftServer server,UUID player,String requestHash,Path output,long deadline,BooleanSupplier live,BufferedWriter log){this.server=server;this.player=player;this.requestHash=requestHash;this.output=output;this.deadline=deadline;this.live=live;this.log=log;}
 }
 private static volatile Context active;private static Context last;
 public static boolean requested(){return "1".equals(System.getenv("KNEEKURA_TANK_AI"));}
 public static synchronized void arm(MinecraftServer server,UUID player,String requestHash,Path output,long began,long maxWallMs,BooleanSupplier live)throws Exception{
  if(!requested())return;if(active!=null||last!=null)throw new IllegalStateException("MANUAL_AI_LENS_ALREADY_ARMED");
  var log=Files.newBufferedWriter(output.resolve("ai.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
  var c=new Context(server,player,requestHash,output,began+maxWallMs*1_000_000L,live,log);active=c;last=c;
 }
 public static synchronized void clear(String reason){if(active!=null){active.reason=reason;active=null;}}
 public static synchronized JsonObject finish(){
  clear("SERVER_STOPPED");if(last==null)return null;
  if(!last.closed){last.closed=true;try{last.log.close();}catch(Exception e){last.errors.add(e.toString());}}
  var f=facts(last);try{Files.writeString(last.output.resolve("ai-result.json"),f+"\n",StandardOpenOption.CREATE_NEW);}catch(Exception e){last.errors.add(e.toString());}return f;
 }
 private static JsonObject facts(Context c){
  var x=new JsonObject();x.addProperty("lens","tank-ai-lens-v1");x.addProperty("requestHash",c.requestHash);x.addProperty("reason",c.reason);x.addProperty("at",Instant.now().toString());
  x.addProperty("scope","WHAT_THE_AI_IS_DOING_FROM_PUBLIC_VANILLA_STATE_AND_READ_ONLY_MOD_FIELDS_NOT_WHY_NOT_EVIDENCE");
  x.addProperty("selection","Mob_WITHIN_48XZ_32Y_OF_BOUND_PLAYER_NEAREST_32_EVERY_5_TICKS");x.addProperty("log","ai.jsonl CHANGE/GONE records only; pathTo is the value at the change");
  x.addProperty("sampledTicks",c.sampledTicks);x.addProperty("records",c.records);x.addProperty("droppedRecords",c.droppedRecords);x.addProperty("maxMobs",c.maxMobs);x.addProperty("overflowMobs",c.overflowMobs);
  x.addProperty("stateProbes",c.stateProbes);x.addProperty("renderedFrames",c.renders);x.addProperty("maxLinesPerFrame",c.maxLines);x.addProperty("maxLabelsPerFrame",c.maxLabels);x.addProperty("truncatedFrames",c.truncatedFrames);
  x.addProperty("renderCpuMeanNanos",c.renders==0?0:c.renderNanos/c.renders);x.addProperty("renderCpuMaxNanos",c.renderMaxNanos);x.addProperty("rawPixelsVerified",false);
  var t=new JsonArray();c.types.stream().limit(32).forEach(t::add);x.add("entityTypes",t);var g=new JsonArray();c.goals.stream().limit(64).forEach(g::add);x.add("goalsSeen",g);var ex=new JsonArray();c.explained.stream().limit(32).forEach(ex::add);x.add("explainedClasses",ex);x.addProperty("whyErrors",c.whyErrors);
  x.add("errors",new Gson().toJsonTree(c.errors));return x;
 }

 static String simple(Class<?> k){var n=k.getName();return n.substring(n.lastIndexOf('.')+1);}
 static boolean vanilla(Class<?> k){var n=k.getName();return n.startsWith("net.minecraft.")||n.startsWith("net.minecraftforge.");}
 /** Optional MOD-owned explanation: a public no-arg tankWhy() returning a Map or String, on the entity or a running goal. */
 private static final Map<Class<?>,Optional<Method>> WHY=new ConcurrentHashMap<>();
 static Optional<Method> whyMethod(Class<?> k){return WHY.computeIfAbsent(k,x->{try{var w=x.getMethod("tankWhy");try{w.setAccessible(true);}catch(Throwable ignored){}return Modifier.isStatic(w.getModifiers())?Optional.empty():Optional.of(w);}catch(Throwable e){return Optional.empty();}});}
 static void why(Context c,Object owner,String prefix,Map<String,String> out){
  var w=whyMethod(owner.getClass());if(w.isEmpty())return;
  try{Object v=w.get().invoke(owner);
   if(v instanceof Map<?,?> map){for(var e:map.entrySet()){if(out.size()>=MAX_WHY)break;out.put(prefix+e.getKey(),clip(String.valueOf(e.getValue())));}}
   else if(v!=null&&out.size()<MAX_WHY)out.put(prefix.isEmpty()?"why":prefix+"why",clip(String.valueOf(v)));
  }catch(Throwable e){c.whyErrors++;if(c.errors.size()<16)c.errors.add("tankWhy "+simple(owner.getClass())+": "+(e.getCause()!=null?e.getCause():e));}
 }
 static String clip(String s){return s.length()>60?s.substring(0,60):s;}
 static List<String> running(GoalSelector s){return s.getRunningGoals().sorted(Comparator.comparingInt(WrappedGoal::getPriority)).map(w->w.getPriority()+":"+simple(w.getGoal().getClass())).toList();}
 /** Read-only probes of state-like members declared by MOD classes between the concrete type and Mob; cached per class. */
 static List<Probe> probes(Class<?> type){return PROBES.computeIfAbsent(type,ManualAiLens::scan);}
 static List<Probe> scan(Class<?> type){
  var out=new ArrayList<Probe>();
  for(Class<?> k=type;k!=null&&k!=Mob.class&&out.size()<MAX_FIELDS;k=k.getSuperclass()){
   if(vanilla(k))continue;
   for(var f:k.getDeclaredFields()){
    if(out.size()>=MAX_FIELDS)break;if(f.isSynthetic())continue;int m=f.getModifiers();var t=f.getType();
    try{
     if(Modifier.isStatic(m)){if(t==EntityDataAccessor.class){f.setAccessible(true);if(f.get(null) instanceof EntityDataAccessor<?> a)out.add(new Probe(f.getName(),null,a));}}
     else if(t.isEnum()||t==int.class&&STATE_NAME.matcher(f.getName()).find()||t==boolean.class&&FLAG_NAME.matcher(f.getName()).find()){f.setAccessible(true);out.add(new Probe(f.getName(),f,null));}
    }catch(Throwable ignored){} // inaccessible member: simply not shown
   }
  }
  return List.copyOf(out);
 }
 static Map<String,String> state(Mob m){
  var out=new LinkedHashMap<String,String>();
  for(var p:probes(m.getClass())){
   try{Object v=p.accessor()!=null?m.getEntityData().get(p.accessor()):p.field().get(m);
    if(v instanceof Integer||v instanceof Boolean||v instanceof Byte||v instanceof Short||v instanceof String||v instanceof Enum<?>){var s=String.valueOf(v);out.put(p.name(),s.length()>40?s.substring(0,40):s);}}
   catch(Throwable ignored){} // accessor of another entity class, or unreadable: skipped
  }
  return out;
 }

 @SubscribeEvent public void sample(TickEvent.ServerTickEvent event){long t0=System.nanoTime();try{sample0(event);}finally{ManualScenario.overhead(System.nanoTime()-t0);}}
 private void sample0(TickEvent.ServerTickEvent event){
  var c=active;if(c==null||event.phase!=TickEvent.Phase.END)return;
  try{
   if(System.nanoTime()>=c.deadline||!c.live.getAsBoolean()){clear("WINDOW_ENDED");return;}
   var p=c.server.getPlayerList().getPlayer(c.player);if(p==null)return;var level=p.serverLevel();long tick=level.getGameTime();if(tick%EVERY!=0)return;
   var near=level.getEntitiesOfClass(Mob.class,p.getBoundingBox().inflate(RANGE_XZ,RANGE_Y,RANGE_XZ),Entity::isAlive);
   near.sort(Comparator.comparingDouble((Mob e)->e.distanceToSqr(p)).thenComparing(e->e.getUUID().toString()));
   if(near.size()>MAX_MOBS){c.overflowMobs+=near.size()-MAX_MOBS;near=near.subList(0,MAX_MOBS);}c.maxMobs=Math.max(c.maxMobs,near.size());
   var views=new ArrayList<View>(near.size());var seen=new HashSet<UUID>();
   for(var m:near){
    var id=m.getUUID();seen.add(id);var type=EntityType.getKey(m.getType()).toString();c.types.add(type);
    var goals=running(m.goalSelector);var targets=running(m.targetSelector);goals.forEach(c.goals::add);targets.forEach(c.goals::add);
    var brain=m.getBrain();var activities=brain.getActiveActivities().stream().map(Activity::getName).sorted().toList();
    var behaviors=brain.getRunningBehaviors().stream().map(b->b.debugString()).sorted().limit(6).toList();
    var fields=state(m);c.stateProbes=Math.max(c.stateProbes,fields.size());
    var whys=new LinkedHashMap<String,String>();why(c,m,"",whys);for(var s:List.of(m.goalSelector,m.targetSelector))s.getRunningGoals().forEach(g->why(c,g.getGoal(),simple(g.getGoal().getClass())+".",whys));
    if(!whys.isEmpty())c.explained.add(simple(m.getClass()));var tracked=new LinkedHashMap<String,String>(fields);whys.forEach((k,v)->tracked.put("?"+k,v));LivingEntity target=m.getTarget();
    var key=goals+"|"+targets+"|"+activities+"|"+behaviors+"|"+stable(c,m,id,tracked)+"|"+(target==null?"":target.getUUID());
    var nav=m.getNavigation();var path=nav.getPath();double[] points=null;
    if(path!=null&&!path.isDone()){int from=path.getNextNodeIndex(),to=Math.min(path.getNodeCount(),from+MAX_PATH);points=new double[Math.max(0,to-from)*3];
     for(int i=from;i<to;i++){var n=path.getNode(i);points[(i-from)*3]=n.x+0.5;points[(i-from)*3+1]=n.y+0.1;points[(i-from)*3+2]=n.z+0.5;}}
    c.lastType.put(id,type);if(!key.equals(c.lastKey.put(id,key))){
     var r=new JsonObject();r.addProperty("tick",tick);r.addProperty("event","CHANGE");r.addProperty("uuid",id.toString());r.addProperty("type",type);
     var pos=new JsonArray();pos.add(Math.round(m.getX()*10)/10.0);pos.add(Math.round(m.getY()*10)/10.0);pos.add(Math.round(m.getZ()*10)/10.0);r.add("pos",pos);
     r.add("goals",new Gson().toJsonTree(goals));r.add("targetGoals",new Gson().toJsonTree(targets));
     if(!activities.isEmpty())r.add("activities",new Gson().toJsonTree(activities));if(!behaviors.isEmpty())r.add("behaviors",new Gson().toJsonTree(behaviors));
     if(!fields.isEmpty())r.add("state",new Gson().toJsonTree(fields));if(!whys.isEmpty())r.add("why",new Gson().toJsonTree(whys));
     if(target!=null){var t=new JsonObject();t.addProperty("uuid",target.getUUID().toString());t.addProperty("type",EntityType.getKey(target.getType()).toString());r.add("target",t);}
     var goal=nav.getTargetPos();if(points!=null&&goal!=null){var to=new JsonArray();to.add(goal.getX());to.add(goal.getY());to.add(goal.getZ());r.add("pathTo",to);}
     record(c,r);
    }
    var labels=new ArrayList<String>();
    for(var s:goals){if(labels.size()<2)labels.add("> "+s);}for(var s:behaviors){if(labels.size()<2)labels.add("> "+s);}
    for(var s:targets){if(labels.size()<3)labels.add("@ "+s);}if(labels.isEmpty()&&!activities.isEmpty())labels.add("~ "+String.join(",",activities));
    int whyLines=0;for(var e:whys.entrySet()){if(whyLines<2&&labels.size()<MAX_LABEL_LINES){labels.add("? "+e.getKey()+"="+e.getValue());whyLines++;}}
    for(var e:fields.entrySet()){if(labels.size()<MAX_LABEL_LINES)labels.add(e.getKey()+"="+e.getValue());}
    views.add(new View(id,List.copyOf(labels),target==null?null:target.getUUID(),points));
   }
   for(var it=c.lastKey.keySet().iterator();it.hasNext();){var id=it.next();if(seen.contains(id))continue;it.remove();c.lastFields.remove(id);
    var r=new JsonObject();r.addProperty("tick",tick);r.addProperty("event","GONE");r.addProperty("uuid",id.toString());r.addProperty("type",c.lastType.remove(id));r.addProperty("why",level.getEntity(id)==null?"REMOVED":"OUT_OF_SELECTION");record(c,r);}
   c.snapshot=List.copyOf(views);c.sampledTicks++;if(c.sampledTicks%20==0)synchronized(ManualAiLens.class){if(!c.closed)c.log.flush();}
  }catch(Exception e){synchronized(ManualAiLens.class){c.errors.add(e.toString());}clear("SAMPLE_FAILED");}
 }
 /** Fields that change on most samples (timers, counters) still show in labels but do not trigger CHANGE records. */
 private static Map<String,String> stable(Context c,Mob m,UUID id,Map<String,String> fields){
  var before=c.lastFields.put(id,fields);var out=new TreeMap<String,String>();
  for(var e:fields.entrySet()){var k=m.getClass().getName()+"#"+e.getKey();var n=c.churn.computeIfAbsent(k,x->new long[2]);
   if(before!=null&&before.containsKey(e.getKey())){n[0]++;if(!e.getValue().equals(before.get(e.getKey())))n[1]++;}
   if(n[0]<20||n[1]*2<n[0])out.put(e.getKey(),e.getValue());}
  return out;
 }
 private static void record(Context c,JsonObject r)throws Exception{
  synchronized(ManualAiLens.class){if(c.closed)return;if(c.records>=MAX_RECORDS){c.droppedRecords++;return;}c.log.write(r.toString());c.log.newLine();c.records++;}
 }

 @SubscribeEvent public void render(RenderLevelStageEvent event){if(event.getStage()==RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS)draw(event);}
 private static void draw(RenderLevelStageEvent event){
  var c=active;if(c==null)return;var mc=Minecraft.getInstance();
  if(mc.level==null||mc.getSingleplayerServer()!=c.server||!mc.level.dimension().equals(Level.OVERWORLD))return;
  var views=c.snapshot;if(views.isEmpty())return;long started=System.nanoTime();var pose=event.getPoseStack();boolean pushed=false;
  try{
   var wanted=new HashSet<UUID>();for(var v:views){wanted.add(v.id());if(v.target()!=null)wanted.add(v.target());}
   var client=new HashMap<UUID,Entity>();for(var e:mc.level.entitiesForRendering()){if(wanted.contains(e.getUUID()))client.put(e.getUUID(),e);}
   float partial=event.getPartialTick();var camera=event.getCamera().getPosition();pose.pushPose();pushed=true;pose.translate(-camera.x,-camera.y,-camera.z);
   var buffers=mc.renderBuffers().bufferSource();var out=buffers.getBuffer(RenderType.lines());int lines=0;boolean truncated=false;int[] red={255,70,70,230},green={90,255,120,200};
   outer:for(var v:views){
    var self=client.get(v.id());if(self==null)continue;var at=self.getPosition(partial);double eye=at.y+self.getBbHeight()*0.5;
    var t=v.target()==null?null:client.get(v.target());
    if(t!=null){if(lines+1>MAX_LINES){truncated=true;break;}var to=t.getPosition(partial);line(out,pose.last(),at.x,eye,at.z,to.x,to.y+t.getBbHeight()*0.5,to.z,red);lines++;}
    var p=v.path();if(p==null)continue;
    for(int i=0;i+3<p.length;i+=3){if(lines+1>MAX_LINES){truncated=true;break outer;}line(out,pose.last(),p[i],p[i+1],p[i+2],p[i+3],p[i+4],p[i+5],green);lines++;}
   }
   buffers.endBatch(RenderType.lines());pose.popPose();pushed=false;
   var font=mc.font;var rotation=event.getCamera().rotation();int labels=0;
   var near=views.stream().filter(v->!v.labels().isEmpty()&&client.containsKey(v.id())).sorted(Comparator.comparingDouble(v->client.get(v.id()).getPosition(partial).distanceToSqr(camera))).toList();
   // Group: mobs within GROUP blocks of an already chosen label with identical lines share it ("x N"), so crowds stay readable.
   record Group(net.minecraft.world.phys.Vec3 at,float height,List<String> lines,int[] count){}
   var groups=new ArrayList<Group>();
   for(var v:near){
    var self=client.get(v.id());var at=self.getPosition(partial);if(at.distanceToSqr(camera)>LABEL_RANGE*LABEL_RANGE)break;if(at.distanceToSqr(camera)<LABEL_MIN*LABEL_MIN)continue; // pressed against the camera: a label would cover the screen
    Group same=null;for(var g:groups)if(g.lines().equals(v.labels())&&g.at().distanceToSqr(at)<GROUP*GROUP){same=g;break;}
    if(same!=null){same.count()[0]++;continue;}if(groups.size()>=MAX_LABELS)continue;groups.add(new Group(at,self.getBbHeight(),v.labels(),new int[]{1}));
   }
   for(var g:groups){
    labels++;var at=g.at();var text=new ArrayList<>(g.lines());if(g.count()[0]>1)text.set(0,text.get(0)+"  x"+g.count()[0]);
    pose.pushPose();pose.translate(at.x-camera.x,at.y+g.height()+0.35+0.25*text.size()-camera.y,at.z-camera.z);pose.mulPose(rotation);pose.scale(-0.025f,-0.025f,0.025f);
    for(int i=0;i<text.size();i++){var t=text.get(i);int color=t.startsWith("> ")?0xFFFFFFFF:t.startsWith("@ ")?0xFFFF8A65:t.startsWith("~ ")?0xFFB0BEC5:t.startsWith("? ")?0xFFCE93D8:0xFFFFD54F;
     font.drawInBatch(t,-font.width(t)/2f,i*10,color,false,pose.last().pose(),buffers,Font.DisplayMode.NORMAL,0x60000000,0xF000F0);}
    pose.popPose();
   }
   buffers.endBatch();
   long cost=Math.max(0,System.nanoTime()-started);
   synchronized(ManualAiLens.class){c.renders++;c.renderNanos+=cost;c.renderMaxNanos=Math.max(c.renderMaxNanos,cost);c.maxLines=Math.max(c.maxLines,lines);c.maxLabels=Math.max(c.maxLabels,labels);if(truncated)c.truncatedFrames++;
    if(!c.firstReceipt&&lines+labels>0){c.firstReceipt=true;Files.writeString(c.output.resolve("ai-rendered.json"),facts(c)+"\n",StandardOpenOption.CREATE_NEW);}}
  }catch(Exception e){synchronized(ManualAiLens.class){c.errors.add(e.toString());}clear("RENDER_FAILED");}finally{if(pushed)pose.popPose();}
 }
 private static void line(VertexConsumer out,PoseStack.Pose pose,double x,double y,double z,double a,double b,double c,int[] s){
  var n=new Vector3f((float)(a-x),(float)(b-y),(float)(c-z));if(n.lengthSquared()==0)n.set(0,1,0);n.normalize();
  out.vertex(pose.pose(),(float)x,(float)y,(float)z).color(s[0],s[1],s[2],s[3]).normal(pose.normal(),n.x,n.y,n.z).endVertex();
  out.vertex(pose.pose(),(float)a,(float)b,(float)c).color(s[0],s[1],s[2],s[3]).normal(pose.normal(),n.x,n.y,n.z).endVertex();
 }
}
