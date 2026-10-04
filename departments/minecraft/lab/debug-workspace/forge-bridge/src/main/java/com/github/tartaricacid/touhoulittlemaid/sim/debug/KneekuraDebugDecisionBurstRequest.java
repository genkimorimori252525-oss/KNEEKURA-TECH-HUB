package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;

/** Strict optional observation request. This cannot authorize a world action or enable launch hooks. */
public record KneekuraDebugDecisionBurstRequest(int ticks, int maxEvents, int maxBytes,
                                               int maxNodes, Set<String> channels) {
    private static final Set<String> CHANNELS=Set.of("goal","brain","path","control","malus","sensor","mod","projectile","neighbors","effective_malus","frontier","path_nodes");
    public KneekuraDebugDecisionBurstRequest {
        if(ticks<1||ticks>200||maxEvents<1||maxEvents>256||maxBytes<1||maxBytes>524288
                ||maxNodes<1||maxNodes>64||channels==null||channels.isEmpty()
                ||!CHANNELS.containsAll(channels))throw new IllegalArgumentException("INVALID_DECISION_BURST");
        channels=Set.copyOf(channels);
    }
    public static KneekuraDebugDecisionBurstRequest parse(JsonElement value) {
        if(value==null||value.isJsonNull())return null;
        if(!value.isJsonObject())throw new IllegalArgumentException("INVALID_DECISION_BURST");
        JsonObject object=value.getAsJsonObject();
        if(!object.keySet().equals(Set.of("ticks","maxEvents","maxBytes","maxNodes","channels")))
            throw new IllegalArgumentException("INVALID_DECISION_BURST_FIELDS");
        JsonElement list=object.get("channels");
        if(!list.isJsonArray()||list.getAsJsonArray().isEmpty()||list.getAsJsonArray().size()>CHANNELS.size())
            throw new IllegalArgumentException("INVALID_DECISION_BURST_CHANNELS");
        Set<String> channels=new HashSet<>();
        for(JsonElement item:list.getAsJsonArray()) {
            if(!item.isJsonPrimitive()||!item.getAsJsonPrimitive().isString()
                    ||!channels.add(item.getAsString()))throw new IllegalArgumentException("INVALID_DECISION_BURST_CHANNELS");
        }
        return new KneekuraDebugDecisionBurstRequest(integer(object,"ticks"),integer(object,"maxEvents"),
                integer(object,"maxBytes"),integer(object,"maxNodes"),channels);
    }
    private static int integer(JsonObject object,String key) {
        JsonElement value=object.get(key);
        if(!value.isJsonPrimitive()||!value.getAsJsonPrimitive().isNumber())
            throw new IllegalArgumentException("INVALID_DECISION_BURST_NUMBER");
        try{return new BigDecimal(value.getAsString()).intValueExact();}
        catch(ArithmeticException|NumberFormatException error){throw new IllegalArgumentException("INVALID_DECISION_BURST_NUMBER",error);}
    }
}
