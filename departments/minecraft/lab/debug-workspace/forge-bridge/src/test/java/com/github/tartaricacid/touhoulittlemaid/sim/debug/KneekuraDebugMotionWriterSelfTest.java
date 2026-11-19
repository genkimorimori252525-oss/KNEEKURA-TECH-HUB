package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.nio.file.*;
import java.util.UUID;
public final class KneekuraDebugMotionWriterSelfTest {
 public static void main(String[] args)throws Exception {
  var root=Files.createTempDirectory("motion-writer-test");var config=new KneekuraDebugEnv.Config(true,"s","r",1,"snap","n".repeat(32),
   root.resolve("ready.json"),root,root,root.resolve("evidence/raw"),root.resolve("target.json"),root.resolve("stop.json"),root.resolve("ack.json"),"KNEEKURA_DEBUG_WORLD");
  var uuid=UUID.fromString("00000000-0000-0000-0000-000000000001");
  KneekuraDebugMotionOverlayRuntime.select(config,7,1,uuid);
  var payload=KneekuraDebugMotionTraceCacheSelfTest.row(100,0,"obs:fixture").getAsJsonObject("payload").deepCopy();
  KneekuraDebugEvidenceWriter.recordServerSelectedObserved(config,7,100,100L,"SERVER_ENTITY_STATE","test",uuid,payload);
  for(int index=1;index<=3;index++) {
   var projectile=KneekuraDebugRelatedProjectileTraceSelfTest.row(1,index==1,100+index,index,index).getAsJsonObject("payload");
   KneekuraDebugEvidenceWriter.recordServerSelectedObserved(config,7,100+index,100L+index,"AI_DECISION","test",uuid,projectile);
  }
  var flush=KneekuraDebugEvidenceWriter.sealAndFlush(5000);if(!flush.clean())throw new AssertionError("unclean flush");
  Path file;try(var files=Files.list(config.evidenceRawDir())){file=files.findFirst().orElseThrow();}
  var rows=Files.readString(file).lines().filter(line->!line.isBlank()).map(line->JsonParser.parseString(line).getAsJsonObject()).toList();
  if(rows.size()!=4)throw new AssertionError("four actual writer rows required");var row=rows.get(0);
  if(row.get("arenaEpoch").getAsInt()!=7||!row.getAsJsonObject("source").get("side").getAsString().equals("SERVER"))throw new AssertionError("lost actual Arena/source");
  var view=KneekuraDebugMotionOverlayRuntime.snapshot();
  if(args[0].equals("ON")) {
   if(view.samples().size()!=1||!view.samples().get(0).sourceId().equals(row.get("observationId").getAsString()))throw new AssertionError("display did not use exact flushed source ID");
   var related=KneekuraDebugMotionOverlayRuntime.relatedSnapshot();
   if(related.traces().size()!=1||related.retainedSamples()!=2||related.context().arena()!=7)throw new AssertionError("related display lost actual flushed group/Arena");
   var points=related.traces().get(0).trace().samples();
   for(int i=0;i<2;i++)if(!points.get(i).sourceId().equals(rows.get(i+2).get("observationId").getAsString()))throw new AssertionError("related display lost exact flushed tick source ID");
   if(!related.traces().get(0).spawnSource().equals(rows.get(1).get("observationId").getAsString()))throw new AssertionError("accepted spawn source lost");
  }else if(!view.samples().isEmpty())throw new AssertionError("default OFF collected a hidden trace");
  if(args[0].equals("OFF")&&!KneekuraDebugMotionOverlayRuntime.relatedSnapshot().traces().isEmpty())throw new AssertionError("default OFF collected hidden projectile groups");
  System.out.println("Real flushed source / actual Arena / selected+related native Motion overlay "+args[0]+" passed");
 }
}
