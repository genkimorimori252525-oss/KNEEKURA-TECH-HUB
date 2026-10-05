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
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.phys.Vec3;
import net.minecraft.core.BlockPos;
import org.objectweb.asm.*;
import org.objectweb.asm.Type;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;

/** Genuine requirement-loop bytecode; only private test access and original source delegate replaced. */
public final class KneekuraDebugBrainMemoryCheckSelfTest {
    private static final class Subject extends Mob {
        int brains,foreignAt;Brain<?> foreign;private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){brains++;return brains==foreignAt?foreign:(Brain<?>)read(this,LivingEntity.class,"brain");}
    }
    private static final class ProbeBrain extends Brain<Mob> {
        int calls;RuntimeException failure;Runnable during;Boolean forced;
        ProbeBrain(Collection<MemoryModuleType<?>> modules){super(modules,List.of(),ImmutableList.of(),()->null);}
        @Override public boolean checkMemory(MemoryModuleType<?> module,MemoryStatus status){calls++;if(during!=null)during.run();if(failure!=null)throw failure;return forced!=null?forced:super.checkMemory(module,status);}
    }
    private static final class Navigation extends PathNavigation {
        private Navigation(Mob owner,Level level){super(owner,level);}
        @Override protected PathFinder createPathFinder(int limit){throw new AssertionError("SEARCH_REPLAY");}
        @Override protected Vec3 getTempMobPos(){throw new AssertionError("POSITION_REPLAY");}
        @Override protected boolean canUpdatePath(){throw new AssertionError("UPDATE_REPLAY");}
    }
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static Object read(Object owner,Class<?> base,String name){try{return KneekuraDebugDecisionSnapshot.read(base,name,owner);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static void field(Object owner,Class<?> base,String name,Object value){try{var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Object call(Method m,Object owner,Object... args){try{return m.invoke(owner,args);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException r)throw r;if(e.getCause() instanceof Error r)throw r;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    public static Map<?,?> entries(Behavior<?> behavior){return (Map<?,?>)read(behavior,Behavior.class,"entryCondition");}
    public static boolean sourceCheck(Brain<?> brain,MemoryModuleType<?> module,MemoryStatus status,Behavior<?> behavior,LivingEntity owner){
        try{return (Boolean)call(KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainMemoryCheck",Behavior.class,Brain.class,MemoryModuleType.class,MemoryStatus.class,LivingEntity.class),null,behavior,brain,module,status,owner);}
        catch(NoSuchMethodException absent){return brain.checkMemory(module,status);}
    }
    private static Method fixture;
    private static void fixture()throws Exception {
        String b=Type.getInternalName(Behavior.class),test=Type.getInternalName(KneekuraDebugBrainMemoryCheckSelfTest.class),name=test+"$ActualRequirementFixture";
        var w=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);w.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);int[] members={0},checks={0},getters={0},fields={0};
        try(var bytes=Behavior.class.getResourceAsStream("Behavior.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
            @Override public MethodVisitor visitMethod(int a,String n,String desc,String sig,String[] ex){if(!n.equals("hasRequiredMemories"))return null;require((a&Opcodes.ACC_PROTECTED)!=0,"original protected method");members[0]++;
                return new MethodVisitor(Opcodes.ASM9,w.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,"required","(L"+b+";"+desc.substring(1),null,ex)){
                    @Override public void visitFieldInsn(int op,String owner,String f,String d){require(op==Opcodes.GETFIELD&&owner.equals(b)&&f.equals("entryCondition"),"exact private test accessor");fields[0]++;super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"entries","(L"+b+";)Ljava/util/Map;",false);}
                    @Override public void visitMethodInsn(int op,String owner,String n,String d,boolean itf){if(owner.equals("net/minecraft/world/entity/ai/Brain")&&n.equals("checkMemory")){require(op==Opcodes.INVOKEVIRTUAL,"original virtual check");checks[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitVarInsn(Opcodes.ALOAD,1);super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"sourceCheck","(Lnet/minecraft/world/entity/ai/Brain;Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;L"+b+";Lnet/minecraft/world/entity/LivingEntity;)Z",false);return;}if(owner.equals("net/minecraft/world/entity/LivingEntity")&&n.equals("getBrain"))getters[0]++;super.visitMethodInsn(op,owner,n,d,itf);}
                };}
        },ClassReader.SKIP_FRAMES);}
        require(members[0]==1&&checks[0]==1&&getters[0]==1&&fields[0]==1,"genuine loop, one source check and owner getter retained");w.visitEnd();byte[] bytes=w.toByteArray();class Loader extends ClassLoader{Loader(){super(KneekuraDebugBrainMemoryCheckSelfTest.class.getClassLoader());}Class<?> define(){return defineClass(name.replace('/','.'),bytes,0,bytes.length);}}fixture=new Loader().define().getMethod("required",Behavior.class,LivingEntity.class);
    }
    private static boolean observed(ProbeBrain brain,Behavior<?> behavior,Subject owner,BooleanSupplier body)throws Exception {
        var m=KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainStartCall",Brain.class,BehaviorControl.class,ServerLevel.class,LivingEntity.class,long.class,BooleanSupplier.class);m.setAccessible(true);
        return (Boolean)call(m,null,brain,behavior,null,owner,100L,(BooleanSupplier)()->KneekuraDebugDecisionHooks.originalBrainStartCondition(behavior,"HAS_REQUIRED_MEMORIES",null,owner,body));
    }
    private static List<JsonObject> requirements(List<JsonObject> rows){return rows.stream().filter(x->x.get("kind").getAsString().equals("BRAIN_PATH_MEMORY_REQUIREMENT_RETURN")).toList();}
    private static KneekuraDebugDecisionHooks.Session install(Subject owner,Set<String> channels,int events,int bytes,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(context.get().selectionRevision());var session=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static int emitted;private static void emit(List<JsonObject> rows){for(var row:requirements(rows)){System.out.println("BRAIN_MEMORY_CHECK_INTEROP:"+new com.google.gson.Gson().toJson(row));emitted++;}}
    private static void compiledHandler()throws Exception {
        String source="hasRequiredMemories(Lnet/minecraft/world/entity/LivingEntity;)Z",target="Lnet/minecraft/world/entity/ai/Brain;checkMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;)Z";
        int[] found={0},selectors={0},targets={0},required={0},delegates={0},original={0};
        try(var bytes=KneekuraDebugBrainMemoryCheckSelfTest.class.getResourceAsStream("decisionmixin/KneekuraDebugBehaviorDecisionMixin.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
            @Override public MethodVisitor visitMethod(int a,String n,String d,String sig,String[] ex){if(!n.equals("kneekura$memoryCheck"))return null;found[0]++;
                require(d.equals("(Lnet/minecraft/world/entity/ai/Brain;Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;Lnet/minecraft/world/entity/LivingEntity;)Z"),"exact original argument handler");
                return new MethodVisitor(Opcodes.ASM9){private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){
                    @Override public void visit(String key,Object value){if(key.equals("require"))required[0]=(Integer)value;if(key.equals("target")){require(value.equals(target),"exact original checkMemory target");targets[0]++;}}
                    @Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String ignored,Object value){require(value.equals(source),"exact original requirement source");selectors[0]++;}};return annotation();}
                    @Override public AnnotationVisitor visitAnnotation(String key,String desc){return annotation();}};}
                    @Override public AnnotationVisitor visitAnnotation(String desc,boolean visible){return desc.equals("Lorg/spongepowered/asm/mixin/injection/Redirect;")?annotation():null;}
                    @Override public void visitMethodInsn(int op,String owner,String name,String desc,boolean itf){require(op==Opcodes.INVOKESTATIC&&owner.endsWith("/KneekuraDebugDecisionHooks")&&name.equals("originalBrainMemoryCheck"),"single source production delegate");delegates[0]++;}
                };}
        },0);}
        try(var bytes=KneekuraDebugDecisionHooks.class.getResourceAsStream("KneekuraDebugDecisionHooks.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int a,String n,String d,String sig,String[] ex){if(!n.equals("originalBrainMemoryCheck"))return null;return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String name,String desc,boolean itf){
            if(owner.equals("net/minecraft/world/entity/ai/Brain")){require(op==Opcodes.INVOKEVIRTUAL&&name.equals("checkMemory")&&desc.equals("(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Lnet/minecraft/world/entity/ai/memory/MemoryStatus;)Z"),"only original virtual source check, no memory/getter replay");original[0]++;}
        }};}},0);}
        // OFF and observed branches each contain one delegate; every invocation executes only one branch.
        require(found[0]==1&&selectors[0]==1&&targets[0]==1&&required[0]==1&&delegates[0]==1&&original[0]==2,"mandatory exact source Redirect and one virtual delegate per branch");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        var owner=(Subject)unsafe.allocateInstance(Subject.class);var nav=(Navigation)unsafe.allocateInstance(Navigation.class);field(nav,PathNavigation.class,"mob",owner);field(owner,Mob.class,"navigation",nav);var brain=new ProbeBrain(List.of(MemoryModuleType.PATH,MemoryModuleType.WALK_TARGET,MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE));field(owner,LivingEntity.class,"brain",brain);var behavior=new MoveToTargetSink();fixture();
        var original=Behavior.class.getDeclaredMethod("hasRequiredMemories",LivingEntity.class);original.setAccessible(true);boolean baseline=(Boolean)call(original,behavior,owner);int baselineCalls=brain.calls;require(!baseline&&owner.brains==baselineCalls,"genuine baseline first false");brain.calls=owner.brains=0;
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))==baseline,"original return unchanged");require(brain.calls==baselineCalls&&owner.brains==baselineCalls,"original check and getter counts exactly baseline");
        var received=requirements(rows);require(received.size()==1,"missing actual source memory requirement receipt");var data=received.get(0).getAsJsonObject("data");require(!data.get("result").getAsBoolean()&&!data.get("checksTruncated").getAsBoolean(),"original false and uncapped prefix");require(data.getAsJsonArray("checks").size()==baselineCalls,"actual ordered return count");require(!data.getAsJsonArray("checks").get(baselineCalls-1).getAsJsonObject().get("result").getAsBoolean(),"first actual false short circuit");emit(rows);KneekuraDebugDecisionHooks.clear("DONE");
        var originalEntries=entries(behavior);
        brain.setMemory(MemoryModuleType.WALK_TARGET,new WalkTarget(BlockPos.ZERO,0.5f,1));rows.clear();brain.calls=owner.brains=0;boolean trueBaseline=(Boolean)call(original,behavior,owner);int trueCount=brain.calls;require(trueBaseline&&trueCount==3,"actual Sink three requirements true baseline");brain.calls=owner.brains=0;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&brain.calls==trueCount&&owner.brains==trueCount,"true original loop unchanged");require(requirements(rows).get(0).getAsJsonObject("data").getAsJsonArray("checks").asList().stream().allMatch(x->x.getAsJsonObject().get("result").getAsBoolean()),"three true original booleans");emit(rows);
        for(var status:MemoryStatus.values()){
            field(behavior,Behavior.class,"entryCondition",Map.of(MemoryModuleType.PATH,status));brain.calls=owner.brains=0;boolean expected=(Boolean)call(original,behavior,owner);brain.calls=owner.brains=0;rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
            require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))==expected&&brain.calls==1&&owner.brains==1,"original MemoryStatus virtual result once");var check=requirements(rows).get(0).getAsJsonObject("data").getAsJsonArray("checks").get(0).getAsJsonObject();require(check.get("memoryModule").getAsString().equals("PATH")&&check.get("requestedMemoryStatus").getAsString().equals(status.name())&&check.get("result").getAsBoolean()==expected,"actual requested status and returned boolean");emit(rows);
        }
        var unknown=new MemoryModuleType<Object>(Optional.empty());
        for(int mode=0;mode<3;mode++){
            var map=new LinkedHashMap<MemoryModuleType<?>,MemoryStatus>();map.put(mode==0?unknown:mode==1?null:MemoryModuleType.PATH,mode==2?null:MemoryStatus.REGISTERED);field(behavior,Behavior.class,"entryCondition",map);rows.clear();brain.calls=owner.brains=0;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
            require(!observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&brain.calls==1&&owner.brains==1,"unknown/null original false unchanged");var check=requirements(rows).get(0).getAsJsonObject("data").getAsJsonArray("checks").get(0).getAsJsonObject();require(mode==2?check.get("requestedMemoryStatus").getAsString().equals("NOT_EXPOSED"):!check.has("memoryModule")&&check.get("memoryModuleStatus").getAsString().equals("NOT_EXPOSED"),"unknown operand explicit, no registry query");emit(rows);
        }
        field(behavior,Behavior.class,"entryCondition",Map.of(unknown,MemoryStatus.VALUE_PRESENT));brain.forced=true;rows.clear();brain.calls=owner.brains=0;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&brain.calls==1&&owner.brains==1,"custom virtual true despite unknown absent module");emit(rows);
        var many=new LinkedHashMap<MemoryModuleType<?>,MemoryStatus>();for(int i=0;i<9;i++)many.put(new MemoryModuleType<Object>(Optional.empty()),MemoryStatus.REGISTERED);field(behavior,Behavior.class,"entryCondition",many);rows.clear();brain.calls=owner.brains=0;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&brain.calls==9&&owner.brains==9,"nine actual source checks, no query replay");data=requirements(rows).get(0).getAsJsonObject("data");require(data.getAsJsonArray("checks").size()==8&&data.get("checksTruncated").getAsBoolean(),"eight-prefix and explicit ninth-return tail");emit(rows);
        field(behavior,Behavior.class,"entryCondition",Map.of(MemoryModuleType.PATH,MemoryStatus.REGISTERED));rows.clear();brain.calls=owner.brains=0;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);brain.during=()->{brain.during=null;sourceCheck(brain,MemoryModuleType.WALK_TARGET,MemoryStatus.VALUE_PRESENT,behavior,owner);};
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&brain.calls==2&&owner.brains==1,"nested arbitrary delegate executes once but is not source-loop parent evidence");require(requirements(rows).get(0).getAsJsonObject("data").getAsJsonArray("checks").size()==1,"nested callback suppressed");emit(rows);
        rows.clear();brain.calls=owner.brains=0;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);brain.during=()->{brain.during=null;KneekuraDebugDecisionHooks.originalBrainStartCondition(behavior,"HAS_REQUIRED_MEMORIES",null,owner,()->(Boolean)call(fixture,null,behavior,owner));};
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&brain.calls==2&&owner.brains==2&&requirements(rows).size()==2,"nested original predicate scopes retained separately");
        require(requirements(rows).get(0).getAsJsonObject("data").get("requirementInvocationId").getAsString().equals("memory-requirement:7:2")&&requirements(rows).get(1).getAsJsonObject("data").get("requirementInvocationId").getAsString().equals("memory-requirement:7:1")&&requirements(rows).stream().allMatch(x->x.getAsJsonObject("data").getAsJsonArray("checks").size()==1),"nested child completes before restored parent, independent source prefixes");emit(rows);
        brain.during=null;field(behavior,Behavior.class,"entryCondition",Map.of());rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&requirements(rows).isEmpty(),"empty source loop does not fabricate check receipt");
        field(behavior,Behavior.class,"entryCondition",Map.of(MemoryModuleType.PATH,MemoryStatus.REGISTERED));var foreignBrain=new ProbeBrain(List.of(MemoryModuleType.PATH));var foreignOwner=(Subject)unsafe.allocateInstance(Subject.class);
        field(behavior,Behavior.class,"entryCondition",originalEntries);brain.forced=foreignBrain.forced=true;owner.brains=brain.calls=foreignBrain.calls=0;owner.foreign=foreignBrain;owner.foreignAt=2;rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&owner.brains==3&&brain.calls==2&&foreignBrain.calls==1,"genuine mixed original virtual Brain getters unchanged");require(requirements(rows).isEmpty(),"foreign source inside original loop cannot become a compressed complete prefix");owner.foreignAt=0;owner.foreign=null;foreignBrain.forced=null;
        field(behavior,Behavior.class,"entryCondition",Map.of(MemoryModuleType.PATH,MemoryStatus.REGISTERED));
        for(String mismatch:List.of("BRAIN","OWNER","BEHAVIOR")){
            rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);int before=brain.calls+foreignBrain.calls;
            observed(brain,behavior,owner,()->sourceCheck(mismatch.equals("BRAIN")?foreignBrain:brain,MemoryModuleType.PATH,MemoryStatus.REGISTERED,mismatch.equals("BEHAVIOR")?new MoveToTargetSink():behavior,mismatch.equals("OWNER")?foreignOwner:owner));
            require(brain.calls+foreignBrain.calls==before+1&&requirements(rows).isEmpty(),"unsupported source args delegate once without old parent attribution");
        }
        var failure=new IllegalStateException("ORIGINAL_MEMORY_CHECK_FAILURE");brain.failure=failure;rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        try{observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner));throw new AssertionError("original exception missing");}catch(RuntimeException actual){require(actual==failure,"original exception identity");}require(rows.isEmpty(),"no fabricated normal source/predicate/tryStart receipt on exception");brain.failure=null;
        for(String fence:List.of("OFF","CHANNEL","REVISION","TIME","EVENT","BYTE","CACHED_BRAIN","NAV_OWNER","REARM","THREAD")){
            rows.clear();brain.calls=owner.brains=0;context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));time.set(100);field(owner,LivingEntity.class,"brain",brain);field(nav,PathNavigation.class,"mob",owner);
            install(owner,fence.equals("CHANNEL")?Set.of("brain"):Set.of("brain_navigation"),fence.equals("EVENT")?1:256,fence.equals("BYTE")?1:524288,context,time,rows);if(fence.equals("OFF"))KneekuraDebugDecisionHooks.clear("OFF");if(fence.equals("CACHED_BRAIN"))field(owner,LivingEntity.class,"brain",foreignBrain);if(fence.equals("NAV_OWNER"))field(nav,PathNavigation.class,"mob",foreignOwner);
            if(Set.of("REVISION","TIME","REARM").contains(fence))brain.during=()->{brain.during=null;if(fence.equals("REVISION"))context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));else if(fence.equals("TIME"))time.set(201);else try{install(owner,Set.of("brain_navigation"),256,524288,context,time,new ArrayList<>());}catch(Exception e){throw new AssertionError(e);}};
            if(fence.equals("THREAD")){var caught=new AtomicReference<Throwable>();var thread=new Thread(()->{try{observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner));}catch(Throwable e){caught.set(e);}});thread.start();thread.join();require(caught.get()==null,"foreign-thread original untouched");}else observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner));
            if(fence.equals("EVENT")){require(rows.size()==1&&requirements(rows).size()==1,"one event budget retains memory summary only");emit(rows);}else require(requirements(rows).isEmpty(),"fenced normal return must not attach "+fence);
            brain.during=null;KneekuraDebugDecisionHooks.clear("DONE");
        }
        context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));time.set(100);field(owner,LivingEntity.class,"brain",brain);field(nav,PathNavigation.class,"mob",owner);rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        var start=KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainStartCall",Brain.class,BehaviorControl.class,ServerLevel.class,LivingEntity.class,long.class,BooleanSupplier.class);start.setAccessible(true);brain.calls=owner.brains=0;
        call(start,null,brain,behavior,null,owner,100L,(BooleanSupplier)()->{
            for(int i=0;i<255;i++){brain.failure=failure;try{KneekuraDebugDecisionHooks.originalBrainStartCondition(behavior,"HAS_REQUIRED_MEMORIES",null,owner,()->(Boolean)call(fixture,null,behavior,owner));throw new AssertionError("missing cap setup exception");}catch(RuntimeException e){require(e==failure,"original cap exception");}}
            brain.failure=null;KneekuraDebugDecisionHooks.originalBrainStartCondition(behavior,"HAS_REQUIRED_MEMORIES",null,owner,()->(Boolean)call(fixture,null,behavior,owner));KneekuraDebugDecisionHooks.originalBrainStartCondition(behavior,"HAS_REQUIRED_MEMORIES",null,owner,()->(Boolean)call(fixture,null,behavior,owner));return false;
        });require(brain.calls==257&&owner.brains==257&&requirements(rows).size()==1,"requirement ID256 cap preserves every original source call");require(requirements(rows).get(0).getAsJsonObject("data").get("requirementInvocationId").getAsString().equals("memory-requirement:7:256"),"last available ID exact");emit(rows);
        rows.clear();var capped=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var identities=(Map<Object,String>)read(capped,KneekuraDebugDecisionHooks.Session.class,"identities");for(int i=0;i<128;i++)identities.put(new Object(),"component:7:"+(i+1));
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner)),"identity cap does not change source result");data=requirements(rows).get(0).getAsJsonObject("data");require(data.get("instanceIdentityStatus").getAsString().equals("NOT_EXPOSED")&&data.get("instanceIdentity").isJsonNull(),"component cap leaves explicit unknown, source checks still bounded");emit(rows);
        var broken=new KneekuraDebugDecisionHooks.Session(owner,null,null,new KneekuraDebugDecisionSnapshot(),new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->{throw new java.io.IOException("WRITER_FAILURE");});KneekuraDebugDecisionHooks.install(broken);brain.calls=owner.brains=0;
        require(observed(brain,behavior,owner,()->(Boolean)call(fixture,null,behavior,owner))&&brain.calls==1&&owner.brains==1&&broken.budget().reason().equals("WRITER_UNAVAILABLE")&&read(broken,KneekuraDebugDecisionHooks.Session.class,"startFrame")==null,"writer failure changes capture only, original once and frame released");
        field(behavior,Behavior.class,"entryCondition",originalEntries);brain.forced=null;brain.failure=null;KneekuraDebugDecisionHooks.clear("DONE");compiledHandler();require(emitted==16,"exact actual Gson case count");
        System.out.println("BRAIN_MEMORY_CHECK_INTEROP_COUNT:"+emitted);System.out.println("Sixteen actual Brain memory requirement/Gson cases preserve original checks and bounded prefixes");
    }
}
