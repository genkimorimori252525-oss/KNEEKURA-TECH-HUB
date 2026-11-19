package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import java.util.ArrayList;
import java.util.Set;
import java.util.UUID;

/** Genuine mapped API with a counting custom original evaluator; not native dispatch proof. */
public final class KneekuraDebugPathNeighborsSelfTest {
    private static final class Subject extends Mob {private Subject(){super(null,null);}}
    private static final class CountingEvaluator extends WalkNodeEvaluator {
        int calls;boolean fail;Node first=new Node(2,64,0),second=new Node(1,64,0);
        @Override public int getNeighbors(Node[] output,Node current) {
            calls++;if(fail)throw new IllegalArgumentException("ORIGINAL_NEIGHBOR_FAILURE");
            output[0]=first;output[1]=second;output[2]=null;return 3;
        }
    }
    private static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);
        Subject selected=(Subject)((sun.misc.Unsafe)field.get(null)).allocateInstance(Subject.class);selected.setUUID(new UUID(0,1));
        var context=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,2,1,selected.getUUID().toString(),"minecraft:overworld");
        var rows=new ArrayList<JsonObject>();var evaluator=new CountingEvaluator();var finder=new PathFinder(evaluator,32);
        var session=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,2,65536),2,Set.of("neighbors"),()->context,()->100L,(method,row)->rows.add(row));
        KneekuraDebugDecisionHooks.install(session);
        var output=new Node[32];var current=new Node(0,64,0);
        require(KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current)==3,"original return unchanged without registered search");
        require(evaluator.calls==1&&rows.isEmpty(),"unregistered finder not recorded or replayed");
        KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        require(KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current)==3,"original count preserved");
        require(evaluator.calls==2&&rows.size()==1,"exactly one original virtual invocation");
        var data=rows.get(0).getAsJsonObject("data");
        require(data.get("returnedCount").getAsInt()==3&&data.getAsJsonArray("neighbors").size()==2&&data.get("truncated").getAsBoolean(),"bounded source slots");
        evaluator.first.g=99;
        require(data.getAsJsonArray("neighbors").get(0).getAsJsonObject().getAsJsonObject("node").getAsJsonObject("data").get("g").getAsFloat()!=99,"node state detached before subsequent relaxation");
        evaluator.fail=true;
        try{KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current);throw new AssertionError("original exception lost");}
        catch(IllegalArgumentException expected){require(expected.getMessage().equals("ORIGINAL_NEIGHBOR_FAILURE"),"original exception identity retained");}
        require(evaluator.calls==3&&rows.size()==1,"failed original call has no invented return");evaluator.fail=false;
        KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current);
        KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current);
        require(evaluator.calls==5&&rows.size()==2,"full budget still preserves gameplay invocation");
        KneekuraDebugDecisionHooks.clear("TEST_DONE");
        KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current);
        require(evaluator.calls==6&&rows.size()==2,"OFF does not record or replay");
        var excludedRows=new ArrayList<JsonObject>();
        var pathOnly=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,8,65536),2,Set.of("path"),()->context,()->100L,(method,row)->excludedRows.add(row));
        KneekuraDebugDecisionHooks.install(pathOnly);KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current);
        require(evaluator.calls==7&&excludedRows.isEmpty()&&pathOnly.budget().events()==0,"legacy path channel does not acquire neighbor records");
        var enabledRows=new ArrayList<JsonObject>();
        var enabled=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,8,65536),2,Set.of("neighbors"),()->context,()->100L,(method,row)->enabledRows.add(row));
        KneekuraDebugDecisionHooks.install(enabled);KneekuraDebugDecisionHooks.pathBegin(finder,selected);
        Thread other=new Thread(()->KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current));other.start();other.join();
        require(evaluator.calls==8&&enabledRows.isEmpty(),"other thread keeps original call but emits no observation");
        KneekuraDebugDecisionHooks.pathEnd(finder);
        KneekuraDebugDecisionHooks.originalNeighbors(finder,evaluator,output,current);
        require(evaluator.calls==9&&enabledRows.isEmpty(),"ended original search not recorded");KneekuraDebugDecisionHooks.clear("TEST_DONE");
        System.out.println("NEIGHBOR_INTEROP:"+rows.get(0));
        System.out.println("Original neighbor producer: single virtual call/count/exception, detached bounded slots and no capture OFF or outside registered search");
    }
}
