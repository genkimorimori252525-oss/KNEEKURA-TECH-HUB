package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.io.IOException;
import java.util.*;
/** Sealed camera intent parser. No Minecraft APIs and no permission inferred from a file. */
final class KneekuraDebugMobPovCommands {
 static final String MODE="mob-eye-live-v1",PERMISSION="MOB_POV_CAMERA";
 record Command(int index,String operation,UUID subject,long durationMs){}
 private KneekuraDebugMobPovCommands(){}
 static boolean enabled(KneekuraDebugOwnerInputs input)throws IOException{
  JsonObject rig=KneekuraDebugOwnerInputs.o(input.request(),"visual_rig");
  if(!MODE.equals(KneekuraDebugOwnerInputs.t(rig,"mode")))return false;
  KneekuraDebugActionJournal.keys(rig,"mode","fov","viewport");
  JsonElement fov=rig.get("fov");
  if(fov==null||!fov.isJsonPrimitive()||!fov.getAsJsonPrimitive().isNumber()||!Double.isFinite(fov.getAsDouble())||fov.getAsDouble()<30||fov.getAsDouble()>100)throw new IOException("MOB_POV_FOV");
  for(JsonElement dimension:KneekuraDebugOwnerInputs.a(rig,"viewport",2,2)){
   JsonObject value=new JsonObject();value.add("n",dimension);long n=KneekuraDebugOwnerInputs.n(value,"n");if(n<64||n>2048)throw new IOException("MOB_POV_VIEWPORT");
  }
  boolean permission=false;for(JsonElement p:input.world().getAsJsonArray("permissions"))permission|=PERMISSION.equals(p.getAsString());
  if(!permission)throw new IOException("MOB_POV_PERMISSION_MISSING");
  for(JsonElement a:input.request().getAsJsonArray("assertions"))if(!"structured".equals(KneekuraDebugOwnerInputs.t(a.getAsJsonObject(),"kind")))throw new IOException("MOB_POV_NO_AUTOMATIC_VISUAL_ASSERTIONS");
  return true;
 }
 static Command parse(KneekuraDebugOwnerInputs input,JsonObject marker,int next,KneekuraDebugArenaController.Snapshot state)throws IOException{
  if(!enabled(input))throw new IOException("MOB_POV_NOT_CONFIGURED");
  String operation=KneekuraDebugOwnerInputs.t(marker,"operation");
  List<String> keys=new ArrayList<>(List.of("schemaVersion","commandIndex","operation","ownerEnvelopeHash","runSnapshotId","runSnapshotHash","requestHash","handshakeNonce","leaseId","expectedArenaEpoch","expectedArenaRevision"));
  if(operation.equals("attach"))keys.addAll(List.of("subjectUuid","durationMs"));
  else if(!Set.of("snapshot","return").contains(operation))throw new IOException("MOB_POV_OPERATION");
  KneekuraDebugActionJournal.keys(marker,keys.toArray(String[]::new));
  long index=KneekuraDebugOwnerInputs.n(marker,"commandIndex");var grant=input.grant();var id=grant.identity();
  if(next<0||next>=32||index!=next||KneekuraDebugOwnerInputs.n(marker,"schemaVersion")!=1||!KneekuraDebugOwnerInputs.t(marker,"ownerEnvelopeHash").equals(input.envelopeHash())||
    !KneekuraDebugOwnerInputs.t(marker,"runSnapshotId").equals(id.runSnapshotId())||!KneekuraDebugOwnerInputs.t(marker,"runSnapshotHash").equals(input.snapshotHash())||
    !KneekuraDebugOwnerInputs.t(marker,"requestHash").equals(grant.requestHash())||!KneekuraDebugOwnerInputs.t(marker,"handshakeNonce").equals(id.handshakeNonce())||
    !KneekuraDebugOwnerInputs.t(marker,"leaseId").equals(grant.leaseId())||!state.identity().equals(id)||!state.arenaId().equals(grant.arena().arenaId())||
    KneekuraDebugOwnerInputs.n(marker,"expectedArenaEpoch")!=state.arenaEpoch()||KneekuraDebugOwnerInputs.n(marker,"expectedArenaRevision")!=state.arenaRevision())throw new IOException("MOB_POV_IDENTITY_OR_ORDER");
  UUID subject=null;long duration=0;
  if(operation.equals("attach")){
   String uuid=KneekuraDebugOwnerInputs.t(marker,"subjectUuid");
   if(!uuid.matches("[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}")||grant.subjects().values().stream().noneMatch(s->s.uuid().equals(uuid)))throw new IOException("MOB_POV_SUBJECT_NOT_REGISTERED");
   subject=UUID.fromString(uuid);duration=KneekuraDebugOwnerInputs.n(marker,"durationMs");if(duration<1||duration>120000)throw new IOException("MOB_POV_DURATION_BOUND");
  }
  if(operation.equals("snapshot")&&grant.maxCaptures()==0)throw new IOException("MOB_POV_VIEW_ONLY");
  return new Command((int)index,operation,subject,duration);
 }
}
