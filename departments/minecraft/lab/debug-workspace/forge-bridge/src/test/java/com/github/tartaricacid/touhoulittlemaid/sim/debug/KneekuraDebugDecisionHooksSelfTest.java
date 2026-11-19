package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.util.profiling.InactiveProfiler;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.concurrent.atomic.AtomicLong;

/** Genuine mapped APIs; producer contracts do not substitute for native Mixin acceptance. */
public final class KneekuraDebugDecisionHooksSelfTest {
    private static final class CountingGoal extends Goal {
        int eligibility, starts, stops;
        CountingGoal() { setFlags(EnumSet.of(Flag.MOVE)); }
        @Override public boolean canUse() { eligibility++; return true; }
        @Override public void start() { starts++; }
        @Override public void stop() { stops++; }
        @Override public EnumSet<Flag> getFlags() { throw new AssertionError("custom getter called"); }
        @Override public String toString() { throw new AssertionError("stringification called"); }
    }
    public static void main(String[] args) throws Exception {
        var goal = new CountingGoal();
        var selector = new GoalSelector(() -> InactiveProfiler.INSTANCE);
        selector.addGoal(2,goal);
        WrappedGoal wrapper = selector.getAvailableGoals().iterator().next();
        var context = new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,
                "11111111-2222-3333-4444-555555555555","minecraft:overworld");
        var snapshot = new KneekuraDebugDecisionSnapshot();snapshot.reset(7);
        var time = new AtomicLong(100);
        var rows = new ArrayList<JsonObject>();
        var session = new KneekuraDebugDecisionHooks.Session(null,selector,
                new GoalSelector(() -> InactiveProfiler.INSTANCE),snapshot,
                new KneekuraDebugDecisionBurstBudget(context,100,5,8,65536),8,java.util.Set.of("goal"),
                () -> context,time::get,(method,row) -> rows.add(row));
        require(goal.eligibility==0 && goal.starts==0 && goal.stops==0,"arming must not execute AI");
        boolean result=wrapper.canUse(); // original gameplay call, deliberately made by the test
        session.goalReturn(wrapper,false,result);
        wrapper.start();session.goalLifecycle(wrapper,true);
        wrapper.stop();session.goalLifecycle(wrapper,false);
        require(goal.eligibility==1 && goal.starts==1 && goal.stops==1,"observer must not replay original callbacks");
        require(rows.size()==3,"exact original invocations captured");
        require(rows.get(0).getAsJsonObject("data").get("result").getAsBoolean(),"actual returned eligibility");
        require(rows.get(0).get("targetRevision").getAsLong()==7,"selection fenced");
        require(rows.get(0).getAsJsonObject("data").get("instanceIdentity").getAsString().startsWith("goal:7:"),"shared stable goal identity");
        require(!rows.get(2).getAsJsonObject("data").get("running").getAsBoolean(),"post-stop cached state");
        session.goalReturn(new WrappedGoal(1,new CountingGoal()),false,true);
        require(rows.size()==3,"unselected/unregistered wrapper excluded");
        time.set(105);session.goalReturn(wrapper,false,true);
        require(rows.size()==3 && session.budget().reason().equals("WINDOW_ENDED"),"finite hook window");
        var excluded=new KneekuraDebugDecisionHooks.Session(null,selector,
                new GoalSelector(() -> InactiveProfiler.INSTANCE),snapshot,
                new KneekuraDebugDecisionBurstBudget(context,100,5,8,65536),8,java.util.Set.of("path"),
                () -> context,() -> 100L,(method,row) -> {throw new AssertionError("excluded channel emitted");});
        excluded.goalReturn(wrapper,false,true);
        excluded.goalLifecycle(wrapper,true);
        require(excluded.budget().events()==0,"excluded channels do not consume budget");

        var evaluator=new WalkNodeEvaluator();
        var finder=new PathFinder(evaluator,1024);
        @SuppressWarnings("unchecked") var cache=(Int2ObjectMap<Node>)KneekuraDebugDecisionSnapshot.read(
                net.minecraft.world.level.pathfinder.NodeEvaluator.class,"nodes",evaluator);
        for(int i=0;i<12;i++) {var node=new Node(i,64,0);node.g=i;node.h=2;node.f=i+2;node.closed=i%2==0;node.heapIdx=i%2==0?-1:i;cache.put(i,node);}
        JsonObject frontier=KneekuraDebugDecisionHooks.frontier(finder,8);
        require(frontier.get("status").getAsString().equals("PARTIAL"),"bounded frontier declares truncation");
        require(frontier.getAsJsonObject("data").getAsJsonArray("nodes").size()==8,"node bound");
        require(cache.size()==12 && cache.get(3).g==3 && cache.get(3).heapIdx==3,"frontier read cannot reorder/mutate search state");
        require(frontier.getAsJsonObject("data").get("neighborEvaluationTraceStatus").getAsString().equals("NOT_EXPOSED"),"cache is not fabricated neighbor evaluation trace");
        System.out.println("Actual decision-hook producers: no AI replay, exact wrapper/selection fence, finite window, unchanged bounded node cache");
    }
    private static void require(boolean condition,String message) { if(!condition)throw new AssertionError(message); }
}
