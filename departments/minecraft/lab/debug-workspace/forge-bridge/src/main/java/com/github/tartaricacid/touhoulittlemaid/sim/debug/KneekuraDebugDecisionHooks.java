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
import net.minecraft.world.entity.ai.behavior.Behavior;
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
import java.util.function.Supplier;

/** Debug-only callbacks of original ANCHOR method invocations, never a second AI call. */
public final class KneekuraDebugDecisionHooks {
    private static volatile Session active;
    private KneekuraDebugDecisionHooks() { }
    @FunctionalInterface public interface Sink { void record(String method, JsonObject payload) throws IOException; }
    @FunctionalInterface private interface Data { JsonObject read() throws ReflectiveOperationException; }
    private record PendingPop(Node node,int eventIndex) { }

    public static void install(Session session) {
        if (session.thread != Thread.currentThread()) throw new IllegalStateException("SERVER_THREAD_REQUIRED");
        clear("REARMED");active=session;
    }
    public static void clear(String reason) {
        Session previous=active;active=null;
        if(previous!=null){previous.budget.close(reason);previous.clearHeapNodes();}
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
        private boolean goalCoveragePartial;

        public Session(Mob subject, GoalSelector goal, GoalSelector target,
                       KneekuraDebugDecisionSnapshot snapshot, KneekuraDebugDecisionBurstBudget budget,
                       int nodeLimit, Set<String> channels, Supplier<KneekuraDebugDecisionBurstBudget.Context> currentContext,
                       LongSupplier time, Sink sink) throws ReflectiveOperationException {
            if(nodeLimit<1 || nodeLimit>64)throw new IllegalArgumentException("NODE_LIMIT_OUT_OF_RANGE");
            this.subject=subject;this.snapshot=snapshot;this.budget=budget;this.nodeLimit=nodeLimit;
            if(channels==null||channels.isEmpty()||!Set.of("goal","brain","path","control","malus","sensor","mod","projectile","neighbors","effective_malus","frontier","path_nodes","path_g","path_distance").containsAll(channels))
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
        private String token(Object object) {
            String token=identities.get(object);
            if(token!=null)return token;
            if(identities.size()>=128)return null;
            token="component:"+budget.context().selectionRevision()+":"+(++nextIdentity);identities.put(object,token);return token;
        }
        private boolean record(String kind,String method,Data capture) {
            if(thread!=Thread.currentThread())return false;
            String channel=kind.startsWith("CONTROL_PROJECTILE_")&&channels.contains("projectile")?"projectile":
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
                    kind.equals("PATH_NODE_CLOSED_CHECKPOINT")||kind.equals("PATH_NODE_G_WRITE_CHECKPOINT")?"ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY":"ORIGINAL_INVOCATION_RETURN_ONLY");
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
