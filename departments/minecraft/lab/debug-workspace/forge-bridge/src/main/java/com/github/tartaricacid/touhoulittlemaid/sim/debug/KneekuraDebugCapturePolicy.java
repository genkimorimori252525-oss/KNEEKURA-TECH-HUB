package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.util.HashSet;
import java.util.Set;

/** Immutable visual intent installed by the Supervisor after reading the exact registered request.
 * Permission flags here are source-owner decisions; request flags cannot replace them. */
public record KneekuraDebugCapturePolicy(String requestHash, int generation, double fov,
        int width, int height, long maxDurationMs, boolean pauseAuthorized,
        boolean cameraTakeoverAuthorized, Set<String> behaviorAssertionIds) {
    public KneekuraDebugCapturePolicy {
        KneekuraDebugCaptureSession.hash(requestHash);
        behaviorAssertionIds = Set.copyOf(behaviorAssertionIds);
        if (generation < 1 || generation > 1_000_000 || !Double.isFinite(fov) || fov < 30 || fov > 100 ||
                width < 64 || width > 2048 || height < 64 || height > 2048 ||
                maxDurationMs < 100 || maxDurationMs > 5000 || behaviorAssertionIds.size() > 32)
            throw new IllegalArgumentException("INVALID_APPROVED_VISUAL_POLICY");
        behaviorAssertionIds.forEach(KneekuraDebugCaptureSession::id);
    }
    public void validate(KneekuraDebugCaptureSession.Request request) {
        if (!pauseAuthorized || !cameraTakeoverAuthorized || !request.allowPause() || !request.allowCameraTakeover() ||
                !requestHash.equals(request.identity().requestHash()) || generation != request.identity().generation() ||
                Double.compare(fov, request.fov()) != 0 || width != request.width() || height != request.height() ||
                request.totalBudgetMs() > maxDurationMs ||
                !behaviorAssertionIds.equals(new HashSet<>(request.behaviorAssertionIds())))
            throw new IllegalArgumentException("CAPTURE_DIFFERS_FROM_APPROVED_VISUAL_INTENT");
    }
}
