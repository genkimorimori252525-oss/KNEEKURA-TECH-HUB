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
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.storage.WritableLevelData;
import net.minecraft.util.RandomSource;
import org.objectweb.asm.*;
import org.objectweb.asm.Type;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;

/** Cloned genuine final tryStart body; only private access and original source delegates are replaced. */
public final class KneekuraDebugBrainStartSelfTest {
    private static final class Subject extends Mob {
        int brains,navigations;
        private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){brains++;return (Brain<?>)read(this,LivingEntity.class,"brain");}
        @Override public PathNavigation getNavigation(){navigations++;return (PathNavigation)read(this,Mob.class,"navigation");}
    }
    private static final class ProbeBrain extends Brain<Mob> {
        int checks;RuntimeException failure;Runnable duringCheck;
        ProbeBrain(){super(List.of(MemoryModuleType.PATH,MemoryModuleType.WALK_TARGET,MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE),List.of(),ImmutableList.of(),()->null);}
        @Override public boolean checkMemory(MemoryModuleType<?> type,net.minecraft.world.entity.ai.memory.MemoryStatus status){checks++;if(duringCheck!=null)duringCheck.run();if(failure!=null)throw failure;return super.checkMemory(type,status);}
    }
    private static final class Navigation extends PathNavigation {
        int creates,moves;Path returned;RuntimeException createFailure,moveFailure;
        private Navigation(Mob owner,Level level){super(owner,level);}
        @Override public Path createPath(BlockPos target,int accuracy){creates++;if(createFailure!=null)throw createFailure;return returned;}
        @Override public boolean moveTo(Path path,double speed){moves++;if(moveFailure!=null)throw moveFailure;field(this,PathNavigation.class,"path",path);field(this,PathNavigation.class,"speedModifier",speed);return true;}
        @Override protected PathFinder createPathFinder(int limit){throw new AssertionError("SEARCH_REPLAY");}
        @Override protected Vec3 getTempMobPos(){throw new AssertionError("POSITION_REPLAY");}
        @Override protected boolean canUpdatePath(){throw new AssertionError("UPDATE_REPLAY");}
    }
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static Object read(Object owner,Class<?> base,String name){try{return KneekuraDebugDecisionSnapshot.read(base,name,owner);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static void field(Object owner,Class<?> base,String name,Object value){try{var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Object call(Method method,Object owner,Object... args){try{return method.invoke(owner,args);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException r)throw r;if(e.getCause() instanceof Error r)throw r;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Object protectedCall(Behavior<?> behavior,String name,Class<?>[] types,Object... args){try{var m=Behavior.class.getDeclaredMethod(name,types);m.setAccessible(true);return call(m,behavior,args);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Method startFixture,extraFixture,sinkStartFixture;private static int memoryCalls,extraCalls,startCalls,rngCalls,emitted;private static RuntimeException rngFailure;
    private static boolean condition(Behavior<?> behavior,String kind,ServerLevel level,LivingEntity owner,BooleanSupplier once){
        try{return (Boolean)call(KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainStartCondition",Behavior.class,String.class,ServerLevel.class,LivingEntity.class,BooleanSupplier.class),null,behavior,kind,level,owner,once);}
        catch(NoSuchMethodException absent){return once.getAsBoolean();}
    }
    public static boolean originalMemory(Behavior<?> behavior,LivingEntity owner){return condition(behavior,"HAS_REQUIRED_MEMORIES",null,owner,()->{memoryCalls++;return (Boolean)protectedCall(behavior,"hasRequiredMemories",new Class<?>[]{LivingEntity.class},owner);});}
    public static boolean originalExtra(Behavior<?> behavior,ServerLevel level,LivingEntity owner){return condition(behavior,"CHECK_EXTRA_START",level,owner,()->{extraCalls++;return behavior.getClass()==MoveToTargetSink.class?(Boolean)call(extraFixture,null,behavior,level,(Mob)owner):(Boolean)protectedCall(behavior,"checkExtraStartConditions",new Class<?>[]{ServerLevel.class,LivingEntity.class},level,owner);});}
    public static void originalStart(Behavior<?> behavior,ServerLevel level,LivingEntity owner,long game){
        Runnable once=()->{startCalls++;if(behavior.getClass()==MoveToTargetSink.class)KneekuraDebugDecisionHooks.originalSinkCall((MoveToTargetSink)behavior,(Mob)owner,game,"START_FROM_BRIDGE",()->call(sinkStartFixture,null,behavior,level,(Mob)owner,game));else protectedCall(behavior,"start",new Class<?>[]{ServerLevel.class,LivingEntity.class,long.class},level,owner,game);};
        try{call(KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainStartDispatch",Behavior.class,ServerLevel.class,LivingEntity.class,long.class,Runnable.class),null,behavior,level,owner,game,once);}
        catch(NoSuchMethodException absent){once.run();}
    }
    public static int minDuration(Behavior<?> behavior){return (Integer)read(behavior,Behavior.class,"minDuration");}
    public static int maxDuration(Behavior<?> behavior){return (Integer)read(behavior,Behavior.class,"maxDuration");}
    public static void setStatus(Behavior<?> behavior,Behavior.Status value){field(behavior,Behavior.class,"status",value);}
    public static void setEnd(Behavior<?> behavior,long value){field(behavior,Behavior.class,"endTimestamp",value);}
    public static int cooldown(MoveToTargetSink sink){return (Integer)read(sink,MoveToTargetSink.class,"remainingCooldown");}
    public static void setCooldown(MoveToTargetSink sink,int value){field(sink,MoveToTargetSink.class,"remainingCooldown",value);}
    public static void setTarget(MoveToTargetSink sink,BlockPos value){field(sink,MoveToTargetSink.class,"lastTargetPos",value);}
    public static Path sinkPath(MoveToTargetSink sink){return (Path)read(sink,MoveToTargetSink.class,"path");}
    public static float sinkSpeed(MoveToTargetSink sink){return (Float)read(sink,MoveToTargetSink.class,"speedModifier");}
    public static boolean reached(MoveToTargetSink sink,Mob owner,WalkTarget target){try{var m=MoveToTargetSink.class.getDeclaredMethod("reachedTarget",Mob.class,WalkTarget.class);m.setAccessible(true);return (Boolean)call(m,sink,owner,target);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    public static boolean compute(MoveToTargetSink sink,Mob owner,WalkTarget target,long game){return KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,game,"CHECK_EXTRA_START",()->{try{var m=MoveToTargetSink.class.getDeclaredMethod("tryComputePath",Mob.class,WalkTarget.class,long.class);m.setAccessible(true);return (Boolean)call(m,sink,owner,target,game);}catch(ReflectiveOperationException e){throw new AssertionError(e);}});}
    private static void fixture()throws Exception {
        String behavior=Type.getInternalName(Behavior.class),test=Type.getInternalName(KneekuraDebugBrainStartSelfTest.class),name=test+"$ActualStartFixture";
        var w=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);w.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);var seen=new HashMap<String,Integer>();
        try(var bytes=Behavior.class.getResourceAsStream("Behavior.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
            @Override public MethodVisitor visitMethod(int access,String method,String desc,String sig,String[] ex){if(!method.equals("tryStart"))return null;require((access&Opcodes.ACC_FINAL)!=0,"genuine final method");seen.merge(method,1,Integer::sum);
                return new MethodVisitor(Opcodes.ASM9,w.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,"tryStart","(L"+behavior+";"+desc.substring(1),null,ex)){
                    @Override public void visitFieldInsn(int op,String owner,String field,String d){if(owner.equals(behavior)){String delegate=op==Opcodes.GETFIELD?field:field.equals("status")?"setStatus":"setEnd";require(Set.of("minDuration","maxDuration","status","endTimestamp").contains(field),"exact private field access");seen.merge(field,1,Integer::sum);super.visitMethodInsn(Opcodes.INVOKESTATIC,test,delegate,"(L"+behavior+";"+(op==Opcodes.GETFIELD?")"+d:d+")V"),false);return;}super.visitFieldInsn(op,owner,field,d);}
                    @Override public void visitMethodInsn(int op,String owner,String call,String d,boolean itf){if(owner.equals(behavior)){String delegate=switch(call){case "hasRequiredMemories"->"originalMemory";case "checkExtraStartConditions"->"originalExtra";case "start"->"originalStart";default->throw new AssertionError(call);};seen.merge(call,1,Integer::sum);super.visitMethodInsn(Opcodes.INVOKESTATIC,test,delegate,"(L"+behavior+";"+d.substring(1),false);return;}super.visitMethodInsn(op,owner,call,d,itf);}
                };}
        },ClassReader.SKIP_FRAMES);}
        require(seen.equals(Map.of("tryStart",1,"hasRequiredMemories",1,"checkExtraStartConditions",1,"start",1,"status",1,"endTimestamp",1,"minDuration",2,"maxDuration",1)),"exact original source conditions/private access; RNG bytecode retained");w.visitEnd();byte[] bytes=w.toByteArray();
        class Loader extends ClassLoader{Loader(){super(KneekuraDebugBrainStartSelfTest.class.getClassLoader());}Class<?> define(){return defineClass(name.replace('/','.'),bytes,0,bytes.length);}}
        startFixture=new Loader().define().getMethod("tryStart",Behavior.class,ServerLevel.class,LivingEntity.class,long.class);
        sinkFixture();
    }
    private static void sinkFixture()throws Exception {
        String sink=Type.getInternalName(MoveToTargetSink.class),test=Type.getInternalName(KneekuraDebugBrainStartSelfTest.class),hooks=Type.getInternalName(KneekuraDebugDecisionHooks.class),name=test+"$ActualSinkFixture";
        var w=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);w.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);int[] members={0},writes={0},moves={0},computes={0};
        try(var bytes=MoveToTargetSink.class.getResourceAsStream("MoveToTargetSink.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int a,String method,String desc,String sig,String[] ex){
            if(!(method.equals("checkExtraStartConditions")&&desc.equals("(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;)Z")||method.equals("start")&&desc.equals("(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V")))return null;members[0]++;
            return new MethodVisitor(Opcodes.ASM9,w.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,method,"(L"+sink+";"+desc.substring(1),null,ex)){
                @Override public void visitFieldInsn(int op,String owner,String f,String d){if(owner.equals(sink)){String delegate=op==Opcodes.GETFIELD?switch(f){case "remainingCooldown"->"cooldown";case "path"->"sinkPath";case "speedModifier"->"sinkSpeed";default->throw new AssertionError(f);}:switch(f){case "remainingCooldown"->"setCooldown";case "lastTargetPos"->"setTarget";default->throw new AssertionError(f);};super.visitMethodInsn(Opcodes.INVOKESTATIC,test,delegate,"(L"+sink+";"+(op==Opcodes.GETFIELD?")"+d:d+")V"),false);return;}super.visitFieldInsn(op,owner,f,d);}
                @Override public void visitMethodInsn(int op,String owner,String call,String d,boolean itf){
                    if(owner.equals(sink)){require(Set.of("reachedTarget","tryComputePath").contains(call),"exact private source call");if(call.equals("tryComputePath"))computes[0]++;super.visitMethodInsn(Opcodes.INVOKESTATIC,test,call.equals("reachedTarget")?"reached":"compute","(L"+sink+";"+d.substring(1),false);return;}
                    if(owner.equals("net/minecraft/world/entity/ai/Brain")&&call.equals("setMemory")){writes[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitLdcInsn("START_PATH_WRITE");super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,"originalSinkPathWrite","(L"+owner+";Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Ljava/lang/Object;L"+sink+";Ljava/lang/String;)V",false);return;}
                    if(owner.equals("net/minecraft/world/entity/ai/navigation/PathNavigation")&&call.equals("moveTo")){moves[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,"originalSinkMoveTo","(L"+owner+";Lnet/minecraft/world/level/pathfinder/Path;DL"+sink+";)Z",false);return;}
                    super.visitMethodInsn(op,owner,call,d,itf);
                }
            };}},ClassReader.SKIP_FRAMES);}
        require(members[0]==2&&writes[0]==1&&moves[0]==1&&computes[0]==1,"genuine exact extra/start source boundaries");w.visitEnd();byte[] bytes=w.toByteArray();class Loader extends ClassLoader{Loader(){super(KneekuraDebugBrainStartSelfTest.class.getClassLoader());}Class<?> define(){return defineClass(name.replace('/','.'),bytes,0,bytes.length);}}var cls=new Loader().define();extraFixture=cls.getMethod("checkExtraStartConditions",MoveToTargetSink.class,ServerLevel.class,Mob.class);sinkStartFixture=cls.getMethod("start",MoveToTargetSink.class,ServerLevel.class,Mob.class,long.class);
    }
    private static boolean observed(Brain<?> brain,BehaviorControl<?> behavior,ServerLevel level,LivingEntity owner,long game,BooleanSupplier once){
        try{var m=KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainStartCall",Brain.class,BehaviorControl.class,ServerLevel.class,LivingEntity.class,long.class,BooleanSupplier.class);m.setAccessible(true);return (Boolean)call(m,null,brain,behavior,level,owner,game,once);}
        catch(NoSuchMethodException absent){return once.getAsBoolean();}
    }
    private static List<JsonObject> upstream(List<JsonObject> rows){return rows.stream().filter(x->Set.of("BRAIN_PATH_START_CONDITION_RETURN","BRAIN_PATH_START_DISPATCH_RETURN","BRAIN_PATH_TRY_START_RETURN").contains(x.get("kind").getAsString())).toList();}
    private static KneekuraDebugDecisionHooks.Session install(Subject owner,Set<String> channels,int events,int bytes,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(context.get().selectionRevision());var session=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static void emit(List<JsonObject> rows){for(var row:rows){System.out.println("BRAIN_START_INTEROP:"+new com.google.gson.Gson().toJson(row));emitted++;}}
    private static void seed(Subject owner,Navigation nav,ProbeBrain brain,MoveToTargetSink behavior,boolean target){memoryCalls=extraCalls=startCalls=rngCalls=owner.brains=owner.navigations=nav.creates=nav.moves=brain.checks=0;rngFailure=nav.createFailure=nav.moveFailure=brain.failure=null;brain.duringCheck=null;field(nav,PathNavigation.class,"path",null);field(behavior,MoveToTargetSink.class,"path",null);setCooldown(behavior,0);setStatus(behavior,Behavior.Status.STOPPED);setEnd(behavior,-1);field(owner,net.minecraft.world.entity.Entity.class,"blockPosition",BlockPos.ZERO);nav.returned=new Path(new ArrayList<>(List.of(new Node(0,0,0))),new BlockPos(10,0,0),false);brain.eraseMemory(MemoryModuleType.PATH);brain.eraseMemory(MemoryModuleType.WALK_TARGET);brain.eraseMemory(MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE);if(target)brain.setMemory(MemoryModuleType.WALK_TARGET,new WalkTarget(new BlockPos(10,0,0),0.5f,0));}
    private static boolean run(Brain<?> brain,Behavior<?> behavior,ServerLevel level,LivingEntity owner){return observed(brain,behavior,level,owner,100,()->(Boolean)call(startFixture,null,behavior,level,owner,100L));}
    private static final class CustomSink extends MoveToTargetSink { }
    private static void expect(RuntimeException expected,Runnable action){try{action.run();throw new AssertionError("missing original exception");}catch(RuntimeException actual){require(actual==expected,"original exception identity preserved");}}
    private static boolean nested(int depth,Brain<?> brain,Behavior<?> behavior,Subject owner){return observed(brain,behavior,null,owner,100,()->depth==1?(Boolean)call(startFixture,null,behavior,null,owner,100L):nested(depth-1,brain,behavior,owner));}
    private static void compiledHandlers()throws Exception {
        String living="(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)",behavior="Lnet/minecraft/world/entity/ai/behavior/Behavior;",source="tryStart"+living+"Z";
        var expected=Map.of("kneekura$originalTryStart",new String[]{"startEachNonRunningBehavior(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)V","Lnet/minecraft/world/entity/ai/behavior/BehaviorControl;tryStart"+living+"Z","originalBrainTryStart"},
            "kneekura$startMemory",new String[]{source,behavior+"hasRequiredMemories(Lnet/minecraft/world/entity/LivingEntity;)Z","originalBrainStartCondition"},
            "kneekura$startExtra",new String[]{source,behavior+"checkExtraStartConditions(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;)Z","originalBrainStartCondition"},
            "kneekura$startDispatch",new String[]{source,behavior+"start"+living+"V","originalBrainStartDispatch"});
        var found=new HashSet<String>();int[] delegates={0},shadows={0};
        for(String name:List.of("Brain","Behavior"))try(var bytes=KneekuraDebugBrainStartSelfTest.class.getClassLoader().getResourceAsStream("com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/KneekuraDebug"+name+"DecisionMixin.class")){
            require(bytes!=null,"compiled original source mixin required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String method,String desc,String sig,String[] ex){
                if(Set.of("hasRequiredMemories","checkExtraStartConditions","start").contains(method))return new MethodVisitor(Opcodes.ASM9){@Override public AnnotationVisitor visitAnnotation(String d,boolean visible){if(d.equals("Lorg/spongepowered/asm/mixin/Shadow;"))shadows[0]++;return null;}};
                if(method.startsWith("lambda$kneekura$start"))return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String call,String descriptor,boolean itf){require(op==Opcodes.INVOKEVIRTUAL&&owner.endsWith("/KneekuraDebugBehaviorDecisionMixin")&&Set.of("hasRequiredMemories","checkExtraStartConditions","start").contains(call),"single original protected virtual Shadow delegate");delegates[0]++;}};
                var spec=expected.get(method);if(spec==null)return null;found.add(method);int[] selectors={0},targets={0},required={0},calls={0};return new MethodVisitor(Opcodes.ASM9){
                    private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object value){if(key.equals("require"))required[0]=(Integer)value;if(key.equals("target")){require(value.equals(spec[1]),"exact original start target");targets[0]++;}}
                        @Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String ignored,Object value){require(value.equals(spec[0]),"exact original source descriptor");selectors[0]++;}};return annotation();}
                        @Override public AnnotationVisitor visitAnnotation(String key,String d){return annotation();}};}
                    @Override public AnnotationVisitor visitAnnotation(String d,boolean visible){return d.equals("Lorg/spongepowered/asm/mixin/injection/Redirect;")?annotation():null;}
                    @Override public void visitMethodInsn(int op,String owner,String call,String d,boolean itf){if(owner.endsWith("/KneekuraDebugDecisionHooks")){require(op==Opcodes.INVOKESTATIC&&call.equals(spec[2]),"single production wrapper");calls[0]++;}}
                    @Override public void visitEnd(){require(selectors[0]==1&&targets[0]==1&&required[0]==1&&calls[0]==1,"mandatory exact source Redirect "+method);}
                };}},0);
        }
        require(found.equals(expected.keySet())&&delegates[0]==3&&shadows[0]==3,"four original start Redirects/three virtual Shadow delegates");
        int[] sourceCalls={0};try(var bytes=KneekuraDebugDecisionHooks.class.getResourceAsStream("KneekuraDebugDecisionHooks.class")){new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int a,String n,String d,String sig,String[] ex){if(!n.startsWith("lambda$originalBrainTryStart$"))return null;return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String call,String desc,boolean itf){require(op==Opcodes.INVOKEINTERFACE&&owner.equals("net/minecraft/world/entity/ai/behavior/BehaviorControl")&&call.equals("tryStart")&&desc.equals(living+"Z"),"original source interface call exactly once");sourceCalls[0]++;}};}},0);}require(sourceCalls[0]==1,"single original interface source lambda");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        var owner=(Subject)unsafe.allocateInstance(Subject.class);var nav=(Navigation)unsafe.allocateInstance(Navigation.class);field(nav,PathNavigation.class,"mob",owner);field(owner,Mob.class,"navigation",nav);var brain=new ProbeBrain();field(owner,LivingEntity.class,"brain",brain);var behavior=new MoveToTargetSink();fixture();
        require(!behavior.tryStart(null,owner,100)&&behavior.getStatus()==Behavior.Status.STOPPED,"genuine absent-memory baseline does not access level/RNG/start");owner.brains=brain.checks=0;
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        require(!observed(brain,behavior,null,owner,100,()->(Boolean)call(startFixture,null,behavior,null,owner,100L)),"original false unchanged");
        require(memoryCalls==1&&extraCalls==0&&startCalls==0&&owner.brains==brain.checks&&owner.navigations==0,"original memory checks once; no extra/RNG/start/getter replay");
        var facts=upstream(rows);require(facts.size()==2,"missing original required-memory and tryStart return receipts");require(facts.get(0).getAsJsonObject("data").get("condition").getAsString().equals("HAS_REQUIRED_MEMORIES")&&!facts.get(0).getAsJsonObject("data").get("result").getAsBoolean(),"actual memory predicate false");require(!facts.get(1).getAsJsonObject("data").get("result").getAsBoolean(),"actual interface-call false");require(read(session,KneekuraDebugDecisionHooks.Session.class,"startFrame")==null,"finally releases source frame");emit(facts);
        rows.clear();seed(owner,nav,brain,behavior,true);setCooldown(behavior,1);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(!run(brain,behavior,null,owner)&&cooldown(behavior)==0,"actual cooldown false/decrement preserved");facts=upstream(rows);require(facts.size()==3&&memoryCalls==1&&extraCalls==1&&startCalls==0&&rngCalls==0&&nav.creates==0,"extra false short circuits original RNG/start");emit(facts);
        var level=(ServerLevel)unsafe.allocateInstance(ServerLevel.class);
        field(level,Level.class,"levelData",Proxy.newProxyInstance(WritableLevelData.class.getClassLoader(),new Class<?>[]{WritableLevelData.class},(proxy,method,values)->{if(method.getName().equals("getGameTime"))return 100L;throw new AssertionError("UNEXPECTED_LEVEL_QUERY:"+method.getName());}));
        field(level,Level.class,"random",Proxy.newProxyInstance(RandomSource.class.getClassLoader(),new Class<?>[]{RandomSource.class},(proxy,method,values)->{require(method.getName().equals("nextInt")&&values.length==1&&(Integer)values[0]>5,"only original bounded duration RNG");rngCalls++;if(rngFailure!=null)throw rngFailure;return 5;}));
        seed(owner,nav,brain,behavior,true);require(behavior.tryStart(level,owner,100),"genuine final tryStart true baseline");int baseBrains=owner.brains,baseNav=owner.navigations,baseChecks=brain.checks;require(rngCalls==1&&nav.creates==1&&nav.moves==1,"genuine duration RNG/create/start/Nav once");
        rows.clear();seed(owner,nav,brain,behavior,true);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(run(brain,behavior,level,owner),"actual true return preserved");facts=upstream(rows);require(facts.size()==4&&memoryCalls==1&&extraCalls==1&&startCalls==1&&rngCalls==1&&nav.creates==1&&nav.moves==1&&owner.brains==baseBrains&&owner.navigations==baseNav&&brain.checks==baseChecks,"genuine source once, no memory/Nav/RNG replay");
        require(behavior.getStatus()==Behavior.Status.RUNNING&&(Long)read(behavior,Behavior.class,"endTimestamp")==100L+minDuration(behavior)+5,"original status/endTimestamp writes preserved");
        String parent=facts.get(0).getAsJsonObject("data").get("tryStartInvocationId").getAsString();require(facts.stream().allMatch(x->parent.equals(x.getAsJsonObject("data").get("tryStartInvocationId").getAsString())),"same original start frame");
        String computeId=facts.get(1).getAsJsonObject("data").getAsJsonArray("capturedComputeInvocationIds").get(0).getAsString(),sinkId=facts.get(2).getAsJsonObject("data").getAsJsonArray("capturedSinkInvocationIds").get(0).getAsString();require(rows.stream().anyMatch(x->x.get("kind").getAsString().equals("BRAIN_PATH_COMPUTE_RETURN")&&x.getAsJsonObject("data").get("computeInvocationId").getAsString().equals(computeId)),"compute child from actual source scope");require(rows.stream().anyMatch(x->x.get("kind").getAsString().equals("BRAIN_PATH_SINK_RETURN")&&x.getAsJsonObject("data").get("sinkInvocationId").getAsString().equals(sinkId)),"Sink child from actual start bridge scope");emit(facts);
        var failure=new IllegalStateException("ORIGINAL_FAILURE");
        for(String phase:List.of("MEMORY","EXTRA","RNG","START")){
            rows.clear();seed(owner,nav,brain,behavior,true);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);if(phase.equals("MEMORY"))brain.failure=failure;else if(phase.equals("EXTRA"))nav.createFailure=failure;else if(phase.equals("RNG"))rngFailure=failure;else nav.moveFailure=failure;
            expect(failure,()->run(brain,behavior,level,owner));facts=upstream(rows);require(facts.size()==(phase.equals("MEMORY")?0:phase.equals("EXTRA")?1:2)&&facts.stream().noneMatch(x->x.get("kind").getAsString().equals("BRAIN_PATH_TRY_START_RETURN")||x.get("kind").getAsString().equals("BRAIN_PATH_START_DISPATCH_RETURN")),"no fabricated normal return after original throw "+phase);require(read(session,KneekuraDebugDecisionHooks.Session.class,"startFrame")==null,"throw frame cleanup");emit(facts);
        }
        var originalContext=context.get();
        for(String fence:List.of("OFF","OWNER","BRAIN","NAV_OWNER","REVISION","TIME","EVENT","BYTE","CUSTOM")){
            rows.clear();seed(owner,nav,brain,behavior,false);session=install(owner,fence.equals("OFF")?Set.of("brain"):Set.of("brain_navigation"),fence.equals("EVENT")?1:256,fence.equals("BYTE")?1:524288,context,time,rows);var other=(Subject)unsafe.allocateInstance(Subject.class);field(other,LivingEntity.class,"brain",brain);field(other,Mob.class,"navigation",nav);
            if(fence.equals("NAV_OWNER"))field(nav,PathNavigation.class,"mob",other);if(fence.equals("REVISION"))context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,originalContext.subjectUuid(),"minecraft:overworld"));if(fence.equals("TIME"))time.set(200);
            Behavior<?> actual=fence.equals("CUSTOM")?new CustomSink():behavior;require(!observed(fence.equals("BRAIN")?new ProbeBrain():brain,actual,null,fence.equals("OWNER")?other:owner,100,()->(Boolean)call(startFixture,null,actual,null,owner,100L)),"fenced original still false "+fence);require(upstream(rows).size()==(fence.equals("EVENT")?1:0),"exact start capture fence "+fence);require(read(session,KneekuraDebugDecisionHooks.Session.class,"startFrame")==null,"fenced cleanup");context.set(originalContext);time.set(100);field(nav,PathNavigation.class,"mob",owner);
        }
        rows.clear();seed(owner,nav,brain,behavior,false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var problem=new AtomicReference<Throwable>();var foreign=new Thread(()->{try{require(!run(brain,behavior,null,owner),"foreign original false");}catch(Throwable e){problem.set(e);}});foreign.start();foreign.join();require(problem.get()==null&&upstream(rows).isEmpty()&&memoryCalls==1,"foreign thread original once without capture");
        rows.clear();seed(owner,nav,brain,behavior,false);var old=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);brain.duringCheck=()->{try{install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);}catch(Exception e){throw new AssertionError(e);}};require(!run(brain,behavior,null,owner)&&upstream(rows).isEmpty()&&read(old,KneekuraDebugDecisionHooks.Session.class,"startFrame")==null,"rearm inside original memory query cannot revive old parent");
        rows.clear();seed(owner,nav,brain,behavior,false);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);nested(8,brain,behavior,owner);facts=upstream(rows);require(facts.size()==9&&facts.get(0).getAsJsonObject("data").get("tryStartInvocationId").getAsString().equals("try-start:7:8"),"depth8 actual condition plus source returns");emit(facts);
        rows.clear();seed(owner,nav,brain,behavior,false);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);nested(9,brain,behavior,owner);facts=upstream(rows);require(facts.size()==8&&facts.stream().allMatch(x->x.get("kind").getAsString().equals("BRAIN_PATH_TRY_START_RETURN"))&&memoryCalls==1,"depth9 suppresses inner condition without attributing it to parent");emit(facts);
        rows.clear();seed(owner,nav,brain,behavior,false);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);for(int i=0;i<256;i++)expect(failure,()->observed(brain,behavior,null,owner,100,()->{throw failure;}));require(!run(brain,behavior,null,owner)&&upstream(rows).isEmpty()&&(Integer)read(session,KneekuraDebugDecisionHooks.Session.class,"nextStart")==256&&memoryCalls==1,"256 invocation cap preserves original independently of event budget");
        rows.clear();seed(owner,nav,brain,behavior,false);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var token=KneekuraDebugDecisionHooks.Session.class.getDeclaredMethod("token",Object.class);token.setAccessible(true);for(int i=0;i<128;i++)call(token,session,new Object());run(brain,behavior,null,owner);facts=upstream(rows);require(facts.size()==2&&facts.get(0).getAsJsonObject("data").get("instanceIdentityStatus").getAsString().equals("NOT_EXPOSED"),"component cap unknown preserved");emit(facts);
        rows.clear();seed(owner,nav,brain,behavior,false);var broken=new KneekuraDebugDecisionHooks.Session(owner,null,null,new KneekuraDebugDecisionSnapshot(),new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->{throw new java.io.IOException("WRITER_FAILURE");});KneekuraDebugDecisionHooks.install(broken);require(!run(brain,behavior,null,owner)&&broken.budget().reason().equals("WRITER_UNAVAILABLE")&&memoryCalls==1&&read(broken,KneekuraDebugDecisionHooks.Session.class,"startFrame")==null,"writer failure changes only capture");
        for(String child:List.of("COMPUTE","SINK")){
            rows.clear();seed(owner,nav,brain,behavior,true);session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var wt=brain.getMemory(MemoryModuleType.WALK_TARGET).orElseThrow();
            require(observed(brain,behavior,level,owner,100,()->{if(child.equals("COMPUTE"))return KneekuraDebugDecisionHooks.originalBrainStartCondition(behavior,"CHECK_EXTRA_START",level,owner,()->{for(int i=0;i<9;i++)compute(behavior,owner,wt,100);return true;});KneekuraDebugDecisionHooks.originalBrainStartDispatch(behavior,level,owner,100,()->{for(int i=0;i<9;i++)KneekuraDebugDecisionHooks.originalSinkCall(behavior,owner,100,"START_FROM_BRIDGE",()->call(sinkStartFixture,null,behavior,level,owner,100L));});return true;}),"synthetic repeated source delegates preserve normal return");
            facts=upstream(rows);var d=facts.get(0).getAsJsonObject("data");String prefix=child.equals("COMPUTE")?"capturedComputeInvocation":"capturedSinkInvocation";require(d.getAsJsonArray(prefix+"Ids").size()==8&&d.get(prefix+"sTruncated").getAsBoolean(),"eight child IDs plus explicit tail "+child);emit(facts);
        }
        for(String mismatch:List.of("OWNER","LEVEL","KIND","DISPATCH_TIME")){
            rows.clear();seed(owner,nav,brain,behavior,true);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var wt=brain.getMemory(MemoryModuleType.WALK_TARGET).orElseThrow();var other=(Subject)unsafe.allocateInstance(Subject.class);var otherLevel=(ServerLevel)unsafe.allocateInstance(ServerLevel.class);int[] once={0};
            observed(brain,behavior,level,owner,100,()->{if(mismatch.equals("DISPATCH_TIME")){KneekuraDebugDecisionHooks.originalBrainStartDispatch(behavior,level,owner,101,()->{once[0]++;KneekuraDebugDecisionHooks.originalSinkCall(behavior,owner,100,"START_FROM_BRIDGE",()->call(sinkStartFixture,null,behavior,level,owner,100L));});return false;}return KneekuraDebugDecisionHooks.originalBrainStartCondition(behavior,mismatch.equals("KIND")?"TIMED_OUT":"CHECK_EXTRA_START",mismatch.equals("LEVEL")?otherLevel:level,mismatch.equals("OWNER")?other:owner,()->{once[0]++;compute(behavior,owner,wt,100);return false;});});
            facts=upstream(rows);require(once[0]==1&&facts.size()==1&&facts.get(0).get("kind").getAsString().equals("BRAIN_PATH_TRY_START_RETURN"),"unsupported original callback cannot attribute children to enclosing parent "+mismatch);emit(facts);
        }
        rows.clear();seed(owner,nav,brain,behavior,false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(!KneekuraDebugDecisionHooks.originalBrainTryStart(brain,behavior,null,owner,100)&&upstream(rows).size()==1,"actual public interface wrapper preserves source boolean once; fixtures without installed Mixins have no invented internal receipts");emit(upstream(rows));
        compiledHandlers();
        System.out.println("BRAIN_START_INTEROP_COUNT:"+emitted);
        KneekuraDebugDecisionHooks.clear("DONE");System.out.println("Original Brain tryStart: genuine memory short circuit and source receipts; not full reasons/native adoption/arrival proof");
    }
}
