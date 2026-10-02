package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.io.*;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.util.concurrent.CompletableFuture;
/** Existing writer worker's durable row checkpoint, not another thread/store. */
final class KneekuraDebugDurability {
 private KneekuraDebugDurability(){}
 static void write(Path file,BufferedWriter writer,String row,CompletableFuture<String> proof)throws IOException {
  try {
   writer.write(row);writer.write('\n');writer.flush();
   if(proof!=null){try(FileChannel channel=FileChannel.open(file,StandardOpenOption.WRITE,LinkOption.NOFOLLOW_LINKS)){channel.force(true);}proof.complete(KneekuraDebugActionJournal.sha256(row));}
  }catch(IOException|RuntimeException e){if(proof!=null)proof.completeExceptionally(e);throw e;}
 }
}
