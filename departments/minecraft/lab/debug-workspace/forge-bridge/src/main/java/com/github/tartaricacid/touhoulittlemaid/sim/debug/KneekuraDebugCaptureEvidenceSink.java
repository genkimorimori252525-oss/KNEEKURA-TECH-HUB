package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.JsonObject;
import java.util.concurrent.CompletableFuture;
/** Explicit adapter to the existing raw evidence worker. No additional worker or database. */
public final class KneekuraDebugCaptureEvidenceSink implements KneekuraDebugCardinalCapture.EvidenceSink {
    public CompletableFuture<String> frame(KneekuraDebugEnv.Config config,long epoch,long tick,Long gameTime,byte[] png,JsonObject metadata) {
        return KneekuraDebugEvidenceWriter.recordVisualObservedAsync(config,epoch,tick,gameTime,png,metadata);
    }
    public CompletableFuture<String> manifest(KneekuraDebugEnv.Config config,long epoch,long tick,Long gameTime,JsonObject metadata) {
        return KneekuraDebugEvidenceWriter.recordVisualObservedAsync(config,epoch,tick,gameTime,null,metadata);
    }
}
