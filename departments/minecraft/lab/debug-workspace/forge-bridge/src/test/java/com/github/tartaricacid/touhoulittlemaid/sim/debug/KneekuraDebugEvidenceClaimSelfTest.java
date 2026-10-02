package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.lang.reflect.*;
import java.nio.file.*;
import java.io.*;
import java.util.concurrent.*;
/** Deterministic claim/shutdown check of the actual writer, using genuine Gson/logging dependencies. */
public final class KneekuraDebugEvidenceClaimSelfTest {
 static void set(String n,Object v)throws Exception{Field f=KneekuraDebugEvidenceWriter.class.getDeclaredField(n);f.setAccessible(true);f.set(null,v);}
 @SuppressWarnings("unchecked")
 public static void main(String[] args)throws Exception {
  Path file=Files.createTempFile("lab-writer-claim",".jsonl");BufferedWriter writer=Files.newBufferedWriter(file);
  set("out",writer);set("file",file);set("identityKey","old");set("writerBusy",false);set("accepting",true);set("sealed",false);set("broken",false);
  Field q=KneekuraDebugEvidenceWriter.class.getDeclaredField("QUEUE");q.setAccessible(true);BlockingQueue<Object> queue=(BlockingQueue<Object>)q.get(null);queue.clear();
  Class<?> row=Class.forName(KneekuraDebugEvidenceWriter.class.getName()+"$QueuedRow");Constructor<?> ctor=row.getDeclaredConstructor(String.class,CompletableFuture.class,KneekuraDebugImageArtifact.class);ctor.setAccessible(true);CompletableFuture<String> proof=new CompletableFuture<>();queue.add(ctor.newInstance("{}",proof,null));
  Method claim=KneekuraDebugEvidenceWriter.class.getDeclaredMethod("claimQueuedRow");claim.setAccessible(true);Object claimed=claim.invoke(null);
  Field busy=KneekuraDebugEvidenceWriter.class.getDeclaredField("writerBusy");busy.setAccessible(true);
  if(claimed==null||!queue.isEmpty()||!busy.getBoolean(null))throw new AssertionError("dequeue must atomically establish in-flight ownership");
  var result=KneekuraDebugEvidenceWriter.sealAndFlush(0);
  if(result.clean())throw new AssertionError("in-flight claimed row cannot produce clean shutdown");
  try{KneekuraDebugDurability.write(file,writer,"{}",proof);throw new AssertionError("closed stream must not acknowledge");}catch(IOException expected){}
  if(!proof.isCompletedExceptionally())throw new AssertionError("shutdown-interrupted claim must not prove evidence");
  set("writerBusy",false);System.out.println("Actual writer claim self-test: 3 checks passed");
 }
}
