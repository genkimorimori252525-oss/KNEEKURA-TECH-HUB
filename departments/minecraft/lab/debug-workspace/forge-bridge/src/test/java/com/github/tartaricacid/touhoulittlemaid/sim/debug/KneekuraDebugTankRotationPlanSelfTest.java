package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Consumes the real Node sealed JSON closure; no native installation or world operations. */
public final class KneekuraDebugTankRotationPlanSelfTest {
    static int checks;
    interface Checked { void run() throws Exception; }
    static void check(boolean value, String label) { checks++; if (!value) throw new AssertionError(label); }
    static void rejects(Checked call, String label) throws Exception {
        try { call.run(); throw new AssertionError("did not reject " + label); }
        catch (IOException | IllegalArgumentException expected) { checks++; }
    }
    static JsonObject object(JsonObject parent, String key) { return parent.getAsJsonObject(key); }
    static KneekuraDebugTankRotationPlan.Validated parse(JsonObject fixture) throws IOException {
        return KneekuraDebugTankRotationPlan.parse(object(fixture,"plan"),KneekuraDebugArenaOwnerGrant.parse(object(fixture,"grant")),object(fixture,"request"),object(fixture,"world"),
                fixture.get("trigger").isJsonNull() ? null : object(fixture,"trigger"),Base64.getDecoder().decode(fixture.get("previousOwnerBytes").getAsString()));
    }
    static void rehashRecipe(JsonObject plan) { plan.addProperty("nextRecipeHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(object(plan,"nextRecipe")))); }
    public static void main(String[] args) throws Exception {
        JsonObject fixture = KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(Files.readString(Path.of(args[0]))));
        var valid = parse(fixture); check(valid != null, "actual sealed Node Tank plan accepted by Java");
        check(valid.next().width() == 9 && valid.next().height() == 7 && valid.next().depth() == 9 && valid.priorRegions().size() == 1, "exact next geometry and preserved predecessor");
        check(valid.intent().get("previousTankEpoch").getAsLong() == 8 && valid.intent().get("expectedArenaEpoch").getAsLong() == 0, "distinct source Tank and Arena epochs");
        valid.intent().addProperty("scope","changed"); check(parse(fixture).intent().get("scope").getAsString().equals(KneekuraDebugTankRotationPlan.PERMISSION), "validated intent immutable copy");
        var grant=KneekuraDebugArenaOwnerGrant.parse(object(fixture,"grant"));String envelopeHash="e".repeat(64);
        JsonObject receipt=new JsonObject();receipt.addProperty("schemaVersion",1);receipt.addProperty("kind","owner_installation_receipt");receipt.addProperty("status","INSTALLED_SCOPED_CONTROL");
        receipt.addProperty("scope",KneekuraDebugOwnerInputs.CONTROL);receipt.addProperty("ownerEnvelopeHash",envelopeHash);
        for(String key:List.of("debugSessionId","runId","runSnapshotId","processEpoch","requestHash","leaseId","arenaId"))receipt.add(key,object(fixture,"plan").get(key));
        receipt.addProperty("arenaEpoch",grant.arena().arenaEpoch());receipt.addProperty("arenaRevision",grant.arena().arenaRevision());
        receipt.addProperty("receiptHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(receipt)));
        check(receipt.get("receiptHash").getAsString().equals(KneekuraDebugTankRotationPlan.installationReceiptHash(receipt,envelopeHash,grant)),"source installation hash bound to exact maintenance identity");
        for(String key:List.of("schemaVersion","kind","status","scope","ownerEnvelopeHash","debugSessionId","runId","runSnapshotId","processEpoch","requestHash","leaseId","arenaId","arenaEpoch","arenaRevision","receiptHash")){
            JsonObject bad=receipt.deepCopy();JsonElement value=bad.get(key);if(value.getAsJsonPrimitive().isNumber())bad.addProperty(key,value.getAsLong()+1);else bad.addProperty(key,"changed");
            if(!key.equals("receiptHash")){bad.remove("receiptHash");bad.addProperty("receiptHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(bad)));}
            rejects(()->KneekuraDebugTankRotationPlan.installationReceiptHash(bad,envelopeHash,grant),"installation binding "+key);
        }
        for (String key : List.of("schemaVersion","scope","debugSessionId","runId","runSnapshotId","processEpoch","handshakeNonce","requestHash","grantId","leaseId","arenaId",
                "expectedArenaEpoch","expectedArenaRevision","previousOwnerFileSha256","previousRecipeHash","previousTankEpoch","nextRecipeHash")) {
            JsonObject bad=fixture.deepCopy(),plan=object(bad,"plan");JsonElement value=plan.get(key);
            if(value.getAsJsonPrimitive().isNumber())plan.addProperty(key,value.getAsLong()+1);else plan.addProperty(key,"changed");rejects(()->parse(bad),"sealed "+key);
        }
        for(String extra:List.of("runtimeAccepted","ttlMs","command")){JsonObject bad=fixture.deepCopy();object(bad,"plan").addProperty(extra,true);rejects(()->parse(bad),"extra "+extra);}
        JsonObject permission=fixture.deepCopy();object(permission,"world").getAsJsonArray("permissions").remove(1);rejects(()->parse(permission),"separate rotation permission");
        JsonObject actions=fixture.deepCopy();object(actions,"request").getAsJsonArray("actions").add(new JsonObject());rejects(()->parse(actions),"maintenance excludes actions");
        JsonObject capture=fixture.deepCopy();object(capture,"grant").addProperty("maxCaptures",4);rejects(()->parse(capture),"maintenance excludes captures");
        JsonObject trigger=fixture.deepCopy();trigger.add("trigger",new JsonObject());rejects(()->parse(trigger),"maintenance excludes triggers");
        for(String fault:List.of("overlap","edge","volume","preset","shell","environment","presentation","extra")) {
            JsonObject bad=fixture.deepCopy(),p=object(bad,"plan"),recipe=object(p,"nextRecipe");
            switch(fault){case "overlap"->object(recipe,"origin").addProperty("x",20);case "edge"->object(recipe,"origin").addProperty("y",319);
                case "volume"->{recipe.addProperty("preset","custom");object(recipe,"dimensions").addProperty("width",64);object(recipe,"dimensions").addProperty("height",64);object(recipe,"dimensions").addProperty("depth",64);}
                case "preset"->recipe.addProperty("preset","wide");case "shell"->recipe.addProperty("shellBlock","minecraft:lava");
                case "environment"->object(recipe,"environment").addProperty("mobSpawning",true);case "presentation"->object(recipe,"presentation").addProperty("gridSpacing",2);case "extra"->recipe.addProperty("command","x");}
            rehashRecipe(p);rejects(()->parse(bad),"recipe "+fault);
        }
        for(String fault:List.of("status","recipe","epoch","reservations","duplicate","oversize")) {
            JsonObject bad=fixture.deepCopy(),p=object(bad,"plan");byte[] original=Base64.getDecoder().decode(bad.get("previousOwnerBytes").getAsString());
            JsonObject owner=KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(new String(original,StandardCharsets.UTF_8)));
            switch(fault){case "status"->owner.addProperty("status","OUTCOME_UNKNOWN");case "recipe"->owner.addProperty("recipeHash","b".repeat(64));case "epoch"->owner.addProperty("arenaEpoch",9);
                case "reservations"->{JsonArray rows=new JsonArray();for(int i=0;i<16;i++)rows.add(owner.get("recipe").deepCopy());owner.add("reservedRegions",rows);}}
            byte[] bytes=KneekuraDebugActionJournal.canonical(owner).getBytes(StandardCharsets.UTF_8);
            if(fault.equals("duplicate"))bytes="{\"status\":\"GEOMETRY_VERIFIED\",\"status\":\"GEOMETRY_VERIFIED\"}".getBytes(StandardCharsets.UTF_8);
            if(fault.equals("oversize"))bytes=new byte[65537];bad.addProperty("previousOwnerBytes",Base64.getEncoder().encodeToString(bytes));p.addProperty("previousOwnerFileSha256",KneekuraDebugOwnerFiles.sha256(bytes));
            rejects(()->parse(bad),"predecessor "+fault);
        }
        System.out.println("Real Node/Java sealed Tank rotation plan cases passed: " + checks + "; intent parser only; Minecraft NOT_RUN");
    }
}
