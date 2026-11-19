package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.nio.file.*;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

public final class KneekuraDebugArenaControllerSelfTest {
    static int checks;
    static void check(boolean b, String label) { checks++; if (!b) throw new AssertionError(label); }
    static void rejects(KneekuraDebugActionJournalSelfTest.RunnableWithException r, String label) throws Exception {
        try { r.run(); throw new AssertionError("did not reject " + label); }
        catch (IllegalArgumentException | IllegalStateException | IOException expected) { checks++; }
    }
    static final String BASE = "a".repeat(64);
    static final KneekuraDebugArenaController.Identity ID = new KneekuraDebugArenaController.Identity("session","run","snapshot",1,"nonce-0000000000000001","experiment");
    static final KneekuraDebugArenaController.Bounds BOX = new KneekuraDebugArenaController.Bounds(0,0,0,8,8,8);
    static final class MemoryBackend implements KneekuraDebugArenaController.Backend {
        String hash = BASE; int writes, events; Runnable duringApply=()->{},duringObserve=()->{}; boolean failMutation, failEvidence, wrongReset, failGuard;
        public void requireOwnerThread() { }
        public void guard() throws IOException { if(failGuard)throw new IOException("gate revoked"); }
        public void preflight(JsonObject action) { }
        public JsonObject apply(JsonObject action) throws IOException {
            writes++; duringApply.run(); hash="b".repeat(64); if (failMutation) throw new IOException("interrupted after mutation");
            JsonObject result = new JsonObject(); result.addProperty("postconditionMatched",true); return result;
        }
        public String stateHash() { return hash; }
        public void restoreBaseline() { writes++; hash = wrongReset ? "c".repeat(64) : BASE; }
        public String observe(long epoch, long tick, String kind, JsonObject payload) throws IOException {
            events++; duringObserve.run(); if (failEvidence) throw new IOException("evidence unavailable");
            check(payload.get("scope").getAsString().equals("BOUNDED_BLOCKS_AND_SUBJECT_POSE"), "scoped proof");
            return String.format("%064x",events);
        }
    }
    record Rig(Path run, AtomicLong clock, MemoryBackend backend, KneekuraDebugArenaController controller) { }
    static Rig rig() throws Exception {
        Path run=Files.createTempDirectory("lab-java-controller").toRealPath(); Files.createDirectories(run.resolve("control/actions"));
        AtomicLong clock = new AtomicLong(1_000_000); MemoryBackend backend = new MemoryBackend();
        var arena=new KneekuraDebugArenaController.Arena("arena",1,0,BASE,BOX);
        var lease=new KneekuraDebugArenaController.Lease("lease",ID,clock.get(),clock.get()+1_000_000_000L,4,Set.of("wait_ticks","teleport_subject","set_block"));
        var subjects=Map.of("subject", new KneekuraDebugArenaController.Subject("00000000-0000-0000-0000-000000000001","minecraft:armor_stand"));
        return new Rig(run,clock,backend,new KneekuraDebugArenaController(ID,arena,lease,subjects,backend,new KneekuraDebugActionJournal(run),clock::get));
    }
    static KneekuraDebugArenaController.Command command(Rig r,String key,String type,JsonObject args) throws Exception {
        JsonObject a=KneekuraDebugActionJournalSelfTest.action(key); a.addProperty("type",type); a.add("args",args);
        a.addProperty("arenaEpoch",r.controller.snapshot().arenaEpoch()); a.addProperty("expectedArenaRevision",r.controller.snapshot().arenaRevision());
        if (!type.equals("reset_arena")) KneekuraDebugActionJournalSelfTest.fixture(r.run,a);
        return new KneekuraDebugArenaController.Command(a,ID.handshakeNonce(),"lease");
    }
    static JsonObject waitArgs(int ticks) { JsonObject a=new JsonObject(); a.addProperty("ticks",ticks); return a; }
    static JsonObject blockArgs(int x) { JsonObject a=new JsonObject(); JsonArray p=new JsonArray(); p.add(x);p.add(2);p.add(2);a.add("position",p);a.addProperty("block","minecraft:stone");return a; }
    public static void main(String[] args) throws Exception {
        Rig leaseWindow=rig();leaseWindow.controller.requireLeaseRemaining(leaseWindow.controller.snapshot(),800);rejects(()->leaseWindow.controller.requireLeaseRemaining(leaseWindow.controller.snapshot(),1100),"capture barrier cannot exceed remaining lease");
        Rig r=rig(); var c=command(r,"set","set_block",blockArgs(2));
        check(r.controller.submit(c,10).status().equals("VERIFIED"),"block verifies");
        check(r.backend.writes==1 && r.controller.snapshot().arenaRevision()==1,"one mutation/revision");
        check(r.controller.submit(c,10).status().equals("VERIFIED"),"duplicate returns prior terminal despite old revision");
        check(r.backend.writes==1,"no duplicate world invocation");
        var reset=command(r,"reset","reset_arena",new JsonObject());
        check(r.controller.reset(reset,10).classification().equals("INCONCLUSIVE"),"reset no full world clean");
        check(r.controller.snapshot().arenaEpoch()==2 && r.controller.snapshot().arenaRevision()==2,"reset fences epoch/revision");
        check(r.controller.reset(reset,10).status().equals("VERIFIED"),"reset duplicate no replay");
        check(r.backend.writes==2,"reset writes once");
        var stale=command(r,"stale","set_block",blockArgs(2)); JsonObject sa=stale.action(); sa.addProperty("arenaEpoch",1);
        rejects(()->r.controller.submit(new KneekuraDebugArenaController.Command(sa,ID.handshakeNonce(),"lease"),10),"old epoch");
        Rig w=rig(); var wait=command(w,"wait","wait_ticks",waitArgs(2));
        check(w.controller.submit(wait,20).status().equals("ACCEPTED"),"wait pending");
        rejects(()->w.controller.submit(command(w,"other","set_block",blockArgs(2)),20),"single writer queue");
        check(w.controller.onTick(21).status().equals("ACCEPTED"),"one tick not complete");
        check(w.controller.onTick(22).status().equals("VERIFIED"),"exact elapsed server ticks");
        check(w.backend.writes==0 && w.controller.snapshot().arenaRevision()==0,"wait no world/revision mutation");
        for (String field:List.of("debugSessionId","runId","runSnapshotId","processEpoch","experimentId","arenaId","arenaEpoch","expectedArenaRevision")) {
            Rig f=rig(); var good=command(f,"bad-"+field,"set_block",blockArgs(2)); JsonObject bad=good.action();
            if (field.equals("processEpoch")||field.equals("arenaEpoch")||field.equals("expectedArenaRevision")) bad.addProperty(field,99); else bad.addProperty(field,"wrong");
            rejects(()->f.controller.submit(new KneekuraDebugArenaController.Command(bad,ID.handshakeNonce(),"lease"),1),field);
            check(f.backend.writes==0,"identity rejected before mutation");
        }
        Rig bad=rig(); var b=command(bad,"nonce","set_block",blockArgs(2));
        rejects(()->bad.controller.submit(new KneekuraDebugArenaController.Command(b.action(),"wrong","lease"),1),"nonce");
        rejects(()->bad.controller.submit(new KneekuraDebugArenaController.Command(b.action(),ID.handshakeNonce(),"wrong"),1),"lease");
        rejects(()->bad.controller.submit(command(bad,"outside","set_block",blockArgs(8)),1),"half open bounds");
        JsonObject item=new JsonObject();item.addProperty("subject_id","subject");item.addProperty("hand","main_hand");item.addProperty("ticks",1);
        rejects(()->bad.controller.submit(command(bad,"item","use_item",item),1),"unsupported item use");
        Rig exp=rig();var pending=command(exp,"exp","wait_ticks",waitArgs(2)); exp.controller.submit(pending,1);exp.clock.addAndGet(2_000_000_000L);
        check(exp.controller.onTick(2).status().equals("OUTCOME_UNKNOWN")&&exp.controller.snapshot().unsafe(),"expiry pending wait blocks reuse");
        Rig gate=rig();gate.controller.submit(command(gate,"gate","wait_ticks",waitArgs(3)),1);gate.backend.failGuard=true;
        check(gate.controller.onTick(2).status().equals("OUTCOME_UNKNOWN")&&gate.controller.snapshot().unsafe(),"owner gate revoked during pending wait is journaled unknown");
        Rig detach=rig();var detachCommand=command(detach,"detach","wait_ticks",waitArgs(3));detach.controller.submit(detachCommand,1);detach.backend.failGuard=true;detach.clock.addAndGet(2_000_000_000L);detach.controller.revoke();
        check(detach.controller.snapshot().unsafe()&&detach.controller.snapshot().idle(),"revoked expired owner can safely detach without world mutation");
        check(new KneekuraDebugActionJournal(detach.run).lookup(detachCommand.action()).equals("OUTCOME_UNKNOWN"),"teardown persists pending outcome UNKNOWN");
        Rig gap=rig();gap.controller.submit(command(gap,"gap","wait_ticks",waitArgs(3)),1);
        check(gap.controller.onTick(3).status().equals("OUTCOME_UNKNOWN"),"missing tick proof never assumed");
        Rig mutation=rig();mutation.backend.failMutation=true;
        check(mutation.controller.submit(command(mutation,"mut","set_block",blockArgs(2)),1).status().equals("OUTCOME_UNKNOWN"),"interrupted mutation unknown");
        rejects(()->mutation.controller.submit(command(mutation,"later","set_block",blockArgs(2)),2),"unsafe no more writes");
        Rig evidence=rig();evidence.backend.failEvidence=true;
        check(evidence.controller.submit(command(evidence,"ev","set_block",blockArgs(2)),1).status().equals("OUTCOME_UNKNOWN"),"missing durable evidence unknown");
        check(evidence.controller.snapshot().arenaRevision()==0,"no revision without proof");
        Rig resetFail=rig();resetFail.backend.wrongReset=true;
        check(resetFail.controller.reset(command(resetFail,"resetfail","reset_arena",new JsonObject()),1).status().equals("OUTCOME_UNKNOWN"),"reset mismatch unknown");
        check(resetFail.controller.snapshot().arenaEpoch()==1 && resetFail.controller.snapshot().unsafe(),"failed reset cannot reuse arena");
        Rig duringApply=rig();duringApply.backend.duringApply=()->duringApply.clock.addAndGet(2_000_000_000L);
        check(duringApply.controller.submit(command(duringApply,"late-apply","set_block",blockArgs(2)),1).status().equals("OUTCOME_UNKNOWN"),"lease expires during mutation never VERIFIED");
        Rig duringObserve=rig();duringObserve.backend.duringObserve=()->duringObserve.clock.addAndGet(2_000_000_000L);
        check(duringObserve.controller.submit(command(duringObserve,"late-observe","set_block",blockArgs(2)),1).status().equals("OUTCOME_UNKNOWN"),"lease expires during durable observation never VERIFIED");
        Rig budget=rig();for(int i=0;i<4;i++) budget.controller.submit(command(budget,"budget"+i,"set_block",blockArgs(2)),1);
        rejects(()->budget.controller.submit(command(budget,"budget5","set_block",blockArgs(2)),1),"action count budget");
        check(budget.controller.reset(command(budget,"cleanup","reset_arena",new JsonObject()),1).status().equals("VERIFIED"),"one explicit owner cleanup reset after exhausted requested action budget");
        rejects(()->budget.controller.reset(command(budget,"cleanup2","reset_arena",new JsonObject()),1),"separate cleanup reset allowance bounded to one");
        rejects(()->new KneekuraDebugArenaController.Bounds(0,0,0,65,1,1),"edge size");
        rejects(()->new KneekuraDebugArenaController.Bounds(0,-65,0,1,1,1),"world height");
        System.out.println("Java bounded controller self-test: "+checks+" checks passed");
    }
}
