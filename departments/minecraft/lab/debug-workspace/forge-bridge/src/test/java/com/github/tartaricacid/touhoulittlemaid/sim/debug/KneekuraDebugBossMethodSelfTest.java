package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.SharedConstants;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import sun.misc.Unsafe;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Genuine compiled TF field/producer fixtures, not an execution of TF AI or gameplay acceptance. */
public final class KneekuraDebugBossMethodSelfTest {
    private static final class HostileList extends ArrayList<Object> {
        @Override public int size(){throw new AssertionError("custom list size");}
        @Override public Object get(int index){throw new AssertionError("custom list get");}
    }
    private static void set(Class<?> owner,String name,Object object,Object value)throws Exception {
        var f=owner.getDeclaredField(name);f.setAccessible(true);f.set(object,value);
    }
    private static Object named(Class<?> owner,String name){return Arrays.stream(owner.getEnumConstants())
        .filter(v->((Enum<?>)v).name().equals(name)).findFirst().orElseThrow();}
    private static KneekuraDebugDecisionHooks.Session session(Mob subject,ArrayList<JsonObject> rows,int events,
            Set<String> channels,KneekuraDebugDecisionBurstBudget.Context context)throws ReflectiveOperationException {
        var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(7);
        return new KneekuraDebugDecisionHooks.Session(subject,null,null,snapshot,
            new KneekuraDebugDecisionBurstBudget(context,100,5,events,65536),2,channels,()->context,()->100L,
            (method,row)->rows.add(row));
    }
    private static KneekuraDebugDecisionBurstBudget.Context context(String uuid){return
        new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,uuid,"minecraft:overworld");}
    public static void main(String[] args)throws Exception {
        SharedConstants.tryDetectVersion();Bootstrap.bootStrap();
        var f=Unsafe.class.getDeclaredField("theUnsafe");f.setAccessible(true);Unsafe unsafe=(Unsafe)f.get(null);
        Class<?> knight=Class.forName("twilightforest.entity.boss.KnightPhantom"),
            goalClass=Class.forName("twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal"),
            formation=Class.forName("twilightforest.entity.boss.KnightPhantom$Formation"),
            hydra=Class.forName("twilightforest.entity.boss.Hydra"),
            container=Class.forName("twilightforest.entity.boss.HydraHeadContainer"),
            state=Class.forName("twilightforest.entity.boss.HydraHeadContainer$State");
        var adapter=KneekuraDebugTwilightForestAdapter.shared();
        var hashes=new java.util.LinkedHashMap<String,String>();
        adapter.descriptor().getAsJsonObject("classHashes").entrySet().forEach(e->hashes.put(e.getKey(),e.getValue().getAsString()));
        hashes.put(goalClass.getName(),"bb1f3d4374a2f5926050c3fd9cf0dff142e47d81daf4d0f801d79b473f1fdaf1");
        require(KneekuraDebugAdapterSourceProof.verify(Path.of(args[0]),"7d7842c3c66d355c94bd726ef69ad14ac4f944061198927c3eb54a728e23580a",
            hashes,owner->{try(var in=knight.getClassLoader().getResourceAsStream(owner.replace('.','/')+".class")){return in.readAllBytes();}}),
            "actual mapped artifact and all class resource hashes");
        // Warm only after the genuine source proof above; Forge ModList is not initialized by this unit fixture.
        set(adapter.getClass(),"compatible",adapter,true);set(adapter.getClass(),"provenLoader",adapter,knight.getClassLoader());
        set(adapter.getClass(),"coordinationCompatible",adapter,true);set(adapter.getClass(),"coordinationLoader",adapter,goalClass.getClassLoader());
        var members=new ArrayList<Object>();
        for(int i=0;i<3;i++) {
            Object m=unsafe.allocateInstance(knight);set(Entity.class,"uuid",m,new UUID(0,i+1));
            set(knight,"number",m,i);set(knight,"ticksProgress",m,0);set(knight,"currentFormation",m,named(formation,"SMALL_CLOCKWISE"));members.add(m);
        }
        Mob source=(Mob)members.get(0),member=(Mob)members.get(1),target=(Mob)members.get(2);
        set(Mob.class,"target",source,target);set(Mob.class,"target",member,target);
        Object goal=unsafe.allocateInstance(goalClass);set(goalClass,"boss",goal,source);
        var knightRows=new ArrayList<JsonObject>();var s=session(source,knightRows,2,Set.of("mod"),context(new UUID(0,1).toString()));
        s.knightLeader(goal,new HostileList(),true);require(knightRows.isEmpty(),"custom list suppressed without methods");
        Object wrongGoal=unsafe.allocateInstance(goalClass);set(goalClass,"boss",wrongGoal,member);
        s.knightLeader(wrongGoal,members,true);require(knightRows.isEmpty(),"wrong source goal excluded");
        Thread other=new Thread(()->s.knightLeader(goal,members,true));other.start();other.join();require(knightRows.isEmpty(),"other thread excluded");
        s.knightLeader(goal,members,true);s.knightMemberDispatch(goal,member);
        require(knightRows.size()==2,"two bounded original boundaries");
        JsonObject leader=knightRows.get(0).getAsJsonObject("data");
        require(leader.getAsJsonArray("membersAtReturn").size()==2&&leader.get("truncated").getAsBoolean(),"member prefix bound");
        require(leader.getAsJsonArray("membersAtReturn").get(1).getAsJsonObject().get("targetUuid").getAsString().equals(new UUID(0,3).toString()),"per-member stored target");
        set(Mob.class,"target",member,null);
        require(knightRows.get(1).getAsJsonObject("data").get("targetUuid").getAsString().equals(new UUID(0,3).toString()),"detached dispatch target");
        s.knightLeader(goal,members,false);require(knightRows.size()==2,"event cap excludes later callbacks");
        var noMod=new ArrayList<JsonObject>();var excluded=session(source,noMod,8,Set.of("path"),context(new UUID(0,1).toString()));
        excluded.knightLeader(goal,members,true);excluded.knightMemberDispatch(goal,member);require(noMod.isEmpty(),"opt-in channel only");
        Mob boss=(Mob)unsafe.allocateInstance(hydra);set(Entity.class,"uuid",boss,new UUID(0,10));set(hydra,"numHeads",boss,7);
        Object[] heads=(Object[])java.lang.reflect.Array.newInstance(container,7);
        for(int i=0;i<7;i++){
            Object h=unsafe.allocateInstance(container);set(container,"hydra",h,boss);set(container,"headNum",h,i);
            set(container,"prevState",h,named(state,"IDLE"));set(container,"currentState",h,named(state,"MORTAR_BEGINNING"));
            set(container,"ticksProgress",h,0);set(container,"ticksNeeded",h,40);set(container,"targetEntity",h,target);heads[i]=h;
        }
        set(hydra,"hc",boss,heads);var hydraRows=new ArrayList<JsonObject>();
        var h=session(boss,hydraRows,8,Set.of("mod"),context(new UUID(0,10).toString()));
        Object foreign=unsafe.allocateInstance(container);set(container,"hydra",foreign,unsafe.allocateInstance(hydra));set(container,"headNum",foreign,0);
        h.hydraTargetReturn(foreign,target);h.hydraStateWrite(foreign);require(hydraRows.isEmpty(),"unselected coordinator excluded");
        h.hydraTargetReturn(heads[0],target);h.hydraStateWrite(heads[0]);
        require(hydraRows.size()==2,"target setter and exact field checkpoint emitted");
        require(hydraRows.get(1).get("semantics").getAsString().equals("ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY"),"field semantics distinct from return");
        require(hydraRows.get(1).getAsJsonObject("data").get("activeAttackType").getAsString().equals("MORTAR"),"derived stored attack type");
        set(container,"targetEntity",heads[0],null);h.hydraTargetReturn(heads[0],null);
        require(hydraRows.get(2).getAsJsonObject("data").get("requestedTargetUuid").isJsonNull(),"null assignment retained");
        set(container,"prevState",heads[0],named(state,"MORTAR_BEGINNING"));h.hydraStateWrite(heads[0]);
        require(!hydraRows.get(3).getAsJsonObject("data").get("valueChanged").getAsBoolean(),"actual write may keep same state value");
        for(JsonObject r:knightRows)System.out.println("BOSS_INTEROP:"+r);
        for(JsonObject r:hydraRows)System.out.println("BOSS_INTEROP:"+r);
        System.out.println("Boss method fixtures: genuine resource proof; owner/thread/channel/caps; detached member targets; null setter; conditional write and derived attack state");
    }
    private static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
}
