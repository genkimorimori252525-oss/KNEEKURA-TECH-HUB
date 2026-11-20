package kneekura.manual;

import com.google.gson.*;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.commands.CommandSource;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.entity.Mob;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import java.io.File;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.BooleanSupplier;

/**
 * Opt-in declarative scenario (KNEEKURA_TANK_SCENARIO=<inputs/scenario.json>): vanilla commands run as the bound Player
 * (permission 4) at fixed server ticks inside the Tank's private world copy, command checks, client screenshots and marks.
 * Also measures every server tick (START at HIGHEST to END at LOWEST, so all MOD tick handlers are inside) and the Tank's
 * own sampling cost in that tick, so load can be reported with and without the Tank's tools. Step execution happens
 * after the measured END and is excluded. Judging (expect) is done by the host from the written facts.
 */
public final class ManualScenario {
 static final int MAX_TICKS=2400,MAX_MESSAGES=3;
 record Step(int index,int at,String kind,String value){}
 private static final AtomicLong OVERHEAD=new AtomicLong();
 /** Called by the Tank's own server-thread samplers (trails, AI lens) with the nanos they spent in this tick. */
 public static void overhead(long nanos){if(active!=null)OVERHEAD.addAndGet(nanos);}
 private static final class Context {
  final MinecraftServer server;final UUID player;final Path output;final File gameDir;final BooleanSupplier live;final List<Step> steps;
  final int[] tickMicros=new int[MAX_TICKS],toolMicros=new int[MAX_TICKS];final JsonArray results=new JsonArray();final List<String> errors=new ArrayList<>();
  int next,ticks;long started=-1,startGameTime=-1;String reason="ACTIVE";volatile String pendingShot;volatile JsonObject pendingShotRow;
  Context(MinecraftServer server,UUID player,Path output,File gameDir,BooleanSupplier live,List<Step> steps){this.server=server;this.player=player;this.output=output;this.gameDir=gameDir;this.live=live;this.steps=steps;}
 }
 private static volatile Context active;private static Context last;
 public static String requested(){return System.getenv("KNEEKURA_TANK_SCENARIO");}
 public static synchronized void arm(MinecraftServer server,UUID player,Path output,File gameDir,BooleanSupplier live)throws Exception{
  var file=requested();if(file==null)return;if(active!=null||last!=null)throw new IllegalStateException("MANUAL_SCENARIO_ALREADY_ARMED");
  var raw=JsonParser.parseString(Files.readString(Path.of(file))).getAsJsonArray();var steps=new ArrayList<Step>();
  for(int i=0;i<raw.size();i++){var o=raw.get(i).getAsJsonObject();int at=o.get("at").getAsInt();String kind=null;
   for(var k:List.of("run","try","check","screenshot","mark"))if(o.has(k)){kind=k;break;}
   if(kind==null)throw new IllegalArgumentException("MANUAL_SCENARIO_STEP_KIND "+i);steps.add(new Step(i,at,kind,o.get(kind).getAsString()));}
  var c=new Context(server,player,output,gameDir,live,List.copyOf(steps));active=c;last=c;
 }
 public static synchronized void clear(String reason){if(active!=null){active.reason=reason;active=null;}}
 public static synchronized JsonObject finish(){
  clear("SERVER_STOPPED");if(last==null)return null;var c=last;
  for(int i=c.next;i<c.steps.size();i++){var s=c.steps.get(i);var r=row(s);r.addProperty("status","NOT_REACHED");c.results.add(r);}c.next=c.steps.size();
  var pending=c.pendingShotRow;if(pending!=null&&!pending.has("status"))pending.addProperty("status","NOT_TAKEN");
  var x=new JsonObject();x.addProperty("scenario","tank-scenario-v1");x.addProperty("reason",c.reason);x.addProperty("at",Instant.now().toString());
  x.addProperty("scope","COMMANDS_RUN_IN_PRIVATE_TRIAL_WORLD_AS_BOUND_PLAYER_PERMISSION_4; TICK_TIME_IS_ONE_RUN_ON_THIS_MACHINE_INTEGRATED_SERVER");
  x.addProperty("startGameTime",c.startGameTime);x.addProperty("ticks",c.ticks);
  var t=new JsonArray();var o=new JsonArray();for(int i=0;i<Math.min(c.ticks,MAX_TICKS);i++){t.add(c.tickMicros[i]);o.add(c.toolMicros[i]);}
  x.add("tickMicros",t);x.add("tankToolMicros",o);x.add("steps",c.results);x.add("errors",new Gson().toJsonTree(c.errors));
  try{Files.writeString(c.output.resolve("scenario-result.json"),x+"\n",StandardOpenOption.CREATE_NEW);}catch(Exception e){c.errors.add(e.toString());}
  var summary=new JsonObject();summary.addProperty("reason",c.reason);summary.addProperty("ticks",c.ticks);summary.addProperty("steps",c.steps.size());return summary;
 }
 private static JsonObject row(Step s){var r=new JsonObject();r.addProperty("index",s.index());r.addProperty("at",s.at());r.addProperty(s.kind(),s.value());return r;}

 @SubscribeEvent(priority=EventPriority.HIGHEST) public void begin(TickEvent.ServerTickEvent event){
  var c=active;if(c==null||event.phase!=TickEvent.Phase.START)return;c.started=System.nanoTime();OVERHEAD.set(0);
 }
 @SubscribeEvent(priority=EventPriority.LOWEST) public void end(TickEvent.ServerTickEvent event){
  var c=active;if(c==null||event.phase!=TickEvent.Phase.END||c.started<0)return;
  long spent=System.nanoTime()-c.started,tools=OVERHEAD.get();c.started=-1;
  try{
   if(!c.live.getAsBoolean()){clear("WINDOW_ENDED");return;}
   var p=c.server.getPlayerList().getPlayer(c.player);if(p==null)return;
   int tick=c.ticks;if(tick>=MAX_TICKS){clear("TICK_CAPACITY");return;}
   if(tick==0)c.startGameTime=p.serverLevel().getGameTime();
   c.tickMicros[tick]=(int)Math.min(Integer.MAX_VALUE,spent/1000);c.toolMicros[tick]=(int)Math.min(Integer.MAX_VALUE,tools/1000);c.ticks++;
   while(c.next<c.steps.size()&&c.steps.get(c.next).at()<=tick){var s=c.steps.get(c.next++);var r=row(s);r.addProperty("tick",tick);
    switch(s.kind()){
     case "run","try","check"->command(c,p,s,r);
     case "mark"->{var level=p.serverLevel();int all=0;for(var e:level.getAllEntities())all++;r.addProperty("loadedEntities",all);
      r.addProperty("mobsNear",level.getEntitiesOfClass(Mob.class,p.getBoundingBox().inflate(48,32,48)).size());r.addProperty("status","MARKED");}
     case "screenshot"->{if(c.pendingShot!=null){r.addProperty("status","SKIPPED_PREVIOUS_PENDING");}else{c.pendingShotRow=r;c.pendingShot=s.value();}}
     default->r.addProperty("status","UNKNOWN_KIND");
    }
    synchronized(ManualScenario.class){c.results.add(r);}
   }
  }catch(Exception e){synchronized(ManualScenario.class){c.errors.add(e.toString());}clear("SCENARIO_FAILED");}
 }
 private static void command(Context c,net.minecraft.server.level.ServerPlayer p,Step s,JsonObject r){
  var messages=new JsonArray();int[] calls={0,0,0};// callbacks, successes, summed result
  CommandSource capture=new CommandSource(){
   public void sendSystemMessage(Component m){if(messages.size()<MAX_MESSAGES){var t=m.getString();messages.add(t.length()>200?t.substring(0,200):t);}}
   public boolean acceptsSuccess(){return true;}public boolean acceptsFailure(){return true;}public boolean shouldInformAdmins(){return false;}};
  var source=p.createCommandSourceStack().withPermission(4).withSource(capture).withCallback((ctx,success,result)->{calls[0]++;if(success){calls[1]++;calls[2]+=result;}});
  var text=s.value().startsWith("/")?s.value().substring(1):s.value();
  int returned=c.server.getCommands().performPrefixedCommand(source,text);
  boolean ok=s.kind().equals("check")?calls[1]>0&&calls[2]>0:calls[1]>0;
  r.addProperty("status",ok?"PASS":"FAIL");r.addProperty("returned",returned);r.addProperty("callbacks",calls[0]);r.addProperty("successes",calls[1]);r.addProperty("result",calls[2]);r.add("messages",messages);
 }

 @SubscribeEvent public void shoot(TickEvent.ClientTickEvent event){
  var c=active;if(c==null||event.phase!=TickEvent.Phase.END||c.pendingShot==null)return;
  var mc=Minecraft.getInstance();if(mc.level==null||mc.getSingleplayerServer()!=c.server)return;
  var name="scenario-"+c.pendingShot+".png";var row=c.pendingShotRow;c.pendingShot=null;
  try{Screenshot.grab(c.gameDir,name,mc.getMainRenderTarget(),msg->{synchronized(ManualScenario.class){row.addProperty("status","TAKEN");row.addProperty("file",c.gameDir.toPath().resolve("screenshots").resolve(name).toAbsolutePath().normalize().toString());}});}
  catch(Exception e){synchronized(ManualScenario.class){row.addProperty("status","FAILED");c.errors.add(e.toString());}}
 }
}
