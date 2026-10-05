package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Ghast;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.schedule.Activity;
import net.minecraft.world.entity.schedule.Schedule;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.ai.behavior.Behavior;
import net.minecraft.world.entity.ai.behavior.BehaviorControl;
import net.minecraft.world.entity.ai.behavior.OneShot;
import net.minecraft.world.entity.ai.behavior.GateBehavior;
import net.minecraft.world.entity.ai.behavior.MoveToTargetSink;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.level.pathfinder.AmphibiousNodeEvaluator;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import net.minecraft.world.level.pathfinder.BinaryHeap;
import net.minecraft.world.level.pathfinder.FlyNodeEvaluator;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.NodeEvaluator;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.SwimNodeEvaluator;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.IdentityHashMap;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.LongSupplier;
import java.util.function.BooleanSupplier;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.level.PathNavigationRegion;
import net.minecraft.server.level.ServerLevel;
import java.util.function.Supplier;

/** Debug-only callbacks of original ANCHOR method invocations, never a second AI call. */
public final class KneekuraDebugDecisionHooks {
    private static volatile Session active;
    private KneekuraDebugDecisionHooks() { }
    @FunctionalInterface public interface Sink { void record(String method, JsonObject payload) throws IOException; }
    @FunctionalInterface private interface Data { JsonObject read() throws ReflectiveOperationException; }
    private record PendingPop(Node node,int eventIndex) { }
    private record ActivityFrame(Brain<?> brain,String id,JsonObject before,long preCallCost) { }
    private static final class ActivityRequirementFrame {
        final ActivityFrame parent;final Activity requested;final Map<?,?> requirements;final String id,site;
        final List<JsonObject> checks=new ArrayList<>();Boolean membership;int count;boolean truncated,invalid;
        ActivityRequirementFrame(ActivityFrame parent,Activity requested,Map<?,?> requirements,String id,String site){this.parent=parent;this.requested=requested;this.requirements=requirements;this.id=id;this.site=site;}
    }
    private static final class MemorySourceFrame {
        final Brain<?> brain;final MemoryModuleType<?> module;final MemoryStatus requested;final Map<?,?> memories;final String id;final int index;
        final StartFrame start;final StartConditionCapture condition;final MemoryRequirementCapture requirement;final ActivityRequirementFrame activity;
        Object slot;boolean got,invalid,returned;Boolean presence,baseResult;String presenceSite;
        MemorySourceFrame(Brain<?> brain,MemoryModuleType<?> module,MemoryStatus requested,Map<?,?> memories,String id,int index,StartFrame start,StartConditionCapture condition,MemoryRequirementCapture requirement,ActivityRequirementFrame activity){this.brain=brain;this.module=module;this.requested=requested;this.memories=memories;this.id=id;this.index=index;this.start=start;this.condition=condition;this.requirement=requirement;this.activity=activity;}
    }
    private record SinkFrame(MoveToTargetSink behavior,Mob owner,Brain<?> brain,PathNavigation navigation,
                             String id,String parentId,String callSite,long gameTime,JsonObject before,long preCallCost) { }

    private static final class ComputeFrame {
        final MoveToTargetSink behavior;final Mob owner;final Brain<?> brain;final PathNavigation navigation;
        final WalkTarget target;final long gameTime;final String id,site,sinkId,tickStopId;
        int nextCreate,nextReached;CreateFrame lastCreate;
        ComputeFrame(MoveToTargetSink behavior,Mob owner,Brain<?> brain,PathNavigation navigation,WalkTarget target,long gameTime,String id,String site,String sinkId,String tickStopId){
            this.behavior=behavior;this.owner=owner;this.brain=brain;this.navigation=navigation;this.target=target;this.gameTime=gameTime;this.id=id;this.site=site;this.sinkId=sinkId;this.tickStopId=tickStopId;
        }
    }
    private static final class ReachedFrame {
        final ComputeFrame compute;final String id;int distance,closeEnough,distanceCalls,closeCalls;
        ReachedFrame(ComputeFrame compute,String id){this.compute=compute;this.id=id;}
    }
    private static final class CreateFrame {
        final ComputeFrame compute;final String id,site;final JsonObject arguments;
        final List<String> finderIds=new ArrayList<>();boolean truncated,returned;Path path;
        CreateFrame(ComputeFrame compute,String id,String site,JsonObject arguments){this.compute=compute;this.id=id;this.site=site;this.arguments=arguments;}
    }
    private static final class FinderFrame {
        final CreateFrame create;final PathFinder finder;final String id;String searchId;
        FinderFrame(CreateFrame create,PathFinder finder,String id){this.create=create;this.finder=finder;this.id=id;}
    }

    private static final class DispatchCapture {
        final String branch;final List<String> children=new ArrayList<>();boolean truncated;
        DispatchCapture(String branch){this.branch=branch;}
    }
    private static final class TickStopFrame {
        final MoveToTargetSink behavior;final Mob owner;final Brain<?> brain;final PathNavigation navigation;
        final ServerLevel level;final long gameTime;final String id;DispatchCapture dispatch;
        TickStopFrame(MoveToTargetSink behavior,Mob owner,Brain<?> brain,PathNavigation navigation,ServerLevel level,long gameTime,String id){
            this.behavior=behavior;this.owner=owner;this.brain=brain;this.navigation=navigation;this.level=level;this.gameTime=gameTime;this.id=id;
        }
    }
    private static final class StartConditionCapture {
        final String condition;final List<String> computes=new ArrayList<>();boolean truncated;
        MemoryRequirementCapture requirement;
        StartConditionCapture(String condition){this.condition=condition;}
    }
    private static final class MemoryRequirementCapture {
        final String id;final List<JsonObject> checks=new ArrayList<>();int count;boolean truncated,unsupportedSource;
        MemoryRequirementCapture(String id){this.id=id;}
    }
    private static final class StartFrame {
        final MoveToTargetSink behavior;final Mob owner;final Brain<?> brain;final PathNavigation navigation;
        final ServerLevel level;final long gameTime;final String id;
        StartConditionCapture condition;DispatchCapture dispatch;
        StartFrame(MoveToTargetSink behavior,Mob owner,Brain<?> brain,PathNavigation navigation,ServerLevel level,long gameTime,String id){
            this.behavior=behavior;this.owner=owner;this.brain=brain;this.navigation=navigation;this.level=level;this.gameTime=gameTime;this.id=id;
        }
    }

    private static final class StartLoopFrame {
        final Brain<?> brain;final Mob owner;final PathNavigation navigation;final ServerLevel level;final Set<?> activeActivities;final String id;
        final List<StartActivityCapture> activities=new ArrayList<>();int count;boolean truncated,invalid;Long gameTime;
        StartActivityCapture activity;StartControlCapture control;
        StartLoopFrame(Brain<?> brain,Mob owner,PathNavigation navigation,ServerLevel level,Set<?> activeActivities,String id){
            this.brain=brain;this.owner=owner;this.navigation=navigation;this.level=level;this.activeActivities=activeActivities;this.id=id;
        }
    }
    private static final class StartActivityCapture {
        final Object requested;final boolean result;final int index;final List<StartControlCapture> controls=new ArrayList<>();int count;boolean truncated;
        StartActivityCapture(Object requested,boolean result,int index){this.requested=requested;this.result=result;this.index=index;}
    }
    private static final class StartControlCapture {
        final BehaviorControl<?> control;final Behavior.Status status;final int index;Boolean result;String child;
        StartControlCapture(BehaviorControl<?> control,Behavior.Status status,int index){this.control=control;this.status=status;this.index=index;}
    }

    public static void install(Session session) {
        if (session.thread != Thread.currentThread()) throw new IllegalStateException("SERVER_THREAD_REQUIRED");
        clear("REARMED");active=session;
    }
    public static void clear(String reason) {
        Session previous=active;active=null;
        if(previous!=null){previous.budget.close(reason);previous.clearHeapNodes();previous.memorySourceFrame=null;previous.activityRequirementFrame=null;previous.sinkFrame=null;previous.tickStopFrame=null;previous.startFrame=null;previous.startLoopFrame=null;previous.computeFrame=null;previous.createFrame=null;previous.finderFrame=null;previous.reachedFrame=null;}
    }

    public static final class Session {
        private final Thread thread=Thread.currentThread();
        private final Mob subject;
        private final KneekuraDebugDecisionSnapshot snapshot;
        private final KneekuraDebugDecisionBurstBudget budget;
        private final int nodeLimit;
        private final Set<String> channels;
        private final KneekuraDebugTwilightForestAdapter modAdapter;
        private final Supplier<KneekuraDebugDecisionBurstBudget.Context> currentContext;
        private final LongSupplier time;
        private final Sink sink;
        private final IdentityHashMap<WrappedGoal,JsonObject> goals=new IdentityHashMap<>();
        private final IdentityHashMap<Object,String> identities=new IdentityHashMap<>();
        private final IdentityHashMap<PathFinder,String> searches=new IdentityHashMap<>();
        private final IdentityHashMap<PathFinder,IdentityHashMap<Node,String>> heapNodes;
        private final IdentityHashMap<PathFinder,PendingPop> pendingPops;
        private final IdentityHashMap<Projectile,Integer> projectiles=new IdentityHashMap<>();
        private long nextIdentity, nextSearch;
        private int nextActivity;
        private int activityDepth;
        private ActivityFrame activityFrame;
        private ActivityRequirementFrame activityRequirementFrame;private int nextActivityRequirement,activityRequirementDepth;
        private int nextSink,sinkDepth;
        private SinkFrame sinkFrame;
        private TickStopFrame tickStopFrame;
        private int nextTickStop,tickStopDepth;
        private StartFrame startFrame;private int nextStart,startDepth;
        private int nextMemoryRequirement;
        private MemorySourceFrame memorySourceFrame;private int nextMemorySource,memorySourceDepth;
        private StartLoopFrame startLoopFrame;private int nextStartLoop,startLoopDepth;
        private ComputeFrame computeFrame;private CreateFrame createFrame;private FinderFrame finderFrame;
        private int nextCompute,computeDepth,createDepth,finderDepth,reachedDepth;
        private ReachedFrame reachedFrame;
        private boolean goalCoveragePartial;

        public Session(Mob subject, GoalSelector goal, GoalSelector target,
                       KneekuraDebugDecisionSnapshot snapshot, KneekuraDebugDecisionBurstBudget budget,
                       int nodeLimit, Set<String> channels, Supplier<KneekuraDebugDecisionBurstBudget.Context> currentContext,
                       LongSupplier time, Sink sink) throws ReflectiveOperationException {
            if(nodeLimit<1 || nodeLimit>64)throw new IllegalArgumentException("NODE_LIMIT_OUT_OF_RANGE");
            this.subject=subject;this.snapshot=snapshot;this.budget=budget;this.nodeLimit=nodeLimit;
            if(channels==null||channels.isEmpty()||!Set.of("goal","brain","brain_activity","brain_navigation","navigation_result","path","control","malus","sensor","mod","projectile","neighbors","effective_malus","frontier","path_nodes","path_g","path_distance").containsAll(channels))
                throw new IllegalArgumentException("INVALID_CHANNELS");
            this.channels=Set.copyOf(channels);
            this.heapNodes=channels.contains("frontier")||channels.contains("path_nodes")||channels.contains("path_g")||channels.contains("path_distance")?new IdentityHashMap<>():null;
            this.pendingPops=channels.contains("frontier")?new IdentityHashMap<>():null;
            this.modAdapter=channels.contains("mod")?KneekuraDebugTwilightForestAdapter.shared():null;
            this.currentContext=currentContext;this.time=time;this.sink=sink;
            if(channels.contains("goal")){register(goal,"goal");register(target,"target");}
        }
        private void register(GoalSelector selector,String name) throws ReflectiveOperationException {
            Set<?> registered=(Set<?>)KneekuraDebugDecisionSnapshot.read(GoalSelector.class,"availableGoals",selector);
            int count=0;
            for(Object object:registered) {
                if(count++>=64)break;
                WrappedGoal wrapper=(WrappedGoal)object;
                Goal goal=(Goal)KneekuraDebugDecisionSnapshot.read(WrappedGoal.class,"goal",wrapper);
                JsonObject data=new JsonObject();data.addProperty("selector",name);
                String token=snapshot.identity(goal);
                data.addProperty("instanceIdentity",token);
                data.addProperty("instanceIdentityStatus",token==null?"NOT_EXPOSED":"AVAILABLE");
                data.addProperty("goalClass",label(goal.getClass().getName()));
                data.addProperty("priority",(Integer)KneekuraDebugDecisionSnapshot.read(WrappedGoal.class,"priority",wrapper));
                goals.put(wrapper,data);
            }
            goalCoveragePartial|=registered.size()>64;
        }
        public KneekuraDebugDecisionBurstBudget budget() { return budget; }
        public boolean goalCoveragePartial() { return goalCoveragePartial; }
        private void clearHeapNodes(){if(heapNodes!=null)heapNodes.clear();if(pendingPops!=null)pendingPops.clear();}
        private JsonObject nodeIdentity(PathFinder finder,Node node) {
            JsonObject identity=new JsonObject();var nodes=heapNodes.get(finder);
            String id=node==null?null:nodes.get(node);
            if(node!=null&&id==null&&nodes.size()<nodeLimit){id=searches.get(finder)+":node:"+(nodes.size()+1);nodes.put(node,id);}
            if(id==null){identity.addProperty("status","NOT_EXPOSED");identity.addProperty("detail",node==null?"NULL_NODE":"NODE_IDENTITY_LIMIT");}
            else {identity.addProperty("status","AVAILABLE");identity.addProperty("id",id);}
            return identity;
        }
        private boolean matches(LivingEntity entity) { return subject!=null && subject==entity && thread==Thread.currentThread(); }
        private boolean activityReady(Brain<?> brain) {
            if(thread!=Thread.currentThread()||subject==null||!channels.contains("brain_activity"))return false;
            try {
                return budget.allows(currentContext.get(),time.getAsLong())&&
                    KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",subject)==brain;
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){
                budget.close("ACTIVITY_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return false;
            }
        }
        private ActivityFrame activityBegin(Brain<?> brain) {
            if(!activityReady(brain)||nextActivity>=256||activityDepth>8)return null;
            long started=System.nanoTime();
            try {
                JsonObject before=activityState(brain);
                return new ActivityFrame(brain,"activity:"+budget.context().selectionRevision()+":"+(++nextActivity),
                    before,Math.max(0L,System.nanoTime()-started));
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){
                budget.close("ACTIVITY_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return null;
            }
        }
        private boolean activityRequirementReady(ActivityRequirementFrame frame) {
            if(active!=this||frame==null||frame.invalid||activityFrame!=frame.parent||!activityReady(frame.parent.brain()))return false;
            try {return KneekuraDebugDecisionSnapshot.read(Brain.class,"activityRequirements",frame.parent.brain())==frame.requirements;}
            catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("ACTIVITY_REQUIREMENT_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return false;}
        }
        private ActivityRequirementFrame activityRequirementBegin(Brain<?> brain,Activity requested,String site) {
            ActivityFrame parent=activityFrame(this,brain);
            if(parent==null||!Set.of("IF_POSSIBLE","FIRST_VALID").contains(site)||nextActivityRequirement>=256||activityRequirementDepth>8)return null;
            try {Map<?,?> map=(Map<?,?>)KneekuraDebugDecisionSnapshot.read(Brain.class,"activityRequirements",brain);if(map==null)return null;
                return new ActivityRequirementFrame(parent,requested,map,"activity-requirement:"+budget.context().selectionRevision()+":"+(++nextActivityRequirement),site);
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("ACTIVITY_REQUIREMENT_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return null;}
        }
        private boolean memorySourceReady(MemorySourceFrame frame) {
            if(active!=this||thread!=Thread.currentThread()||frame==null||frame.invalid)return false;
            if(frame.start!=null){if(startFrame!=frame.start||frame.start.condition!=frame.condition||frame.condition.requirement!=null||frame.requirement.unsupportedSource||!startReady(frame.start))return false;}
            else if(activityRequirementFrame!=null||!activityRequirementReady(frame.activity))return false;
            try {return KneekuraDebugDecisionSnapshot.read(Brain.class,"memories",frame.brain)==frame.memories;}
            catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("MEMORY_SOURCE_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return false;}
        }
        private MemorySourceFrame memorySourceBegin(Brain<?> brain,MemoryModuleType<?> module,MemoryStatus requested,int index,StartFrame start,StartConditionCapture condition,MemoryRequirementCapture requirement,ActivityRequirementFrame activity) {
            if(index<1||index>8||nextMemorySource>=256||memorySourceDepth>8)return null;
            try {Map<?,?> map=(Map<?,?>)KneekuraDebugDecisionSnapshot.read(Brain.class,"memories",brain);if(map==null)return null;
                MemorySourceFrame frame=new MemorySourceFrame(brain,module,requested,map,"memory-source:"+budget.context().selectionRevision()+":"+(++nextMemorySource),index,start,condition,requirement,activity);
                return memorySourceReady(frame)?frame:null;
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("MEMORY_SOURCE_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return null;}
        }
        private boolean sinkReady(SinkFrame frame) {
            if(active!=this||thread!=Thread.currentThread()||!channels.contains("brain_navigation")||!matches(frame.owner()))return false;
            try {
                return budget.allows(currentContext.get(),time.getAsLong())&&
                    KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",subject)==frame.brain()&&
                    KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",subject)==frame.navigation()&&
                    KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",frame.navigation())==subject;
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("SINK_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return false;}
        }
        private SinkFrame sinkBegin(MoveToTargetSink behavior,Mob owner,long gameTime,String site,SinkFrame previous) {
            if(!matches(owner)||!channels.contains("brain_navigation")||behavior==null||behavior.getClass()!=MoveToTargetSink.class||
                !Set.of("START_FROM_BRIDGE","TICK_FROM_BRIDGE","START_FROM_TICK","STOP_FROM_BRIDGE").contains(site)||nextSink>=256||sinkDepth>8)return null;
            long started=System.nanoTime();
            try {
                if(!budget.allows(currentContext.get(),time.getAsLong()))return null;
                Brain<?> brain=(Brain<?>)KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",owner);
                PathNavigation navigation=(PathNavigation)KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",owner);
                if(brain==null||navigation==null||KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",navigation)!=owner)return null;
                JsonObject before=sinkState(this,behavior,brain,navigation,site.equals("STOP_FROM_BRIDGE"));
                return new SinkFrame(behavior,owner,brain,navigation,"sink:"+budget.context().selectionRevision()+":"+(++nextSink),
                    previous!=null&&previous.behavior()==behavior&&previous.owner()==owner?previous.id():null,site,gameTime,before,
                    Math.max(0L,System.nanoTime()-started));
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("SINK_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return null;}
        }
        private boolean tickStopReady(TickStopFrame frame) {
            if(active!=this||!matches(frame.owner)||!channels.contains("brain_navigation"))return false;
            try {return budget.allows(currentContext.get(),time.getAsLong())&&
                KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",subject)==frame.brain&&
                KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",subject)==frame.navigation&&
                KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",frame.navigation)==subject;
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("TICK_STOP_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return false;}
        }
        private TickStopFrame tickStopBegin(Brain<?> brain,BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long gameTime) {
            if(!matches(owner)||!channels.contains("brain_navigation")||control==null||control.getClass()!=MoveToTargetSink.class||nextTickStop>=256||tickStopDepth>8)return null;
            try {
                if(!budget.allows(currentContext.get(),time.getAsLong())||KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",owner)!=brain)return null;
                PathNavigation navigation=(PathNavigation)KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",owner);
                if(brain==null||navigation==null||KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",navigation)!=owner)return null;
                return new TickStopFrame((MoveToTargetSink)control,(Mob)owner,brain,navigation,level,gameTime,
                    "tick-stop:"+budget.context().selectionRevision()+":"+(++nextTickStop));
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("TICK_STOP_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return null;}
        }
        private boolean computeReady(ComputeFrame frame) {
            if(active!=this||frame==null||!matches(frame.owner)||!channels.contains("brain_navigation"))return false;
            try {return budget.allows(currentContext.get(),time.getAsLong())&&
                KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",subject)==frame.brain&&
                KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",subject)==frame.navigation&&
                KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",frame.navigation)==subject;
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("COMPUTE_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return false;}
        }
        private boolean startLoopReady(StartLoopFrame frame) {
            if(active!=this||frame==null||frame.invalid||!matches(frame.owner)||!channels.contains("brain_navigation"))return false;
            try {return budget.allows(currentContext.get(),time.getAsLong())&&
                KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",subject)==frame.brain&&
                KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",subject)==frame.navigation&&
                KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",frame.navigation)==subject&&
                KneekuraDebugDecisionSnapshot.read(Brain.class,"activeActivities",frame.brain)==frame.activeActivities;
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("START_LOOP_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return false;}
        }
        private StartLoopFrame startLoopBegin(Brain<?> brain,ServerLevel level,LivingEntity owner) {
            if(!matches(owner)||!channels.contains("brain_navigation")||brain==null||nextStartLoop>=256||startLoopDepth>8)return null;
            try {
                if(!budget.allows(currentContext.get(),time.getAsLong())||KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",owner)!=brain)return null;
                PathNavigation navigation=(PathNavigation)KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",owner);
                Set<?> activities=(Set<?>)KneekuraDebugDecisionSnapshot.read(Brain.class,"activeActivities",brain);
                if(navigation==null||activities==null||KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",navigation)!=owner)return null;
                return new StartLoopFrame(brain,(Mob)owner,navigation,level,activities,"start-loop:"+budget.context().selectionRevision()+":"+(++nextStartLoop));
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("START_LOOP_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return null;}
        }
        private boolean startReady(StartFrame frame) {
            if(active!=this||frame==null||!matches(frame.owner)||!channels.contains("brain_navigation"))return false;
            try {return budget.allows(currentContext.get(),time.getAsLong())&&
                KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",subject)==frame.brain&&
                KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",subject)==frame.navigation&&
                KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",frame.navigation)==subject;
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("START_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return false;}
        }
        private StartFrame startBegin(Brain<?> brain,BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long gameTime) {
            if(!matches(owner)||!channels.contains("brain_navigation")||control==null||control.getClass()!=MoveToTargetSink.class||nextStart>=256||startDepth>8)return null;
            try {
                if(!budget.allows(currentContext.get(),time.getAsLong())||KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",owner)!=brain)return null;
                PathNavigation navigation=(PathNavigation)KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",owner);
                if(brain==null||navigation==null||KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",navigation)!=owner)return null;
                return new StartFrame((MoveToTargetSink)control,(Mob)owner,brain,navigation,level,gameTime,"try-start:"+budget.context().selectionRevision()+":"+(++nextStart));
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("START_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return null;}
        }
        private boolean reachedReady(ReachedFrame frame) {
            return frame!=null&&computeFrame==frame.compute&&computeReady(frame.compute);
        }
        private ComputeFrame computeBegin(MoveToTargetSink behavior,Mob owner,WalkTarget target,long game,String site) {
            if(!matches(owner)||!channels.contains("brain_navigation")||behavior==null||behavior.getClass()!=MoveToTargetSink.class||target==null||
                !Set.of("CHECK_EXTRA_START","TICK_RECOMPUTE").contains(site)||nextCompute>=256||computeDepth>8)return null;
            try {
                if(!budget.allows(currentContext.get(),time.getAsLong()))return null;
                Brain<?> brain=(Brain<?>)KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",owner);
                PathNavigation navigation=(PathNavigation)KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",owner);
                if(brain==null||navigation==null||KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",navigation)!=owner)return null;
                String sinkId=sinkFrame!=null&&sinkFrame.behavior()==behavior&&sinkFrame.owner()==owner&&sinkFrame.brain()==brain&&sinkFrame.navigation()==navigation&&sinkReady(sinkFrame)?sinkFrame.id():null;
                String tickId=tickStopFrame!=null&&tickStopFrame.behavior==behavior&&tickStopFrame.owner==owner&&tickStopFrame.brain==brain&&tickStopFrame.navigation==navigation&&tickStopReady(tickStopFrame)?tickStopFrame.id:null;
                return new ComputeFrame(behavior,owner,brain,navigation,target,game,"compute:"+budget.context().selectionRevision()+":"+(++nextCompute),site,sinkId,tickId);
            }catch(ReflectiveOperationException|RuntimeException|LinkageError error){budget.close("COMPUTE_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());return null;}
        }
        private String token(Object object) {
            String token=identities.get(object);
            if(token!=null)return token;
            if(identities.size()>=128)return null;
            token="component:"+budget.context().selectionRevision()+":"+(++nextIdentity);identities.put(object,token);return token;
        }
        private boolean record(String kind,String method,Data capture) {
            if(thread!=Thread.currentThread())return false;
            String channel=kind.startsWith("CONTROL_PROJECTILE_")&&channels.contains("projectile")?"projectile":
                    kind.startsWith("BRAIN_ACTIVITY_")?"brain_activity":
                    kind.startsWith("BRAIN_PATH_")?"brain_navigation":
                    kind.equals("NAVIGATION_MOVE_TO_RETURN")?"navigation_result":
                    kind.equals("PATH_NEIGHBORS_RETURN")?"neighbors":
                    kind.equals("PATH_RETURNED_NODES")?"path_nodes":
                    kind.equals("PATH_NODE_G_WRITE_CHECKPOINT")?"path_g":
                    kind.equals("PATH_EDGE_DISTANCE_RETURN")?"path_distance":
                    kind.equals("PATH_HEAP_OPERATION_RETURN")||kind.equals("PATH_NODE_CLOSED_CHECKPOINT")?"frontier":
                    kind.equals("EFFECTIVE_MALUS_RETURN")?"effective_malus":
                    kind.startsWith("MOD_")?"mod":kind.startsWith("GOAL_")?"goal":kind.startsWith("PATH_")?"path":
                    kind.startsWith("CONTROL_")?"control":kind.startsWith("BASE_MALUS_")?"malus":
                    kind.startsWith("SENSOR_")?"sensor":kind.startsWith("BRAIN_")||kind.startsWith("BEHAVIOR_")?"brain":null;
            if(channel==null||!channels.contains(channel))return false;
            try {
                var context=currentContext.get();long tick=time.getAsLong();
                if(!budget.allows(context,tick)){clearHeapNodes();return false;}
                long started=System.nanoTime();JsonObject data=capture.read();
                JsonObject root=new JsonObject();
                boolean mod=kind.equals("MOD_TRANSITION_RETURN");
                root.addProperty("schema",mod?"kneekura.mod-decision-return/v1":"kneekura.original-decision-event/v1");
                root.addProperty("semantics",mod?"ORIGINAL_MOD_INVOCATION_RETURN_ONLY":
                    kind.equals("PATH_NODE_CLOSED_CHECKPOINT")||kind.equals("PATH_NODE_G_WRITE_CHECKPOINT")||kind.equals("BRAIN_PATH_COMPUTE_PATH_WRITE_CHECKPOINT")||kind.equals("MOD_HYDRA_STATE_WRITE_CHECKPOINT")?"ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY":"ORIGINAL_INVOCATION_RETURN_ONLY");
                if(mod) {
                    root.addProperty("returnTick",subject.level().getGameTime());
                    root.addProperty("returnLocalTick",tick);root.addProperty("localTickScope","LAST_COMPLETED_SERVER_END_COUNTER");
                    root.add("descriptor",data.get("descriptor"));
                    root.add("compatibilityStatus",data.get("compatibilityStatus"));root.add("entityClass",data.get("entityClass"));
                    data=data.getAsJsonObject("data");
                }
                root.addProperty("targetRevision",context.selectionRevision());
                root.addProperty("burstId","burst:"+context.selectionRevision()+":"+budget.startTick());
                root.addProperty("eventIndex",budget.events()+1);root.addProperty("kind",kind);root.add("data",data);
                root.addProperty("observerCostNanos",0L);
                root.addProperty("observerCostScope","BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER");
                root.toString().getBytes(StandardCharsets.UTF_8);
                root.addProperty("observerCostNanos",Math.max(0L,System.nanoTime()-started));
                int bytes=root.toString().getBytes(StandardCharsets.UTF_8).length;
                if(budget.claim(context,tick,bytes)){sink.record(method,root);return true;}
                clearHeapNodes();
            } catch(ReflectiveOperationException|RuntimeException|LinkageError error) {
                clearHeapNodes();
                budget.close("CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());
            } catch(IOException error) {clearHeapNodes();budget.close("WRITER_UNAVAILABLE");}
            return false;
        }
        private boolean readyProjectile() {
            if(thread!=Thread.currentThread()||(!channels.contains("control")&&!channels.contains("projectile"))||subject==null)return false;
            try{return budget.allows(currentContext.get(),time.getAsLong());}
            catch(RuntimeException error){budget.close("CONTEXT_UNAVAILABLE");return false;}
        }
        private boolean selectedOwner(Projectile shot) throws ReflectiveOperationException {
            // Do not call getOwner: its fallback performs a level lookup and mutates cachedOwner.
            return KneekuraDebugDecisionSnapshot.read(Projectile.class,"cachedOwner",shot)==subject&&
                subject.getUUID().equals(KneekuraDebugDecisionSnapshot.read(Projectile.class,"ownerUUID",shot))&&
                KneekuraDebugDecisionSnapshot.read(Entity.class,"level",shot)==KneekuraDebugDecisionSnapshot.read(Entity.class,"level",subject);
        }
        private boolean trackedProjectile(Projectile shot) {
            if(!projectiles.containsKey(shot)||!readyProjectile())return false;
            if(projectiles.get(shot)==0)return false;
            try{if(selectedOwner(shot))return true;projectiles.put(shot,0);return false;}
            catch(ReflectiveOperationException|RuntimeException error){budget.close("PROJECTILE_OWNER_UNAVAILABLE");return false;}
        }
        private JsonObject projectileReference(Projectile shot,int spawnIndex) {
            JsonObject data=new JsonObject();data.addProperty("ownerUuid",budget.context().subjectUuid());
            data.addProperty("projectileUuid",shot.getUUID().toString());data.addProperty("projectileClass",label(shot.getClass().getName()));
            data.addProperty("spawnEventIndex",spawnIndex);
            data.addProperty("relationshipScope","ACCEPTED_FRESH_SPAWN_SELECTED_CACHED_OWNER");return data;
        }
        private void projectileSpawn(Projectile shot,boolean result) {
            if(!readyProjectile()||projectiles.containsKey(shot)||projectiles.size()>=16)return;
            try{if(!selectedOwner(shot))return;}
            catch(ReflectiveOperationException|RuntimeException error){budget.close("PROJECTILE_OWNER_UNAVAILABLE");return;}
            int index=budget.events()+1;
            boolean written=record("CONTROL_PROJECTILE_SPAWN_RETURN","ServerLevel.addFreshEntity.RETURN",()->{
                JsonObject data=projectileReference(shot,index);data.addProperty("result",result);data.addProperty("trackingLimit",16);
                data.add("position",position(shot));data.add("velocity",vector(shot.getDeltaMovement()));
                data.addProperty("dispatchScope","SERVER_ADD_FRESH_ENTITY_RETURN");return data;
            });
            if(written&&result)projectiles.put(shot,index);
        }
        void goalReturn(WrappedGoal wrapper,boolean continuation,boolean result) {
            JsonObject reference=goals.get(wrapper);if(reference==null)return;
            record(continuation?"GOAL_CONTINUATION_RETURN":"GOAL_ELIGIBILITY_RETURN",
                    continuation?"WrappedGoal.canContinueToUse.RETURN":"WrappedGoal.canUse.RETURN",()->{
                        JsonObject data=reference.deepCopy();data.addProperty("result",result);
                        data.addProperty("rejectionReasonStatus","NOT_EXPOSED");
                        data.addProperty("callSiteStatus","NOT_EXPOSED");return data;
                    });
        }
        void goalLifecycle(WrappedGoal wrapper,boolean started) {
            JsonObject reference=goals.get(wrapper);if(reference==null)return;
            record(started?"GOAL_START_RETURN":"GOAL_STOP_RETURN",
                    started?"WrappedGoal.Goal.start.AFTER":"WrappedGoal.Goal.stop.AFTER",()->{
                        JsonObject data=reference.deepCopy();
                        data.addProperty("running",(Boolean)KneekuraDebugDecisionSnapshot.read(WrappedGoal.class,"isRunning",wrapper));
                        data.addProperty("reasonStatus","NOT_EXPOSED");return data;
                    });
        }
        void modReturn(Object owner,String method,Object requested) {
            if(modAdapter==null||thread!=Thread.currentThread()||!modAdapter.supports(subject)||owner==null)return;
            boolean head=owner.getClass().getName().equals("twilightforest.entity.boss.HydraHeadContainer")&&
                subject.getClass().getName().equals("twilightforest.entity.boss.Hydra");
            if(owner!=subject&&!head)return;
            if(head)try {
                if(KneekuraDebugDecisionSnapshot.read(owner.getClass(),"hydra",owner)!=subject)return;
            }catch(ReflectiveOperationException|RuntimeException unavailable){return;}
            // Owner/member reads and source proof occur only after the finite budget/context check in record.
            record("MOD_TRANSITION_RETURN",owner.getClass().getName()+"."+method+".RETURN",
                ()->modAdapter.captureOriginalReturn(subject,owner,method,requested));
        }
        void knightCoordination(Object goal,List<?> members) {
            if(modAdapter==null||thread!=Thread.currentThread()||subject==null||goal==null||members==null||
                    !subject.getClass().getName().equals("twilightforest.entity.boss.KnightPhantom")||
                    !goal.getClass().getName().equals("twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal")||
                    members.getClass()!=ArrayList.class)return;
            try {
                if(!budget.allows(currentContext.get(),time.getAsLong())||
                        KneekuraDebugDecisionSnapshot.read(goal.getClass(),"boss",goal)!=subject||
                        !budget.context().subjectUuid().equals(KneekuraDebugDecisionSnapshot.read(Entity.class,"uuid",subject).toString()))return;
            }catch(ReflectiveOperationException|RuntimeException unavailable){return;}
            record("MOD_COORDINATION_RETURN",goal.getClass().getName()+".broadcastMyFormation.RETURN",
                ()->modAdapter.captureKnightCoordination(subject,goal,members,Math.min(16,nodeLimit)));
        }
        private boolean readyKnightBoundary(Object goal) {
            if(modAdapter==null||!channels.contains("mod")||thread!=Thread.currentThread()||subject==null||goal==null||
                    !subject.getClass().getName().equals("twilightforest.entity.boss.KnightPhantom")||
                    !goal.getClass().getName().equals("twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal"))return false;
            try{return budget.allows(currentContext.get(),time.getAsLong())&&
                KneekuraDebugDecisionSnapshot.read(goal.getClass(),"boss",goal)==subject&&
                budget.context().subjectUuid().equals(KneekuraDebugDecisionSnapshot.read(Entity.class,"uuid",subject).toString());
            }catch(ReflectiveOperationException|RuntimeException unavailable){return false;}
        }
        void knightLeader(Object goal,List<?> members,boolean result) {
            if(members==null||members.getClass()!=ArrayList.class||!readyKnightBoundary(goal))return;
            record("MOD_KNIGHT_LEADER_RETURN",goal.getClass().getName()+".isThisTheLeader.RETURN",
                ()->modAdapter.captureKnightLeader(subject,goal,members,Math.min(16,nodeLimit),result));
        }
        void knightMemberDispatch(Object goal,Object member) {
            if(!readyKnightBoundary(goal)||member==null||member.getClass()!=subject.getClass())return;
            record("MOD_KNIGHT_MEMBER_DISPATCH_RETURN",goal.getClass().getName()+".broadcastMyFormation.AFTER_ORIGINAL_MEMBER_SWITCH",
                ()->modAdapter.captureKnightMemberDispatch(subject,goal,member));
        }
        private boolean readyHydraBoundary(Object head) {
            if(modAdapter==null||!channels.contains("mod")||thread!=Thread.currentThread()||subject==null||head==null||
                    !subject.getClass().getName().equals("twilightforest.entity.boss.Hydra")||
                    !head.getClass().getName().equals("twilightforest.entity.boss.HydraHeadContainer"))return false;
            try{return budget.allows(currentContext.get(),time.getAsLong())&&
                KneekuraDebugDecisionSnapshot.read(head.getClass(),"hydra",head)==subject&&
                budget.context().subjectUuid().equals(KneekuraDebugDecisionSnapshot.read(Entity.class,"uuid",subject).toString());
            }catch(ReflectiveOperationException|RuntimeException unavailable){return false;}
        }
        void hydraTargetReturn(Object head,Entity requested) {
            if(!readyHydraBoundary(head))return;
            record("MOD_HYDRA_TARGET_RETURN",head.getClass().getName()+".setTargetEntity.RETURN",
                ()->modAdapter.captureHydraTargetReturn(subject,head,requested));
        }
        void hydraStateWrite(Object head) {
            if(!readyHydraBoundary(head))return;
            record("MOD_HYDRA_STATE_WRITE_CHECKPOINT",head.getClass().getName()+".advanceHeadState.AFTER_ORIGINAL_CURRENT_STATE_WRITE",
                ()->modAdapter.captureHydraStateWrite(subject,head));
        }
    }

    public static void goalReturn(WrappedGoal wrapper,boolean continuation,boolean result) {
        Session session=active;if(session!=null)session.goalReturn(wrapper,continuation,result);
    }
    public static void modReturn(Object owner,String method,Object requested) {
        Session session=active;if(session!=null)session.modReturn(owner,method,requested);
    }
    public static void knightCoordination(Object goal,List<?> members) {
        Session session=active;if(session!=null)session.knightCoordination(goal,members);
    }
    public static void knightLeader(Object goal,List<?> members,boolean result) {
        Session session=active;if(session!=null)session.knightLeader(goal,members,result);
    }
    public static void knightMemberDispatch(Object goal,Object member) {
        Session session=active;if(session!=null)session.knightMemberDispatch(goal,member);
    }
    public static void hydraTargetReturn(Object head,Entity requested) {
        Session session=active;if(session!=null)session.hydraTargetReturn(head,requested);
    }
    public static void hydraStateWrite(Object head) {
        Session session=active;if(session!=null)session.hydraStateWrite(head);
    }
    public static void goalLifecycle(WrappedGoal wrapper,boolean started) {
        Session session=active;if(session!=null)session.goalLifecycle(wrapper,started);
    }
    public static void brainReturn(Brain<?> brain,LivingEntity entity) {
        Session session=active;if(session==null||!session.matches(entity))return;
        session.record("BRAIN_TICK_RETURN","Brain.tick.RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("brainClass",label(brain.getClass().getName()));
            data.addProperty("storedBrainMatch",KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"brain",entity)==brain);
            data.addProperty("instanceIdentity",session.token(brain));return data;
        });
    }
    /** Exact private source delegate; its boolean is not Path.canReach, adoption or arrival. */
    public static boolean originalBrainCompute(MoveToTargetSink behavior,Mob owner,WalkTarget target,long game,String site,BooleanSupplier original) {
        Session session=active;if(session==null||session.thread!=Thread.currentThread())return original.getAsBoolean();
        ComputeFrame previous=session.computeFrame;CreateFrame previousCreate=session.createFrame;FinderFrame previousFinder=session.finderFrame;
        ReachedFrame previousReached=session.reachedFrame;int depth=session.computeDepth;session.computeDepth++;
        try {
            ComputeFrame frame=session.computeBegin(behavior,owner,target,game,site);session.computeFrame=frame;session.createFrame=null;session.finderFrame=null;session.reachedFrame=null;
            StartFrame caller=session.startFrame;
            if(frame!=null&&caller!=null&&caller.behavior==behavior&&caller.owner==owner&&caller.brain==frame.brain&&caller.navigation==frame.navigation&&
                caller.gameTime==game&&site.equals("CHECK_EXTRA_START")&&session.startReady(caller)&&caller.condition!=null&&caller.condition.condition.equals("CHECK_EXTRA_START")){
                if(caller.condition.computes.size()<8)caller.condition.computes.add(frame.id);else caller.condition.truncated=true;
            }
            boolean result=original.getAsBoolean();
            if(session.computeReady(frame))session.record("BRAIN_PATH_COMPUTE_RETURN","MoveToTargetSink.tryComputePath.AFTER",()->{
                JsonObject data=computeData(session,frame);data.addProperty("result",result);
                data.addProperty("resultScope","ORIGINAL_PRIVATE_COMPUTE_BOOLEAN_NOT_CAN_REACH_ADOPTION_OR_ARRIVAL");
                Path stored=(Path)KneekuraDebugDecisionSnapshot.read(MoveToTargetSink.class,"path",behavior);
                data.add("sinkPath",session.snapshot.pathFact(stored));
                data.add("navigationPath",session.snapshot.pathReferenceFact((Path)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"path",frame.navigation)));
                addCreateRelation(session,data,frame.lastCreate,stored);return data;
            });return result;
        }finally {session.computeFrame=active==session?previous:null;session.createFrame=active==session?previousCreate:null;session.finderFrame=active==session?previousFinder:null;session.reachedFrame=active==session?previousReached:null;session.computeDepth=depth;}
    }
    /** Exact original private predicate within compute; operands are original returned ints, not coordinate reconstruction. */
    public static boolean originalComputeReached(MoveToTargetSink behavior,Mob owner,WalkTarget target,BooleanSupplier original) {
        Session session=active;if(session==null||session.thread!=Thread.currentThread())return original.getAsBoolean();
        ComputeFrame compute=session.computeFrame;ReachedFrame previous=session.reachedFrame;int depth=session.reachedDepth;session.reachedDepth++;ReachedFrame frame=null;
        try {
            if(session.computeReady(compute)&&compute.behavior==behavior&&compute.owner==owner&&compute.target==target&&session.reachedDepth<=8&&compute.nextReached<8)
                frame=new ReachedFrame(compute,compute.id+":reached:"+(++compute.nextReached));
            session.reachedFrame=frame;boolean result=original.getAsBoolean();
            if(session.reachedReady(frame)){ReachedFrame captured=frame;session.record("BRAIN_PATH_COMPUTE_CONDITION_RETURN","MoveToTargetSink.tryComputePath.reachedTarget.AFTER",()->{
                JsonObject data=computeData(session,compute);data.addProperty("condition","REACHED_TARGET");data.addProperty("result",result);data.addProperty("reachedInvocationId",captured.id);
                JsonObject operands=new JsonObject();operands.addProperty("scope","ORIGINAL_PRIVATE_PREDICATE_RETURN_OPERANDS_NOT_COORDINATE_RECOMPUTATION");
                operands.addProperty("distanceStatus",captured.distanceCalls==1?"AVAILABLE":"NOT_CAPTURED");if(captured.distanceCalls==1)operands.addProperty("distanceReturn",captured.distance);
                operands.addProperty("closeEnoughStatus",captured.closeCalls==1?"AVAILABLE":"NOT_CAPTURED");if(captured.closeCalls==1)operands.addProperty("closeEnoughReturn",captured.closeEnough);
                data.add("operands",operands);data.addProperty("resultScope","ORIGINAL_PRIVATE_REACHED_TARGET_BOOLEAN_NOT_ARRIVAL");return data;
            });}return result;
        }finally {session.reachedFrame=active==session?previous:null;session.reachedDepth=depth;}
    }
    public static int originalComputeDistance(MoveToTargetSink behavior,BlockPos target,Vec3i ownerPosition) {
        Session session=active;ReachedFrame frame=session==null?null:session.reachedFrame;int result=target.distManhattan(ownerPosition);
        if(session!=null){if(session.reachedFrame==frame&&session.reachedReady(frame)&&frame.compute.behavior==behavior){frame.distance=result;if(frame.distanceCalls<2)frame.distanceCalls++;}}
        return result;
    }
    public static int originalComputeCloseEnough(MoveToTargetSink behavior,WalkTarget target) {
        Session session=active;ReachedFrame frame=session==null?null:session.reachedFrame;int result=target.getCloseEnoughDist();
        if(session!=null){if(session.reachedFrame==frame&&session.reachedReady(frame)&&frame.compute.behavior==behavior&&frame.compute.target==target){frame.closeEnough=result;if(frame.closeCalls<2)frame.closeCalls++;}}
        return result;
    }
    public static boolean originalComputeCanReach(MoveToTargetSink behavior,Path path) {
        Session session=active;ComputeFrame frame=session==null?null:session.computeFrame;
        boolean result=path.canReach();
        if(session!=null&&session.computeFrame==frame&&session.computeReady(frame)&&frame.behavior==behavior)session.record("BRAIN_PATH_COMPUTE_CONDITION_RETURN","MoveToTargetSink.tryComputePath.Path.canReach.AFTER",()->{
            JsonObject data=computeData(session,frame);data.addProperty("condition","PATH_CAN_REACH");data.addProperty("result",result);
            Path cached=(Path)KneekuraDebugDecisionSnapshot.read(MoveToTargetSink.class,"path",behavior);
            data.add("argumentPath",session.snapshot.pathReferenceFact(path));data.add("cachedSinkPath",session.snapshot.pathReferenceFact(cached));data.addProperty("argumentMatchesCachedSinkPath",path==cached);
            data.addProperty("referenceScope","RAW_ARGUMENT_VS_CACHED_SINK_PATH_AFTER_ORIGINAL_RETURN");
            data.addProperty("resultScope","ORIGINAL_VIRTUAL_PATH_CAN_REACH_BOOLEAN_NOT_COMPUTE_SUCCESS_OR_ARRIVAL");return data;
        });return result;
    }
    public static Path originalBrainCreatePath(PathNavigation navigation,BlockPos target,int accuracy) {
        return originalBrainCreate(navigation,"INITIAL",()->blockArguments(target,accuracy),()->navigation.createPath(target,accuracy));
    }
    public static Path originalBrainFallbackPath(PathNavigation navigation,double x,double y,double z,int accuracy) {
        return originalBrainCreate(navigation,"FALLBACK",()->{
            JsonObject args=new JsonObject();args.addProperty("kind","DDD_I");finite(args,"x",x);finite(args,"y",y);finite(args,"z",z);args.addProperty("accuracy",accuracy);return args;
        },()->navigation.createPath(x,y,z,accuracy));
    }
    private static JsonObject blockArguments(BlockPos target,int accuracy)throws ReflectiveOperationException {
        JsonObject args=new JsonObject();args.addProperty("kind","BLOCK_POS_I");args.addProperty("accuracy",accuracy);args.addProperty("present",target!=null);
        if(target!=null){args.addProperty("className",label(target.getClass().getName()));
            boolean known=target.getClass()==BlockPos.class||target.getClass()==BlockPos.MutableBlockPos.class;args.addProperty("positionStatus",known?"AVAILABLE":"NOT_EXPOSED");
            if(known)for(String axis:List.of("x","y","z"))args.addProperty(axis,(Integer)KneekuraDebugDecisionSnapshot.read(Vec3i.class,axis,target));
        }return args;
    }
    private static Path originalBrainCreate(PathNavigation navigation,String site,Data arguments,Supplier<Path> original) {
        Session session=active;if(session==null||session.thread!=Thread.currentThread())return original.get();
        ComputeFrame compute=session.computeFrame;CreateFrame previous=session.createFrame;FinderFrame previousFinder=session.finderFrame;
        int depth=session.createDepth;session.createDepth++;CreateFrame frame=null;
        // Clear even an unsupported/capped second call; never attribute its store to an earlier return.
        if(compute!=null)compute.lastCreate=null;
        try {
            if(session.computeReady(compute)&&compute.navigation==navigation&&compute.nextCreate<8&&session.createDepth<=8){
                try {frame=new CreateFrame(compute,compute.id+":create:"+(++compute.nextCreate),site,arguments.read());}
                catch(ReflectiveOperationException|RuntimeException|LinkageError error){session.budget.close("CREATE_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());}
            }
            session.createFrame=frame;session.finderFrame=null;Path path=original.get();
            if(frame!=null&&session.computeReady(compute)){
                frame.path=path;frame.returned=true;compute.lastCreate=frame;CreateFrame captured=frame;
                session.record("BRAIN_PATH_CREATE_RETURN","MoveToTargetSink.PathNavigation.createPath.AFTER",()->{
                    JsonObject data=computeData(session,compute);data.addProperty("createInvocationId",captured.id);data.addProperty("createSite",site);data.add("arguments",captured.arguments.deepCopy());
                    data.add("returnedPath",session.snapshot.pathFact(path));Path cached=(Path)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"path",navigation);
                    data.add("navigationPath",session.snapshot.pathReferenceFact(cached));data.addProperty("returnedMatchesNavigationPath",path==cached);
                    JsonArray children=new JsonArray();captured.finderIds.forEach(children::add);data.add("capturedFinderInvocationIds",children);data.addProperty("capturedFinderInvocationsTruncated",captured.truncated);
                    data.addProperty("searchScope","CAPTURED_ORIGINAL_BASE_NAVIGATION_FINDER_CALLS_ONLY_EMPTY_IS_NOT_NO_SEARCH_PROOF");
                    data.addProperty("returnScope","ORIGINAL_CREATE_PATH_NORMAL_RETURN_NOT_ADOPTION_OR_ARRIVAL");return data;
                });
            }return path;
        }finally {session.createFrame=active==session?previous:null;session.finderFrame=active==session?previousFinder:null;session.createDepth=depth;}
    }
    /** Called AFTER the two genuine PUTFIELD instructions; never replaces the assignment. */
    public static void brainComputePathWrite(MoveToTargetSink behavior,Mob owner,WalkTarget target,long game,String site) {
        Session session=active;if(session==null)return;ComputeFrame frame=session.computeFrame;
        if(!session.computeReady(frame)||frame.behavior!=behavior||frame.owner!=owner||frame.target!=target||frame.gameTime!=game||!Set.of("INITIAL","FALLBACK").contains(site))return;
        session.record("BRAIN_PATH_COMPUTE_PATH_WRITE_CHECKPOINT","MoveToTargetSink.tryComputePath.path.PUTFIELD.AFTER",()->{
            JsonObject data=computeData(session,frame);data.addProperty("writeSite",site);data.addProperty("writeScope","AFTER_ORIGINAL_SINK_PATH_PUTFIELD_NOT_NAVIGATION_ADOPTION");
            Path stored=(Path)KneekuraDebugDecisionSnapshot.read(MoveToTargetSink.class,"path",behavior);data.add("sinkPath",session.snapshot.pathFact(stored));
            CreateFrame create=frame.lastCreate;addCreateRelation(session,data,create!=null&&create.site.equals(site)?create:null,stored);return data;
        });
    }
    public static Path originalBrainFinder(PathNavigation navigation,PathFinder finder,PathNavigationRegion region,Mob owner,Set<BlockPos> targets,float range,int accuracy,float multiplier) {
        return originalBrainFinderCall(navigation,finder,owner,range,accuracy,multiplier,targets==null?null:targets.getClass().getName(),()->finder.findPath(region,owner,targets,range,accuracy,multiplier));
    }
    private static Path originalBrainFinderCall(PathNavigation navigation,PathFinder finder,Mob owner,float range,int accuracy,float multiplier,String targetsClass,Supplier<Path> original) {
        Session session=active;if(session==null||session.thread!=Thread.currentThread())return original.get();
        CreateFrame create=session.createFrame;FinderFrame previous=session.finderFrame;int depth=session.finderDepth;session.finderDepth++;FinderFrame frame=null;
        try {
            if(create!=null&&session.computeReady(create.compute)&&create.compute.navigation==navigation&&create.compute.owner==owner&&session.finderDepth<=8){
                try {if(finder!=null&&KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"pathFinder",navigation)==finder){
                    if(create.finderIds.size()<8){frame=new FinderFrame(create,finder,create.id+":finder:"+(create.finderIds.size()+1));create.finderIds.add(frame.id);}else create.truncated=true;
                }}catch(ReflectiveOperationException|RuntimeException|LinkageError error){session.budget.close("FINDER_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());}
            }
            session.finderFrame=frame;Path path=original.get();
            if(frame!=null&&session.computeReady(create.compute)){FinderFrame captured=frame;session.record("BRAIN_PATH_FINDER_RETURN","PathNavigation.createPath.PathFinder.findPath.AFTER",()->{
                JsonObject data=computeData(session,create.compute);data.addProperty("createInvocationId",create.id);data.addProperty("createSite",create.site);data.addProperty("finderInvocationId",captured.id);
                data.addProperty("finderClass",label(finder.getClass().getName()));
                data.addProperty("targetSetClass",targetsClass==null?null:label(targetsClass));data.addProperty("targetContentsStatus","NOT_EXPOSED");
                finite(data,"followRange",range);data.addProperty("accuracy",accuracy);finite(data,"maxVisitedNodesMultiplier",multiplier);
                data.add("returnedPath",session.snapshot.pathFact(path));data.addProperty("searchIdStatus",captured.searchId==null?"NOT_CAPTURED":"AVAILABLE");if(captured.searchId!=null)data.addProperty("searchId",captured.searchId);
                data.addProperty("returnScope","ORIGINAL_NAVIGATION_SOURCE_FINDER_NORMAL_RETURN_NOT_ADOPTION_OR_ARRIVAL");return data;
            });}return path;
        }finally {session.finderFrame=active==session?previous:null;session.finderDepth=depth;}
    }
    private static JsonObject computeData(Session session,ComputeFrame frame) {
        JsonObject data=new JsonObject();data.addProperty("sinkClass",label(frame.behavior.getClass().getName()));component(data,session,frame.behavior,"instanceIdentity");
        data.addProperty("computeInvocationId",frame.id);data.addProperty("callSite",frame.site);data.addProperty("gameTimeArgument",Long.toString(frame.gameTime));
        data.addProperty("walkTargetClass",label(frame.target.getClass().getName()));
        data.addProperty("enclosingSinkInvocationStatus",frame.sinkId==null?"NOT_CAPTURED":"AVAILABLE");if(frame.sinkId!=null)data.addProperty("enclosingSinkInvocationId",frame.sinkId);
        data.addProperty("enclosingTickStopInvocationStatus",frame.tickStopId==null?"NOT_CAPTURED":"AVAILABLE");if(frame.tickStopId!=null)data.addProperty("enclosingTickStopInvocationId",frame.tickStopId);
        data.addProperty("parentScope","CAPTURED_ENCLOSING_SOURCE_SCOPES_NOT_IMMEDIATE_CAUSE_OR_ADOPTION");
        data.addProperty("fieldScope","BASE_CACHED_FIELDS_AT_DECLARED_CAPTURE_BOUNDARY");data.addProperty("arrivalStatus","NOT_EXPOSED");data.addProperty("operandReasonStatus","NOT_EXPOSED");return data;
    }
    private static void addCreateRelation(Session session,JsonObject data,CreateFrame create,Path stored) {
        boolean known=create!=null&&create.returned;data.addProperty("createReturnStatus",known?"AVAILABLE":"NOT_CAPTURED");
        if(known){data.addProperty("lastCreateInvocationId",create.id);data.add("createdPath",session.snapshot.pathReferenceFact(create.path));data.addProperty("createdMatchesSinkPath",create.path==stored);}
        data.addProperty("referenceScope","RAW_RETURNED_VS_CACHED_PATH_REFERENCE_EQUALITY");
    }

    /** Original base return and later cached fields; a true boolean is neither arrival nor Path adoption. */
    public static void navigationMoveReturn(PathNavigation navigation,Path requested,double speed,boolean result) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()||!session.channels.contains("navigation_result"))return;
        try {
            if(!session.budget.allows(session.currentContext.get(),session.time.getAsLong()))return;
            Mob owner=(Mob)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"mob",navigation);
            if(!session.matches(owner)||KneekuraDebugDecisionSnapshot.read(Mob.class,"navigation",owner)!=navigation)return;
            session.record("NAVIGATION_MOVE_TO_RETURN","PathNavigation.moveTo(Path,double).RETURN",()->{
                Path cached=(Path)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"path",navigation);
                double cachedSpeed=(Double)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"speedModifier",navigation);
                JsonObject data=new JsonObject();data.addProperty("navigationClass",label(navigation.getClass().getName()));
                String identity=session.token(navigation);data.addProperty("instanceIdentity",identity);
                data.addProperty("instanceIdentityStatus",identity==null?"NOT_EXPOSED":"AVAILABLE");data.addProperty("result",result);
                if(Double.isFinite(speed))data.addProperty("requestedSpeed",speed);else data.addProperty("requestedSpeedStatus","NOT_EXPOSED");
                if(Double.isFinite(cachedSpeed))data.addProperty("cachedSpeed",cachedSpeed);else data.addProperty("cachedSpeedStatus","NOT_EXPOSED");
                data.addProperty("requestedMatchesCachedPath",requested==cached);
                JsonObject passed=session.snapshot.pathFact(requested);data.add("requestedPath",passed);
                data.add("cachedPath",requested==cached?passed.deepCopy():session.snapshot.pathFact(cached));
                data.addProperty("dispatchScope","BASE_PATHNAVIGATION_NORMAL_RETURN_NOT_FINAL_CUSTOM_OVERRIDE");
                data.addProperty("fieldScope","BASE_NAVIGATION_AND_EXACT_PATH_CACHED_FIELDS_AFTER_RETURN_AND_CAPTURE_GATES");
                data.addProperty("resultScope","ORIGINAL_BASE_METHOD_BOOLEAN_NOT_ARRIVAL");
                data.addProperty("referenceScope","RAW_ARGUMENT_VS_CACHED_PATH_REFERENCE_EQUALITY");
                data.addProperty("reasonStatus","NOT_EXPOSED");data.addProperty("arrivalStatus","NOT_EXPOSED");
                data.addProperty("searchRelationStatus","NOT_EXPOSED");return data;
            });
        }catch(ReflectiveOperationException|RuntimeException|LinkageError error){session.budget.close("NAVIGATION_CAPTURE_UNAVAILABLE:"+error.getClass().getSimpleName());}
    }
    /** Wrap the actual private loop; source delegates gather returns without replaying its iterators. */
    public static void originalBrainStartLoop(Brain<?> brain,ServerLevel level,LivingEntity owner,Runnable original) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()){original.run();return;}
        StartLoopFrame previous=session.startLoopFrame;int depth=session.startLoopDepth;session.startLoopDepth++;
        try {
            StartLoopFrame frame=session.startLoopBegin(brain,level,owner);session.startLoopFrame=frame;
            original.run();
            if(session.startLoopReady(frame))session.record("BRAIN_PATH_START_LOOP_RETURN","Brain.startEachNonRunningBehavior.AFTER",()->startLoopData(session,frame));
        }finally{session.startLoopFrame=active==session?previous:null;session.startLoopDepth=depth;}
    }
    public static boolean originalBrainStartActivity(Brain<?> brain,Set<?> activities,Object requested,ServerLevel level,LivingEntity owner) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread())return activities.contains(requested);
        StartLoopFrame frame=session.startLoopFrame;
        boolean supported=session.startLoopReady(frame)&&frame.brain==brain&&frame.level==level&&frame.owner==owner&&frame.activeActivities==activities;
        if(frame!=null){frame.activity=null;frame.control=null;if(!supported)frame.invalid=true;}
        session.startLoopFrame=null;
        try {
            boolean result=activities.contains(requested);
            if(supported&&session.startLoopReady(frame)){
                int index=frame.count=Math.min(9,frame.count+1);
                if(index>8)frame.truncated=true;
                else {frame.activity=new StartActivityCapture(requested,result,index);frame.activities.add(frame.activity);}
            }return result;
        }finally{session.startLoopFrame=active==session?frame:null;}
    }
    public static Behavior.Status originalBrainStartStatus(Brain<?> brain,BehaviorControl<?> control,ServerLevel level,LivingEntity owner) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread())return control.getStatus();
        StartLoopFrame frame=session.startLoopFrame;StartActivityCapture activity=frame==null?null:frame.activity;
        boolean source=session.startLoopReady(frame)&&frame.brain==brain&&frame.level==level&&frame.owner==owner;
        boolean supported=source&&activity!=null&&activity.result;
        if(frame!=null){frame.control=null;if(!source||activity!=null&&!activity.result)frame.invalid=true;}
        session.startLoopFrame=null;
        try {
            Behavior.Status status=control.getStatus();
            if(supported&&session.startLoopReady(frame)){
                int index=activity.count=Math.min(9,activity.count+1);
                if(index>8)activity.truncated=true;
                else {frame.control=new StartControlCapture(control,status,index);activity.controls.add(frame.control);}
            }return status;
        }finally{session.startLoopFrame=active==session?frame:null;}
    }
    private static JsonObject startLoopData(Session session,StartLoopFrame frame) {
        JsonObject data=new JsonObject();data.addProperty("brainClass",label(frame.brain.getClass().getName()));component(data,session,frame.brain,"instanceIdentity");
        data.addProperty("loopInvocationId",frame.id);data.addProperty("sourceGameTimeStatus",frame.gameTime==null?"NOT_CAPTURED":"AVAILABLE");
        if(frame.gameTime!=null)data.addProperty("gameTimeArgument",Long.toString(frame.gameTime));data.addProperty("priorityStatus","NOT_EXPOSED");JsonArray activities=new JsonArray();
        for(StartActivityCapture activity:frame.activities){JsonObject a=new JsonObject();a.addProperty("activityIndex",activity.index);
            String name=activity.requested==Activity.CORE?"CORE":activity.requested==Activity.IDLE?"IDLE":activity.requested==Activity.REST?"REST":activity.requested==Activity.WORK?"WORK":
                activity.requested==Activity.MEET?"MEET":activity.requested==Activity.PLAY?"PLAY":activity.requested==Activity.FIGHT?"FIGHT":null;
            a.addProperty("activityStatus",name==null?"NOT_EXPOSED":"AVAILABLE");if(name!=null)a.addProperty("activity",name);a.addProperty("result",activity.result);JsonArray controls=new JsonArray();
            for(StartControlCapture control:activity.controls){JsonObject c=new JsonObject();c.addProperty("controlIndex",control.index);c.addProperty("controlClass",label(control.control.getClass().getName()));component(c,session,control.control,"instanceIdentity");
                c.addProperty("status",control.status==Behavior.Status.STOPPED?"STOPPED":control.status==Behavior.Status.RUNNING?"RUNNING":"NOT_EXPOSED");
                c.addProperty("tryStartStatus",control.result==null?"NOT_CALLED":"NORMAL_RETURN");if(control.result!=null)c.addProperty("tryStartResult",control.result);if(control.child!=null)c.addProperty("capturedTryStartInvocationId",control.child);controls.add(c);
            }a.add("controls",controls);a.addProperty("controlsTruncated",activity.truncated);activities.add(a);
        }data.add("activities",activities);data.addProperty("activitiesTruncated",frame.truncated);
        data.addProperty("iterationScope","ORIGINAL_ACTIVITY_AND_CONTROL_RETURN_PREFIX_NOT_ALL_ELIGIBILITY_REASONS");data.addProperty("returnScope","NORMAL_ORIGINAL_PRIVATE_START_LOOP_NOT_ALL_STARTS_OR_ARRIVAL");
        data.addProperty("eligibilityReasonStatus","NOT_EXPOSED");data.addProperty("arrivalStatus","NOT_EXPOSED");return data;
    }
    /** Source Brain loop interface call. Unknown controls and all OFF/throw paths still execute once. */
    @SuppressWarnings({"rawtypes","unchecked"})
    public static boolean originalBrainTryStart(Brain<?> brain,BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long gameTime) {
        return originalBrainStartCall(brain,control,level,owner,gameTime,()->((BehaviorControl)control).tryStart(level,owner,gameTime));
    }
    private static boolean originalBrainStartCall(Brain<?> brain,BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long gameTime,BooleanSupplier original) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread())return original.getAsBoolean();
        StartLoopFrame loop=session.startLoopFrame;StartControlCapture captured=loop==null?null:loop.control;
        boolean loopSource=session.startLoopReady(loop)&&loop.brain==brain&&loop.level==level&&loop.owner==owner;
        boolean loopSupported=loopSource&&captured!=null&&captured.control==control&&captured.status==Behavior.Status.STOPPED&&captured.result==null;
        if(loop!=null&&(!loopSource||captured!=null&&!loopSupported))loop.invalid=true;
        session.startLoopFrame=null;
        StartFrame previous=session.startFrame;int depth=session.startDepth;session.startDepth++;
        try {
            StartFrame frame=session.startBegin(brain,control,level,owner,gameTime);session.startFrame=frame;
            boolean result=original.getAsBoolean();
            if(loopSource&&session.startLoopReady(loop)){
                if(loop.gameTime!=null&&loop.gameTime.longValue()!=gameTime)loop.invalid=true;
                else {loop.gameTime=gameTime;if(loopSupported){captured.result=result;captured.child=frame==null?null:frame.id;}}
            }
            if(session.startReady(frame))session.record("BRAIN_PATH_TRY_START_RETURN","Brain.startEachNonRunningBehavior.tryStart.AFTER",()->{
                JsonObject data=startData(session,frame);data.addProperty("result",result);
                data.addProperty("resultScope","ORIGINAL_INTERFACE_TRY_START_BOOLEAN_NOT_NAVIGATION_SUCCESS_OR_ARRIVAL");return data;
            });return result;
        }finally{session.startFrame=active==session?previous:null;session.startDepth=depth;session.startLoopFrame=active==session?loop:null;}
    }
    public static boolean originalBrainStartCondition(Behavior<?> behavior,String condition,ServerLevel level,LivingEntity owner,BooleanSupplier original) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread())return original.getAsBoolean();
        StartFrame previous=session.startFrame,frame=startFrame(session,behavior);
        boolean supported=frame!=null&&frame.owner==owner&&Set.of("HAS_REQUIRED_MEMORIES","CHECK_EXTRA_START").contains(condition)&&
            (condition.equals("HAS_REQUIRED_MEMORIES")||frame.level==level);
        StartConditionCapture capture=supported?new StartConditionCapture(condition):null,old=supported?frame.condition:null;
        if(supported&&condition.equals("HAS_REQUIRED_MEMORIES")&&session.nextMemoryRequirement<256)
            capture.requirement=new MemoryRequirementCapture("memory-requirement:"+session.budget.context().selectionRevision()+":"+(++session.nextMemoryRequirement));
        if(supported)frame.condition=capture;else session.startFrame=null;
        try {
            boolean result=original.getAsBoolean();
            if(supported&&session.startFrame==frame&&session.startReady(frame)&&capture.requirement!=null&&!capture.requirement.unsupportedSource&&!capture.requirement.checks.isEmpty())
                session.record("BRAIN_PATH_MEMORY_REQUIREMENT_RETURN","Behavior.hasRequiredMemories.checkMemory.AFTER",()->{
                    JsonObject data=startData(session,frame);data.addProperty("requirementInvocationId",capture.requirement.id);
                    data.addProperty("condition","HAS_REQUIRED_MEMORIES");data.addProperty("result",result);JsonArray checks=new JsonArray();capture.requirement.checks.forEach(checks::add);
                    data.add("checks",checks);data.addProperty("checksTruncated",capture.requirement.truncated);
                    data.addProperty("checkScope","ORIGINAL_VIRTUAL_CHECK_MEMORY_RETURNS_PREFIX_NOT_REPLAY_OR_ALL_ELIGIBILITY_REASONS");return data;
                });
            if(supported&&session.startFrame==frame&&session.startReady(frame))session.record("BRAIN_PATH_START_CONDITION_RETURN",
                "Behavior.tryStart."+(condition.equals("HAS_REQUIRED_MEMORIES")?"hasRequiredMemories":"checkExtraStartConditions")+".AFTER",()->{
                    JsonObject data=startData(session,frame);data.addProperty("condition",condition);data.addProperty("result",result);
                    JsonArray ids=new JsonArray();capture.computes.forEach(ids::add);data.add("capturedComputeInvocationIds",ids);
                    data.addProperty("capturedComputeInvocationsTruncated",capture.truncated);
                    data.addProperty("childScope","DIRECT_CAPTURED_PRIVATE_COMPUTE_SCOPES_NOT_COMPLETION_OR_FULL_CHILDREN");
                    data.addProperty("resultScope","ORIGINAL_VIRTUAL_START_CONDITION_BOOLEAN_NOT_INDIVIDUAL_MEMORY_REASONS");return data;
                });return result;
        }finally{if(supported)frame.condition=active==session?old:null;session.startFrame=active==session?previous:null;}
    }
    /** The original requirement-loop virtual call; no additional memory query or owner getter. */
    public static boolean originalBrainMemoryCheck(Behavior<?> behavior,Brain<?> brain,MemoryModuleType<?> module,MemoryStatus requested,LivingEntity owner) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread())return brain.checkMemory(module,requested);
        StartFrame frame=session.startFrame;StartConditionCapture condition=frame==null?null:frame.condition;
        MemoryRequirementCapture previous=condition==null?null:condition.requirement;
        boolean supported=previous!=null&&frame.behavior==behavior&&frame.brain==brain&&frame.owner==owner&&
            condition.condition.equals("HAS_REQUIRED_MEMORIES")&&session.startReady(frame);
        if(previous!=null&&!supported)previous.unsupportedSource=true;
        int index=supported?(previous.count=Math.min(9,previous.count+1)):0;
        if(condition!=null)condition.requirement=null;
        MemorySourceFrame oldSource=session.memorySourceFrame;int sourceDepth=session.memorySourceDepth;session.memorySourceDepth++;
        MemorySourceFrame source=supported?session.memorySourceBegin(brain,module,requested,index,frame,condition,previous,null):null;session.memorySourceFrame=source;
        try {
            boolean result=brain.checkMemory(module,requested);memorySourceReturn(session,source,result);
            if(supported&&active==session&&session.startFrame==frame&&frame.condition==condition&&session.startReady(frame)){
                if(index>8)previous.truncated=true;
                else {JsonObject check=new JsonObject();check.addProperty("checkIndex",index);
                    String name=module==MemoryModuleType.PATH?"PATH":module==MemoryModuleType.WALK_TARGET?"WALK_TARGET":
                        module==MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE?"CANT_REACH_WALK_TARGET_SINCE":null;
                    check.addProperty("memoryModuleStatus",name==null?"NOT_EXPOSED":"AVAILABLE");if(name!=null)check.addProperty("memoryModule",name);
                    check.addProperty("requestedMemoryStatus",requested==MemoryStatus.REGISTERED?"REGISTERED":requested==MemoryStatus.VALUE_PRESENT?"VALUE_PRESENT":
                        requested==MemoryStatus.VALUE_ABSENT?"VALUE_ABSENT":"NOT_EXPOSED");check.addProperty("result",result);previous.checks.add(check);
                }
            }return result;
        }finally{session.memorySourceFrame=active==session?oldSource:null;session.memorySourceDepth=sourceDepth;if(condition!=null)condition.requirement=active==session&&session.startFrame==frame&&frame.condition==condition?previous:null;}
    }
    public static void originalBrainStartDispatch(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long gameTime,Runnable original) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()){original.run();return;}
        StartFrame previous=session.startFrame,frame=startFrame(session,behavior);
        boolean supported=frame!=null&&frame.owner==owner&&frame.level==level&&frame.gameTime==gameTime;
        DispatchCapture capture=supported?new DispatchCapture("START"):null,old=supported?frame.dispatch:null;
        if(supported)frame.dispatch=capture;else session.startFrame=null;
        try {
            original.run();
            if(supported&&session.startFrame==frame&&session.startReady(frame))session.record("BRAIN_PATH_START_DISPATCH_RETURN","Behavior.tryStart.start.AFTER",()->{
                JsonObject data=startData(session,frame);data.addProperty("branch","START");JsonArray ids=new JsonArray();capture.children.forEach(ids::add);
                data.add("capturedSinkInvocationIds",ids);data.addProperty("capturedSinkInvocationsTruncated",capture.truncated);
                data.addProperty("childScope","DIRECT_CAPTURED_CONCRETE_CALL_SCOPES_NOT_COMPLETION_OR_FULL_CHILDREN");
                data.addProperty("returnScope","NORMAL_ORIGINAL_START_VOID_NOT_NAVIGATION_SUCCESS_OR_ARRIVAL");return data;
            });
        }finally{if(supported)frame.dispatch=active==session?old:null;session.startFrame=active==session?previous:null;}
    }
    private static StartFrame startFrame(Session session,Behavior<?> behavior) {
        if(session==null||session.thread!=Thread.currentThread())return null;StartFrame frame=session.startFrame;
        return frame!=null&&frame.behavior==behavior&&session.startReady(frame)?frame:null;
    }
    private static JsonObject startData(Session session,StartFrame frame) {
        JsonObject data=new JsonObject();data.addProperty("sinkClass",label(frame.behavior.getClass().getName()));component(data,session,frame.behavior,"instanceIdentity");
        data.addProperty("tryStartInvocationId",frame.id);data.addProperty("gameTimeArgument",Long.toString(frame.gameTime));
        data.addProperty("dispatchScope","ORIGINAL_BRAIN_NON_RUNNING_BEHAVIOR_INTERFACE_CALL_EXACT_SINK");
        data.addProperty("operandReasonStatus","NOT_EXPOSED");data.addProperty("arrivalStatus","NOT_EXPOSED");data.addProperty("searchRelationStatus","NOT_EXPOSED");return data;
    }
    @SuppressWarnings({"rawtypes","unchecked"})
    public static void originalBrainTickOrStop(Brain<?> brain,BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long gameTime) {
        originalBrainCall(brain,control,level,owner,gameTime,()->((BehaviorControl)control).tickOrStop(level,owner,gameTime));
    }
    private static void originalBrainCall(Brain<?> brain,BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long gameTime,Runnable original) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()){original.run();return;}
        TickStopFrame previous=session.tickStopFrame;int depth=session.tickStopDepth;session.tickStopDepth++;
        try {session.tickStopFrame=session.tickStopBegin(brain,control,level,owner,gameTime);original.run();}
        finally {session.tickStopFrame=active==session?previous:null;session.tickStopDepth=depth;}
    }
    public static boolean originalBrainCondition(Behavior<?> behavior,long gameTime,String condition,ServerLevel level,LivingEntity owner,BooleanSupplier original) {
        boolean result=original.getAsBoolean();Session session=active;TickStopFrame frame=tickStopFrame(session,behavior,gameTime);
        if(frame!=null&&Set.of("TIMED_OUT","CAN_STILL_USE").contains(condition)&&(condition.equals("TIMED_OUT")||frame.owner==owner&&frame.level==level))session.record("BRAIN_PATH_CONDITION_RETURN",
            "Behavior.tickOrStop."+(condition.equals("TIMED_OUT")?"timedOut":"canStillUse")+".AFTER",()->{
                JsonObject data=tickStopData(session,frame);data.addProperty("condition",condition);data.addProperty("result",result);
                data.addProperty("resultScope","ORIGINAL_VIRTUAL_BOOLEAN_NOT_INDIVIDUAL_OPERAND_REASONS");return data;
            });return result;
    }
    public static void originalBrainDispatch(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long gameTime,String branch,Runnable original) {
        Session session=active;TickStopFrame frame=tickStopFrame(session,behavior,gameTime);
        if(frame==null||frame.owner!=owner||frame.level!=level||!Set.of("TICK","STOP").contains(branch)){original.run();return;}
        DispatchCapture capture=new DispatchCapture(branch),previous=frame.dispatch;frame.dispatch=capture;
        try {
            original.run();
            if(session.tickStopReady(frame))session.record("BRAIN_PATH_DISPATCH_RETURN","Behavior.tickOrStop."+(branch.equals("TICK")?"tick":"doStop")+".AFTER",()->{
                JsonObject data=tickStopData(session,frame);data.addProperty("branch",branch);JsonArray children=new JsonArray();capture.children.forEach(children::add);
                data.add("capturedSinkInvocationIds",children);data.addProperty("capturedSinkInvocationsTruncated",capture.truncated);
                data.addProperty("childScope","DIRECT_CAPTURED_CONCRETE_CALL_SCOPES_NOT_COMPLETION_OR_FULL_CHILDREN");
                data.addProperty("returnScope","NORMAL_ORIGINAL_DISPATCH_VOID_NOT_ARRIVAL");return data;
            });
        }finally{frame.dispatch=active==session?previous:null;}
    }
    private static TickStopFrame tickStopFrame(Session session,Behavior<?> behavior,long gameTime) {
        if(session==null||session.thread!=Thread.currentThread())return null;TickStopFrame frame=session.tickStopFrame;
        return frame!=null&&frame.behavior==behavior&&frame.gameTime==gameTime&&session.tickStopReady(frame)?frame:null;
    }
    private static JsonObject tickStopData(Session session,TickStopFrame frame) {
        JsonObject data=new JsonObject();data.addProperty("sinkClass",label(frame.behavior.getClass().getName()));component(data,session,frame.behavior,"instanceIdentity");
        data.addProperty("tickOrStopInvocationId",frame.id);data.addProperty("gameTimeArgument",Long.toString(frame.gameTime));
        data.addProperty("dispatchScope","ORIGINAL_BRAIN_RUNNING_BEHAVIOR_INTERFACE_CALL_EXACT_SINK");data.addProperty("operandReasonStatus","NOT_EXPOSED");
        data.addProperty("arrivalStatus","NOT_EXPOSED");data.addProperty("searchRelationStatus","NOT_EXPOSED");return data;
    }
    /** Known sink bridge/restart call. The protected original delegate runs once, including OFF/throw. */
    public static void originalSinkCall(MoveToTargetSink behavior,Mob owner,long gameTime,String site,Runnable original) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()){original.run();return;}
        SinkFrame previous=session.sinkFrame;int previousDepth=session.sinkDepth;session.sinkDepth++;
        try {
            SinkFrame frame=session.sinkBegin(behavior,owner,gameTime,site,previous);
            session.sinkFrame=frame; // Never attribute an unsupported nested call to the captured parent.
            TickStopFrame caller=session.tickStopFrame;
            if(frame!=null&&caller!=null&&caller.behavior==behavior&&caller.owner==owner&&caller.brain==frame.brain()&&
                caller.navigation==frame.navigation()&&caller.gameTime==gameTime&&session.tickStopReady(caller)&&caller.dispatch!=null&&
                (caller.dispatch.branch.equals("STOP")?site.equals("STOP_FROM_BRIDGE"):Set.of("TICK_FROM_BRIDGE","START_FROM_TICK").contains(site))){
                if(caller.dispatch.children.size()<8)caller.dispatch.children.add(frame.id());else caller.dispatch.truncated=true;
            }
            StartFrame starter=session.startFrame;
            if(frame!=null&&starter!=null&&starter.behavior==behavior&&starter.owner==owner&&starter.brain==frame.brain()&&starter.navigation==frame.navigation()&&
                starter.gameTime==gameTime&&session.startReady(starter)&&starter.dispatch!=null&&site.equals("START_FROM_BRIDGE")){
                if(starter.dispatch.children.size()<8)starter.dispatch.children.add(frame.id());else starter.dispatch.truncated=true;
            }
            original.run();
            if(frame!=null&&session.sinkReady(frame))session.record("BRAIN_PATH_SINK_RETURN","MoveToTargetSink."+site+".AFTER",()->{
                JsonObject data=sinkData(session,frame);data.add("before",frame.before().deepCopy());
                data.add("after",sinkState(session,behavior,frame.brain(),frame.navigation(),frame.callSite().equals("STOP_FROM_BRIDGE")));
                data.addProperty("preCallObserverCostNanos",frame.preCallCost());
                data.addProperty("beforeScope","BEFORE_ORIGINAL_CALL_AFTER_CAPTURE_GATES");
                data.addProperty("afterScope","AFTER_ORIGINAL_RETURN_AND_CAPTURE_GATES");
                data.addProperty("returnScope","NORMAL_ORIGINAL_VOID_RETURN_NOT_MOVEMENT_SUCCESS");return data;
            });
        }finally{session.sinkFrame=active==session?previous:null;session.sinkDepth=previousDepth;}
    }
    @SuppressWarnings({"rawtypes","unchecked"})
    public static void originalSinkPathWrite(Brain<?> brain,MemoryModuleType<?> module,Object requested,MoveToTargetSink behavior,String site) {
        brain.setMemory((MemoryModuleType)module,requested);
        Session session=active;SinkFrame frame=sinkFrame(session,behavior);
        if(frame==null||frame.callSite().equals("STOP_FROM_BRIDGE")||frame.brain()!=brain||module!=MemoryModuleType.PATH||!(requested==null||requested instanceof Path)||
            !(frame.callSite().equals("TICK_FROM_BRIDGE")?"TICK_PATH_RECONCILE":"START_PATH_WRITE").equals(site))return;
        session.record("BRAIN_PATH_MEMORY_WRITE_RETURN","MoveToTargetSink."+site+".Brain.setMemory.AFTER",()->{
            JsonObject data=sinkData(session,frame);data.addProperty("brainClass",label(brain.getClass().getName()));
            component(data,session,brain,"brainIdentity");var cached=session.snapshot.pathMemoryReference(brain);
            data.add("requestedPath",session.snapshot.pathFact((Path)requested));data.add("memoryAtReturn",cached.data());
            if(cached.known())data.addProperty("requestedMatchesCachedMemory",requested==cached.path());
            else data.addProperty("requestedMatchesCachedMemoryStatus","NOT_EXPOSED");
            data.addProperty("writeSite",site);data.addProperty("returnScope","ORIGINAL_VIRTUAL_PATH_MEMORY_WRITE_NORMAL_RETURN_NOT_RETENTION_SUCCESS");
            data.addProperty("referenceScope","RAW_ARGUMENT_VS_CACHED_MEMORY_VALUE_REFERENCE_NOT_WRITE_SUCCESS");return data;
        });
    }
    public static boolean originalSinkMoveTo(PathNavigation navigation,Path requested,double speed,MoveToTargetSink behavior) {
        boolean result=navigation.moveTo(requested,speed);
        Session session=active;SinkFrame frame=sinkFrame(session,behavior);
        if(frame!=null&&frame.navigation()==navigation&&Set.of("START_FROM_BRIDGE","START_FROM_TICK").contains(frame.callSite()))session.record(
            "BRAIN_PATH_NAVIGATION_RETURN","MoveToTargetSink.start.PathNavigation.moveTo.AFTER",()->{
                JsonObject data=sinkData(session,frame);data.addProperty("navigationClass",label(navigation.getClass().getName()));
                component(data,session,navigation,"navigationIdentity");data.addProperty("result",result);
                finite(data,"requestedSpeed",speed);finite(data,"cachedSpeed",(Double)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"speedModifier",navigation));
                Path cached=(Path)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"path",navigation);
                data.addProperty("requestedMatchesCachedPath",requested==cached);JsonObject passed=session.snapshot.pathFact(requested);
                data.add("requestedPath",passed);data.add("cachedPath",requested==cached?passed.deepCopy():session.snapshot.pathFact(cached));
                data.add("brainPathAtReturn",session.snapshot.pathMemoryReference(frame.brain()).data());
                data.addProperty("returnScope","ORIGINAL_VIRTUAL_MOVE_TO_RETURN_AT_SINK_CALL_SITE_NOT_ARRIVAL");
                data.addProperty("referenceScope","RAW_ARGUMENT_VS_CACHED_PATH_REFERENCE_EQUALITY");return data;
            });
        return result;
    }
    public static void originalSinkNavigationStop(PathNavigation navigation,MoveToTargetSink behavior) {
        navigation.stop();
        Session session=active;SinkFrame frame=sinkFrame(session,behavior);
        if(frame!=null&&frame.navigation()==navigation&&frame.callSite().equals("STOP_FROM_BRIDGE"))session.record(
            "BRAIN_PATH_NAVIGATION_STOP_RETURN","MoveToTargetSink.stop.PathNavigation.stop.AFTER",()->{
                JsonObject data=sinkData(session,frame);data.addProperty("navigationClass",label(navigation.getClass().getName()));
                component(data,session,navigation,"navigationIdentity");
                data.add("cachedPath",session.snapshot.pathFact((Path)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"path",navigation)));
                finite(data,"cachedSpeed",(Double)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"speedModifier",navigation));
                data.add("brainPathAtReturn",session.snapshot.pathMemoryReference(frame.brain()).data());
                data.addProperty("returnScope","ORIGINAL_VIRTUAL_STOP_NORMAL_RETURN_NOT_ARRIVAL_OR_PATH_CLEAR_SUCCESS");return data;
            });
    }
    @SuppressWarnings({"rawtypes","unchecked"})
    public static void originalSinkMemoryErase(Brain<?> brain,MemoryModuleType<?> module,MoveToTargetSink behavior) {
        brain.eraseMemory((MemoryModuleType)module);
        Session session=active;SinkFrame frame=sinkFrame(session,behavior);
        if(frame!=null&&frame.brain()==brain&&frame.callSite().equals("STOP_FROM_BRIDGE")&&
            (module==MemoryModuleType.PATH||module==MemoryModuleType.WALK_TARGET))session.record(
                "BRAIN_PATH_MEMORY_ERASE_RETURN","MoveToTargetSink.stop.Brain.eraseMemory.AFTER",()->{
                    JsonObject data=sinkData(session,frame);data.addProperty("brainClass",label(brain.getClass().getName()));
                    component(data,session,brain,"brainIdentity");data.addProperty("memoryModule",module==MemoryModuleType.PATH?"PATH":"WALK_TARGET");
                    data.add("slotAtReturn",module==MemoryModuleType.PATH?session.snapshot.pathMemoryReference(brain).data():session.snapshot.walkTargetMemoryPresence(brain));
                    data.addProperty("memoryScope","BASE_CACHED_PATH_OR_WALK_TARGET_OPTIONAL_SLOT_AFTER_RETURN");
                    data.addProperty("returnScope","ORIGINAL_VIRTUAL_ERASE_NORMAL_RETURN_NOT_SLOT_CLEAR_SUCCESS");return data;
                });
    }
    private static SinkFrame sinkFrame(Session session,MoveToTargetSink behavior) {
        if(session==null||session.thread!=Thread.currentThread())return null;
        SinkFrame frame=session.sinkFrame;return frame!=null&&frame.behavior()==behavior&&session.sinkReady(frame)?frame:null;
    }
    private static void component(JsonObject data,Session session,Object value,String key) {
        String token=session.token(value);data.addProperty(key,token);data.addProperty(key+"Status",token==null?"NOT_EXPOSED":"AVAILABLE");
    }
    private static void finite(JsonObject data,String key,double value) {
        if(Double.isFinite(value))data.addProperty(key,value);else data.addProperty(key+"Status","NOT_EXPOSED");
    }
    private static JsonObject sinkData(Session session,SinkFrame frame) {
        JsonObject data=new JsonObject();data.addProperty("sinkClass",label(frame.behavior().getClass().getName()));
        component(data,session,frame.behavior(),"instanceIdentity");data.addProperty("sinkInvocationId",frame.id());
        data.addProperty("parentInvocationStatus",frame.parentId()==null?"NOT_CAPTURED":"AVAILABLE");
        if(frame.parentId()!=null)data.addProperty("parentInvocationId",frame.parentId());
        data.addProperty("callSite",frame.callSite());data.addProperty("gameTimeArgument",Long.toString(frame.gameTime()));
        data.addProperty("dispatchScope","ORIGINAL_KNOWN_SINK_CONCRETE_CALL_FROM_BRIDGE_OR_RESTART");
        data.addProperty("fieldScope","BASE_CACHED_FIELDS_AT_DECLARED_CAPTURE_BOUNDARY");
        data.addProperty("reasonStatus","NOT_EXPOSED");data.addProperty("arrivalStatus","NOT_EXPOSED");data.addProperty("searchRelationStatus","NOT_EXPOSED");return data;
    }
    private static JsonObject sinkState(Session session,MoveToTargetSink behavior,Brain<?> brain,PathNavigation navigation,boolean stop)throws ReflectiveOperationException {
        JsonObject state=new JsonObject();state.add("sinkPath",session.snapshot.pathReferenceFact((Path)KneekuraDebugDecisionSnapshot.read(MoveToTargetSink.class,"path",behavior)));
        state.add("brainPath",session.snapshot.pathMemoryReference(brain).data());
        state.add("navigationPath",session.snapshot.pathReferenceFact((Path)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"path",navigation)));
        finite(state,"sinkSpeed",(Float)KneekuraDebugDecisionSnapshot.read(MoveToTargetSink.class,"speedModifier",behavior));
        finite(state,"navigationSpeed",(Double)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"speedModifier",navigation));
        if(stop)state.add("walkTargetSlot",session.snapshot.walkTargetMemoryPresence(brain));return state;
    }
    /** Exact UpdateActivityFromSchedule call site. Virtual original executes once, including OFF/throw. */
    public static void originalActivityUpdate(Brain<?> brain,long day,long game) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()){brain.updateActivityFromSchedule(day,game);return;}
        ActivityFrame previous=session.activityFrame;
        int previousDepth=session.activityDepth;session.activityDepth++;
        try {
            ActivityFrame frame=session.activityBegin(brain);
            // Suppress an unsupported nested call rather than misattribute its callbacks to the caller.
            session.activityFrame=frame;
            brain.updateActivityFromSchedule(day,game);
            if(frame!=null&&active==session&&session.activityReady(brain))session.record(
                "BRAIN_ACTIVITY_UPDATE_RETURN","UpdateActivityFromSchedule.Brain.updateActivityFromSchedule.AFTER",()->{
                    JsonObject data=activityData(session,frame);
                    data.addProperty("dayTimeArgument",Long.toString(day));data.addProperty("gameTimeArgument",Long.toString(game));
                    data.add("before",frame.before().deepCopy());data.add("after",activityState(brain));
                    data.addProperty("preCallObserverCostNanos",frame.preCallCost());
                    data.addProperty("returnScope","NORMAL_VOID_RETURN_NOT_ACTIVITY_SUCCESS");return data;
                });
        } finally {session.activityFrame=active==session?previous:null;session.activityDepth=previousDepth;}
    }
    /** Delegate the original stateful query once; never evaluate Schedule to fill an observation. */
    public static Activity originalActivityQuery(Brain<?> brain,Schedule schedule,int tick) {
        Activity result=schedule.getActivityAt(tick);
        Session session=active;ActivityFrame frame=activityFrame(session,brain);
        if(frame!=null)session.record("BRAIN_ACTIVITY_QUERY_RETURN","Brain.updateActivityFromSchedule.Schedule.getActivityAt.AFTER",()->{
            JsonObject data=activityData(session,frame);data.addProperty("scheduleClass",label(schedule.getClass().getName()));
            String identity=session.token(schedule);data.addProperty("scheduleInstanceIdentity",identity);
            data.addProperty("scheduleInstanceIdentityStatus",identity==null?"NOT_EXPOSED":"AVAILABLE");data.addProperty("queryTickArgument",tick);
            data.addProperty("storedScheduleMatch",KneekuraDebugDecisionSnapshot.read(Brain.class,"schedule",brain)==schedule);
            data.add("returnedActivity",activityValue(result));data.add("stateAtReturn",activityState(brain));
            data.addProperty("returnScope","ORIGINAL_VIRTUAL_SCHEDULE_QUERY_RETURN");return data;
        });
        return result;
    }
    /** Two original private predicate callers; normal results are not recomputed from slots. */
    public static boolean originalActivityRequirement(Brain<?> brain,Activity requested,String site,BooleanSupplier original) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread())return original.getAsBoolean();
        ActivityRequirementFrame previous=session.activityRequirementFrame;int depth=session.activityRequirementDepth;session.activityRequirementDepth++;
        try {
            ActivityRequirementFrame frame=session.activityRequirementBegin(brain,requested,site);session.activityRequirementFrame=frame;
            boolean result=original.getAsBoolean();
            if(session.activityRequirementReady(frame)&&frame.membership!=null)session.record("BRAIN_ACTIVITY_REQUIREMENT_CHECKS_RETURN","Brain.activityRequirementsAreMet.sourceChecks.AFTER",()->{
                JsonObject data=activityData(session,frame.parent);data.addProperty("requirementInvocationId",frame.id);data.addProperty("callerSite",frame.site);
                String name=requested==Activity.CORE?"CORE":requested==Activity.IDLE?"IDLE":requested==Activity.REST?"REST":requested==Activity.WORK?"WORK":requested==Activity.MEET?"MEET":requested==Activity.PLAY?"PLAY":requested==Activity.FIGHT?"FIGHT":null;
                data.addProperty("requestedActivityStatus",name==null?"NOT_EXPOSED":"AVAILABLE");if(name!=null)data.addProperty("requestedActivity",name);
                data.addProperty("mapContains",frame.membership);data.addProperty("result",result);JsonArray checks=new JsonArray();frame.checks.forEach(checks::add);data.add("checks",checks);data.addProperty("checksTruncated",frame.truncated);
                data.addProperty("checkScope","ORIGINAL_ACTIVITY_REQUIREMENT_MAP_AND_VIRTUAL_CHECK_RETURNS_PREFIX_NOT_ALL_ELIGIBILITY_REASONS");return data;
            });return result;
        }finally{session.activityRequirementFrame=active==session?previous:null;session.activityRequirementDepth=depth;}
    }
    public static boolean originalActivityRequirementContains(Brain<?> brain,Map<?,?> map,Object key,Activity requested) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread())return map.containsKey(key);
        ActivityRequirementFrame frame=session.activityRequirementFrame;
        boolean supported=session.activityRequirementReady(frame)&&frame.parent.brain()==brain&&frame.requirements==map&&frame.requested==requested&&key==requested&&frame.membership==null;
        if(frame!=null&&!supported)frame.invalid=true;session.activityRequirementFrame=null;
        try {boolean result=map.containsKey(key);if(supported&&session.activityRequirementReady(frame))frame.membership=result;return result;}
        finally{session.activityRequirementFrame=active==session?frame:null;}
    }
    public static boolean originalActivityRequirementCheck(Brain<?> brain,MemoryModuleType<?> module,MemoryStatus status,Activity requested) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread())return brain.checkMemory(module,status);
        ActivityRequirementFrame frame=session.activityRequirementFrame;
        boolean supported=session.activityRequirementReady(frame)&&frame.parent.brain()==brain&&frame.requested==requested&&Boolean.TRUE.equals(frame.membership);
        if(frame!=null&&!supported)frame.invalid=true;session.activityRequirementFrame=null;
        MemorySourceFrame oldSource=session.memorySourceFrame;int sourceDepth=session.memorySourceDepth;session.memorySourceDepth++;
        MemorySourceFrame source=supported?session.memorySourceBegin(brain,module,status,frame.count+1,null,null,null,frame):null;session.memorySourceFrame=source;
        try {boolean result=brain.checkMemory(module,status);memorySourceReturn(session,source,result);if(supported&&session.activityRequirementReady(frame)){
                int index=frame.count=Math.min(9,frame.count+1);if(index>8)frame.truncated=true;
                else {JsonObject c=new JsonObject();c.addProperty("checkIndex",index);String name=module==MemoryModuleType.PATH?"PATH":module==MemoryModuleType.WALK_TARGET?"WALK_TARGET":module==MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE?"CANT_REACH_WALK_TARGET_SINCE":null;
                    c.addProperty("memoryModuleStatus",name==null?"NOT_EXPOSED":"AVAILABLE");if(name!=null)c.addProperty("memoryModule",name);c.addProperty("requestedMemoryStatus",status==MemoryStatus.REGISTERED?"REGISTERED":status==MemoryStatus.VALUE_PRESENT?"VALUE_PRESENT":status==MemoryStatus.VALUE_ABSENT?"VALUE_ABSENT":"NOT_EXPOSED");c.addProperty("result",result);frame.checks.add(c);}
            }return result;
        }finally{session.memorySourceFrame=active==session?oldSource:null;session.memorySourceDepth=sourceDepth;session.activityRequirementFrame=active==session?frame:null;}
    }
    /** Source Map.get returns Object: the original caller retains its checkcast and null branch. */
    public static Object originalMemorySourceGet(Brain<?> brain,Map<?,?> map,Object key,MemoryModuleType<?> module,MemoryStatus requested) {
        Session session=active;if(session==null||session.thread!=Thread.currentThread())return map.get(key);
        MemorySourceFrame frame=session.memorySourceFrame;
        boolean supported=session.memorySourceReady(frame)&&frame.brain==brain&&frame.module==module&&frame.requested==requested&&frame.memories==map&&key==module&&!frame.got&&!frame.returned;
        if(frame!=null&&!supported)frame.invalid=true;session.memorySourceFrame=null;
        try {Object result=map.get(key);if(supported&&session.memorySourceReady(frame)){frame.got=true;frame.slot=result;}return result;}
        finally{session.memorySourceFrame=active==session?frame:null;}
    }
    public static boolean originalMemorySourcePresence(Brain<?> brain,java.util.Optional<?> slot,MemoryModuleType<?> module,MemoryStatus requested,String site) {
        Session session=active;if(session==null||session.thread!=Thread.currentThread())return slot.isPresent();
        MemorySourceFrame frame=session.memorySourceFrame;
        boolean supported=session.memorySourceReady(frame)&&frame.brain==brain&&frame.module==module&&frame.requested==requested&&frame.got&&frame.slot==slot&&slot!=null&&frame.presence==null&&!frame.returned&&
            (requested==MemoryStatus.VALUE_PRESENT&&"VALUE_PRESENT".equals(site)||requested==MemoryStatus.VALUE_ABSENT&&"VALUE_ABSENT".equals(site));
        if(frame!=null&&!supported)frame.invalid=true;session.memorySourceFrame=null;
        try {boolean result=slot.isPresent();if(supported&&session.memorySourceReady(frame)){frame.presence=result;frame.presenceSite=site;}return result;}
        finally{session.memorySourceFrame=active==session?frame:null;}
    }
    public static void memorySourceBaseReturn(Brain<?> brain,MemoryModuleType<?> module,MemoryStatus requested,boolean result) {
        Session session=active;if(session==null||session.thread!=Thread.currentThread())return;MemorySourceFrame frame=session.memorySourceFrame;
        boolean supported=session.memorySourceReady(frame)&&frame.brain==brain&&frame.module==module&&frame.requested==requested&&frame.got&&!frame.returned&&
            (frame.slot==null||requested!=MemoryStatus.VALUE_PRESENT&&requested!=MemoryStatus.VALUE_ABSENT||frame.presence!=null);
        if(frame!=null&&!supported)frame.invalid=true;if(supported){frame.returned=true;frame.baseResult=result;}
    }
    private static void memorySourceReturn(Session session,MemorySourceFrame frame,boolean result) {
        if(!session.memorySourceReady(frame)||!frame.got||!frame.returned)return;
        session.record(frame.start==null?"BRAIN_ACTIVITY_MEMORY_SOURCE_RETURN":"BRAIN_PATH_MEMORY_SOURCE_RETURN","Brain.checkMemory.originalSource.AFTER_VIRTUAL_RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("brainClass",label(frame.brain.getClass().getName()));String token=session.token(frame.brain);
            if(token!=null)data.addProperty("instanceIdentity",token);data.addProperty("instanceIdentityStatus",token==null?"NOT_EXPOSED":"AVAILABLE");
            data.addProperty("memorySourceInvocationId",frame.id);data.addProperty("requirementInvocationId",frame.start==null?frame.activity.id:frame.requirement.id);
            if(frame.start==null)data.addProperty("activityInvocationId",frame.activity.parent.id());else data.addProperty("tryStartInvocationId",frame.start.id);
            data.addProperty("checkIndex",frame.index);String name=frame.module==MemoryModuleType.PATH?"PATH":frame.module==MemoryModuleType.WALK_TARGET?"WALK_TARGET":frame.module==MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE?"CANT_REACH_WALK_TARGET_SINCE":null;
            data.addProperty("memoryModuleStatus",name==null?"NOT_EXPOSED":"AVAILABLE");if(name!=null)data.addProperty("memoryModule",name);
            data.addProperty("requestedMemoryStatus",frame.requested==MemoryStatus.REGISTERED?"REGISTERED":frame.requested==MemoryStatus.VALUE_PRESENT?"VALUE_PRESENT":frame.requested==MemoryStatus.VALUE_ABSENT?"VALUE_ABSENT":"NOT_EXPOSED");
            data.addProperty("slotStatus",frame.slot==null?"NULL":"NON_NULL");data.addProperty("presenceStatus",frame.presence==null?"NOT_CALLED":"NORMAL_RETURN");
            if(frame.presence!=null){data.addProperty("presenceSite",frame.presenceSite);data.addProperty("presenceResult",frame.presence);}
            data.addProperty("baseResult",frame.baseResult);data.addProperty("result",result);data.addProperty("sourceScope","ORIGINAL_BASE_MAP_PRESENCE_AND_RETURN_WITH_VIRTUAL_RESULT_NOT_ALL_ELIGIBILITY_REASONS");return data;
        });
    }
    public static void activityRequirementsReturn(Brain<?> brain,Activity requested,boolean result) {
        Session session=active;ActivityFrame frame=activityFrame(session,brain);
        if(frame!=null)session.record("BRAIN_ACTIVITY_REQUIREMENTS_RETURN","Brain.activityRequirementsAreMet.RETURN",()->{
            JsonObject data=activityData(session,frame);data.add("requestedActivity",activityValue(requested));
            data.addProperty("result",result);data.add("stateAtReturn",activityState(brain));
            data.addProperty("returnScope","ORIGINAL_REGISTERED_MEMORY_REQUIREMENTS_RETURN");return data;
        });
    }
    public static void activeActivityReturn(Brain<?> brain,Activity requested) {
        Session session=active;ActivityFrame frame=activityFrame(session,brain);
        if(frame!=null)session.record("BRAIN_ACTIVITY_SET_RETURN","Brain.setActiveActivity.RETURN",()->{
            JsonObject data=activityData(session,frame);data.add("requestedActivity",activityValue(requested));
            data.add("stateAtReturn",activityState(brain));data.addProperty("returnScope","NORMAL_PRIVATE_SETTER_RETURN_NOT_SWITCH_SUCCESS");return data;
        });
    }
    private static ActivityFrame activityFrame(Session session,Brain<?> brain) {
        if(session==null||session.thread!=Thread.currentThread())return null;
        ActivityFrame frame=session.activityFrame;
        return frame!=null&&frame.brain()==brain&&session.activityReady(brain)?frame:null;
    }
    private static JsonObject activityData(Session session,ActivityFrame frame) {
        JsonObject data=new JsonObject();data.addProperty("brainClass",label(frame.brain().getClass().getName()));
        String identity=session.token(frame.brain());data.addProperty("instanceIdentity",identity);
        data.addProperty("instanceIdentityStatus",identity==null?"NOT_EXPOSED":"AVAILABLE");data.addProperty("activityInvocationId",frame.id());
        data.addProperty("dispatchScope","UPDATE_ACTIVITY_FROM_SCHEDULE_ORIGINAL_VIRTUAL_CALL");
        data.addProperty("fieldScope","BASE_BRAIN_CACHED_FIELDS_ONLY");
        data.addProperty("behaviorStopStatus","NOT_EXPOSED");data.addProperty("movementOutcomeStatus","NOT_EXPOSED");return data;
    }
    private static JsonObject activityState(Brain<?> brain)throws ReflectiveOperationException {
        JsonObject state=new JsonObject();
        state.add("activeActivities",activitySet(KneekuraDebugDecisionSnapshot.read(Brain.class,"activeActivities",brain)));
        state.add("coreActivities",activitySet(KneekuraDebugDecisionSnapshot.read(Brain.class,"coreActivities",brain)));
        state.add("defaultActivity",activityValue((Activity)KneekuraDebugDecisionSnapshot.read(Brain.class,"defaultActivity",brain)));
        state.addProperty("lastScheduleUpdate",Long.toString((Long)KneekuraDebugDecisionSnapshot.read(Brain.class,"lastScheduleUpdate",brain)));
        return state;
    }
    private static JsonObject activityValue(Activity activity) {
        JsonObject value=new JsonObject();
        if(activity==null||activity.getClass()!=Activity.class){value.addProperty("status","NOT_EXPOSED");value.addProperty("detail",activity==null?"NULL_ACTIVITY":"CUSTOM_ACTIVITY_CLASS");return value;}
        var key=BuiltInRegistries.ACTIVITY.getKey(activity);
        if(key==null){value.addProperty("status","NOT_EXPOSED");value.addProperty("detail","UNREGISTERED_ACTIVITY");}
        else {value.addProperty("status","AVAILABLE");value.addProperty("key",label(key.toString()));}
        return value;
    }
    private static JsonObject activitySet(Object object) {
        JsonObject section=new JsonObject();
        if(object==null||!Set.of("java.util.HashSet","java.util.ImmutableCollections$Set12","java.util.ImmutableCollections$SetN",
            "com.google.common.collect.RegularImmutableSet","com.google.common.collect.SingletonImmutableSet").contains(object.getClass().getName())){
            section.addProperty("status","NOT_EXPOSED");section.addProperty("detail",object==null?"NULL_ACTIVITY_SET":"CUSTOM_ACTIVITY_SET");return section;
        }
        Set<?> set=(Set<?>)object;JsonArray values=new JsonArray();int retained=0;
        for(Object activity:set){if(retained++>=16)break;values.add(activityValue((Activity)activity));}
        section.addProperty("status",set.size()>16?"PARTIAL":"AVAILABLE");section.addProperty("count",set.size());
        section.addProperty("truncated",set.size()>16);section.add("values",values);return section;
    }
    public static void behaviorReturn(Behavior<?> behavior,LivingEntity entity,String kind,Boolean result) {
        Session session=active;if(session==null||!session.matches(entity))return;
        String method=switch(kind){case "BEHAVIOR_TRY_START_RETURN"->"tryStart";
            case "BEHAVIOR_TICK_OR_STOP_RETURN"->"tickOrStop";case "BEHAVIOR_STOP_RETURN"->"doStop";default->null;};
        if(method==null)return;
        session.record(kind,"Behavior."+method+".RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("className",label(behavior.getClass().getName()));
            data.addProperty("instanceIdentity",session.token(behavior));
            data.addProperty("cachedStatus",((Enum<?>)KneekuraDebugDecisionSnapshot.read(Behavior.class,"status",behavior)).name());
            if(result!=null)data.addProperty("result",result);
            data.addProperty("reasonStatus","NOT_EXPOSED");return data;
        });
    }
    /** Original independent-control base return only; parent success is not a child result. */
    public static void behaviorControlReturn(BehaviorControl<?> control,LivingEntity entity,String kind,Boolean result) {
        Session session=active;if(session==null||!session.matches(entity))return;
        Class<?> base=control instanceof OneShot<?>?OneShot.class:control instanceof GateBehavior<?>?GateBehavior.class:null;
        if(base==null)return;
        String method=switch(kind){case "BEHAVIOR_TRY_START_RETURN"->"tryStart";
            case "BEHAVIOR_TICK_OR_STOP_RETURN"->"tickOrStop";case "BEHAVIOR_STOP_RETURN"->"doStop";default->null;};
        if(method==null)return;
        session.record(kind,base.getSimpleName()+"."+method+".RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("className",label(control.getClass().getName()));
            data.addProperty("instanceIdentity",session.token(control));
            data.addProperty("cachedStatus",((Enum<?>)KneekuraDebugDecisionSnapshot.read(base,"status",control)).name());
            if(result!=null)data.addProperty("result",result);
            data.addProperty("reasonStatus","NOT_EXPOSED");return data;
        });
    }
    public static void sensorReturn(Object sensor,LivingEntity entity) {
        Session session=active;if(session==null||!session.matches(entity))return;
        session.record("SENSOR_SCAN_RETURN","Sensor.doTick.AFTER",()->{
            JsonObject data=new JsonObject();data.addProperty("className",label(sensor.getClass().getName()));
            data.addProperty("instanceIdentity",session.token(sensor));
            data.addProperty("candidatePopulationStatus","NOT_EXPOSED");return data;
        });
    }
    public static void controlReturn(Mob mob,String kind) {
        Session session=active;if(session==null||!session.matches(mob))return;
        session.record("CONTROL_TICK_RETURN","Mob.serverAiStep."+kind+"Control.tick.AFTER",()->{
            JsonObject data=new JsonObject();data.addProperty("control",kind);
            data.add("cachedBaseFields",session.snapshot.controls(mob).getAsJsonObject(kind));return data;
        });
    }
    public static void teleportReturn(LivingEntity entity,double x,double y,double z,boolean result) {
        Session session=active;if(session==null||!session.matches(entity))return;
        session.record("CONTROL_TELEPORT_RETURN","LivingEntity.randomTeleport.RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("result",result);
            JsonObject requested=new JsonObject();requested.addProperty("x",x);requested.addProperty("y",y);requested.addProperty("z",z);
            JsonObject returned=new JsonObject();returned.addProperty("x",entity.getX());returned.addProperty("y",entity.getY());returned.addProperty("z",entity.getZ());
            data.add("requestedPosition",requested);data.add("returnedPosition",returned);
            data.addProperty("dispatchScope","BASE_RANDOM_TELEPORT_RETURN");
            data.addProperty("reasonStatus","NOT_EXPOSED");return data;
        });
    }
    public static void ghastReachReturn(Ghast mob,Object controller,Vec3 direction,int stepCount,boolean result) {
        Session session=active;if(session==null||!session.matches(mob))return;
        session.record("CONTROL_GHAST_REACH_RETURN","Ghast$GhastMoveControl.canReach.RETURN",()->{
            String uuid=KneekuraDebugDecisionSnapshot.read(Entity.class,"uuid",mob).toString();
            if(!uuid.equals(session.budget.context().subjectUuid())||controller==null||
                controller!=KneekuraDebugDecisionSnapshot.read(Mob.class,"moveControl",mob)||
                !controller.getClass().getName().equals("net.minecraft.world.entity.monster.Ghast$GhastMoveControl"))
                throw new IllegalArgumentException("GHAST_REACH_RECEIVER_CHANGED");
            if(direction==null||!Double.isFinite(direction.x)||!Double.isFinite(direction.y)||!Double.isFinite(direction.z)||stepCount<0)
                throw new IllegalArgumentException("GHAST_REACH_ARGUMENT_UNAVAILABLE");
            JsonObject data=new JsonObject();data.addProperty("receiverUuid",uuid);
            data.addProperty("controllerClass",controller.getClass().getName());data.add("direction",vector(direction));
            data.addProperty("stepCount",stepCount);data.addProperty("result",result);
            data.addProperty("dispatchScope","GHAST_ORIGINAL_CAN_REACH_RETURN");
            data.addProperty("pathSemantics","CUSTOM_STEERING_REACH_NOT_A_STAR");
            data.addProperty("collisionLocationStatus","NOT_EXPOSED");data.addProperty("reasonStatus","NOT_EXPOSED");return data;
        });
    }
    public static void projectileSpawnReturn(Entity entity,boolean result) {
        Session session=active;if(session!=null&&entity instanceof Projectile shot)session.projectileSpawn(shot,result);
    }
    public static void projectileTickReturn(Entity entity) {
        Session session=active;if(session==null||!(entity instanceof Projectile shot)||!session.trackedProjectile(shot))return;
        session.record("CONTROL_PROJECTILE_TICK_RETURN","ServerLevel.tickNonPassenger.Entity.tick.AFTER",()->{
            JsonObject data=session.projectileReference(shot,session.projectiles.get(shot));
            data.add("position",position(shot));data.add("velocity",vector(shot.getDeltaMovement()));data.addProperty("removed",shot.isRemoved());
            data.addProperty("dimension",session.budget.context().dimension());
            data.addProperty("dispatchScope","SERVER_NON_PASSENGER_ORIGINAL_TICK_AFTER");return data;
        });
    }
    public static void projectileHitReturn(Projectile shot,HitResult hit) {
        Session session=active;if(session==null||!session.trackedProjectile(shot)||hit==null||hit.getType()==HitResult.Type.MISS)return;
        session.record("CONTROL_PROJECTILE_HIT_RETURN","Projectile.onHit.RETURN",()->{
            JsonObject data=session.projectileReference(shot,session.projectiles.get(shot));
            data.addProperty("hitType",hit.getType().name());data.add("hitPosition",vector(hit.getLocation()));
            if(hit instanceof EntityHitResult entityHit)data.addProperty("targetUuid",entityHit.getEntity().getUUID().toString());
            data.addProperty("dispatchScope","BASE_PROJECTILE_ON_HIT_RETURN");
            data.addProperty("damageOutcomeStatus","NOT_EXPOSED");return data;
        });
    }
    /** Redirect the one existing hurt call at inspected Arrow/Fireball sites; never replay it. */
    public static boolean projectileHurt(Projectile shot,Entity target,DamageSource source,float amount) {
        Session session=active;
        boolean capture=session!=null&&session.trackedProjectile(shot);
        long started=capture?System.nanoTime():0L;
        Float before=capture?baseHealth(target):null;
        long beforeCost=capture?Math.max(0L,System.nanoTime()-started):0L;
        boolean result=target.hurt(source,amount); // Exact original dynamic dispatch, including false/exception.
        if(capture&&session==active&&session.trackedProjectile(shot))session.record(
            "CONTROL_PROJECTILE_HURT_RETURN","ArrowOrFireball.Entity.hurt.AFTER",()->{
                JsonObject data=session.projectileReference(shot,session.projectiles.get(shot));
                data.addProperty("targetUuid",target.getUUID().toString());data.addProperty("result",result);data.addProperty("requestedDamage",amount);
                Float after=baseHealth(target);
                if(before!=null&&after!=null){data.addProperty("healthStatus","AVAILABLE");
                    data.addProperty("healthBefore",before);data.addProperty("healthAfter",after);data.addProperty("healthDelta",(double)before-(double)after);
                    data.addProperty("healthScope","BASE_LIVING_DATA_HEALTH_ACROSS_ORIGINAL_CALL");
                }else{data.addProperty("healthStatus","NOT_EXPOSED");data.addProperty("healthScope","NON_LIVING_OR_UNAVAILABLE");}
                data.addProperty("preCallObserverCostNanos",beforeCost);
                data.addProperty("dispatchScope","ARROW_OR_FIREBALL_ORIGINAL_ENTITY_HURT_CALL");
                data.addProperty("damageReasonStatus","NOT_EXPOSED");return data;
            });
        return result;
    }
    @SuppressWarnings("unchecked") private static Float baseHealth(Entity entity) {
        if(!(entity instanceof LivingEntity))return null;
        try {
            var data=(SynchedEntityData)KneekuraDebugDecisionSnapshot.read(Entity.class,"entityData",entity);
            var accessor=(EntityDataAccessor<Float>)KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"DATA_HEALTH_ID",null);
            Float result=data.get(accessor);return result!=null&&Float.isFinite(result)?result:null;
        }catch(ReflectiveOperationException|RuntimeException|LinkageError unavailable){return null;}
    }
    private static JsonObject position(Entity entity){return vector(new Vec3(entity.getX(),entity.getY(),entity.getZ()));}
    private static JsonObject vector(Vec3 value){JsonObject out=new JsonObject();out.addProperty("x",value.x);out.addProperty("y",value.y);out.addProperty("z",value.z);return out;}
    public static void malusReturn(Mob mob,BlockPathTypes type,float result) {
        Session session=active;if(session==null||!session.matches(mob))return;
        session.record("BASE_MALUS_RETURN","Mob.getPathfindingMalus.RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("pathType",type.name());
            number(data,"returnedMalus",result);data.addProperty("dispatchScope","BASE_METHOD_RETURN_NOT_CUSTOM_OVERRIDE_RESULT");
            data.addProperty("effectiveSourceStatus","NOT_EXPOSED");return data;
        });
    }
    /** The original evaluator call invokes a custom override once; no second getter/table query. */
    public static float originalMalus(NodeEvaluator evaluator,Mob mob,BlockPathTypes type) {
        float result=mob.getPathfindingMalus(type);
        Session session=active;if(session==null||!session.matches(mob))return result;
        session.record("EFFECTIVE_MALUS_RETURN","NodeEvaluator.virtualMobMalus.AFTER",()->{
            String uuid=KneekuraDebugDecisionSnapshot.read(Entity.class,"uuid",mob).toString();
            if(!uuid.equals(session.budget.context().subjectUuid()))throw new IllegalArgumentException("ORIGINAL_MALUS_RECEIVER_CHANGED");
            JsonObject data=new JsonObject();data.addProperty("receiverUuid",uuid);data.addProperty("receiverClass",label(mob.getClass().getName()));
            data.addProperty("evaluatorClass",label(evaluator.getClass().getName()));data.addProperty("pathType",type.name());
            number(data,"returnedMalus",result);data.addProperty("dispatchScope","ORIGINAL_EVALUATOR_VIRTUAL_MOB_MALUS_RETURN");
            data.addProperty("callSiteScope","KNOWN_BASE_EVALUATOR_CLASS_SET_NOT_EXACT_METHOD");
            data.addProperty("effectivePathCostStatus","NOT_EXPOSED");data.addProperty("underlyingSourceStatus","NOT_EXPOSED");return data;
        });
        return result;
    }
    public static void pathBegin(PathFinder finder,Mob mob) {
        Session session=active;if(session==null||session.thread!=Thread.currentThread())return;
        // Also clear an interrupted selected search when this finder is reused by another Mob.
        session.searches.remove(finder);
        if(session.heapNodes!=null)session.heapNodes.remove(finder);
        if(session.pendingPops!=null)session.pendingPops.remove(finder);
        if(!session.matches(mob)||(!session.channels.contains("path")&&!session.channels.contains("neighbors")&&!session.channels.contains("frontier")&&!session.channels.contains("path_nodes")&&!session.channels.contains("path_g")&&!session.channels.contains("path_distance")))return;
        try { if(!session.budget.allows(session.currentContext.get(),session.time.getAsLong())){session.clearHeapNodes();return;} }
        catch(RuntimeException error) {session.clearHeapNodes();session.budget.close("CONTEXT_UNAVAILABLE");return;}
        if(session.searches.size()>=8)return;
        session.searches.put(finder,"search:"+session.budget.context().selectionRevision()+":"+(++session.nextSearch));
        if(session.heapNodes!=null)session.heapNodes.put(finder,new IdentityHashMap<>());
        FinderFrame direct=session.finderFrame;
        if(direct!=null&&direct.finder==finder&&direct.create.compute.owner==mob&&session.computeReady(direct.create.compute))direct.searchId=session.searches.get(finder);
    }
    public static void pathState(PathFinder finder,Mob mob) {
        Session session=active;if(session==null||!session.matches(mob)||!session.searches.containsKey(finder))return;
        session.record("PATH_SEARCH_STATE","PathFinder.outer.findPath.BEFORE_EVALUATOR_DONE_AFTER_INNER_RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("searchId",session.searches.get(finder));
            data.add("frontier",frontier(finder,session.nodeLimit));return data;
        });
    }
    /** Preserve exactly one original virtual dispatch, including its return and exception. */
    public static int originalNeighbors(PathFinder finder,NodeEvaluator evaluator,Node[] output,Node current) {
        int count=evaluator.getNeighbors(output,current);
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()||!session.searches.containsKey(finder))return count;
        session.record("PATH_NEIGHBORS_RETURN","PathFinder.inner.NodeEvaluator.getNeighbors.AFTER",()->{
            if(KneekuraDebugDecisionSnapshot.read(PathFinder.class,"nodeEvaluator",finder)!=evaluator)
                throw new IllegalArgumentException("ORIGINAL_EVALUATOR_MISMATCH");
            if(output==null||count<0||count>output.length)throw new IllegalArgumentException("ORIGINAL_NEIGHBOR_COUNT_UNAVAILABLE");
            JsonObject data=new JsonObject();data.addProperty("searchId",session.searches.get(finder));
            data.addProperty("evaluatorClass",label(evaluator.getClass().getName()));data.add("currentNode",observedNode(current));
            data.addProperty("returnedCount",count);data.addProperty("returnedArrayLength",output.length);
            data.addProperty("maxNodes",session.nodeLimit);data.addProperty("truncated",count>session.nodeLimit);
            JsonArray neighbors=new JsonArray();
            for(int i=0;i<Math.min(count,session.nodeLimit);i++) {
                JsonObject item=new JsonObject();item.addProperty("slot",i);item.add("node",observedNode(output[i]));neighbors.add(item);
            }
            data.add("neighbors",neighbors);data.addProperty("phase","AFTER_ORIGINAL_GET_NEIGHBORS_BEFORE_RELAXATION");
            data.addProperty("dispatchScope","ORIGINAL_VIRTUAL_GET_NEIGHBORS_RETURN");
            data.addProperty("subjectRelationScope","SELECTED_OUTER_FIND_PATH_INVOCATION");
            data.addProperty("fieldScope","BASE_NODE_FIELDS_BEFORE_RELAXATION");
            data.addProperty("neighborPopulationStatus","NOT_EXPOSED");data.addProperty("rejectionReasonStatus","NOT_EXPOSED");return data;
        });
        return count;
    }
    /** Exactly one original virtual heap call. Observation never reads the whole heap. */
    public static Node originalHeapInsert(PathFinder finder,BinaryHeap heap,Node argument,boolean start) {
        Node returned=heap.insert(argument);
        heapReturn(finder,heap,returned,start?"START_INSERT":"RELAXATION_INSERT",argument==returned,0);
        return returned;
    }
    public static Node originalHeapPop(PathFinder finder,BinaryHeap heap) {
        // A failed next original pop cannot leave an earlier return eligible for a checkpoint.
        Session session=active;
        if(session!=null&&session.thread==Thread.currentThread()&&session.pendingPops!=null)session.pendingPops.remove(finder);
        Node returned=heap.pop();heapReturn(finder,heap,returned,"POP",false,0);return returned;
    }
    public static void originalHeapChangeCost(PathFinder finder,BinaryHeap heap,Node argument,float requestedCost) {
        heap.changeCost(argument,requestedCost);heapReturn(finder,heap,argument,"CHANGE_COST",false,requestedCost);
    }
    private static void heapReturn(PathFinder finder,BinaryHeap heap,Node node,String operation,boolean argumentMatches,float cost) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()||!session.channels.contains("frontier")||!session.searches.containsKey(finder))return;
        session.record("PATH_HEAP_OPERATION_RETURN","PathFinder.inner.BinaryHeap."+operation+".AFTER",()->{
            if(KneekuraDebugDecisionSnapshot.read(PathFinder.class,"openSet",finder)!=heap)
                throw new IllegalArgumentException("ORIGINAL_HEAP_MISMATCH");
            String searchId=session.searches.get(finder);
            JsonObject data=new JsonObject();data.addProperty("searchId",searchId);data.addProperty("heapClass",label(heap.getClass().getName()));
            data.addProperty("operation",operation);
            data.addProperty("phase",operation.equals("POP")?"AFTER_ORIGINAL_POP_BEFORE_CALLER_CLOSE":
                operation.equals("CHANGE_COST")?"AFTER_ORIGINAL_CHANGE_COST":"AFTER_ORIGINAL_INSERT");
            data.addProperty("nodeRole",operation.equals("CHANGE_COST")?"PASSED_NODE_AFTER_ORIGINAL_CALL":"ORIGINAL_RETURNED_NODE");
            data.add("node",observedNode(node));data.addProperty("maxNodes",session.nodeLimit);
            data.add("nodeIdentity",session.nodeIdentity(finder,node));
            if(operation.endsWith("INSERT"))data.addProperty("argumentMatchesReturned",argumentMatches);
            if(operation.equals("CHANGE_COST"))number(data,"requestedCost",cost);
            data.addProperty("dispatchScope","ORIGINAL_PATHFINDER_INNER_HEAP_CALL_RETURN");
            data.addProperty("subjectRelationScope","SELECTED_OUTER_FIND_PATH_INVOCATION");
            data.addProperty("neighborPopulationStatus","NOT_EXPOSED");data.addProperty("rejectionReasonStatus","NOT_EXPOSED");
            data.addProperty("finalPathCostStatus","NOT_EXPOSED");
            // Saved within the checked capture. record clears references on claim/writer failure.
            if(operation.equals("POP")&&node!=null)session.pendingPops.put(finder,new PendingPop(node,session.budget.events()+1));
            return data;
        });
    }
    /** Read only the preceding original pop return after the caller's original field write. */
    public static void pathClosedWrite(PathFinder finder) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()||session.pendingPops==null||!session.searches.containsKey(finder))return;
        PendingPop pending=session.pendingPops.remove(finder);if(pending==null)return;
        session.record("PATH_NODE_CLOSED_CHECKPOINT","PathFinder.inner.Node.closed.AFTER_ORIGINAL_WRITE",()->{
            JsonObject data=new JsonObject();data.addProperty("searchId",session.searches.get(finder));
            data.addProperty("priorPopEventIndex",pending.eventIndex());
            data.addProperty("nodeRole","PRECEDING_ORIGINAL_POP_RETURN_REFERENCE");
            data.add("node",observedNode(pending.node(),true));data.add("nodeIdentity",session.nodeIdentity(finder,pending.node()));
            data.addProperty("maxNodes",session.nodeLimit);data.addProperty("phase","AFTER_ORIGINAL_CALLER_CLOSED_FIELD_WRITE");
            data.addProperty("dispatchScope","ORIGINAL_PATHFINDER_INNER_CLOSED_FIELD_WRITE");
            data.addProperty("subjectRelationScope","SELECTED_OUTER_FIND_PATH_INVOCATION");
            data.addProperty("referenceScope","RETAINED_ORIGINAL_POP_RETURN_REFERENCE");
            data.addProperty("neighborPopulationStatus","NOT_EXPOSED");data.addProperty("rejectionReasonStatus","NOT_EXPOSED");
            data.addProperty("finalPathCostStatus","NOT_EXPOSED");return data;
        });
    }
    private static JsonObject observedNode(Node node)throws ReflectiveOperationException {
        return observedNode(node,false);
    }
    private static JsonObject observedNode(Node node,boolean checkpoint)throws ReflectiveOperationException {
        JsonObject section=new JsonObject();
        if(node==null){section.addProperty("status","NOT_EXPOSED");section.addProperty("detail","NULL_NODE");return section;}
        JsonObject row=new JsonObject();row.addProperty("className",label(node.getClass().getName()));
        row.addProperty("x",node.x);row.addProperty("y",node.y);row.addProperty("z",node.z);
        if(node.type==null)row.addProperty("pathTypeStatus","NOT_EXPOSED");else row.addProperty("pathType",node.type.name());
        number(row,"g",node.g);number(row,"h",node.h);number(row,"f",node.f);
        number(row,"costMalus",node.costMalus);number(row,"walkedDistance",node.walkedDistance);
        row.addProperty(checkpoint?"openAtCheckpoint":"openAtReturn",(Integer)KneekuraDebugDecisionSnapshot.read(Node.class,"heapIdx",node)>=0);
        row.addProperty(checkpoint?"closedAtCheckpoint":"closedAtReturn",node.closed);section.addProperty("status","AVAILABLE");section.add("data",row);return section;
    }
    /** Capture only the caller's already returned protected virtual distance; never replay it. */
    public static void pathDistanceReturn(PathFinder finder,Node from,Node to,float result) {
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()||!session.searches.containsKey(finder))return;
        session.record("PATH_EDGE_DISTANCE_RETURN","PathFinder.inner.distance.AFTER_ORIGINAL_VIRTUAL_RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("searchId",session.searches.get(finder));data.addProperty("maxNodes",session.nodeLimit);
            data.addProperty("receiverClass",label(finder.getClass().getName()));data.addProperty("receiverScope","ORIGINAL_CALLER_THIS");
            number(data,"returnedDistance",result);data.addProperty("returnedDistanceScope","ORIGINAL_VIRTUAL_CALL_RETURN");
            data.add("fromNode",observedNode(from));data.add("fromIdentity",session.nodeIdentity(finder,from));
            data.add("toNode",observedNode(to));data.add("toIdentity",session.nodeIdentity(finder,to));
            data.addProperty("phase","AFTER_ORIGINAL_EDGE_DISTANCE_BEFORE_WALKED_DISTANCE_WRITE");
            data.addProperty("dispatchScope","ORIGINAL_PATHFINDER_INNER_PROTECTED_VIRTUAL_DISTANCE_RETURN");
            data.addProperty("subjectRelationScope","SELECTED_OUTER_FIND_PATH_INVOCATION");
            data.addProperty("fieldScope","BASE_NODE_FIELDS_AFTER_ORIGINAL_RETURN_AND_CAPTURE_GATES");
            for(String key:new String[]{"comparisonOperandsStatus","neighborPopulationStatus","rejectionReasonStatus","finalPathCostStatus","navigationAdoptionStatus"})data.addProperty(key,"NOT_EXPOSED");
            return data;
        });
    }
    /** Exact accepted-neighbor PUTFIELD receiver/value. Original assignment precedes all capture gates. */
    public static void originalAcceptedGWrite(PathFinder finder,Node node,float writtenG) {
        node.g=writtenG;
        Session session=active;
        if(session==null||session.thread!=Thread.currentThread()||!session.searches.containsKey(finder))return;
        session.record("PATH_NODE_G_WRITE_CHECKPOINT","PathFinder.inner.Node.g.AFTER_ORIGINAL_ACCEPTED_WRITE",()->{
            JsonObject data=new JsonObject();data.addProperty("searchId",session.searches.get(finder));data.addProperty("maxNodes",session.nodeLimit);
            number(data,"writtenG",writtenG);data.addProperty("writtenGScope","ORIGINAL_PUTFIELD_ARGUMENT");
            data.addProperty("nodeRole","ORIGINAL_FIELD_WRITE_RECEIVER");data.add("node",observedNode(node,true));
            data.add("nodeIdentity",session.nodeIdentity(finder,node));Node predecessor=node.cameFrom;
            data.addProperty("predecessorPresent",predecessor!=null);data.add("predecessorIdentity",session.nodeIdentity(finder,predecessor));
            data.addProperty("phase","AFTER_ORIGINAL_ACCEPTED_G_FIELD_WRITE_BEFORE_HEURISTIC_UPDATE");
            data.addProperty("dispatchScope","ORIGINAL_PATHFINDER_INNER_ACCEPTED_G_FIELD_WRITE");
            data.addProperty("subjectRelationScope","SELECTED_OUTER_FIND_PATH_INVOCATION");
            data.addProperty("fieldScope","BASE_NODE_FIELDS_AFTER_WRITE_AND_CAPTURE_GATES");
            for(String key:new String[]{"comparisonOperandsStatus","neighborPopulationStatus","rejectionReasonStatus","finalPathCostStatus","navigationAdoptionStatus"})data.addProperty(key,"NOT_EXPOSED");
            return data;
        });
    }
    public static void pathResult(PathFinder finder,Mob mob,Path result) {
        Session session=active;if(session==null||!session.matches(mob)||!session.searches.containsKey(finder))return;
        session.record("PATH_SEARCH_RESULT","PathFinder.outer.findPath.RETURN",()->{
            JsonObject data=new JsonObject();data.addProperty("searchId",session.searches.get(finder));
            data.addProperty("resultPresent",result!=null);
            if(result!=null) {
                data.addProperty("resultClass",label(result.getClass().getName()));
                if(result.getClass()==Path.class) {
                    data.addProperty("canReach",(Boolean)KneekuraDebugDecisionSnapshot.read(Path.class,"reached",result));
                    Object nodes=KneekuraDebugDecisionSnapshot.read(Path.class,"nodes",result);
                    if(nodes!=null&&nodes.getClass()==ArrayList.class)data.addProperty("resultNodeCount",((ArrayList<?>)nodes).size());
                    else data.addProperty("resultNodeCountStatus","NOT_EXPOSED");
                }
            }
            return data;
        });
        session.record("PATH_RETURNED_NODES","PathFinder.outer.findPath.RETURN_CACHED_NODES",()->{
            JsonObject data=new JsonObject();data.addProperty("searchId",session.searches.get(finder));
            data.addProperty("resultPresent",result!=null);if(result!=null)data.addProperty("resultClass",label(result.getClass().getName()));
            data.addProperty("maxNodes",session.nodeLimit);data.addProperty("dimension",session.budget.context().dimension());
            data.add("pathNodes",returnedPathNodes(session,finder,result));
            data.addProperty("phase","AFTER_ORIGINAL_OUTER_FIND_PATH_RETURN");
            data.addProperty("dispatchScope","SELECTED_OUTER_FIND_PATH_RETURN");
            data.addProperty("fieldScope","BASE_PATH_AND_NODE_CACHED_FIELDS_AT_RETURN");
            data.addProperty("navigationAdoptionStatus","NOT_EXPOSED");data.addProperty("finalEffectiveCostStatus","NOT_EXPOSED");return data;
        });
    }
    private static JsonObject returnedPathNodes(Session session,PathFinder finder,Path result)throws ReflectiveOperationException {
        JsonObject section=new JsonObject();String unavailable=result==null?"NULL_PATH":result.getClass()!=Path.class?"CUSTOM_PATH_CLASS":null;
        if(unavailable!=null){section.addProperty("status","NOT_EXPOSED");section.addProperty("detail",unavailable);return section;}
        Object raw=KneekuraDebugDecisionSnapshot.read(Path.class,"nodes",result);
        if(raw==null||raw.getClass()!=ArrayList.class){section.addProperty("status","NOT_EXPOSED");section.addProperty("detail","CUSTOM_NODE_LIST");return section;}
        // Exact ArrayList only: arbitrary Path/List/Node query methods are never dispatched.
        ArrayList<?> nodes=(ArrayList<?>)raw;int count=nodes.size(),retained=Math.min(count,session.nodeLimit);
        JsonObject data=new JsonObject();data.addProperty("listClass","java.util.ArrayList");
        data.addProperty("nodeCount",count);data.addProperty("retainedNodeCount",retained);data.addProperty("truncated",retained<count);
        JsonArray entries=new JsonArray();for(int i=0;i<retained;i++)entries.add(returnedPathSlot(session,finder,(Node)nodes.get(i),i));
        data.add("nodes",entries);JsonObject terminal=new JsonObject();
        if(count==0){terminal.addProperty("status","NOT_EXPOSED");terminal.addProperty("detail","EMPTY_PATH");}
        else {terminal.addProperty("status","AVAILABLE");terminal.add("data",count<=retained?entries.get(count-1).deepCopy():returnedPathSlot(session,finder,(Node)nodes.get(count-1),count-1));}
        data.add("terminalNode",terminal);JsonObject targetSection=new JsonObject();
        BlockPos target=(BlockPos)KneekuraDebugDecisionSnapshot.read(Path.class,"target",result);
        if(target==null){targetSection.addProperty("status","NOT_EXPOSED");targetSection.addProperty("detail","NULL_TARGET");}
        else {JsonObject xyz=new JsonObject();for(String axis:new String[]{"x","y","z"})xyz.addProperty(axis,(Integer)KneekuraDebugDecisionSnapshot.read(Vec3i.class,axis,target));
            targetSection.addProperty("status","AVAILABLE");targetSection.add("data",xyz);}
        data.add("target",targetSection);data.addProperty("canReach",(Boolean)KneekuraDebugDecisionSnapshot.read(Path.class,"reached",result));
        data.addProperty("nextNodeIndex",(Integer)KneekuraDebugDecisionSnapshot.read(Path.class,"nextNodeIndex",result));
        number(data,"distanceToTarget",(Float)KneekuraDebugDecisionSnapshot.read(Path.class,"distToTarget",result));
        data.addProperty("distanceToTargetScope","PATH_CONSTRUCTOR_CACHED_VALUE");
        section.addProperty("status",retained<count?"PARTIAL":"AVAILABLE");section.add("data",data);return section;
    }
    private static JsonObject returnedPathSlot(Session session,PathFinder finder,Node node,int index)throws ReflectiveOperationException {
        JsonObject slot=new JsonObject();slot.addProperty("index",index);slot.add("node",observedNode(node));
        slot.add("nodeIdentity",session.nodeIdentity(finder,node));Node predecessor=node==null?null:node.cameFrom;
        slot.addProperty("predecessorPresent",predecessor!=null);slot.add("predecessorIdentity",session.nodeIdentity(finder,predecessor));return slot;
    }
    public static void pathEnd(PathFinder finder) {
        Session session=active;if(session!=null&&session.thread==Thread.currentThread()){
            session.searches.remove(finder);if(session.heapNodes!=null)session.heapNodes.remove(finder);
            if(session.pendingPops!=null)session.pendingPops.remove(finder);
        }
    }

    static JsonObject frontier(PathFinder finder,int limit) throws ReflectiveOperationException {
        if(limit<1||limit>64)throw new IllegalArgumentException("NODE_LIMIT_OUT_OF_RANGE");
        NodeEvaluator evaluator=(NodeEvaluator)KneekuraDebugDecisionSnapshot.read(PathFinder.class,"nodeEvaluator",finder);
        JsonObject section=new JsonObject();
        if(!Set.of(WalkNodeEvaluator.class,FlyNodeEvaluator.class,SwimNodeEvaluator.class,AmphibiousNodeEvaluator.class).contains(evaluator.getClass())) {
            section.addProperty("status","NOT_EXPOSED");section.addProperty("detail","CUSTOM_NODE_EVALUATOR");return section;
        }
        Map<?,?> cache=(Map<?,?>)KneekuraDebugDecisionSnapshot.read(NodeEvaluator.class,"nodes",evaluator);
        JsonObject data=new JsonObject();JsonArray nodes=new JsonArray();data.add("nodes",nodes);
        data.addProperty("cacheNodeCount",cache.size());data.addProperty("phase","OUTER_BEFORE_DONE_AFTER_INNER_RETURN");
        data.addProperty("neighborEvaluationTraceStatus","NOT_EXPOSED");
        data.addProperty("rejectionReasonStatus","NOT_EXPOSED");
        for(Object value:cache.values()) {
            if(nodes.size()>=limit)break;
            Node node=(Node)value;JsonObject row=new JsonObject();
            row.addProperty("x",node.x);row.addProperty("y",node.y);row.addProperty("z",node.z);
            int heapIndex=(Integer)KneekuraDebugDecisionSnapshot.read(Node.class,"heapIdx",node);
            row.addProperty("openAtReturn",heapIndex>=0);row.addProperty("closedAtReturn",node.closed);
            row.addProperty("cacheRole",node.closed?"CLOSED_AT_RETURN":heapIndex>=0?"OPEN_AT_RETURN":"OTHER_CACHED");
            number(row,"g",node.g);number(row,"h",node.h);number(row,"f",node.f);
            number(row,"costMalus",node.costMalus);number(row,"walkedDistance",node.walkedDistance);
            row.addProperty("pathType",node.type.name());
            if(node.cameFrom!=null) {row.addProperty("parentX",node.cameFrom.x);row.addProperty("parentY",node.cameFrom.y);row.addProperty("parentZ",node.cameFrom.z);}
            nodes.add(row);
        }
        data.addProperty("truncated",cache.size()>limit);
        section.addProperty("status",cache.size()>limit?"PARTIAL":"AVAILABLE");section.add("data",data);return section;
    }
    private static void number(JsonObject out,String key,float value) {
        if(Float.isFinite(value))out.addProperty(key,value);else out.addProperty(key+"Status","NOT_EXPOSED");
    }
    private static String label(String value) { return value.length()<=512?value:value.substring(0,512); }
}
