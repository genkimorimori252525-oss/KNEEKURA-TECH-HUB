package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.util.profiling.InactiveProfiler;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.entity.ai.memory.ExpirableValue;

import java.util.EnumSet;

/** Uses actual ANCHOR classes, not substitutes for Minecraft APIs. */
public final class KneekuraDebugDecisionSnapshotSelfTest {
    private static final class StatefulGoal extends Goal {
        StatefulGoal() { setFlags(EnumSet.of(Flag.MOVE)); }
        @Override public boolean canUse() { throw new AssertionError("observer replayed canUse"); }
        @Override public boolean canContinueToUse() { throw new AssertionError("observer replayed continuation"); }
        @Override public void start() { throw new AssertionError("observer started goal"); }
        @Override public void stop() { throw new AssertionError("observer stopped goal"); }
        @Override public void tick() { throw new AssertionError("observer ticked goal"); }
        @Override public EnumSet<Flag> getFlags() { throw new AssertionError("observer invoked custom getter"); }
        @Override public String toString() { throw new AssertionError("observer invoked toString"); }
    }

    public static void main(String[] args) throws Exception {
        GoalSelector selector = new GoalSelector(() -> InactiveProfiler.INSTANCE);
        for (int i = 0; i < 70; i++) selector.addGoal(i, new StatefulGoal());
        KneekuraDebugDecisionSnapshot snapshot = new KneekuraDebugDecisionSnapshot();
        snapshot.reset(7);
        JsonObject first = snapshot.selector(selector);
        require(first.getAsJsonArray("entries").size() == 64, "must bound registered goals");
        require(first.get("truncated").getAsBoolean(), "must declare truncation");
        require(selector.getAvailableGoals().size() == 70, "must not change selector");
        require(selector.getAvailableGoals().stream().noneMatch(WrappedGoal::isRunning), "must not change running state");
        JsonObject row = first.getAsJsonArray("entries").get(0).getAsJsonObject();
        String token = row.get("instanceIdentity").getAsString();
        require(token.startsWith("goal:7:"), "instance identity must fence target revision");
        require(row.getAsJsonArray("flags").get(0).getAsString().equals("MOVE"), "read cached flags without callback");
        require(token.equals(snapshot.selector(selector).getAsJsonArray("entries").get(0)
                .getAsJsonObject().get("instanceIdentity").getAsString()), "same instance stays stable");
        snapshot.reset(8);
        require(!token.equals(snapshot.selector(selector).getAsJsonArray("entries").get(0)
                .getAsJsonObject().get("instanceIdentity").getAsString()), "reselection must change identity");
        Object opaque = new Object() {
            @Override public String toString() { throw new AssertionError("must not stringify opaque memory"); }
        };
        require(snapshot.memoryValue(opaque).get("status").getAsString().equals("NOT_EXPOSED"), "opaque memory status");
        ExpirableValue<Object> custom = new ExpirableValue<>(opaque, 100) {
            @Override public Object getValue() { throw new AssertionError("custom memory value getter invoked"); }
            @Override public long getTimeToLive() { throw new AssertionError("custom TTL getter invoked"); }
            @Override public boolean canExpire() { throw new AssertionError("custom expiry getter invoked"); }
        };
        JsonObject expiry = snapshot.expirableValue(custom);
        require(expiry.get("timeToLive").getAsLong() == 100, "read cached TTL without mutation");
        require(expiry.get("canExpire").getAsBoolean(), "read cached expiry policy");
        require(expiry.get("timeToLive").getAsJsonPrimitive().isString(), "TTL must remain exact through JavaScript JSON parsing");
        require(expiry.getAsJsonObject("value").get("status").getAsString().equals("NOT_EXPOSED"), "opaque expirable value");
        for (long value : new long[] {Long.MIN_VALUE, Long.MAX_VALUE, 100L}) {
            JsonObject encoded = snapshot.memoryValue(value);
            require(encoded.get("value").getAsJsonPrimitive().isString(), "64-bit memory must not lose precision in JavaScript");
            require(encoded.get("value").getAsString().equals(Long.toString(value)), "exact signed memory value");
            require(encoded.get("encoding").getAsString().equals("INT64_DECIMAL_STRING"), "explicit memory value encoding");
        }
        System.out.println("Actual GoalSelector snapshot: bounded, revision fenced, no AI replay or mutation");
    }

    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
}
