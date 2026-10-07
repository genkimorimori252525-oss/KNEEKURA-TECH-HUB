package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Path;
import java.util.function.LongSupplier;

/** One immutable pending status; only denied atomic renames retry, on later owner ticks. */
final class KneekuraDebugOwnerStatus {
 interface Publication {boolean publish()throws IOException;}
 interface Backend {Publication prepare(JsonObject snapshot)throws IOException;}
 interface Maintenance {void run()throws IOException;}
 private final Backend backend;
 private Publication pending;
 private long deadline;
 private int attempts;
 private boolean terminal,terminalPublished;
 private IOException failure;
 KneekuraDebugOwnerStatus(Path root){this(snapshot->KneekuraDebugOwnerFiles.prepareStatus(root,snapshot));}
 KneekuraDebugOwnerStatus(Backend backend){this.backend=backend;}
 boolean pending(){return pending!=null;}
 boolean failed(){return failure!=null;}
 boolean dispatchAllowed(){return !terminal&&!pending()&&!failed();}
 boolean terminalPublished(){return terminalPublished&&!failed();}
 void tickActive(LongSupplier clock,boolean unsafe,Maintenance maintenance)throws IOException{
  if(unsafe)throw new IOException("OWNER_ARENA_OUTCOME_UNKNOWN");
  maintenance.run();tick(clock.getAsLong());
 }
 void submit(JsonObject body,boolean closing,long now)throws IOException{
  if(failure!=null)throw failure;
  if(terminal&&!closing)throw new IOException("STATUS_TERMINAL_ALREADY_REQUESTED");
  if(pending!=null&&!closing)throw new IOException("STATUS_PUBLICATION_ALREADY_PENDING");
  if(terminal)return; // Repeated shutdown requests never extend or replace the terminal publication.
  try{
   Publication next=backend.prepare(body.deepCopy());
   if(pending==null){deadline=now+500_000_000L;attempts=0;}
   pending=next;terminal=closing;tick(now);
  }catch(IOException error){failure=error;throw error;}
 }
 void tick(long now)throws IOException{
  if(failure!=null)throw failure;if(pending==null)return;
  try{
   if(now>=deadline||attempts>=8)throw new IOException("STATUS_ATOMIC_PUBLICATION_DEADLINE");
   attempts++;
   if(pending.publish()){pending=null;terminalPublished=terminal;}
  }catch(IOException error){failure=error;throw error;}
 }
}
