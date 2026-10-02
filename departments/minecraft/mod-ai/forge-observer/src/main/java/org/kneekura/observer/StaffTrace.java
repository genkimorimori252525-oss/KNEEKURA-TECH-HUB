package org.kneekura.observer;

import com.google.gson.*;
import java.lang.reflect.Modifier;
import java.util.Map;
import java.util.Set;

/** Fixed read-only helper lookup, called only after all session class probes verified. */
final class StaffTrace {
    private static final String RESOURCE="org/kneekura/staff/ClientUseTrace.class";
    private static final Gson JSON=new GsonBuilder().serializeNulls().create();
    private StaffTrace() {}
    static boolean enabled(JsonObject verifiedSession) {
        JsonArray probes=verifiedSession.getAsJsonArray("class_probes");if(probes==null)return false;
        for(JsonElement e:probes)if(e.isJsonObject() && e.getAsJsonObject().has("resource")
                && RESOURCE.equals(e.getAsJsonObject().get("resource").getAsString()))return true;
        return false;
    }
    static JsonObject unavailable(boolean supported,String reason) {
        JsonObject out=new JsonObject();out.addProperty("schema_version",1);out.addProperty("supported",supported);
        out.addProperty("status",supported?"UNKNOWN":"UNSUPPORTED");out.addProperty("reason",reason);return out;
    }
    static JsonObject capture(JsonObject verifiedSession) {
        if(!enabled(verifiedSession))return unavailable(false,"Fixed staff instrumentation class is absent from verified build probes");
        try {
            Class<?> helper=Class.forName("org.kneekura.staff.ClientUseTrace",false,StaffTrace.class.getClassLoader());
            var method=helper.getMethod("snapshot");
            DedicatedSession.require(Modifier.isStatic(method.getModifiers()) && Map.class.isAssignableFrom(method.getReturnType()),"Invalid fixed helper signature");
            Object value=method.invoke(null);DedicatedSession.require(value instanceof Map,"Missing fixed helper snapshot");
            JsonObject out=JSON.toJsonTree(value).getAsJsonObject();
            DedicatedSession.require(out.keySet().equals(Set.of("schema_version","limit","started","completed","unknown","dropped","records")),"Invalid fixed helper fields");
            DedicatedSession.integer(out,"schema_version",1,1);DedicatedSession.integer(out,"limit",16,16);
            for(String key:Set.of("started","completed","unknown","dropped")) {
                JsonElement count=out.get(key);
                DedicatedSession.require(count.isJsonPrimitive() && count.getAsJsonPrimitive().isNumber() && count.getAsString().matches("0|[1-9][0-9]*"),"Invalid helper counter");
                DedicatedSession.require(Long.parseLong(count.getAsString())>=0,"Invalid helper counter");
            }
            DedicatedSession.require(out.get("records").isJsonArray() && out.getAsJsonArray("records").size()<=16,"Unbounded helper records");
            DedicatedSession.require(JSON.toJson(out).length()<=65536,"Helper snapshot exceeds fixed budget");
            out.addProperty("supported",true);out.addProperty("status","CAPTURED");return out;
        } catch(Exception | LinkageError unavailable) {return unavailable(true,"Fixed verified helper snapshot unavailable or malformed");}
    }
}
