package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.*;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.*;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.function.BooleanSupplier;

/** Inert without the real installed owner. Live viewing allocates no images or frame history. */
@Mod.EventBusSubscriber(modid="touhou_little_maid",value=Dist.CLIENT)
public final class KneekuraDebugMobPovCamera {
 private record Installation(KneekuraDebugEnv.Config config,BooleanSupplier live,double fov,int width,int height){}
 private static Installation installation;
 private static volatile Active active;
 private static long clientTick,renderFrame;
 private static int writes;
 private static volatile String lastRestoration="NOT_RUN";
 private KneekuraDebugMobPovCamera(){}
 static void install(KneekuraDebugEnv.Config config,BooleanSupplier live,JsonObject rig){
  thread();if(installation!=null||config==null||!config.enabled())throw new IllegalStateException("MOB_POV_INSTALL_CONFLICT");
  installation=new Installation(config,live,rig.get("fov").getAsDouble(),rig.getAsJsonArray("viewport").get(0).getAsInt(),rig.getAsJsonArray("viewport").get(1).getAsInt());
 }
 static void uninstall(){thread();installation=null;if(active!=null)active.finish("OWNER_UNINSTALLED");}
 static boolean quiescent(){thread();return active==null&&writes==0;}
 static UUID subject(){Active a=active;return a==null?null:a.target.getUUID();}
 static String restoration(){return lastRestoration;}
 static boolean rawSnapshotPending(){thread();Active a=active;return a!=null&&a.pending!=null;}
 static CompletableFuture<JsonObject> attach(UUID uuid,String type,String dimension,long deadline,JsonObject identity){
  thread();Installation owner=installation;Minecraft mc=Minecraft.getInstance();
  if(owner==null||!owner.live().getAsBoolean()||active!=null||mc.level==null||mc.player==null||!mc.player.isSpectator()||mc.isPaused()||mc.screen!=null||mc.getOverlay()!=null||mc.getCameraEntity()==null||!mc.level.dimension().location().toString().equals(dimension))throw new IllegalStateException("MOB_POV_CLIENT_NOT_AVAILABLE");
  Entity found=null;for(Entity e:mc.level.entitiesForRendering())if(e.getUUID().equals(uuid)){found=e;break;}
  if(!(found instanceof Mob mob)||!mob.isAlive()||mob.isRemoved()||!BuiltInRegistries.ENTITY_TYPE.getKey(mob.getType()).toString().equals(type))throw new IllegalStateException("MOB_POV_EXACT_MOB_NOT_LOADED");
  long now=System.nanoTime();Active next=new Active(owner,mob,mc,now,deadline,identity);
  if(!KneekuraDebugCameraOwnership.claim(next))throw new IllegalStateException("CAMERA_ALREADY_OWNED");
  active=next;
  try{mc.options.setCameraType(CameraType.FIRST_PERSON);mc.setCameraEntity(mob);}
  catch(Throwable failure){next.finish("ATTACH_FAILED");throw failure;}
  JsonObject result=new JsonObject();result.addProperty("status","ATTACHED");result.addProperty("subjectUuid",uuid.toString());result.addProperty("frameRecording",false);
  return CompletableFuture.completedFuture(result);
 }
 static CompletableFuture<JsonObject> snapshot(String captureId,JsonObject serverReference){
  thread();Active a=active;if(a==null)throw new IllegalStateException("MOB_POV_NOT_ATTACHED");a.progress();
  if(active!=a||a.pending!=null||a.imageWriting)throw new IllegalStateException("MOB_POV_NOT_READY_OR_CAPTURE_BUSY");
  long now=System.nanoTime();if(now-serverReference.get("validatedAtNanos").getAsLong()<0||now-serverReference.get("validatedAtNanos").getAsLong()>500_000_000L)throw new IllegalStateException("MOB_POV_AUTHORIZATION_STALE");
  a.pending=new Pending(captureId,serverReference.deepCopy(),now);return a.pending.result;
 }
 static CompletableFuture<JsonObject> returnView(){thread();Active a=active;JsonObject result=new JsonObject();
  if(a!=null)a.finish("EXPLICIT_RETURN");result.addProperty("status","RETURNED");result.addProperty("restoration",a==null?lastRestoration:a.restoration);
  return CompletableFuture.completedFuture(result);
 }
 @SubscribeEvent public static void tick(TickEvent.ClientTickEvent event){if(event.phase!=TickEvent.Phase.END)return;clientTick++;Active a=active;if(a!=null)a.progress();}
 @SubscribeEvent public static void render(TickEvent.RenderTickEvent event){if(event.phase!=TickEvent.Phase.START)return;renderFrame++;Active a=active;if(a!=null)a.progress();}
 @SubscribeEvent public static void fov(ViewportEvent.ComputeFov event){Active a=active;if(a!=null&&event.getCamera().getEntity()==a.target)event.setFOV(a.owner.fov());}
 @SubscribeEvent public static void frame(RenderLevelStageEvent event){Active a=active;if(a==null||a.pending==null)return;
  if(event.getStage()==RenderLevelStageEvent.Stage.AFTER_ENTITIES){a.viewMatrix=new float[16];event.getPoseStack().last().pose().get(a.viewMatrix);a.viewFrame=renderFrame;}
  if(event.getStage()==RenderLevelStageEvent.Stage.AFTER_LEVEL)a.capture(event);
 }
 private static final class Pending {
  final String id;final JsonObject serverReference;final long started;final CompletableFuture<JsonObject> result=new CompletableFuture<>();
  Pending(String id,JsonObject reference,long started){this.id=id;serverReference=reference;this.started=started;}
 }
 private static final class Active {
  final Installation owner;final Mob target;final ClientLevel level;final Entity oldCamera;final CameraType oldType;
  final KneekuraDebugMobPovSession session;final JsonObject identity;
  Pending pending;boolean imageWriting;float[] viewMatrix;long viewFrame=-1;String restoration="NOT_RUN";
  Active(Installation owner,Mob target,Minecraft mc,long now,long deadline,JsonObject identity){
   this.owner=owner;this.target=target;level=mc.level;oldCamera=mc.getCameraEntity();oldType=mc.options.getCameraType();
   session=new KneekuraDebugMobPovSession(target.getUUID(),now,deadline);this.identity=identity.deepCopy();
  }
  void progress(){
   if(active!=this)return;Minecraft mc=Minecraft.getInstance();long now=System.nanoTime();
   String reason=session.poll(now,installation==owner&&owner.live().getAsBoolean(),mc.level==level&&mc.player!=null&&mc.player.isSpectator(),
    !target.isRemoved()&&level.getEntity(target.getId())==target,target.isAlive(),KneekuraDebugCameraOwnership.owns(this)&&mc.getCameraEntity()==target&&mc.options.getCameraType()==CameraType.FIRST_PERSON);
   if(reason==null&&(mc.screen!=null||mc.getOverlay()!=null||mc.isPaused()))reason="PRESENTATION_INTERRUPTED";
   if(reason!=null){finish(reason);return;}
   if(pending!=null&&now-pending.started>=2_000_000_000L){Pending p=pending;pending=null;p.result.completeExceptionally(new IllegalStateException("MOB_POV_FRAME_DEADLINE"));}
  }
  void finish(String reason){
   if(active!=this)return;Minecraft mc=Minecraft.getInstance();boolean sameWorld=mc.level==level;
   boolean exact=false;
   try{
    if(KneekuraDebugCameraOwnership.owns(this)&&sameWorld&&mc.getCameraEntity()==target){
     Entity previous=!oldCamera.isRemoved()&&oldCamera.level()==level&&level.getEntity(oldCamera.getId())==oldCamera?oldCamera:mc.player;
     if(previous!=null&&previous.level()==level){
      boolean typeOwned=mc.options.getCameraType()==CameraType.FIRST_PERSON;mc.setCameraEntity(previous);
      if(typeOwned)mc.options.setCameraType(oldType);
      exact=previous==oldCamera&&typeOwned&&mc.getCameraEntity()==oldCamera&&mc.options.getCameraType()==oldType;
     }
    }
   }finally{
    restoration=exact?"RESTORED":"UNKNOWN";lastRestoration=restoration;KneekuraDebugCameraOwnership.release(this);active=null;
    if(pending!=null){pending.result.completeExceptionally(new IllegalStateException(reason));pending=null;}
    JsonObject row=common("mob_pov_return");row.addProperty("reason",reason);row.addProperty("restoration",restoration);row.addProperty("frameRecording",false);
    writes++;new KneekuraDebugCaptureEvidenceSink().manifest(owner.config(),identity.get("arenaEpoch").getAsLong(),clientTick,null,row)
     .whenComplete((hash,error)->Minecraft.getInstance().execute(()->{writes--;if(error!=null)lastRestoration="UNKNOWN_EVIDENCE_WRITE";}));
   }
  }
  JsonObject common(String kind){JsonObject row=new JsonObject();row.addProperty("schemaVersion",1);row.addProperty("kind",kind);row.addProperty("rig",KneekuraDebugMobPovCommands.MODE);
   row.add("identity",identity.deepCopy());row.addProperty("subjectUuid",target.getUUID().toString());row.addProperty("entityType",BuiltInRegistries.ENTITY_TYPE.getKey(target.getType()).toString());
   row.addProperty("dimension",level.dimension().location().toString());row.addProperty("clientTick",clientTick);row.addProperty("renderFrame",renderFrame);return row;
  }
  void capture(RenderLevelStageEvent event){
   progress();Pending p=pending;if(active!=this||p==null)return;pending=null;
   try{
    Minecraft mc=Minecraft.getInstance();if(event.getCamera().getEntity()!=target||viewFrame!=renderFrame||viewMatrix==null)throw new IllegalStateException("MOB_POV_RENDER_BINDING");
    if(mc.getMainRenderTarget().width!=owner.width()||mc.getMainRenderTarget().height!=owner.height())throw new IllegalStateException("MOB_POV_VIEWPORT_CHANGED");
    double fov=Math.toDegrees(2*Math.atan(1.0/event.getProjectionMatrix().m11()));
    if(!Double.isFinite(fov)||Math.abs(fov-owner.fov())>.001)throw new IllegalStateException("MOB_POV_FOV_CHANGED");
    byte[] png;try(NativeImage image=Screenshot.takeScreenshot(mc.getMainRenderTarget())){png=image.asByteArray();}
    if(png.length==0||png.length>4*1024*1024)throw new IllegalStateException("MOB_POV_PNG_BUDGET");
    JsonObject row=common("mob_pov_raw_frame");String hash=KneekuraDebugOwnerFiles.sha256(png);
    row.add("identity",p.serverReference.getAsJsonObject("identity").deepCopy());
    row.addProperty("captureId",p.id);row.addProperty("imageHash",hash);row.addProperty("imageBytes",png.length);row.addProperty("imagePath","evidence/raw/visual/"+hash+".png");
    row.addProperty("captureStage","AFTER_LEVEL_BEFORE_POST_EFFECT_HAND_HUD");row.addProperty("artifactRole","RAW_SCENE_RGB");row.addProperty("partialTick",event.getPartialTick());row.addProperty("clientGameTime",level.getGameTime());
    row.add("serverReference",p.serverReference.deepCopy());row.addProperty("timePairing","INDEPENDENT_ASYNC_SERVER_SAMPLE_NOT_SAME_TICK");row.addProperty("aiPerceptionVerdict","NOT_ESTABLISHED");
    row.addProperty("cameraEffect",mc.gameRenderer.currentEffect()==null?"NONE":"ACTIVE_NOT_INCLUDED_AT_THIS_STAGE");
    JsonObject camera=new JsonObject();Vec3 pos=event.getCamera().getPosition();camera.add("position",numbers(pos.x,pos.y,pos.z));
    var q=event.getCamera().rotation();camera.add("quaternion",numbers(q.x(),q.y(),q.z(),q.w()));camera.addProperty("yaw",event.getCamera().getYRot());camera.addProperty("pitch",event.getCamera().getXRot());camera.addProperty("fov",fov);
    float[] projection=new float[16];event.getProjectionMatrix().get(projection);camera.add("projectionMatrix",numbers(projection));camera.add("viewMatrix",numbers(viewMatrix));
    camera.add("viewport",numbers(owner.width(),owner.height()));camera.addProperty("matrixConvention","JOML_COLUMN_MAJOR_CAMERA_RELATIVE");row.add("camera",camera);
    imageWriting=true;writes++;
    new KneekuraDebugCaptureEvidenceSink().frame(owner.config(),row.getAsJsonObject("identity").get("arenaEpoch").getAsLong(),clientTick,null,png,row)
     .whenComplete((proof,error)->Minecraft.getInstance().execute(()->{imageWriting=false;writes--;
      if(error!=null)p.result.completeExceptionally(error);else{JsonObject result=row.deepCopy();result.addProperty("status","CAPTURED");result.addProperty("observationPayloadHash",proof);p.result.complete(result);}
     }));
   }catch(Throwable error){p.result.completeExceptionally(error);}
  }
 }
 private static JsonArray numbers(double...v){JsonArray a=new JsonArray();for(double n:v){if(!Double.isFinite(n))throw new IllegalStateException("MOB_POV_NON_FINITE_CAMERA");a.add(n);}return a;}
 private static JsonArray numbers(float[]v){JsonArray a=new JsonArray();for(float n:v){if(!Float.isFinite(n))throw new IllegalStateException("MOB_POV_NON_FINITE_MATRIX");a.add(n);}return a;}
 private static void thread(){if(!Minecraft.getInstance().isSameThread())throw new IllegalStateException("CLIENT_THREAD_REQUIRED");}
}
