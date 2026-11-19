package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;

/** Actual shared on-disk receipts, without a Minecraft process. */
public final class KneekuraDebugActionJournalSelfTest {
    static int checks;
    static void check(boolean value, String name) {
        checks++; if (!value) throw new AssertionError(name);
    }
    static void rejects(RunnableWithException op, String name) throws Exception {
        try { op.run(); throw new AssertionError("did not reject " + name); }
        catch (IllegalArgumentException | java.io.IOException | IllegalStateException expected) { checks++; }
    }
    interface RunnableWithException { void run() throws Exception; }
    static JsonObject action(String key) {
        JsonObject a = new JsonObject();
        a.addProperty("schemaVersion", 1); a.addProperty("debugSessionId", "session");
        a.addProperty("runId", "run"); a.addProperty("runSnapshotId", "snapshot");
        a.addProperty("processEpoch", 1); a.addProperty("experimentId", "experiment");
        a.addProperty("arenaId", "arena"); a.addProperty("arenaEpoch", 1);
        a.addProperty("expectedArenaRevision", 0); a.addProperty("actionId", "action-" + key);
        a.addProperty("idempotencyKey", key); a.addProperty("type", "wait_ticks");
        JsonObject args = new JsonObject(); args.addProperty("ticks", 2); a.add("args", args);
        return a;
    }
    static Path fixture(Path run, JsonObject a) throws Exception {
        Path directory = run.resolve("control/actions/" + KneekuraDebugActionJournal.sha256(a.get("idempotencyKey").getAsString()));
        Files.createDirectories(directory);
        String bytes = KneekuraDebugActionJournal.canonical(a);
        String hash = KneekuraDebugActionJournal.sha256(bytes);
        Files.writeString(directory.resolve("canonical-action.json"), bytes);
        JsonObject request = new JsonObject(); request.addProperty("schemaVersion", 1);
        request.addProperty("payloadHash", hash); request.add("action", a.deepCopy());
        Files.writeString(directory.resolve("request.json"), request.toString());
        JsonObject body = new JsonObject(); body.addProperty("sequence", 0);
        body.addProperty("payloadHash", hash); body.addProperty("previousHash", hash);
        body.addProperty("status", "REQUESTED"); body.add("evidenceHashes", new JsonArray());
        body.addProperty("receiptHash", KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(body)));
        Files.writeString(directory.resolve("receipt-000000.json"), body.toString());
        return directory;
    }
    public static void main(String[] args) throws Exception {
        Path run = args.length > 0 ? Path.of(args[0]).toRealPath() : Files.createTempDirectory("lab-java-journal").toRealPath();
        KneekuraDebugActionJournal journal = new KneekuraDebugActionJournal(run);
        JsonObject a = action("complete"); fixture(run, a);
        var accepted = journal.accept(a);
        check("ACCEPTED".equals(accepted.status()), "durable acceptance");
        check(Files.exists(accepted.handle().directory().resolve("receipt-000001.json")), "acceptance on disk before caller gets handle");
        rejects(() -> journal.accept(a), "concurrent writer");
        accepted.handle().append("APPLIED", List.of("a".repeat(64)));
        accepted.handle().append("VERIFIED", List.of("b".repeat(64)));
        accepted.handle().close();
        check(journal.accept(a).status().equals("VERIFIED"), "verified duplicate read-only");
        JsonObject changed = a.deepCopy(); changed.getAsJsonObject("args").addProperty("ticks", 3);
        rejects(() -> journal.accept(changed), "same key different payload");
        JsonObject crash = action("crash"); fixture(run, crash);
        var c = journal.accept(crash); c.handle().close();
        check(journal.lookup(crash).equals("OUTCOME_UNKNOWN"), "accepted interruption unknown");
        rejects(() -> journal.accept(crash), "abandoned accepted action never replayed");
        JsonObject gap = action("gap"); Path g = fixture(run, gap);
        Files.move(g.resolve("receipt-000000.json"), g.resolve("receipt-000001.json"));
        rejects(() -> journal.accept(gap), "receipt gap");
        JsonObject torn = action("torn"); Path t = fixture(run, torn);
        Files.writeString(t.resolve("receipt-000000.json"), "{\"status\":");
        rejects(() -> journal.accept(torn), "torn receipt");
        JsonObject bad = action("sidecar"); Path b = fixture(run, bad);
        Files.writeString(b.resolve("canonical-action.json"), "{}");
        rejects(() -> journal.accept(bad), "sidecar drift");
        rejects(() -> KneekuraDebugActionJournal.parse("{\"a\":1,\"a\":2}"), "duplicate JSON keys");
        rejects(() -> KneekuraDebugActionJournal.parse("{\"a\":NaN}"), "non JSON numbers");
        rejects(() -> KneekuraDebugActionJournal.parse("{\"a\":9007199254740992}"), "unsafe JSON numbers");
        for(JsonElement invalid:List.of(new JsonPrimitive(1.5),new JsonPrimitive("1"))){JsonObject malformed=action("schema"+checks);Path dir=fixture(run,malformed);JsonObject request=JsonParser.parseString(Files.readString(dir.resolve("request.json"))).getAsJsonObject();request.add("schemaVersion",invalid);Files.writeString(dir.resolve("request.json"),request.toString());rejects(()->journal.accept(malformed),"exact numeric schemaVersion");}
        JsonObject sequence=action("sequence");Path sequenceDir=fixture(run,sequence);JsonObject receipt=JsonParser.parseString(Files.readString(sequenceDir.resolve("receipt-000000.json"))).getAsJsonObject();receipt.remove("receiptHash");receipt.addProperty("sequence","0");receipt.addProperty("receiptHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(receipt)));Files.writeString(sequenceDir.resolve("receipt-000000.json"),receipt.toString());rejects(()->journal.accept(sequence),"numeric receipt sequence required");
        System.out.println("Java shared journal self-test: " + checks + " checks passed");
    }
}
