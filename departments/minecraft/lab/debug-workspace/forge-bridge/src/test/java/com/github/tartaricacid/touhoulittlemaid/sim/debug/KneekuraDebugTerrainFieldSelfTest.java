package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import java.util.EnumMap;
import java.util.concurrent.atomic.AtomicInteger;

public final class KneekuraDebugTerrainFieldSelfTest {
    public static void main(String[] args)throws Exception {
        var overrides=new EnumMap<BlockPathTypes,Float>(BlockPathTypes.class);overrides.put(BlockPathTypes.WALKABLE,2.5F);
        var reads=new AtomicInteger();
        var data=KneekuraDebugTerrainField.capture(new BlockPos(0,64,0),1,9,1000000L,()->0L,
                pos->{reads.incrementAndGet();return BlockPathTypes.WALKABLE;},overrides);
        require(reads.get()==9,"finite square query");
        require(data.getAsJsonArray("cells").size()==9,"nine cells retained");
        var cell=data.getAsJsonArray("cells").get(0).getAsJsonObject();
        require(cell.get("observationRole").getAsString().equals("OBSERVER_QUERIED_GROUND_ONLY"),"query is not path evaluation");
        require(cell.get("selectedMobOverride").getAsFloat()==2.5F,"cached own override");
        require(cell.get("effectiveMalusStatus").getAsString().equals("NOT_EXPOSED"),"no effective getter replay or invented inheritance");
        require(cell.get("evaluatedByPathfinderStatus").getAsString().equals("NOT_CAPTURED"),"no invented evaluation");
        require(overrides.size()==1&&overrides.get(BlockPathTypes.WALKABLE)==2.5F,"own map unchanged");
        var unavailable=KneekuraDebugTerrainField.capture(new BlockPos(0,64,0),0,1,1000000L,()->0L,
                pos->{throw new IllegalStateException("CHUNK_UNAVAILABLE");},overrides);
        require(unavailable.getAsJsonArray("cells").get(0).getAsJsonObject().get("status").getAsString().equals("NOT_EXPOSED"),"unavailable cell cannot become air");
        reads.set(0);
        var bounded=KneekuraDebugTerrainField.capture(new BlockPos(0,64,0),3,2,1000000L,()->0L,
                pos->{reads.incrementAndGet();return BlockPathTypes.BLOCKED;},overrides);
        require(reads.get()==2&&bounded.get("truncated").getAsBoolean(),"cell limit stops query");
        var clock=new java.util.concurrent.atomic.AtomicLong();
        var timed=KneekuraDebugTerrainField.capture(new BlockPos(0,64,0),1,9,10L,()->clock.getAndAdd(10L),
                pos->{throw new AssertionError("deadline exceeded before first cell");},overrides);
        require(timed.get("truncated").getAsBoolean()&&timed.getAsJsonArray("cells").isEmpty(),"deadline checked between cells");
        try{KneekuraDebugTerrainField.capture(new BlockPos(0,64,0),4,49,1000000L,()->0L,pos->BlockPathTypes.OPEN,overrides);throw new AssertionError("radius accepted");}
        catch(IllegalArgumentException expected){ }
        System.out.println("Terrain field: finite cells/radius/deadline, explicit query/evaluation distinction, unchanged cached override, missing cell unknown");
    }
    private static void require(boolean condition,String text){if(!condition)throw new AssertionError(text);}
}
