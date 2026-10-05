package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;

/** Actual filesystem publication primitive; no game or authority fixture. */
public final class KneekuraDebugTankRotationFilesSelfTest {
 static int checks;
 static void check(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
 interface Checked{void run()throws Exception;}
 static void rejects(Checked call,String label)throws Exception{try{call.run();throw new AssertionError("did not reject "+label);}catch(IOException|IllegalArgumentException expected){checks++;}}
 public static void main(String[] args)throws Exception{
  Path root=Files.createTempDirectory("kneekura-tank-publish-").toRealPath();JsonObject original=new JsonObject();original.addProperty("status","GEOMETRY_VERIFIED");
  KneekuraDebugOwnerFiles.writeNew(root,"kneekura-tank-owner.json",original);Path file=root.resolve("kneekura-tank-owner.json");String previous=KneekuraDebugOwnerFiles.sha256(Files.readAllBytes(file));
  JsonObject unknown=new JsonObject();unknown.addProperty("status","OUTCOME_UNKNOWN");String published=KneekuraDebugOwnerFiles.replaceExpected(root,"kneekura-tank-owner.json",previous,unknown);
  check(KneekuraDebugOwnerFiles.json(root,"kneekura-tank-owner.json",published,65536).equals(unknown),"atomic source-owner replacement publishes exact new bytes");
  check(!published.equals(previous),"new hash includes actual newline-terminated file bytes");
  rejects(()->KneekuraDebugOwnerFiles.replaceExpected(root,"kneekura-tank-owner.json",previous,original),"changed predecessor cannot be replaced");
  check(KneekuraDebugOwnerFiles.sha256(Files.readAllBytes(file)).equals(published),"stale update leaves slot unchanged");
  rejects(()->KneekuraDebugOwnerFiles.replaceExpected(root,"../outside.json",published,original),"escaped root");
  rejects(()->KneekuraDebugOwnerFiles.replaceExpected(root,"kneekura-tank-owner.json","bad",original),"malformed source hash");
  JsonObject oversized=new JsonObject();oversized.addProperty("data","x".repeat(65536));rejects(()->KneekuraDebugOwnerFiles.replaceExpected(root,"kneekura-tank-owner.json",published,oversized),"bounded publication");
  check(KneekuraDebugOwnerFiles.sha256(Files.readAllBytes(file)).equals(published),"failed publication cannot alter owner slot");
  JsonObject next=new JsonObject();next.addProperty("status","GEOMETRY_VERIFIED");next.addProperty("arenaEpoch",9);
  String nextHash=KneekuraDebugOwnerFiles.replaceExpected(root,"kneekura-tank-owner.json",published,next);
  check(KneekuraDebugOwnerFiles.json(root,"kneekura-tank-owner.json",nextHash,65536).equals(next),"second transition uses exact intervening owner hash");
  try(var entries=Files.list(root)){check(entries.count()==1,"successful atomic publish leaves no temporary files");}
  System.out.println("Actual Tank owner atomic file publication passed: "+checks+"; artifacts retained at "+root+"; no game process launched");
 }
}
