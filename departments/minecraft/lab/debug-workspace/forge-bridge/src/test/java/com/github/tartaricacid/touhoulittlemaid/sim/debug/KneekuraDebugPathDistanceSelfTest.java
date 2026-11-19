package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin.KneekuraDebugPathDecisionMixin;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import org.objectweb.asm.*;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

/** Actual compiled handler through an untransformed Shadow carrier, not native Mixin acceptance. */
public final class KneekuraDebugPathDistanceSelfTest {
    private static final class Subject extends Mob {private Subject(){super(null,null);}}
    private static final class QueryNode extends Node {
        int originalDistanceQueries;
        QueryNode(){super(0,64,0);}
        @Override public float distanceTo(Node other){originalDistanceQueries++;return 12.5f;}
        @Override public float distanceManhattan(BlockPos pos){throw new AssertionError("EXTRA_QUERY");}
        @Override public boolean inOpenSet(){throw new AssertionError("EXTRA_QUERY");}
        @Override public BlockPos asBlockPos(){throw new AssertionError("EXTRA_QUERY");}
    }
    private static final class CountingFinder extends PathFinder {
        int calls;float result=31.25f;boolean base;RuntimeException failure;Node actualFrom,actualTo;
        CountingFinder(){super(new WalkNodeEvaluator(),32);}
        @Override protected float distance(Node from,Node to){calls++;actualFrom=from;actualTo=to;if(failure!=null)throw failure;return base?super.distance(from,to):result;}
        float invokeOriginal(Node from,Node to){return distance(from,to);}
    }
    private static final class ShadowCarrier extends KneekuraDebugPathDecisionMixin {
        final CountingFinder finder;
        ShadowCarrier(CountingFinder finder){this.finder=finder;}
        @Override protected float distance(Node from,Node to){return finder.invokeOriginal(from,to);}
    }
    private static void require(boolean b,String m){if(!b)throw new AssertionError(m);}
    private static JsonObject data(JsonObject r){return r.getAsJsonObject("data");}
    private static float invoke(CountingFinder finder,Node from,Node to)throws Exception {
        var method=KneekuraDebugPathDecisionMixin.class.getDeclaredMethod("kneekura$originalDistance",PathFinder.class,Node.class,Node.class);
        method.setAccessible(true);
        try{return (Float)method.invoke(new ShadowCarrier(finder),finder,from,to);}
        catch(InvocationTargetException error){if(error.getCause() instanceof RuntimeException cause)throw cause;if(error.getCause() instanceof Error cause)throw cause;throw error;}
    }
    private static KneekuraDebugDecisionHooks.Session install(Subject subject,Set<String> channels,int events,int bytes,int nodes,
            AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,java.util.function.LongSupplier time,KneekuraDebugDecisionHooks.Sink sink)throws Exception {
        var session=new KneekuraDebugDecisionHooks.Session(subject,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context.get(),100,10,events,bytes),nodes,channels,context::get,time,sink);
        KneekuraDebugDecisionHooks.install(session);return session;
    }
    private static void handlerBytecode()throws Exception {
        int[] shadow={0},original={0},observer={0},returnSlot={-1};
        try(var stream=KneekuraDebugPathDecisionMixin.class.getResourceAsStream("KneekuraDebugPathDecisionMixin.class")){
            new ClassReader(stream).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
                    if(name.equals("distance")){require((access&(Opcodes.ACC_PROTECTED|Opcodes.ACC_ABSTRACT))==(Opcodes.ACC_PROTECTED|Opcodes.ACC_ABSTRACT)&&(access&(Opcodes.ACC_PUBLIC|Opcodes.ACC_STATIC|Opcodes.ACC_FINAL))==0,"protected abstract Shadow, no access widening");shadow[0]++;return null;}
                    if(!name.equals("kneekura$originalDistance"))return null;
                    require(descriptor.equals("(Lnet/minecraft/world/level/pathfinder/PathFinder;Lnet/minecraft/world/level/pathfinder/Node;Lnet/minecraft/world/level/pathfinder/Node;)F"),"original receiver and arguments handler");
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public void visitMethodInsn(int opcode,String owner,String name,String desc,boolean itf){
                            if(name.equals("distance")){require(opcode==Opcodes.INVOKEVIRTUAL&&owner.endsWith("/KneekuraDebugPathDecisionMixin")&&observer[0]==0,"one virtual target Shadow call before observer");original[0]++;}
                            else {require(name.equals("pathDistanceReturn")&&original[0]==1&&opcode==Opcodes.INVOKESTATIC,"only capture after original virtual return");observer[0]++;}
                        }
                        @Override public void visitVarInsn(int opcode,int slot){if(opcode==Opcodes.FSTORE){require(returnSlot[0]<0,"one primitive original result slot");returnSlot[0]=slot;}if(opcode==Opcodes.FLOAD)require(slot==returnSlot[0],"observer and final return use same result slot");}
                        @Override public void visitInsn(int opcode){require(!Set.of(Opcodes.FADD,Opcodes.FSUB,Opcodes.FMUL,Opcodes.FDIV,Opcodes.FNEG).contains(opcode),"no primitive result recomputation");}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }
        require(shadow[0]==1&&original[0]==1&&observer[0]==1&&returnSlot[0]>=0,"actual compiled single virtual call and same primitive result");
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);var unsafe=(sun.misc.Unsafe)field.get(null);
        Subject selected=(Subject)unsafe.allocateInstance(Subject.class);selected.setUUID(new UUID(0,1));
        var initial=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,2,1,selected.getUUID().toString(),"minecraft:overworld");
        var context=new AtomicReference<>(initial);var rows=new ArrayList<JsonObject>();var finder=new CountingFinder();var from=new QueryNode();var to=new QueryNode();
        KneekuraDebugDecisionHooks.clear("OFF");finder.result=-0.0f;
        require(Float.floatToRawIntBits(invoke(finder,from,to))==Float.floatToRawIntBits(-0.0f)&&finder.calls==1,"OFF preserves original primitive bits and single dispatch");
        new KneekuraDebugDecisionBurstRequest(10,64,524288,2,Set.of("path_distance"));finder.result=31.25f;
        var session=install(selected,Set.of("path_distance"),64,524288,2,context,()->100L,(m,r)->{
            require(finder.calls>=2&&finder.actualFrom==from&&finder.actualTo==to,"original actual protected override already ran with exact references");rows.add(r);
        });
        KneekuraDebugDecisionHooks.pathDistanceReturn(finder,from,to,9);require(rows.isEmpty(),"unregistered search excluded");
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);int before=finder.calls;
        require(invoke(finder,from,to)==31.25f&&finder.calls==before+1&&from.originalDistanceQueries==0,"custom protected override, no replay or base-only substitution");
        var first=data(rows.get(0));require(first.get("returnedDistance").getAsFloat()==31.25f&&!first.getAsJsonObject("fromIdentity").equals(first.getAsJsonObject("toIdentity")),"original return independent of equal coordinates/reference IDs");
        from.g=77;require(first.getAsJsonObject("fromNode").getAsJsonObject("data").get("g").getAsFloat()==0,"detached cached data");
        System.out.println("DISTANCE_INTEROP:"+rows.get(0));
        finder.base=true;require(invoke(finder,from,to)==12.5f&&from.originalDistanceQueries==1,"base original virtual Node distance exactly once");finder.base=false;
        System.out.println("DISTANCE_INTEROP:"+rows.get(1));
        finder.failure=new IllegalStateException("ORIGINAL_PROTECTED_FAILURE");int captured=rows.size();before=finder.calls;
        try{invoke(finder,from,to);throw new AssertionError("original failure expected");}catch(IllegalStateException error){require(error==finder.failure&&finder.calls==before+1&&rows.size()==captured,"same original exception/no observer on failure");}finder.failure=null;
        session=install(selected,Set.of("path_distance"),64,524288,1,context,()->100L,(m,r)->rows.add(r));KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        invoke(finder,from,to);require(data(rows.get(rows.size()-1)).getAsJsonObject("toIdentity").get("status").getAsString().equals("NOT_EXPOSED"),"shared reference cap excludes coordinate fallback");
        finder.result=Float.NaN;invoke(finder,null,null);var unknown=rows.get(rows.size()-1);
        require(data(unknown).get("returnedDistanceStatus").getAsString().equals("NOT_EXPOSED")&&data(unknown).getAsJsonObject("fromIdentity").get("detail").getAsString().equals("NULL_NODE"),"custom original null arguments/nonfinite return remain explicit");System.out.println("DISTANCE_INTEROP:"+unknown);finder.result=31.25f;
        captured=rows.size();before=finder.calls;Thread thread=new Thread(()->{try{require(invoke(finder,from,to)==31.25f,"thread primitive preserved");}catch(Exception error){throw new AssertionError(error);}});thread.start();thread.join();require(finder.calls==before+1&&rows.size()==captured,"foreign thread preserves original dispatch and excludes capture");
        for(String legacy: new String[]{"path","frontier","neighbors","path_nodes","path_g"}){
            install(selected,Set.of(legacy),64,524288,2,context,()->100L,(m,r)->{throw new AssertionError("LEGACY_DISTANCE_CAPTURE");});KneekuraDebugDecisionHooks.pathBegin(finder,selected);before=finder.calls;
            require(invoke(finder,from,to)==31.25f&&finder.calls==before+1,"legacy channel leaves original dispatch intact");
        }
        for(String fence:new String[]{"ARENA","WINDOW","EVENT","BYTE","WRITER","END","REUSE"}){
            context.set(initial);rows.clear();long[] tick={100};session=install(selected,Set.of("path_distance"),fence.equals("EVENT")?1:64,fence.equals("BYTE")?1:524288,2,context,()->tick[0],(m,r)->{if(fence.equals("WRITER"))throw new java.io.IOException("writer fixture");rows.add(r);});KneekuraDebugDecisionHooks.pathBegin(finder,selected);
            if(fence.equals("ARENA"))context.set(new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,3,1,selected.getUUID().toString(),"minecraft:overworld"));
            if(fence.equals("WINDOW"))tick[0]=110;if(fence.equals("END"))KneekuraDebugDecisionHooks.pathEnd(finder);if(fence.equals("REUSE"))KneekuraDebugDecisionHooks.pathBegin(finder,null);
            before=finder.calls;require(invoke(finder,from,to)==31.25f&&finder.calls==before+1,"original before "+fence);
            if(fence.equals("EVENT")){before=finder.calls;require(invoke(finder,from,to)==31.25f&&finder.calls==before+1&&rows.size()==1,"event cap still original once");}
            else require(rows.isEmpty(),"no capture after "+fence);
            require(((java.util.Map<?,?>)KneekuraDebugDecisionSnapshot.read(KneekuraDebugDecisionHooks.Session.class,"heapNodes",session)).isEmpty(),"references released at "+fence);
        }
        context.set(initial);rows.clear();session=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),new KneekuraDebugDecisionBurstBudget(initial,100,10,64,524288),2,Set.of("path_distance"),()->{from.g=99;return initial;},()->100L,(m,r)->rows.add(r));KneekuraDebugDecisionHooks.install(session);KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        require(invoke(finder,from,to)==31.25f&&data(rows.get(0)).getAsJsonObject("fromNode").getAsJsonObject("data").get("g").getAsFloat()==99,"original result and later gate-modified cache stay distinct");System.out.println("DISTANCE_INTEROP:"+rows.get(0));
        require(KneekuraDebugDecisionSnapshot.read(KneekuraDebugDecisionHooks.Session.class,"pendingPops",session)==null,"distance-only allocates no pop holder");
        KneekuraDebugDecisionHooks.clear("STOP");require(((java.util.Map<?,?>)KneekuraDebugDecisionSnapshot.read(KneekuraDebugDecisionHooks.Session.class,"heapNodes",session)).isEmpty(),"clear releases shared references");handlerBytecode();
        System.out.println("Original protected edge-distance: actual compiled Shadow handler single override/base call, bits/exception, detached return/cache/IDs, OFF/thread/search/context/cap/writer and bytecode checks passed; not transformed native acceptance");
    }
}
