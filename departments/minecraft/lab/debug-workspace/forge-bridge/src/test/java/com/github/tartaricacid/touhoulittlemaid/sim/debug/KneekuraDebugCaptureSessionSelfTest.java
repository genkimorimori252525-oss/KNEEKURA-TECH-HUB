package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.util.List;
import java.util.UUID;

public final class KneekuraDebugCaptureSessionSelfTest {
    private static int checks;
    private static final String HASH = "a".repeat(64);
    private static KneekuraDebugCaptureSession.Request request() {
        return new KneekuraDebugCaptureSession.Request("capture-1",
                new KneekuraDebugCaptureSession.Identity("session", "run", "snapshot", 1,
                        "experiment", 1, HASH, "arena", 2, 3, HASH),
                List.of(UUID.fromString("00000000-0000-0000-0000-000000000001")),
                List.of("behavior-1"), List.of(0, 0, 0), List.of(16, 16, 16),
                70, 640, 480, 2000, 5000, true, true);
    }
    private static void check(boolean value, String message) {
        checks++;
        if (!value) throw new AssertionError(message);
    }
    private static void rejects(Runnable action) {
        checks++;
        try { action.run(); } catch (IllegalArgumentException | IllegalStateException expected) { return; }
        throw new AssertionError("expected rejection");
    }
    public static void main(String[] args) {
        var request = request();
        var session = new KneekuraDebugCaptureSession(request, 100);
        rejects(() -> session.frame("north", 1, HASH));
        session.acquire(101, 20, 30, HASH);
        for (int i = 0; i < 4; i++) {
            var view = KneekuraDebugCaptureSession.VIEWS.get(i);
            session.frame(view, i + 10, HASH);
            session.durable(view, HASH);
        }
        rejects(() -> session.frame("north", 20, HASH));
        session.restored(true);
        check(session.finish(200).status().equals("COMPLETE"), "four durable frames and restoration");
        check(!session.finish(200).sameFrame(), "sequential never same frame");
        check(session.finish(200).invalidatedAssertions().equals(List.of("behavior-1")), "behavior invalidation");
        var timeout = new KneekuraDebugCaptureSession(request, 100);
        timeout.acquire(101, 20, 30, HASH);
        timeout.frame("north", 10, HASH);
        timeout.restored(true);
        timeout.abort("DEADLINE_EXPIRED");
        timeout.durable("north", HASH);
        check(timeout.finish(6000).status().equals("PARTIAL"), "late acknowledgement cannot promote completion");
        check(timeout.finish(6000).frames().get(0).status().equals("WRITE_UNKNOWN"), "late PNG never silently adopted");
        check(timeout.finish(6000).frames().get(1).status().equals("MISSING"), "missing east explicit");
        var restore = new KneekuraDebugCaptureSession(request, 100);
        restore.restored(false);
        check(restore.finish(200).status().equals("UNKNOWN"), "restoration failure remains unknown");
        rejects(() -> new KneekuraDebugCaptureSession(request, -1));
        rejects(() -> session.acquire(102, 20, 30, HASH));
        var ordered = new KneekuraDebugCaptureSession(request, 100);
        ordered.acquire(101, 20, 30, HASH);
        rejects(() -> ordered.frame("east", 10, HASH));
        ordered.frame("north", 10, HASH);
        rejects(() -> ordered.frame("east", 10, HASH));
        check(request.pose("north").get(2) < 0, "north canonical");
        check(request.pose("east").get(0) > 16, "east canonical");
        check(request.pose("south").get(2) > 16, "south canonical");
        check(request.pose("west").get(0) < 0, "west canonical");
        System.out.println("capture session checks=" + checks);
    }
}
