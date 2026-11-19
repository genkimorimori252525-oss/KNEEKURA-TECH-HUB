package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import com.mojang.datafixers.util.Pair;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.Behavior;
import net.minecraft.world.entity.ai.behavior.BehaviorControl;
import net.minecraft.world.entity.ai.behavior.GateBehavior;
import net.minecraft.world.entity.ai.behavior.OneShot;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import org.objectweb.asm.*;

/** Genuine originals and compiled RETURN handlers; installed native Mixin proof is separate. */
public final class KneekuraDebugBehaviorControlSelfTest {
    private static Method recorder;
    private static final class Subject extends Mob {
        int brainQueries;Brain<?> retainedBrain;
        private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){brainQueries++;return retainedBrain;}
        @Override public String toString(){throw new AssertionError("ENTITY_STRING_REPLAY");}
    }
    private static final class Shot extends OneShot<LivingEntity> {
        int triggers;boolean result;RuntimeException failure;
        Shot(boolean result){this.result=result;}
        @Override public boolean trigger(ServerLevel level,LivingEntity entity,long tick){triggers++;if(failure!=null)throw failure;return result;}
        @Override public String debugString(){throw new AssertionError("TRIGGER_DESCRIPTION_REPLAY");}
        @Override public String toString(){throw new AssertionError("TRIGGER_STRING_REPLAY");}
    }
    private static final class Child implements BehaviorControl<LivingEntity> {
        int starts,ticks,stops,statusQueries;boolean succeeds;boolean forbid;
        Behavior.Status status=Behavior.Status.STOPPED;
        Child(boolean succeeds){this.succeeds=succeeds;}
        private void allowed(){if(forbid)throw new AssertionError("CHILD_REPLAY");}
        @Override public Behavior.Status getStatus(){allowed();statusQueries++;return status;}
        @Override public boolean tryStart(ServerLevel l,LivingEntity e,long t){allowed();starts++;if(succeeds)status=Behavior.Status.RUNNING;return succeeds;}
        @Override public void tickOrStop(ServerLevel l,LivingEntity e,long t){allowed();ticks++;status=Behavior.Status.STOPPED;}
        @Override public void doStop(ServerLevel l,LivingEntity e,long t){allowed();stops++;status=Behavior.Status.STOPPED;}
        @Override public String debugString(){throw new AssertionError("CHILD_DEBUG_REPLAY");}
        @Override public String toString(){throw new AssertionError("CHILD_STRING_REPLAY");}
    }
    private static final class Gate extends GateBehavior<LivingEntity> {
        Gate(Map<MemoryModuleType<?>,MemoryStatus> conditions,RunningPolicy policy,List<Pair<? extends BehaviorControl<? super LivingEntity>,Integer>> children){
            super(conditions,Set.of(),OrderPolicy.ORDERED,policy,children);
        }
        @Override public Behavior.Status getStatus(){throw new AssertionError("PARENT_STATUS_REPLAY");}
        @Override public String debugString(){throw new AssertionError("PARENT_DEBUG_REPLAY");}
        @Override public String toString(){throw new AssertionError("PARENT_STRING_REPLAY");}
    }
    private static void require(boolean b,String m){if(!b)throw new AssertionError(m);}
    private static JsonObject data(JsonObject r){return r.getAsJsonObject("data");}
    private static void emit(BehaviorControl<?> control,Subject subject,String kind,Boolean result)throws Exception {
        try{recorder.invoke(null,control,subject,kind,result);}
        catch(InvocationTargetException error){if(error.getCause() instanceof Error cause)throw cause;if(error.getCause() instanceof RuntimeException cause)throw cause;throw error;}
    }
    private static void originalStart(Shot shot,Subject subject)throws Exception {
        boolean result=shot.tryStart(null,subject,100);emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",result);
    }
    private static KneekuraDebugDecisionHooks.Session install(Subject subject,Set<String> channels,int events,int bytes,
            AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows,List<String> methods)throws Exception {
        var session=new KneekuraDebugDecisionHooks.Session(subject,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,
            (method,row)->{methods.add(method);rows.add(row);});KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static void handlerBytecode(String owner)throws Exception {
        String name="com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/KneekuraDebug"+owner+"DecisionMixin";
        int[] handlers={0};try(var stream=KneekuraDebugBehaviorControlSelfTest.class.getClassLoader().getResourceAsStream(name+".class")){
            require(stream!=null,"compiled known-control RETURN mixin required");new ClassReader(stream).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String method,String descriptor,String signature,String[] exceptions){
                    if(!method.startsWith("kneekura$"))return null;handlers[0]++;int[] injections={0},captures={0},returns={0},required={0};
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public AnnotationVisitor visitAnnotation(String desc,boolean visible){
                            if(!desc.endsWith("/Inject;"))return null;injections[0]++;
                            return new AnnotationVisitor(Opcodes.ASM9){
                                @Override public void visit(String key,Object value){if(key.equals("require"))required[0]=(Integer)value;if(key.equals("cancellable"))require(Boolean.FALSE.equals(value),"must not cancel original");}
                                @Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String k,Object v){String s=(String)v;require(s.matches("(tryStart|tickOrStop|doStop)\\(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J\\)(Z|V)"),"exact original descriptor");}};return new AnnotationVisitor(Opcodes.ASM9){@Override public AnnotationVisitor visitAnnotation(String k,String d){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String k,Object v){if(k.equals("value")){require(v.equals("RETURN"),"normal original return only");returns[0]++;}}};}};}
                            };
                        }
                        @Override public void visitMethodInsn(int opcode,String target,String call,String desc,boolean itf){
                            if(target.endsWith("/KneekuraDebugDecisionHooks")&&call.equals("behaviorControlReturn")){require(opcode==Opcodes.INVOKESTATIC,"one static observation");captures[0]++;}
                            else require(target.endsWith("/CallbackInfoReturnable")&&call.equals("getReturnValue"),"handler cannot replay lifecycle/getters or mutate original return");
                        }
                        @Override public void visitEnd(){require(injections[0]==1&&captures[0]==1&&returns[0]==1&&required[0]==1,"one required noncancelling RETURN capture");}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }require(handlers[0]==3,"all original lifecycle normal returns");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        var subject=(Subject)unsafe.allocateInstance(Subject.class);var other=(Subject)unsafe.allocateInstance(Subject.class);
        subject.retainedBrain=(Brain<?>)unsafe.allocateInstance(Brain.class);
        var memories=Brain.class.getDeclaredField("memories");memories.setAccessible(true);memories.set(subject.retainedBrain,new HashMap<>());
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));
        var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();var methods=new ArrayList<String>();
        var shot=new Shot(true);boolean accepted=shot.tryStart(null,subject,100);require(accepted&&shot.triggers==1,"genuine OneShot trigger exactly once");
        try{recorder=KneekuraDebugDecisionHooks.class.getMethod("behaviorControlReturn",BehaviorControl.class,LivingEntity.class,String.class,Boolean.class);}
        catch(NoSuchMethodException error){throw new AssertionError("independent OneShot/Gate original callback observation missing",error);}
        KneekuraDebugDecisionHooks.clear("OFF");emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",accepted);require(shot.triggers==1,"OFF never replays trigger");
        install(subject,Set.of("brain"),256,524288,context,time,rows,methods);emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",accepted);
        shot.tickOrStop(null,subject,100);emit(shot,subject,"BEHAVIOR_STOP_RETURN",null);emit(shot,subject,"BEHAVIOR_TICK_OR_STOP_RETURN",null);
        require(shot.triggers==1&&data(rows.get(0)).get("cachedStatus").getAsString().equals("RUNNING")&&data(rows.get(1)).get("cachedStatus").getAsString().equals("STOPPED"),"detached actual cached lifecycle facts");
        var rejected=new Shot(false);originalStart(rejected,subject);require(rejected.triggers==1&&!data(rows.get(3)).get("result").getAsBoolean(),"actual false return retained");
        int count=rows.size();var failing=new Shot(true);var failure=new IllegalStateException("original trigger failure");failing.failure=failure;
        try{originalStart(failing,subject);throw new AssertionError("original exception lost");}catch(IllegalStateException error){require(error==failure,"same original exception");}require(failing.triggers==1&&rows.size()==count,"throwing original has no normal-return event");
        var child=new Child(false);var gate=new Gate(Map.of(),GateBehavior.RunningPolicy.RUN_ONE,List.of(Pair.of(child,1)));
        boolean parent=gate.tryStart(null,subject,100);require(parent&&child.starts==1&&child.status==Behavior.Status.STOPPED,"parent true does not mean child success");
        child.forbid=true;emit(gate,subject,"BEHAVIOR_TRY_START_RETURN",parent);child.forbid=false;
        require(data(rows.get(4)).get("result").getAsBoolean()&&data(rows.get(4)).get("reasonStatus").getAsString().equals("NOT_EXPOSED"),"parent-only original fact, no invented child result or reason");
        gate.tickOrStop(null,subject,100);int brainQueries=subject.brainQueries;child.forbid=true;emit(gate,subject,"BEHAVIOR_STOP_RETURN",null);emit(gate,subject,"BEHAVIOR_TICK_OR_STOP_RETURN",null);
        require(child.starts==1&&child.ticks==0&&subject.brainQueries==brainQueries&&data(rows.get(5)).get("cachedStatus").getAsString().equals("STOPPED"),"observer cannot read children/status/brain or rerun policy");
        child.forbid=false;var first=new Child(false);var second=new Child(true);var third=new Child(true);var one=new Gate(Map.of(),GateBehavior.RunningPolicy.RUN_ONE,List.of(Pair.of(first,1),Pair.of(second,1),Pair.of(third,1)));
        parent=one.tryStart(null,subject,100);require(first.starts==1&&second.starts==1&&third.starts==0,"RUN_ONE original stops at first successful stopped child");first.forbid=second.forbid=third.forbid=true;emit(one,subject,"BEHAVIOR_TRY_START_RETURN",parent);
        var allA=new Child(false);var allB=new Child(true);var all=new Gate(Map.of(),GateBehavior.RunningPolicy.TRY_ALL,List.of(Pair.of(allA,1),Pair.of(allB,1)));parent=all.tryStart(null,subject,100);require(allA.starts==1&&allB.starts==1,"TRY_ALL originals each once");allA.forbid=allB.forbid=true;emit(all,subject,"BEHAVIOR_TRY_START_RETURN",parent);
        var absent=new Gate(Map.of(MemoryModuleType.WALK_TARGET,MemoryStatus.VALUE_PRESENT),GateBehavior.RunningPolicy.RUN_ONE,List.of());parent=absent.tryStart(null,subject,100);brainQueries=subject.brainQueries;emit(absent,subject,"BEHAVIOR_TRY_START_RETURN",parent);require(!parent&&subject.brainQueries==brainQueries,"actual missing-memory failure without observer replay");
        var sticky=new Shot(true);originalStart(sticky,subject);sticky.result=false;originalStart(sticky,subject);
        require(sticky.triggers==2&&!data(rows.get(rows.size()-1)).get("result").getAsBoolean()&&data(rows.get(rows.size()-1)).get("cachedStatus").getAsString().equals("RUNNING"),"false original return does not imply stopped status");
        var interop=new ArrayList<>(rows);count=rows.size();emit(shot,other,"BEHAVIOR_TRY_START_RETURN",true);emit(shot,subject,"UNKNOWN",true);
        Thread worker=new Thread(()->{try{emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",true);}catch(Exception e){throw new RuntimeException(e);}});worker.start();worker.join();require(rows.size()==count,"selection/thread/unknown kind fence");
        var unsupported=new Child(false);unsupported.forbid=true;emit(unsupported,subject,"BEHAVIOR_TRY_START_RETURN",true);require(rows.size()==count,"arbitrary BehaviorControl stays unobserved");
        rows.clear();methods.clear();install(subject,Set.of("brain"),256,524288,context,time,rows,methods);
        var retained=new Shot(false);for(int i=0;i<130;i++)emit(i==0?retained:new Shot(false),subject,"BEHAVIOR_TRY_START_RETURN",false);
        require(data(rows.get(127)).get("instanceIdentity").getAsString().equals("component:7:128")&&data(rows.get(129)).get("instanceIdentity").isJsonNull(),"shared128 reference cap preserves unknown, no eviction");interop.add(rows.get(129));emit(retained,subject,"BEHAVIOR_TRY_START_RETURN",false);require(data(rows.get(130)).get("instanceIdentity").getAsString().equals("component:7:1"),"known identity remains stable after cap");
        context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,context.get().subjectUuid(),context.get().dimension()));count=rows.size();emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",true);require(rows.size()==count,"revision change refuses observation");
        rows.clear();install(subject,Set.of("brain"),2,524288,context,time,rows,methods);emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",true);require(data(rows.get(0)).get("instanceIdentity").getAsString().equals("component:8:1"),"reselection component scope reset");emit(shot,subject,"BEHAVIOR_STOP_RETURN",null);emit(shot,subject,"BEHAVIOR_STOP_RETURN",null);require(rows.size()==2,"finite event fence");
        rows.clear();install(subject,Set.of("sensor"),8,65536,context,time,rows,methods);emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",true);require(rows.isEmpty(),"brain opt-in only");
        install(subject,Set.of("brain"),8,1,context,time,rows,methods);emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",true);require(rows.isEmpty(),"byte fence");
        install(subject,Set.of("brain"),8,65536,context,time,rows,methods);time.set(200);emit(shot,subject,"BEHAVIOR_TRY_START_RETURN",true);require(rows.isEmpty(),"time window fence");
        KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");handlerBytecode("OneShot");handlerBytecode("GateBehavior");
        for(var row:interop)System.out.println("BEHAVIOR_CONTROL_INTEROP:"+new com.google.gson.Gson().toJson(row));
        System.out.println("Genuine OneShot/Gate returns: original counters/exceptions, parent-only results, cached status, no trigger/child/getter replay, shared cap/reset and fences; compiled RETURN handlers, not native installed proof");
    }
}