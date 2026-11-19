package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;
import java.util.Set;
import java.util.concurrent.atomic.AtomicLong;

/** Genuine producer APIs with unconstructed test subjects; not native Mixin acceptance. */
public final class KneekuraDebugTeleportReturnSelfTest {
    private static final class Subject extends Mob {
        private Subject() { super(null,null); }
        @Override public boolean randomTeleport(double x,double y,double z,boolean particles) {
            throw new AssertionError("Observer must not invoke teleport");
        }
    }
    private static Subject subject(double x,double y,double z) throws Exception {
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);
        var unsafe=(sun.misc.Unsafe)field.get(null);
        var subject=(Subject)unsafe.allocateInstance(Subject.class);
        var position=Entity.class.getDeclaredField("position");position.setAccessible(true);
        position.set(subject,new Vec3(x,y,z));return subject;
    }
    private static void require(boolean condition,String message) {
        if(!condition)throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        var context=new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,3,7,
                "11111111-2222-3333-4444-555555555555","minecraft:overworld");
        var clock=new AtomicLong(100);var rows=new ArrayList<JsonObject>();
        var selected=subject(1,64,2);var other=subject(9,64,9);
        var snapshot=new KneekuraDebugDecisionSnapshot();
        var session=new KneekuraDebugDecisionHooks.Session(selected,null,null,snapshot,
                new KneekuraDebugDecisionBurstBudget(context,100,5,3,65536),8,Set.of("control"),
                ()->context,clock::get,(method,row)->rows.add(row));
        KneekuraDebugDecisionHooks.install(session);
        KneekuraDebugDecisionHooks.teleportReturn(other,2,64,2,true);
        require(rows.isEmpty(),"Unselected subject excluded");
        KneekuraDebugDecisionHooks.teleportReturn(selected,2,64,2,false);
        require(rows.size()==1,"Failed original attempt retained");
        require(!rows.get(0).getAsJsonObject("data").get("result").getAsBoolean(),"Actual false return retained");
        require(rows.get(0).getAsJsonObject("data").getAsJsonObject("returnedPosition").get("x").getAsDouble()==1,"Cached position read without teleport replay");
        KneekuraDebugDecisionHooks.teleportReturn(selected,2,64,2,true);
        require(rows.size()==2&&rows.get(1).getAsJsonObject("data").get("result").getAsBoolean(),"Actual true return retained separately");
        require(rows.get(1).get("targetRevision").getAsLong()==7,"Selection fenced");
        var thread=new Thread(()->KneekuraDebugDecisionHooks.teleportReturn(selected,2,64,2,true));thread.start();thread.join();
        require(rows.size()==2,"Wrong thread excluded");
        clock.set(105);KneekuraDebugDecisionHooks.teleportReturn(selected,2,64,2,true);
        require(rows.size()==2&&session.budget().reason().equals("WINDOW_ENDED"),"Expired original capture excluded");
        KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");
        var excluded=new KneekuraDebugDecisionHooks.Session(selected,null,null,snapshot,
                new KneekuraDebugDecisionBurstBudget(context,100,5,3,65536),8,Set.of("path"),
                ()->context,()->100L,(method,row)->{throw new AssertionError("Excluded channel emitted");});
        KneekuraDebugDecisionHooks.install(excluded);
        KneekuraDebugDecisionHooks.teleportReturn(selected,2,64,2,true);
        require(excluded.budget().events()==0,"Excluded channel consumes no event budget");
        KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");
        System.out.println("Teleport original-return producer: selected/channel/thread/window fences, actual boolean and cached position, no teleport replay passed");
    }
}
