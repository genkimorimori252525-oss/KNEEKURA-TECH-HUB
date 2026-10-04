package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.common.collect.ImmutableList;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.MoveToTargetSink;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
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

/** Genuine start/early-tick bytecode fixture; private field access and observed calls are rewritten explicitly.
 * This fixture is not installed-Mixin/native proof and does not exercise the later path-computation branches. */
public final class KneekuraDebugBrainNavigationSelfTest {
    private static Method scope,start,tick;
    private static final class Subject extends Mob {
        int brains,navigations;boolean forbid;
        private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){if(forbid)throw new AssertionError("BRAIN_GETTER_REPLAY");brains++;return (Brain<?>)read(this,LivingEntity.class,"brain");}
        @Override public PathNavigation getNavigation(){if(forbid)throw new AssertionError("NAVIGATION_GETTER_REPLAY");navigations++;return (PathNavigation)read(this,Mob.class,"navigation");}
        @Override public String toString(){throw new AssertionError("ENTITY_STRING_REPLAY");}
    }
    private static final class ProbeBrain extends Brain<Mob> {
        int writes;RuntimeException failure;
        ProbeBrain(){super(List.of(MemoryModuleType.PATH),List.of(),ImmutableList.of(),()->null);}
        @Override public <U> void setMemory(MemoryModuleType<U> type,U value){writes++;if(failure!=null)throw failure;super.setMemory(type,value);}
        @Override public <U> Optional<U> getMemory(MemoryModuleType<U> type){throw new AssertionError("MEMORY_QUERY_REPLAY");}
        @Override public String toString(){throw new AssertionError("BRAIN_STRING_REPLAY");}
    }
    private static final class Navigation extends PathNavigation {
        int moves,paths;boolean invert,forbid;RuntimeException failure;
        Navigation(Mob mob,Level level){super(mob,level);}
        private void allowed(){if(forbid)throw new AssertionError("NAVIGATION_QUERY_REPLAY");}
        @Override public boolean moveTo(Path path,double speed){allowed();moves++;if(failure!=null)throw failure;boolean result=super.moveTo(path,speed);forbid=true;return invert?!result:result;}
        @Override public Path getPath(){allowed();paths++;return super.getPath();}
        @Override protected PathFinder createPathFinder(int limit){throw new AssertionError("SEARCH_REPLAY");}
        @Override protected Vec3 getTempMobPos(){allowed();return Vec3.ZERO;}
        @Override protected boolean canUpdatePath(){throw new AssertionError("UPDATE_QUERY_REPLAY");}
        @Override protected void trimPath(){allowed();}
        @Override public String toString(){throw new AssertionError("NAVIGATION_STRING_REPLAY");}
    }
    private static final class CustomSink extends MoveToTargetSink { }
    private static final class CustomMap extends HashMap<Object,Object> {
        boolean forbid;
        private void allowed(){if(forbid)throw new AssertionError("CUSTOM_MEMORY_MAP_REPLAY");}
        @Override public Object get(Object key){allowed();return super.get(key);}
        @Override public boolean containsKey(Object key){allowed();return super.containsKey(key);}
        @Override public Set<Map.Entry<Object,Object>> entrySet(){allowed();return super.entrySet();}
    }
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static Object read(Object owner,Class<?> base,String name){try{return KneekuraDebugDecisionSnapshot.read(base,name,owner);}catch(ReflectiveOperationException error){throw new AssertionError(error);}}
    private static void field(Object owner,Class<?> base,String name,Object value){try{var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}catch(ReflectiveOperationException error){throw new AssertionError(error);}}
    public static Path sinkPath(MoveToTargetSink sink){return (Path)read(sink,MoveToTargetSink.class,"path");}
    public static float sinkSpeed(MoveToTargetSink sink){return (Float)read(sink,MoveToTargetSink.class,"speedModifier");}
    public static BlockPos sinkTarget(MoveToTargetSink sink){return (BlockPos)read(sink,MoveToTargetSink.class,"lastTargetPos");}
    public static void setSinkPath(MoveToTargetSink sink,Path value){field(sink,MoveToTargetSink.class,"path",value);}
    private static Object call(Method method,Object receiver,Object... args){
        try{return method.invoke(receiver,args);}catch(InvocationTargetException e){if(e.getCause() instanceof RuntimeException error)throw error;if(e.getCause() instanceof Error error)throw error;throw new AssertionError(e);}catch(ReflectiveOperationException e){throw new AssertionError(e);}
    }
    private static void invoke(MoveToTargetSink sink,Subject owner,String site,Runnable body){call(scope,null,sink,owner,100L,site,body);}
    public static void restart(MoveToTargetSink sink,ServerLevel level,Mob owner,long game){call(scope,null,sink,owner,game,"START_FROM_TICK",(Runnable)()->call(start,null,sink,level,owner,game));}
    public static boolean compute(MoveToTargetSink sink,Mob owner,net.minecraft.world.entity.ai.memory.WalkTarget target,long game){try{var m=MoveToTargetSink.class.getDeclaredMethod("tryComputePath",Mob.class,net.minecraft.world.entity.ai.memory.WalkTarget.class,long.class);m.setAccessible(true);return (Boolean)call(m,sink,owner,target,game);}catch(ReflectiveOperationException e){throw new AssertionError(e);}}
    private static Path path(int x){var nodes=new ArrayList<Node>();nodes.add(new Node(x,0,0));nodes.add(new Node(x+1,0,0));for(var node:nodes)node.type=BlockPathTypes.WALKABLE;return new Path(nodes,new BlockPos(x+2,0,0),false);}
    private static void reset(Subject owner,Navigation nav){owner.forbid=false;nav.forbid=false;}
    private static Class<?> fixture()throws Exception {
        String sink=Type.getInternalName(MoveToTargetSink.class),hooks=Type.getInternalName(KneekuraDebugDecisionHooks.class),test=Type.getInternalName(KneekuraDebugBrainNavigationSelfTest.class),name=test+"$ActualSinkFixture";
        var writer=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);writer.visit(Opcodes.V17,Opcodes.ACC_PUBLIC,name,null,"java/lang/Object",null);
        int[] writes={0},moves={0},members={0};
        try(var bytes=MoveToTargetSink.class.getResourceAsStream("MoveToTargetSink.class")){require(bytes!=null,"genuine sink class required");
            new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String method,String descriptor,String signature,String[] exceptions){
                if(!Set.of("start","tick").contains(method)||!descriptor.equals("(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V"))return null;
                members[0]++;var delegate=writer.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC,method,"(L"+sink+";"+descriptor.substring(1),null,exceptions);
                return new MethodVisitor(Opcodes.ASM9,delegate){
                    @Override public void visitFieldInsn(int opcode,String owner,String field,String desc){
                        if(owner.equals(sink)&&opcode==Opcodes.GETFIELD&&Set.of("path","speedModifier","lastTargetPos").contains(field)){
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,test,field.equals("path")?"sinkPath":field.equals("speedModifier")?"sinkSpeed":"sinkTarget","(L"+sink+";)"+desc,false);return;
                        }
                        if(owner.equals(sink)&&opcode==Opcodes.PUTFIELD&&field.equals("path")){super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"setSinkPath","(L"+sink+";"+desc+")V",false);return;}
                        super.visitFieldInsn(opcode,owner,field,desc);
                    }
                    @Override public void visitMethodInsn(int opcode,String owner,String call,String desc,boolean itf){
                        if(owner.equals("net/minecraft/world/entity/ai/Brain")&&call.equals("setMemory")){
                            writes[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitLdcInsn(method.equals("start")?"START_PATH_WRITE":"TICK_PATH_RECONCILE");
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,"originalSinkPathWrite","(L"+owner+";Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Ljava/lang/Object;L"+sink+";Ljava/lang/String;)V",false);return;
                        }
                        if(owner.equals("net/minecraft/world/entity/ai/navigation/PathNavigation")&&call.equals("moveTo")){
                            moves[0]++;super.visitVarInsn(Opcodes.ALOAD,0);super.visitMethodInsn(Opcodes.INVOKESTATIC,hooks,"originalSinkMoveTo","(L"+owner+";Lnet/minecraft/world/level/pathfinder/Path;DL"+sink+";)Z",false);return;
                        }
                        if(owner.equals(sink)&&call.equals("start")){super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"restart","(L"+sink+";"+desc.substring(1),false);return;}
                        if(owner.equals(sink)&&call.equals("tryComputePath")){super.visitMethodInsn(Opcodes.INVOKESTATIC,test,"compute","(L"+sink+";"+desc.substring(1),false);return;}
                        super.visitMethodInsn(opcode,owner,call,desc,itf);
                    }
                };
            }},ClassReader.SKIP_FRAMES);
        }require(members[0]==2&&writes[0]==2&&moves[0]==1,"exact genuine start/tick source boundaries");writer.visitEnd();byte[] b=writer.toByteArray();
        class Loader extends ClassLoader{Loader(){super(KneekuraDebugBrainNavigationSelfTest.class.getClassLoader());}Class<?> define(){return defineClass(name.replace('/','.'),b,0,b.length);}}
        return new Loader().define();
    }
    private static KneekuraDebugDecisionHooks.Session install(Subject subject,Set<String> channels,int events,int bytes,AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(context.get().selectionRevision());
        var session=new KneekuraDebugDecisionHooks.Session(subject,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static void sameScope(List<JsonObject> rows,int offset){String id=rows.get(offset).getAsJsonObject("data").get("sinkInvocationId").getAsString();for(int i=offset;i<rows.size();i++)require(rows.get(i).getAsJsonObject("data").get("sinkInvocationId").getAsString().equals(id),"actual captured invocation identity");}
    private static void emit(List<JsonObject> rows){for(var row:rows)System.out.println("BRAIN_NAVIGATION_INTEROP:"+new com.google.gson.Gson().toJson(row));}
    private static void nested(int depth,MoveToTargetSink sink,Subject owner){invoke(sink,owner,"TICK_FROM_BRIDGE",()->{if(depth>1)nested(depth-1,sink,owner);else call(start,null,sink,null,owner,100L);});}
    private static void compiledHandlers()throws Exception {
        String mob="(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/Mob;J)V",living=mob.replace("/Mob;","/LivingEntity;");
        String sink="Lnet/minecraft/world/entity/ai/behavior/MoveToTargetSink;",write="Lnet/minecraft/world/entity/ai/Brain;setMemory(Lnet/minecraft/world/entity/ai/memory/MemoryModuleType;Ljava/lang/Object;)V";
        var expected=Map.of("kneekura$startFromBridge",new String[]{"start"+living,sink+"start"+mob,"originalSinkCall"},
            "kneekura$tickFromBridge",new String[]{"tick"+living,sink+"tick"+mob,"originalSinkCall"},
            "kneekura$startFromTick",new String[]{"tick"+mob,sink+"start"+mob,"originalSinkCall"},
            "kneekura$startPathWrite",new String[]{"start"+mob,write,"originalSinkPathWrite"},
            "kneekura$tickPathWrite",new String[]{"tick"+mob,write,"originalSinkPathWrite"},
            "kneekura$navigationReturn",new String[]{"start"+mob,"Lnet/minecraft/world/entity/ai/navigation/PathNavigation;moveTo(Lnet/minecraft/world/level/pathfinder/Path;D)Z","originalSinkMoveTo"});
        var found=new HashSet<String>();int[] originals={0};
        try(var bytes=KneekuraDebugBrainNavigationSelfTest.class.getClassLoader().getResourceAsStream("com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/KneekuraDebugBrainNavigationMixin.class")){
            require(bytes!=null,"compiled source-specific mixin required");new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String desc,String signature,String[] exceptions){
                    var spec=expected.get(name);if(spec==null){if(!name.startsWith("lambda$"))return null;return new MethodVisitor(Opcodes.ASM9){@Override public void visitMethodInsn(int op,String owner,String call,String descriptor,boolean itf){require(op==Opcodes.INVOKEVIRTUAL&&owner.endsWith("/KneekuraDebugBrainNavigationMixin")&&Set.of("start","tick","stop").contains(call)&&descriptor.equals(mob),"original protected Shadow delegate only");originals[0]++;}};}
                    found.add(name);int[] methods={0},target={0},at={0},required={0},calls={0};return new MethodVisitor(Opcodes.ASM9){
                        private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String key,Object value){if(key.equals("require"))required[0]=(Integer)value;if(key.equals("target")){require(value.equals(spec[1]),"exact original target");target[0]++;}if(key.equals("value")&&value.equals("INVOKE"))at[0]++;if(key.equals("cancellable"))require(Boolean.FALSE.equals(value),"noncancelling");}
                            @Override public AnnotationVisitor visitArray(String key){if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String ignored,Object value){require(value.equals(spec[0]),"exact source method descriptor");methods[0]++;}};return annotation();}
                            @Override public AnnotationVisitor visitAnnotation(String key,String desc){return annotation();}};}
                        @Override public AnnotationVisitor visitAnnotation(String desc,boolean visible){require(desc.endsWith("/Redirect;"),"original-call redirect only");return annotation();}
                        @Override public void visitMethodInsn(int op,String owner,String call,String descriptor,boolean itf){require(op==Opcodes.INVOKESTATIC&&owner.endsWith("/KneekuraDebugDecisionHooks")&&call.equals(spec[2]),"single observer/original delegate, no query replay");calls[0]++;}
                        @Override public void visitEnd(){require(methods[0]==1&&target[0]==1&&at[0]==1&&required[0]==1&&calls[0]==1,"required exact original boundary");}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }require(found.equals(expected.keySet())&&originals[0]==4,"six existing redirect handlers and four protected delegates");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        var owner=(Subject)unsafe.allocateInstance(Subject.class);var nav=(Navigation)unsafe.allocateInstance(Navigation.class);field(nav,PathNavigation.class,"mob",owner);field(owner,Mob.class,"navigation",nav);var brain=new ProbeBrain();field(owner,LivingEntity.class,"brain",brain);
        var sink=new MoveToTargetSink();var requested=path(1);field(sink,MoveToTargetSink.class,"path",requested);field(sink,MoveToTargetSink.class,"speedModifier",0.75f);
        var actualStart=MoveToTargetSink.class.getDeclaredMethod("start",ServerLevel.class,Mob.class,long.class);actualStart.setAccessible(true);call(actualStart,sink,null,owner,100L);
        require(brain.writes==1&&nav.moves==1&&owner.brains==1&&owner.navigations==1,"genuine original start writes PATH and calls Navigation exactly once");
        require(read(nav,PathNavigation.class,"path")==requested,"genuine original cached Path");
        try{scope=KneekuraDebugDecisionHooks.class.getMethod("originalSinkCall",MoveToTargetSink.class,Mob.class,long.class,String.class,Runnable.class);}catch(NoSuchMethodException e){throw new AssertionError("original sink invocation observation missing",e);}
        var compiled=fixture();start=compiled.getMethod("start",MoveToTargetSink.class,ServerLevel.class,Mob.class,long.class);tick=compiled.getMethod("tick",MoveToTargetSink.class,ServerLevel.class,Mob.class,long.class);
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();
        reset(owner,nav);brain.writes=nav.moves=owner.brains=owner.navigations=0;install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);
        invoke(sink,owner,"START_FROM_BRIDGE",()->{call(start,null,sink,null,owner,100L);owner.forbid=true;});require(rows.size()==3&&brain.writes==1&&nav.moves==1&&owner.brains==1&&owner.navigations==1,"actual bytecode fixture once/no observer getter replay");sameScope(rows,0);
        require(rows.get(0).get("kind").getAsString().equals("BRAIN_PATH_MEMORY_WRITE_RETURN")&&rows.get(1).get("kind").getAsString().equals("BRAIN_PATH_NAVIGATION_RETURN")&&rows.get(2).get("kind").getAsString().equals("BRAIN_PATH_SINK_RETURN"),"write then virtual Navigation then original void return");
        require(rows.get(0).getAsJsonObject("data").get("requestedMatchesCachedMemory").getAsBoolean(),"actual cached Brain PATH raw identity");require(rows.get(1).getAsJsonObject("data").get("result").getAsBoolean(),"actual original virtual boolean");
        var detached=rows.get(1).deepCopy();requested.advance();require(rows.get(1).equals(detached),"detached original cached Path copy");
        reset(owner,nav);nav.invert=true;int n=rows.size();invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(rows.size()==n+3&&!rows.get(n+1).getAsJsonObject("data").get("result").getAsBoolean(),"final custom virtual false distinct from base true");nav.invert=false;
        reset(owner,nav);var old=path(20);field(nav,PathNavigation.class,"path",old);field(sink,MoveToTargetSink.class,"lastTargetPos",null);n=rows.size();invoke(sink,owner,"TICK_FROM_BRIDGE",()->{call(tick,null,sink,null,owner,100L);owner.forbid=true;nav.forbid=true;});require(rows.size()==n+2&&nav.paths==1&&sinkPath(sink)==old,"original early tick reconciles raw cached Path exactly once");
        reset(owner,nav);var failure=new IllegalStateException("ORIGINAL_NAVIGATION_FAILURE");nav.failure=failure;n=rows.size();try{invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));throw new AssertionError("original must throw");}catch(IllegalStateException e){require(e==failure,"same original exception");}require(rows.size()==n+1,"completed memory write retained but no fabricated Navigation/frame normal return");nav.failure=null;
        reset(owner,nav);n=rows.size();invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(rows.size()==n+3,"exception cleanup permits next real invocation");
        emit(rows);
        for(Set<String> channels:List.of(Set.of("control"),Set.of("navigation_result"))){rows.clear();reset(owner,nav);install(owner,channels,256,524288,context,time,rows);invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(rows.isEmpty(),"channel opt-in only");}
        rows.clear();reset(owner,nav);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var workerFailure=new AtomicReference<Throwable>();Thread other=new Thread(()->{try{invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));}catch(Throwable e){workerFailure.set(e);}});other.start();other.join();require(rows.isEmpty()&&workerFailure.get()==null,"wrong thread original preserved/no observation");
        reset(owner,nav);invoke(new CustomSink(),owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(rows.isEmpty(),"unknown sink override does not inherit an observed frame");
        reset(owner,nav);var custom=new CustomMap();field(brain,Brain.class,"memories",custom);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,"START_FROM_BRIDGE",()->{call(start,null,sink,null,owner,100L);custom.forbid=true;});require(rows.get(0).getAsJsonObject("data").getAsJsonObject("memoryAtReturn").get("status").getAsString().equals("NOT_EXPOSED"),"custom cached memory map never queried by observer");
        emit(rows);field(brain,Brain.class,"memories",new HashMap<>(Map.of(MemoryModuleType.PATH,Optional.empty())));
        rows.clear();reset(owner,nav);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);nested(9,sink,owner);require(rows.size()==8&&rows.stream().allMatch(r->r.get("kind").getAsString().equals("BRAIN_PATH_SINK_RETURN")),"depth9 suppresses nested callbacks without assigning parent invocation");
        rows.clear();reset(owner,nav);var rearmed=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,"START_FROM_BRIDGE",()->{try{install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);}catch(Exception e){throw new AssertionError(e);}});require(rows.isEmpty()&&read(rearmed,KneekuraDebugDecisionHooks.Session.class,"sinkFrame")==null,"rearm cannot retain old invocation");
        for(String fence:List.of("EVENT","BYTE","TIME","REVISION","OWNER","NAVIGATION_OWNER")){
            rows.clear();reset(owner,nav);time.set(100);var originalContext=context.get();var fenced=install(owner,Set.of("brain_navigation"),fence.equals("EVENT")?1:256,fence.equals("BYTE")?1:524288,context,time,rows);
            if(fence.equals("TIME"))time.set(200);if(fence.equals("REVISION"))context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,originalContext.subjectUuid(),"minecraft:overworld"));
            var otherOwner=(Subject)unsafe.allocateInstance(Subject.class);if(fence.equals("NAVIGATION_OWNER"))field(nav,PathNavigation.class,"mob",otherOwner);
            int before=nav.moves;invoke(sink,fence.equals("OWNER")?otherOwner:owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(nav.moves==before+1,"fenced original executes once");require(rows.size()==(fence.equals("EVENT")?1:0),"exact capture fence "+fence);require(read(fenced,KneekuraDebugDecisionHooks.Session.class,"sinkFrame")==null,"fenced frame cleanup");context.set(originalContext);field(nav,PathNavigation.class,"mob",owner);
        }
        rows.clear();reset(owner,nav);time.set(100);var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(7);for(int i=0;i<256;i++)snapshot.memoryValue(path(1000+i*3));
        var capped=new KneekuraDebugDecisionHooks.Session(owner,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(capped);invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(rows.size()==3&&rows.get(1).getAsJsonObject("data").getAsJsonObject("requestedPath").getAsJsonObject("identity").get("status").getAsString().equals("NOT_EXPOSED"),"shared Snapshot256 cap does not create a token");emit(rows);
        rows.clear();reset(owner,nav);var components=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);var token=KneekuraDebugDecisionHooks.Session.class.getDeclaredMethod("token",Object.class);token.setAccessible(true);for(int i=0;i<128;i++)call(token,components,new Object());invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(rows.size()==3&&!rows.get(1).getAsJsonObject("data").get("instanceIdentityStatus").getAsString().equals("AVAILABLE"),"component128 cap independent of shared Path identities");emit(rows);
        rows.clear();reset(owner,nav);field(sink,MoveToTargetSink.class,"speedModifier",Float.NaN);install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(rows.size()==3&&!rows.get(1).getAsJsonObject("data").has("requestedSpeed"),"original nonfinite speed unchanged but omitted from facts");emit(rows);field(sink,MoveToTargetSink.class,"speedModifier",0.75f);
        rows.clear();reset(owner,nav);int beforeMoves=nav.moves;var writerFailed=new KneekuraDebugDecisionHooks.Session(owner,null,null,new KneekuraDebugDecisionSnapshot(),new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("brain_navigation"),context::get,time::get,(method,row)->{throw new java.io.IOException("SOURCE_WRITER_FAILURE");});KneekuraDebugDecisionHooks.install(writerFailed);invoke(sink,owner,"START_FROM_BRIDGE",()->call(start,null,sink,null,owner,100L));require(nav.moves==beforeMoves+1&&writerFailed.budget().reason().equals("WRITER_UNAVAILABLE"),"writer error fails capture closed, original still once");
        rows.clear();reset(owner,nav);var session=install(owner,Set.of("brain_navigation"),256,524288,context,time,rows);for(int i=0;i<257;i++)try{invoke(sink,owner,"START_FROM_BRIDGE",()->{throw failure;});}catch(IllegalStateException e){require(e==failure,"same exception across ID cap");}require(rows.isEmpty()&&((Integer)read(session,KneekuraDebugDecisionHooks.Session.class,"nextSink"))==256&&read(session,KneekuraDebugDecisionHooks.Session.class,"sinkFrame")==null,"finite invocation IDs and exception cleanup");
        compiledHandlers();KneekuraDebugDecisionHooks.clear("DONE");System.out.println("Original Brain/Navigation call fixture: genuine start/early-tick, write/virtual/void separation, once/exception/copy/custom map/depth/rearm/ID/budget/owner/thread/writer and compiled-handler fences; not native or complete path-computation proof");
    }
}
