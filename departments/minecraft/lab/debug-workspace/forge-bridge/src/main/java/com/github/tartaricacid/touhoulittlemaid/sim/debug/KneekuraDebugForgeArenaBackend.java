package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.entity.EntityTypeTest;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import java.io.IOException;
import java.util.*;

/** Real Forge actions. Captures/restores blocks and subject pose only, never full-world rollback. */
public final class KneekuraDebugForgeArenaBackend implements KneekuraDebugArenaController.Backend {
    @FunctionalInterface public interface ObservationSink {
        String persist(long arenaEpoch,long localServerTick,long gameTime,String lane,JsonObject payload)throws IOException;
    }
    @FunctionalInterface public interface AuthorityCheck { void require() throws IOException; }
    private final AuthorityCheck authority;
    private static final Set<Block> PALETTE=Set.of(Blocks.AIR,Blocks.STONE,Blocks.GLASS,Blocks.BARRIER);
    private final KneekuraDebugEnv.Config config; private final MinecraftServer server; private final ServerLevel level;
    private final String dimensionId; private final KneekuraDebugArenaController.Bounds bounds;
    private final Map<String,KneekuraDebugArenaController.Subject> subjects;private final ObservationSink sink;
    private final Map<BlockPos,BlockState> baselineBlocks=new LinkedHashMap<>();
    private final Map<UUID,Pose> baselineSubjects=new LinkedHashMap<>();
    private record Pose(double x,double y,double z,float yaw,float pitch,Vec3 velocity) { }

    KneekuraDebugForgeArenaBackend(KneekuraDebugEnv.Config config,MinecraftServer server,ServerLevel level,
            String dimensionId,KneekuraDebugArenaController.Bounds bounds,Map<String,KneekuraDebugArenaController.Subject> subjects,ObservationSink sink,AuthorityCheck authority)throws IOException {
        this.authority=Objects.requireNonNull(authority);this.config=Objects.requireNonNull(config);this.server=Objects.requireNonNull(server);this.level=Objects.requireNonNull(level);
        this.dimensionId=dimensionId;this.bounds=Objects.requireNonNull(bounds);this.subjects=Map.copyOf(subjects);this.sink=Objects.requireNonNull(sink);
        guard();inspectSupportedState();
        for(BlockPos p:positions())baselineBlocks.put(p,level.getBlockState(p));
        for(var s:this.subjects.values()){Entity e=resolve(s);baselineSubjects.put(e.getUUID(),pose(e));}
    }
    @Override public void requireOwnerThread()throws IOException {if(!server.isSameThread())throw new IOException("SERVER_THREAD_REQUIRED");}
    @Override public void guard()throws IOException {
        requireOwnerThread();authority.require();
        if(!config.enabled()||level.getServer()!=server||!"KNEEKURA_DEBUG_WORLD".equals(config.worldName())||
                !config.worldName().equals(server.getWorldData().getLevelName())||!dimensionId.equals(level.dimension().location().toString()))throw new IOException("DISPOSABLE_DEBUG_WORLD_IDENTITY_MISMATCH");
    }
    private List<BlockPos> positions(){
        List<BlockPos> cells=new ArrayList<>();for(int x=bounds.minX();x<bounds.maxX();x++)for(int y=bounds.minY();y<bounds.maxY();y++)for(int z=bounds.minZ();z<bounds.maxZ();z++)cells.add(new BlockPos(x,y,z));return cells;
    }
    private AABB box(){return new AABB(bounds.minX(),bounds.minY(),bounds.minZ(),bounds.maxX(),bounds.maxY(),bounds.maxZ());}
    private void inspectSupportedState()throws IOException {
        guard();for(BlockPos p:positions()){
            if(!level.isLoaded(p))throw new IOException("ARENA_CHUNK_NOT_LOADED");
            BlockState state=level.getBlockState(p);
            if(!PALETTE.contains(state.getBlock())||!state.equals(state.getBlock().defaultBlockState())||level.getBlockEntity(p)!=null||!state.getFluidState().isEmpty())throw new IOException("UNCONTROLLED_BLOCK_STATE");
        }
        Set<UUID> registered=new HashSet<>();subjects.values().forEach(s->registered.add(UUID.fromString(s.uuid())));
        List<Entity> occupants=new ArrayList<>();
        // Bound the result allocation. No world-wide scan or entity-name lookup.
        level.getEntities(EntityTypeTest.forClass(Entity.class),box(),e->true,occupants,17);
        for(Entity e:occupants)if(e instanceof Player||!registered.contains(e.getUUID()))throw new IOException("UNCONTROLLED_ARENA_ENTITY");
        if(occupants.size()>16)throw new IOException("ARENA_ENTITY_LIMIT");
        for(var s:subjects.values())resolve(s);
    }
    private boolean containsBox(AABB b){return b.minX>=bounds.minX()&&b.maxX<=bounds.maxX()&&b.minY>=bounds.minY()&&b.maxY<=bounds.maxY()&&b.minZ>=bounds.minZ()&&b.maxZ<=bounds.maxZ();}
    private Entity resolve(KneekuraDebugArenaController.Subject subject)throws IOException {
        guard();Entity e=level.getEntity(UUID.fromString(subject.uuid()));
        if(e==null||e.isRemoved()||!e.isAlive()||e instanceof Player||e.level()!=level||e.isPassenger()||e.isVehicle()||
                !BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString().equals(subject.entityType())||!containsBox(e.getBoundingBox()))throw new IOException("SUBJECT_NOT_EXACT_OR_OUTSIDE_ARENA");
        return e;
    }
    @Override public void preflight(JsonObject action)throws IOException {
        inspectSupportedState();String type=action.get("type").getAsString();
        if("teleport_subject".equals(type)){
            JsonObject args=action.getAsJsonObject("args");Entity e=resolve(subjects.get(args.get("subject_id").getAsString()));
            JsonArray p=args.getAsJsonArray("position");AABB target=e.getBoundingBox().move(p.get(0).getAsDouble()-e.getX(),p.get(1).getAsDouble()-e.getY(),p.get(2).getAsDouble()-e.getZ());
            if(!containsBox(target))throw new IOException("SUBJECT_BOUNDING_BOX_OUTSIDE_ARENA");
        }else if(!Set.of("wait_ticks","set_block","reset_arena").contains(type))throw new IOException("BACKEND_UNAVAILABLE");
    }
    @Override public JsonObject apply(JsonObject action)throws IOException {
        preflight(action);JsonObject args=action.getAsJsonObject("args"),out=new JsonObject();
        switch(action.get("type").getAsString()){
            case "set_block" -> {
                JsonArray p=args.getAsJsonArray("position");BlockPos pos=new BlockPos(p.get(0).getAsInt(),p.get(1).getAsInt(),p.get(2).getAsInt());
                Block block=BuiltInRegistries.BLOCK.get(ResourceLocation.tryParse(args.get("block").getAsString()));
                if(!PALETTE.contains(block))throw new IOException("BLOCK_BACKEND_UNAVAILABLE");
                BlockState target=block.defaultBlockState();
                // UPDATE_CLIENTS only. Third-party callbacks are uncontrolled and disclosed.
                level.setBlock(pos,target,2);
                if(!target.equals(level.getBlockState(pos)))throw new IOException("POSTCONDITION_MISMATCH");
                out.addProperty("block",BuiltInRegistries.BLOCK.getKey(level.getBlockState(pos).getBlock()).toString());out.add("position",p.deepCopy());
            }
            case "teleport_subject" -> {
                Entity e=resolve(subjects.get(args.get("subject_id").getAsString()));JsonArray p=args.getAsJsonArray("position"),r=args.getAsJsonArray("rotation");
                e.teleportTo(p.get(0).getAsDouble(),p.get(1).getAsDouble(),p.get(2).getAsDouble());e.setYRot(r.get(0).getAsFloat());e.setXRot(r.get(1).getAsFloat());
                if(e.getX()!=p.get(0).getAsDouble()||e.getY()!=p.get(1).getAsDouble()||e.getZ()!=p.get(2).getAsDouble()||e.getYRot()!=r.get(0).getAsFloat()||e.getXRot()!=r.get(1).getAsFloat()||!containsBox(e.getBoundingBox()))throw new IOException("POSTCONDITION_MISMATCH");
                out.addProperty("subjectUuid",e.getUUID().toString());out.add("measuredPose",poseJson(pose(e)));
            }
            default -> throw new IOException("BACKEND_UNAVAILABLE");
        }
        out.addProperty("postconditionMatched",true);return out;
    }
    @Override public void restoreBaseline()throws IOException {
        // Preflight the complete bounded scope before the first restoration write.
        inspectSupportedState();
        for(var entry:baselineBlocks.entrySet()){
            guard();level.setBlock(entry.getKey(),entry.getValue(),2);
            if(!entry.getValue().equals(level.getBlockState(entry.getKey())))throw new IOException("POSTCONDITION_MISMATCH");
        }
        for(var entry:baselineSubjects.entrySet()){
            guard();Entity e=level.getEntity(entry.getKey());if(e==null||e instanceof Player||e.level()!=level)throw new IOException("RESET_SUBJECT_UNAVAILABLE");
            Pose p=entry.getValue();e.teleportTo(p.x,p.y,p.z);e.setYRot(p.yaw);e.setXRot(p.pitch);e.setDeltaMovement(p.velocity);
        }
        // Controller measures the same scope fingerprint before a VERIFIED reset receipt.
    }
    @Override public String stateHash()throws IOException {
        inspectSupportedState();JsonObject snapshot=new JsonObject();snapshot.addProperty("scope",KneekuraDebugArenaController.SCOPE);
        snapshot.addProperty("dimension",dimensionId);JsonArray blocks=new JsonArray();
        for(BlockPos p:positions()){JsonArray cell=new JsonArray();cell.add(p.getX());cell.add(p.getY());cell.add(p.getZ());cell.add(BuiltInRegistries.BLOCK.getKey(level.getBlockState(p).getBlock()).toString());blocks.add(cell);}
        snapshot.add("blocks",blocks);JsonObject poses=new JsonObject();for(var s:subjects.values())poses.add(s.uuid(),poseJson(pose(resolve(s))));snapshot.add("subjectPoses",poses);
        return KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(snapshot));
    }
    private static Pose pose(Entity e){return new Pose(e.getX(),e.getY(),e.getZ(),e.getYRot(),e.getXRot(),e.getDeltaMovement());}
    private static JsonObject poseJson(Pose p){JsonObject o=new JsonObject();o.addProperty("x",p.x);o.addProperty("y",p.y);o.addProperty("z",p.z);o.addProperty("yaw",p.yaw);o.addProperty("pitch",p.pitch);o.addProperty("vx",p.velocity.x);o.addProperty("vy",p.velocity.y);o.addProperty("vz",p.velocity.z);return o;}
    @Override public String observe(long epoch,long tick,String lane,JsonObject payload)throws IOException {guard();return sink.persist(epoch,tick,level.getGameTime(),lane,payload);}
}
