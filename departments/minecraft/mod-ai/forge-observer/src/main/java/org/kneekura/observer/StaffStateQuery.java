package org.kneekura.observer;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.UUID;

/** Narrow opt-in scope for the fixed staff scenario; no game access or writes. */
final class StaffStateQuery {
    private StaffStateQuery() {}

    static boolean enabled(JsonObject query) {
        if (!query.has("staff_state")) return false;
        JsonElement enabled = query.get("staff_state");
        require(enabled.isJsonPrimitive() && enabled.getAsJsonPrimitive().isBoolean(), "staff_state must be boolean");
        if (!enabled.getAsBoolean()) return false;
        JsonElement ids = query.get("entity_uuids"), dimension = query.get("dimension"), limit = query.get("limit");
        require(ids != null && ids.isJsonArray() && ids.getAsJsonArray().size() == 1,
                "Staff state requires exactly one explicit player UUID");
        JsonElement id = ids.getAsJsonArray().get(0);
        require(id.isJsonPrimitive() && id.getAsJsonPrimitive().isString(), "Player UUID must be a string");
        String uuid = id.getAsString();
        require(UUID.fromString(uuid).toString().equals(uuid), "Canonical player UUID required");
        require(dimension != null && dimension.isJsonPrimitive() && dimension.getAsJsonPrimitive().isString()
                        && dimension.getAsString().length() <= 256
                        && dimension.getAsString().matches("[a-z0-9_.-]+:[a-z0-9_/.-]+"),
                "Staff state requires an explicit dimension resource ID");
        require(limit != null && limit.isJsonPrimitive() && limit.getAsJsonPrimitive().isNumber()
                        && limit.getAsString().equals("1"), "Staff state requires integer entity limit 1");
        return true;
    }

    private static void require(boolean condition, String reason) {
        if (!condition) throw new IllegalArgumentException(reason);
    }
}
