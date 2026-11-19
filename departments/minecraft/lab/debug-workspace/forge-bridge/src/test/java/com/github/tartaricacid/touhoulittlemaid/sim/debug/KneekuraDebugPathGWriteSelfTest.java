package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;
import java.util.ArrayList;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

/** Genuine mapped direct-field/observer fences, not an original transformed-loop acceptance. */
public final class KneekuraDebugPathGWriteSelfTest {
    private static final class Subject extends Mob {private Subject(){super(null,null);}}
    private static final class CustomNode extends Node {
        CustomNode(){super(0,64,0);}
        @Override public float distanceTo(Node other){throw new AssertionError("NODE_QUERY_REPLAY");}
        @Override public float distanceManhattan(BlockPos pos){throw new AssertionError("NODE_QUERY_REPLAY");}
        @Override public boolean inOpenSet(){throw new AssertionError("NODE_QUERY_REPLAY");}
        @Override public BlockPos asBlockPos(){throw new AssertionError("NODE_QUERY_REPLAY");}
    }
    private static void require(boolean b,String m){if(!b)throw new AssertionError(m);}
    private static JsonObject data(JsonObject r){return r.getAsJsonObject("data");}
    private static KneekuraDebugDecisionHooks.Session install(Subject selected,Set<String> channels,int events,int bytes,int nodes,
            AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,java.util.function.LongSupplier time,KneekuraDebugDecisionHooks.Sink sink)throws Exception {
        var s=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context.get(),100,10,events,bytes),nodes,channels,context::get,time,sink);
        KneekuraDebugDecisionHooks.install(s);return s;
    }
    private static void write(PathFinder f,Node n,float value){KneekuraDebugDecisionHooks.originalAcceptedGWrite(f,n,value);}
    private static void originalWriteBytecode()throws Exception {
        int[] fields={0},methodsBeforeWrite={0};
        try(var stream=KneekuraDebugDecisionHooks.class.getResourceAsStream("KneekuraDebugDecisionHooks.class")){
            require(stream!=null,"actual compiled hook bytecode required");
            new ClassReader(stream).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
                    if(!name.equals("originalAcceptedGWrite"))return null;
                    require(descriptor.equals("(Lnet/minecraft/world/level/pathfinder/PathFinder;Lnet/minecraft/world/level/pathfinder/Node;F)V"),"actual receiver/value helper descriptor");
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public void visitFieldInsn(int opcode,String owner,String name,String descriptor){
                            if(opcode==Opcodes.PUTFIELD){require(owner.equals("net/minecraft/world/level/pathfinder/Node")&&name.equals("g")&&descriptor.equals("F"),"only original Node.g assignment");fields[0]++;}
                        }
                        @Override public void visitMethodInsn(int opcode,String owner,String name,String descriptor,boolean itf){if(fields[0]==0)methodsBeforeWrite[0]++;}
                        @Override public void visitInvokeDynamicInsn(String name,String descriptor,org.objectweb.asm.Handle bootstrap,Object...args){if(fields[0]==0)methodsBeforeWrite[0]++;}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }
        require(fields[0]==1&&methodsBeforeWrite[0]==0,"one original direct field assignment precedes any observer method/lambda");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);var unsafe=(sun.misc.Unsafe)field.get(null);
        Subject selected=(Subject)unsafe.allocateInstance(Subject.class);selected.setUUID(new UUID(0,1));
        Subject excluded=(Subject)unsafe.allocateInstance(Subject.class);excluded.setUUID(new UUID(0,2));
        var initial=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,2,1,selected.getUUID().toString(),"minecraft:overworld");
        var context=new AtomicReference<>(initial);var rows=new ArrayList<JsonObject>();var finder=new PathFinder(new WalkNodeEvaluator(),32);
        var node=new CustomNode();var parent=new Node(0,64,0);node.cameFrom=parent;node.h=11;node.f=50;
        KneekuraDebugDecisionHooks.clear("INITIAL_OFF");write(finder,node,-0.0f);
        require(Float.floatToRawIntBits(node.g)==Float.floatToRawIntBits(-0.0f),"OFF preserves exact original signed-zero assignment");
        new KneekuraDebugDecisionBurstRequest(10,64,524288,2,Set.of("path_g"));
        var session=install(selected,Set.of("path_g"),64,524288,2,context,()->100L,(m,r)->{
            require(node.g==data(r).get("writtenG").getAsFloat()||Float.isNaN(node.g),"writer observes already assigned original value");rows.add(r);
        });
        write(finder,node,3.5f);require(node.g==3.5f&&rows.isEmpty(),"unregistered search preserves assignment but excludes observation");
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);write(finder,node,3.5f);
        require(rows.size()==1&&rows.get(0).get("semantics").getAsString().equals("ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY"),"field checkpoint only");
        var first=data(rows.get(0));require(first.getAsJsonObject("node").getAsJsonObject("data").get("g").getAsFloat()==3.5f&&
            first.getAsJsonObject("node").getAsJsonObject("data").get("h").getAsFloat()==11&&first.getAsJsonObject("node").getAsJsonObject("data").get("f").getAsFloat()==50,"g observed before later original heuristic/f update");
        require(!first.getAsJsonObject("nodeIdentity").equals(first.getAsJsonObject("predecessorIdentity")),"equal coordinates are distinct original references");
        node.g=99;node.cameFrom=null;require(first.get("writtenG").getAsFloat()==3.5f&&first.getAsJsonObject("predecessorIdentity").get("status").getAsString().equals("AVAILABLE"),"detached written/node/predecessor facts");
        var limited=new CustomNode();limited.cameFrom=node;
        // Use the same actual table and a third receiver; no coordinate fallback at max2.
        session=install(selected,Set.of("path_g"),64,524288,1,context,()->100L,(m,r)->rows.add(r));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);write(finder,node,7);write(finder,limited,8);
        require(data(rows.get(2)).getAsJsonObject("nodeIdentity").get("detail").getAsString().equals("NODE_IDENTITY_LIMIT")&&
            data(rows.get(2)).getAsJsonObject("predecessorIdentity").get("status").getAsString().equals("AVAILABLE"),"unknown receiver retains actual bounded predecessor identity");
        write(finder,limited,Float.NaN);require(data(rows.get(3)).get("writtenGStatus").getAsString().equals("NOT_EXPOSED")&&
            data(rows.get(3)).getAsJsonObject("node").getAsJsonObject("data").get("gStatus").getAsString().equals("NOT_EXPOSED"),"NaN remains unknown on both original argument and cached field");
        var interop=new ArrayList<>(rows);
        int events=session.budget().events();try{write(finder,null,9);throw new AssertionError("ORIGINAL_NULL_EXCEPTION_REQUIRED");}catch(NullPointerException expected){}
        require(session.budget().events()==events,"original null exception precedes any observation");
        var refs=KneekuraDebugDecisionHooks.Session.class.getDeclaredField("heapNodes");refs.setAccessible(true);
        var pending=KneekuraDebugDecisionHooks.Session.class.getDeclaredField("pendingPops");pending.setAccessible(true);
        require(pending.get(session)==null,"g-write-only capture has no pop marker holders");
        var quiet=new ArrayList<JsonObject>();
        for(String channel:new String[]{"path","frontier","path_nodes","neighbors"}){
            quiet.clear();session=install(selected,Set.of(channel),64,524288,2,context,()->100L,(m,r)->quiet.add(r));
            KneekuraDebugDecisionHooks.pathBegin(finder,selected);write(finder,node,123);require(node.g==123&&quiet.isEmpty(),"legacy channel does not acquire new field events: "+channel);
        }
        for(String boundary:new String[]{"THREAD","ARENA","WINDOW","EVENT","BYTE","WRITER","END","REBEGIN"}){
            quiet.clear();var tick=new java.util.concurrent.atomic.AtomicLong(100);
            session=install(selected,Set.of("path_g"),boundary.equals("EVENT")?1:64,boundary.equals("BYTE")?1:524288,2,context,tick::get,
                (m,r)->{if(boundary.equals("WRITER"))throw new java.io.IOException("TEST_WRITER");quiet.add(r);});
            KneekuraDebugDecisionHooks.pathBegin(finder,selected);
            if(boundary.equals("ARENA"))context.set(new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,3,1,selected.getUUID().toString(),"minecraft:overworld"));
            if(boundary.equals("WINDOW"))tick.set(110);
            if(boundary.equals("EVENT"))write(finder,node,122);
            if(boundary.equals("END"))KneekuraDebugDecisionHooks.pathEnd(finder);
            if(boundary.equals("REBEGIN"))KneekuraDebugDecisionHooks.pathBegin(finder,excluded);
            if(boundary.equals("THREAD")){Thread thread=new Thread(()->write(finder,node,123));thread.start();thread.join();}else write(finder,node,123);
            require(node.g==123&&quiet.size()==(boundary.equals("EVENT")?1:0),"original write survives capture fence: "+boundary);
            require(((java.util.Map<?,?>)refs.get(session)).size()==(boundary.equals("THREAD")?1:0),"owning-thread preservation/stop reference release: "+boundary);
            if(boundary.equals("ARENA"))require("CONTEXT_CHANGED".equals(session.budget().reason()),"exact Arena context stop reason");
            if(boundary.equals("WINDOW"))require("WINDOW_ENDED".equals(session.budget().reason()),"exact window stop reason");
            if(boundary.equals("EVENT"))require("EVENT_BUDGET".equals(session.budget().reason()),"exact event stop reason");
            if(boundary.equals("BYTE"))require("BYTE_BUDGET".equals(session.budget().reason()),"exact byte stop reason");
            if(boundary.equals("WRITER"))require("WRITER_UNAVAILABLE".equals(session.budget().reason()),"exact writer stop reason");
            context.set(initial);
        }
        KneekuraDebugDecisionHooks.clear("DONE");require(((java.util.Map<?,?>)refs.get(session)).isEmpty(),"OFF releases all Node/finder references");
        quiet.clear();session=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(initial,100,10,64,524288),2,Set.of("path_g"),
            ()->{node.g=77;return initial;},()->100L,(m,r)->quiet.add(r));
        KneekuraDebugDecisionHooks.install(session);KneekuraDebugDecisionHooks.pathBegin(finder,selected);write(finder,node,9);
        require(quiet.size()==1&&data(quiet.get(0)).get("writtenG").getAsFloat()==9&&
            data(quiet.get(0)).getAsJsonObject("node").getAsJsonObject("data").get("g").getAsFloat()==77,
            "synthetic side-effectful context supplier proves original argument and later cached field stay separate");
        interop.add(quiet.get(0));
        quiet.clear();session=install(selected,Set.of("path_g"),64,524288,2,context,()->100L,(m,r)->quiet.add(r));
        for(int i=0;i<9;i++){var other=new PathFinder(new WalkNodeEvaluator(),32);KneekuraDebugDecisionHooks.pathBegin(other,selected);write(other,node,123);}
        require(node.g==123&&quiet.size()==8&&((java.util.Map<?,?>)refs.get(session)).size()==8,"original assignments preserve maximum8 registered finders");
        KneekuraDebugDecisionHooks.clear("DONE");
        originalWriteBytecode();for(var r:interop)System.out.println("G_WRITE_INTEROP:"+r);
        System.out.println("Original g-field write: actual direct assignment before observation, signed-zero/NaN/null exception/custom Node no query, bounded detached references/OFF/channel/thread/context/caps/writer teardown");
    }
}
