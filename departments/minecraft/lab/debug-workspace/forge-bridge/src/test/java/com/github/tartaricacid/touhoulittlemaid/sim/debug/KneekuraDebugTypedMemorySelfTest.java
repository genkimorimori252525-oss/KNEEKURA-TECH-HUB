package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.behavior.BlockPosTracker;
import net.minecraft.world.entity.ai.behavior.EntityTracker;
import net.minecraft.world.entity.ai.behavior.PositionTracker;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.phys.Vec3;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Map;
import java.util.UUID;

/** Genuine cached fields, adversarial getters, bounded references and production Gson. */
public final class KneekuraDebugTypedMemorySelfTest {
    private static final class Subject extends Mob {
        private Subject() { super(null, null); }
        @Override public Vec3 position() { throw new AssertionError("ENTITY_POSITION_REPLAY"); }
        @Override public BlockPos blockPosition() { throw new AssertionError("ENTITY_BLOCK_REPLAY"); }
        @Override public UUID getUUID() { throw new AssertionError("ENTITY_UUID_REPLAY"); }
        @Override public String toString() { throw new AssertionError("ENTITY_STRING_REPLAY"); }
    }
    private static final class CustomTracker implements PositionTracker {
        @Override public Vec3 currentPosition() { throw new AssertionError("TRACKER_POSITION_REPLAY"); }
        @Override public BlockPos currentBlockPosition() { throw new AssertionError("TRACKER_BLOCK_REPLAY"); }
        @Override public boolean isVisibleBy(LivingEntity entity) { throw new AssertionError("TRACKER_VISIBILITY_REPLAY"); }
        @Override public String toString() { throw new AssertionError("TRACKER_STRING_REPLAY"); }
    }
    private static final class CustomWalk extends WalkTarget {
        CustomWalk() { super(new CustomTracker(), 1, 2); }
        @Override public PositionTracker getTarget() { throw new AssertionError("WALK_REPLAY"); }
        @Override public float getSpeedModifier() { throw new AssertionError("WALK_REPLAY"); }
        @Override public int getCloseEnoughDist() { throw new AssertionError("WALK_REPLAY"); }
    }
    private static final class CustomBlockTracker extends BlockPosTracker {
        CustomBlockTracker() { super(new BlockPos(0, 0, 0)); }
        @Override public Vec3 currentPosition() { throw new AssertionError("CUSTOM_BLOCK_REPLAY"); }
    }
    private static final class CustomPath extends Path {
        CustomPath() { super(new ArrayList<>(), new BlockPos(1, 2, 3), false); }
        @Override public int getNodeCount() { throw new AssertionError("PATH_REPLAY"); }
        @Override public boolean canReach() { throw new AssertionError("PATH_REPLAY"); }
    }
    private static final class CustomList extends ArrayList<Node> {
        boolean forbid;
        @Override public int size() { if (forbid) throw new AssertionError("LIST_REPLAY"); return super.size(); }
        @Override public Node get(int index) { if (forbid) throw new AssertionError("LIST_REPLAY"); return super.get(index); }
    }
    private static void set(Class<?> owner, String field, Object target, Object value) throws Exception {
        Field member = owner.getDeclaredField(field); member.setAccessible(true); member.set(target, value);
    }
    private static JsonObject data(JsonObject value) { return value.getAsJsonObject("data"); }
    private static String token(JsonObject value) { return data(value).getAsJsonObject("instanceIdentity").get("token").getAsString(); }
    private static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion(); net.minecraft.server.Bootstrap.bootStrap();
        var uf = sun.misc.Unsafe.class.getDeclaredField("theUnsafe"); uf.setAccessible(true);
        var unsafe = (sun.misc.Unsafe) uf.get(null);
        var observer = new KneekuraDebugDecisionSnapshot(); observer.reset(19);
        var tracker = new BlockPosTracker(new Vec3(1.25, 64.75, -2.5));
        var walk = new WalkTarget(tracker, .75F, 3);
        JsonObject encoded = observer.memoryValue(walk);
        require(encoded.has("encoding") && encoded.get("encoding").getAsString().equals("TYPED_CACHED_MEMORY_V1"), "exact WalkTarget cached fields must be exposed");
        require(data(encoded).get("speedModifier").getAsFloat() == .75F && data(encoded).get("closeEnoughDist").getAsInt() == 3, "cached walk parameters");
        JsonObject target = data(data(encoded).getAsJsonObject("target"));
        require(target.getAsJsonObject("position").get("x").getAsDouble() == 1.25 && target.getAsJsonObject("blockPosition").get("z").getAsInt() == -3, "direct Vec3 tracker retains position and containing block");
        var fraction = observer.memoryValue(new WalkTarget(new Vec3(1.25, 64.75, -2.5), 1, 0));
        require(data(data(fraction).getAsJsonObject("target")).getAsJsonObject("position").get("x").getAsDouble() == 1.5, "Vec3 WalkTarget constructor already reduced target to BlockPos center");
        require(token(encoded).equals(token(observer.memoryValue(walk))), "same reference stable");
        require(!token(encoded).equals(token(observer.memoryValue(new WalkTarget(tracker, .75F, 3)))), "equal target coordinates do not merge references");
        require(observer.memoryValue(new CustomWalk()).get("status").getAsString().equals("NOT_EXPOSED"), "custom WalkTarget remains unknown");
        require(observer.memoryValue(new CustomBlockTracker()).get("status").getAsString().equals("NOT_EXPOSED"), "custom BlockPosTracker remains unknown");
        require(observer.memoryValue(new WalkTarget(new CustomTracker(), 1, 2)).get("status").getAsString().equals("PARTIAL"), "custom tracker unknown without any dispatch");
        var entity = (Subject) unsafe.allocateInstance(Subject.class);
        set(Entity.class, "uuid", entity, new UUID(0, 41)); set(Entity.class, "position", entity, new Vec3(2.5, 65.5, 3.5));
        set(Entity.class, "blockPosition", entity, new BlockPos(2, 65, 3)); set(Entity.class, "eyeHeight", entity, 1.625F);
        var entityTracker = new EntityTracker(entity, true);
        JsonObject tracked = observer.memoryValue(entityTracker), entityCopy = data(tracked).getAsJsonObject("entity");
        require(data(tracked).get("trackEyeHeight").getAsBoolean(), "cached tracker policy");
        require(data(entityCopy).getAsJsonObject("eyeHeight").get("value").getAsFloat() == 1.625F, "cached eye height, not getter result");
        require(token(entityCopy).equals(token(observer.memoryValue(entity))), "attack memory and tracker share same scoped entity reference");
        set(Entity.class, "position", entity, new Vec3(9, 90, 9));
        require(data(entityCopy).getAsJsonObject("position").get("x").getAsDouble() == 2.5, "retained JSON detached from mutable entity");
        set(Entity.class, "position", entity, new Vec3(Double.NaN, 1, 2));
        require(observer.memoryValue(entity).get("status").getAsString().equals("PARTIAL"), "nonfinite cached position explicitly unavailable");
        set(Entity.class, "uuid", entity, null);
        require(data(observer.memoryValue(entity)).getAsJsonObject("entityUuid").get("status").getAsString().equals("NOT_EXPOSED"), "null cached UUID unknown");
        var nullTracker = new EntityTracker(entity, false); set(EntityTracker.class, "entity", nullTracker, null);
        require(observer.memoryValue(nullTracker).get("status").getAsString().equals("PARTIAL"), "null tracker entity unknown");
        var nonfiniteWalk = new WalkTarget(tracker, Float.NaN, 1);
        require(observer.memoryValue(nonfiniteWalk).get("status").getAsString().equals("PARTIAL"), "nonfinite speed unknown");
        var nodes = new ArrayList<Node>(); for (int i = 0; i < 70; i++) nodes.add(new Node(i, 64, 0));
        var path = new Path(nodes, new BlockPos(70, 64, 0), false); JsonObject route = observer.memoryValue(path);
        require(data(route).getAsJsonArray("nodes").size() == 64 && data(route).get("nodeCount").getAsInt() == 70 && route.get("status").getAsString().equals("PARTIAL"), "path retains bounded prefix and actual count");
        var navigation = (net.minecraft.world.entity.ai.navigation.GroundPathNavigation) unsafe.allocateInstance(net.minecraft.world.entity.ai.navigation.GroundPathNavigation.class);
        set(Mob.class, "navigation", entity, navigation); set(net.minecraft.world.entity.ai.navigation.PathNavigation.class, "path", navigation, path);
        var navigationMethod = KneekuraDebugDecisionSnapshot.class.getDeclaredMethod("navigation", Mob.class); navigationMethod.setAccessible(true);
        var navCopy = (JsonObject) navigationMethod.invoke(observer, entity);
        require(navCopy.getAsJsonObject("pathIdentity").get("token").getAsString().equals(token(route)), "memory and Navigation share actual Path reference in one allocator, not coordinate adoption");
        nodes.get(0).costMalus = 77; nodes.clear(); path.advance();
        require(data(route).getAsJsonArray("nodes").size() == 64 && data(route).get("nextNodeIndex").getAsInt() == 0, "Path copy detached from list/index mutations");
        require(observer.memoryValue(new CustomPath()).get("status").getAsString().equals("NOT_EXPOSED"), "custom Path never queried");
        var customList = new CustomList(); customList.add(new Node(1, 64, 0)); var listPath = new Path(customList, new BlockPos(1, 64, 0), false); customList.forbid = true;
        require(data(observer.memoryValue(listPath)).get("nodesStatus").getAsString().equals("NOT_EXPOSED"), "custom list not dispatched");
        set(net.minecraft.world.entity.ai.navigation.PathNavigation.class, "path", navigation, listPath);
        try { navigationMethod.invoke(observer, entity); throw new AssertionError("custom list Navigation should be unavailable"); }
        catch (java.lang.reflect.InvocationTargetException expected) { require(expected.getCause() instanceof IllegalStateException, "custom list receives no callback"); }
        @SuppressWarnings("unchecked") Map<String, Field> fields = (Map<String, Field>) get(KneekuraDebugDecisionSnapshot.class, "FIELDS", null);
        String key = WalkTarget.class.getName() + ":target"; Field original = fields.get(key);
        try { fields.put(key, Entity.class.getDeclaredField("position")); require(observer.memoryValue(walk).get("status").getAsString().equals("NOT_EXPOSED"), "member failure fails typed value closed"); }
        finally { fields.put(key, original); }
        observer.reset(20); require(!token(encoded).equals(token(observer.memoryValue(walk))), "reset changes reference scope");
        JsonObject stable = observer.memoryValue(path);
        for (int i = 0; i < 256; i++) observer.identity(new Object());
        JsonObject capped = observer.memoryValue(new BlockPosTracker(new BlockPos(0, 0, 0)));
        require(data(capped).getAsJsonObject("instanceIdentity").get("status").getAsString().equals("NOT_EXPOSED"), "shared reference cap declares unknown");
        require(token(stable).equals(token(observer.memoryValue(path))), "cap must not evict or rename known reference");
        var values = new JsonArray(); for (JsonObject v : new JsonObject[] {encoded, tracked, route, capped, observer.memoryValue(null), observer.memoryValue(new CustomTracker()), observer.memoryValue(nonfiniteWalk), observer.memoryValue(listPath)}) values.add(v);
        var hugeNodes = new ArrayList<Node>(); for (int i = 0; i < 64; i++) hugeNodes.add(new Node(i, 64, i));
        var hugePath = new Path(hugeNodes, new BlockPos(64, 64, 64), true);
        var brain = (net.minecraft.world.entity.ai.Brain<?>) unsafe.allocateInstance(net.minecraft.world.entity.ai.Brain.class);
        var memories = new java.util.HashMap<Object, Object>();
        net.minecraft.core.registries.BuiltInRegistries.MEMORY_MODULE_TYPE.stream().limit(70).forEach(k -> memories.put(k, java.util.Optional.of(net.minecraft.world.entity.ai.memory.ExpirableValue.of(hugePath))));
        require(memories.size() >= 64, "real registered-memory population required for byte bound");
        set(net.minecraft.world.entity.ai.Brain.class, "memories", brain, memories); set(LivingEntity.class, "brain", entity, brain);
        set(Mob.class, "goalSelector", entity, new net.minecraft.world.entity.ai.goal.GoalSelector(() -> net.minecraft.util.profiling.InactiveProfiler.INSTANCE));
        set(Mob.class, "targetSelector", entity, new net.minecraft.world.entity.ai.goal.GoalSelector(() -> net.minecraft.util.profiling.InactiveProfiler.INSTANCE));
        JsonObject bounded = observer.capture(entity);
        require(bounded.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length < 48 * 1024, "composite memories cannot escape existing snapshot byte cap");
        require(bounded.getAsJsonObject("sections").getAsJsonObject("brain_memory").get("detail").getAsString().equals("PAYLOAD_BYTE_BUDGET"), "large typed snapshots are unavailable, not claimed complete");
        System.out.println("MEMORY_INTEROP:" + new Gson().toJson(values));
        System.out.println("Actual typed memories: cached copies, no custom replay, finite facts, shared cap/reset and Gson unknowns");
    }
    private static Object get(Class<?> owner, String name, Object instance) throws Exception { Field f = owner.getDeclaredField(name); f.setAccessible(true); return f.get(instance); }
}
