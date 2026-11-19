package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Supplier;

/** Bounded rendezvous on an existing server owner task. Owns no thread or scheduler. */
public final class KneekuraDebugCaptureBarrier<T> {
    private final CompletableFuture<T> ready = new CompletableFuture<>();
    private final CountDownLatch release = new CountDownLatch(1);
    private final AtomicBoolean entered = new AtomicBoolean();
    private volatile boolean held;
    private volatile boolean expired;
    private volatile long heldAt;
    private volatile long releasedAt;
    public CompletableFuture<T> ready() { return ready; }
    public boolean isHeld() { return held; }
    public boolean expired() { return expired; }
    public long durationMs() {
        if (heldAt == 0) return 0;
        return TimeUnit.NANOSECONDS.toMillis(Math.max(0, (releasedAt == 0 ? System.nanoTime() : releasedAt) - heldAt));
    }
    public void release() { release.countDown(); }
    public void hold(Supplier<T> snapshot, long budgetMs) {
        if (budgetMs < 1 || budgetMs > 2000 || !entered.compareAndSet(false, true))
            throw new IllegalArgumentException("INVALID_BARRIER_ATTEMPT");
        try {
            if (release.getCount() == 0) throw new IllegalStateException("BARRIER_ALREADY_RELEASED");
            T state = snapshot.get();
            if (release.getCount() == 0) throw new IllegalStateException("BARRIER_ALREADY_RELEASED");
            heldAt = System.nanoTime();
            held = true;
            ready.complete(state);
            if (!release.await(budgetMs, TimeUnit.MILLISECONDS)) expired = true;
        } catch (Throwable error) {
            expired = true;
            ready.completeExceptionally(error);
            if (error instanceof InterruptedException) Thread.currentThread().interrupt();
        } finally { releasedAt = System.nanoTime(); held = false; }
    }
}
