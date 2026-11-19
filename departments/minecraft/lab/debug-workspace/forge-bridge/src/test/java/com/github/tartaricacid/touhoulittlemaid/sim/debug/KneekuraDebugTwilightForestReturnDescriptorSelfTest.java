package com.github.tartaricacid.touhoulittlemaid.sim.debug;

public final class KneekuraDebugTwilightForestReturnDescriptorSelfTest {
    public static void main(String[] args) {
        var cached=KneekuraDebugTwilightForestDescriptor.descriptor();
        var returned=KneekuraDebugTwilightForestReturnDescriptor.descriptor();
        if(cached.get("id").equals(returned.get("id"))||!returned.get("id").getAsString().equals("twilightforest:boss-original-return")||
            !cached.get("mappedArtifactSha256").equals(returned.get("mappedArtifactSha256"))||
            !cached.get("classHashes").equals(returned.get("classHashes"))||
            !returned.getAsJsonArray("supportedEpistemicLevels").get(0).getAsString().equals("DIRECT_OBSERVED"))throw new AssertionError("TF source/generation separation");
        returned.getAsJsonObject("classHashes").remove("twilightforest.entity.boss.Hydra");
        if(KneekuraDebugTwilightForestReturnDescriptor.descriptor().getAsJsonObject("classHashes").size()!=10)throw new AssertionError("mutable descriptor cache");
        System.out.println("TF return descriptor: exact snapshot source, distinct instrumentation, immutable regenerated metadata");
    }
}
