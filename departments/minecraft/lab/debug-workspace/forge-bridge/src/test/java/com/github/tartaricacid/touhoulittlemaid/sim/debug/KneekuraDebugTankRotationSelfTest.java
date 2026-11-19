package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

public final class KneekuraDebugTankRotationSelfTest {
    static int checks;
    static void check(boolean condition, String label) { checks++; if (!condition) throw new AssertionError(label); }
    interface Checked { void run() throws Exception; }
    static void rejects(Checked call, String label) throws Exception {
        try { call.run(); throw new AssertionError("did not reject " + label); }
        catch (IllegalArgumentException | IOException expected) { checks++; }
    }
    static final class MemoryBackend implements KneekuraDebugTankRotationController.Backend {
        final Map<KneekuraDebugTankRotationController.Cell, String> blocks = new HashMap<>();
        final List<String> order = new ArrayList<>();
        final AtomicLong clock;
        boolean authorized = true, quiet = true, reserved, failReserve, failGenerate, failPublish, failUnknown, corruptReadback;
        int writes, preflight, generated, verified, publications, unknowns, guards;
        Runnable afterCell = () -> {};
        MemoryBackend(AtomicLong clock) { this.clock = clock; }
        public void guard() throws IOException { guards++; if (!authorized) throw new IOException("OWNER_CHANGED"); }
        public void requireQuiet() throws IOException { if (!quiet) throw new IOException("WORLD_NOT_QUIET"); }
        public void preflight(KneekuraDebugTankRotationController.Cell cell, boolean interior) throws IOException {
            preflight++; if (blocks.containsKey(cell)) throw new IOException("REGION_NOT_EMPTY"); afterCell.run();
        }
        public void generate(KneekuraDebugTankRotationController.Cell cell, boolean interior) throws IOException {
            check(reserved, "durable reservation precedes every generation cell"); generated++;
            if (blocks.containsKey(cell)) throw new IOException("REGION_DRIFT");
            if (!interior) { blocks.put(cell, "minecraft:black_concrete"); writes++; order.add("write"); }
            afterCell.run(); if (failGenerate) throw new IOException("AFTER_MUTATION_FAILURE");
        }
        public String verify(KneekuraDebugTankRotationController.Cell cell, boolean interior) throws IOException {
            verified++; String actual = blocks.getOrDefault(cell, "minecraft:air");
            if (corruptReadback || !actual.equals(interior ? "minecraft:air" : "minecraft:black_concrete")) throw new IOException("GEOMETRY_MISMATCH");
            afterCell.run(); return actual;
        }
        public void reserve(KneekuraDebugTankRotationController.Plan plan) throws IOException {
            order.add("reserve"); if (failReserve) throw new IOException("RESERVATION_FAILED"); reserved = true;
        }
        public void publishVerified(KneekuraDebugTankRotationController.Plan plan, String fingerprint) throws IOException {
            publications++; check(fingerprint.matches("[a-f0-9]{64}"), "bounded actual verification fingerprint");
            order.add("publish"); if (failPublish) throw new IOException("PUBLICATION_FAILED");
        }
        public void unknown(KneekuraDebugTankRotationController.Snapshot snapshot) throws IOException {
            unknowns++; order.add("unknown"); if (failUnknown) throw new IOException("UNKNOWN_PERSISTENCE_FAILED");
            check(snapshot.phase() == KneekuraDebugTankRotationController.Phase.OUTCOME_UNKNOWN, "unknown never success");
        }
    }
    record Rig(AtomicLong clock, MemoryBackend backend, KneekuraDebugTankRotationController controller) {}
    static final KneekuraDebugTankRotationController.Geometry OLD = new KneekuraDebugTankRotationController.Geometry(0, 224, 0, 19, 11, 19);
    static final KneekuraDebugTankRotationController.Geometry NEXT = new KneekuraDebugTankRotationController.Geometry(40, 224, 0, 9, 7, 9);
    static Rig rig() throws Exception {
        AtomicLong clock = new AtomicLong(1000); MemoryBackend b = new MemoryBackend(clock);
        var plan = new KneekuraDebugTankRotationController.Plan(NEXT, List.of(OLD), 2, clock.get(), clock.get() + 120_000_000_000L);
        return new Rig(clock, b, new KneekuraDebugTankRotationController(plan, b, clock::get));
    }
    static KneekuraDebugTankRotationController.Snapshot finish(Rig r, long tick) throws Exception {
        for (int i = 0; i < 1200; i++, tick++) {
            var s = r.controller.onTick(tick);
            if (s.phase() == KneekuraDebugTankRotationController.Phase.VERIFIED || s.phase() == KneekuraDebugTankRotationController.Phase.OUTCOME_UNKNOWN) return s;
        }
        throw new AssertionError("finite generator did not terminate");
    }
    static void unknown(Rig r, String label) {
        check(r.controller.snapshot().phase() == KneekuraDebugTankRotationController.Phase.OUTCOME_UNKNOWN, label);
        check(r.backend.publications == 0, label + " no publication");
    }
    public static void main(String[] args) throws Exception {
        Rig paced = rig(); paced.backend.afterCell = () -> paced.clock.addAndGet(10_000_000L);
        var pacedFirst = paced.controller.onTick(10);
        check(pacedFirst.preflightCells() == 3 && pacedFirst.cursor() == 3, "slow cells yield between completed cells after 25ms of tick work");
        check(pacedFirst.phase() == KneekuraDebugTankRotationController.Phase.PREFLIGHT && !paced.backend.reserved, "time-budget yield retains preflight without reservation or publication");
        check(paced.backend.guards >= 3 * paced.backend.preflight + 2, "paced work retains authority checks around every completed cell");
        long simulatedTickStart = 50_001_000L; int pacedTicks = 1;
        for (long tick = 11; tick < 1200 && paced.controller.snapshot().phase() != KneekuraDebugTankRotationController.Phase.VERIFIED; tick++) {
            paced.clock.set(simulatedTickStart); simulatedTickStart += 50_000_000L;
            var before = paced.controller.snapshot(); var after = paced.controller.onTick(tick); pacedTicks++;
            check(after.preflightCells() - before.preflightCells() + after.generationCells() - before.generationCells() + after.verifiedCells() - before.verifiedCells() <= 3, "all paced phases yield without skipping completed-cell accounting");
            check(after.phase() != KneekuraDebugTankRotationController.Phase.OUTCOME_UNKNOWN, "normal 20TPS paced work stays within the original finite lease");
        }
        var pacedDone = paced.controller.snapshot();
        check(pacedDone.phase() == KneekuraDebugTankRotationController.Phase.VERIFIED && pacedTicks > 15, "paced three-pass generation reaches verified over multiple server ticks");
        check(pacedDone.preflightCells() == NEXT.allocationCells() && pacedDone.generationCells() == NEXT.allocationCells() && pacedDone.verifiedCells() == NEXT.allocationCells(), "paced completion covers every allocated cell in every phase");
        check(paced.backend.writes == NEXT.allocationCells() - NEXT.innerCells() && paced.backend.publications == 1, "paced shell mutation and terminal publication remain exactly once");
        Rig oneSlowCell = rig(); oneSlowCell.backend.afterCell = () -> oneSlowCell.clock.addAndGet(40_000_000L);
        var single = oneSlowCell.controller.onTick(10);
        check(single.preflightCells() == 1 && single.phase() == KneekuraDebugTankRotationController.Phase.PREFLIGHT, "one synchronous delegate may exceed the time budget but no next cell starts");
        Rig revokedAfterYield = rig(); revokedAfterYield.backend.afterCell = () -> revokedAfterYield.clock.addAndGet(10_000_000L);
        revokedAfterYield.controller.onTick(10); int beforeRevocation = revokedAfterYield.backend.preflight; revokedAfterYield.backend.authorized = false;
        revokedAfterYield.controller.onTick(11); unknown(revokedAfterYield, "authority loss after time-budget yield");
        check(revokedAfterYield.backend.preflight == beforeRevocation && !revokedAfterYield.backend.reserved, "yield never caches authorization for the next tick");
        Rig expiredAfterYield = rig(); expiredAfterYield.backend.afterCell = () -> expiredAfterYield.clock.addAndGet(10_000_000L);
        expiredAfterYield.controller.onTick(10); int beforeExpiry = expiredAfterYield.backend.preflight; expiredAfterYield.clock.set(120_000_001_000L);
        expiredAfterYield.controller.onTick(11); unknown(expiredAfterYield, "original lease expiry after time-budget yield");
        check(expiredAfterYield.backend.preflight == beforeExpiry && !expiredAfterYield.backend.reserved, "time-budget yield does not renew the original lease");
        Rig quietMid = rig(); quietMid.backend.afterCell = () -> quietMid.backend.quiet = false;
        quietMid.controller.onTick(10); unknown(quietMid, "quiet state changes within tick");
        check(quietMid.backend.preflight == 1, "no second cell after newly scheduled/occupied state");
        Rig r = rig(); var first = r.controller.onTick(10);
        check(first.preflightCells() == 256 && r.backend.preflight == 256, "first tick inspects exactly 256 cells");
        check(r.backend.writes == 0 && !r.backend.reserved, "preflight cannot mutate or publish owner");
        int lastPreflight = 256, lastGeneration = 0, lastVerified = 0;
        for (long tick = 11; tick < 40 && r.controller.snapshot().phase() != KneekuraDebugTankRotationController.Phase.VERIFIED; tick++) {
            var s = r.controller.onTick(tick);
            check(s.preflightCells() - lastPreflight + s.generationCells() - lastGeneration + s.verifiedCells() - lastVerified <= 256, "all phase work shares one tick cell cap");
            lastPreflight = s.preflightCells(); lastGeneration = s.generationCells(); lastVerified = s.verifiedCells();
        }
        var done = r.controller.snapshot(); int allocated = NEXT.allocationCells();
        check(done.phase() == KneekuraDebugTankRotationController.Phase.VERIFIED && done.nextEpoch() == 3, "full verification increments source epoch");
        check(done.preflightCells() == allocated && done.generationCells() == allocated && done.verifiedCells() == allocated, "all three passes cover every allocated cell");
        check(r.backend.blocks.size() == allocated - NEXT.innerCells(), "only shell written once");
        check(r.backend.order.get(0).equals("reserve") && r.backend.order.get(r.backend.order.size() - 1).equals("publish"), "journal before mutation and publication after reread");
        int guards = r.backend.guards, writes = r.backend.writes;
        check(r.controller.onTick(40).equals(done) && r.controller.revoke("late").equals(done), "verified terminal cannot replay");
        check(r.backend.guards == guards && r.backend.writes == writes && r.backend.publications == 1, "terminal calls have no native effects");
        Set<KneekuraDebugTankRotationController.Cell> cells = new HashSet<>(); int interior = 0;
        for (int index = 0; index < allocated; index++) { var cell = NEXT.cell(index); check(cells.add(cell), "no duplicate allocation coordinate"); if (NEXT.inside(cell)) interior++; }
        check(interior == NEXT.innerCells(), "usable volume separate from shell");
        rejects(() -> NEXT.cell(-1), "negative cell"); rejects(() -> NEXT.cell(allocated), "cell beyond allocation");
        rejects(() -> new KneekuraDebugTankRotationController.Geometry(0, 224, 0, 65, 1, 1), "dimension cap");
        rejects(() -> new KneekuraDebugTankRotationController.Geometry(0, 224, 0, 64, 64, 64), "inner volume cap");
        rejects(() -> new KneekuraDebugTankRotationController.Geometry(Integer.MAX_VALUE, 224, 0, 1, 1, 1), "overflow world edge");
        rejects(() -> new KneekuraDebugTankRotationController.Geometry(0, -64, 0, 1, 1, 1), "floor shell build limit");
        rejects(() -> new KneekuraDebugTankRotationController.Geometry(0, 319, 0, 1, 1, 1), "ceiling shell build limit");
        rejects(() -> new KneekuraDebugTankRotationController.Plan(OLD, List.of(OLD), 1, 0, 1), "current region overlap");
        var adjacent = new KneekuraDebugTankRotationController.Geometry(20, 224, 0, 1, 1, 1);
        rejects(() -> new KneekuraDebugTankRotationController.Plan(adjacent, List.of(OLD), 1, 0, 1), "touching shell cell overlap");
        rejects(() -> new KneekuraDebugTankRotationController.Plan(NEXT, List.of(), 1, 0, 1), "missing predecessor");
        rejects(() -> new KneekuraDebugTankRotationController.Plan(NEXT, Collections.nCopies(17, OLD), 1, 0, 1), "reservation budget");
        rejects(() -> new KneekuraDebugTankRotationController.Plan(NEXT, List.of(OLD), 9007199254740991L, 0, 1), "epoch exhaustion");
        rejects(() -> new KneekuraDebugTankRotationController.Plan(NEXT, List.of(OLD), 1, 0, 120_000_000_001L), "no new extended lease");
        for (String fault : List.of("owner", "quiet", "expiry", "clock", "negativeTick")) {
            Rig f = rig(); if (fault.equals("owner")) f.backend.authorized = false;
            if (fault.equals("quiet")) f.backend.quiet = false;
            if (fault.equals("expiry")) f.clock.addAndGet(120_000_000_000L);
            if (fault.equals("clock")) f.clock.decrementAndGet();
            f.controller.onTick(fault.equals("negativeTick") ? -1 : 10); unknown(f, fault);
            check(f.backend.writes == 0 && f.backend.preflight == 0, fault + " stops before any cell");
        }
        Rig gap = rig(); gap.controller.onTick(10); gap.controller.onTick(12); unknown(gap, "server tick discontinuity");
        Rig repeat = rig(); repeat.controller.onTick(10); repeat.controller.onTick(10); unknown(repeat, "duplicate tick cannot spend twice");
        Rig mid = rig(); mid.backend.afterCell = () -> mid.backend.authorized = false; mid.controller.onTick(10); unknown(mid, "owner changes within tick"); check(mid.backend.preflight == 1, "no second cell after authority loss");
        Rig empty = rig(); empty.backend.blocks.put(NEXT.cell(0), "minecraft:stone"); finish(empty, 10); unknown(empty, "nonempty preflight"); check(empty.backend.writes == 0, "existing blocks not cleared");
        Rig reservation = rig(); reservation.backend.failReserve = true; finish(reservation, 10); unknown(reservation, "failed reservation"); check(reservation.backend.writes == 0, "no writes without durable reservation");
        Rig mutation = rig(); mutation.backend.failGenerate = true; finish(mutation, 10); unknown(mutation, "original write throws after mutation"); check(mutation.backend.writes == 1 && mutation.backend.unknowns == 1, "partial write retained with unknown receipt");
        int retained = mutation.backend.writes; finish(mutation, 100); check(mutation.backend.writes == retained, "partial apply never replayed");
        Rig readback = rig(); readback.backend.corruptReadback = true; finish(readback, 10); unknown(readback, "mismatched postcondition");
        Rig publish = rig(); publish.backend.failPublish = true; var ps = finish(publish, 10); check(ps.phase() == KneekuraDebugTankRotationController.Phase.OUTCOME_UNKNOWN && ps.unknownPersisted(), "failed durable publication remains unknown");
        Rig unknownFailure = rig(); unknownFailure.backend.failUnknown = true; unknownFailure.controller.revoke("shutdown"); check(!unknownFailure.controller.snapshot().unknownPersisted(), "unknown persistence failure not concealed");
        Rig cancel = rig(); cancel.controller.onTick(10); cancel.controller.revoke("shutdown"); unknown(cancel, "shutdown revokes finite generator"); check(cancel.backend.writes == 0, "shutdown does not start generation");
        Rig expiryAfter = rig(); expiryAfter.backend.afterCell = () -> expiryAfter.clock.addAndGet(120_000_000_000L);
        expiryAfter.controller.onTick(10); unknown(expiryAfter, "expiry after delegate"); check(expiryAfter.backend.preflight == 1, "no further delegate after expiry");
        Rig nested = rig(); nested.backend.afterCell = () -> nested.controller.onTick(10);
        nested.controller.onTick(10); unknown(nested, "reentrant original callback"); check(nested.backend.preflight == 1 && nested.backend.unknowns == 1, "reentrant callback cannot replay or publish two unknowns");
        System.out.println("Tank rotation state-machine checks passed: " + checks + "; no game process launched");
    }
}
