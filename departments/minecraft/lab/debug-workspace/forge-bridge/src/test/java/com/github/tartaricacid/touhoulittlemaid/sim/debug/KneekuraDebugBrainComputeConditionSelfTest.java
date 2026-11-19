package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.common.collect.ImmutableList;
import com.google.gson.JsonObject;
import net.minecraft.SharedConstants;
import net.minecraft.server.Bootstrap;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.MoveToTargetSink;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.*;
import net.minecraft.world.phys.Vec3;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;
import org.objectweb.asm.*;
import org.objectweb.asm.Type;
import net.minecraft.world.level.PathNavigationRegion;
import net.minecraft.world.entity.ai.behavior.PositionTracker;

/** Original private compute runs on the pinned class. No simulated boolean or canReach result. */
public final class KneekuraDebugBrainComputeConditionSelfTest {
    private static final class Subject extends PathfinderMob {
        int brains,navigations;
        private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){brains++;return (Brain<?>)read(this,LivingEntity.class,"brain");}
        @Override public PathNavigation getNavigation(){navigations++;return (PathNavigation)read(this,Mob.class,"navigation");}
        @Override public String toString(){throw new AssertionError("ENTITY_STRING_REPLAY");}
    }
    private static final class ProbeBrain extends Brain<Mob> {
        int queries,writes,erases;
        ProbeBrain(){super(List.of(MemoryModuleType.PATH,MemoryModuleType.WALK_TARGET,MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE),List.of(),ImmutableList.of(),()->null);}
        @Override public boolean hasMemoryValue(MemoryModuleType<?> type){queries++;return super.hasMemoryValue(type);}
        @Override public <U> void setMemory(MemoryModuleType<U> type,U value){writes++;super.setMemory(type,value);}
        @Override public <U> void eraseMemory(MemoryModuleType<U> type){erases++;super.eraseMemory(type);}
        @Override public String toString(){throw new AssertionError("BRAIN_STRING_REPLAY");}
    }
    private static final class Navigation extends PathNavigation {
        int creates;Path returned;boolean useFinder;RuntimeException failure;
        private Navigation(Mob mob,Level level){super(mob,level);}
        @Override public Path createPath(BlockPos target,int accuracy){creates++;if(failure!=null)throw failure;
            if(useFinder)return KneekuraDebugDecisionHooks.originalBrainFinder(this,(PathFinder)read(this,PathNavigation.class,"pathFinder"),null,(Mob)read(this,PathNavigation.class,"mob"),new PoisonTargets(),32,accuracy,1);
            return returned;
        }
        @Override protected PathFinder createPathFinder(int limit){throw new AssertionError("SEARCH_REPLAY");}
        @Override protected Vec3 getTempMobPos(){throw new AssertionError("POSITION_REPLAY");}
        @Override protected boolean canUpdatePath(){throw new AssertionError("UPDATE_REPLAY");}
        @Override public String toString(){throw new AssertionError("NAVIGATION_STRING_REPLAY");}
    }
    private static void require(boolean value,String reason){if(!value)throw new AssertionError(reason);}
    private static Object read(Object owner,Class<?> base,String name){try{return KneekuraDebugDecisionSnapshot.read(base,name,owner);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static void field(Object owner,Class<?> base,String name,Object value)throws Exception {var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}
    private static boolean original(MoveToTargetSink sink,Mob owner,WalkTarget target,long game){try{var m=MoveToTargetSink.class.getDeclaredMethod("tryComputePath",Mob.class,WalkTarget.class,long.class);m.setAccessible(true);return (Boolean)m.invoke(sink,owner,target,game);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException r)throw r;if(e.getCause() instanceof Error r)throw r;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static boolean observed(MoveToTargetSink sink,Mob owner,WalkTarget target,long game){
        BooleanSupplier once=()->original(sink,owner,target,game);
        try {var m=KneekuraDebugDecisionHooks.class.getDeclaredMethod("originalBrainCompute",MoveToTargetSink.class,Mob.class,WalkTarget.class,long.class,String.class,BooleanSupplier.class);return (Boolean)m.invoke(null,sink,owner,target,game,"CHECK_EXTRA_START",once);}
        catch(NoSuchMethodException e){return once.getAsBoolean();}
        catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException r)throw r;if(e.getCause() instanceof Error r)throw r;throw new AssertionError(e);}
        catch(ReflectiveOperationException e){throw new AssertionError(e);}
    }

    private static Method fixtureCompute,fixtureReachedMethod;
    private static int emitted;
    private static final class CustomSink extends MoveToTargetSink { }
    private static final class PoisonTargets extends HashSet<BlockPos> {
        @Override public Iterator<BlockPos> iterator(){throw new AssertionError("TARGET_SET_QUERY_REPLAY");}
        @Override public int size(){throw new AssertionError("TARGET_SET_SIZE_REPLAY");}
        @Override public String toString(){throw new AssertionError("TARGET_SET_STRING_REPLAY");}
    }
    private static final class Finder extends PathFinder {
        int calls;Path returned;RuntimeException failure;
        private Finder(){super(null,1);}
        @Override public Path findPath(PathNavigationRegion region,Mob owner,Set<BlockPos> targets,float range,int accuracy,float multiplier){
            calls++;if(failure!=null)throw failure;KneekuraDebugDecisionHooks.pathBegin(this,owner);
            KneekuraDebugDecisionHooks.pathResult(this,owner,returned);KneekuraDebugDecisionHooks.pathEnd(this);return returned;
        }
        @Override public String toString(){throw new AssertionError("FINDER_STRING_REPLAY");}
    }
    private static final class ProbePath extends Path {
        int reach;boolean result;RuntimeException failure;ProbePath(){super(new ArrayList<>(List.of(new Node(1,0,0))),new BlockPos(10,0,0),false);}
        @Override public boolean canReach(){reach++;if(failure!=null)throw failure;return result;}
        @Override public String toString(){throw new AssertionError("PATH_STRING_REPLAY");}
    }
    private static final class ProbeTarget extends WalkTarget {
        int trackers,speeds,close,threshold;RuntimeException closeFailure;
        ProbeTarget(){this(new BlockPos(10,0,0),0);}
        ProbeTarget(BlockPos pos,int threshold){super(new net.minecraft.world.entity.ai.behavior.BlockPosTracker(pos),0.5f,0);this.threshold=threshold;}
        @Override public PositionTracker getTarget(){trackers++;return super.getTarget();}
        @Override public float getSpeedModifier(){speeds++;return super.getSpeedModifier();}
        @Override public int getCloseEnoughDist(){close++;if(closeFailure!=null)throw closeFailure;return threshold;}
    }
    public static Path fixturePath(MoveToTargetSink sink){return (Path)read(sink,MoveToTargetSink.class,"path");}
    public static void fixtureSetPath(MoveToTargetSink sink,Path value){try{field(sink,MoveToTargetSink.class,"path",value);}catch(Exception e){throw new AssertionError(e);}}
    public static void fixtureSetSpeed(MoveToTargetSink sink,float value){try{field(sink,MoveToTargetSink.class,"speedModifier",value);}catch(Exception e){throw new AssertionError(e);}}
    private static Object invoke(Method method,Object receiver,Object... args){try{return method.invoke(receiver,args);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException r)throw r;if(e.getCause() instanceof Error r)throw r;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Object optional(String name,Class<?>[] types,Object[] args,java.util.function.Supplier<Object> original){try{return invoke(KneekuraDebugDecisionHooks.class.getDeclaredMethod(name,types),null,args);}catch(NoSuchMethodException e){return original.get();}}
    public static boolean fixtureReached(MoveToTargetSink sink,Mob owner,WalkTarget target){java.util.function.BooleanSupplier once=()->(Boolean)invoke(fixtureReachedMethod,null,sink,owner,target);return (Boolean)optional("originalComputeReached",new Class<?>[]{MoveToTargetSink.class,Mob.class,WalkTarget.class,java.util.function.BooleanSupplier.class},new Object[]{sink,owner,target,once},()->once.getAsBoolean());}
    public static boolean fixtureCanReach(Path path,MoveToTargetSink sink){return (Boolean)optional("originalComputeCanReach",new Class<?>[]{MoveToTargetSink.class,Path.class},new Object[]{sink,path},path::canReach);}
    public static int fixtureDistance(BlockPos target,net.minecraft.core.Vec3i owner,MoveToTargetSink sink){return (Integer)optional("originalComputeDistance",new Class<?>[]{MoveToTargetSink.class,BlockPos.class,net.minecraft.core.Vec3i.class},new Object[]{sink,target,owner},()->target.distManhattan(owner));}
    public static int fixtureClose(WalkTarget target,MoveToTargetSink sink){return (Integer)optional("originalComputeCloseEnough",new Class<?>[]{MoveToTargetSink.class,WalkTarget.class},new Object[]{sink,target},target::getCloseEnoughDist);}

    private static boolean fixture(MoveToTargetSink sink,Mob owner,WalkTarget target,long game){try{return (Boolean)fixtureCompute.invoke(null,sink,owner,target,game);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException r)throw r;if(e.getCause() instanceof Error r)throw r;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    /** Genuine private bytecode and real control flow. Only private access, source delegates and AFTER stores rewritten for this test. */
    private static void prepareFixture()throws Exception {
        String sink=Type.getInternalName(MoveToTargetSink.class),test=Type.getInternalName(KneekuraDebugBrainComputeConditionSelfTest.class),hooks=Type.getInternalName(KneekuraDebugDecisionHooks.class),name=test+"$ActualComputeFixture";
        var w=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);w.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);int[] stores={0},creates={0},methods={0};
        try(var bytes=MoveToTargetSink.class.getResourceAsStream("MoveToTargetSink.class")){require(bytes!=null,"pinned private source required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String method,String descriptor,String signature,String[] exceptions){
            if(!method.equals("tryComputePath"))return null;require(access==Opcodes.ACC_PRIVATE,"genuine method remains private");methods[0]++;
            return new MethodVisitor(Opcodes.ASM9,w.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,"compute","(L"+sink+";"+descriptor.substring(1),null,exceptions)){
                @Override public void visitFieldInsn(int op,String owner,String field,String desc){
                    if(owner.equals(sink)){if(op==Opcodes.GETFIELD&&field.equals("path")){super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"fixturePath","(L"+sink+";)"+desc,false);return;}
                        if(op==Opcodes.PUTFIELD&&field.equals("speedModifier")){super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"fixtureSetSpeed","(L"+sink+";F)V",false);return;}
                        if(op==Opcodes.PUTFIELD&&field.equals("path")){super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"fixtureSetPath","(L"+sink+";"+desc+")V",false);
                            for(int slot:List.of(0,1,2))super.visitVarInsn(Opcodes.ALOAD,slot);super.visitVarInsn(Opcodes.LLOAD,3);super.visitLdcInsn(stores[0]++==0?"INITIAL":"FALLBACK");
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,"brainComputePathWrite","(L"+sink+";Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;JLjava/lang/String;)V",false);return;}
                        throw new AssertionError("unresearched source field:"+field);
                    }super.visitFieldInsn(op,owner,field,desc);
                }
                @Override public void visitMethodInsn(int op,String owner,String method,String desc,boolean itf){
                    if(owner.equals(sink)&&method.equals("reachedTarget")){super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"fixtureReached","(L"+sink+";"+desc.substring(1),false);return;}
                    if(owner.equals("net/minecraft/world/level/pathfinder/Path")&&method.equals("canReach")){super.visitVarInsn(Opcodes.ALOAD,0);super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"fixtureCanReach","(L"+owner+";L"+sink+";)Z",false);return;}
                    if(owner.equals("net/minecraft/world/entity/ai/navigation/PathNavigation")&&method.equals("createPath")){
                        creates[0]++;super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,desc.startsWith("(DDD")?"originalBrainFallbackPath":"originalBrainCreatePath","(L"+owner+";"+desc.substring(1),false);return;
                    }super.visitMethodInsn(op,owner,method,desc,itf);
                }
            };
        }},ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);}
        require(methods[0]==1&&stores[0]==2&&creates[0]==2,"one genuine private body/two original stores/two source creates");w.visitEnd();byte[] code=w.toByteArray();Class<?> c=new ClassLoader(KneekuraDebugBrainComputeConditionSelfTest.class.getClassLoader()){Class<?> load(){return defineClass(name.replace('/','.'),code,0,code.length);}}.load();fixtureCompute=c.getMethod("compute",MoveToTargetSink.class,Mob.class,WalkTarget.class,long.class);
    }
    private static void emit(List<JsonObject> rows){for(var row:rows){System.out.println("BRAIN_COMPUTE_CONDITION_INTEROP:"+new com.google.gson.Gson().toJson(row));emitted++;}}
    private static KneekuraDebugDecisionHooks.Session install(Subject owner,Set<String> channels,int events,int bytes,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(context.get().selectionRevision());var session=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static boolean captured(MoveToTargetSink sink,Subject owner,WalkTarget target){return KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->fixture(sink,owner,target,100));}
    private static void nested(int depth,MoveToTargetSink sink,Subject owner,WalkTarget target){KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"TICK_RECOMPUTE",()->{if(depth>1)nested(depth-1,sink,owner,target);else fixture(sink,owner,target,100);return true;});}

    private static void prepareReached()throws Exception {
        String sink=Type.getInternalName(MoveToTargetSink.class),test=Type.getInternalName(KneekuraDebugBrainComputeConditionSelfTest.class),name=test+"$ActualReachedFixture";
        var w=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);w.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);int[] methods={0},distance={0},close={0};
        try(var bytes=MoveToTargetSink.class.getResourceAsStream("MoveToTargetSink.class")){require(bytes!=null,"genuine reached source required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String method,String desc,String sig,String[] errors){
            if(!method.equals("reachedTarget"))return null;require(access==Opcodes.ACC_PRIVATE,"private original predicate");methods[0]++;
            return new MethodVisitor(Opcodes.ASM9,w.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,"reached","(L"+sink+";"+desc.substring(1),null,errors)){
                @Override public void visitMethodInsn(int op,String owner,String call,String d,boolean itf){
                    if(owner.equals("net/minecraft/core/BlockPos")&&call.equals("distManhattan")){distance[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"fixtureDistance","(L"+owner+";Lnet/minecraft/core/Vec3i;L"+sink+";)I",false);return;}
                    if(owner.equals("net/minecraft/world/entity/ai/memory/WalkTarget")&&call.equals("getCloseEnoughDist")){close[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"fixtureClose","(L"+owner+";L"+sink+";)I",false);return;}
                    super.visitMethodInsn(op,owner,call,d,itf);
                }
            };
        }},ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);}
        require(methods[0]==1&&distance[0]==1&&close[0]==1,"genuine comparator and two original virtual operands");w.visitEnd();byte[] code=w.toByteArray();Class<?> c=new ClassLoader(KneekuraDebugBrainComputeConditionSelfTest.class.getClassLoader()){Class<?> load(){return defineClass(name.replace('/','.'),code,0,code.length);}}.load();fixtureReachedMethod=c.getMethod("reached",MoveToTargetSink.class,Mob.class,WalkTarget.class);
    }

    private static final class ProbePosition extends BlockPos {
        int distance,calls;RuntimeException failure;Runnable beforeReturn;
        ProbePosition(int distance){super(10,0,0);this.distance=distance;}
        @Override public int distManhattan(net.minecraft.core.Vec3i owner){calls++;if(failure!=null)throw failure;if(beforeReturn!=null)beforeReturn.run();return distance;}
        @Override public String toString(){throw new AssertionError("POSITION_STRING_REPLAY");}
    }
    private static List<JsonObject> conditions(List<JsonObject> rows){return rows.stream().filter(r->r.get("kind").getAsString().equals("BRAIN_PATH_COMPUTE_CONDITION_RETURN")).toList();}
    private static void operands(List<JsonObject> rows,int distance,int close){var d=conditions(rows).get(0).getAsJsonObject("data");var o=d.getAsJsonObject("operands");require(o.get("distanceReturn").getAsInt()==distance&&o.get("closeEnoughReturn").getAsInt()==close,"actual original signed int returns retained");require(d.get("result").getAsBoolean()==(distance<=close),"original private comparator, not observer replacement");}
    private static boolean nestedReached(int depth,MoveToTargetSink sink,Subject owner,WalkTarget target){BooleanSupplier original=()->depth>1?nestedReached(depth-1,sink,owner,target):(Boolean)invoke(fixtureReachedMethod,null,sink,owner,target);return (Boolean)optional("originalComputeReached",new Class<?>[]{MoveToTargetSink.class,Mob.class,WalkTarget.class,BooleanSupplier.class},new Object[]{sink,owner,target,original},()->original.getAsBoolean());}
    private static void checks(sun.misc.Unsafe unsafe,Subject owner,Navigation nav,ProbeBrain brain,MoveToTargetSink sink,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        compiledHandlers();nav.returned=new ProbePath();var position=new ProbePosition(5);var target=new ProbeTarget(position,5);
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(!captured(sink,owner,target)&&position.calls==1&&target.close==1&&((ProbePath)nav.returned).reach==0,"custom virtual distance and threshold equality preserve reached short circuit");operands(rows,5,5);emit(conditions(rows));
        rows.clear();position=new ProbePosition(-7);target=new ProbeTarget(position,-8);var current=target;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(captured(sink,owner,target),"signed negative actual operands retained");operands(rows,-7,-8);emit(conditions(rows));
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(!captured(sink,owner,new WalkTarget(new BlockPos(Integer.MIN_VALUE,0,0),0.5f,0)),"actual inherited int subtraction/Math.abs/float-sum result retained");operands(rows,Integer.MIN_VALUE,0);emit(conditions(rows));
        rows.clear();var path=new ProbePath();path.result=true;nav.returned=path;target=new ProbeTarget();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(captured(sink,owner,target)&&path.reach==1,"actual custom canReach true differs from cached base reached=false");require(conditions(rows).size()==2&&conditions(rows).get(1).getAsJsonObject("data").get("result").getAsBoolean(),"actual virtual boolean independent of cached field");emit(conditions(rows));
        path.result=false;
        for(String call:List.of("DISTANCE","CLOSE","PATH")){
            rows.clear();var pos=new ProbePosition(10);var wt=new ProbeTarget(pos,0);var failure=new IllegalArgumentException("ORIGINAL_"+call+"_THROW");if(call.equals("DISTANCE"))pos.failure=failure;if(call.equals("CLOSE"))wt.closeFailure=failure;if(call.equals("PATH"))path.failure=failure;
            var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);try{captured(sink,owner,wt);throw new AssertionError("original failure expected");}catch(IllegalArgumentException e){require(e==failure,"same original exception");}
            require(conditions(rows).size()==(call.equals("PATH")?1:0),"only previously completed predicates survive original throw");require(read(session,KneekuraDebugDecisionHooks.Session.class,"reachedFrame")==null&&read(session,KneekuraDebugDecisionHooks.Session.class,"computeFrame")==null,"throw cleans both frames");if(call.equals("PATH"))emit(conditions(rows));path.failure=null;
        }
        rows.clear();target=new ProbeTarget();current=target;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var selected=target;
        KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->fixtureReached(sink,owner,new ProbeTarget()));require(conditions(rows).isEmpty(),"mismatched exact target executes original without borrowed predicate frame");
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->nestedReached(9,sink,owner,selected));require(conditions(rows).size()==8&&conditions(rows).stream().allMatch(r->r.getAsJsonObject("data").getAsJsonObject("operands").get("distanceStatus").getAsString().equals("NOT_CAPTURED")),"depth9 suppresses inner operands instead of assigning them to outer frames");emit(conditions(rows));
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);int before=target.close;KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->{for(int i=0;i<9;i++)fixtureReached(sink,owner,selected);return false;});require(target.close==before+9&&conditions(rows).size()==8,"bounded8reached IDs do not skip original calls");emit(conditions(rows));
        rows.clear();KneekuraDebugDecisionHooks.clear("OFF");before=path.reach;require(captured(sink,owner,target)&&path.reach==before+1&&conditions(rows).isEmpty(),"OFF original compute and predicates once");
        install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var error=new AtomicReference<Throwable>();Thread worker=new Thread(()->{try{captured(sink,owner,selected);}catch(Throwable e){error.set(e);}});worker.start();worker.join();require(error.get()==null&&conditions(rows).isEmpty(),"wrong thread no predicate capture");
        for(String fence:List.of("EVENT","BYTE","TIME","REVISION","OWNER","NAVIGATION_OWNER")){
            rows.clear();time.set(100);var old=context.get();var session=install(owner,Set.of("brain_navigation"),fence.equals("EVENT")?1:256,fence.equals("BYTE")?1:524288,context,time,rows);
            if(fence.equals("TIME"))time.set(200);if(fence.equals("REVISION"))context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,old.subjectUuid(),"minecraft:overworld"));var other=(Subject)unsafe.allocateInstance(Subject.class);if(fence.equals("NAVIGATION_OWNER"))field(nav,PathNavigation.class,"mob",other);Subject passed=fence.equals("OWNER")?other:owner;
            before=target.close;KneekuraDebugDecisionHooks.originalBrainCompute(sink,passed,target,100,"CHECK_EXTRA_START",()->fixtureReached(sink,owner,selected));require(target.close==before+1&&conditions(rows).size()==(fence.equals("EVENT")?1:0),"original predicate retained under "+fence);require(read(session,KneekuraDebugDecisionHooks.Session.class,"reachedFrame")==null,"fenced reached cleanup");if(fence.equals("EVENT"))emit(conditions(rows));context.set(old);field(nav,PathNavigation.class,"mob",owner);
        }
        rows.clear();time.set(100);position=new ProbePosition(10);target=new ProbeTarget(position,0);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);position.beforeReturn=()->{try{install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);}catch(Exception e){throw new AssertionError(e);}};captured(sink,owner,target);require(conditions(rows).isEmpty(),"rearm inside original getter cannot associate old return to new frame");
        rows.clear();position=new ProbePosition(10);target=new ProbeTarget(position,0);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);position.beforeReturn=()->optional("originalComputeDistance",new Class<?>[]{MoveToTargetSink.class,BlockPos.class,net.minecraft.core.Vec3i.class},new Object[]{sink,new BlockPos(1,0,0),BlockPos.ZERO},()->1);require(captured(sink,owner,target),"ambiguous synthetic distance callbacks original preserved");require(conditions(rows).get(0).getAsJsonObject("data").getAsJsonObject("operands").get("distanceStatus").getAsString().equals("NOT_CAPTURED"),"multiple returned ints never masquerade as exact single source operand");emit(conditions(rows));
        rows.clear();target=new ProbeTarget();var finalTarget=target;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->(Boolean)optional("originalComputeReached",new Class<?>[]{MoveToTargetSink.class,Mob.class,WalkTarget.class,BooleanSupplier.class},new Object[]{sink,owner,finalTarget,(BooleanSupplier)()->true},()->true));require(conditions(rows).size()==1&&conditions(rows).get(0).getAsJsonObject("data").getAsJsonObject("operands").get("distanceStatus").getAsString().equals("NOT_CAPTURED"),"synthetic absent source operand remains unknown");emit(conditions(rows));
        for(String limit:List.of("COMPONENT","PATH")){
            rows.clear();var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
            if(limit.equals("COMPONENT")){var token=KneekuraDebugDecisionHooks.Session.class.getDeclaredMethod("token",Object.class);token.setAccessible(true);for(int i=0;i<128;i++)token.invoke(session,new Object());}
            else {var snapshot=(KneekuraDebugDecisionSnapshot)read(session,KneekuraDebugDecisionHooks.Session.class,"snapshot");for(int i=0;i<256;i++)snapshot.pathReferenceFact(new Path(new ArrayList<>(),BlockPos.ZERO,false));}
            captured(sink,owner,target);require(conditions(rows).size()==2,"predicate raw facts retained under "+limit);if(limit.equals("COMPONENT"))require(conditions(rows).get(0).getAsJsonObject("data").get("instanceIdentityStatus").getAsString().equals("NOT_EXPOSED"),"component cap unknown");else require(conditions(rows).get(1).getAsJsonObject("data").getAsJsonObject("argumentPath").getAsJsonObject("identity").get("status").getAsString().equals("NOT_EXPOSED"),"Path cap unknown not fake token");emit(conditions(rows));
        }
        var copied=conditions(rows).get(0).deepCopy();target.threshold=1234;require(conditions(rows).get(0).equals(copied),"operands detached from original objects");
        rows.clear();target=new ProbeTarget();var snap=new KneekuraDebugDecisionSnapshot();snap.reset(7);var budget=new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288);KneekuraDebugDecisionHooks.install(new KneekuraDebugDecisionHooks.Session(owner,null,null,snap,budget,8,Set.of("brain_navigation"),context::get,time::get,(method,row)->{throw new java.io.IOException("TEST_WRITER");}));var writerTarget=target;KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->fixtureReached(sink,owner,writerTarget));require(budget.reason().equals("WRITER_UNAVAILABLE")&&target.close==1,"writer failure changes no original predicate result or count");
        KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");
    }
    private static void compiledHandlers()throws Exception {
        String root="com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/",name="KneekuraDebugBrainNavigationMixin",compute="tryComputePath(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;J)Z",reached="reachedTarget(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;)Z";
        var specs=Map.of("kneekura$reachedFromCompute",new String[]{compute,"Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;"+reached,"originalComputeReached"},"kneekura$pathCanReach",new String[]{compute,"Lnet/minecraft/world/level/pathfinder/Path;canReach()Z","originalComputeCanReach"},"kneekura$reachedDistance",new String[]{reached,"Lnet/minecraft/core/BlockPos;distManhattan(Lnet/minecraft/core/Vec3i;)I","originalComputeDistance"},"kneekura$reachedClose",new String[]{reached,"Lnet/minecraft/world/entity/ai/memory/WalkTarget;getCloseEnoughDist()I","originalComputeCloseEnough"});
        var found=new HashSet<String>();int[] invokers={0},delegates={0};try(var bytes=KneekuraDebugBrainComputeConditionSelfTest.class.getClassLoader().getResourceAsStream(root+name+".class")){require(bytes!=null,"compiled source predicate mixin");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String method,String desc,String sig,String[] errors){
            if(method.equals("kneekura$invokeReached")){require((access&Opcodes.ACC_ABSTRACT)!=0,"exact private Invoker preserves original");return new MethodVisitor(Opcodes.ASM9){@Override public AnnotationVisitor visitAnnotation(String d,boolean visible){require(d.endsWith("/Invoker;"),"private original invoker");return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object value){if(key.equals("value")){require(value.equals("reachedTarget"),"actual private name");invokers[0]++;}if(key.equals("remap"))require(Boolean.FALSE.equals(value),"pinned namespace");}};}};}
            var spec=specs.get(method);if(spec==null){if(!method.startsWith("lambda$kneekura$reachedFromCompute"))return null;return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String call,String d,boolean itf){require(op==Opcodes.INVOKEVIRTUAL&&owner.equals(root+name)&&call.equals("kneekura$invokeReached"),"single private delegate without getter replay");delegates[0]++;}};}
            found.add(method);var values=new HashMap<String,Object>();int[] calls={0};return new MethodVisitor(Opcodes.ASM9){
                private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object value){values.put(key,value);}@Override public AnnotationVisitor visitAnnotation(String key,String d){return annotation();}@Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String k,Object v){values.put("method",v);}};return annotation();}};}
                @Override public AnnotationVisitor visitAnnotation(String d,boolean visible){require(d.endsWith("/Redirect;"),"exact source-call Redirect");return annotation();}
                @Override public void visitMethodInsn(int op,String owner,String call,String d,boolean itf){require(op==Opcodes.INVOKESTATIC&&owner.endsWith("/KneekuraDebugDecisionHooks")&&call.equals(spec[2]),"single original hook delegate");calls[0]++;}
                @Override public void visitEnd(){require(spec[0].equals(values.get("method"))&&spec[1].equals(values.get("target"))&&"INVOKE".equals(values.get("value"))&&Integer.valueOf(1).equals(values.get("require"))&&calls[0]==1,"required exact source descriptor/target/single delegation");}
            };
        }},ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);}require(found.equals(specs.keySet())&&invokers[0]==1&&delegates[0]==1,"four exact source calls plus one private Invoker/delegate");
    }

    public static void main(String[] args)throws Exception {
        SharedConstants.tryDetectVersion();Bootstrap.bootStrap();var u=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");u.setAccessible(true);var unsafe=(sun.misc.Unsafe)u.get(null);prepareReached();prepareFixture();
        var owner=(Subject)unsafe.allocateInstance(Subject.class);var nav=(Navigation)unsafe.allocateInstance(Navigation.class);var brain=new ProbeBrain();
        field(owner,LivingEntity.class,"brain",brain);field(owner,Mob.class,"navigation",nav);field(nav,PathNavigation.class,"mob",owner);field(owner,net.minecraft.world.entity.Entity.class,"blockPosition",BlockPos.ZERO);
        var path=new ProbePath();nav.returned=path;var target=new ProbeTarget();var sink=new MoveToTargetSink();
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"123e4567-e89b-42d3-a456-426614174000","minecraft:overworld"));var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();
        install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        require(captured(sink,owner,target),"original unreachable nonnull compute true");require(owner.brains==1&&owner.navigations==1&&nav.creates==1&&brain.queries==1&&brain.writes==1&&path.reach==1&&target.trackers==2&&target.speeds==1&&target.close==1,"actual compute/predicate calls occur once without getter replay");
        require(!captured(sink,owner,new WalkTarget(BlockPos.ZERO,0.5f,0))&&path.reach==1,"already reached false compute short circuits canReach");nav.returned=null;require(!captured(sink,owner,new WalkTarget(BlockPos.ZERO,0.5f,0))&&path.reach==1,"null initial path reached false compute skips Path and RNG");
        var conditions=rows.stream().filter(r->r.get("kind").getAsString().equals("BRAIN_PATH_COMPUTE_CONDITION_RETURN")).toList();require(conditions.size()==4,"missing actual reachedTarget/Path.canReach return receipts");
        require(conditions.stream().filter(r->r.getAsJsonObject("data").get("condition").getAsString().equals("PATH_CAN_REACH")).count()==1,"no fake canReach on original short circuits");emit(conditions);KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");checks(unsafe,owner,nav,brain,sink,context,time,rows);System.out.println("BRAIN_COMPUTE_CONDITION_INTEROP_COUNT:"+emitted);System.out.println("Actual private compute predicates preserve original branches, returned operands, scopes and getter counts; full RNG/native/arrival proof separate");
    }
}
