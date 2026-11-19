package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public final class KneekuraDebugCaptureBarrierSelfTest {
    public static void main(String[] args) throws Exception {
        var barrier = new KneekuraDebugCaptureBarrier<String>();
        Thread owner = new Thread(() -> barrier.hold(() -> "state", 1000));
        owner.start();
        if (!barrier.ready().get(1, TimeUnit.SECONDS).equals("state") || !barrier.isHeld()) throw new AssertionError("not held");
        barrier.release(); owner.join(1000);
        if (owner.isAlive() || barrier.isHeld() || barrier.expired()) throw new AssertionError("not released");
        var late = new KneekuraDebugCaptureBarrier<String>();
        AtomicBoolean called = new AtomicBoolean(); late.release();
        late.hold(() -> { called.set(true); return "late"; }, 100);
        if (called.get() || !late.ready().isCompletedExceptionally()) throw new AssertionError("late server task executed");
        var timeout = new KneekuraDebugCaptureBarrier<String>();
        Thread timed = new Thread(() -> timeout.hold(() -> "state", 20)); timed.start(); timed.join(1000);
        if (timed.isAlive() || !timeout.expired() || timeout.isHeld()) throw new AssertionError("barrier not bounded");
        System.out.println("capture barrier checks=5");
    }
}
