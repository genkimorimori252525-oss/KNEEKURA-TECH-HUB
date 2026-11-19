package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.*;
import java.util.ArrayList;
import java.util.List;

/** Strict sealed intent only; it never supplies the source owner callback or a new lease. */
final class KneekuraDebugTankRotationPlan {
    static final String PERMISSION = "PRE_EXPERIMENT_TANK_ROTATION";
    static String installationReceiptHash(JsonObject receipt, String envelopeHash, KneekuraDebugArenaOwnerGrant grant) throws IOException {
        String hash=KneekuraDebugActionJournal.hash(t(receipt,"receiptHash"));JsonObject body=receipt.deepCopy();body.remove("receiptHash");
        require(hash(body).equals(hash) && n(body,"schemaVersion")==1 && t(body,"kind").equals("owner_installation_receipt")
                && t(body,"status").equals("INSTALLED_SCOPED_CONTROL") && t(body,"scope").equals(KneekuraDebugOwnerInputs.CONTROL),"TANK_ROTATION_INSTALLATION_RECEIPT_INVALID");
        var id=grant.identity();require(t(body,"ownerEnvelopeHash").equals(KneekuraDebugActionJournal.hash(envelopeHash))
                && t(body,"debugSessionId").equals(id.debugSessionId()) && t(body,"runId").equals(id.runId())
                && t(body,"runSnapshotId").equals(id.runSnapshotId()) && n(body,"processEpoch")==id.processEpoch()
                && t(body,"requestHash").equals(grant.requestHash()) && t(body,"leaseId").equals(grant.leaseId())
                && t(body,"arenaId").equals(grant.arena().arenaId()) && n(body,"arenaEpoch")==grant.arena().arenaEpoch()
                && n(body,"arenaRevision")==grant.arena().arenaRevision(),"TANK_ROTATION_INSTALLATION_IDENTITY_MISMATCH");return hash;
    }
    record Validated(JsonObject intent, JsonObject predecessor, KneekuraDebugTankRotationController.Geometry next,
                     List<KneekuraDebugTankRotationController.Geometry> priorRegions) {
        Validated { intent = intent.deepCopy(); predecessor = predecessor.deepCopy(); priorRegions = List.copyOf(priorRegions); }
        @Override public JsonObject intent() { return intent.deepCopy(); }
        @Override public JsonObject predecessor() { return predecessor.deepCopy(); }
        long previousEpoch() { return intent.get("previousTankEpoch").getAsLong(); }
        String previousOwnerHash() { return intent.get("previousOwnerFileSha256").getAsString(); }
        String nextRecipeHash() { return intent.get("nextRecipeHash").getAsString(); }
        String rotationId() { return intent.get("rotationId").getAsString(); }
        JsonObject nextRecipe() { return intent.getAsJsonObject("nextRecipe").deepCopy(); }
        KneekuraDebugTankRotationController.Plan controllerPlan(KneekuraDebugArenaController.Lease lease) throws IOException {
            require(lease.leaseId().equals(t(intent,"leaseId")) && lease.maxActions() == 0 && lease.allowedActions().isEmpty(),"TANK_ROTATION_LEASE_MISMATCH");
            var id=lease.identity();require(t(intent,"debugSessionId").equals(id.debugSessionId()) && t(intent,"runId").equals(id.runId())
                    && t(intent,"runSnapshotId").equals(id.runSnapshotId()) && n(intent,"processEpoch")==id.processEpoch()
                    && t(intent,"handshakeNonce").equals(id.handshakeNonce()),"TANK_ROTATION_LEASE_IDENTITY_MISMATCH");
            return new KneekuraDebugTankRotationController.Plan(next,priorRegions,previousEpoch(),lease.issuedNanos(),lease.deadlineNanos());
        }
    }
    static Validated parse(JsonObject plan, KneekuraDebugArenaOwnerGrant grant, JsonObject request,
                           JsonObject world, JsonObject trigger, byte[] previousOwnerBytes) throws IOException {
        KneekuraDebugActionJournal.keys(plan,"schemaVersion","scope","rotationId","debugSessionId","runId","runSnapshotId","processEpoch","handshakeNonce",
                "requestHash","grantId","leaseId","arenaId","expectedArenaEpoch","expectedArenaRevision","previousOwnerFileSha256","previousRecipeHash","previousTankEpoch","nextRecipeHash","nextRecipe");
        require(n(plan,"schemaVersion")==1 && t(plan,"scope").equals(PERMISSION),"TANK_ROTATION_SCOPE");KneekuraDebugArenaController.id(t(plan,"rotationId"));
        var id=grant.identity();require(t(plan,"debugSessionId").equals(id.debugSessionId()) && t(plan,"runId").equals(id.runId())
                && t(plan,"runSnapshotId").equals(id.runSnapshotId()) && n(plan,"processEpoch")==id.processEpoch() && t(plan,"handshakeNonce").equals(id.handshakeNonce()),"TANK_ROTATION_IDENTITY_MISMATCH");
        require(t(plan,"grantId").equals(grant.grantId()) && t(plan,"leaseId").equals(grant.leaseId()) && t(plan,"arenaId").equals(grant.arena().arenaId())
                && t(plan,"requestHash").equals(grant.requestHash()) && n(plan,"expectedArenaEpoch")==grant.arena().arenaEpoch()
                && n(plan,"expectedArenaRevision")==grant.arena().arenaRevision(),"TANK_ROTATION_GRANT_MISMATCH");
        for(String key:List.of("requestHash","previousOwnerFileSha256","previousRecipeHash","nextRecipeHash"))KneekuraDebugActionJournal.hash(t(plan,key));
        KneekuraDebugArenaController.range(n(plan,"previousTankEpoch"),0,KneekuraDebugTankRotationController.MAX_EPOCH-1);
        boolean permitted=false;JsonElement permissions=world.get("permissions");
        if(permissions!=null && permissions.isJsonArray())for(JsonElement p:permissions.getAsJsonArray())permitted|=p.isJsonPrimitive() && p.getAsJsonPrimitive().isString() && p.getAsString().equals(PERMISSION);
        require(permitted && t(world,"dimensionId").equals("minecraft:overworld") && grant.dimensionId().equals(t(world,"dimensionId")),"TANK_ROTATION_PERMISSION_MISSING");
        require(grant.maxActions()==0 && grant.maxCaptures()==0 && grant.allowedActions().isEmpty() && empty(request,"initial_state") && empty(request,"actions")
                && n(o(request,"budgets"),"max_actions")==0 && n(o(request,"budgets"),"max_captures")==0
                && t(o(request,"visual_rig"),"mode").equals("none") && trigger==null,"TANK_ROTATION_MAINTENANCE_ONLY");
        require(previousOwnerBytes!=null && previousOwnerBytes.length<=65536 && KneekuraDebugOwnerFiles.sha256(previousOwnerBytes).equals(t(plan,"previousOwnerFileSha256")),"TANK_ROTATION_SAVED_OWNER_BYTES_MISMATCH");
        String text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(previousOwnerBytes)).toString();
        JsonObject owner=KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(text));
        require(t(owner,"status").equals("GEOMETRY_VERIFIED") && n(owner,"arenaEpoch")==n(plan,"previousTankEpoch"),"TANK_ROTATION_SAVED_OWNER_STATE");
        String sourceHash=t(owner,"recipeHash");if(sourceHash.startsWith("sha256:"))sourceHash=sourceHash.substring(7);
        require(KneekuraDebugActionJournal.hash(sourceHash).equals(t(plan,"previousRecipeHash")) && hash(o(owner,"recipe")).equals(sourceHash),"TANK_ROTATION_PREDECESSOR_RECIPE_MISMATCH");
        JsonArray reservations=new JsonArray();if(owner.has("reservedRegions")){require(owner.get("reservedRegions").isJsonArray(),"TANK_ROTATION_RESERVATION_LIMIT");reservations=owner.getAsJsonArray("reservedRegions");}
        require(reservations.size()<16,"TANK_ROTATION_RESERVATION_LIMIT");
        var next=recipe(o(plan,"nextRecipe"));require(hash(o(plan,"nextRecipe")).equals(t(plan,"nextRecipeHash")),"TANK_ROTATION_NEXT_RECIPE_HASH_MISMATCH");
        List<KneekuraDebugTankRotationController.Geometry> prior=new ArrayList<>();
        for(JsonElement entry:reservations)prior.add(recipe(KneekuraDebugActionJournal.object(entry)));prior.add(recipe(o(owner,"recipe")));
        for(var old:prior)require(!next.overlaps(old),"TANK_ROTATION_RESERVED_REGION_OVERLAP");
        return new Validated(plan,owner,next,prior);
    }
    static KneekuraDebugTankRotationController.Geometry recipe(JsonObject r) throws IOException {
        KneekuraDebugActionJournal.keys(r,"v","kind","preset","dimensions","origin","dimension","shellBlock","environment","presentation");
        require(n(r,"v")==1 && t(r,"kind").equals("tank_recipe") && t(r,"dimension").equals("minecraft:overworld") && t(r,"shellBlock").equals("minecraft:black_concrete"),"TANK_ROTATION_RECIPE_SCOPE");
        JsonObject sizes=o(r,"dimensions"),origin=o(r,"origin");KneekuraDebugActionJournal.keys(sizes,"width","height","depth");KneekuraDebugActionJournal.keys(origin,"x","y","z");
        int width=bounded(sizes,"width",1,64),height=bounded(sizes,"height",1,64),depth=bounded(sizes,"depth",1,64);
        boolean preset=switch(t(r,"preset")){case "custom"->true;case "narrow"->width==9 && height==7 && depth==9;case "normal"->width==17 && height==11 && depth==17;case "wide"->width==19 && height==11 && depth==19;default->false;};
        require(preset,"TANK_ROTATION_PRESET_MISMATCH");
        var geometry=new KneekuraDebugTankRotationController.Geometry(bounded(origin,"x",-29999983,29999983),bounded(origin,"y",-63,318),bounded(origin,"z",-29999983,29999983),width,height,depth);
        JsonObject environment=o(r,"environment");KneekuraDebugActionJournal.keys(environment,"difficulty","time","daylightCycle","weatherCycle","weather","mobSpawning");
        JsonObject expected=new JsonObject();expected.addProperty("difficulty","normal");expected.addProperty("time",6000);expected.addProperty("daylightCycle",false);expected.addProperty("weatherCycle",false);expected.addProperty("weather","clear");expected.addProperty("mobSpawning",false);
        require(environment.equals(expected),"TANK_ROTATION_ENVIRONMENT_RECIPE");JsonObject presentation=o(r,"presentation");KneekuraDebugActionJournal.keys(presentation,"mode","gridSpacing");
        require((t(presentation,"mode").equals("OBSERVATION_BRIGHT") || t(presentation,"mode").equals("NATIVE")) && n(presentation,"gridSpacing")==1,"TANK_ROTATION_PRESENTATION_SCOPE");return geometry;
    }
    private static int bounded(JsonObject o,String key,int min,int max)throws IOException{long value=n(o,key);KneekuraDebugArenaController.range(value,min,max);return (int)value;}
    private static boolean empty(JsonObject o,String key){JsonElement e=o.get(key);return e!=null && e.isJsonArray() && e.getAsJsonArray().isEmpty();}
    private static String hash(JsonObject o){return KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(o));}
    private static String t(JsonObject o,String key)throws IOException{return KneekuraDebugArenaController.text(o,key);}
    private static long n(JsonObject o,String key)throws IOException{return KneekuraDebugArenaController.integer(o,key);}
    private static JsonObject o(JsonObject o,String key)throws IOException{return KneekuraDebugActionJournal.object(o.get(key));}
    private static void require(boolean condition,String reason)throws IOException{if(!condition)throw new IOException(reason);}
}
