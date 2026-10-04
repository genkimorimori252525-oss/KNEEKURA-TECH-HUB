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
public final class KneekuraDebugBrainComputeSelfTest {
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

    private static Method fixtureCompute;
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
        int reach;ProbePath(){super(new ArrayList<>(List.of(new Node(1,0,0))),new BlockPos(10,0,0),false);}
        @Override public boolean canReach(){reach++;return false;}
        @Override public String toString(){throw new AssertionError("PATH_STRING_REPLAY");}
    }
    private static final class ProbeTarget extends WalkTarget {
        int trackers,speeds,close;
        ProbeTarget(){super(new BlockPos(10,0,0),0.5f,0);}
        @Override public PositionTracker getTarget(){trackers++;return super.getTarget();}
        @Override public float getSpeedModifier(){speeds++;return super.getSpeedModifier();}
        @Override public int getCloseEnoughDist(){close++;return super.getCloseEnoughDist();}
    }
    public static Path fixturePath(MoveToTargetSink sink){return (Path)read(sink,MoveToTargetSink.class,"path");}
    public static void fixtureSetPath(MoveToTargetSink sink,Path value){try{field(sink,MoveToTargetSink.class,"path",value);}catch(Exception e){throw new AssertionError(e);}}
    public static void fixtureSetSpeed(MoveToTargetSink sink,float value){try{field(sink,MoveToTargetSink.class,"speedModifier",value);}catch(Exception e){throw new AssertionError(e);}}
    public static boolean fixtureReached(MoveToTargetSink sink,Mob owner,WalkTarget target){try{var m=MoveToTargetSink.class.getDeclaredMethod("reachedTarget",Mob.class,WalkTarget.class);m.setAccessible(true);return (Boolean)m.invoke(sink,owner,target);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static boolean fixture(MoveToTargetSink sink,Mob owner,WalkTarget target,long game){try{return (Boolean)fixtureCompute.invoke(null,sink,owner,target,game);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException r)throw r;if(e.getCause() instanceof Error r)throw r;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    /** Genuine private bytecode and real control flow. Only private access, source delegates and AFTER stores rewritten for this test. */
    private static void prepareFixture()throws Exception {
        String sink=Type.getInternalName(MoveToTargetSink.class),test=Type.getInternalName(KneekuraDebugBrainComputeSelfTest.class),hooks=Type.getInternalName(KneekuraDebugDecisionHooks.class),name=test+"$ActualComputeFixture";
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
                    if(owner.equals("net/minecraft/world/entity/ai/navigation/PathNavigation")&&method.equals("createPath")){
                        creates[0]++;super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,desc.startsWith("(DDD")?"originalBrainFallbackPath":"originalBrainCreatePath","(L"+owner+";"+desc.substring(1),false);return;
                    }super.visitMethodInsn(op,owner,method,desc,itf);
                }
            };
        }},ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);}
        require(methods[0]==1&&stores[0]==2&&creates[0]==2,"one genuine private body/two original stores/two source creates");w.visitEnd();byte[] code=w.toByteArray();Class<?> c=new ClassLoader(KneekuraDebugBrainComputeSelfTest.class.getClassLoader()){Class<?> load(){return defineClass(name.replace('/','.'),code,0,code.length);}}.load();fixtureCompute=c.getMethod("compute",MoveToTargetSink.class,Mob.class,WalkTarget.class,long.class);
    }
    private static void emit(List<JsonObject> rows){for(var row:rows){System.out.println("BRAIN_COMPUTE_INTEROP:"+new com.google.gson.Gson().toJson(row));emitted++;}}
    private static KneekuraDebugDecisionHooks.Session install(Subject owner,Set<String> channels,int events,int bytes,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(context.get().selectionRevision());var session=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static boolean captured(MoveToTargetSink sink,Subject owner,WalkTarget target){return KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->fixture(sink,owner,target,100));}
    private static void nested(int depth,MoveToTargetSink sink,Subject owner,WalkTarget target){KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"TICK_RECOMPUTE",()->{if(depth>1)nested(depth-1,sink,owner,target);else fixture(sink,owner,target,100);return true;});}
    private static void extraChecks(sun.misc.Unsafe unsafe,Subject owner,Navigation nav,ProbeBrain brain,MoveToTargetSink sink,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        prepareFixture();compiledHandlers();var finder=(Finder)unsafe.allocateInstance(Finder.class);field(nav,PathNavigation.class,"pathFinder",finder);finder.returned=nav.returned;nav.useFinder=true;
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);int before=nav.creates,queries=brain.queries;var target=new WalkTarget(new BlockPos(10,0,0),0.5f,0);
        require(captured(sink,owner,target),"genuine nonnull unreachable branch returns true");require(nav.creates==before+1&&finder.calls==1&&brain.queries==queries+1,"each original create/Finder/query once");
        require(rows.size()==4,"direct Finder/create/write/compute");require(rows.stream().map(r->r.get("kind").getAsString()).toList().equals(List.of("BRAIN_PATH_FINDER_RETURN","BRAIN_PATH_CREATE_RETURN","BRAIN_PATH_COMPUTE_PATH_WRITE_CHECKPOINT","BRAIN_PATH_COMPUTE_RETURN")),"source return and original field write order");
        var create=rows.get(1).getAsJsonObject("data");var write=rows.get(2).getAsJsonObject("data");require(create.get("createInvocationId").equals(write.get("lastCreateInvocationId"))&&write.get("createdMatchesSinkPath").getAsBoolean(),"raw returned Path connects actual original write");require(!create.get("returnedMatchesNavigationPath").getAsBoolean(),"return differs from unadopted Navigation cache");require(rows.get(0).getAsJsonObject("data").get("searchIdStatus").getAsString().equals("NOT_CAPTURED"),"brain-only does not invent generic search IDs");emit(rows);
        rows.clear();install(owner,Set.of("brain_navigation","path"),256,524288,context,time,rows);require(captured(sink,owner,target),"path channel original retained");require(rows.size()==5&&rows.get(1).getAsJsonObject("data").get("searchId").getAsString().equals("search:7:1"),"search ID retained inside actual source call before pathEnd");emit(rows);
        rows.clear();nav.useFinder=false;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(!captured(sink,owner,new WalkTarget(BlockPos.ZERO,0.5f,0)),"genuine already reached false");require(rows.size()==3&&rows.get(0).getAsJsonObject("data").getAsJsonArray("capturedFinderInvocationIds").isEmpty(),"empty list is only absent direct capture");emit(rows);
        rows.clear();var customPath=new ProbePath();var customTarget=new ProbeTarget();nav.returned=customPath;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(captured(sink,owner,customTarget),"custom virtual boolean preserved");require(customPath.reach==1&&customTarget.trackers==2&&customTarget.speeds==1&&customTarget.close==1,"observer never replays Path/WalkTarget getters");require(rows.get(0).getAsJsonObject("data").getAsJsonObject("returnedPath").getAsJsonObject("cachedFields").get("status").getAsString().equals("NOT_EXPOSED"),"custom cached Path fields unknown");emit(rows);nav.returned=finder.returned;
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);KneekuraDebugDecisionHooks.originalSinkCall(sink,owner,100,"TICK_FROM_BRIDGE",()->captured(sink,owner,target));require(rows.get(0).getAsJsonObject("data").get("enclosingSinkInvocationId").getAsString().equals("sink:7:1"),"actual enclosing source ID only");emit(rows);
        rows.clear();nav.returned=null;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);require(!captured(sink,owner,new WalkTarget(BlockPos.ZERO,0.5f,0))&&rows.size()==3,"genuine initial null and reached short circuit, no fallback RNG");require(!rows.get(1).getAsJsonObject("data").getAsJsonObject("sinkPath").get("present").getAsBoolean(),"actual null write checkpoint retained");emit(rows);nav.returned=finder.returned;
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);nav.useFinder=true;var finderError=new IllegalStateException("ORIGINAL_FINDER_THROW");finder.failure=finderError;
        try{captured(sink,owner,target);throw new AssertionError("Finder exception expected");}catch(IllegalStateException e){require(e==finderError,"original Finder exception identical");}require(rows.isEmpty(),"no false normal return on Finder throw");finder.failure=null;require(captured(sink,owner,target)&&rows.size()==4,"Finder/source frame restored after throw");emit(rows);nav.useFinder=false;
        rows.clear();var pathCapped=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var snapshot=(KneekuraDebugDecisionSnapshot)read(pathCapped,KneekuraDebugDecisionHooks.Session.class,"snapshot");for(int i=0;i<256;i++)snapshot.pathReferenceFact(new Path(new ArrayList<>(),BlockPos.ZERO,false));captured(sink,owner,target);require(rows.get(0).getAsJsonObject("data").getAsJsonObject("returnedPath").getAsJsonObject("identity").get("status").getAsString().equals("NOT_EXPOSED"),"shared snapshot Path reference cap does not fabricate ID");emit(rows);
        rows.clear();var writerSnapshot=new KneekuraDebugDecisionSnapshot();writerSnapshot.reset(7);var writerBudget=new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288);var writerSession=new KneekuraDebugDecisionHooks.Session(owner,null,null,writerSnapshot,writerBudget,8,Set.of("brain_navigation"),context::get,time::get,(method,row)->{throw new java.io.IOException("TEST_WRITER");});KneekuraDebugDecisionHooks.install(writerSession);before=nav.creates;require(captured(sink,owner,target)&&nav.creates==before+1&&writerBudget.reason().equals("WRITER_UNAVAILABLE"),"writer failure closes observation without changing original boolean");
        rows.clear();KneekuraDebugDecisionHooks.clear("OFF");before=nav.creates;require(captured(sink,owner,target)&&nav.creates==before+1&&rows.isEmpty(),"OFF executes genuine original once");
        install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var failure=new IllegalArgumentException("ORIGINAL_CREATE_THROW");nav.failure=failure;
        try{captured(sink,owner,target);throw new AssertionError("exception expected");}catch(IllegalArgumentException e){require(e==failure,"original create exception unchanged");}nav.failure=null;require(rows.isEmpty(),"no original create/compute receipt on throw");
        require(captured(sink,owner,target)&&rows.size()==3,"after exception fresh scope restored");emit(rows);
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var error=new AtomicReference<Throwable>();Thread worker=new Thread(()->{try{captured(sink,owner,target);}catch(Throwable e){error.set(e);}});worker.start();worker.join();require(rows.isEmpty()&&error.get()==null,"wrong thread runs once without capture");
        for(String fence:List.of("EVENT","BYTE","TIME","REVISION","OWNER","NAVIGATION_OWNER","COMPUTE_ID")){
            rows.clear();time.set(100);var old=context.get();var session=install(owner,Set.of("brain_navigation"),fence.equals("EVENT")?1:256,fence.equals("BYTE")?1:524288,context,time,rows);
            if(fence.equals("TIME"))time.set(200);if(fence.equals("REVISION"))context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,old.subjectUuid(),"minecraft:overworld"));
            var other=(Subject)unsafe.allocateInstance(Subject.class);if(fence.equals("NAVIGATION_OWNER"))field(nav,PathNavigation.class,"mob",other);if(fence.equals("COMPUTE_ID"))field(session,KneekuraDebugDecisionHooks.Session.class,"nextCompute",256);
            before=nav.creates;Subject passed=fence.equals("OWNER")?other:owner;KneekuraDebugDecisionHooks.originalBrainCompute(sink,passed,target,100,"CHECK_EXTRA_START",()->fixture(sink,owner,target,100));
            require(nav.creates==before+1&&rows.size()==(fence.equals("EVENT")?1:0),"original preserved under "+fence);require(read(session,KneekuraDebugDecisionHooks.Session.class,"computeFrame")==null&&read(session,KneekuraDebugDecisionHooks.Session.class,"createFrame")==null&&read(session,KneekuraDebugDecisionHooks.Session.class,"finderFrame")==null,"all source frames released");
            if(fence.equals("EVENT"))emit(rows);context.set(old);field(nav,PathNavigation.class,"mob",owner);
        }
        rows.clear();time.set(100);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);KneekuraDebugDecisionHooks.originalBrainCompute(new CustomSink(),owner,target,100,"CHECK_EXTRA_START",()->fixture(sink,owner,target,100));require(rows.isEmpty(),"unknown Sink suppresses nested original creates");
        install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);nested(9,sink,owner,target);require(rows.size()==8&&rows.stream().allMatch(r->r.get("kind").getAsString().equals("BRAIN_PATH_COMPUTE_RETURN")),"depth-nine suppresses nested call rather than borrowing parent");emit(rows);
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->{try{install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);}catch(Exception e){throw new AssertionError(e);}return fixture(sink,owner,target,100);});require(rows.isEmpty(),"rearm cannot retain stale source frame");
        // Synthetic wrapper bounds/primitive operands only; this does NOT claim full original fallback RNG coverage.
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->{
            var p=KneekuraDebugDecisionHooks.originalBrainFallbackPath(nav,Double.NaN,2,Double.POSITIVE_INFINITY,0);fixtureSetPath(sink,p);KneekuraDebugDecisionHooks.brainComputePathWrite(sink,owner,target,100,"FALLBACK");return p!=null;
        });require(rows.size()==3&&rows.get(0).getAsJsonObject("data").getAsJsonObject("arguments").get("xStatus").getAsString().equals("NOT_EXPOSED"),"nonfinite passed fallback operands unknown; original final delegation retained");emit(rows);
        rows.clear();install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);KneekuraDebugDecisionHooks.originalBrainCompute(sink,owner,target,100,"CHECK_EXTRA_START",()->{
            for(int i=0;i<9;i++)KneekuraDebugDecisionHooks.originalBrainCreatePath(nav,BlockPos.ZERO,0);
            KneekuraDebugDecisionHooks.brainComputePathWrite(sink,owner,target,100,"INITIAL");return true;
        });require(rows.size()==10&&rows.get(8).getAsJsonObject("data").get("createReturnStatus").getAsString().equals("NOT_CAPTURED"),"ninth suppressed create clears prior relation instead of associating stale return");emit(rows);
        rows.clear();var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);for(int i=0;i<128;i++){var token=KneekuraDebugDecisionHooks.Session.class.getDeclaredMethod("token",Object.class);token.setAccessible(true);token.invoke(session,new Object());}captured(sink,owner,target);require(rows.get(0).getAsJsonObject("data").get("instanceIdentityStatus").getAsString().equals("NOT_EXPOSED"),"component cap remains unknown");emit(rows);
        var copied=rows.get(0).deepCopy();nav.returned.advance();require(rows.get(0).equals(copied),"facts detached from mutable original Path");
        KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");System.out.println("Original compute fixtures preserve source calls, field write order, bounded direct scopes and unknown branches; not full fallback RNG or installed native proof");
    }
    private static void compiledHandlers()throws Exception {
        String root="com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/",compute="tryComputePath(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/ai/memory/WalkTarget;J)Z";
        var expected=new LinkedHashMap<String,String[]>();String invoke="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;"+compute;
        expected.put("kneekura$computeFromCheck",new String[]{"Redirect","checkExtraStartConditions(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;)Z","INVOKE",invoke,"originalBrainCompute"});
        expected.put("kneekura$computeFromTick",new String[]{"Redirect","tick(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V","INVOKE",invoke,"originalBrainCompute"});
        expected.put("kneekura$initialCreate",new String[]{"Redirect",compute,"INVOKE","Lnet/minecraft/world/entity/ai/navigation/PathNavigation;createPath(Lnet/minecraft/core/BlockPos;I)Lnet/minecraft/world/level/pathfinder/Path;","originalBrainCreatePath"});
        expected.put("kneekura$fallbackCreate",new String[]{"Redirect",compute,"INVOKE","Lnet/minecraft/world/entity/ai/navigation/PathNavigation;createPath(DDDI)Lnet/minecraft/world/level/pathfinder/Path;","originalBrainFallbackPath"});
        for(String site:List.of("initial","fallback"))expected.put("kneekura$"+site+"Stored",new String[]{"Inject",compute,"FIELD","Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;path:Lnet/minecraft/world/level/pathfinder/Path;","brainComputePathWrite"});
        expected.put("kneekura$finderReturn",new String[]{"Redirect","createPath(Ljava/util/Set;IZIF)Lnet/minecraft/world/level/pathfinder/Path;","INVOKE","Lnet/minecraft/world/level/pathfinder/PathFinder;findPath(Lnet/minecraft/world/level/PathNavigationRegion;Lnet/minecraft/world/entity/Mob;Ljava/util/Set;FIF)Lnet/minecraft/world/level/pathfinder/Path;","originalBrainFinder"});
        var found=new HashSet<String>();int[] invokers={0},delegates={0};
        for(String mixin:List.of("KneekuraDebugBrainNavigationMixin","KneekuraDebugNavigationResultMixin"))try(var bytes=KneekuraDebugBrainComputeSelfTest.class.getClassLoader().getResourceAsStream(root+mixin+".class")){
            require(bytes!=null,"compiled original source mixin required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String name,String desc,String signature,String[] exceptions){
                if(name.equals("kneekura$invokeCompute")){require((access&Opcodes.ACC_ABSTRACT)!=0,"private Invoker must delegate rather than implement predicate");return new MethodVisitor(Opcodes.ASM9){@Override public AnnotationVisitor visitAnnotation(String d,boolean visible){require(d.endsWith("/Invoker;"),"exact private invoker");return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object value){if(key.equals("value")){require(value.equals("tryComputePath"),"private original name");invokers[0]++;}if(key.equals("remap"))require(Boolean.FALSE.equals(value),"pinned namespace");}};}};}
                var spec=expected.get(name);if(spec==null){if(!name.startsWith("lambda$")||!desc.contains("/WalkTarget;"))return null;return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String method,String d,boolean itf){require(op==Opcodes.INVOKEVIRTUAL&&owner.equals(root+mixin)&&method.equals("kneekura$invokeCompute"),"one exact private Invoker delegate");delegates[0]++;}};}
                found.add(name);var values=new HashMap<String,Object>();int[] calls={0};return new MethodVisitor(Opcodes.ASM9){
                    private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object value){values.put(key,value);}@Override public void visitEnum(String key,String d,String value){values.put(key,value);}@Override public AnnotationVisitor visitAnnotation(String key,String d){return annotation();}@Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String ignored,Object value){values.put("method",value);}};return annotation();}};}
                    @Override public AnnotationVisitor visitAnnotation(String d,boolean visible){require(d.endsWith("/"+spec[0]+";"),"required source annotation type");return annotation();}
                    @Override public void visitMethodInsn(int op,String owner,String method,String d,boolean itf){require(op==Opcodes.INVOKESTATIC&&owner.endsWith("/KneekuraDebugDecisionHooks")&&method.equals(spec[4]),"single original/observer delegate without query replay");calls[0]++;}
                    @Override public void visitEnd(){require(spec[1].equals(values.get("method"))&&spec[2].equals(values.get("value"))&&spec[3].equals(values.get("target"))&&Integer.valueOf(1).equals(values.get("require"))&&calls[0]==1,"exact source descriptor/target/require/delegate");if(spec[0].equals("Inject"))require(Integer.valueOf(181).equals(values.get("opcode"))&&Integer.valueOf(name.contains("initial")?0:1).equals(values.get("ordinal"))&&"AFTER".equals(values.get("shift")),"checkpoint after actual original PUTFIELD only");}
                };
            }},ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }
        require(found.equals(expected.keySet())&&invokers[0]==1&&delegates[0]==2,"seven exact boundaries, one private invoker and two single original delegates");
    }

    public static void main(String[] args)throws Exception {
        SharedConstants.tryDetectVersion();Bootstrap.bootStrap();var u=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");u.setAccessible(true);var unsafe=(sun.misc.Unsafe)u.get(null);
        var owner=(Subject)unsafe.allocateInstance(Subject.class);var nav=(Navigation)unsafe.allocateInstance(Navigation.class);var brain=new ProbeBrain();
        field(owner,LivingEntity.class,"brain",brain);field(owner,Mob.class,"navigation",nav);field(nav,PathNavigation.class,"mob",owner);field(owner,net.minecraft.world.entity.Entity.class,"blockPosition",BlockPos.ZERO);
        nav.returned=new Path(new ArrayList<>(List.of(new Node(1,0,0))),new BlockPos(10,0,0),false);
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"123e4567-e89b-42d3-a456-426614174000","minecraft:overworld"));var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();var snap=new KneekuraDebugDecisionSnapshot();snap.reset(7);
        KneekuraDebugDecisionHooks.install(new KneekuraDebugDecisionHooks.Session(owner,null,null,snap,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->rows.add(row)));
        var sink=new MoveToTargetSink();
        require(observed(sink,owner,new WalkTarget(new BlockPos(10,0,0),0.5f,0),100),"nonnull unreachable Path returns true, independently of canReach");
        require(owner.brains==1&&owner.navigations==1&&nav.creates==1&&brain.queries==1&&brain.writes==1&&brain.erases==0,"original private initial branch executes once without getter/query replay");
        require(read(sink,MoveToTargetSink.class,"path")==nav.returned,"original real PUTFIELD retained");
        require(!observed(sink,owner,new WalkTarget(BlockPos.ZERO,0.5f,0),101),"already reached returns false despite nonnull Path");
        require(owner.brains==2&&owner.navigations==2&&nav.creates==2&&brain.queries==1&&brain.writes==1&&brain.erases==1,"original reached branch short circuit preserved");
        require(rows.size()==2&&rows.stream().allMatch(r->r.get("kind").getAsString().equals("BRAIN_PATH_COMPUTE_RETURN")),"missing original compute return receipts");
        emit(rows);KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");
        extraChecks(unsafe,owner,nav,brain,sink,context,time,rows);
        System.out.println("BRAIN_COMPUTE_INTEROP_COUNT:"+emitted);
        System.out.println("Original private compute booleans preserve nonnull-unreachable and reached short circuit");
    }
}
