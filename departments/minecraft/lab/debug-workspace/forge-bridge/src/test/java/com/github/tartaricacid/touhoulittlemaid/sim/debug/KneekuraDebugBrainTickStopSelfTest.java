package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.common.collect.ImmutableList;
import com.google.gson.JsonObject;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.Behavior;
import net.minecraft.world.entity.ai.behavior.BehaviorControl;
import net.minecraft.world.entity.ai.behavior.MoveToTargetSink;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.phys.Vec3;
import java.lang.reflect.*;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.level.pathfinder.Node;
import org.objectweb.asm.*;
import org.objectweb.asm.Type;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/** Genuine original tickOrStop baseline and source-specific observation contract. */
public final class KneekuraDebugBrainTickStopSelfTest {
    private static final class Subject extends Mob {
        int brains,navigations;
        private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){brains++;return (Brain<?>)read(this,LivingEntity.class,"brain");}
        @Override public PathNavigation getNavigation(){navigations++;return (PathNavigation)read(this,Mob.class,"navigation");}
    }
    private static final class ProbeBrain extends Brain<Mob> {
        int queries,erases,memoryReads;RuntimeException failure;Runnable duringMemory;
        ProbeBrain(){super(List.of(MemoryModuleType.PATH,MemoryModuleType.WALK_TARGET),List.of(),ImmutableList.of(),()->null);}
        @Override public <U> Optional<U> getMemory(MemoryModuleType<U> type){memoryReads++;if(duringMemory!=null)duringMemory.run();if(failure!=null)throw failure;return super.getMemory(type);}
        @Override public boolean hasMemoryValue(MemoryModuleType<?> type){queries++;return super.hasMemoryValue(type);}
        @Override public <U> void eraseMemory(MemoryModuleType<U> type){erases++;super.eraseMemory(type);}
    }
    private static final class Navigation extends PathNavigation {
        int stops,doneQueries,pathQueries;boolean done;RuntimeException failure;
        Navigation(Mob mob,Level level){super(mob,level);}
        @Override public void stop(){stops++;if(failure!=null)throw failure;super.stop();}
        @Override public boolean isDone(){doneQueries++;return done;}
        @Override public Path getPath(){pathQueries++;return (Path)read(this,PathNavigation.class,"path");}
        @Override protected PathFinder createPathFinder(int limit){throw new AssertionError("SEARCH_REPLAY");}
        @Override protected Vec3 getTempMobPos(){throw new AssertionError("POSITION_REPLAY");}
        @Override protected boolean canUpdatePath(){throw new AssertionError("UPDATE_REPLAY");}
    }
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static Object read(Object owner,Class<?> base,String name){try{return KneekuraDebugDecisionSnapshot.read(base,name,owner);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static void field(Object owner,Class<?> base,String name,Object value){try{var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    @SuppressWarnings({"rawtypes","unchecked"})
    private static void original(Brain<?> brain,MoveToTargetSink behavior,Subject owner,long game)throws Exception {
        try {var method=KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainTickOrStop",Brain.class,BehaviorControl.class,ServerLevel.class,LivingEntity.class,long.class);method.invoke(null,brain,behavior,null,owner,game);}
        catch(NoSuchMethodException absent){behavior.tickOrStop(null,owner,game);}
        catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException error)throw error;if(e.getCause() instanceof Error error)throw error;throw e;}
    }
    private static Method tickFixture,stopFixture;private static int timedCalls,canCalls,tickCalls,stopCalls;
    private static Object call(Method m,Object receiver,Object... args){try{return m.invoke(receiver,args);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException error)throw error;if(e.getCause() instanceof Error error)throw error;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Object protectedCall(Behavior<?> behavior,String method,Class<?>[] types,Object... args){try{var m=Behavior.class.getDeclaredMethod(method,types);m.setAccessible(true);return call(m,behavior,args);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    public static boolean originalTimedOut(Behavior<?> behavior,long tick){return KneekuraDebugDecisionHooks.originalBrainCondition(behavior,tick,"TIMED_OUT",null,null,()->{timedCalls++;return (Boolean)protectedCall(behavior,"timedOut",new Class<?>[]{long.class},tick);});}
    public static boolean originalCanStillUse(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long tick){return KneekuraDebugDecisionHooks.originalBrainCondition(behavior,tick,"CAN_STILL_USE",level,owner,()->{canCalls++;return (Boolean)protectedCall(behavior,"canStillUse",new Class<?>[]{ServerLevel.class,LivingEntity.class,long.class},level,owner,tick);});}
    public static void originalTick(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long tick){KneekuraDebugDecisionHooks.originalBrainDispatch(behavior,level,owner,tick,"TICK",()->{tickCalls++;KneekuraDebugDecisionHooks.originalSinkCall((MoveToTargetSink)behavior,(Mob)owner,tick,"TICK_FROM_BRIDGE",()->protectedCall(behavior,"tick",new Class<?>[]{ServerLevel.class,LivingEntity.class,long.class},level,owner,tick));});}
    public static void originalDoStop(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long tick){KneekuraDebugDecisionHooks.originalBrainDispatch(behavior,level,owner,tick,"STOP",()->{stopCalls++;call(stopFixture,null,behavior,level,owner,tick);});}
    public static void originalStop(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long tick){KneekuraDebugDecisionHooks.originalSinkCall((MoveToTargetSink)behavior,(Mob)owner,tick,"STOP_FROM_BRIDGE",()->protectedCall(behavior,"stop",new Class<?>[]{ServerLevel.class,LivingEntity.class,long.class},level,owner,tick));}
    public static void setStatus(Behavior<?> behavior,Behavior.Status status){field(behavior,Behavior.class,"status",status);}
    private static void fixtures()throws Exception {
        String behavior=Type.getInternalName(Behavior.class),test=Type.getInternalName(KneekuraDebugBrainTickStopSelfTest.class),name=test+"$ActualControlFixture";
        var writer=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);writer.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);var seen=new HashMap<String,Integer>();int[] writes={0};
        try(var bytes=Behavior.class.getResourceAsStream("Behavior.class")){require(bytes!=null,"genuine Behavior required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
            @Override public MethodVisitor visitMethod(int access,String method,String desc,String signature,String[] exceptions){if(!Set.of("tickOrStop","doStop").contains(method))return null;seen.merge(method,1,Integer::sum);
                return new MethodVisitor(Opcodes.ASM9,writer.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,method,"(L"+behavior+";"+desc.substring(1),null,exceptions)){
                    @Override public void visitFieldInsn(int op,String owner,String field,String descriptor){if(owner.equals(behavior)&&field.equals("status")&&op==Opcodes.PUTFIELD){writes[0]++;super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"setStatus","(L"+behavior+";"+descriptor+")V",false);return;}super.visitFieldInsn(op,owner,field,descriptor);}
                    @Override public void visitMethodInsn(int op,String owner,String call,String descriptor,boolean itf){if(owner.equals(behavior)){String delegate=switch(call){case "timedOut"->"originalTimedOut";case "canStillUse"->"originalCanStillUse";case "tick"->"originalTick";case "doStop"->"originalDoStop";case "stop"->"originalStop";default->throw new AssertionError("UNEXPECTED_BEHAVIOR_CALL:"+call);};seen.merge(call+"call",1,Integer::sum);super.visitMethodInsn(Opcodes.INVOKESTATIC,test,delegate,"(L"+behavior+";"+descriptor.substring(1),false);return;}super.visitMethodInsn(op,owner,call,descriptor,itf);}
                };}
        },ClassReader.SKIP_FRAMES);}require(writes[0]==1&&seen.equals(Map.of("tickOrStop",1,"doStop",1,"timedOutcall",1,"canStillUsecall",1,"tickcall",1,"doStopcall",1,"stopcall",1)),"exact genuine short-circuit/dispatch/status-write source");writer.visitEnd();byte[] bytes=writer.toByteArray();
        class Loader extends ClassLoader{Loader(){super(KneekuraDebugBrainTickStopSelfTest.class.getClassLoader());}Class<?> define(){return defineClass(name.replace('/','.'),bytes,0,bytes.length);}}
        var fixture=new Loader().define();tickFixture=fixture.getMethod("tickOrStop",Behavior.class,ServerLevel.class,LivingEntity.class,long.class);stopFixture=fixture.getMethod("doStop",Behavior.class,ServerLevel.class,LivingEntity.class,long.class);
    }
    private static void invokeFixture(Brain<?> brain,BehaviorControl<?> control,LivingEntity owner,long tick,Runnable original){try{var m=KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainCall",Brain.class,BehaviorControl.class,ServerLevel.class,LivingEntity.class,long.class,Runnable.class);m.setAccessible(true);call(m,null,brain,control,null,owner,tick,original);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static KneekuraDebugDecisionHooks.Session install(Subject owner,Set<String> channels,int events,int bytes,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(context.get().selectionRevision());var session=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static void seed(Subject owner,Navigation nav,ProbeBrain brain,MoveToTargetSink behavior,long end,boolean walking){
        timedCalls=canCalls=tickCalls=stopCalls=owner.brains=owner.navigations=nav.stops=nav.doneQueries=nav.pathQueries=brain.queries=brain.erases=brain.memoryReads=0;nav.done=false;nav.failure=brain.failure=null;brain.duringMemory=null;
        field(behavior,Behavior.class,"endTimestamp",end);setStatus(behavior,Behavior.Status.RUNNING);var pos=new BlockPos(10,0,0);var path=new Path(new ArrayList<>(List.of(new Node(0,0,0))),pos,false);
        field(owner,net.minecraft.world.entity.Entity.class,"blockPosition",BlockPos.ZERO);field(nav,PathNavigation.class,"path",walking?path:null);field(behavior,MoveToTargetSink.class,"path",walking?path:null);field(behavior,MoveToTargetSink.class,"lastTargetPos",walking?pos:null);
        brain.eraseMemory(MemoryModuleType.WALK_TARGET);if(walking)brain.setMemory(MemoryModuleType.WALK_TARGET,new WalkTarget(pos,0.5f,0));brain.erases=0;
    }
    private static void emit(List<JsonObject> rows){for(var row:rows)System.out.println("BRAIN_TICK_STOP_INTEROP:"+new com.google.gson.Gson().toJson(row));}
    private static List<JsonObject> upstream(List<JsonObject> rows){return rows.stream().filter(r->Set.of("BRAIN_PATH_CONDITION_RETURN","BRAIN_PATH_DISPATCH_RETURN").contains(r.get("kind").getAsString())).toList();}
    private static void sameScope(List<JsonObject> rows,int conditions,String branch){var data=upstream(rows);require(data.size()==conditions+1,"actual condition and normal dispatch count");String id=data.get(0).getAsJsonObject("data").get("tickOrStopInvocationId").getAsString();require(data.stream().allMatch(r->id.equals(r.getAsJsonObject("data").get("tickOrStopInvocationId").getAsString())),"direct same control scope");var last=data.get(data.size()-1).getAsJsonObject("data");require(last.get("branch").getAsString().equals(branch)&&last.getAsJsonArray("capturedSinkInvocationIds").size()==1,"direct concrete child scope");String child=last.getAsJsonArray("capturedSinkInvocationIds").get(0).getAsString();require(rows.stream().filter(r->r.get("kind").getAsString().equals("BRAIN_PATH_SINK_RETURN")).anyMatch(r->r.getAsJsonObject("data").get("sinkInvocationId").getAsString().equals(child)),"child ID comes from actual captured call, not time adjacency");}
    private static void nested(int count,Brain<?> brain,MoveToTargetSink behavior,Subject owner){invokeFixture(brain,behavior,owner,100,()->{if(count==1)call(tickFixture,null,behavior,null,owner,100L);else nested(count-1,brain,behavior,owner);});}
    private static void compiledHandlers()throws Exception {
        String living="(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)V",behavior="Lnet/minecraft/world/entity/ai/behavior/Behavior;",brainLoop="tickEachRunningBehavior(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V";
        var expected=Map.of("kneekura$originalTickOrStop",new String[]{brainLoop,"Lnet/minecraft/world/entity/ai/behavior/BehaviorControl;tickOrStop"+living,"originalBrainTickOrStop"},
            "kneekura$originalTimedOut",new String[]{"tickOrStop"+living,behavior+"timedOut(J)Z","originalBrainCondition"},"kneekura$originalCanStillUse",new String[]{"tickOrStop"+living,behavior+"canStillUse"+living.replace(")V",")Z"),"originalBrainCondition"},
            "kneekura$originalTick",new String[]{"tickOrStop"+living,behavior+"tick"+living,"originalBrainDispatch"},"kneekura$originalStop",new String[]{"tickOrStop"+living,behavior+"doStop"+living,"originalBrainDispatch"});
        var found=new HashSet<String>();int[] protectedDelegates={0},finalStop={0},shadows={0};
        for(String name:List.of("Brain","Behavior"))try(var bytes=KneekuraDebugBrainTickStopSelfTest.class.getClassLoader().getResourceAsStream("com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/KneekuraDebug"+name+"DecisionMixin.class")){
            require(bytes!=null,"compiled source mixin required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String method,String descriptor,String signature,String[] exceptions){
                if(Set.of("timedOut","canStillUse","tick").contains(method))return new MethodVisitor(Opcodes.ASM9){@Override public AnnotationVisitor visitAnnotation(String descriptor,boolean visible){if(descriptor.equals("Lorg/spongepowered/asm/mixin/Shadow;"))shadows[0]++;return null;}};
                if(method.startsWith("lambda$kneekura$original"))return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String call,String desc,boolean itf){require(op==Opcodes.INVOKEVIRTUAL,"original virtual dispatch required");if(call.equals("doStop")){require(owner.equals("net/minecraft/world/entity/ai/behavior/Behavior")&&desc.equals(living),"exact final doStop delegate");finalStop[0]++;}else {require(owner.endsWith("/KneekuraDebugBehaviorDecisionMixin")&&Set.of("timedOut","canStillUse","tick").contains(call),"single protected Shadow original");protectedDelegates[0]++;}}};
                var spec=expected.get(method);if(spec==null)return null;found.add(method);int[] selectors={0},targets={0},required={0},calls={0};return new MethodVisitor(Opcodes.ASM9){
                    private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object value){if(key.equals("require"))required[0]=(Integer)value;if(key.equals("target")){require(value.equals(spec[1]),"exact condition/dispatch target");targets[0]++;}}
                        @Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String ignored,Object value){require(value.equals(spec[0]),"exact source descriptor");selectors[0]++;}};return annotation();}
                        @Override public AnnotationVisitor visitAnnotation(String name,String desc){return annotation();}};}
                    @Override public AnnotationVisitor visitAnnotation(String descriptor,boolean visible){if(descriptor.equals("Lorg/spongepowered/asm/mixin/injection/Redirect;"))return annotation();return null;}
                    @Override public void visitMethodInsn(int op,String owner,String call,String desc,boolean itf){if(owner.endsWith("/KneekuraDebugDecisionHooks")){require(op==Opcodes.INVOKESTATIC&&call.equals(spec[2]),"single production wrapper");calls[0]++;}}
                    @Override public void visitEnd(){require(selectors[0]==1&&targets[0]==1&&required[0]==1&&calls[0]==1,"exact mandatory source redirect "+method+" selectors="+selectors[0]+" targets="+targets[0]+" require="+required[0]+" calls="+calls[0]);}
                };}
            },0);
        }
        require(found.equals(expected.keySet())&&protectedDelegates[0]==3&&finalStop[0]==1&&shadows[0]==3,"five exact redirects/three protected Shadow delegates/one original final stop");
        int[] interfaceCalls={0};try(var bytes=KneekuraDebugDecisionHooks.class.getResourceAsStream("KneekuraDebugDecisionHooks.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int a,String n,String d,String sig,String[] ex){if(!n.startsWith("lambda$originalBrainTickOrStop$"))return null;return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String call,String desc,boolean itf){require(op==Opcodes.INVOKEINTERFACE&&owner.equals("net/minecraft/world/entity/ai/behavior/BehaviorControl")&&call.equals("tickOrStop")&&desc.equals(living),"original source interface delegate exactly once");interfaceCalls[0]++;}};}},0);}require(interfaceCalls[0]==1,"single source interface lambda");
    }
    private static final class CustomSink extends MoveToTargetSink { }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        var owner=(Subject)unsafe.allocateInstance(Subject.class);var nav=(Navigation)unsafe.allocateInstance(Navigation.class);field(nav,PathNavigation.class,"mob",owner);field(owner,Mob.class,"navigation",nav);var brain=new ProbeBrain();field(owner,LivingEntity.class,"brain",brain);var behavior=new MoveToTargetSink();field(behavior,Behavior.class,"endTimestamp",100L);
        behavior.tickOrStop(null,owner,100L);require(owner.brains==3&&owner.navigations==1&&brain.queries==1&&brain.erases==2&&nav.stops==1,"genuine equal-deadline, absent-path stop original queries/calls once");
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(7);
        var session=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);
        original(brain,behavior,owner,100L);require(owner.brains==6&&owner.navigations==2&&brain.queries==2&&brain.erases==4&&nav.stops==2,"observer never replays original query or dispatch");
        require(rows.isEmpty()&&read(session,KneekuraDebugDecisionHooks.Session.class,"tickStopFrame")==null,"untransformed genuine bytecode does not fake installed condition callbacks");fixtures();
        for(String mode:List.of("EQUAL_DEADLINE_STOP","TIMED_OUT_STOP","CONTINUE_TICK")){
            rows.clear();seed(owner,nav,brain,behavior,mode.equals("TIMED_OUT_STOP")?99L:100L,mode.equals("CONTINUE_TICK"));install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));
            require(timedCalls==1&&canCalls==(mode.equals("TIMED_OUT_STOP")?0:1)&&stopCalls==(mode.equals("CONTINUE_TICK")?0:1)&&tickCalls==(mode.equals("CONTINUE_TICK")?1:0),"original booleans and dispatch once/short circuit");sameScope(rows,mode.equals("TIMED_OUT_STOP")?1:2,mode.equals("CONTINUE_TICK")?"TICK":"STOP");
            if(mode.equals("CONTINUE_TICK"))require(brain.memoryReads==2&&nav.doneQueries==1&&nav.pathQueries==1&&owner.brains==2&&owner.navigations==2&&brain.queries==0&&brain.erases==0&&nav.stops==0,"genuine continuation/tick operands execute once without observer replay");
            else require(owner.brains==3&&owner.navigations==1&&brain.queries==1&&brain.erases==2&&brain.memoryReads==0&&nav.stops==1,"stop short-circuits original continuation query; original stop calls once");emit(upstream(rows));
        }
        var failure=new IllegalStateException("ORIGINAL_CONDITION_FAILURE");rows.clear();seed(owner,nav,brain,behavior,100,true);brain.failure=failure;session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);try{invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));throw new AssertionError("original condition must throw");}catch(IllegalStateException e){require(e==failure,"original condition exception identity");}require(rows.size()==1&&canCalls==1&&tickCalls==0&&stopCalls==0&&read(session,KneekuraDebugDecisionHooks.Session.class,"tickStopFrame")==null,"no failed condition/branch normal return or frame leak");emit(upstream(rows));
        rows.clear();seed(owner,nav,brain,behavior,100,false);nav.failure=failure;session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);try{invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));throw new AssertionError("original dispatch must throw");}catch(IllegalStateException e){require(e==failure,"original dispatch exception identity");}require(rows.size()==2&&stopCalls==1&&read(session,KneekuraDebugDecisionHooks.Session.class,"tickStopFrame")==null&&read(session,KneekuraDebugDecisionHooks.Session.class,"sinkFrame")==null,"prior conditions retained, no failed normal dispatch or Sink return");emit(upstream(rows));
        rows.clear();seed(owner,nav,brain,behavior,100,false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));sameScope(rows,2,"STOP");emit(upstream(rows));
        for(String fence:List.of("OFF","TIME","REVISION","OWNER","NAV_OWNER","BYTE","EVENT")){
            rows.clear();seed(owner,nav,brain,behavior,100,false);time.set(100);var previous=context.get();session=install(owner,fence.equals("OFF")?Set.of("brain"):Set.of("brain_navigation"),fence.equals("EVENT")?1:256,fence.equals("BYTE")?1:524288,context,time,rows);
            var other=(Subject)unsafe.allocateInstance(Subject.class);if(fence.equals("TIME"))time.set(200);if(fence.equals("REVISION"))context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,previous.subjectUuid(),previous.dimension()));if(fence.equals("NAV_OWNER"))field(nav,PathNavigation.class,"mob",other);
            invokeFixture(brain,behavior,fence.equals("OWNER")?other:owner,100,()->call(tickFixture,null,behavior,null,owner,100L));require(upstream(rows).size()==(fence.equals("EVENT")?1:0)&&stopCalls==1&&timedCalls==1&&canCalls==1,"all capture fences preserve original dispatch "+fence);if(fence.equals("OWNER"))require(rows.size()==1&&rows.get(0).get("kind").getAsString().equals("BRAIN_PATH_SINK_RETURN"),"independent valid concrete Sink callback is not attributed to invalid upstream owner");context.set(previous);field(nav,PathNavigation.class,"mob",owner);
        }
        rows.clear();time.set(100);seed(owner,nav,brain,behavior,100,false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var workerError=new AtomicReference<Throwable>();var worker=new Thread(()->{try{invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));}catch(Throwable e){workerError.set(e);}});worker.start();worker.join();require(rows.isEmpty()&&workerError.get()==null&&stopCalls==1,"wrong-thread originals once");
        rows.clear();seed(owner,nav,brain,behavior,100,false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var custom=new CustomSink();field(custom,Behavior.class,"endTimestamp",100L);invokeFixture(brain,custom,owner,100,()->call(tickFixture,null,custom,null,owner,100L));require(rows.isEmpty()&&stopCalls==1,"custom Sink bypasses observation, originals once");
        rows.clear();seed(owner,nav,brain,behavior,100,true);var old=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);brain.duringMemory=()->{try{install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);}catch(Exception e){throw new AssertionError(e);}};invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));require(rows.size()==1&&read(old,KneekuraDebugDecisionHooks.Session.class,"tickStopFrame")==null,"rearm during original condition cannot revive old frame/dispatch");
        rows.clear();seed(owner,nav,brain,behavior,100,false);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);nested(8,brain,behavior,owner);sameScope(rows,2,"STOP");require(upstream(rows).get(0).getAsJsonObject("data").get("tickOrStopInvocationId").getAsString().equals("tick-stop:7:8"),"depth8 scope only");
        rows.clear();seed(owner,nav,brain,behavior,100,false);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);nested(9,brain,behavior,owner);require(upstream(rows).isEmpty()&&stopCalls==1&&read(session,KneekuraDebugDecisionHooks.Session.class,"tickStopFrame")==null,"depth9 suppresses upstream scope without losing original");
        rows.clear();seed(owner,nav,brain,behavior,100,false);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);for(int i=0;i<256;i++)original(brain,behavior,owner,100);require((Integer)read(session,KneekuraDebugDecisionHooks.Session.class,"nextSink")==0,"light scopes do not burn concrete Sink IDs");invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));require(upstream(rows).isEmpty()&&(Integer)read(session,KneekuraDebugDecisionHooks.Session.class,"nextTickStop")==256&&stopCalls==1,"invocation cap preserves original/independent concrete callback");
        rows.clear();seed(owner,nav,brain,behavior,100,false);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var token=KneekuraDebugDecisionHooks.Session.class.getDeclaredMethod("token",Object.class);token.setAccessible(true);for(int i=0;i<128;i++)call(token,session,new Object());invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));require(upstream(rows).size()==3&&upstream(rows).get(0).getAsJsonObject("data").get("instanceIdentityStatus").getAsString().equals("NOT_EXPOSED"),"component cap is explicit unknown");emit(upstream(rows));
        rows.clear();seed(owner,nav,brain,behavior,100,true);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invokeFixture(brain,behavior,owner,100,()->KneekuraDebugDecisionHooks.originalBrainDispatch(behavior,null,owner,100,"TICK",()->{for(int i=0;i<9;i++)KneekuraDebugDecisionHooks.originalSinkCall(behavior,owner,100,"TICK_FROM_BRIDGE",()->protectedCall(behavior,"tick",new Class<?>[]{ServerLevel.class,LivingEntity.class,long.class},null,owner,100L));}));var capped=upstream(rows);require(capped.size()==1&&capped.get(0).getAsJsonObject("data").getAsJsonArray("capturedSinkInvocationIds").size()==8&&capped.get(0).getAsJsonObject("data").get("capturedSinkInvocationsTruncated").getAsBoolean(),"test-only repeated concrete calls expose bounded child tail");
        rows.clear();seed(owner,nav,brain,behavior,100,false);var broken=new KneekuraDebugDecisionHooks.Session(owner,null,null,new KneekuraDebugDecisionSnapshot(),new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->{throw new java.io.IOException("WRITER_FAILURE");});KneekuraDebugDecisionHooks.install(broken);invokeFixture(brain,behavior,owner,100,()->call(tickFixture,null,behavior,null,owner,100L));require(broken.budget().reason().equals("WRITER_UNAVAILABLE")&&stopCalls==1&&read(broken,KneekuraDebugDecisionHooks.Session.class,"tickStopFrame")==null,"writer failure closes only capture");
        for(String fence:List.of("CONDITION_OWNER","CONDITION_LEVEL","CONDITION_TIME","CONDITION_KIND")){
            rows.clear();seed(owner,nav,brain,behavior,100,false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var other=(Subject)unsafe.allocateInstance(Subject.class);var otherLevel=(ServerLevel)unsafe.allocateInstance(ServerLevel.class);int[] originalCalls={0};
            invokeFixture(brain,behavior,owner,100,()->require(!KneekuraDebugDecisionHooks.originalBrainCondition(behavior,fence.equals("CONDITION_TIME")?101:100,fence.equals("CONDITION_KIND")?"REACHED_TARGET":"CAN_STILL_USE",fence.equals("CONDITION_LEVEL")?otherLevel:null,fence.equals("CONDITION_OWNER")?other:owner,()->{originalCalls[0]++;return false;}),"original mismatched condition boolean unchanged"));
            require(rows.isEmpty()&&originalCalls[0]==1,"mismatched continuation arguments cannot acquire selected source frame "+fence);
        }
        compiledHandlers();
        System.out.println("Original tick-or-stop fixture: genuine boolean short circuit/dispatch/child scope/original once/exception/OFF/thread/owner/budget/rearm; not installed native or individual operand reason/arrival proof");
        KneekuraDebugDecisionHooks.clear("DONE");
    }
}
