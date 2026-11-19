package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
/** Node fixtures exercise the same receipt bytes. No runtime/backend is instantiated. */
public final class KneekuraDebugActionJournalInterop {
 public static void main(String[] args)throws Exception {
  Path run=Path.of(args[0]).toRealPath(),directory=run.resolve("control/actions/"+KneekuraDebugActionJournal.sha256(args[1]));
  JsonObject action=KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(Files.readString(directory.resolve("canonical-action.json"))));
  var accepted=new KneekuraDebugActionJournal(run).accept(action);
  if(!accepted.status().equals("ACCEPTED"))throw new AssertionError("Node requested receipt not accepted");
  accepted.handle().append("APPLIED",List.of("a".repeat(64)));accepted.handle().append("VERIFIED",List.of("b".repeat(64)));accepted.handle().close();
  System.out.println("Node/Java shared receipt chain verified for "+args[1]);
 }
}
