package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import java.util.ArrayList;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

/** Actual mapped Path/Node fields and custom getter fences; not native RETURN acceptance. */
public final class KneekuraDebugPathNodesSelfTest {
    private static final class Subject extends Mob {private Subject(){super(null,null);}}
    private static final class GetterList extends ArrayList<Node> {
        boolean forbid;int calls;
        private void query(){calls++;if(forbid)throw new AssertionError("CUSTOM_LIST_QUERY");}
        @Override public int size(){query();return super.size();}
        @Override public boolean isEmpty(){query();return super.isEmpty();}
        @Override public Node get(int i){query();return super.get(i);}
    }
    private static final class CustomPath extends Path {
        CustomPath(ArrayList<Node> nodes){super(nodes,new BlockPos(3,64,0),true);}
        @Override public int getNodeCount(){throw new AssertionError("CUSTOM_PATH_QUERY");}
        @Override public boolean canReach(){throw new AssertionError("CUSTOM_PATH_QUERY");}
        @Override public Node getEndNode(){throw new AssertionError("CUSTOM_PATH_QUERY");}
    }
    private static final class CustomNode extends Node {
        CustomNode(){super(0,64,0);}
        @Override public float distanceManhattan(BlockPos target){throw new AssertionError("CUSTOM_NODE_QUERY");}
        @Override public boolean inOpenSet(){throw new AssertionError("CUSTOM_NODE_QUERY");}
        @Override public BlockPos asBlockPos(){throw new AssertionError("CUSTOM_NODE_QUERY");}
    }
    private static void require(boolean b,String m){if(!b)throw new AssertionError(m);}
    private static JsonObject data(JsonObject r){return r.getAsJsonObject("data");}
    private static JsonObject snapshot(JsonObject r){return data(r).getAsJsonObject("pathNodes").getAsJsonObject("data");}
    private static KneekuraDebugDecisionHooks.Session install(Subject selected,Set<String> channels,int events,int bytes,int nodes,
            AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,java.util.function.LongSupplier time,KneekuraDebugDecisionHooks.Sink sink)throws Exception {
        var s=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context.get(),100,10,events,bytes),nodes,channels,context::get,time,sink);
        KneekuraDebugDecisionHooks.install(s);return s;
    }
    private static void result(PathFinder f,Subject s,Path p){KneekuraDebugDecisionHooks.pathResult(f,s,p);}
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);var unsafe=(sun.misc.Unsafe)field.get(null);
        Subject selected=(Subject)unsafe.allocateInstance(Subject.class);selected.setUUID(new UUID(0,1));
        Subject excluded=(Subject)unsafe.allocateInstance(Subject.class);excluded.setUUID(new UUID(0,2));
        var initial=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,2,1,selected.getUUID().toString(),"minecraft:overworld");
        var context=new AtomicReference<>(initial);var rows=new ArrayList<JsonObject>();var finder=new PathFinder(new WalkNodeEvaluator(),32);
        new KneekuraDebugDecisionBurstRequest(10,64,524288,2,Set.of("path_nodes"));
        var first=new Node(0,64,0);var second=new Node(0,64,0);var terminal=new Node(2,64,0);
        second.cameFrom=first;terminal.cameFrom=second;terminal.g=20;terminal.h=1;terminal.f=21;
        var nodes=new ArrayList<Node>();nodes.add(first);nodes.add(second);nodes.add(terminal);
        Path path=new Path(nodes,new BlockPos(3,64,0),true);
        var session=install(selected,Set.of("path_nodes"),64,524288,2,context,()->100L,(m,r)->rows.add(r));
        result(finder,selected,path);require(rows.isEmpty(),"unregistered finder excluded");KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        result(finder,excluded,path);require(rows.isEmpty(),"other Mob excluded");result(finder,selected,path);
        require(rows.size()==1&&rows.get(0).get("kind").getAsString().equals("PATH_RETURNED_NODES"),"explicit returned-node channel only");
        JsonObject snap=snapshot(rows.get(0));require(snap.getAsJsonArray("nodes").size()==2&&snap.get("nodeCount").getAsInt()==3&&snap.get("truncated").getAsBoolean(),"bounded prefix declares actual count");
        require(snap.getAsJsonObject("terminalNode").getAsJsonObject("data").get("index").getAsInt()==2,"terminal outside prefix remains a separate slot");
        require(snap.getAsJsonObject("terminalNode").getAsJsonObject("data").getAsJsonObject("node").getAsJsonObject("data").get("g").getAsFloat()==20&&snap.get("distanceToTarget").getAsFloat()==1,"cached g is distinct from constructor distance");
        var a=snap.getAsJsonArray("nodes").get(0).getAsJsonObject();var b=snap.getAsJsonArray("nodes").get(1).getAsJsonObject();
        require(!a.getAsJsonObject("nodeIdentity").equals(b.getAsJsonObject("nodeIdentity"))&&a.getAsJsonObject("nodeIdentity").equals(b.getAsJsonObject("predecessorIdentity")),"same coordinates are distinct references; real predecessor retained");
        terminal.g=99;second.cameFrom=null;nodes.clear();require(snap.getAsJsonObject("terminalNode").getAsJsonObject("data").getAsJsonObject("node").getAsJsonObject("data").get("g").getAsFloat()==20&&snap.getAsJsonArray("nodes").size()==2,"snapshot detached from actual returned list/Node");
        result(finder,selected,path);require(snapshot(rows.get(1)).getAsJsonObject("terminalNode").get("detail").getAsString().equals("EMPTY_PATH"),"empty actual list preserves cached constructor distance");
        result(finder,selected,null);require(data(rows.get(2)).getAsJsonObject("pathNodes").get("detail").getAsString().equals("NULL_PATH"),"null actual return unavailable");
        var customList=new GetterList();customList.add(new Node(0,64,0));Path customListPath=new Path(customList,new BlockPos(3,64,0),false);customList.calls=0;customList.forbid=true;
        result(finder,selected,customListPath);require(customList.calls==0&&data(rows.get(3)).getAsJsonObject("pathNodes").get("detail").getAsString().equals("CUSTOM_NODE_LIST"),"custom list receives no observational dispatch");
        var customPath=new CustomPath(new ArrayList<>());result(finder,selected,customPath);
        require(data(rows.get(4)).getAsJsonObject("pathNodes").get("detail").getAsString().equals("CUSTOM_PATH_CLASS"),"custom Path receives no getter replay");
        var exoticNodes=new ArrayList<Node>();exoticNodes.add(first);exoticNodes.add(null);exoticNodes.add(terminal);
        Path exotic=new Path(exoticNodes,new BlockPos(3,64,0),false);exoticNodes.set(0,new CustomNode());terminal.g=Float.NaN;
        session=install(selected,Set.of("path_nodes"),64,524288,3,context,()->100L,(m,r)->rows.add(r));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);result(finder,selected,exotic);
        JsonObject exoticSnap=snapshot(rows.get(5));
        require(exoticSnap.getAsJsonArray("nodes").get(1).getAsJsonObject().getAsJsonObject("node").get("detail").getAsString().equals("NULL_NODE"),"actual interior null retains its list slot");
        require(exoticSnap.getAsJsonObject("terminalNode").getAsJsonObject("data").equals(exoticSnap.getAsJsonArray("nodes").get(2)),"inside-prefix terminal copies exact already-read slot");
        require(exoticSnap.getAsJsonObject("terminalNode").getAsJsonObject("data").getAsJsonObject("node").getAsJsonObject("data").get("gStatus").getAsString().equals("NOT_EXPOSED"),"NaN cached g remains unknown, never coerced to a cost");
        var interop=new ArrayList<>(rows);
        var pendingField=KneekuraDebugDecisionHooks.Session.class.getDeclaredField("pendingPops");pendingField.setAccessible(true);
        require(pendingField.get(session)==null,"path_nodes alone allocates no pop marker map");
        var identities=KneekuraDebugDecisionHooks.Session.class.getDeclaredField("heapNodes");identities.setAccessible(true);
        require(((java.util.Map<?,?>)((java.util.Map<?,?>)identities.get(session)).get(finder)).size()<=3,"shared reference identity table bounded");
        var quiet=new ArrayList<JsonObject>();session=install(selected,Set.of("path"),64,524288,2,context,()->100L,(m,r)->quiet.add(r));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);result(finder,selected,customListPath);
        require(customList.calls==0&&quiet.size()==1&&data(quiet.get(0)).get("resultNodeCountStatus").getAsString().equals("NOT_EXPOSED"),"legacy summary no longer calls an arbitrary custom List");
        require(identities.get(session)==null,"legacy path alone allocates no Node identity table");
        quiet.clear();session=install(selected,Set.of("frontier"),64,524288,2,context,()->100L,(m,r)->quiet.add(r));
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);result(finder,selected,path);require(quiet.isEmpty(),"frontier alone does not acquire new returned-node records");
        for(String boundary:new String[]{"THREAD","ARENA","WINDOW","EVENT","BYTE","WRITER","END","REBEGIN"}) {
            quiet.clear();var tick=new java.util.concurrent.atomic.AtomicLong(100);
            session=install(selected,Set.of("path_nodes"),boundary.equals("EVENT")?1:64,boundary.equals("BYTE")?1:524288,2,context,tick::get,
                (m,r)->{if(boundary.equals("WRITER"))throw new java.io.IOException("TEST_WRITER");quiet.add(r);});
            KneekuraDebugDecisionHooks.pathBegin(finder,selected);
            if(boundary.equals("THREAD")){Thread t=new Thread(()->result(finder,selected,path));t.start();t.join();}
            if(boundary.equals("ARENA"))context.set(new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,3,1,selected.getUUID().toString(),"minecraft:overworld"));
            if(boundary.equals("WINDOW"))tick.set(110);
            if(boundary.equals("EVENT"))result(finder,selected,path);
            if(boundary.equals("END"))KneekuraDebugDecisionHooks.pathEnd(finder);
            if(boundary.equals("REBEGIN"))KneekuraDebugDecisionHooks.pathBegin(finder,excluded);
            if(!boundary.equals("THREAD"))result(finder,selected,path);
            require(quiet.size()==(boundary.equals("EVENT")?1:0),"capture gate: "+boundary);
            require(((java.util.Map<?,?>)identities.get(session)).size()==(boundary.equals("THREAD")?1:0),"wrong thread preserves owning session; other stop boundaries release finder/Node references: "+boundary);
            if(boundary.equals("ARENA"))require("CONTEXT_CHANGED".equals(session.budget().reason()),"exact Arena change reason");
            if(boundary.equals("WINDOW"))require("WINDOW_ENDED".equals(session.budget().reason()),"exact window reason");
            if(boundary.equals("EVENT"))require("EVENT_BUDGET".equals(session.budget().reason()),"exact event reason");
            if(boundary.equals("BYTE"))require("BYTE_BUDGET".equals(session.budget().reason()),"exact byte reason");
            if(boundary.equals("WRITER"))require("WRITER_UNAVAILABLE".equals(session.budget().reason()),"exact writer reason");
            context.set(initial);
        }
        session=install(selected,Set.of("path_nodes"),64,524288,64,context,()->100L,(m,r)->quiet.add(r));quiet.clear();
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);var large=new ArrayList<Node>();
        for(int i=0;i<80;i++){Node n=new Node(i,64,0);if(i>0)n.cameFrom=large.get(i-1);n.g=i;large.add(n);}
        var largePath=new Path(large,new BlockPos(81,64,0),false);result(finder,selected,largePath);
        require(quiet.size()==1&&snapshot(quiet.get(0)).getAsJsonArray("nodes").size()==64&&snapshot(quiet.get(0)).getAsJsonObject("terminalNode").getAsJsonObject("data").get("index").getAsInt()==79,"maximum64 prefix and separate terminal stay within real event byte limit");
        interop.add(quiet.get(0));KneekuraDebugDecisionHooks.clear("DONE");result(finder,selected,path);require(quiet.size()==1,"OFF never acquires");
        require(((java.util.Map<?,?>)identities.get(session)).isEmpty(),"OFF releases all retained reference tables");
        session=install(selected,Set.of("path_nodes"),64,524288,2,context,()->100L,(m,r)->quiet.add(r));quiet.clear();
        for(int i=0;i<9;i++){var f=new PathFinder(new WalkNodeEvaluator(),32);KneekuraDebugDecisionHooks.pathBegin(f,selected);result(f,selected,path);}
        require(quiet.size()==8&&((java.util.Map<?,?>)identities.get(session)).size()==8,"at most eight interrupted finders retained");
        KneekuraDebugDecisionHooks.clear("DONE");
        for(var r:interop)System.out.println("PATH_NODES_INTEROP:"+r);
        System.out.println("Original returned Path: bounded detached prefix/terminal/cached cost/predecessor, custom List/Path no queries, OFF/legacy/context/caps/writer fences");
    }
}
