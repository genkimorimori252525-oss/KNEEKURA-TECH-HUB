package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.world.entity.Mob;

/**
 * SDK v1 producer half. Explicit trusted registration only; no owner/action authority is supplied.
 * Implementations declare exact source compatibility and read cached state without replaying AI.
 * Retained emitStructuredFacts/emitVisualPrimitives live in the Node SDK after writer IDs exist.
 */
public interface KneekuraDebugDecisionAdapter {
    record Limits(int maxEntries,int maxBytes) {
        public Limits {
            if(maxEntries<1||maxEntries>64||maxBytes<1024||maxBytes>32768)throw new IllegalArgumentException("INVALID_ADAPTER_LIMITS");
        }
    }
    JsonObject descriptor();
    boolean supports(Mob entity);
    JsonObject describeCapabilities();
    JsonObject captureSnapshot(Mob entity,KneekuraDebugDecisionBurstBudget.Context context,Limits limits)throws Exception;
    /** An unsupported channel cannot be implemented by rerunning decision methods. */
    default JsonObject captureBurst(Mob entity,KneekuraDebugDecisionBurstBudget.Context context,KneekuraDebugDecisionBurstRequest request) {
        JsonObject unavailable=new JsonObject();unavailable.addProperty("status","NOT_EXPOSED");
        unavailable.addProperty("detail","ORIGINAL_INVOCATION_MOD_BURST_NOT_REGISTERED");return unavailable;
    }
}
