package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Ghast;
import net.minecraft.world.entity.ai.control.MoveControl;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;
import java.util.Set;
import java.util.UUID;

/** Genuine mapped APIs with synthetic callback arguments; actual Mixin firing is a separate native proof. */
public final class KneekuraDebugGhastReachSelfTest {
    private static Ghast subject(long id)throws Exception {
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);
        Ghast ghast=(Ghast)((sun.misc.Unsafe)field.get(null)).allocateInstance(Ghast.class);
        ghast.setUUID(new UUID(0,id));
        var constructor=Class.forName("net.minecraft.world.entity.monster.Ghast$GhastMoveControl").getDeclaredConstructor(Ghast.class);
        constructor.setAccessible(true);var move=Mob.class.getDeclaredField("moveControl");move.setAccessible(true);
        move.set(ghast,constructor.newInstance(ghast));return ghast;
    }
    private static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var selected=subject(1);var other=subject(2);var controller=selected.getMoveControl();
        var rows=new ArrayList<JsonObject>();var direction=new Vec3(0,0.6,0.8);
        var context=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,2,1,selected.getUUID().toString(),"minecraft:overworld");
        var current=new java.util.concurrent.atomic.AtomicReference<>(context);var tick=new java.util.concurrent.atomic.AtomicLong(100);
        var budget=new KneekuraDebugDecisionBurstBudget(context,100,10,2,65536);
        var session=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),budget,
            8,Set.of("control"),current::get,tick::get,(method,row)->rows.add(row));
        KneekuraDebugDecisionHooks.install(session);
        KneekuraDebugDecisionHooks.ghastReachReturn(selected,controller,direction,7,true);
        require(rows.size()==1&&rows.get(0).getAsJsonObject("data").get("result").getAsBoolean(),"actual passed true argument retained");
        KneekuraDebugDecisionHooks.ghastReachReturn(other,other.getMoveControl(),direction,7,true);
        Thread worker=new Thread(()->KneekuraDebugDecisionHooks.ghastReachReturn(selected,controller,direction,7,true));worker.start();worker.join();
        require(rows.size()==1,"other subject/thread excluded");
        KneekuraDebugDecisionHooks.ghastReachReturn(selected,controller,direction,7,false);
        require(rows.size()==2&&!rows.get(1).getAsJsonObject("data").get("result").getAsBoolean(),"false return retained without invented reason");
        KneekuraDebugDecisionHooks.ghastReachReturn(selected,controller,direction,7,true);
        require(rows.size()==2&&"EVENT_BUDGET".equals(budget.reason()),"event bound suppresses later callback");
        KneekuraDebugDecisionHooks.clear("TEST_DONE");
        KneekuraDebugDecisionHooks.ghastReachReturn(selected,controller,direction,7,true);require(rows.size()==2,"OFF suppresses callback");
        for(String boundary:new String[]{"CHANNEL","CONTEXT","WINDOW","UUID","OTHER_CONTROLLER","WRONG_CLASS","NAN","STEP","BYTE","SINK"}) {
            current.set(context);tick.set(100);
            var guard=new KneekuraDebugDecisionBurstBudget(context,100,10,3,boundary.equals("BYTE")?1:65536);
            var bounded=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),guard,8,
                Set.of(boundary.equals("CHANNEL")?"path":"control"),current::get,tick::get,(method,row)->{
                    if(boundary.equals("SINK"))throw new java.io.IOException("SYNTHETIC_SINK_FAILURE");rows.add(row);
                });
            KneekuraDebugDecisionHooks.install(bounded);
            if(boundary.equals("CONTEXT"))current.set(new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,3,1,context.subjectUuid(),"minecraft:overworld"));
            if(boundary.equals("WINDOW"))tick.set(110);
            if(boundary.equals("UUID"))selected.setUUID(new UUID(0,3));
            Object supplied=boundary.equals("OTHER_CONTROLLER")?other.getMoveControl():boundary.equals("WRONG_CLASS")?new MoveControl(selected):controller;
            KneekuraDebugDecisionHooks.ghastReachReturn(selected,supplied,boundary.equals("NAN")?new Vec3(Double.NaN,0,0):direction,boundary.equals("STEP")?-1:7,true);
            require(rows.size()==2,"boundary suppresses invalid callback: "+boundary);
            if(boundary.equals("CONTEXT"))require("CONTEXT_CHANGED".equals(guard.reason()),"Arena change closes capture");
            if(boundary.equals("WINDOW"))require("WINDOW_ENDED".equals(guard.reason()),"exclusive tick bound closes capture");
            if(boundary.equals("BYTE"))require("BYTE_BUDGET".equals(guard.reason()),"byte cap retained");
            if(boundary.equals("SINK"))require("WRITER_UNAVAILABLE".equals(guard.reason()),"sink failure contained");
            KneekuraDebugDecisionHooks.clear("TEST_BOUNDARY_DONE");selected.setUUID(new UUID(0,1));
        }
        require(KneekuraDebugDecisionSnapshot.read(Entity.class,"uuid",selected).equals(new UUID(0,1)),"cached UUID retained");
        System.out.println("GHAST_REACH_INTEROP:"+rows.get(0));
        System.out.println("Ghast original reach callback: true/false, exact subject/controller/thread/UUID, OFF/channel/context/window/event/byte/sink guards; no reach/collision/controller replay");
    }
}
