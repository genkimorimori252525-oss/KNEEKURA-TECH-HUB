package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.nio.file.*;
public final class KneekuraDebugOwnerGrantInterop {
 public static void main(String[] args)throws Exception {
  var grant=KneekuraDebugArenaOwnerGrant.parse(KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(Files.readString(Path.of(args[0])))));
  if(!grant.requestHash().equals("a".repeat(64))||grant.generation()!=1||grant.maxCaptures()!=4)throw new AssertionError("Node grant linkage drift");
  System.out.println("Node/Java owner grant parsed; capability/linkage is not authority proof");
 }
}
