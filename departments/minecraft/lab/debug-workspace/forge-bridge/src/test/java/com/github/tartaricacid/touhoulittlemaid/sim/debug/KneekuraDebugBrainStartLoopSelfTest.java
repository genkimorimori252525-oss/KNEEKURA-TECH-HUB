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
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.schedule.Activity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.WritableLevelData;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.phys.Vec3;
import org.objectweb.asm.*;
import org.objectweb.asm.Type;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/** Actual private Brain loop bytecode, with only field access and the three source delegates replaced. */
public final class KneekuraDebugBrainStartLoopSelfTest {
    private static final class Subject extends Mob {
        int brains;private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){brains++;return (Brain<?>)read(this,LivingEntity.class,"brain");}
    }
    private static final class Navigation extends PathNavigation {
        private Navigation(Mob owner,Level level){super(owner,level);}
        @Override protected PathFinder createPathFinder(int limit){throw new AssertionError("SEARCH_REPLAY");}
        @Override protected Vec3 getTempMobPos(){throw new AssertionError("POSITION_REPLAY");}
        @Override protected boolean canUpdatePath(){throw new AssertionError("UPDATE_REPLAY");}
    }
    private static final class Control implements BehaviorControl<LivingEntity> {
        final String name;Behavior.Status status;boolean result;int statuses,starts;Runnable duringStatus,duringStart;RuntimeException statusFailure,startFailure;
        Control(String name,Behavior.Status status,boolean result){this.name=name;this.status=status;this.result=result;}
        public Behavior.Status getStatus(){statuses++;order.add(name+":status");if(duringStatus!=null)duringStatus.run();if(statusFailure!=null)throw statusFailure;return status;}
        public boolean tryStart(ServerLevel level,LivingEntity owner,long game){starts++;order.add(name+":start:"+game);if(duringStart!=null)duringStart.run();if(startFailure!=null)throw startFailure;return result;}
        public void tickOrStop(ServerLevel level,LivingEntity owner,long game){throw new AssertionError("TICK_REPLAY");}
        public void doStop(ServerLevel level,LivingEntity owner,long game){throw new AssertionError("STOP_REPLAY");}
        public String debugString(){throw new AssertionError("DEBUG_STRING_QUERY");}
    }
    private static final class Active extends LinkedHashSet<Activity> {
        int calls;Runnable during;RuntimeException failure;
        @Override public boolean contains(Object value){calls++;order.add("contains:"+(value==Activity.CORE?"CORE":value==Activity.IDLE?"IDLE":"unknown"));if(during!=null)during.run();if(failure!=null)throw failure;return super.contains(value);}
    }
    private static final class Priorities extends LinkedHashMap<Integer,Map<Activity,Set<BehaviorControl<?>>>> {
        int valuesCalls;
        @Override public Collection<Map<Activity,Set<BehaviorControl<?>>>> values(){valuesCalls++;order.add("values");return super.values();}
        @Override public Set<Integer> keySet(){throw new AssertionError("PRIORITY_KEY_REPLAY");}
    }
    private static final List<String> order=new ArrayList<>();private static int gameQueries;
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static Object read(Object owner,Class<?> base,String name){try{return KneekuraDebugDecisionSnapshot.read(base,name,owner);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static void field(Object owner,Class<?> base,String name,Object value){try{var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Object call(Method m,Object owner,Object... args){try{return m.invoke(owner,args);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException r)throw r;if(e.getCause() instanceof Error r)throw r;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    public static Map<?,?> priorities(Brain<?> brain){return (Map<?,?>)read(brain,Brain.class,"availableBehaviorsByPriority");}
    public static Set<?> active(Brain<?> brain){return (Set<?>)read(brain,Brain.class,"activeActivities");}
    public static boolean sourceActivity(Set<?> set,Object value,Brain<?> brain,ServerLevel level,LivingEntity owner){try{return (Boolean)call(KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainStartActivity",Brain.class,Set.class,Object.class,ServerLevel.class,LivingEntity.class),null,brain,set,value,level,owner);}catch(NoSuchMethodException absent){return set.contains(value);}}
    public static Behavior.Status sourceStatus(BehaviorControl<?> control,Brain<?> brain,ServerLevel level,LivingEntity owner){try{return (Behavior.Status)call(KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainStartStatus",Brain.class,BehaviorControl.class,ServerLevel.class,LivingEntity.class),null,brain,control,level,owner);}catch(NoSuchMethodException absent){return control.getStatus();}}
    public static boolean sourceStart(BehaviorControl<?> control,ServerLevel level,LivingEntity owner,long game,Brain<?> brain){return KneekuraDebugDecisionHooks.originalBrainTryStart(brain,control,level,owner,game);}
    private static Method fixture,original;
    private static void fixture()throws Exception {
        String brain=Type.getInternalName(Brain.class),test=Type.getInternalName(KneekuraDebugBrainStartLoopSelfTest.class),name=test+"$ActualStartLoopFixture";
        var w=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);w.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);int[] counts=new int[7];
        try(var bytes=Brain.class.getResourceAsStream("Brain.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
            @Override public MethodVisitor visitMethod(int a,String n,String desc,String sig,String[] ex){if(!n.equals("startEachNonRunningBehavior"))return null;require((a&Opcodes.ACC_PRIVATE)!=0,"genuine private method");counts[0]++;
                return new MethodVisitor(Opcodes.ASM9,w.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,"run","(L"+brain+";"+desc.substring(1),null,ex)){
                    @Override public void visitFieldInsn(int op,String owner,String f,String d){if(op==Opcodes.GETFIELD&&owner.equals(brain)){require(f.equals("availableBehaviorsByPriority")||f.equals("activeActivities"),"exact private field test accessor");counts[1]++;super.visitMethodInsn(Opcodes.INVOKESTATIC,test,f.equals("activeActivities")?"active":"priorities","(L"+brain+";)"+d,false);return;}super.visitFieldInsn(op,owner,f,d);}
                    @Override public void visitMethodInsn(int op,String owner,String n,String d,boolean itf){
                        if(owner.equals("java/util/Set")&&n.equals("contains")){counts[2]++;sourceArgs();super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"sourceActivity","(Ljava/util/Set;Ljava/lang/Object;L"+brain+";Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)Z",false);return;}
                        if(owner.equals("net/minecraft/world/entity/ai/behavior/BehaviorControl")&&n.equals("getStatus")){counts[3]++;sourceArgs();super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"sourceStatus","(Lnet/minecraft/world/entity/ai/behavior/BehaviorControl;L"+brain+";Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)Lnet/minecraft/world/entity/ai/behavior/Behavior$Status;",false);return;}
                        if(owner.equals("net/minecraft/world/entity/ai/behavior/BehaviorControl")&&n.equals("tryStart")){counts[4]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"sourceStart","(Lnet/minecraft/world/entity/ai/behavior/BehaviorControl;Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;JL"+brain+";)Z",false);return;}
                        if(n.equals("getGameTime"))counts[5]++;if(owner.equals("java/util/Map")&&n.equals("values"))counts[6]++;super.visitMethodInsn(op,owner,n,d,itf);
                    }
                    private void sourceArgs(){super.visitVarInsn(Opcodes.ALOAD,0);super.visitVarInsn(Opcodes.ALOAD,1);super.visitVarInsn(Opcodes.ALOAD,2);}
                };}
        },ClassReader.SKIP_FRAMES);}
        require(Arrays.equals(counts,new int[]{1,2,1,1,1,1,1}),"only genuine fields/source delegates replaced, original gameTime/values/short circuit retained");w.visitEnd();byte[] bytes=w.toByteArray();class Loader extends ClassLoader{Loader(){super(KneekuraDebugBrainStartLoopSelfTest.class.getClassLoader());}Class<?> define(){return defineClass(name.replace('/','.'),bytes,0,bytes.length);}}fixture=new Loader().define().getMethod("run",Brain.class,ServerLevel.class,LivingEntity.class);original=Brain.class.getDeclaredMethod("startEachNonRunningBehavior",ServerLevel.class,LivingEntity.class);original.setAccessible(true);
    }
    private static void observed(Brain<?> brain,ServerLevel level,LivingEntity owner){Runnable body=()->call(fixture,null,brain,level,owner);try{call(KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainStartLoop",Brain.class,ServerLevel.class,LivingEntity.class,Runnable.class),null,brain,level,owner,body);}catch(NoSuchMethodException absent){body.run();}}
    private static List<JsonObject> loops(List<JsonObject> rows){return rows.stream().filter(x->x.get("kind").getAsString().equals("BRAIN_PATH_START_LOOP_RETURN")).toList();}
    private static KneekuraDebugDecisionHooks.Session install(Subject owner,Set<String> channels,int events,int bytes,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(context.get().selectionRevision());var session=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static int emitted;private static void emit(List<JsonObject> rows){for(var row:loops(rows)){System.out.println("BRAIN_START_LOOP_INTEROP:"+new com.google.gson.Gson().toJson(row));emitted++;}}
    private static void configure(Brain<?> brain,Active active,Priorities priorities){field(brain,Brain.class,"activeActivities",active);field(brain,Brain.class,"availableBehaviorsByPriority",priorities);}
    private static Priorities map(Activity activity,BehaviorControl<?>... controls){var map=new LinkedHashMap<Activity,Set<BehaviorControl<?>>>();map.put(activity,new LinkedHashSet<>(Arrays.asList(controls)));var p=new Priorities();p.put(913,map);return p;}
    private static JsonObject data(List<JsonObject> rows){require(loops(rows).size()==1,"exact one loop receipt");return loops(rows).get(0).getAsJsonObject("data");}
    private static void compiledHandlers()throws Exception {
        String living="(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V",loop="startEachNonRunningBehavior"+living;
        var expected=Map.of("kneekura$originalStartLoop",new String[]{"tick"+living,"Lnet/minecraft/world/entity/ai/Brain;"+loop,"originalBrainStartLoop"},
            "kneekura$originalStartActivity",new String[]{loop,"Ljava/util/Set;contains(Ljava/lang/Object;)Z","originalBrainStartActivity"},
            "kneekura$originalStartStatus",new String[]{loop,"Lnet/minecraft/world/entity/ai/behavior/BehaviorControl;getStatus()Lnet/minecraft/world/entity/ai/behavior/Behavior$Status;","originalBrainStartStatus"});
        var found=new HashSet<String>();int[] invokers={0},delegates={0};
        try(var bytes=KneekuraDebugBrainStartLoopSelfTest.class.getResourceAsStream("decisionmixin/KneekuraDebugBrainDecisionMixin.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
            @Override public MethodVisitor visitMethod(int a,String n,String d,String sig,String[] ex){
                if(n.equals("kneekura$invokeStartEach")){require((a&Opcodes.ACC_ABSTRACT)!=0&&d.equals(living),"exact private access Invoker signature");return new MethodVisitor(Opcodes.ASM9){@Override public AnnotationVisitor visitAnnotation(String desc,boolean visible){if(!desc.equals("Lorg/spongepowered/asm/mixin/gen/Invoker;"))return null;return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object v){if(key.equals("value")){require(v.equals("startEachNonRunningBehavior"),"exact private method Invoker");invokers[0]++;}if(key.equals("remap"))require(v.equals(false),"pinned unmapped Invoker");}};}};}
                if(n.startsWith("lambda$kneekura$originalStartLoop$"))return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String name,String desc,boolean itf){require(op==Opcodes.INVOKEVIRTUAL&&owner.endsWith("/KneekuraDebugBrainDecisionMixin")&&name.equals("kneekura$invokeStartEach")&&desc.equals(living),"one private original loop delegate");delegates[0]++;}};
                var spec=expected.get(n);if(spec==null)return null;found.add(n);int[] counts=new int[4];return new MethodVisitor(Opcodes.ASM9){
                    private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object v){if(key.equals("require")){require(v.equals(1),"mandatory source Redirect");counts[2]++;}if(key.equals("target")){require(v.equals(spec[1]),"exact source target");counts[1]++;}}
                        @Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object v){require(v.equals(spec[0]),"exact source selector");counts[0]++;}};return annotation();}
                        @Override public AnnotationVisitor visitAnnotation(String key,String desc){return annotation();}};}
                    @Override public AnnotationVisitor visitAnnotation(String desc,boolean visible){return desc.equals("Lorg/spongepowered/asm/mixin/injection/Redirect;")?annotation():null;}
                    @Override public void visitMethodInsn(int op,String owner,String name,String desc,boolean itf){require(op==Opcodes.INVOKESTATIC&&owner.endsWith("/KneekuraDebugDecisionHooks")&&name.equals(spec[2]),"single source wrapper delegate");counts[3]++;}
                    @Override public void visitEnd(){require(Arrays.equals(counts,new int[]{1,1,1,1}),"one mandatory source boundary "+n);}
                };}
        },0);}
        require(found.equals(expected.keySet())&&invokers[0]==1&&delegates[0]==1,"three exact source Redirects/one private Invoker/one original loop delegate");
        var calls=new HashMap<String,Integer>();try(var bytes=KneekuraDebugDecisionHooks.class.getResourceAsStream("KneekuraDebugDecisionHooks.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
            @Override public MethodVisitor visitMethod(int a,String n,String d,String sig,String[] ex){if(!Set.of("originalBrainStartActivity","originalBrainStartStatus").contains(n))return null;return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String name,String desc,boolean itf){
                if(owner.equals("java/util/Set")||owner.equals("net/minecraft/world/entity/ai/behavior/BehaviorControl")){require(op==Opcodes.INVOKEINTERFACE&&name.equals(n.equals("originalBrainStartActivity")?"contains":"getStatus"),"only original source virtual delegate");calls.merge(n,1,Integer::sum);}
            }};}
        },0);}require(calls.equals(Map.of("originalBrainStartActivity",2,"originalBrainStartStatus",2)),"OFF and observed paths each execute one original source call");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        var owner=(Subject)unsafe.allocateInstance(Subject.class);var nav=(Navigation)unsafe.allocateInstance(Navigation.class);field(nav,PathNavigation.class,"mob",owner);field(owner,Mob.class,"navigation",nav);var brain=new Brain<LivingEntity>(List.of(),List.of(),ImmutableList.of(),()->null);field(owner,LivingEntity.class,"brain",brain);
        var level=(ServerLevel)unsafe.allocateInstance(ServerLevel.class);field(level,Level.class,"levelData",Proxy.newProxyInstance(WritableLevelData.class.getClassLoader(),new Class<?>[]{WritableLevelData.class},(p,m,v)->{require(m.getName().equals("getGameTime"),"only original game time query");gameQueries++;order.add("gameTime");return 100L;}));fixture();
        var a=new Active();a.add(Activity.CORE);var stopped=new Control("stopped",Behavior.Status.STOPPED,true);var running=new Control("running",Behavior.Status.RUNNING,false);var nullable=new Control("null",null,false);var inactive=new Control("inactive",Behavior.Status.STOPPED,true);var p=map(Activity.CORE,stopped,running,nullable);p.get(913).put(Activity.IDLE,Set.of(inactive));configure(brain,a,p);
        call(original,brain,level,owner);var baseline=List.copyOf(order);require(gameQueries==1&&a.calls==2&&p.valuesCalls==1&&stopped.statuses==1&&stopped.starts==1&&running.statuses==1&&running.starts==0&&nullable.statuses==1&&nullable.starts==0&&inactive.statuses==0,"genuine baseline short circuit and source counts");order.clear();gameQueries=a.calls=p.valuesCalls=stopped.statuses=stopped.starts=running.statuses=nullable.statuses=0;
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);observed(brain,level,owner);
        require(order.equals(baseline)&&gameQueries==1&&a.calls==2&&p.valuesCalls==1,"original exact order/counts unchanged");require(loops(rows).size()==1,"missing actual original start-loop receipt");var d=data(rows);require(d.getAsJsonArray("activities").size()==2&&d.get("gameTimeArgument").getAsString().equals("100")&&d.get("priorityStatus").getAsString().equals("NOT_EXPOSED"),"actual returned Activity/control facts, no numeric priority");require(d.getAsJsonArray("activities").get(0).getAsJsonObject().getAsJsonArray("controls").size()==3,"running and nullable status preserved, no query replay");emit(rows);
        configure(brain,a,map(Activity.IDLE,inactive));rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);observed(brain,level,owner);d=data(rows);require(d.get("sourceGameTimeStatus").getAsString().equals("NOT_CAPTURED")&&!d.has("gameTimeArgument"),"no original tryStart time argument when inactive");emit(rows);
        configure(brain,a,new Priorities());rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);observed(brain,level,owner);require(data(rows).getAsJsonArray("activities").isEmpty(),"empty original loop normal return");emit(rows);
        configure(brain,a,map(Activity.CORE,stopped));stopped.result=false;rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);observed(brain,level,owner);require(!data(rows).getAsJsonArray("activities").get(0).getAsJsonObject().getAsJsonArray("controls").get(0).getAsJsonObject().get("tryStartResult").getAsBoolean(),"actual virtual false, not reinterpreted by unchanged cached status");emit(rows);

        // Each cap bounds retained source returns, never original iteration/call counts.
        p=new Priorities();for(int i=0;i<9;i++){var group=new LinkedHashMap<Activity,Set<BehaviorControl<?>>>();group.put(Activity.CORE,Set.of(stopped));p.put(i,group);}configure(brain,a,p);rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);int starts=stopped.starts;observed(brain,level,owner);d=data(rows);require(stopped.starts==starts+9&&d.getAsJsonArray("activities").size()==8&&d.get("activitiesTruncated").getAsBoolean(),"ninth actual Activity executes, retained prefix eight with explicit tail");emit(rows);
        var many=new BehaviorControl<?>[9];for(int i=0;i<9;i++)many[i]=new Control("many"+i,Behavior.Status.STOPPED,false);configure(brain,a,map(Activity.CORE,many));rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);observed(brain,level,owner);var ac=data(rows).getAsJsonArray("activities").get(0).getAsJsonObject();require(ac.getAsJsonArray("controls").size()==8&&ac.get("controlsTruncated").getAsBoolean()&&Arrays.stream(many).allMatch(c->((Control)c).starts==1&&((Control)c).statuses==1),"ninth control actually called; no attachment to eighth");emit(rows);
        for(Activity requested:Arrays.asList(Activity.HIDE,null)){a.add(requested);configure(brain,a,map(requested,stopped));rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);observed(brain,level,owner);ac=data(rows).getAsJsonArray("activities").get(0).getAsJsonObject();require(ac.get("activityStatus").getAsString().equals("NOT_EXPOSED")&&!ac.has("activity"),"unknown/null original Activity operand, no registry/debug-name replay");emit(rows);}
        configure(brain,a,map(Activity.CORE,stopped));rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);stopped.duringStatus=()->{stopped.duringStatus=null;sourceStatus(running,brain,level,owner);};observed(brain,level,owner);require(data(rows).getAsJsonArray("activities").get(0).getAsJsonObject().getAsJsonArray("controls").size()==1,"arbitrary status callback is not source parent evidence");emit(rows);
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);stopped.duringStart=()->{stopped.duringStart=null;sourceStart(stopped,level,owner,100,brain);};starts=stopped.starts;observed(brain,level,owner);require(stopped.starts==starts+2&&data(rows).getAsJsonArray("activities").get(0).getAsJsonObject().getAsJsonArray("controls").size()==1,"arbitrary start callback executes but does not overwrite direct original return");emit(rows);
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);stopped.duringStatus=()->{stopped.duringStatus=null;observed(brain,level,owner);};observed(brain,level,owner);require(loops(rows).size()==2&&loops(rows).get(0).getAsJsonObject("data").get("loopInvocationId").getAsString().equals("start-loop:7:2")&&loops(rows).get(1).getAsJsonObject("data").get("loopInvocationId").getAsString().equals("start-loop:7:1"),"genuine nested loops have separate IDs and normal completion order");emit(rows);
        // Existing R57 frame allocation is linked only to the exact source control in this loop.
        var sink=new MoveToTargetSink();configure(brain,a,map(Activity.CORE,sink));rows.clear();owner.brains=0;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);observed(brain,level,owner);var c=data(rows).getAsJsonArray("activities").get(0).getAsJsonObject().getAsJsonArray("controls").get(0).getAsJsonObject();require(c.get("capturedTryStartInvocationId").getAsString().equals("try-start:7:1")&&!c.get("tryStartResult").getAsBoolean()&&rows.stream().anyMatch(r->r.get("kind").getAsString().equals("BRAIN_PATH_TRY_START_RETURN")),"actual captured R57 child and normal interface false");require(owner.brains==1,"only actual Behavior requirement getter, observer does not query");emit(rows);
        configure(brain,a,map(Activity.CORE,stopped));
        var sentinel=new IllegalStateException("ORIGINAL_SOURCE_EXCEPTION");for(int mode=0;mode<3;mode++){rows.clear();var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);if(mode==0)a.failure=sentinel;else if(mode==1)stopped.statusFailure=sentinel;else stopped.startFailure=sentinel;try{observed(brain,level,owner);throw new AssertionError("expected original exception");}catch(IllegalStateException actual){require(actual==sentinel,"original exception identity unchanged");}finally{a.failure=stopped.statusFailure=stopped.startFailure=null;}require(loops(rows).isEmpty()&&read(session,KneekuraDebugDecisionHooks.Session.class,"startLoopFrame")==null,"exception has no fabricated normal loop receipt and frame cleans up");}
        // An actual source field replacement during a source callback invalidates the entire receipt.
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);stopped.duringStatus=()->{stopped.duringStatus=null;field(brain,Brain.class,"activeActivities",new Active());};observed(brain,level,owner);require(loops(rows).isEmpty(),"changed cached Set invalidates whole loop, no compressed missing prefix");configure(brain,a,map(Activity.CORE,stopped));
        // Gates preserve original source work and suppress late observations.
        for(int mode=0;mode<8;mode++){
            rows.clear();time.set(100);var old=context.get();var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);int selected=mode;
            stopped.duringStatus=()->{stopped.duringStatus=null;switch(selected){case 0->time.set(201);case 1->context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,old.subjectUuid(),"minecraft:overworld"));case 2->field(owner,LivingEntity.class,"brain",new Brain<LivingEntity>(List.of(),List.of(),ImmutableList.of(),()->null));case 3->field(owner,Mob.class,"navigation",null);case 4->field(nav,PathNavigation.class,"mob",null);case 5->KneekuraDebugDecisionHooks.clear("SOURCE_CLEAR");case 6->{try{install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);}catch(Exception e){throw new AssertionError(e);}}case 7->session.budget().close("SOURCE_CLOSE");}};
            starts=stopped.starts;observed(brain,level,owner);require(stopped.starts==starts+1&&loops(rows).isEmpty(),"gate suppresses receipt without changing source branch mode="+mode);field(owner,LivingEntity.class,"brain",brain);field(owner,Mob.class,"navigation",nav);field(nav,PathNavigation.class,"mob",owner);context.set(old);time.set(100);KneekuraDebugDecisionHooks.clear("DONE");
        }
        rows.clear();KneekuraDebugDecisionHooks.clear("OFF");starts=stopped.starts;observed(brain,level,owner);require(stopped.starts==starts+1&&rows.isEmpty(),"OFF original once");install(owner,Set.of("brain"),256,524288,context,time,rows);observed(brain,level,owner);require(rows.isEmpty(),"other channel remains OFF");
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);starts=stopped.starts;var failure=new AtomicReference<Throwable>();var thread=new Thread(()->{try{observed(brain,level,owner);}catch(Throwable e){failure.set(e);}});thread.start();thread.join();require(failure.get()==null&&stopped.starts==starts+1&&rows.isEmpty(),"wrong thread executes original without observations");
        for(int mode=0;mode<2;mode++){rows.clear();install(owner,Set.of("brain_navigation"),mode==0?1:256,mode==0?524288:1,context,time,rows);observed(brain,level,owner);if(mode==0){require(loops(rows).size()==1,"one event budget first loop");observed(brain,level,owner);require(loops(rows).size()==1,"event cap unchanged");emit(rows);}else require(rows.isEmpty(),"byte cap unchanged");}
        configure(brain,a,new Priorities());rows.clear();var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);field(session,KneekuraDebugDecisionHooks.Session.class,"nextStartLoop",255);observed(brain,level,owner);observed(brain,level,owner);require(data(rows).get("loopInvocationId").getAsString().equals("start-loop:7:256"),"loop ID256 has independent finite cap");emit(rows);
        rows.clear();session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);field(session,KneekuraDebugDecisionHooks.Session.class,"startLoopDepth",8);observed(brain,level,owner);require(rows.isEmpty(),"ninth depth not observed; original private loop still runs");
        configure(brain,a,map(Activity.CORE,stopped));rows.clear();session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var identities=(Map<Object,String>)read(session,KneekuraDebugDecisionHooks.Session.class,"identities");for(int i=0;i<128;i++)identities.put(new Object(),"synthetic:"+i);observed(brain,level,owner);require(data(rows).get("instanceIdentityStatus").getAsString().equals("NOT_EXPOSED"),"component128 cap preserves unknown identity");emit(rows);
        rows.clear();var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(7);session=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->{throw new java.io.IOException("WRITER_FAILURE");});KneekuraDebugDecisionHooks.install(session);observed(brain,level,owner);require(rows.isEmpty()&&read(session,KneekuraDebugDecisionHooks.Session.class,"startLoopFrame")==null,"writer failure closes capture and cleans frame");
        compiledHandlers();KneekuraDebugDecisionHooks.clear("DONE");
        System.out.println("Original Brain start-loop source fixture passed; Gson cases="+emitted);
    }
}
