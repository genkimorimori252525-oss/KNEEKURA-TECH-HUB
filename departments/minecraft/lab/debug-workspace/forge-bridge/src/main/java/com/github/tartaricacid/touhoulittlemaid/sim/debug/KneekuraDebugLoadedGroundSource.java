package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import java.util.HashMap;
import java.util.Map;

/** Loaded, bounded ground inputs. No chunk ticket, load/generation call or BlockEntity creation. */
final class KneekuraDebugLoadedGroundSource implements BlockGetter,KneekuraDebugTerrainField.GroundSource {
    private final ServerLevel level;
    private final int centerX,centerY,centerZ,margin,minHeight,height;
    private final Map<Long,LevelChunk> chunks=new HashMap<>();
    KneekuraDebugLoadedGroundSource(ServerLevel level,BlockPos center,int radius) {
        if(level==null||!level.getServer().isSameThread()||radius<0||radius>3)throw new IllegalArgumentException("INVALID_GROUND_SOURCE");
        this.level=level;centerX=center.getX();centerY=center.getY();centerZ=center.getZ();margin=radius+2;
        minHeight=level.getMinBuildHeight();height=level.getHeight();
    }
    private LevelChunk loaded(BlockPos pos) {
        if(Math.abs((long)pos.getX()-centerX)>margin||Math.abs((long)pos.getZ()-centerZ)>margin
                ||Math.abs((long)pos.getY()-centerY)>2||pos.getY()<minHeight||pos.getY()>=(long)minHeight+height)
            throw new IllegalStateException("GROUND_QUERY_INPUT_OUT_OF_BOUNDS");
        int x=pos.getX()>>4,z=pos.getZ()>>4;long key=((long)x&0xffffffffL)|((long)z<<32);
        LevelChunk chunk=chunks.get(key);
        if(chunk==null) {
            // ANCHOR getChunkNow is nonblocking; it may warm its lookup cache/profiler counter.
            // It can also expose a currently-loading chunk, so require the cached loaded flag.
            chunk=level.getChunkSource().getChunkNow(x,z);
            try {
                if(chunk==null||!(Boolean)KneekuraDebugDecisionSnapshot.read(LevelChunk.class,"loaded",chunk))
                    throw new IllegalStateException("GROUND_QUERY_CHUNK_NOT_LOADED");
            }catch(ReflectiveOperationException error){throw new IllegalStateException("GROUND_QUERY_CHUNK_IDENTITY_UNAVAILABLE",error);}
            if(chunks.size()>=4)throw new IllegalStateException("GROUND_QUERY_CHUNK_LIMIT");
            chunks.put(key,chunk);
        }
        return chunk;
    }
    @Override public BlockState getBlockState(BlockPos pos){return loaded(pos).getBlockState(pos);}
    @Override public FluidState getFluidState(BlockPos pos){return loaded(pos).getFluidState(pos);}
    @Override public BlockEntity getBlockEntity(BlockPos pos){
        // A custom classifier requiring mutable BlockEntity access remains unavailable.
        throw new UnsupportedOperationException("GROUND_QUERY_BLOCK_ENTITY_ACCESS_NOT_SUPPORTED");
    }
    @Override public int getHeight(){return height;}
    @Override public int getMinBuildHeight(){return minHeight;}
    @Override public BlockPathTypes classify(BlockPos pos){return WalkNodeEvaluator.getBlockPathTypeStatic(this,pos.mutable());}
}
