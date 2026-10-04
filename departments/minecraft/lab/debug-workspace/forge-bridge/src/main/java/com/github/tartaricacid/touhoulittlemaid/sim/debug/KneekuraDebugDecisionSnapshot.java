package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ai.behavior.BlockPosTracker;
import net.minecraft.world.entity.ai.behavior.EntityTracker;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.control.JumpControl;
import net.minecraft.world.entity.ai.control.LookControl;
import net.minecraft.world.entity.ai.control.MoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.entity.ai.memory.ExpirableValue;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.schedule.Activity;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/**
 * Opt-in, exact-subject ANCHOR component snapshots. Reads cached fields only;
 * no eligibility, sensor, behavior, controller tick or path search is replayed.
 * Private members are a capability: an unavailable member fails its section
 * closed. Other versions require renewed source/runtime correspondence.
 */
public final class KneekuraDebugDecisionSnapshot {
    static final int MAX_ENTRIES = 64;
    private static final int MAX_IDENTITIES = 256;
    private static final Map<String, Field> FIELDS = new HashMap<>();
    private final IdentityHashMap<Object, String> identities = new IdentityHashMap<>();
    private long revision;
    private long nextIdentity;

    public void reset(long targetRevision) {
        revision = targetRevision;
        nextIdentity = 0;
        identities.clear();
    }

    public JsonObject capture(Mob mob) {
        JsonObject root = new JsonObject();
        root.addProperty("schema", "kneekura.vanilla-decision-snapshot/v1");
        root.addProperty("targetRevision", revision);
        root.addProperty("semantics", "MOB_COMPONENT_SNAPSHOT_ONLY");
        root.addProperty("entityClass", label(mob.getClass().getName()));
        JsonObject sections = new JsonObject();
        root.add("sections", sections);
        sections.add("goal_scheduler", section(() -> {
            JsonObject data = new JsonObject();
            data.add("goal", selector(mob.goalSelector));
            data.add("target", selector(mob.targetSelector));
            data.addProperty("eligibilityStatus", "NOT_EXPOSED");
            data.addProperty("lifecycleStatus", "SAMPLED_ONLY");
            data.addProperty("truncated", data.getAsJsonObject("goal").get("truncated").getAsBoolean()
                    || data.getAsJsonObject("target").get("truncated").getAsBoolean());
            return data;
        }));
        sections.add("brain_memory", section(() -> memories((Brain<?>) read(LivingEntity.class, "brain", mob))));
        sections.add("brain_activities", section(() -> activities((Brain<?>) read(LivingEntity.class, "brain", mob))));
        sections.add("navigation_path", section(() -> navigation(mob)));
        sections.add("movement_control", section(() -> controls(mob)));
        // Leave envelope/identity/cost headroom inside the writer's 64 KiB row.
        if (root.toString().getBytes(StandardCharsets.UTF_8).length > 48 * 1024) {
            for (String name : Set.of("goal_scheduler", "brain_memory", "brain_activities", "navigation_path", "movement_control")) {
                sections.add(name, unavailable("PAYLOAD_BYTE_BUDGET"));
            }
        }
        return root;
    }

    JsonObject selector(GoalSelector selector) throws ReflectiveOperationException {
        Set<?> registered = (Set<?>) read(GoalSelector.class, "availableGoals", selector);
        JsonObject out = new JsonObject();
        JsonArray entries = new JsonArray();
        out.add("entries", entries);
        int visited = 0;
        for (Object object : registered) {
            if (visited++ >= MAX_ENTRIES) break;
            WrappedGoal wrapper = (WrappedGoal) object;
            Goal goal = (Goal) read(WrappedGoal.class, "goal", wrapper);
            JsonObject row = new JsonObject();
            String token = identity(goal);
            row.addProperty("instanceIdentity", token);
            row.addProperty("instanceIdentityStatus", token == null ? "NOT_EXPOSED" : "AVAILABLE");
            row.addProperty("className", label(goal.getClass().getName()));
            row.addProperty("priority", (Integer) read(WrappedGoal.class, "priority", wrapper));
            row.addProperty("running", (Boolean) read(WrappedGoal.class, "isRunning", wrapper));
            JsonArray flags = new JsonArray();
            for (Object flag : (Set<?>) read(Goal.class, "flags", goal)) flags.add(((Goal.Flag) flag).name());
            row.add("flags", flags);
            entries.add(row);
        }
        out.addProperty("registeredCount", registered.size());
        out.addProperty("truncated", registered.size() > MAX_ENTRIES || identities.size() >= MAX_IDENTITIES);
        JsonArray disabled = new JsonArray();
        for (Object flag : (Set<?>) read(GoalSelector.class, "disabledFlags", selector)) disabled.add(((Goal.Flag) flag).name());
        out.add("disabledFlags", disabled);
        JsonArray owners = new JsonArray();
        for (Map.Entry<?, ?> entry : ((Map<?, ?>) read(GoalSelector.class, "lockedFlags", selector)).entrySet()) {
            if (owners.size() >= MAX_ENTRIES) break;
            JsonObject owner = new JsonObject();
            owner.addProperty("flag", ((Goal.Flag) entry.getKey()).name());
            owner.addProperty("instanceIdentity", identity(read(WrappedGoal.class, "goal", entry.getValue())));
            owners.add(owner);
        }
        out.add("flagOwners", owners);
        return out;
    }

    String identity(Object goal) { return identity(goal, "goal"); }

    private String identity(Object value, String namespace) {
        if (value == null) return null;
        String token = identities.get(value);
        if (token != null) return token;
        if (identities.size() >= MAX_IDENTITIES) return null;
        token = namespace + ":" + revision + ":" + (++nextIdentity);
        identities.put(value, token);
        return token;
    }

    private JsonObject memories(Brain<?> brain) throws ReflectiveOperationException {
        Map<?, ?> memories = (Map<?, ?>) read(Brain.class, "memories", brain);
        JsonObject out = new JsonObject();
        JsonArray entries = new JsonArray();
        out.add("entries", entries);
        for (Map.Entry<?, ?> entry : memories.entrySet()) {
            if (entries.size() >= MAX_ENTRIES) break;
            JsonObject row = new JsonObject();
            row.addProperty("key", String.valueOf(BuiltInRegistries.MEMORY_MODULE_TYPE.getKey((MemoryModuleType<?>) entry.getKey())));
            row.addProperty("registered", true);
            Optional<?> optional = (Optional<?>) entry.getValue();
            row.addProperty("present", optional.isPresent());
            if (optional.isPresent()) {
                ExpirableValue<?> value = (ExpirableValue<?>) optional.get();
                JsonObject expiry = expirableValue(value);
                row.add("canExpire", expiry.get("canExpire"));
                row.add("timeToLive", expiry.get("timeToLive"));
                row.add("value", expiry.get("value"));
            }
            entries.add(row);
        }
        out.addProperty("registeredCount", memories.size());
        out.addProperty("truncated", memories.size() > MAX_ENTRIES);
        out.addProperty("brainClass", label(brain.getClass().getName()));
        out.addProperty("activeTickMechanismStatus", "NOT_EXPOSED");
        return out;
    }

    JsonObject expirableValue(ExpirableValue<?> value) throws ReflectiveOperationException {
        JsonObject out = new JsonObject();
        long ttl = (Long) read(ExpirableValue.class, "timeToLive", value);
        out.addProperty("canExpire", ttl != Long.MAX_VALUE);
        out.addProperty("timeToLive", Long.toString(ttl));
        out.add("value", memoryValue(read(ExpirableValue.class, "value", value)));
        return out;
    }

    JsonObject memoryValue(Object value) {
        JsonObject out = new JsonObject();
        out.addProperty("className", value == null ? "null" : label(value.getClass().getName()));
        out.addProperty("status", "AVAILABLE");
        if (value == null) out.add("value", JsonNull.INSTANCE);
        else if (value instanceof Boolean b) out.addProperty("value", b);
        else if (value instanceof String s) {
            out.addProperty("value", label(s));
            if (s.length() > 512) out.addProperty("status", "PARTIAL");
        } else if (value instanceof UUID uuid) out.addProperty("value", uuid.toString());
        else if (value.getClass() == Long.class) {
            out.addProperty("value", Long.toString((Long) value));
            out.addProperty("encoding", "INT64_DECIMAL_STRING");
        } else if (value.getClass() == Integer.class || value.getClass() == Short.class
                || value.getClass() == Byte.class || value.getClass() == Float.class || value.getClass() == Double.class) {
            Number number = (Number) value;
            if (Double.isFinite(number.doubleValue())) out.addProperty("value", number);
            else out.addProperty("status", "NOT_EXPOSED");
        } else if (value.getClass() == BlockPos.class) {
            BlockPos pos = (BlockPos) value;
            out.addProperty("x", pos.getX()); out.addProperty("y", pos.getY()); out.addProperty("z", pos.getZ());
        } else if (value.getClass() == Vec3.class) {
            Vec3 pos = (Vec3) value;
            if (Double.isFinite(pos.x) && Double.isFinite(pos.y) && Double.isFinite(pos.z)) {
                out.addProperty("x", pos.x); out.addProperty("y", pos.y); out.addProperty("z", pos.z);
            } else return unavailable("NONFINITE_CACHED_POSITION");
        } else if (value.getClass() == WalkTarget.class || value.getClass() == BlockPosTracker.class
                || value.getClass() == EntityTracker.class || value instanceof Entity || value.getClass() == Path.class) {
            return typedMemory(value);
        } else out.addProperty("status", "NOT_EXPOSED");
        return out;
    }

    /** Same path namespace/256-reference budget as sampled memory, including opaque custom references. */
    JsonObject pathReferenceFact(Path path) {
        JsonObject out=new JsonObject();out.addProperty("present",path!=null);
        if(path==null)return out;
        out.addProperty("className",label(path.getClass().getName()));
        out.add("identity",reference(path,"path"));return out;
    }
    JsonObject pathFact(Path path) {
        JsonObject out=pathReferenceFact(path);
        if(path!=null)out.add("cachedFields",memoryValue(path));
        return out;
    }
    record CachedPathMemory(JsonObject data,Path path,boolean known) { }
    /** One known map slot and base wrapper fields; no Brain getter or custom map dispatch. */
    CachedPathMemory pathMemoryReference(Brain<?> brain) {
        try {
            Object object=read(Brain.class,"memories",brain);
            if(object==null||object.getClass()!=HashMap.class)
                return new CachedPathMemory(unavailable(object==null?"NULL_MEMORY_MAP":"CUSTOM_MEMORY_MAP"),null,false);
            Map<?,?> map=(Map<?,?>)object;boolean registered=map.containsKey(MemoryModuleType.PATH);
            Object entry=map.get(MemoryModuleType.PATH);JsonObject out=new JsonObject();
            out.addProperty("status","AVAILABLE");out.addProperty("registered",registered);
            if(!registered){out.addProperty("present",false);return new CachedPathMemory(out,null,true);}
            if(!(entry instanceof Optional<?> optional))return new CachedPathMemory(unavailable("UNEXPECTED_MEMORY_ENTRY"),null,false);
            out.addProperty("present",optional.isPresent());
            if(optional.isEmpty())return new CachedPathMemory(out,null,true);
            Object wrapper=optional.get();
            if(wrapper.getClass()!=ExpirableValue.class)return new CachedPathMemory(unavailable("CUSTOM_MEMORY_WRAPPER"),null,false);
            Object value=read(ExpirableValue.class,"value",wrapper);
            if(!(value instanceof Path path))return new CachedPathMemory(unavailable("NON_PATH_MEMORY_VALUE"),null,false);
            out.addProperty("timeToLive",Long.toString((Long)read(ExpirableValue.class,"timeToLive",wrapper)));
            out.add("path",pathReferenceFact(path));return new CachedPathMemory(out,path,true);
        }catch(ReflectiveOperationException|RuntimeException|LinkageError error){
            return new CachedPathMemory(unavailable("MEMBER_UNAVAILABLE:"+error.getClass().getSimpleName()),null,false);
        }
    }

    /** Same bounded allocator as Goals; these tokens never equal the Hooks component allocator. */
    private JsonObject reference(Object value, String namespace) {
        JsonObject out = new JsonObject();
        String token = identity(value, namespace);
        out.addProperty("status", token == null ? "NOT_EXPOSED" : "AVAILABLE");
        out.addProperty("allocator", "SNAPSHOT_REFERENCE");
        out.addProperty("targetRevision", revision);
        if (token == null) out.addProperty("detail", "REFERENCE_LIMIT");
        else out.addProperty("token", token);
        return out;
    }

    private JsonObject typedMemory(Object value) {
        try {
            JsonObject data = new JsonObject();
            String kind;
            if (value.getClass() == WalkTarget.class) {
                kind = "WALK_TARGET";
                data.add("instanceIdentity", reference(value, "memory"));
                float speed = (Float) read(WalkTarget.class, "speedModifier", value);
                if (Float.isFinite(speed)) data.addProperty("speedModifier", speed);
                else data.addProperty("speedModifierStatus", "NOT_EXPOSED");
                data.addProperty("closeEnoughDist", (Integer) read(WalkTarget.class, "closeEnoughDist", value));
                Object target = read(WalkTarget.class, "target", value);
                data.add("target", target == null ? unavailable("NULL_TRACKER") : memoryValue(target));
                data.addProperty("semantics", "CACHED_WALK_PARAMETERS_NOT_ELIGIBILITY_OR_NAVIGATION_RESULT");
            } else if (value.getClass() == BlockPosTracker.class) {
                kind = "BLOCK_POSITION_TRACKER";
                data.add("instanceIdentity", reference(value, "memory"));
                data.add("blockPosition", cachedMemory(read(BlockPosTracker.class, "blockPos", value), "NULL_CACHED_BLOCK_POSITION"));
                data.add("position", cachedMemory(read(BlockPosTracker.class, "centerPosition", value), "NULL_CACHED_POSITION"));
                data.addProperty("semantics", "CACHED_FIXED_TRACKER_FIELDS_NOT_VISIBILITY_QUERY");
            } else if (value.getClass() == EntityTracker.class) {
                kind = "ENTITY_TRACKER";
                data.add("instanceIdentity", reference(value, "memory"));
                data.addProperty("trackEyeHeight", (Boolean) read(EntityTracker.class, "trackEyeHeight", value));
                data.add("entity", cachedMemory(read(EntityTracker.class, "entity", value), "NULL_ENTITY"));
                data.addProperty("semantics", "CACHED_TRACKER_POLICY_NOT_CURRENT_POSITION_OR_VISIBILITY_QUERY");
            } else if (value instanceof Entity) {
                kind = "ENTITY_REFERENCE";
                data.add("instanceIdentity", reference(value, "entity"));
                data.add("entityUuid", cachedMemory(read(Entity.class, "uuid", value), "NULL_CACHED_UUID"));
                data.add("position", cachedMemory(read(Entity.class, "position", value), "NULL_CACHED_POSITION"));
                data.add("blockPosition", cachedMemory(read(Entity.class, "blockPosition", value), "NULL_CACHED_BLOCK_POSITION"));
                data.add("eyeHeight", memoryValue(read(Entity.class, "eyeHeight", value)));
                data.addProperty("semantics", "BASE_ENTITY_CACHED_FIELDS_ONLY_NOT_TRACKER_QUERY_OR_ACTUAL_MOTION");
            } else {
                kind = "PATH";
                data.add("instanceIdentity", reference(value, "path"));
                data.add("target", cachedMemory(read(Path.class, "target", value), "NULL_CACHED_TARGET"));
                data.addProperty("nextNodeIndex", (Integer) read(Path.class, "nextNodeIndex", value));
                data.addProperty("canReach", (Boolean) read(Path.class, "reached", value));
                data.add("distanceToTarget", memoryValue(read(Path.class, "distToTarget", value)));
                Object list = read(Path.class, "nodes", value);
                if (list == null || list.getClass() != ArrayList.class) {
                    data.addProperty("nodesStatus", "NOT_EXPOSED");
                    data.addProperty("nodesDetail", list == null ? "NULL_NODE_LIST" : "CUSTOM_NODE_LIST");
                } else {
                    ArrayList<?> nodes = (ArrayList<?>) list;
                    data.addProperty("nodeCount", nodes.size());
                    data.addProperty("truncated", nodes.size() > MAX_ENTRIES);
                    data.addProperty("nodesStatus", nodes.size() > MAX_ENTRIES ? "PARTIAL" : "AVAILABLE");
                    JsonArray entries = new JsonArray();
                    for (int i = 0; i < Math.min(nodes.size(), MAX_ENTRIES); i++) {
                        Object node = nodes.get(i);
                        if (node == null || node.getClass() != Node.class) {
                            entries.add(unavailable(node == null ? "NULL_NODE" : "CUSTOM_NODE_CLASS"));
                            continue;
                        }
                        Node cached = (Node) node;
                        JsonObject row = new JsonObject();
                        row.addProperty("status", "AVAILABLE");
                        row.addProperty("x", cached.x); row.addProperty("y", cached.y); row.addProperty("z", cached.z);
                        if (cached.type != null) row.addProperty("type", cached.type.name());
                        else row.addProperty("status", "PARTIAL");
                        if (Float.isFinite(cached.costMalus)) row.addProperty("costMalus", cached.costMalus);
                        else row.addProperty("status", "PARTIAL");
                        entries.add(row);
                    }
                    data.add("nodes", entries);
                }
                data.addProperty("semantics", "CACHED_MEMORY_ROUTE_NOT_ADOPTION_ACTUAL_MOTION_OR_SEARCH_FRONTIER");
            }
            JsonObject out = new JsonObject();
            out.addProperty("status", incomplete(data) ? "PARTIAL" : "AVAILABLE");
            out.addProperty("className", label(value.getClass().getName()));
            out.addProperty("encoding", "TYPED_CACHED_MEMORY_V1");
            out.addProperty("kind", kind);
            out.add("data", data);
            return out;
        } catch (ReflectiveOperationException | RuntimeException error) {
            return unavailable("MEMBER_UNAVAILABLE:" + error.getClass().getSimpleName());
        }
    }

    private JsonObject cachedMemory(Object value, String nullReason) {
        return value == null ? unavailable(nullReason) : memoryValue(value);
    }

    private static boolean incomplete(com.google.gson.JsonElement value) {
        if (value.isJsonObject()) {
            for (Map.Entry<String, com.google.gson.JsonElement> entry : value.getAsJsonObject().entrySet()) {
                if ((entry.getKey().equals("status") || entry.getKey().endsWith("Status"))
                        && !entry.getValue().getAsString().equals("AVAILABLE")) return true;
                if (entry.getKey().equals("truncated") && entry.getValue().getAsBoolean()) return true;
                if (incomplete(entry.getValue())) return true;
            }
        } else if (value.isJsonArray()) {
            for (com.google.gson.JsonElement child : value.getAsJsonArray()) if (incomplete(child)) return true;
        }
        return false;
    }

    private JsonObject activities(Brain<?> brain) throws ReflectiveOperationException {
        JsonObject out = new JsonObject();
        boolean truncated = false;
        for (String field : Set.of("activeActivities", "coreActivities")) {
            Set<?> set = (Set<?>) read(Brain.class, field, brain);
            JsonArray names = new JsonArray();
            for (Object activity : set) {
                if (names.size() >= MAX_ENTRIES) break;
                names.add(String.valueOf(BuiltInRegistries.ACTIVITY.getKey((Activity) activity)));
            }
            out.add(field, names);
            truncated |= set.size() > MAX_ENTRIES;
        }
        out.addProperty("defaultActivity", String.valueOf(BuiltInRegistries.ACTIVITY.getKey((Activity) read(Brain.class, "defaultActivity", brain))));
        out.addProperty("behaviorEligibilityStatus", "NOT_EXPOSED");
        out.addProperty("truncated", truncated);
        return out;
    }

    private JsonObject navigation(Mob mob) throws ReflectiveOperationException {
        PathNavigation navigation = (PathNavigation) read(Mob.class, "navigation", mob);
        Path path = (Path) read(PathNavigation.class, "path", navigation);
        JsonObject out = new JsonObject();
        out.addProperty("className", label(navigation.getClass().getName()));
        out.addProperty("pathPresent", path != null);
        out.addProperty("pathSemantics", "DECLARED_ROUTE_NOT_ACTUAL_MOTION_OR_FRONTIER");
        out.addProperty("truncated", false);
        if (path == null) return out;
        JsonObject memory = memoryValue(path);
        if (!memory.has("encoding")) throw new IllegalStateException("CUSTOM_PATH_NOT_EXPOSED");
        JsonObject cached = memory.getAsJsonObject("data");
        if (cached.get("nodesStatus").getAsString().equals("NOT_EXPOSED")) throw new IllegalStateException("NODE_LIST_NOT_EXPOSED");
        JsonObject target = cached.getAsJsonObject("target");
        if (!target.get("status").getAsString().equals("AVAILABLE")) throw new IllegalStateException("PATH_TARGET_NOT_EXPOSED");
        out.add("pathIdentity", cached.get("instanceIdentity"));
        out.add("nodeCount", cached.get("nodeCount"));
        out.add("nextNodeIndex", cached.get("nextNodeIndex"));
        out.add("canReach", cached.get("canReach"));
        out.add("targetX", target.get("x")); out.add("targetY", target.get("y")); out.add("targetZ", target.get("z"));
        JsonArray entries = new JsonArray();
        int index = 0;
        for (com.google.gson.JsonElement element : cached.getAsJsonArray("nodes")) {
            JsonObject node = element.getAsJsonObject();
            if (!node.get("status").getAsString().equals("AVAILABLE")) throw new IllegalStateException("PATH_NODE_NOT_EXPOSED");
            JsonObject row = new JsonObject();
            row.addProperty("index", index++);
            for (String key : Set.of("x", "y", "z", "type", "costMalus")) row.add(key, node.get(key));
            entries.add(row);
        }
        out.add("entries", entries);
        out.add("truncated", cached.get("truncated"));
        return out;
    }

    JsonObject controls(Mob mob) throws ReflectiveOperationException {
        JsonObject out = new JsonObject();
        for (String kind : Set.of("move", "look", "jump")) {
            Class<?> owner = kind.equals("move") ? MoveControl.class : kind.equals("look") ? LookControl.class : JumpControl.class;
            Object control = read(Mob.class, kind + "Control", mob);
            JsonObject row = new JsonObject();
            row.addProperty("className", label(control.getClass().getName()));
            row.addProperty("fieldScope", "BASE_CONTROL_FIELDS_ONLY");
            if (kind.equals("jump")) row.addProperty("jumpRequested", (Boolean) read(owner, "jump", control));
            else {
                for (String name : Set.of("wantedX", "wantedY", "wantedZ")) row.addProperty(name, (Double) read(owner, name, control));
                if (kind.equals("move")) {
                    row.addProperty("speedModifier", (Double) read(owner, "speedModifier", control));
                    row.addProperty("operation", ((Enum<?>) read(owner, "operation", control)).name());
                } else row.addProperty("lookAtCooldown", (Integer) read(owner, "lookAtCooldown", control));
            }
            out.add(kind, row);
        }
        return out;
    }

    static synchronized Object read(Class<?> owner, String name, Object instance) throws ReflectiveOperationException {
        String key = owner.getName() + ":" + name;
        Field field = FIELDS.get(key);
        if (field == null) {
            field = owner.getDeclaredField(name);
            if (!field.trySetAccessible()) throw new IllegalAccessException(key);
            FIELDS.put(key, field);
        }
        return field.get(instance);
    }

    private interface Capture { JsonObject read() throws ReflectiveOperationException; }

    private static JsonObject section(Capture capture) {
        try {
            JsonObject data = capture.read();
            JsonObject out = new JsonObject();
            out.addProperty("status", data.has("truncated") && data.get("truncated").getAsBoolean() ? "PARTIAL" : "AVAILABLE");
            out.add("data", data);
            return out;
        } catch (ReflectiveOperationException | RuntimeException error) {
            return unavailable("MEMBER_UNAVAILABLE:" + error.getClass().getSimpleName());
        }
    }

    private static JsonObject unavailable(String reason) {
        JsonObject out = new JsonObject();
        out.addProperty("status", "NOT_EXPOSED");
        out.addProperty("detail", reason);
        return out;
    }

    private static String label(String value) { return value.length() <= 512 ? value : value.substring(0, 512); }
}
