package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.nio.file.*;
import java.util.Arrays;
public final class KneekuraDebugImageArtifactSelfTest {
 public static void main(String[] args)throws Exception {
  Path root=Files.createTempDirectory("image-artifact-test");byte[] bytes=new byte[]{(byte)137,80,78,71,13,10,26,10,0};
  var artifact=new KneekuraDebugImageArtifact(root,bytes);bytes[8]=99;
  artifact.persist();byte[] kept=Files.readAllBytes(root.resolve("evidence/raw/visual/"+artifact.hash()+".png"));
  if(kept[8]!=0)throw new AssertionError("caller altered queued bytes");
  artifact.persist();
  Files.write(root.resolve("evidence/raw/visual/"+artifact.hash()+".png"),new byte[]{1});
  try{artifact.persist();throw new AssertionError("rewrote corrupt immutable image");}catch(java.io.IOException expected){}
  Path other=Files.createTempDirectory("image-artifact-link");Path outside=Files.createTempDirectory("image-artifact-outside");
  Files.createSymbolicLink(other.resolve("evidence"),outside);
  try{new KneekuraDebugImageArtifact(other,kept).persist();throw new AssertionError("followed symlink");}catch(java.io.IOException expected){}
  try{new KneekuraDebugImageArtifact(root,new byte[4*1024*1024+1]);throw new AssertionError("oversized image");}catch(IllegalArgumentException expected){}
  if(!System.getProperty("os.name").toLowerCase().contains("win")) {
   Path race=Files.createTempDirectory("image-artifact-race");var raced=new KneekuraDebugImageArtifact(race,kept);raced.persist();
   Path file=race.resolve("evidence/raw/visual/"+raced.hash()+".png");
   java.util.concurrent.atomic.AtomicReference<Throwable> failure=new java.util.concurrent.atomic.AtomicReference<>();
   Thread reader=new Thread(()->{
    try {raced.persist(()->{
      try {Files.delete(file);if(new ProcessBuilder("mkfifo",file.toString()).start().waitFor()!=0)throw new AssertionError("mkfifo failed");}
      catch(Exception error){throw new RuntimeException(error);}
     });failure.set(new AssertionError("accepted replaced FIFO"));}
    catch(java.io.IOException expected){}catch(Throwable error){failure.set(error);}
   });reader.setDaemon(true);reader.start();reader.join(1000);
   if(reader.isAlive())throw new AssertionError("existing image read blocked on replacement FIFO");
   if(failure.get()!=null)throw new AssertionError(failure.get());
  }
  System.out.println("image artifact checks=6");
 }
}
