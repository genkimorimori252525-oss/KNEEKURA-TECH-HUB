package com.github.tartaricacid.touhoulittlemaid.sim.debug;

/** CPU contract checks; real render-event and restoration verification remain native gates. */
public final class KneekuraDebugCaptureClockSelfTest {
    private static int checks;
    private static final class PausedClient { private float pausePartialTick = .82f; }
    private static final class SrgClient { private float f_91013_ = .24f; }
    private static final class WrongClient { private double pausePartialTick; }
    private static final class FinalClient { private final float pausePartialTick = .2f; }
    private static final class ForgeClient { private float pausePartialTick = .82f; private float realPartialTick = .82f; }
    private static void check(boolean ok) { if (!ok) throw new AssertionError("clock check " + checks); checks++; }
    private static void rejects(Runnable op) { boolean failed = false; try { op.run(); } catch (RuntimeException expected) { failed = true; } check(failed); }
    public static void main(String[] args) {
        var client = new PausedClient();
        var access = KneekuraDebugCaptureClock.field(client, PausedClient.class);
        var clock = new KneekuraDebugCaptureClock(access, () -> true);
        clock.acquire(); check(client.pausePartialTick == 0); check(clock.frozen());
        rejects(clock::acquire); check(clock.restore()); check(client.pausePartialTick == .82f);
        check(clock.restore()); check(!clock.frozen()); rejects(clock::acquire);
        var srg = new SrgClient(); var mapped = new KneekuraDebugCaptureClock(KneekuraDebugCaptureClock.field(srg, SrgClient.class), () -> true);
        mapped.acquire(); check(srg.f_91013_ == 0); check(mapped.restore()); check(srg.f_91013_ == .24f);
        rejects(() -> KneekuraDebugCaptureClock.field(new WrongClient(), WrongClient.class));
        rejects(() -> KneekuraDebugCaptureClock.field(new FinalClient(), FinalClient.class));
        var unpaused = new KneekuraDebugCaptureClock(access, () -> false);
        rejects(unpaused::acquire); check(client.pausePartialTick == .82f); check(unpaused.restore());
        for (float value : new float[]{Float.NaN, Float.POSITIVE_INFINITY, -.1f, 1.1f}) {
            client.pausePartialTick = value;
            var invalid = new KneekuraDebugCaptureClock(access, () -> true);
            rejects(invalid::acquire); check(Float.floatToRawIntBits(client.pausePartialTick) == Float.floatToRawIntBits(value));
        }
        client.pausePartialTick = .6f;
        var drift = new KneekuraDebugCaptureClock(access, () -> true);
        drift.acquire(); client.pausePartialTick = .3f; check(!drift.frozen()); check(drift.restore()); check(client.pausePartialTick == .6f);
        var failingAccess = new KneekuraDebugCaptureClock.Access() {
            private float value = .7f;
            public float read() { return value; }
            public void write(float next) { if (next != 0) throw new IllegalStateException("restore failure"); value = next; }
        };
        var failedRestore = new KneekuraDebugCaptureClock(failingAccess, () -> true);
        failedRestore.acquire(); check(!failedRestore.restore()); check(!failedRestore.restore());
        var lostPause = new boolean[]{true};
        var lost = new KneekuraDebugCaptureClock(access, () -> lostPause[0]);
        lost.acquire(); lostPause[0] = false; check(!lost.frozen()); check(lost.restore());
        var forge = new ForgeClient();
        var paired = new KneekuraDebugCaptureClock(() -> true,
                KneekuraDebugCaptureClock.field(forge, ForgeClient.class),
                KneekuraDebugCaptureClock.eventField(forge, ForgeClient.class));
        paired.acquire(); check(forge.pausePartialTick == 0); check(forge.realPartialTick == 0); check(paired.frozen());
        forge.realPartialTick = .3f; check(!paired.frozen()); check(paired.restore());
        check(forge.pausePartialTick == .82f); check(forge.realPartialTick == .82f);
        System.out.println("capture interpolation clock checks=" + checks + "; native renderer NOT_RUN");
    }
}
