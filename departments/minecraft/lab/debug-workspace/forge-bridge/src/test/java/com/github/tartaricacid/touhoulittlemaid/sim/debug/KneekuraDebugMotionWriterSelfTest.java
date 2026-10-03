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
  var flush=KneekuraDebugEvidenceWriter.sealAndFlush(5000);if(!flush.clean())throw new AssertionError("unclean flush");
  Path file;try(var files=Files.list(config.evidenceRawDir())){file=files.findFirst().orElseThrow();}
  var row=JsonParser.parseString(Files.readString(file).trim()).getAsJsonObject();
  if(row.get("arenaEpoch").getAsInt()!=7||!row.getAsJsonObject("source").get("side").getAsString().equals("SERVER"))throw new AssertionError("lost actual Arena/source");
  var view=KneekuraDebugMotionOverlayRuntime.snapshot();
  if(args[0].equals("ON")) {
   if(view.samples().size()!=1||!view.samples().get(0).sourceId().equals(row.get("observationId").getAsString()))throw new AssertionError("display did not use exact flushed source ID");
  }else if(!view.samples().isEmpty())throw new AssertionError("default OFF collected a hidden trace");
  System.out.println("Real flushed source / actual Arena / native Motion overlay "+args[0]+" passed");
 }
}
