package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.RenderType;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.joml.Vector3f;
import java.util.Objects;

/** Explicit default-OFF rendering from already flushed canonical samples, never gameplay visualization objects. */
@Mod.EventBusSubscriber(modid=TouhouLittleMaid.MOD_ID,value=Dist.CLIENT)
public final class KneekuraDebugMotionOverlay {
 private static KneekuraDebugMotionTraceCache.Context lastContext;
 private static long frames,totalNanos,maxNanos;
 private KneekuraDebugMotionOverlay(){}
 @SubscribeEvent
 public static void render(RenderLevelStageEvent event) {
  if(!KneekuraDebugMotionOverlayRuntime.armed()||event.getStage()!=RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS)return;
  var mc=Minecraft.getInstance();if(mc.level==null)return;
  long started=System.nanoTime();var trace=KneekuraDebugMotionOverlayRuntime.snapshot();var config=KneekuraDebugMotionOverlayRuntime.config();
  if(trace.context()==null||config==null||trace.samples().isEmpty())return;
  if(!Objects.equals(lastContext,trace.context())){lastContext=trace.context();frames=0;totalNanos=0;maxNanos=0;}
  var camera=event.getCamera().getPosition();String dimension=mc.level.dimension().location().toString();long gameTime=mc.level.getGameTime();
  PoseStack pose=event.getPoseStack();pose.pushPose();
  try {
   var related=KneekuraDebugMotionOverlayRuntime.relatedSnapshot();
   boolean captureQuiescent=KneekuraDebugCardinalCapture.quiescent();
   var lines=KneekuraDebugMotionOverlayGeometry.combinedLines(trace,related,dimension,gameTime,camera.x,camera.y,camera.z,captureQuiescent);
   var labels=KneekuraDebugMotionOverlayGeometry.relatedLabels(trace,related,dimension,gameTime,camera.x,camera.y,camera.z,captureQuiescent);if(lines.isEmpty()&&labels.isEmpty())return;
   pose.translate(-camera.x,-camera.y,-camera.z);var buffers=mc.renderBuffers().bufferSource();var consumer=buffers.getBuffer(RenderType.lines());
   for(var line:lines)line(consumer,pose,line);
   buffers.endBatch(RenderType.lines());
   for(var label:labels) {
    pose.pushPose();
    try {
     pose.translate(label.x(),label.y()+0.22,label.z());pose.mulPose(event.getCamera().rotation());pose.scale(-0.015f,-0.015f,0.015f);
     var style=label.style();int argb=(style.alpha()<<24)|(style.r()<<16)|(style.g()<<8)|style.b();
     mc.font.drawInBatch(label.text(),-mc.font.width(label.text())/2.0f,0,argb,false,pose.last().pose(),buffers,Font.DisplayMode.NORMAL,0,0xF000F0);
    }finally{pose.popPose();}
   }
   if(!labels.isEmpty())buffers.endBatch();
   long cost=Math.max(0,System.nanoTime()-started);frames++;totalNanos+=cost;maxNanos=Math.max(maxNanos,cost);
   if(frames%100==0){
    var payload=new JsonObject();payload.addProperty("schema","kneekura.live-motion-overlay-status/v1");
    payload.addProperty("semantics","DERIVED_PRESENTATION_FROM_FLUSHED_SERVER_SAMPLES_NOT_CONTINUOUS_MOTION_OR_GAMEPLAY_OBJECTS");
    payload.addProperty("targetRevision",trace.context().revision());payload.addProperty("dimension",dimension);
    payload.addProperty("renderedFrames",frames);payload.addProperty("submittedLines",lines.size());payload.addProperty("retainedSamples",trace.samples().size());
    payload.addProperty("submittedProjectileLabels",labels.size());payload.addProperty("projectileLabelScope","RELATED_UUID_AT_LAST_RETAINED_POSITION_NOT_LIVE_POSITION");
    payload.addProperty("evictedSamples",trace.evictedSamples());payload.addProperty("rejectedSamples",trace.rejectedSamples());payload.addProperty("gapCount",trace.gaps().size());
    if(Objects.equals(trace.context(),related.context())){
     payload.addProperty("relatedProjectileGroups",related.traces().size());payload.addProperty("relatedProjectileSamples",related.retainedSamples());
     payload.addProperty("relatedProjectileEvictedSamples",related.evictedSamples());payload.addProperty("relatedProjectileRejectedSamples",related.rejectedSamples());
     payload.addProperty("relatedProjectileGroupScope","RETAINED_ACCEPTED_GROUPS_NOT_CURRENTLY_VISIBLE_COUNT");
     var ids=new JsonArray();var spawns=new JsonArray();for(var group:related.traces()){ids.add(group.uuid().toString());spawns.add(group.spawnSource());}
     payload.add("relatedProjectileUuids",ids);payload.add("relatedProjectileSpawnSources",spawns);
    }
    payload.addProperty("firstRetainedTick",trace.samples().get(0).tick());payload.addProperty("lastRetainedTick",trace.samples().get(trace.samples().size()-1).tick());
    payload.addProperty("renderCpuMeanNanos",totalNanos/frames);payload.addProperty("renderCpuMaxNanos",maxNanos);
    payload.addProperty("observerCostScope","CPU_BUILD_AND_DRAW_SUBMIT_EXCLUDES_GPU_FRAMEBUFFER_CAPTURE_WRITER");
    payload.addProperty("rawPixelsVerified",false);payload.addProperty("maxAgeTicks",100);payload.addProperty("maxCameraDistanceBlocks",64);
    var refs=new JsonArray();java.util.stream.Stream.concat(lines.stream().flatMap(l->l.sourceIds().stream()),labels.stream().flatMap(l->l.sourceIds().stream())).distinct().forEach(refs::add);payload.add("source_observation_ids",refs);
    KneekuraDebugEvidenceWriter.recordMotionOverlayObserved(config,trace.context().arena(),gameTime,trace.context().uuid(),payload);
   }
  }catch(Exception error){KneekuraDebugMotionOverlayRuntime.disable();TouhouLittleMaid.LOGGER.error("[KNEEKURA-DEBUG] native Motion overlay disabled after render failure",error);}
  finally{pose.popPose();}
 }
 private static void line(VertexConsumer consumer,PoseStack pose,KneekuraDebugMotionOverlayGeometry.Line line) {
  var normal=new Vector3f((float)(line.x1()-line.x0()),(float)(line.y1()-line.y0()),(float)(line.z1()-line.z0())).normalize();
  var style=line.style();
  consumer.vertex(pose.last().pose(),(float)line.x0(),(float)line.y0(),(float)line.z0()).color(style.r(),style.g(),style.b(),style.alpha()).normal(pose.last().normal(),normal.x,normal.y,normal.z).endVertex();
  consumer.vertex(pose.last().pose(),(float)line.x1(),(float)line.y1(),(float)line.z1()).color(style.r(),style.g(),style.b(),style.alpha()).normal(pose.last().normal(),normal.x,normal.y,normal.z).endVertex();
 }
}
