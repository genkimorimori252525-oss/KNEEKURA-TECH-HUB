package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
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
  var lines=KneekuraDebugMotionOverlayGeometry.lines(trace,dimension,gameTime,camera.x,camera.y,camera.z,KneekuraDebugCardinalCapture.quiescent());if(lines.isEmpty())return;
  PoseStack pose=event.getPoseStack();pose.pushPose();
  try {
   pose.translate(-camera.x,-camera.y,-camera.z);var buffers=mc.renderBuffers().bufferSource();var consumer=buffers.getBuffer(RenderType.lines());
   for(var line:lines)line(consumer,pose,line);
   buffers.endBatch(RenderType.lines());
   long cost=Math.max(0,System.nanoTime()-started);frames++;totalNanos+=cost;maxNanos=Math.max(maxNanos,cost);
   if(frames%100==0){
    var payload=new JsonObject();payload.addProperty("schema","kneekura.live-motion-overlay-status/v1");
    payload.addProperty("semantics","DERIVED_PRESENTATION_FROM_FLUSHED_SERVER_SAMPLES_NOT_CONTINUOUS_MOTION_OR_GAMEPLAY_OBJECTS");
    payload.addProperty("targetRevision",trace.context().revision());payload.addProperty("dimension",dimension);
    payload.addProperty("renderedFrames",frames);payload.addProperty("submittedLines",lines.size());payload.addProperty("retainedSamples",trace.samples().size());
    payload.addProperty("evictedSamples",trace.evictedSamples());payload.addProperty("rejectedSamples",trace.rejectedSamples());payload.addProperty("gapCount",trace.gaps().size());
    payload.addProperty("firstRetainedTick",trace.samples().get(0).tick());payload.addProperty("lastRetainedTick",trace.samples().get(trace.samples().size()-1).tick());
    payload.addProperty("renderCpuMeanNanos",totalNanos/frames);payload.addProperty("renderCpuMaxNanos",maxNanos);
    payload.addProperty("observerCostScope","CPU_BUILD_AND_DRAW_SUBMIT_EXCLUDES_GPU_FRAMEBUFFER_CAPTURE_WRITER");
    payload.addProperty("rawPixelsVerified",false);payload.addProperty("maxAgeTicks",100);payload.addProperty("maxCameraDistanceBlocks",64);
    var refs=new JsonArray();lines.stream().flatMap(l->l.sourceIds().stream()).distinct().forEach(refs::add);payload.add("source_observation_ids",refs);
    KneekuraDebugEvidenceWriter.recordMotionOverlayObserved(config,trace.context().arena(),gameTime,trace.context().uuid(),payload);
   }
  }catch(Exception error){KneekuraDebugMotionOverlayRuntime.disable();TouhouLittleMaid.LOGGER.error("[KNEEKURA-DEBUG] native Motion overlay disabled after render failure",error);}
  finally{pose.popPose();}
 }
 private static void line(VertexConsumer consumer,PoseStack pose,KneekuraDebugMotionOverlayGeometry.Line line) {
  var normal=new Vector3f((float)(line.x1()-line.x0()),(float)(line.y1()-line.y0()),(float)(line.z1()-line.z0())).normalize();
  boolean projectile=line.traceClass().equals("PROJECTILE_ACTUAL");int r=projectile?255:105,g=projectile?199:215,b=projectile?80:255;
  consumer.vertex(pose.last().pose(),(float)line.x0(),(float)line.y0(),(float)line.z0()).color(r,g,b,255).normal(pose.last().normal(),normal.x,normal.y,normal.z).endVertex();
  consumer.vertex(pose.last().pose(),(float)line.x1(),(float)line.y1(),(float)line.z1()).color(r,g,b,255).normal(pose.last().normal(),normal.x,normal.y,normal.z).endVertex();
 }
}
