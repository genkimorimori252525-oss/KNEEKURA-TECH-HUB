package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import java.util.ArrayList;
import java.util.Set;
import java.util.UUID;

/** Genuine mapped API, synthetic custom override behavior; native callsites require a separate trial. */
public final class KneekuraDebugEffectiveMalusSelfTest {
    private static final class Subject extends Mob {
        int calls;float returned=17.25F;boolean fail;
        private Subject(){super(null,null);}
        @Override public float getPathfindingMalus(BlockPathTypes type){calls++;if(fail)throw new IllegalArgumentException("ORIGINAL_MALUS_FAILURE");return returned;}
    }
    private static Subject subject(long id)throws Exception {
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);
        Subject subject=(Subject)((sun.misc.Unsafe)field.get(null)).allocateInstance(Subject.class);
        subject.setUUID(new UUID(0,id));subject.returned=17.25F;return subject;
    }
    private static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var selected=subject(1);var other=subject(2);var evaluator=new WalkNodeEvaluator();var rows=new ArrayList<JsonObject>();
        var context=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,2,1,selected.getUUID().toString(),"minecraft:overworld");
        var session=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,3,65536),8,Set.of("effective_malus"),()->context,()->100L,(method,row)->rows.add(row));
        KneekuraDebugDecisionHooks.install(session);
        require(KneekuraDebugDecisionHooks.originalMalus(evaluator,selected,BlockPathTypes.WATER)==17.25F,"original custom getter value retained");
        require(selected.calls==1&&rows.size()==1,"custom getter called once, no base-table replay");
        require(rows.get(0).getAsJsonObject("data").get("returnedMalus").getAsFloat()==17.25F,"actual original result observed");
        KneekuraDebugDecisionHooks.originalMalus(evaluator,other,BlockPathTypes.WATER);
        require(other.calls==1&&rows.size()==1,"other receiver still called but excluded");
        Thread worker=new Thread(()->KneekuraDebugDecisionHooks.originalMalus(evaluator,selected,BlockPathTypes.WATER));worker.start();worker.join();
        require(selected.calls==2&&rows.size()==1,"other thread preserves original call without observation");
        selected.fail=true;
        try{KneekuraDebugDecisionHooks.originalMalus(evaluator,selected,BlockPathTypes.WATER);throw new AssertionError("original exception lost");}
        catch(IllegalArgumentException expected){require(expected.getMessage().equals("ORIGINAL_MALUS_FAILURE"),"original exception preserved");}
        require(selected.calls==3&&rows.size()==1,"no invented return after original failure");selected.fail=false;selected.returned=Float.NaN;
        require(Float.isNaN(KneekuraDebugDecisionHooks.originalMalus(evaluator,selected,BlockPathTypes.WATER)),"non-finite original value not coerced");
        require(!rows.get(1).getAsJsonObject("data").has("returnedMalus")&&rows.get(1).getAsJsonObject("data").get("returnedMalusStatus").getAsString().equals("NOT_EXPOSED"),"JSON unknown status explicit");
        selected.returned=-2;KneekuraDebugDecisionHooks.originalMalus(evaluator,selected,BlockPathTypes.WATER);
        KneekuraDebugDecisionHooks.originalMalus(evaluator,selected,BlockPathTypes.WATER);
        require(rows.size()==3&&selected.calls==6,"finite budget preserves later original invocations");
        KneekuraDebugDecisionHooks.clear("TEST_DONE");KneekuraDebugDecisionHooks.originalMalus(evaluator,selected,BlockPathTypes.WATER);
        require(rows.size()==3&&selected.calls==7,"OFF preserves gameplay only");
        var current=new java.util.concurrent.atomic.AtomicReference<>(context);
        var tick=new java.util.concurrent.atomic.AtomicLong(100L);
        for(String boundary:new String[]{"BASE_ONLY","CONTEXT","WINDOW","UUID"}) {
            var guard=new KneekuraDebugDecisionBurstBudget(context,100,10,3,65536);
            current.set(context);tick.set(100L);
            var bounded=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
                guard,8,Set.of(boundary.equals("BASE_ONLY")?"malus":"effective_malus"),current::get,tick::get,(method,row)->rows.add(row));
            KneekuraDebugDecisionHooks.install(bounded);
            if(boundary.equals("CONTEXT"))current.set(new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,3,1,context.subjectUuid(),"minecraft:overworld"));
            if(boundary.equals("WINDOW"))tick.set(110L);
            if(boundary.equals("UUID"))selected.setUUID(new UUID(0,3));
            int before=selected.calls;
            require(KneekuraDebugDecisionHooks.originalMalus(evaluator,selected,BlockPathTypes.WATER)==-2F,"boundary preserves original return");
            require(selected.calls==before+1&&rows.size()==3,"boundary suppresses capture, not original dispatch: "+boundary);
            if(boundary.equals("CONTEXT"))require("CONTEXT_CHANGED".equals(guard.reason()),"Arena change closes old context");
            if(boundary.equals("WINDOW"))require("WINDOW_ENDED".equals(guard.reason()),"exclusive tick bound closes capture");
            if(boundary.equals("UUID"))require(guard.reason().startsWith("CAPTURE_UNAVAILABLE:"),"changed cached UUID closes capture");
            KneekuraDebugDecisionHooks.clear("TEST_BOUNDARY_DONE");selected.setUUID(new UUID(0,1));
        }
        System.out.println("MALUS_INTEROP:"+rows.get(0));
        System.out.println("Original effective malus: custom single dispatch, value/exception/NaN preserved, owner/thread/OFF/event/channel/context/window/UUID bounds, no getter replay");
    }
}
