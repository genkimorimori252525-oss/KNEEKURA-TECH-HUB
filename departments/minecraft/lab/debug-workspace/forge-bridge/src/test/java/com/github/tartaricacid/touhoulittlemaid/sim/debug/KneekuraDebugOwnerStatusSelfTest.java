package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import com.sun.nio.file.ExtendedOpenOption;

/** Finite status publication contracts; Windows cases use a genuine no-delete-sharing handle. */
public final class KneekuraDebugOwnerStatusSelfTest {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static JsonObject row(String status){JsonObject b=new JsonObject();b.addProperty("status",status);return b;}
 static final class Fake implements KneekuraDebugOwnerStatus.Backend {
  int prepared,published;boolean locked=true;String last;
  public KneekuraDebugOwnerStatus.Publication prepare(JsonObject b){prepared++;String snapshot=b.get("status").getAsString();return ()->{if(locked)return false;published++;last=snapshot;return true;};}
 }
 public static void main(String[] args)throws Exception{
  Fake f=new Fake();var s=new KneekuraDebugOwnerStatus(f);JsonObject mutable=row("ACTIVE");s.submit(mutable,false,0);mutable.addProperty("status","MUTATED");
  check(!s.dispatchAllowed()&&s.pending(),"pending blocks admission");s.tick(1);check(f.prepared==1&&f.published==0,"one snapshot, no queue");
  f.locked=false;s.tick(2);check(s.dispatchAllowed()&&f.last.equals("ACTIVE"),"immutable transient recovery");
  f=new Fake();s=new KneekuraDebugOwnerStatus(f);s.submit(row("ACTIVE"),false,0);s.submit(row("CLOSED"),true,100);f.locked=false;s.tick(101);
  check(s.terminalPublished()&&!s.dispatchAllowed()&&f.last.equals("CLOSED"),"terminal supersedes active");
  try{s.submit(row("ACTIVE"),false,102);throw new AssertionError("stale active");}catch(IOException expected){checks++;}
  f=new Fake();s=new KneekuraDebugOwnerStatus(f);s.submit(row("ACTIVE"),false,0);s.submit(row("EXPIRED"),true,499_000_000);
  try{s.tick(500_000_000);throw new AssertionError("extended deadline");}catch(IOException expected){check(s.failed()&&!s.terminalPublished(),"expiry keeps original deadline and blocks ACK");}
  f=new Fake();s=new KneekuraDebugOwnerStatus(f);s.submit(row("ACTIVE"),false,0);
  for(int i=1;i<8;i++)s.tick(i);
  try{s.tick(9);throw new AssertionError("unbounded retry");}catch(IOException expected){check(s.failed()&&!s.dispatchAllowed(),"attempt cap fail closed");}
  boundary();
  if(System.getProperty("os.name").startsWith("Windows"))windows();
  System.out.println("owner status publication checks="+checks);
 }
 static void boundary()throws Exception{
  Fake f=new Fake();var s=new KneekuraDebugOwnerStatus(f);s.submit(row("ACTIVE"),false,0);int[] maintained={0};
  s.tickActive(()->1,false,()->maintained[0]++);check(maintained[0]==1&&s.pending(),"camera maintenance continues under status lock");
  var r=KneekuraDebugArenaControllerSelfTest.rig();r.clock().set(950_000_000);
  var wait=KneekuraDebugArenaControllerSelfTest.command(r,"status-expiry","wait_ticks",KneekuraDebugArenaControllerSelfTest.waitArgs(20));
  check(r.controller().submit(wait,10).status().equals("ACCEPTED"),"genuine controller action pending");
  f=new Fake();s=new KneekuraDebugOwnerStatus(f);s.submit(row("ACTIVE"),false,r.clock().get());r.clock().set(1_001_000_000);
  check(r.controller().onTick(11).status().equals("OUTCOME_UNKNOWN")&&r.controller().snapshot().unsafe(),"actual controller catches pending-action lease expiry");
  f.locked=false;
  try{s.tickActive(r.clock()::get,r.controller().snapshot().unsafe(),()->maintained[0]++);throw new AssertionError("stale ACTIVE after caught expiry");}
  catch(IOException expected){check(f.published==0&&maintained[0]==1,"unsafe boundary rejects retry before admission or maintenance");}
  s.submit(row("OUTCOME_UNKNOWN"),true,r.clock().get());check(s.terminalPublished()&&f.last.equals("OUTCOME_UNKNOWN"),"expiry supersedes pending ACTIVE without retrying action");
 }
 static void windows()throws Exception{
  Path root=Files.createTempDirectory("owner-status-publication-").toRealPath();KneekuraDebugOwnerFiles.writeStatus(root,row("OLD"));Path target=root.resolve("control/owner-status.json");
  var s=new KneekuraDebugOwnerStatus(root);
  try(FileChannel held=FileChannel.open(target,StandardOpenOption.READ,ExtendedOpenOption.NOSHARE_DELETE)){
   s.submit(row("ACTIVE"),false,0);check(s.pending()&&Files.readString(target).contains("OLD"),"real rename denied preserves predecessor");s.tick(1);check(s.pending(),"real retry remains pending");
  }
  s.tick(2);check(s.dispatchAllowed()&&Files.readString(target).contains("ACTIVE"),"real released lock publishes");
  try(FileChannel held=FileChannel.open(target,StandardOpenOption.READ,ExtendedOpenOption.NOSHARE_DELETE)){
   s.submit(row("NEXT"),false,3);s.submit(row("OWNER_CLOSED"),true,4);check(!s.terminalPublished(),"real closure awaits publication");
  }
  s.tick(5);check(s.terminalPublished()&&Files.readString(target).contains("OWNER_CLOSED"),"real closure discards stale snapshot");
  s=new KneekuraDebugOwnerStatus(root);
  try(FileChannel held=FileChannel.open(target,StandardOpenOption.READ,ExtendedOpenOption.NOSHARE_DELETE)){
   s.submit(row("ACTIVE"),false,0);s.submit(row("EXPIRED"),true,1);
   try{s.tick(500_000_000);throw new AssertionError("permanent lock");}catch(IOException expected){check(s.failed()&&!s.terminalPublished()&&Files.readString(target).contains("OWNER_CLOSED"),"real permanent lock is unknown, never ACK");}
  }
 }
}
