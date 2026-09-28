package org.kneekura.observer;

import com.google.gson.*;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.*;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.fml.loading.FMLLoader;

import java.io.*;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

/** Opt-in, development-only Forge 1.20.1 observer. Never include in a release MOD. */
@Mod(ForgeObserver.MOD_ID)
public final class ForgeObserver {
    public static final String MOD_ID="kneekura_observer";
    private static final Gson JSON=new GsonBuilder().disableHtmlEscaping().serializeNulls().create();
    private final RunLedger ledger=new RunLedger();
    private final AtomicLong sequence=new AtomicLong();
    private final Deque<JsonObject> events=new ArrayDeque<>();
    private final ConcurrentMap<String,JsonObject> operations=new ConcurrentHashMap<>();
    private MinecraftServer server;
    private BridgeTransport transport;
    private JsonObject session, identity;
    private boolean ready=false;
    private String token;
    private Path directory;

    public ForgeObserver() {
        if (!FMLEnvironment.production && System.getProperty("kneekura.session")!=null)
            MinecraftForge.EVENT_BUS.register(this);
    }

    @SubscribeEvent public void started(ServerStartedEvent event) {
        server=event.getServer();
        try {
            Path file=Path.of(System.getProperty("kneekura.session")).toAbsolutePath().normalize();
            if (Files.isSymbolicLink(file) || Files.size(file)>4*1024*1024) throw new IOException("Invalid session file");
            session=JsonParser.parseString(Files.readString(file)).getAsJsonObject();
            directory=Path.of(session.get("directory").getAsString()).toRealPath();
            if (!file.getParent().toRealPath().equals(directory)) throw new IOException("Wrong session directory");
            // A restart cannot resurrect an old epoch or replay a queued command.
            Files.createFile(directory.resolve(".session-started"));
            token=session.get("token").getAsString();
            identity=session.getAsJsonObject("contract").deepCopy();
            JsonObject expected=session.getAsJsonObject("expected_runtime");
            require(expected.get("minecraft").getAsString().equals(SharedConstants.getCurrentVersion().getName()),"Minecraft version mismatch");
            require(expected.get("forge").getAsString().equals(FMLLoader.versionInfo().forgeVersion()),"Forge version mismatch");
            require(Runtime.version().feature()==17,"Observer requires game JVM17");
            require(identity.get("adapter_id").getAsString().equals("kneekura-forge-observer") && identity.get("adapter_version").getAsString().equals("1.0.0"),"Observer version mismatch");
            String side=FMLEnvironment.dist==Dist.CLIENT?"client":"server";
            require(identity.get("physical_side").getAsString().equals(side),"Physical side mismatch");
            require(identity.get("logical_side").getAsString().equals("server"),"Logical side mismatch");
            require(server.overworld().getSeed()==identity.get("world_seed").getAsLong(),"World seed mismatch");
            Path actualWorld=server.getWorldPath(LevelResource.ROOT).toRealPath();
            require(actualWorld.equals(Path.of(session.get("world").getAsString()).toRealPath()),"Not the prepared test world");
            require(checkConfig().equals(identity.get("config_hash").getAsString()),"Configuration file mismatch");
            verifyBuild();
            if (FMLEnvironment.dist==Dist.CLIENT) Class.forName("org.kneekura.observer.ClientProbe").getMethod("install").invoke(null);
            for (TestFunction test:GameTestRegistry.getAllTestFunctions()) ledger.detect(test.getTestName(),test.isRequired());
            installReporter();
            ready=true;
            transport=new BridgeTransport(token,identity.get("run_id").getAsString(),identity.get("session_epoch").getAsString(),this::request);
            int port=transport.start();
            JsonObject endpoint=new JsonObject(); endpoint.addProperty("url","http://127.0.0.1:"+port);
            endpoint.addProperty("session_epoch",identity.get("session_epoch").getAsString());
            write(directory.resolve("endpoint.json"),JSON.toJson(endpoint));
            log("Observer ready; target class resources verified against compile receipt");
        } catch (Exception failure) {
            ready=false;
            org.slf4j.LoggerFactory.getLogger(MOD_ID).error("KNEEKURA observer not ready: {}",failure.toString());
        }
    }

    private static void require(boolean value,String message) { if (!value) throw new IllegalStateException(message); }
    private static String sha(byte[] bytes) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
    private static String sha(Path path) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try (InputStream in=Files.newInputStream(path)) { byte[] b=new byte[65536]; for (int n;(n=in.read(b))!=-1;) digest.update(b,0,n); }
        return HexFormat.of().formatHex(digest.digest());
    }
    private static JsonElement sorted(JsonElement value) {
        if (value.isJsonObject()) {
            JsonObject out=new JsonObject(); TreeSet<String> keys=new TreeSet<>(value.getAsJsonObject().keySet());
            for(String key:keys) out.add(key,sorted(value.getAsJsonObject().get(key))); return out;
        }
        if (value.isJsonArray()) { JsonArray out=new JsonArray(); for(JsonElement v:value.getAsJsonArray()) out.add(sorted(v)); return out; }
        return value;
    }
    private static String canonical(JsonElement value) { return JSON.toJson(sorted(value)); }
    private String checkConfig() throws Exception {
        JsonArray array=new JsonArray();
        for (JsonElement element:session.getAsJsonArray("config_files")) {
            JsonObject supplied=element.getAsJsonObject(); Path path=Path.of(supplied.get("path").getAsString());
            require(!Files.isSymbolicLink(path),"Config symlink");
            JsonObject file=new JsonObject(); file.addProperty("path",path.toAbsolutePath().normalize().toString().replace('\\','/')); file.addProperty("sha256",sha(path)); array.add(file);
        }
        return sha(canonical(array).getBytes(StandardCharsets.UTF_8));
    }
    private void verifyBuild() throws Exception {
        Path artifact=Path.of(session.get("build_artifact").getAsString()); require(!Files.isSymbolicLink(artifact),"Build artifact symlink");
        String hash;
        if (session.get("build_artifact_kind").getAsString().equals("directory")) {
            JsonArray entries=new JsonArray();
            try (var walk=Files.walk(artifact)) {
                List<Path> files=walk.filter(Files::isRegularFile).sorted(Comparator.comparing(p->artifact.relativize(p).toString().replace('\\','/'))).toList();
                require(files.size()<=50000,"Build artifact too large");
                for (Path file:files) { require(!Files.isSymbolicLink(file),"Build class symlink"); JsonObject item=new JsonObject(); item.addProperty("path",artifact.relativize(file).toString().replace('\\','/')); item.addProperty("hash",sha(file)); entries.add(item); }
            }
            hash=sha(canonical(entries).getBytes(StandardCharsets.UTF_8));
        } else hash=sha(artifact);
        require(hash.equals(identity.get("build_artifact_hash").getAsString()),"Build artifact changed since compilation");
        int checked=0;
        for(JsonElement element:session.getAsJsonArray("class_probes")) {
            JsonObject probe=element.getAsJsonObject(); String resource=probe.get("resource").getAsString();
            try(InputStream stream=getClass().getClassLoader().getResourceAsStream(resource)) {
                require(stream!=null,"Target class resource missing: "+resource); byte[] bytes=stream.readNBytes(16*1024*1024+1);
                require(bytes.length<=16*1024*1024 && sha(bytes).equals(probe.get("sha256").getAsString()),"Stale/wrong-namespace target class: "+resource); checked++;
            }
        }
        require(checked>0,"No target class identity probes");
        // This proves resource bytes, not post-Mixin in-memory instruction identity.
    }

    private void installReporter() throws Exception {
        TestReporter previous=null;
        for (var field:GlobalTestReporter.class.getDeclaredFields()) {
            if (Modifier.isStatic(field.getModifiers()) && TestReporter.class.isAssignableFrom(field.getType())) {
                require(previous==null,"Ambiguous reporter field"); field.setAccessible(true); previous=(TestReporter)field.get(null);
            }
        }
        require(previous!=null,"Cannot preserve the existing GameTest reporter");
        final TestReporter delegate=previous;
        GlobalTestReporter.replaceWith(new TestReporter() {
            @Override public void onTestFailed(GameTestInfo test) {
                ledger.record(test.getTestName(),test.isRequired(),false,String.valueOf(test.getError())); saveReport(); delegate.onTestFailed(test);
            }
            @Override public void onTestSuccess(GameTestInfo test) {
                ledger.record(test.getTestName(),test.isRequired(),true,""); saveReport(); delegate.onTestSuccess(test);
            }
            @Override public void finish() { ledger.complete(); saveReport(); delegate.finish(); }
        });
    }
    private synchronized void saveReport() {
        try {
            JsonObject report=JSON.toJsonTree(ledger.snapshot(Map.of())).getAsJsonObject(); report.add("identity",identity.deepCopy());
            byte[] payload=JSON.toJson(report).getBytes(StandardCharsets.UTF_8); JsonObject signed=new JsonObject();
            signed.addProperty("payload_b64",Base64.getEncoder().encodeToString(payload));
            signed.addProperty("signature",BridgeTransport.sign(token,"gametest-report\n".getBytes(StandardCharsets.UTF_8),payload));
            write(directory.resolve("gametest-report.json"),JSON.toJson(signed));
        } catch(Exception e) { org.slf4j.LoggerFactory.getLogger(MOD_ID).error("Observer report write failed: {}",e.toString()); }
    }
    private static void write(Path path,String content) throws IOException {
        Path temp=Files.createTempFile(path.getParent(),".kneekura-", ".tmp");
        try { Files.writeString(temp,content); Files.move(temp,path,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE); }
        finally { Files.deleteIfExists(temp); }
    }
    private synchronized void log(String text) {
        JsonObject record=new JsonObject(); record.addProperty("sequence",sequence.incrementAndGet()); record.addProperty("text",text);
        record.addProperty("server_tick",server==null?0:server.getTickCount()); events.addLast(record); while(events.size()>256) events.removeFirst();
    }
    private JsonObject base() { JsonObject out=new JsonObject(); out.add("identity",identity.deepCopy()); return out; }
    private JsonObject capture(JsonObject query) {
        JsonObject out=base(); long tick=server.getTickCount(); out.addProperty("server_tick_start",tick); out.addProperty("log_sequence_start",sequence.get());
        int limit=query.has("limit")?query.get("limit").getAsInt():128; require(limit>=1 && limit<=256,"Entity limit out of bounds");
        Set<String> uuids=new HashSet<>(); if(query.has("entity_uuids")) for(JsonElement id:query.getAsJsonArray("entity_uuids")) uuids.add(UUID.fromString(id.getAsString()).toString());
        require(uuids.size()<=256,"Too many entity filters"); String dimension=query.has("dimension")?query.get("dimension").getAsString():null;
        JsonArray entities=new JsonArray(); boolean truncated=false; int scanned=0;
        outer: for(ServerLevel level:server.getAllLevels()) {
            String dim=level.dimension().location().toString(); if(dimension!=null && !dimension.equals(dim)) continue;
            for(Entity entity:level.getAllEntities()) {
                if(++scanned>100000) {truncated=true; break outer;}
                if(!uuids.isEmpty() && !uuids.contains(entity.getUUID().toString())) continue;
                if(entities.size()>=limit) {truncated=true; break outer;}
                JsonObject row=new JsonObject(); row.addProperty("uuid",entity.getUUID().toString()); row.addProperty("dimension",dim);
                row.addProperty("type",BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString());
                row.add("position",JSON.toJsonTree(List.of(entity.getX(),entity.getY(),entity.getZ())));
                var velocity=entity.getDeltaMovement(); row.add("velocity",JSON.toJsonTree(List.of(velocity.x,velocity.y,velocity.z)));
                row.addProperty("health_applicable",entity instanceof LivingEntity);
                if(entity instanceof LivingEntity living) row.addProperty("health",living.getHealth()); else row.add("health",JsonNull.INSTANCE);
                if(entity instanceof Mob mob && mob.getTarget()!=null) row.addProperty("target_uuid",mob.getTarget().getUUID().toString()); else row.add("target_uuid",JsonNull.INSTANCE);
                entities.add(row);
            }
        }
        out.add("entities",entities); out.addProperty("entities_truncated",truncated); out.addProperty("entities_scanned",scanned);
        JsonArray blocks=new JsonArray();
        if(query.has("blocks")) {
            require(query.getAsJsonArray("blocks").size()<=128,"Too many block queries");
            for(JsonElement element:query.getAsJsonArray("blocks")) {
                JsonObject q=element.getAsJsonObject(); JsonObject row=q.deepCopy(); JsonArray xyz=q.getAsJsonArray("position"); require(xyz.size()==3,"Block coordinate required");
                BlockPos pos=new BlockPos(xyz.get(0).getAsInt(),xyz.get(1).getAsInt(),xyz.get(2).getAsInt());
                ServerLevel level=server.getLevel(ResourceKey.create(Registries.DIMENSION,new ResourceLocation(q.get("dimension").getAsString())));
                if(level==null || !level.hasChunkAt(pos)) row.addProperty("unavailable_reason","Dimension/chunk not loaded; no forced generation");
                else { var state=level.getBlockState(pos); row.addProperty("block",BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString()); row.addProperty("state",state.toString()); }
                blocks.add(row);
            }
        }
        out.add("blocks",blocks); out.addProperty("server_tick_end",server.getTickCount()); out.addProperty("log_sequence_end",sequence.get());
        out.add("client_frame_start",JsonNull.INSTANCE); out.add("client_frame_end",JsonNull.INSTANCE); out.addProperty("atomic",false);
        out.addProperty("config_observation","Explicit registered files, not every in-memory Forge config value"); return out;
    }

    private String request(String path,String body,String nonce) throws Exception {
        require(ready,"Observer not ready"); JsonObject query=JsonParser.parseString(body).getAsJsonObject();
        if(path.equals("/v1/handshake")) {
            JsonObject out=base(); out.addProperty("ready",ready); out.addProperty("minecraft",SharedConstants.getCurrentVersion().getName());
            out.addProperty("forge",FMLLoader.versionInfo().forgeVersion()); out.addProperty("java_major",Runtime.version().feature());
            out.addProperty("class_identity_scope","Target resource bytes match build; post-transform memory is not attested");
            out.add("capabilities",JSON.toJsonTree(List.of("entities","blocks","logs","registered_commands","gametest_report",FMLEnvironment.dist==Dist.CLIENT?"client_capture":"server_only")));
            return JSON.toJson(out);
        }
        require(checkConfig().equals(identity.get("config_hash").getAsString()),"Config changed during run");
        if(path.equals("/v1/operation")) {
            String id=query.get("operation_id").getAsString(); JsonObject saved=operations.get(id);
            if(saved==null) {JsonObject out=base(); out.addProperty("request_id",id); out.addProperty("accepted",false); out.addProperty("completed",false); return JSON.toJson(out);}
            return JSON.toJson(saved);
        }
        if(path.equals("/v1/command")) {
            String id=query.get("operation_id").getAsString(), commandId=query.get("command_id").getAsString();
            require(id.matches("[A-Za-z0-9_.-]{1,128}"),"Invalid operation ID");
            JsonObject previous=operations.get(id);
            if(previous!=null) { require(previous.get("command_id").getAsString().equals(commandId),"Operation ID reused"); return JSON.toJson(previous); }
            require(operations.size()<128,"Operation budget exhausted"); JsonObject registry=session.getAsJsonObject("command_registry");
            require(registry.has(commandId),"Command not registered"); String command=registry.get(commandId).getAsString();
            JsonObject accepted=base(); accepted.addProperty("request_id",id); accepted.addProperty("command_id",commandId); accepted.addProperty("accepted",true); accepted.addProperty("completed",false);
            require(operations.putIfAbsent(id,accepted)==null,"Concurrent operation ID");
            // A timeout does not cancel/retry a possibly accepted game-thread mutation.
            return server.submit(()->{
                JsonObject done=accepted.deepCopy();
                try { int code=server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withPermission(2),command); done.addProperty("command_result",code); done.addProperty("success",code>0); }
                catch(Exception failure) { done.addProperty("success",false); done.addProperty("error",failure.getClass().getSimpleName()); }
                done.addProperty("completed",true); done.addProperty("server_tick",server.getTickCount()); operations.put(id,done); log("Registered command completed: "+commandId); return JSON.toJson(done);
            }).get(5,TimeUnit.SECONDS);
        }
        if(path.equals("/v1/logs")) {
            JsonObject out=base(); JsonArray records=new JsonArray(); synchronized(this) {for(JsonObject event:events) records.add(event.deepCopy());}
            out.add("logs",records); out.addProperty("sequence_end",sequence.get()); out.addProperty("retention",256);
            return JSON.toJson(out);
        }
        JsonObject out=server.submit(()->capture(query)).get(5,TimeUnit.SECONDS);
        if(path.equals("/v1/client")) {
            require(FMLEnvironment.dist==Dist.CLIENT,"Client renderer is unavailable on dedicated server");
            @SuppressWarnings("unchecked") CompletableFuture<JsonObject> image=(CompletableFuture<JsonObject>)Class.forName("org.kneekura.observer.ClientProbe").getMethod("capture",Path.class,boolean.class).invoke(null,directory,query.has("screenshot") && query.get("screenshot").getAsBoolean());
            JsonObject client=image.get(10,TimeUnit.SECONDS); for(var entry:client.entrySet()) out.add(entry.getKey(),entry.getValue());
            out.addProperty("server_tick_end",server.submit(()->server.getTickCount()).get(5,TimeUnit.SECONDS));
        }
        return JSON.toJson(out);
    }

    @SubscribeEvent public void tick(TickEvent.ServerTickEvent event) {
        if(ready && event.phase==TickEvent.Phase.END && server.getTickCount()%200==0) log("Server tick "+server.getTickCount());
    }
    @SubscribeEvent public void stopping(ServerStoppingEvent event) {
        if(identity!=null) saveReport(); ready=false; if(transport!=null) transport.close();
    }
}
