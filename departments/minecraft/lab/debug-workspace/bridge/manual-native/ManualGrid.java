package kneekura.manual;

import com.google.gson.*;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.Level;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import org.joml.Vector3f;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Opt-in client lines only. No camera, lightmap override, entity effects or world mutation. */
public final class ManualGrid {
 private static final class Context {
  final MinecraftServer server;final JsonObject presentation;final String requestHash;final Path output;final long deadline;final BooleanSupplier live;
  final List<String> errors=new ArrayList<>();int renders,lines;String reason="ACTIVE";boolean firstReceipt;
  Context(MinecraftServer server,JsonObject presentation,String requestHash,Path output,long deadline,BooleanSupplier live){this.server=server;this.presentation=presentation.deepCopy();this.requestHash=requestHash;this.output=output;this.deadline=deadline;this.live=live;}
 }
 private static Context active,last;
 private static void write(Context c,String name,JsonObject data)throws Exception{Files.writeString(c.output.resolve(name),data+"\n",StandardOpenOption.CREATE_NEW);}
 public static synchronized void arm(MinecraftServer server,JsonObject request,String requestHash,Path output,long began,BooleanSupplier live)throws Exception{
  if(request.get("v").getAsInt()!=2)return;
  if(active!=null||last!=null)throw new IllegalStateException("MANUAL_GRID_ALREADY_ARMED");
  var p=request.getAsJsonObject("presentation");ManualPresentation.verifyWorld(p,Path.of(request.get("worldDir").getAsString()));
  var c=new Context(server,p,requestHash,output,began+request.get("maxWallMs").getAsLong()*1_000_000L,live);write(c,"grid-armed.json",facts(c));active=c;last=c;
 }
 private static JsonObject facts(Context c){var x=new JsonObject();x.addProperty("renderer","tank-grid-v1");x.addProperty("requestHash",c.requestHash);x.add("presentation",c.presentation.deepCopy());x.addProperty("active",active==c);x.addProperty("renderedPasses",c.renders);x.addProperty("linesPerPass",c.lines);x.addProperty("reason",c.reason);x.addProperty("at",Instant.now().toString());x.addProperty("scope","CLIENT_GRID_ONLY_NO_CAMERA_BRIGHTNESS_INPUT_CAPTURE_OR_SERVER_MUTATION");x.add("errors",new Gson().toJsonTree(c.errors));return x;}
 public static synchronized void clear(String reason){if(active!=null){active.reason=reason;active=null;}}
 public static synchronized JsonObject finish(){clear("SERVER_STOPPED");if(last==null)return null;try{write(last,"presentation-result.json",facts(last));}catch(Exception e){last.errors.add(e.toString());}return facts(last);}
 @SubscribeEvent public void render(RenderLevelStageEvent event){if(event.getStage()==RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS)draw(event);}
 private static synchronized void draw(RenderLevelStageEvent event){
  var c=active;if(c==null)return;var mc=Minecraft.getInstance();
  if(System.nanoTime()>=c.deadline||!c.live.getAsBoolean()){clear("WINDOW_ENDED");return;}
  if(mc.level==null||mc.getSingleplayerServer()!=c.server||!mc.level.dimension().equals(Level.OVERWORLD)){clear("WORLD_OR_SERVER_CHANGED");return;}
  var pose=event.getPoseStack();boolean pushed=false;
  try{
   var min=c.presentation.getAsJsonArray("min");var max=c.presentation.getAsJsonArray("max");int x0=min.get(0).getAsInt(),y0=min.get(1).getAsInt(),z0=min.get(2).getAsInt(),x1=max.get(0).getAsInt(),y1=max.get(1).getAsInt(),z1=max.get(2).getAsInt();
   var camera=event.getCamera().getPosition();pose.pushPose();pushed=true;pose.translate(-camera.x,-camera.y,-camera.z);var buffers=mc.renderBuffers().bufferSource();var lines=buffers.getBuffer(RenderType.lines());int count=0;
   for(int x=x0;x<=x1;x++){double px=inset(x,x0,x1);for(double y:new double[]{y0+.01,y1-.01}){line(lines,pose.last(),px,y,z0+.01,px,y,z1-.01);count++;}for(double z:new double[]{z0+.01,z1-.01}){line(lines,pose.last(),px,y0+.01,z,px,y1-.01,z);count++;}}
   for(int z=z0;z<=z1;z++){double pz=inset(z,z0,z1);for(double y:new double[]{y0+.01,y1-.01}){line(lines,pose.last(),x0+.01,y,pz,x1-.01,y,pz);count++;}for(double x:new double[]{x0+.01,x1-.01}){line(lines,pose.last(),x,y0+.01,pz,x,y1-.01,pz);count++;}}
   for(int y=y0;y<=y1;y++){double py=inset(y,y0,y1);for(double z:new double[]{z0+.01,z1-.01}){line(lines,pose.last(),x0+.01,py,z,x1-.01,py,z);count++;}for(double x:new double[]{x0+.01,x1-.01}){line(lines,pose.last(),x,py,z0+.01,x,py,z1-.01);count++;}}
   buffers.endBatch(RenderType.lines());c.renders++;c.lines=count;
   if(!c.firstReceipt){write(c,"grid-rendered.json",facts(c));c.firstReceipt=true;}
  }catch(Exception e){c.errors.add(e.toString());clear("RENDER_FAILED");}finally{if(pushed)pose.popPose();}
 }
 private static double inset(double n,double min,double max){return Math.max(min+.01,Math.min(max-.01,n));}
 private static void line(VertexConsumer out,com.mojang.blaze3d.vertex.PoseStack.Pose pose,double x,double y,double z,double a,double b,double c){var normal=new Vector3f((float)(a-x),(float)(b-y),(float)(c-z)).normalize();out.vertex(pose.pose(),(float)x,(float)y,(float)z).color(100,200,230,210).normal(pose.normal(),normal.x,normal.y,normal.z).endVertex();out.vertex(pose.pose(),(float)a,(float)b,(float)c).color(100,200,230,210).normal(pose.normal(),normal.x,normal.y,normal.z).endVertex();}
}
