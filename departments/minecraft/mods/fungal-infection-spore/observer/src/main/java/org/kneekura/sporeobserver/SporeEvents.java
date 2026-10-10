package org.kneekura.sporeobserver;

import org.kneekura.sporeobserver.core.TraceSink;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.entity.EntityLeaveLevelEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.ModList;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/**
 * Passive observer; does not spawn mobs, move entities, modify chunks, or make
 * any claims about uninstrumented internal method calls. Never run on a live world.
 * A LAB session marker is necessary but not sufficient to attest authority.
 */
public final class SporeEvents {
    private static final String SHA = "d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489";
    private static final String PREFIX = "kneekura.spore.observe.";
    private static final int MAX_TRACKED = 4096;
    private final Map<UUID, WeakReference<Entity>> loaded = new LinkedHashMap<>();
    private TraceSink out;
    private Class<?> protoClass, infectedClass, vigilClass, calamityClass, wombClass;
    private Method protoGetSignal, signalActive, signalPos;
    private Method infectedSearchPos, infectedFollowPartner, calamitySearchArea;
    private String scenario, dimension;
    private long startTick, stopAfter, startedNanos;
    private boolean stopped;

    private static String property(String key) {
        String v = System.getProperty(PREFIX + key);
        TraceSink.require(v != null && !v.isBlank(), "missing property: " + key);
        return v;
    }

    private static String labelledId(String text) {
        TraceSink.require(text.matches("[A-Za-z0-9._-]{1,80}"), "unsafe label");
        return text;
    }

    @SubscribeEvent public void onServerStarted(ServerStartedEvent event) {
        // Errors are recorded to server stderr and disable the recorder. Never
        // accidentally run on a private save if an identity check fails.
        if (stopped) return;
        try {
            MinecraftServer server = event.getServer();
            TraceSink.require(server.isDedicatedServer(), "Dedicated server only");
            ServerLevel overworld = server.overworld();
            TraceSink.require(overworld != null, "missing overworld");
            scenario = property("scenario");
            TraceSink.require(List.of("G09","G10","G11","G12","G13").contains(scenario), "unsupported scenario");
            String run = labelledId(property("runId"));
            long expectedSeed = Long.parseLong(property("seed"));
            TraceSink.require(overworld.getSeed() == expectedSeed, "world seed mismatch");
            stopAfter = Long.parseLong(property("durationTicks"));
            TraceSink.require(stopAfter >= 20 && stopAfter <= 10000, "duration outside approved range");
            Path session = Path.of(property("sessionDirectory")).toRealPath();
            Path world = Path.of(property("expectedWorld")).toRealPath();
            Path observedWorld = server.getWorldPath(LevelResource.ROOT).toRealPath();
            TraceSink.require(Files.isDirectory(session) && !Files.isSymbolicLink(session), "invalid session directory");
            TraceSink.require(world.equals(observedWorld), "not the specified prepared world");
            TraceSink.require(!world.equals(session), "session directory cannot be game world");
            // Matching file paths and marker presence are a safety precondition,
            // not an authentication of the LAB registry or owner authorization.
            TraceSink.require(ModList.get().isLoaded("spore"), "Spore not loaded");
            var info = ModList.get().getModFileById("spore");
            TraceSink.require(info != null && info.getFile() != null, "Spore file identity unavailable");
            Path loadedJar = info.getFile().getFilePath().toRealPath();
            TraceSink.require(Files.isRegularFile(loadedJar) && !Files.isSymbolicLink(loadedJar), "Spore is not an immutable JAR path");
            TraceSink.require(sha256(loadedJar).equals(SHA), "Loaded Spore JAR differs from research artifact");

            protoClass = Class.forName("com.Harbinger.Spore.Sentities.Organoids.Proto", false, getClass().getClassLoader());
            infectedClass = Class.forName("com.Harbinger.Spore.Sentities.BaseEntities.Infected", false, getClass().getClassLoader());
            vigilClass = Class.forName("com.Harbinger.Spore.Sentities.Organoids.Vigil", false, getClass().getClassLoader());
            calamityClass = Class.forName("com.Harbinger.Spore.Sentities.BaseEntities.Calamity", false, getClass().getClassLoader());
            wombClass = Class.forName("com.Harbinger.Spore.Sentities.Organoids.Womb", false, getClass().getClassLoader());
            Class<?> signalClass = Class.forName("com.Harbinger.Spore.Sentities.Signal", false, getClass().getClassLoader());
            protoGetSignal=protoClass.getMethod("getSignal");
            signalActive=signalClass.getMethod("active");
            signalPos=signalClass.getMethod("pos");
            infectedSearchPos=infectedClass.getMethod("getSearchPos");
            infectedFollowPartner=infectedClass.getMethod("getFollowPartner");
            calamitySearchArea=calamityClass.getMethod("getSearchArea");
            dimension = overworld.dimension().location().toString();
            startTick = overworld.getGameTime();
            String worldId=labelledId(property("worldId"));
            verifyLabClaims(session,world,run,worldId,expectedSeed);
            Map<String,Object> meta=new LinkedHashMap<>();
            meta.put("ch","spore_meta"); meta.put("schema","kneekura.spore.observation.v1");
            meta.put("run_id",run); meta.put("scenario",scenario); meta.put("jar_sha256",SHA);
            meta.put("minecraft","1.20.1"); meta.put("loader","Forge");
            meta.put("seed",expectedSeed); meta.put("world_id",worldId);
            meta.put("dimension",dimension); meta.put("world_disposable",true);
            meta.put("origin","runtime_claim_unattested"); meta.put("physical_side","DEDICATED_SERVER");
            meta.put("observer_identity","kneekura_spore_observer_source_v0_1_not_runtime_attested");
            Path path=session.resolve(run+".spore.jsonl");
            out=new TraceSink(path,meta); // CREATE_NEW; cannot overwrite another run.
            for (Entity e:overworld.getAllEntities()) track(e);
            System.out.println("[kneekura-spore-observer] PASSIVE ONLY, run="+run+", trace="+path);
        } catch (Exception failure) { disable(failure); }
    }

    @SubscribeEvent public void onJoin(EntityJoinLevelEvent event) {
        if (out == null || !(event.getLevel() instanceof ServerLevel level)) return;
        if (!level.dimension().location().toString().equals(dimension)) return;
        try {
            Entity e=event.getEntity();
            track(e);
            if (protoClass.isInstance(e)||vigilClass.isInstance(e)||wombClass.isInstance(e)) {
                out.event(level.getGameTime(),dimension,"entity_join_snapshot",
                        Map.of("uuid",e.getUUID().toString(),"kind",e.getClass().getSimpleName(),"entity_id",e.getId()));
            }
        } catch (Exception failure) { disable(failure); }
    }

    @SubscribeEvent public void onLeave(EntityLeaveLevelEvent event) {
        if (out == null || !(event.getLevel() instanceof ServerLevel level)) return;
        if (!level.dimension().location().toString().equals(dimension)) return;
        Entity e=event.getEntity();
        loaded.remove(e.getUUID());
        if (protoClass.isInstance(e)||vigilClass.isInstance(e)) {
            try {out.event(level.getGameTime(),dimension,"entity_leave_snapshot",
                    Map.of("uuid",e.getUUID().toString(),"kind",e.getClass().getSimpleName()));}
            catch (Exception failure) {disable(failure);}
        }
    }

    private void track(Entity e) {
        if (protoClass.isInstance(e)||infectedClass.isInstance(e)||vigilClass.isInstance(e)||calamityClass.isInstance(e)||wombClass.isInstance(e)) {
            TraceSink.require(loaded.size()<MAX_TRACKED || loaded.containsKey(e.getUUID()), "tracked entity budget exceeded");
            loaded.put(e.getUUID(),new WeakReference<>(e));
        }
    }

    @SubscribeEvent public void onServerTick(TickEvent.ServerTickEvent event) {
        if (out==null || stopped) return;
        if (event.phase==TickEvent.Phase.START) {startedNanos=System.nanoTime();return;}
        if (event.phase!=TickEvent.Phase.END) return;
        try {
            var world=event.getServer().overworld();
            long tick=world.getGameTime();
            if (tick - startTick >= stopAfter) { stop("completed");return; }
            long elapsed=System.nanoTime()-startedNanos;
            if (elapsed<0) throw new IllegalStateException("negative monotonic interval");
            if (scenario.equals("G13")) sampleG13(world,tick,elapsed/1_000_000.0);
            else if (scenario.equals("G09")||scenario.equals("G10")) {
                if ((tick-startTick)%20==0) sampleSignals(tick);
            }
            else if (scenario.equals("G12") && (tick - startTick)%20==0) sampleMovement(tick);
            // G11 sees only entity joins/leaves. Method-level award/penalty
            // calls are unobservable from passive Forge events; keep INCONCLUSIVE.
        } catch (Exception failure) { disable(failure); }
    }

    /** Cross-check limited LAB session identity, never a substitute for registry attestation. */
    private static void verifyLabClaims(Path directory, Path world, String run, String worldId, long seed) throws Exception {
        Path session=directory.resolve("session.json");
        Path marker=directory.resolve(".kneekura-run.json");
        TraceSink.require(Files.isRegularFile(session,LinkOption.NOFOLLOW_LINKS)
                && Files.size(session)<=4_000_000, "missing/oversized LAB session");
        TraceSink.require(Files.isRegularFile(marker,LinkOption.NOFOLLOW_LINKS)
                && Files.size(marker)<=64_000, "missing/oversized LAB owned-world marker");
        JsonObject s=JsonParser.parseString(Files.readString(session,StandardCharsets.UTF_8)).getAsJsonObject();
        JsonObject m=JsonParser.parseString(Files.readString(marker,StandardCharsets.UTF_8)).getAsJsonObject();
        JsonObject contract=s.getAsJsonObject("contract");
        TraceSink.require(contract!=null, "missing LAB contract");
        TraceSink.require(Path.of(s.get("directory").getAsString()).toRealPath().equals(directory), "session directory mismatch");
        TraceSink.require(Path.of(m.get("directory").getAsString()).toRealPath().equals(directory), "marker directory mismatch");
        TraceSink.require(Path.of(s.get("world").getAsString()).toRealPath().equals(world), "session world mismatch");
        TraceSink.require(Path.of(m.get("world").getAsString()).toRealPath().equals(world), "marker world mismatch");
        TraceSink.require(run.equals(contract.get("run_id").getAsString()), "run mismatch");
        TraceSink.require(worldId.equals(contract.get("world_id").getAsString())
                && worldId.equals(m.get("world_id").getAsString()), "world ID mismatch");
        TraceSink.require(seed==contract.get("world_seed").getAsLong(), "contract seed mismatch");
        TraceSink.require("dedicated_server".equals(contract.get("session_role").getAsString())
                && "server".equals(contract.get("physical_side").getAsString()), "LAB role mismatch");
        TraceSink.require(!m.get("fresh").getAsBoolean(), "LAB world marker not consumed");
        // Authenticated run, actual prepared-world ancestry, and cleanup remain LAB's responsibility.
    }

    private void sampleG13(ServerLevel world, long tick, double tickMs) throws Exception {
        int protos=0,infected=0,signals=0;
        Iterator<Map.Entry<UUID,WeakReference<Entity>>> it=loaded.entrySet().iterator();
        while(it.hasNext()) {
            Entity e=it.next().getValue().get();
            if(e==null || e.isRemoved()) {it.remove();continue;}
            if(protoClass.isInstance(e)) {
                protos++;
                Object signal=protoGetSignal.invoke(e);
                if(signal!=null && Boolean.TRUE.equals(signalActive.invoke(signal))) signals++;
            }
            if(infectedClass.isInstance(e)) infected++;
        }
        out.event(tick,dimension,"server_tick_sample",
                Map.of("proto_count",protos,"infected_count",infected,"signal_count",signals,"tick_ms",tickMs,
                       "measurement_scope","SERVER_TICK_EVENT_BRACKET_UNCALIBRATED",
                       "loaded_chunks",world.getChunkSource().getLoadedChunksCount(),
                       "vanilla_forced_chunks_only",world.getForcedChunks().size()));
    }

    private void sampleSignals(long tick) throws Exception {
        for (WeakReference<Entity> ref:loaded.values()) {
            Entity e=ref.get();
            if(e==null || e.isRemoved()) continue;
            if(scenario.equals("G10") && calamityClass.isInstance(e)) {
                Object search=calamitySearchArea.invoke(e);
                if(search instanceof BlockPos loc) {
                    out.event(tick,dimension,"calamity_search_snapshot",Map.of(
                            "calamity_uuid",e.getUUID().toString(),"unassigned",loc.equals(BlockPos.ZERO),
                            "capture_scope","PASSIVE_NOT_REDIRECT_CALL"));
                }
            }
            if(!protoClass.isInstance(e)) continue;
            Object signal=protoGetSignal.invoke(e);
            if(signal==null || !Boolean.TRUE.equals(signalActive.invoke(signal))) continue;
            BlockPos pos=(BlockPos)signalPos.invoke(signal);
            if(pos==null) continue;
            out.event(tick,dimension,"proto_signal_snapshot",
                    Map.of("proto_uuid",e.getUUID().toString(),"signal_pos",List.of(pos.getX(),pos.getY(),pos.getZ()),
                           "capture_scope","PASSIVE_AFTER_TICK_NOT_DISPATCH_CALL"));
        }
    }

    private void sampleMovement(long tick) throws Exception {
        int n=0;
        for (WeakReference<Entity> ref:loaded.values()) {
            Entity e=ref.get();
            if(e==null || e.isRemoved() || !infectedClass.isInstance(e)) continue;
            if(++n>1000)break;
            BlockPos pos=(BlockPos)infectedSearchPos.invoke(e);
            if(pos!=null) {
                double dist=Math.sqrt(e.distanceToSqr(pos.getX()+0.5,pos.getY()+0.5,pos.getZ()+0.5));
                out.event(tick,dimension,"search_pos_snapshot",Map.of("unit_uuid",e.getUUID().toString(),"distance_to_block_center",dist,
                        "capture_scope","PASSIVE_NO_GOAL_INVOCATION"));
            }
            Object follow=infectedFollowPartner.invoke(e);
            if (follow instanceof Entity leader) {
                out.event(tick,dimension,"follow_partner_snapshot",Map.of("unit_uuid",e.getUUID().toString(),
                        "leader_uuid",leader.getUUID().toString(),"distance_sq",e.distanceToSqr(leader),
                        "capture_scope","PASSIVE_NO_GOAL_INVOCATION"));
            }
        }
    }

    @SubscribeEvent public void onStop(ServerStoppingEvent event) {
        stop("aborted");
    }

    private void stop(String reason) {
        if (out==null) return;
        try {out.finish(reason);} catch (Exception e) {System.err.println("[kneekura-spore-observer] failed end marker: "+e);}
        finally {out=null;loaded.clear();stopped=true;}
    }

    private void disable(Exception failure) {
        System.err.println("[kneekura-spore-observer] STOP (never a runtime PASS): "+failure);
        stop("error");stopped=true;
    }

    private static String sha256(Path path) throws Exception {
        MessageDigest sha=MessageDigest.getInstance("SHA-256");
        try (var stream=Files.newInputStream(path)) {
            byte[] b=new byte[1<<20];int n;
            while((n=stream.read(b))>=0)if(n>0)sha.update(b,0,n);
        }
        return java.util.HexFormat.of().formatHex(sha.digest());
    }
}
