package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

/** Genuine APIs, synthetic original call behavior; does not prove runtime Mixin dispatch. */
public final class KneekuraDebugProjectileResultSelfTest {
    private static final class Subject extends Mob {
        int calls;boolean result;float loss;boolean fail;
        private Subject(){super(null,null);}
        @Override public float getHealth(){throw new AssertionError("Must read cached base health without custom getter");}
        @Override public boolean hurt(DamageSource source,float amount){
            calls++;if(fail)throw new IllegalArgumentException("ORIGINAL_FAILURE");
            try {var accessor=healthId();getEntityData().set(accessor,getEntityData().get(accessor)-loss);}
            catch(ReflectiveOperationException error){throw new AssertionError(error);}
            return result;
        }
    }
    private static final class Shot extends Projectile {
        private Shot(){super(null,null);}
        @Override protected void defineSynchedData(){}
        @Override protected void readAdditionalSaveData(CompoundTag tag){}
        @Override protected void addAdditionalSaveData(CompoundTag tag){}
        @Override public Entity getOwner(){throw new AssertionError("No owner lookup/replay");}
        @Override public void tick(){throw new AssertionError("No projectile tick replay");}
    }
    @SuppressWarnings("unchecked") private static EntityDataAccessor<Float> healthId()throws ReflectiveOperationException {
        return (EntityDataAccessor<Float>)KneekuraDebugDecisionSnapshot.read(LivingEntity.class,"DATA_HEALTH_ID",null);
    }
    private static <T extends Entity>T entity(Class<T> type)throws Exception {
        var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");field.setAccessible(true);
        var result=type.cast(((sun.misc.Unsafe)field.get(null)).allocateInstance(type));
        result.setUUID(UUID.randomUUID());
        for(String name:new String[]{"position","deltaMovement"}) {
            var member=Entity.class.getDeclaredField(name);member.setAccessible(true);member.set(result,new Vec3(1,65,2));
        }
        if(result instanceof LivingEntity) {
            var data=new SynchedEntityData(result);data.define(healthId(),20F);
            var member=Entity.class.getDeclaredField("entityData");member.setAccessible(true);member.set(result,data);
        }
        return result;
    }
    private static Shot shot(Subject owner)throws Exception {
        var shot=entity(Shot.class);shot.setOwner(owner);return shot;
    }
    private static void require(boolean condition,String detail){if(!condition)throw new AssertionError(detail);}
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var selected=entity(Subject.class);var other=entity(Subject.class);var target=entity(Subject.class);
        var context=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,3,7,selected.getUUID().toString(),"minecraft:overworld");
        var current=new AtomicReference<>(context);var rows=new ArrayList<JsonObject>();
        var session=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,256,512*1024),8,Set.of("control"),current::get,()->100L,(method,row)->rows.add(row));
        KneekuraDebugDecisionHooks.install(session);
        var rejected=shot(selected);KneekuraDebugDecisionHooks.projectileSpawnReturn(rejected,false);
        require(rows.size()==1&&!rows.get(0).getAsJsonObject("data").get("result").getAsBoolean(),"Actual rejected spawn retained");
        KneekuraDebugDecisionHooks.projectileTickReturn(rejected);require(rows.size()==1,"Rejected spawn not tracked");
        KneekuraDebugDecisionHooks.projectileSpawnReturn(shot(other),true);require(rows.size()==1,"Another owner excluded");
        var shot=shot(selected);KneekuraDebugDecisionHooks.projectileSpawnReturn(shot,true);
        KneekuraDebugDecisionHooks.projectileTickReturn(shot);
        require(rows.size()==3&&rows.get(2).getAsJsonObject("data").get("spawnEventIndex").getAsInt()==2,"Exact accepted spawn relationship");
        target.result=false;
        require(!KneekuraDebugDecisionHooks.projectileHurt(shot,target,null,3),"Original false preserved");
        target.result=true;target.loss=0;
        require(KneekuraDebugDecisionHooks.projectileHurt(shot,target,null,3),"Absorbed original true preserved");
        require(rows.get(4).getAsJsonObject("data").get("healthDelta").getAsFloat()==0,"True is not HP loss");
        target.loss=3;require(KneekuraDebugDecisionHooks.projectileHurt(shot,target,null,3),"Successful original return");
        require(target.calls==3&&rows.get(5).getAsJsonObject("data").get("healthDelta").getAsFloat()==3,"Exactly one original call and direct base HP delta");
        KneekuraDebugDecisionHooks.projectileHitReturn(shot,new EntityHitResult(target,new Vec3(3,65,2)));
        require(rows.get(6).get("kind").getAsString().equals("CONTROL_PROJECTILE_HIT_RETURN"),"Dispatch distinct from damage");
        target.fail=true;
        try{KneekuraDebugDecisionHooks.projectileHurt(shot,target,null,3);throw new AssertionError("Original exception missing");}
        catch(IllegalArgumentException expected){require(expected.getMessage().equals("ORIGINAL_FAILURE"),"Original exception preserved");}
        require(rows.size()==7&&target.calls==4,"Thrown original call creates no false RETURN");target.fail=false;
        var thread=new Thread(()->KneekuraDebugDecisionHooks.projectileTickReturn(shot));thread.start();thread.join();
        require(rows.size()==7,"Other thread excluded");
        shot.setOwner(other);KneekuraDebugDecisionHooks.projectileTickReturn(shot);
        require(rows.size()==7,"Ownership change excluded");shot.setOwner(selected);
        KneekuraDebugDecisionHooks.projectileTickReturn(shot);require(rows.size()==7,"Restored owner does not reconnect retired relationship");
        current.set(new KneekuraDebugDecisionBurstBudget.Context("s","different","snap",1,3,7,selected.getUUID().toString(),"minecraft:overworld"));
        KneekuraDebugDecisionHooks.projectileHurt(shot,target,null,3);
        require(rows.size()==7&&target.calls==5&&session.budget().reason().equals("CONTEXT_CHANGED"),"Closed context still calls gameplay exactly once");
        KneekuraDebugDecisionHooks.clear("TEST");
        var limited=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,256,512*1024),8,Set.of("control"),()->context,()->100L,(method,row)->{});
        KneekuraDebugDecisionHooks.install(limited);
        for(int i=0;i<17;i++)KneekuraDebugDecisionHooks.projectileSpawnReturn(shot(selected),true);
        require(limited.budget().events()==16,"Related references bounded to sixteen without UUID expansion");
        KneekuraDebugDecisionHooks.clear("TEST");
        KneekuraDebugDecisionHooks.projectileHurt(shot,target,null,3);require(target.calls==6,"Disabled observer preserves original invocation");
        var excluded=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,256,512*1024),8,Set.of("path"),()->context,()->100L,
            (method,row)->{throw new AssertionError("Excluded channel wrote");});
        KneekuraDebugDecisionHooks.install(excluded);KneekuraDebugDecisionHooks.projectileSpawnReturn(shot,true);
        KneekuraDebugDecisionHooks.projectileHurt(shot,target,null,3);
        require(target.calls==7&&excluded.budget().events()==0,"Excluded channel does no recording and invokes original once");
        KneekuraDebugDecisionHooks.clear("TEST");
        var exhausted=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,1,65536),8,Set.of("control"),()->context,()->100L,(method,row)->{});
        KneekuraDebugDecisionHooks.install(exhausted);var finalShot=shot(selected);
        KneekuraDebugDecisionHooks.projectileSpawnReturn(finalShot,true);KneekuraDebugDecisionHooks.projectileHurt(finalShot,target,null,3);
        require(target.calls==8&&exhausted.budget().events()==1&&exhausted.budget().reason().equals("EVENT_BUDGET"),"Event cap preserves gameplay");
        KneekuraDebugDecisionHooks.clear("TEST");
        var failingSink=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,3,65536),8,Set.of("control"),()->context,()->100L,
            (method,row)->{throw new java.io.IOException("SINK_FAILURE");});
        KneekuraDebugDecisionHooks.install(failingSink);KneekuraDebugDecisionHooks.projectileSpawnReturn(finalShot,true);
        KneekuraDebugDecisionHooks.projectileHurt(finalShot,target,null,3);
        require(target.calls==9&&failingSink.budget().reason().equals("WRITER_UNAVAILABLE"),"Sink failure preserves gameplay and closes tracking");
        KneekuraDebugDecisionHooks.clear("TEST");
        var narrowRows=new ArrayList<JsonObject>();
        var narrow=new KneekuraDebugDecisionHooks.Session(selected,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context,100,10,3,65536),8,Set.of("projectile"),()->context,()->100L,(method,row)->narrowRows.add(row));
        KneekuraDebugDecisionHooks.install(narrow);var narrowShot=shot(selected);
        KneekuraDebugDecisionHooks.controlReturn(selected,"move");KneekuraDebugDecisionHooks.teleportReturn(selected,1,65,2,true);
        KneekuraDebugDecisionHooks.projectileSpawnReturn(narrowShot,true);KneekuraDebugDecisionHooks.projectileTickReturn(narrowShot);
        KneekuraDebugDecisionHooks.projectileHurt(narrowShot,target,null,3);
        require(narrowRows.size()==3&&narrowRows.stream().allMatch(r->r.get("kind").getAsString().startsWith("CONTROL_PROJECTILE_")),"Narrow channel records only projectile facts, no control replay/budget starvation");
        require(target.calls==10,"Narrow observation preserves one original hurt call");KneekuraDebugDecisionHooks.clear("TEST");
        var interop=new JsonObject();interop.addProperty("subjectUuid",selected.getUUID().toString());
        var payloads=new com.google.gson.JsonArray();rows.forEach(payloads::add);interop.add("rows",payloads);
        System.out.println("PROJECTILE_INTEROP:"+interop);
        System.out.println("Related projectile producer: exact accepted owner/spawn, finite16 references, no lookup/tick replay, cancelled/absorbed/HP results, context/thread, original single call/exception passed");
    }
}
