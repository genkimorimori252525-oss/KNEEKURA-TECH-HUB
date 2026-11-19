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

/** Genuine mapped heap dispatch with custom returns; not native Mixin acceptance. */
public final class KneekuraDebugPathHeapSelfTest {
    private static final class Subject extends Mob {private Subject(){super(null,null);}}
    private static final class CountingHeap extends BinaryHeap {
        int inserts,pops,changes;Node replacement;boolean nullPop;
        RuntimeException failure;
        @Override public Node insert(Node node) {
            inserts++;if(failure!=null)throw failure;return super.insert(replacement==null?node:replacement);
        }
        @Override public Node pop() {
            pops++;if(failure!=null)throw failure;return nullPop?null:super.pop();
        }
        @Override public void changeCost(Node node,float cost) {
            changes++;if(failure!=null)throw failure;super.changeCost(node,cost);
        }
    }
    private static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static JsonObject data(JsonObject row){return row.getAsJsonObject("data");}
    private static String id(JsonObject row){return data(row).getAsJsonObject("nodeIdentity").get("id").getAsString();}
    private static KneekuraDebugDecisionHooks.Session install(Subject subject,Set<String> channels,int events,int nodes,
            AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,KneekuraDebugDecisionHooks.Sink sink)throws Exception {
        var session=new KneekuraDebugDecisionHooks.Session(subject,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context.get(),100,10,events,524288),nodes,channels,context::get,()->100L,sink);
        KneekuraDebugDecisionHooks.install(session);return session;
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var unsafeField=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");unsafeField.setAccessible(true);
        var unsafe=(sun.misc.Unsafe)unsafeField.get(null);
        Subject selected=(Subject)unsafe.allocateInstance(Subject.class);selected.setUUID(new UUID(0,1));
        Subject excluded=(Subject)unsafe.allocateInstance(Subject.class);excluded.setUUID(new UUID(0,2));
        var initial=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,2,1,selected.getUUID().toString(),"minecraft:overworld");
        var context=new AtomicReference<>(initial);var rows=new ArrayList<JsonObject>();
        var heap=new CountingHeap();var finder=new PathFinder(new WalkNodeEvaluator(),32);
        var heapField=PathFinder.class.getDeclaredField("openSet");heapField.setAccessible(true);heapField.set(finder,heap);
        var session=install(selected,Set.of("frontier"),64,2,context,(method,row)->rows.add(row));
        Node first=new Node(0,64,0),second=new Node(0,64,0),third=new Node(1,64,0);first.f=8;first.g=5;second.f=10;
        require(KneekuraDebugDecisionHooks.originalHeapInsert(finder,heap,first,true)==first,"original insert reference");
        require(heap.inserts==1&&rows.isEmpty(),"unregistered search preserves one invocation");heap.pop();
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        require(KneekuraDebugDecisionHooks.originalHeapInsert(finder,heap,first,true)==first,"selected original reference");
        KneekuraDebugDecisionHooks.originalHeapInsert(finder,heap,second,false);
        KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,second,7);
        require(KneekuraDebugDecisionHooks.originalHeapPop(finder,heap)==second,"pop preserves actual object");
        require(heap.inserts==3&&heap.changes==1&&heap.pops==2&&rows.size()==4,"single original virtual dispatch per wrapper");
        require(!id(rows.get(0)).equals(id(rows.get(1)))&&id(rows.get(1)).equals(id(rows.get(2)))&&id(rows.get(2)).equals(id(rows.get(3))),"reference identity, never coordinate identity");
        require(data(rows.get(2)).get("requestedCost").getAsFloat()==7&&data(rows.get(2)).getAsJsonObject("node").getAsJsonObject("data").get("f").getAsFloat()==7,"requested and actual cost retained");
        require(!data(rows.get(3)).getAsJsonObject("node").getAsJsonObject("data").get("closedAtReturn").getAsBoolean(),"pop recorded before caller closes node");
        second.closed=true;first.g=99;
        require(!data(rows.get(3)).getAsJsonObject("node").getAsJsonObject("data").get("closedAtReturn").getAsBoolean()&&data(rows.get(0)).getAsJsonObject("node").getAsJsonObject("data").get("g").getAsFloat()==5,"return state detached");
        KneekuraDebugDecisionHooks.originalHeapInsert(finder,heap,third,false);
        require(data(rows.get(4)).getAsJsonObject("nodeIdentity").get("detail").getAsString().equals("NODE_IDENTITY_LIMIT"),"bounded identity retention");
        heap.failure=new IllegalArgumentException("ORIGINAL_HEAP_FAILURE");
        for(int operation=0;operation<3;operation++) {
            try {
                if(operation==0)KneekuraDebugDecisionHooks.originalHeapInsert(finder,heap,new Node(2,64,0),false);
                else if(operation==1)KneekuraDebugDecisionHooks.originalHeapPop(finder,heap);
                else KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,6);
                throw new AssertionError("original exception lost");
            }catch(IllegalArgumentException expected){require(expected==heap.failure,"original exception object preserved");}
        }
        require(heap.inserts==5&&heap.pops==3&&heap.changes==2&&rows.size()==5,"failed original calls do not invent returns");heap.failure=null;
        KneekuraDebugDecisionHooks.pathEnd(finder);
        KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,6);require(rows.size()==5,"ended search excluded");
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,5);
        require(id(rows.get(5)).equals("search:1:2:node:1"),"next search gets a new bounded table");
        KneekuraDebugDecisionHooks.pathBegin(finder,excluded);
        KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,4);require(rows.size()==6,"excluded Mob clears interrupted search");
        var more=new ArrayList<JsonObject>();install(selected,Set.of("frontier"),64,2,context,(method,row)->more.add(row));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);heap.replacement=new Node(3,64,0);
        require(KneekuraDebugDecisionHooks.originalHeapInsert(finder,heap,new Node(4,64,0),false)==heap.replacement,"custom returned object preserved");
        require(!data(more.get(0)).get("argumentMatchesReturned").getAsBoolean(),"argument and return identities remain distinct");heap.replacement=null;
        heap.nullPop=true;require(KneekuraDebugDecisionHooks.originalHeapPop(finder,heap)==null,"custom null return preserved");
        require(data(more.get(1)).getAsJsonObject("nodeIdentity").get("detail").getAsString().equals("NULL_NODE"),"null remains unobserved identity");heap.nullPop=false;
        Thread other=new Thread(()->KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,3));other.start();other.join();
        require(more.size()==2,"other thread does not record");
        context.set(new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,3,1,selected.getUUID().toString(),"minecraft:overworld"));
        KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,2);require(more.size()==2,"changed Arena excluded");context.set(initial);
        var excludedRows=new ArrayList<JsonObject>();session=install(selected,Set.of("path","neighbors"),64,2,context,(method,row)->excludedRows.add(row));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,1);
        require(excludedRows.isEmpty()&&session.budget().events()==0,"legacy channels do not acquire heap records");
        var bounded=new ArrayList<JsonObject>();session=install(selected,Set.of("frontier"),1,2,context,(method,row)->bounded.add(row));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,1);KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,0);
        require(bounded.size()==1&&first.f==0,"full event budget preserves gameplay call");
        session=install(selected,Set.of("frontier"),64,2,context,(method,row)->{throw new java.io.IOException("TEST_SINK");});
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,-1);
        require(first.f==-1,"writer failure cannot replace original result");
        for(String boundary:new String[]{"BYTE_BUDGET","WINDOW_ENDED","CONTEXT_UNAVAILABLE"}) {
            var tick=new java.util.concurrent.atomic.AtomicLong(100);var failContext=new java.util.concurrent.atomic.AtomicBoolean();
            var guard=new KneekuraDebugDecisionBurstBudget(initial,100,10,64,boundary.equals("BYTE_BUDGET")?1:524288);
            session=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),guard,2,Set.of("frontier"),
                ()->{if(failContext.get())throw new IllegalStateException("TEST_CONTEXT");return initial;},tick::get,(method,row)->excludedRows.add(row));
            KneekuraDebugDecisionHooks.install(session);KneekuraDebugDecisionHooks.pathBegin(finder,selected);
            if(boundary.equals("WINDOW_ENDED"))tick.set(110);
            if(boundary.equals("CONTEXT_UNAVAILABLE"))failContext.set(true);
            int calls=heap.changes;KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,-3);
            require(heap.changes==calls+1&&first.f==-3&&excludedRows.isEmpty()&&guard.reason()!=null,"boundary preserves one original call: "+boundary);
            if(!boundary.equals("CONTEXT_UNAVAILABLE"))require(guard.reason().equals(boundary),"exact bounded stop reason");
        }
        session=install(selected,Set.of("frontier"),64,2,context,(method,row)->excludedRows.add(row));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);var wrongHeap=new CountingHeap();var wrongNode=new Node(8,64,0);
        require(KneekuraDebugDecisionHooks.originalHeapInsert(finder,wrongHeap,wrongNode,true)==wrongNode&&wrongHeap.inserts==1&&excludedRows.isEmpty(),"wrong heap excluded after preserving original call");
        KneekuraDebugDecisionHooks.clear("TEST_DONE");KneekuraDebugDecisionHooks.originalHeapChangeCost(finder,heap,first,-2);
        require(first.f==-2&&rows.size()==6,"OFF preserves original without capture");
        for(JsonObject row:rows)System.out.println("HEAP_INTEROP:"+row);
        for(JsonObject row:more)System.out.println("HEAP_INTEROP:"+row);
        System.out.println("Original heap producer: single dispatch/reference/exception, detached bounded identities, OFF/thread/context/budget/writer fences");
    }
}
