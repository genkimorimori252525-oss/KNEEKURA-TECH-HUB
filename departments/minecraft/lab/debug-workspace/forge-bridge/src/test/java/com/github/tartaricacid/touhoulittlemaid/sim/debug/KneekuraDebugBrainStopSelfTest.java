package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.common.collect.ImmutableList;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.MoveToTargetSink;
import net.minecraft.world.entity.ai.memory.*;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.*;
import net.minecraft.world.phys.Vec3;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import org.objectweb.asm.*;
import org.objectweb.asm.Type;

/** Genuine stop bytecode fixture. Private members and observed calls are explicitly rewritten for tests.
 * The exercised absent-WALK_TARGET/custom-query branches do not prove target/RNG branches or installed Mixins. */
public final class KneekuraDebugBrainStopSelfTest {
    private static final class Subject extends Mob {
        int brains,navigations;boolean forbid;
        private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){if(forbid)throw new AssertionError("BRAIN_GETTER_REPLAY");brains++;return (Brain<?>)read(this,LivingEntity.class,"brain");}
        @Override public PathNavigation getNavigation(){if(forbid)throw new AssertionError("NAVIGATION_GETTER_REPLAY");navigations++;return (PathNavigation)read(this,Mob.class,"navigation");}
        @Override public String toString(){throw new AssertionError("ENTITY_STRING_REPLAY");}
    }
    private static final class ProbeBrain extends Brain<Mob> {
        int erases,queries,optionalWrites;boolean keep,customFalse;MemoryModuleType<?> failureModule;RuntimeException failure;
        ProbeBrain(){super(List.of(MemoryModuleType.PATH,MemoryModuleType.WALK_TARGET),List.of(),ImmutableList.of(),()->null);}
        @Override public boolean hasMemoryValue(MemoryModuleType<?> type){queries++;return customFalse?false:super.hasMemoryValue(type);}
        @Override public <U> Optional<U> getMemory(MemoryModuleType<U> type){throw new AssertionError("TARGET_VALUE_QUERY_NOT_EXERCISED");}
        @Override public <U> void eraseMemory(MemoryModuleType<U> type){erases++;if(type==failureModule)throw failure;if(!keep)super.eraseMemory(type);}
        @Override public <U> void setMemory(MemoryModuleType<U> type,Optional<? extends U> value){optionalWrites++;super.setMemory(type,value);}
        @Override public String toString(){throw new AssertionError("BRAIN_STRING_REPLAY");}
    }
    private static final class Navigation extends PathNavigation {
        int stops;boolean keep;RuntimeException failure;Runnable duringStop;
        Navigation(Mob mob,Level level){super(mob,level);}
        @Override public void stop(){stops++;if(failure!=null)throw failure;if(!keep)super.stop();if(duringStop!=null)duringStop.run();}
        @Override public Path getPath(){throw new AssertionError("PATH_QUERY_REPLAY");}
        @Override public boolean isStuck(){throw new AssertionError("STUCK_QUERY_NOT_EXERCISED");}
        @Override protected PathFinder createPathFinder(int limit){throw new AssertionError("SEARCH_REPLAY");}
        @Override protected Vec3 getTempMobPos(){throw new AssertionError("POSITION_QUERY_REPLAY");}
        @Override protected boolean canUpdatePath(){throw new AssertionError("UPDATE_QUERY_REPLAY");}
        @Override public String toString(){throw new AssertionError("NAVIGATION_STRING_REPLAY");}
    }
    private static final class CustomSink extends MoveToTargetSink { }
    private static final class CustomMap extends HashMap<Object,Object> {
        boolean forbid;
        @Override public Object get(Object key){if(forbid)throw new AssertionError("CUSTOM_MAP_GET_REPLAY");return super.get(key);}
        @Override public boolean containsKey(Object key){if(forbid)throw new AssertionError("CUSTOM_MAP_CONTAINS_REPLAY");return super.containsKey(key);}
        @Override public Set<Map.Entry<Object,Object>> entrySet(){if(forbid)throw new AssertionError("CUSTOM_MAP_ITERATOR_REPLAY");return super.entrySet();}
    }
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static Object read(Object owner,Class<?> base,String name){try{return KneekuraDebugDecisionSnapshot.read(base,name,owner);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static void field(Object owner,Class<?> base,String name,Object value){try{var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    public static void setSinkPath(MoveToTargetSink sink,Path path){field(sink,MoveToTargetSink.class,"path",path);}
    public static void setSinkCooldown(MoveToTargetSink sink,int value){field(sink,MoveToTargetSink.class,"remainingCooldown",value);}
    private static Object call(Method m,Object receiver,Object... args){try{return m.invoke(receiver,args);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException error)throw error;if(e.getCause() instanceof Error error)throw error;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    public static boolean reachedTarget(MoveToTargetSink sink,Mob owner,WalkTarget target){try{var m=MoveToTargetSink.class.getDeclaredMethod("reachedTarget",Mob.class,WalkTarget.class);m.setAccessible(true);return (Boolean)call(m,sink,owner,target);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Path path(int x){var nodes=new ArrayList<Node>();nodes.add(new Node(x,0,0));return new Path(nodes,new BlockPos(x+1,0,0),false);}
    private static void seed(Subject owner,Navigation nav,ProbeBrain brain,MoveToTargetSink sink,Path path,boolean walk){
        owner.forbid=false;owner.brains=owner.navigations=0;nav.stops=brain.erases=brain.queries=brain.optionalWrites=0;
        field(nav,PathNavigation.class,"path",path);field(nav,PathNavigation.class,"speedModifier",0.5);setSinkPath(sink,path);
        field(brain,Brain.class,"memories",new HashMap<>(Map.of(MemoryModuleType.PATH,Optional.of(ExpirableValue.of(path)),
            MemoryModuleType.WALK_TARGET,walk?Optional.of(ExpirableValue.of(new WalkTarget(new BlockPos(1,0,0),1,0))):Optional.empty())));
    }
    private static KneekuraDebugDecisionHooks.Session install(Subject owner,Set<String> channels,int events,int bytes,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(context.get().selectionRevision());
        var s=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(s);return s;
    }
    private static void invoke(MoveToTargetSink sink,Subject owner,Runnable body){KneekuraDebugDecisionHooks.originalSinkCall(sink,owner,100,"STOP_FROM_BRIDGE",body);}
    private static void emit(List<JsonObject> rows){for(var row:rows)System.out.println("BRAIN_STOP_INTEROP:"+new com.google.gson.Gson().toJson(row));}
    private static Method fixture()throws Exception {
        String sink=Type.getInternalName(MoveToTargetSink.class),hooks=Type.getInternalName(KneekuraDebugDecisionHooks.class),test=Type.getInternalName(KneekuraDebugBrainStopSelfTest.class),name=test+"$ActualStopFixture";
        var writer=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);writer.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);int[] members={0},stops={0},erases={0};
        try(var bytes=MoveToTargetSink.class.getResourceAsStream("MoveToTargetSink.class")){require(bytes!=null,"genuine Sink required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
            @Override public MethodVisitor visitMethod(int access,String method,String desc,String signature,String[] exceptions){if(!method.equals("stop")||!desc.equals("(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V"))return null;members[0]++;
                var original=writer.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,"stop","(L"+sink+";"+desc.substring(1),null,exceptions);return new MethodVisitor(Opcodes.ASM9,original){
                    @Override public void visitFieldInsn(int op,String owner,String field,String descriptor){if(owner.equals(sink)&&op==Opcodes.PUTFIELD){require(Set.of("path","remainingCooldown").contains(field),"known original private write");super.visitMethodInsn(Opcodes.INVOKESTATIC,test,field.equals("path")?"setSinkPath":"setSinkCooldown","(L"+sink+";"+descriptor+")V",false);return;}super.visitFieldInsn(op,owner,field,descriptor);}
                    @Override public void visitMethodInsn(int op,String owner,String call,String descriptor,boolean itf){
                        if(owner.equals("net/minecraft/world/entity/ai/navigation/PathNavigation")&&call.equals("stop")){stops[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,"originalSinkNavigationStop","(L"+owner+";L"+sink+";)V",false);return;}
                        if(owner.equals("net/minecraft/world/entity/ai/Brain")&&call.equals("eraseMemory")){erases[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,"originalSinkMemoryErase","(L"+owner+";Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;L"+sink+";)V",false);return;}
                        if(owner.equals(sink)&&call.equals("reachedTarget")){super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"reachedTarget","(L"+sink+";"+descriptor.substring(1),false);return;}super.visitMethodInsn(op,owner,call,descriptor,itf);
                    }
                };
            }
        },ClassReader.SKIP_FRAMES);}require(members[0]==1&&stops[0]==1&&erases[0]==2,"genuine stop has one Nav stop and two exact erases");writer.visitEnd();byte[] bytes=writer.toByteArray();
        class Loader extends ClassLoader{Loader(){super(KneekuraDebugBrainStopSelfTest.class.getClassLoader());}Class<?> define(){return defineClass(name.replace('/','.'),bytes,0,bytes.length);}}
        return new Loader().define().getMethod("stop",MoveToTargetSink.class,ServerLevel.class,Mob.class,long.class);
    }
    private static void counts(Subject owner,Navigation nav,ProbeBrain brain){require(owner.brains==3&&owner.navigations==1&&nav.stops==1&&brain.erases==2&&brain.queries==1,"original getters/query/stop/erases once without observer replay");}
    private static void sameScope(List<JsonObject> rows){String id=rows.get(0).getAsJsonObject("data").get("sinkInvocationId").getAsString();for(var row:rows)require(id.equals(row.getAsJsonObject("data").get("sinkInvocationId").getAsString()),"same original stop invocation");}
    private static void compiledHandlers()throws Exception {
        String mob="(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",living=mob.replace("/Mob;","/LivingEntity;");
        var expected=Map.of("kneekura$stopFromBridge",new String[]{"stop"+living,"Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;stop"+mob,"originalSinkCall","1"},
            "kneekura$navigationStop",new String[]{"stop"+mob,"Lnet/minecraft/world/entity/ai/navigation/PathNavigation;stop()V","originalSinkNavigationStop","1"},
            "kneekura$memoryErase",new String[]{"stop"+mob,"Lnet/minecraft/world/entity/ai/Brain;eraseMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;)V","originalSinkMemoryErase","2"});
        var found=new HashSet<String>();int[] delegates={0};try(var bytes=KneekuraDebugBrainStopSelfTest.class.getClassLoader().getResourceAsStream("com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/KneekuraDebugBrainNavigationMixin.class")){
            require(bytes!=null,"compiled stop mixin required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
                if(name.startsWith("lambda$kneekura$stopFromBridge$"))return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String call,String desc,boolean itf){require(op==Opcodes.INVOKEVIRTUAL&&owner.endsWith("/KneekuraDebugBrainNavigationMixin")&&call.equals("stop")&&desc.equals(mob),"single original protected stop Shadow");delegates[0]++;}};
                var spec=expected.get(name);if(spec==null)return null;found.add(name);int[] methods={0},target={0},at={0},required={0},calls={0};return new MethodVisitor(Opcodes.ASM9){
                    private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object value){if(key.equals("require"))required[0]=(Integer)value;if(key.equals("target")){require(value.equals(spec[1]),"exact stop source target");target[0]++;}if(key.equals("value")&&value.equals("INVOKE"))at[0]++;}
                        @Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String ignored,Object value){require(value.equals(spec[0]),"exact stop source descriptor");methods[0]++;}};return annotation();}
                        @Override public AnnotationVisitor visitAnnotation(String key,String desc){return annotation();}};}
                    @Override public AnnotationVisitor visitAnnotation(String desc,boolean visible){require(desc.endsWith("/Redirect;"),"source-specific original stop redirect");return annotation();}
                    @Override public void visitMethodInsn(int op,String owner,String call,String desc,boolean itf){require(op==Opcodes.INVOKESTATIC&&owner.endsWith("/KneekuraDebugDecisionHooks")&&call.equals(spec[2]),"single original stop observer/delegate without queries");calls[0]++;}
                    @Override public void visitEnd(){require(methods[0]==1&&target[0]==1&&at[0]==1&&required[0]==Integer.parseInt(spec[3])&&calls[0]==1,"required exact stop boundary/call count");}
                };
            }},ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }require(found.equals(expected.keySet())&&delegates[0]==1,"three new source-specific redirects and single stop Shadow");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        var owner=(Subject)unsafe.allocateInstance(Subject.class);var nav=(Navigation)unsafe.allocateInstance(Navigation.class);field(nav,PathNavigation.class,"mob",owner);field(owner,Mob.class,"navigation",nav);var brain=new ProbeBrain();field(owner,LivingEntity.class,"brain",brain);var sink=new MoveToTargetSink();
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();
        var actual=MoveToTargetSink.class.getDeclaredMethod("stop",ServerLevel.class,Mob.class,long.class);actual.setAccessible(true);seed(owner,nav,brain,sink,path(1),false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        invoke(sink,owner,()->{call(actual,sink,null,owner,100L);owner.forbid=true;});counts(owner,nav,brain);require(brain.optionalWrites==2&&read(nav,PathNavigation.class,"path")==null&&read(sink,MoveToTargetSink.class,"path")==null,"genuine original clears Path and delegates Optional writes");
        require(rows.size()==1,"original stop scope observation missing");emit(rows);
        Method stop=fixture();rows.clear();seed(owner,nav,brain,sink,path(10),false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,()->{call(stop,null,sink,null,owner,100L);owner.forbid=true;});counts(owner,nav,brain);require(rows.size()==4,"normal Nav stop/two erases/void return");sameScope(rows);
        require(rows.get(0).get("kind").getAsString().equals("BRAIN_PATH_NAVIGATION_STOP_RETURN")&&rows.get(1).getAsJsonObject("data").get("memoryModule").getAsString().equals("WALK_TARGET")&&rows.get(2).getAsJsonObject("data").get("memoryModule").getAsString().equals("PATH"),"original stop call-site order");
        var detached=rows.get(3).deepCopy();setSinkPath(sink,path(99));require(rows.get(3).equals(detached),"detached stop state");emit(rows);
        rows.clear();brain.keep=brain.customFalse=nav.keep=true;seed(owner,nav,brain,sink,path(20),true);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));counts(owner,nav,brain);require(rows.size()==4&&rows.get(0).getAsJsonObject("data").getAsJsonObject("cachedPath").get("present").getAsBoolean(),"normal custom stop can keep cached Path");
        require(rows.get(1).getAsJsonObject("data").getAsJsonObject("slotAtReturn").get("present").getAsBoolean()&&rows.get(2).getAsJsonObject("data").getAsJsonObject("slotAtReturn").get("present").getAsBoolean(),"normal custom erases can retain both slots");emit(rows);brain.keep=brain.customFalse=nav.keep=false;
        var failure=new IllegalStateException("ORIGINAL_STOP_FAILURE");rows.clear();seed(owner,nav,brain,sink,path(30),false);nav.failure=failure;var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);try{invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));throw new AssertionError("original must throw");}catch(IllegalStateException e){require(e==failure,"same virtual stop exception");}require(rows.isEmpty()&&read(session,KneekuraDebugDecisionHooks.Session.class,"sinkFrame")==null,"no normal return or frame leak on Nav throw");nav.failure=null;
        rows.clear();seed(owner,nav,brain,sink,path(40),false);brain.failure=failure;brain.failureModule=MemoryModuleType.PATH;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);try{invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));throw new AssertionError("erase must throw");}catch(IllegalStateException e){require(e==failure,"same virtual erase exception");}require(rows.size()==2&&read(sink,MoveToTargetSink.class,"path")!=null,"prior completed returns retained, no failed erase or Sink return");emit(rows);brain.failureModule=null;
        rows.clear();seed(owner,nav,brain,sink,path(50),false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));require(rows.size()==4,"next stop after exception works");emit(rows);
        for(Set<String> channels:List.of(Set.of("control"),Set.of("navigation_result"))){rows.clear();seed(owner,nav,brain,sink,path(60),false);install(owner,channels,256,524288,context,time,rows);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));counts(owner,nav,brain);require(rows.isEmpty(),"stop channel opt-in");}
        rows.clear();seed(owner,nav,brain,sink,path(70),false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var workerError=new AtomicReference<Throwable>();var worker=new Thread(()->{try{invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));}catch(Throwable e){workerError.set(e);}});worker.start();worker.join();counts(owner,nav,brain);require(workerError.get()==null&&rows.isEmpty(),"wrong thread originals only");
        rows.clear();seed(owner,nav,brain,sink,path(80),false);invoke(new CustomSink(),owner,()->call(stop,null,sink,null,owner,100L));require(rows.isEmpty(),"unknown Sink frame suppressed");
        rows.clear();seed(owner,nav,brain,sink,path(90),false);var map=new CustomMap();field(brain,Brain.class,"memories",map);brain.customFalse=true;brain.keep=true;map.forbid=true;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));require(rows.size()==4&&rows.get(1).getAsJsonObject("data").getAsJsonObject("slotAtReturn").get("detail").getAsString().equals("CUSTOM_MEMORY_MAP"),"observer never dispatches custom map");emit(rows);brain.customFalse=brain.keep=false;
        rows.clear();seed(owner,nav,brain,sink,path(95),false);field(brain,Brain.class,"memories",new HashMap<>(Map.of(MemoryModuleType.PATH,Optional.of(ExpirableValue.of(path(95))))));install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));counts(owner,nav,brain);require(rows.size()==4&&!rows.get(1).getAsJsonObject("data").getAsJsonObject("slotAtReturn").get("registered").getAsBoolean(),"original erase does not register absent memory slot");emit(rows);
        rows.clear();seed(owner,nav,brain,sink,path(96),false);var invalid=new HashMap<Object,Object>();invalid.put(MemoryModuleType.PATH,Optional.of(ExpirableValue.of(path(96))));invalid.put(MemoryModuleType.WALK_TARGET,new Object());field(brain,Brain.class,"memories",invalid);brain.customFalse=brain.keep=true;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));require(rows.size()==4&&rows.get(1).getAsJsonObject("data").getAsJsonObject("slotAtReturn").get("detail").getAsString().equals("UNEXPECTED_MEMORY_ENTRY"),"malformed Optional slot is unknown without value/query replay");emit(rows);brain.customFalse=brain.keep=false;
        rows.clear();seed(owner,nav,brain,sink,path(97),false);var oldSession=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);nav.duringStop=()->{try{install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);}catch(Exception e){throw new AssertionError(e);}};invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));counts(owner,nav,brain);require(rows.isEmpty()&&read(oldSession,KneekuraDebugDecisionHooks.Session.class,"sinkFrame")==null,"rearm during original virtual stop cannot revive old frame");nav.duringStop=null;
        for(String fence:List.of("EVENT","BYTE","TIME","REVISION","OWNER","NAVIGATION_OWNER")){
            rows.clear();seed(owner,nav,brain,sink,path(100),false);time.set(100);var previous=context.get();session=install(owner,Set.of("brain_navigation"),fence.equals("EVENT")?1:256,fence.equals("BYTE")?1:524288,context,time,rows);
            if(fence.equals("TIME"))time.set(200);if(fence.equals("REVISION"))context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,previous.subjectUuid(),previous.dimension()));var other=(Subject)unsafe.allocateInstance(Subject.class);if(fence.equals("NAVIGATION_OWNER"))field(nav,PathNavigation.class,"mob",other);
            invoke(sink,fence.equals("OWNER")?other:owner,()->call(stop,null,sink,null,owner,100L));counts(owner,nav,brain);require(rows.size()==(fence.equals("EVENT")?1:0)&&read(session,KneekuraDebugDecisionHooks.Session.class,"sinkFrame")==null,"stop capture fence "+fence);context.set(previous);field(nav,PathNavigation.class,"mob",owner);
        }
        rows.clear();time.set(100);seed(owner,nav,brain,sink,path(110),false);var failed=new KneekuraDebugDecisionHooks.Session(owner,null,null,new KneekuraDebugDecisionSnapshot(),new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->{throw new java.io.IOException("WRITER_FAILURE");});KneekuraDebugDecisionHooks.install(failed);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));counts(owner,nav,brain);require(failed.budget().reason().equals("WRITER_UNAVAILABLE"),"writer failure closes capture, originals preserved");
        rows.clear();seed(owner,nav,brain,sink,path(120),false);var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(7);for(int i=0;i<256;i++)snapshot.memoryValue(path(1000+i));brain.keep=brain.customFalse=nav.keep=true;
        var capped=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(capped);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));require(rows.size()==4&&rows.get(0).getAsJsonObject("data").getAsJsonObject("cachedPath").getAsJsonObject("identity").get("status").getAsString().equals("NOT_EXPOSED"),"stop shared reference cap is explicit unknown");emit(rows);brain.keep=brain.customFalse=nav.keep=false;
        rows.clear();seed(owner,nav,brain,sink,path(130),false);var components=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var token=KneekuraDebugDecisionHooks.Session.class.getDeclaredMethod("token",Object.class);token.setAccessible(true);for(int i=0;i<128;i++)call(token,components,new Object());invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));require(rows.size()==4&&rows.get(0).getAsJsonObject("data").get("navigationIdentityStatus").getAsString().equals("NOT_EXPOSED"),"stop component cap independent of Path allocator");emit(rows);
        rows.clear();seed(owner,nav,brain,sink,path(140),false);field(nav,PathNavigation.class,"speedModifier",Double.NaN);field(sink,MoveToTargetSink.class,"speedModifier",Float.NaN);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,()->call(stop,null,sink,null,owner,100L));require(rows.size()==4&&!rows.get(0).getAsJsonObject("data").has("cachedSpeed"),"original stop retains nonfinite speed but observation omits it");emit(rows);
        rows.clear();seed(owner,nav,brain,sink,path(150),false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);KneekuraDebugDecisionHooks.originalSinkCall(sink,owner,100,"START_FROM_BRIDGE",()->call(stop,null,sink,null,owner,100L));counts(owner,nav,brain);require(rows.size()==1&&rows.get(0).get("kind").getAsString().equals("BRAIN_PATH_SINK_RETURN"),"stop returns are never assigned a start frame");
        rows.clear();seed(owner,nav,brain,sink,path(151),false);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,()->{KneekuraDebugDecisionHooks.originalSinkPathWrite(brain,MemoryModuleType.PATH,null,sink,"START_PATH_WRITE");require(!KneekuraDebugDecisionHooks.originalSinkMoveTo(nav,null,0.5,sink),"original null move result");});require(rows.size()==1&&brain.optionalWrites==1,"start-only write/move receipts cannot acquire a stop frame");
        compiledHandlers();
        KneekuraDebugDecisionHooks.clear("DONE");System.out.println("Original Brain stop fixture: genuine stop, virtual Nav stop and two erases once/void/exception/custom retained state/copy/OFF/thread/owner/budget/writer; not target/RNG/native or arrival proof");
    }
}
