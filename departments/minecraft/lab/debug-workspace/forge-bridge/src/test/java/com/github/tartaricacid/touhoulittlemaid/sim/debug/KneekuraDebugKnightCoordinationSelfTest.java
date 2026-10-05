package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import net.minecraft.SharedConstants;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.entity.Entity;
import sun.misc.Unsafe;
import java.util.ArrayList;
import java.util.UUID;
import java.util.Set;
import java.util.Map;
import java.nio.file.Path;

/** Genuine pinned TF classes; constructor-free cached fields are not native gameplay acceptance. */
public final class KneekuraDebugKnightCoordinationSelfTest {
    private static final class HostileList extends ArrayList<Object> {
        @Override public int size(){throw new AssertionError("custom size executed");}
        @Override public Object get(int index){throw new AssertionError("custom get executed");}
    }
    private static void set(Class<?> owner,String name,Object target,Object value)throws Exception {
        var field=owner.getDeclaredField(name);field.setAccessible(true);field.set(target,value);
    }
    public static void main(String[] args)throws Exception {
        SharedConstants.tryDetectVersion();Bootstrap.bootStrap();
        var unsafeField=Unsafe.class.getDeclaredField("theUnsafe");unsafeField.setAccessible(true);
        Unsafe unsafe=(Unsafe)unsafeField.get(null);
        Class<?> knight=Class.forName("twilightforest.entity.boss.KnightPhantom");
        Class<?> goalClass=Class.forName("twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal");
        Class<?> formation=Class.forName("twilightforest.entity.boss.KnightPhantom$Formation");
        Object hover=java.util.Arrays.stream(formation.getEnumConstants()).filter(v->((Enum<?>)v).name().equals("HOVER")).findFirst().orElseThrow();
        var members=new ArrayList<Object>();
        for(int i=0;i<17;i++){
            Object member=unsafe.allocateInstance(knight);
            set(Entity.class,"uuid",member,new UUID(0,i+1));set(knight,"number",member,i);
            set(knight,"currentFormation",member,hover);set(knight,"ticksProgress",member,i);
            members.add(member);
        }
        Object source=members.get(0),goal=unsafe.allocateInstance(goalClass);set(goalClass,"boss",goal,source);
        String goalHash="bb1f3d4374a2f5926050c3fd9cf0dff142e47d81daf4d0f801d79b473f1fdaf1";
        var hashes=Map.of(goalClass.getName(),goalHash,knight.getName(),"5be6108fbd0606e7c03060fbe843afe8a8b2b1c57247f71f146ad307b695292f");
        require(KneekuraDebugAdapterSourceProof.verify(Path.of(args[0]),"7d7842c3c66d355c94bd726ef69ad14ac4f944061198927c3eb54a728e23580a",hashes,
            owner->{try(var in=knight.getClassLoader().getResourceAsStream(owner.replace('.','/')+".class")){return in.readAllBytes();}}),"genuine goal and Knight resource proof");
        JsonObject data=KneekuraDebugTwilightForestAdapter.cachedKnightCoordination(source,goal,members,16);
        require(data.getAsJsonArray("membersAtReturn").size()==16&&data.get("originalListCount").getAsInt()==17,"bounded original list");
        require(data.get("truncated").getAsBoolean(),"truncation explicit");
        require(data.getAsJsonArray("membersAtReturn").get(1).getAsJsonObject().get("entityUuid").getAsString().equals(new UUID(0,2).toString()),"original order retained");
        require(data.get("affectedMembersStatus").getAsString().equals("NOT_EXPOSED"),"post-state not dispatch result");
        set(knight,"ticksProgress",members.get(0),99);
        require(data.getAsJsonObject("sourceStateAtReturn").get("ticksProgress").getAsInt()==0,"detached cached state");
        members.set(1,new Object());
        data=KneekuraDebugTwilightForestAdapter.cachedKnightCoordination(source,goal,members,2);
        require(data.getAsJsonArray("membersAtReturn").get(1).getAsJsonObject().get("stateStatus").getAsString().equals("NOT_EXPOSED"),"unknown member not replayed");
        try{KneekuraDebugTwilightForestAdapter.cachedKnightCoordination(source,goal,new HostileList(),16);throw new AssertionError("unknown list accepted");}
        catch(IllegalArgumentException expected){require(expected.getMessage().equals("TF_ORIGINAL_LIST_UNSUPPORTED"),"unknown list rejected before methods");}
        try{KneekuraDebugTwilightForestAdapter.cachedKnightCoordination(members.get(2),goal,members,16);throw new AssertionError("wrong source accepted");}
        catch(IllegalArgumentException expected){require(expected.getMessage().equals("TF_COORDINATION_OWNER_MISMATCH"),"goal cached owner fence");}
        // Supply the actually verified compatibility cache without initializing Forge ModList in this unit harness.
        var adapter=KneekuraDebugTwilightForestAdapter.shared();
        set(adapter.getClass(),"compatible",adapter,true);set(adapter.getClass(),"provenLoader",adapter,knight.getClassLoader());
        set(adapter.getClass(),"coordinationCompatible",adapter,true);set(adapter.getClass(),"coordinationLoader",adapter,goalClass.getClassLoader());
        var context=new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,new UUID(0,1).toString(),"minecraft:overworld");
        var rows=new ArrayList<JsonObject>();var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(7);
        var session=new KneekuraDebugDecisionHooks.Session((net.minecraft.world.entity.Mob)source,null,null,snapshot,
            new KneekuraDebugDecisionBurstBudget(context,100,5,1,65536),2,Set.of("mod"),()->context,()->100L,(method,row)->rows.add(row));
        var hostile=new HostileList();session.knightCoordination(goal,hostile);
        require(rows.isEmpty()&&session.budget().events()==0,"custom list suppressed before observer budget");
        Object wrongGoal=unsafe.allocateInstance(goalClass);set(goalClass,"boss",wrongGoal,members.get(2));
        session.knightCoordination(wrongGoal,members);require(rows.isEmpty(),"unselected goal excluded");
        Thread other=new Thread(()->session.knightCoordination(goal,members));other.start();other.join();
        require(rows.isEmpty(),"other thread excluded");
        session.knightCoordination(goal,members);
        require(rows.size()==1&&rows.get(0).get("kind").getAsString().equals("MOD_COORDINATION_RETURN"),"exact original context recorded");
        require(rows.get(0).getAsJsonObject("data").get("maxMembers").getAsInt()==2,"node budget bounds group members");
        session.knightCoordination(goal,members);require(rows.size()==1,"finite event budget");
        var excluded=new KneekuraDebugDecisionHooks.Session((net.minecraft.world.entity.Mob)source,null,null,snapshot,
            new KneekuraDebugDecisionBurstBudget(context,100,5,8,65536),2,Set.of("path"),()->context,()->100L,(method,row)->{throw new AssertionError("excluded mod channel");});
        excluded.knightCoordination(goal,members);require(excluded.budget().events()==0,"default/excluded channel has no record");
        System.out.println("KNIGHT_INTEROP:"+rows.get(0));
        System.out.println("Knight original-list cached producer: bounded order, detached state, exact owner, no custom List methods or inferred leader");
    }
    private static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
}
