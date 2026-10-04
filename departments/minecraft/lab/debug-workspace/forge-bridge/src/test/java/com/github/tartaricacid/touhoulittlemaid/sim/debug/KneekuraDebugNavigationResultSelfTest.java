package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.*;
import net.minecraft.world.phys.Vec3;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import org.objectweb.asm.*;

/** Genuine originals with explicit test-only virtual overrides; installed RETURN proof is separate. */
public final class KneekuraDebugNavigationResultSelfTest {
    private static Method recorder;
    private static final class Subject extends Mob {
        private Subject(){super(null,null);}
        @Override public PathNavigation getNavigation(){throw new AssertionError("NAVIGATION_GETTER_REPLAY");}
        @Override public String toString(){throw new AssertionError("SUBJECT_STRING_REPLAY");}
    }
    private static final class Navigation extends PathNavigation {
        int done,trim,position;boolean forbid;
        Navigation(Mob mob,Level level){super(mob,level);}
        private void allowed(){if(forbid)throw new AssertionError("NAVIGATION_REPLAY");}
        @Override protected PathFinder createPathFinder(int i){throw new AssertionError("SEARCH_REPLAY");}
        @Override protected boolean canUpdatePath(){throw new AssertionError("UPDATE_REPLAY");}
        @Override protected Vec3 getTempMobPos(){allowed();position++;return Vec3.ZERO;}
        @Override protected void trimPath(){allowed();trim++;}
        @Override public boolean isDone(){allowed();done++;return super.isDone();}
        @Override public Path getPath(){throw new AssertionError("PATH_GETTER_REPLAY");}
        @Override public String toString(){throw new AssertionError("NAVIGATION_STRING_REPLAY");}
    }
    private static final class CustomPath extends Path {
        int same,done,count;boolean forbid;RuntimeException failure;
        CustomPath(){super(nodes(2,0),new BlockPos(1,0,0),false);}
        private void allowed(){if(forbid)throw new AssertionError("CUSTOM_PATH_REPLAY");}
        @Override public boolean sameAs(Path path){allowed();same++;if(failure!=null)throw failure;return super.sameAs(path);}
        @Override public boolean isDone(){allowed();done++;return super.isDone();}
        @Override public int getNodeCount(){allowed();count++;return super.getNodeCount();}
        @Override public boolean canReach(){throw new AssertionError("REACH_GETTER_REPLAY");}
        @Override public String toString(){throw new AssertionError("PATH_STRING_REPLAY");}
    }
    private static final class CustomList extends ArrayList<Node> {
        boolean forbid;
        @Override public int size(){if(forbid)throw new AssertionError("CUSTOM_LIST_REPLAY");return super.size();}
        @Override public Node get(int i){if(forbid)throw new AssertionError("CUSTOM_LIST_REPLAY");return super.get(i);}
    }
    private static ArrayList<Node> nodes(int count,int offset){var out=new ArrayList<Node>();for(int i=0;i<count;i++){var n=new Node(i+offset,0,0);n.type=BlockPathTypes.WALKABLE;out.add(n);}return out;}
    private static Path path(int count,int offset,boolean reach){return new Path(nodes(count,offset),new BlockPos(offset+count,0,0),reach);}
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static JsonObject data(JsonObject row){return row.getAsJsonObject("data");}
    private static void field(Class<?> base,String name,Object owner,Object value)throws Exception {var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}
    private static Path cached(Navigation n)throws Exception {return (Path)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"path",n);}
    private static void emit(Navigation n,Path requested,double speed,boolean result)throws Exception {
        n.forbid=true;if(requested instanceof CustomPath p)p.forbid=true;
        try{recorder.invoke(null,n,requested,speed,result);}
        catch(InvocationTargetException error){if(error.getCause() instanceof Error e)throw e;if(error.getCause() instanceof RuntimeException e)throw e;throw error;}
        finally{n.forbid=false;if(requested instanceof CustomPath p)p.forbid=false;}
    }
    private static boolean original(Navigation n,Path requested,double speed)throws Exception {boolean result=n.moveTo(requested,speed);emit(n,requested,speed,result);return result;}
    private static KneekuraDebugDecisionHooks.Session install(Subject subject,KneekuraDebugDecisionSnapshot snapshot,Set<String> channels,int events,int bytes,
            AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong time,List<JsonObject> rows)throws Exception {
        var s=new KneekuraDebugDecisionHooks.Session(subject,null,null,snapshot,
            new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,time::get,(method,row)->rows.add(row));
        KneekuraDebugDecisionHooks.install(s);return s;
    }
    private static void handlerBytecode()throws Exception {
        String name="com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/KneekuraDebugNavigationResultMixin";
        int[] found={0};try(var stream=KneekuraDebugNavigationResultSelfTest.class.getClassLoader().getResourceAsStream(name+".class")){
            require(stream!=null,"compiled normal-return Navigation mixin required");new ClassReader(stream).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String desc,String signature,String[] exceptions){
                    if(!name.startsWith("kneekura$"))return null;found[0]++;int[] calls={0},required={0},returns={0},methods={0};
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public AnnotationVisitor visitAnnotation(String desc,boolean visible){require(desc.endsWith("/Inject;"),"normal original RETURN injection");return new AnnotationVisitor(Opcodes.ASM9){
                            @Override public void visit(String key,Object value){if(key.equals("require"))required[0]=(Integer)value;if(key.equals("cancellable"))require(Boolean.FALSE.equals(value),"must not cancel");}
                            @Override public AnnotationVisitor visitArray(String key){
                                if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String k,Object v){require(v.equals("moveTo(Lnet/minecraft/world/level/pathfinder/Path;D)Z"),"exact erased original descriptor");methods[0]++;}};
                                return new AnnotationVisitor(Opcodes.ASM9){@Override public AnnotationVisitor visitAnnotation(String k,String d){return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String k,Object v){if(k.equals("value")){require(v.equals("RETURN"),"normal return only");returns[0]++;}}};}};
                            }
                        };}
                        @Override public void visitMethodInsn(int opcode,String owner,String call,String d,boolean itf){
                            if(owner.endsWith("/KneekuraDebugDecisionHooks")){require(call.equals("navigationMoveReturn")&&opcode==Opcodes.INVOKESTATIC,"one observer delegate");calls[0]++;}
                            else require(owner.endsWith("/CallbackInfoReturnable")&&call.equals("getReturnValueZ"),"no original query/getter/replay or changed return");
                        }
                        @Override public void visitEnd(){require(calls[0]==1&&required[0]==1&&returns[0]==1&&methods[0]==1,"one exact required noncancelling normal-return capture");}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }require(found[0]==1,"one original Navigation boundary");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        Subject subject=(Subject)unsafe.allocateInstance(Subject.class),other=(Subject)unsafe.allocateInstance(Subject.class);
        Navigation nav=(Navigation)unsafe.allocateInstance(Navigation.class),foreign=(Navigation)unsafe.allocateInstance(Navigation.class);
        field(PathNavigation.class,"mob",nav,subject);field(PathNavigation.class,"mob",foreign,other);field(Mob.class,"navigation",subject,nav);field(Mob.class,"navigation",other,foreign);
        Path old=path(2,0,true),equal=path(2,0,false);field(PathNavigation.class,"path",nav,old);
        boolean accepted=nav.moveTo(equal,.75);require(accepted&&cached(nav)==old,"genuine equal route keeps distinct cached reference with true return");
        try{recorder=KneekuraDebugDecisionHooks.class.getMethod("navigationMoveReturn",PathNavigation.class,Path.class,double.class,boolean.class);}
        catch(NoSuchMethodException error){throw new AssertionError("original Navigation boolean/cached reference capture missing",error);}
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(7);
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));
        var time=new AtomicLong(100);var rows=new ArrayList<JsonObject>();
        KneekuraDebugDecisionHooks.clear("OFF");emit(nav,equal,.75,accepted);require(rows.isEmpty(),"OFF does not replay Navigation/path");
        install(subject,snapshot,Set.of("navigation_result"),256,524288,context,time,rows);
        require(!original(nav,null,.1)&&cached(nav)==null,"original null clears cached path and returns false");
        field(PathNavigation.class,"path",nav,old);require(original(nav,equal,.75)&&cached(nav)==old,"actual equal route keeps old path");
        require(!data(rows.get(1)).get("requestedMatchesCachedPath").getAsBoolean(),"true method return does not adopt requested reference");
        var fresh=path(2,10,false);require(original(nav,fresh,1.25)&&cached(nav)==fresh,"true original accepts route even canReach=false");
        JsonObject detached=rows.get(2).deepCopy();field(Path.class,"nextNodeIndex",fresh,2);require(rows.get(2).equals(detached),"cached result detached from future path progress");
        require(!original(nav,fresh,2),"done path original false");require(!original(nav,path(0,30,true),2),"empty path original false");
        var custom=new CustomPath();field(PathNavigation.class,"path",nav,null);int done=nav.done,trim=nav.trim,pos=nav.position;
        require(original(nav,custom,1)&&custom.same==1&&custom.done==1&&custom.count==1&&nav.done==done+1&&nav.trim==trim+1&&nav.position==pos+1,"actual original custom virtual calls once, observer never repeats");
        require(data(rows.get(5)).getAsJsonObject("requestedPath").getAsJsonObject("cachedFields").get("status").getAsString().equals("NOT_EXPOSED"),"custom Path structured fields unavailable while raw reference remains observed");
        var failure=new IllegalStateException("original sameAs failed");custom.failure=failure;int count=rows.size();
        try{original(nav,custom,1);throw new AssertionError("original exception lost");}catch(IllegalStateException e){require(e==failure,"original exception identity");}require(rows.size()==count&&custom.same==2,"throwing original has no normal-return event");custom.failure=null;
        require(original(nav,path(2,50,true),Double.NaN)&&Double.isNaN((Double)KneekuraDebugDecisionSnapshot.read(PathNavigation.class,"speedModifier",nav)),"original nonfinite speed is not changed");
        var list=new CustomList();list.addAll(nodes(2,70));var listed=new Path(list,new BlockPos(72,0,0),true);
        accepted=nav.moveTo(listed,1);list.forbid=true;emit(nav,listed,1,accepted);list.forbid=false;
        require(data(rows.get(7)).getAsJsonObject("requestedPath").getAsJsonObject("cachedFields").getAsJsonObject("data").get("nodesDetail").getAsString().equals("CUSTOM_NODE_LIST"),"custom list has no observer virtual size/get call");
        require(original(nav,path(65,80,false),1),"genuine long route original return");
        require(data(rows.get(8)).getAsJsonObject("requestedPath").getAsJsonObject("cachedFields").getAsJsonObject("data").getAsJsonArray("nodes").size()==64,"bounded shared cached Path prefix");
        var interop=new ArrayList<>(rows);count=rows.size();emit(foreign,equal,1,true);field(Mob.class,"navigation",subject,foreign);emit(nav,equal,1,true);field(Mob.class,"navigation",subject,nav);require(rows.size()==count,"exact selected owner and stored Navigation receiver fence");
        var error=new AtomicReference<Throwable>();Thread worker=new Thread(()->{try{emit(nav,equal,1,true);}catch(Throwable e){error.set(e);}});worker.start();worker.join();require(error.get()==null&&rows.size()==count,"server thread fence");
        install(subject,snapshot,Set.of("brain"),256,524288,context,time,rows);emit(nav,equal,1,true);require(rows.size()==count,"dedicated opt-in only");
        install(subject,snapshot,Set.of("navigation_result"),256,524288,context,time,rows);context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,context.get().subjectUuid(),context.get().dimension()));emit(nav,equal,1,true);require(rows.size()==count,"revision fence");
        snapshot.reset(8);rows.clear();install(subject,snapshot,Set.of("navigation_result"),1,524288,context,time,rows);original(nav,path(2,0,true),1);original(nav,path(2,2,true),1);require(rows.size()==1,"event budget does not suppress original moves");
        rows.clear();install(subject,snapshot,Set.of("navigation_result"),256,1,context,time,rows);original(nav,path(2,3,true),1);require(rows.isEmpty(),"byte budget");
        install(subject,snapshot,Set.of("navigation_result"),256,524288,context,time,rows);time.set(200);original(nav,path(2,4,true),1);require(rows.isEmpty(),"time fence");time.set(100);
        snapshot.reset(8);var shared=path(2,0,true);String sharedToken=snapshot.memoryValue(shared).getAsJsonObject("data").getAsJsonObject("instanceIdentity").get("token").getAsString();
        install(subject,snapshot,Set.of("navigation_result"),256,524288,context,time,rows);original(nav,shared,1);
        require(data(rows.get(0)).getAsJsonObject("requestedPath").getAsJsonObject("identity").get("token").getAsString().equals(sharedToken),"existing snapshot-memory Path reference shared, not component namespace");interop.add(rows.get(0));
        snapshot.reset(8);for(int i=0;i<256;i++)snapshot.memoryValue(path(2,i,true));rows.clear();install(subject,snapshot,Set.of("navigation_result"),256,524288,context,time,rows);original(nav,path(2,300,false),1);
        require(data(rows.get(0)).getAsJsonObject("requestedPath").getAsJsonObject("identity").get("status").getAsString().equals("NOT_EXPOSED"),"shared256 reference cap leaves unknown, no evicted/reused ID");interop.add(rows.get(0));
        rows.clear();snapshot.reset(8);var session=new KneekuraDebugDecisionHooks.Session(subject,null,null,snapshot,new KneekuraDebugDecisionBurstBudget(context.get(),100,100,256,524288),8,Set.of("navigation_result"),context::get,time::get,(method,row)->{throw new java.io.IOException("writer failed");});KneekuraDebugDecisionHooks.install(session);
        require(original(nav,path(2,301,false),1)&&rows.isEmpty(),"writer failure does not change original result");
        KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");handlerBytecode();
        require(interop.size()==11,"eleven genuine Navigation interop boundaries");
        for(var row:interop)System.out.println("NAVIGATION_RESULT_INTEROP:"+new com.google.gson.Gson().toJson(row));
        System.out.println("Genuine Navigation results: raw requested/cache references, equal-route retained path, original virtual counts/exceptions, detached cached facts, shared snapshot cap and selected/context budgets; installed proof separate");
    }
}
