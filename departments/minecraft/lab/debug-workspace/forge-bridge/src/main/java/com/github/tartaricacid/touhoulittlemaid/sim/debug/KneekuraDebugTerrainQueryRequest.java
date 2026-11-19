package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.math.BigDecimal;
import java.util.Set;

/** Optional finite ground query, separate from original-invocation burst channels. */
public record KneekuraDebugTerrainQueryRequest(int radius,int maxCells,int maxMillis) {
    public KneekuraDebugTerrainQueryRequest {
        if(radius<0||radius>3||maxCells<1||maxCells>49||maxMillis<1||maxMillis>50)
            throw new IllegalArgumentException("INVALID_TERRAIN_QUERY_LIMITS");
    }
    public static KneekuraDebugTerrainQueryRequest parse(JsonElement element) {
        if(element==null||element.isJsonNull())return null;
        if(!element.isJsonObject()||!element.getAsJsonObject().keySet().equals(Set.of("radius","maxCells","maxMillis")))
            throw new IllegalArgumentException("INVALID_TERRAIN_QUERY_FIELDS");
        JsonObject object=element.getAsJsonObject();
        return new KneekuraDebugTerrainQueryRequest(integer(object,"radius"),integer(object,"maxCells"),integer(object,"maxMillis"));
    }
    private static int integer(JsonObject object,String key) {
        JsonElement value=object.get(key);
        if(value==null||!value.isJsonPrimitive()||!value.getAsJsonPrimitive().isNumber())throw new IllegalArgumentException("INVALID_TERRAIN_QUERY_NUMBER");
        try{return new BigDecimal(value.getAsString()).intValueExact();}
        catch(ArithmeticException|NumberFormatException error){throw new IllegalArgumentException("INVALID_TERRAIN_QUERY_NUMBER",error);}
    }
}
