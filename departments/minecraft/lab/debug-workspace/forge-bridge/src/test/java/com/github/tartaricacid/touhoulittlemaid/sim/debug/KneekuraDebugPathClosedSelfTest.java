package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.BinaryHeap;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import java.util.ArrayList;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

/** Genuine mapped original pop and manual caller field write; not native Mixin acceptance. */
public final class KneekuraDebugPathClosedSelfTest {
    private static final class Subject extends Mob {private Subject(){super(null,null);}}
    private static final class Heap extends BinaryHeap {
        Node result;int calls;RuntimeException failure;
        @Override public Node pop(){calls++;if(failure!=null)throw failure;return result;}
        @Override public Node peek(){throw new AssertionError("OBSERVER_MUST_NOT_QUERY_HEAP");}
        @Override public int size(){throw new AssertionError("OBSERVER_MUST_NOT_QUERY_HEAP");}
        @Override public boolean isEmpty(){throw new AssertionError("OBSERVER_MUST_NOT_QUERY_HEAP");}
    }
    private static void require(boolean b,String message){if(!b)throw new AssertionError(message);}
    private static JsonObject data(JsonObject r){return r.getAsJsonObject("data");}
    private static KneekuraDebugDecisionHooks.Session install(Subject subject,Set<String> channels,int events,int nodes,
            AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,KneekuraDebugDecisionHooks.Sink sink)throws Exception {
        var s=new KneekuraDebugDecisionHooks.Session(subject,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context.get(),100,10,events,524288),nodes,channels,context::get,()->100L,sink);
        KneekuraDebugDecisionHooks.install(s);return s;
    }
    private static Node pop(PathFinder finder,Heap heap){return KneekuraDebugDecisionHooks.originalHeapPop(finder,heap);}
    private static void close(PathFinder finder,Node returned){returned.closed=true;KneekuraDebugDecisionHooks.pathClosedWrite(finder);}
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);
        var unsafe=(sun.misc.Unsafe)field.get(null);var selected=(Subject)unsafe.allocateInstance(Subject.class);selected.setUUID(new UUID(0,1));
        var excluded=(Subject)unsafe.allocateInstance(Subject.class);excluded.setUUID(new UUID(0,2));
        var initial=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,2,1,selected.getUUID().toString(),"minecraft:overworld");
        var context=new AtomicReference<>(initial);var rows=new ArrayList<JsonObject>();var heap=new Heap();
        var finder=new PathFinder(new WalkNodeEvaluator(),32);var otherFinder=new PathFinder(new WalkNodeEvaluator(),32);
        var heapField=PathFinder.class.getDeclaredField("openSet");heapField.setAccessible(true);heapField.set(finder,heap);
        var session=install(selected,Set.of("frontier"),64,1,context,(method,r)->rows.add(r));
        heap.result=new Node(0,64,0);Node returned=pop(finder,heap);close(finder,returned);
        require(rows.isEmpty()&&heap.calls==1,"unregistered original call/write unchanged");
        heap.result=new Node(0,64,0);heap.result.g=5;KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        returned=pop(finder,heap);require(returned==heap.result&&heap.calls==2&&rows.size()==1,"single original return");
        Thread thread=new Thread(()->KneekuraDebugDecisionHooks.pathClosedWrite(finder));thread.start();thread.join();
        KneekuraDebugDecisionHooks.pathClosedWrite(otherFinder);require(rows.size()==1,"other thread/finder cannot consume marker");
        close(finder,returned);KneekuraDebugDecisionHooks.pathClosedWrite(finder);
        require(rows.size()==2&&heap.calls==2,"one checkpoint, no heap queries or replay");
        require(rows.get(1).get("semantics").getAsString().equals("ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY"),"distinct semantics");
        require(data(rows.get(1)).get("priorPopEventIndex").getAsInt()==1,"explicit actual producer index");
        require(data(rows.get(0)).getAsJsonObject("nodeIdentity").equals(data(rows.get(1)).getAsJsonObject("nodeIdentity")),"same actual reference identity");
        require(!data(rows.get(0)).getAsJsonObject("node").getAsJsonObject("data").get("closedAtReturn").getAsBoolean(),"pop before write detached");
        returned.closed=false;returned.g=99;
        require(data(rows.get(1)).getAsJsonObject("node").getAsJsonObject("data").get("closedAtCheckpoint").getAsBoolean()&&
            data(rows.get(1)).getAsJsonObject("node").getAsJsonObject("data").get("g").getAsInt()==5,"checkpoint detached");
        heap.result=new Node(0,64,0);returned=pop(finder,heap);close(finder,returned);
        require(rows.size()==4&&data(rows.get(3)).getAsJsonObject("nodeIdentity").get("detail").getAsString().equals("NODE_IDENTITY_LIMIT"),"same coordinates never merged after identity cap");
        returned=pop(finder,heap);heap.failure=new IllegalArgumentException("ORIGINAL_FAILURE");
        try{pop(finder,heap);throw new AssertionError("lost original exception");}catch(IllegalArgumentException expected){require(expected==heap.failure,"same original exception");}
        heap.failure=null;KneekuraDebugDecisionHooks.pathClosedWrite(finder);require(rows.size()==5,"failed next pop clears previous marker");
        pop(finder,heap);KneekuraDebugDecisionHooks.pathEnd(finder);KneekuraDebugDecisionHooks.pathClosedWrite(finder);require(rows.size()==6,"end clears marker");
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);pop(finder,heap);KneekuraDebugDecisionHooks.pathBegin(finder,excluded);
        KneekuraDebugDecisionHooks.pathClosedWrite(finder);require(rows.size()==7,"excluded subject clears marker");
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);heap.result=null;require(pop(finder,heap)==null,"original null unchanged");
        KneekuraDebugDecisionHooks.pathClosedWrite(finder);require(rows.size()==8,"null pop cannot supply field-write reference");
        heap.result=new Node(1,64,0);returned=pop(finder,heap);KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        KneekuraDebugDecisionHooks.pathClosedWrite(finder);require(rows.size()==9,"next search clears old marker");
        var checks=new ArrayList<JsonObject>();session=install(selected,Set.of("frontier"),1,1,context,(m,r)->checks.add(r));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);returned=pop(finder,heap);close(finder,returned);require(checks.size()==1&&returned.closed,"event budget preserves original write");
        checks.clear();session=install(selected,Set.of("path","neighbors"),64,1,context,(m,r)->checks.add(r));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);returned=pop(finder,heap);close(finder,returned);require(checks.isEmpty()&&session.budget().events()==0,"legacy channels unchanged");
        var pendingField=KneekuraDebugDecisionHooks.Session.class.getDeclaredField("pendingPops");pendingField.setAccessible(true);
        require(pendingField.get(session)==null,"legacy mode allocates no pending reference map");
        for(String boundary:new String[]{"CONTEXT","WINDOW","BYTES","WRITER","CLEAR","REARM"}) {
            checks.clear();var tick=new java.util.concurrent.atomic.AtomicLong(100);var failContext=new java.util.concurrent.atomic.AtomicBoolean();
            var guard=new KneekuraDebugDecisionBurstBudget(initial,100,10,64,524288);
            session=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),guard,1,Set.of("frontier"),
                ()->{if(failContext.get())throw new IllegalStateException("CONTEXT");return context.get();},tick::get,
                (m,r)->{if(boundary.equals("WRITER")&&r.get("kind").getAsString().equals("PATH_NODE_CLOSED_CHECKPOINT"))throw new java.io.IOException("WRITER");checks.add(r);});
            KneekuraDebugDecisionHooks.install(session);KneekuraDebugDecisionHooks.pathBegin(finder,selected);returned=pop(finder,heap);
            require(((java.util.Map<?,?>)pendingField.get(session)).size()==1,"one pending reference per finder");
            if(boundary.equals("CONTEXT"))failContext.set(true);
            if(boundary.equals("WINDOW"))tick.set(110);
            if(boundary.equals("BYTES"))while(guard.bytes()<524288)
                require(guard.claim(initial,100,Math.min(32768,524288-guard.bytes())),"byte budget fixture reservations");
            if(boundary.equals("CLEAR"))KneekuraDebugDecisionHooks.clear("TEST_CLEAR");
            if(boundary.equals("REARM"))install(selected,Set.of("frontier"),64,1,context,(m,r)->checks.add(r));
            close(finder,returned);require(checks.size()==1&&returned.closed,"boundary cannot invent checkpoint: "+boundary);
            require(((java.util.Map<?,?>)pendingField.get(session)).isEmpty(),"boundary releases reference: "+boundary);
            if(boundary.equals("BYTES"))require(guard.reason().equals("BYTE_BUDGET"),"actual byte exhaustion boundary");
        }
        checks.clear();session=install(selected,Set.of("frontier"),64,1,context,(m,r)->checks.add(r));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);pop(finder,heap);
        context.set(new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,3,1,selected.getUUID().toString(),"minecraft:overworld"));
        close(finder,heap.result);require(checks.size()==1&&((java.util.Map<?,?>)pendingField.get(session)).isEmpty(),"changed Arena releases pending reference");
        context.set(initial);checks.clear();session=install(selected,Set.of("frontier"),64,1,context,(m,r)->checks.add(r));
        var finders=new PathFinder[9];var nodes=new Node[9];
        for(int i=0;i<9;i++) {
            finders[i]=new PathFinder(new WalkNodeEvaluator(),32);heapField.set(finders[i],heap);nodes[i]=new Node(i,64,0);heap.result=nodes[i];
            KneekuraDebugDecisionHooks.pathBegin(finders[i],selected);pop(finders[i],heap);
        }
        require(checks.size()==8&&((java.util.Map<?,?>)pendingField.get(session)).size()==8,"at most eight registered finder markers");
        for(int i=0;i<9;i++)close(finders[i],nodes[i]);
        require(checks.size()==16&&((java.util.Map<?,?>)pendingField.get(session)).isEmpty(),"only registered original references consumed");
        session=install(selected,Set.of("frontier"),64,1,context,(m,r)->{throw new java.io.IOException("FAILED_POP_WRITER");});
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);pop(finder,heap);
        require(((java.util.Map<?,?>)pendingField.get(session)).isEmpty()&&session.budget().reason().equals("WRITER_UNAVAILABLE"),"failed pop writer releases pending reference");
        KneekuraDebugDecisionHooks.clear("DONE");close(finder,heap.result);require(checks.size()==16,"OFF does not acquire");
        for(int index:new int[]{1,3})System.out.println("CLOSED_INTEROP:"+rows.get(index));
        System.out.println("Closed checkpoint producer: one original pop/write, actual reference, detached phase, capped/one-shot/exception/thread/context/channel/writer fences");
    }
}
