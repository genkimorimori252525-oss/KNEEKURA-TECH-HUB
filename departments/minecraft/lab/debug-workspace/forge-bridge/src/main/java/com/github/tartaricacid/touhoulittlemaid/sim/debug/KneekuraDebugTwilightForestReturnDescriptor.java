package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

/** Separate contract from cached snapshots; the same exact resource proof is required. */
final class KneekuraDebugTwilightForestReturnDescriptor {
    private KneekuraDebugTwilightForestReturnDescriptor() { }
    static JsonObject descriptor() {
        JsonObject out=KneekuraDebugTwilightForestDescriptor.descriptor();
        out.addProperty("id","twilightforest:boss-original-return");
        out.addProperty("instrumentation","ORIGINAL_METHOD_RETURN_AND_CACHED_POST_STATE");
        out.addProperty("observerEffectRisk","BOUNDED_ORIGINAL_CALLBACK_WITH_ONCE_SOURCE_IO");
        JsonArray levels=new JsonArray();levels.add("DIRECT_OBSERVED");levels.add("DERIVED_FROM_OBSERVED");
        out.add("supportedEpistemicLevels",levels);return out;
    }
}
