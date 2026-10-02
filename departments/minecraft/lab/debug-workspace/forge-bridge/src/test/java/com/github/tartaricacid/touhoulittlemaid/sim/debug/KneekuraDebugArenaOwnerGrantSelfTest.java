package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.util.*;
public final class KneekuraDebugArenaOwnerGrantSelfTest {
 public static void main(String[] ignored)throws Exception {
  JsonObject g=new JsonObject();g.addProperty("schemaVersion",1);
  for(String k:List.of("grantId","debugSessionId","runId","runSnapshotId","experimentId","arenaId","leaseId"))g.addProperty(k,k);
  g.addProperty("handshakeNonce","nonce-0000000000000001");g.addProperty("processEpoch",1);g.addProperty("arenaEpoch",1);g.addProperty("expectedArenaRevision",0);
  g.addProperty("baselineHash","a".repeat(64));g.addProperty("dimensionId","minecraft:overworld");g.addProperty("disposableWorldName","KNEEKURA_DEBUG_WORLD");
  g.addProperty("requestHash","b".repeat(64));g.addProperty("generation",1);g.addProperty("maxCaptures",4);g.addProperty("timeBudgetMs",1000);g.addProperty("maxActions",4);JsonArray types=new JsonArray();types.add("wait_ticks");g.add("allowedActions",types);
  JsonObject b=new JsonObject();JsonArray lo=new JsonArray(),hi=new JsonArray();for(int i=0;i<3;i++){lo.add(0);hi.add(8);}b.add("min",lo);b.add("max",hi);g.add("bounds",b);
  JsonArray s=new JsonArray();JsonObject subject=new JsonObject();subject.addProperty("subjectId","subject");subject.addProperty("uuid","00000000-0000-0000-0000-000000000001");subject.addProperty("entityType","minecraft:armor_stand");s.add(subject);g.add("subjects",s);
  var grant=KneekuraDebugArenaOwnerGrant.parse(g);
  KneekuraDebugActionJournalSelfTest.check(grant.timeBudgetMs()==1000&&grant.subjects().size()==1,"bounded owner grant");
  for(String key:List.of("handshakeNonce","processEpoch","baselineHash","dimensionId","timeBudgetMs","maxActions","bounds")) {
   JsonObject bad=g.deepCopy();bad.remove(key);KneekuraDebugActionJournalSelfTest.rejects(()->KneekuraDebugArenaOwnerGrant.parse(bad),"missing "+key);
  }
  JsonObject bad=g.deepCopy();bad.addProperty("liveAuthorization",true);final JsonObject authority=bad;KneekuraDebugActionJournalSelfTest.rejects(()->KneekuraDebugArenaOwnerGrant.parse(authority),"self-attested authority field");
  bad=g.deepCopy();bad.addProperty("timeBudgetMs",120001);final JsonObject ttl=bad;KneekuraDebugActionJournalSelfTest.rejects(()->KneekuraDebugArenaOwnerGrant.parse(ttl),"oversized lease");
  bad=g.deepCopy();bad.getAsJsonArray("allowedActions").add("use_item");final JsonObject item=bad;KneekuraDebugActionJournalSelfTest.rejects(()->KneekuraDebugArenaOwnerGrant.parse(item),"unimplemented use_item grant");
  bad=g.deepCopy();bad.getAsJsonArray("subjects").add(subject);final JsonObject dup=bad;KneekuraDebugActionJournalSelfTest.rejects(()->KneekuraDebugArenaOwnerGrant.parse(dup),"duplicate subject UUID");
  JsonObject captureOnly=g.deepCopy();captureOnly.addProperty("maxActions",0);captureOnly.add("allowedActions",new JsonArray());
  KneekuraDebugActionJournalSelfTest.check(KneekuraDebugArenaOwnerGrant.parse(captureOnly).maxActions()==0,"capture-only no mutation lease");
  captureOnly.addProperty("maxActions",4);
  KneekuraDebugActionJournalSelfTest.check(KneekuraDebugArenaOwnerGrant.parse(captureOnly).allowedActions().isEmpty(),"capture-only positive unused action budget has no capability");
  System.out.println("Owner grant self-test: "+KneekuraDebugActionJournalSelfTest.checks+" checks passed");
 }
}
