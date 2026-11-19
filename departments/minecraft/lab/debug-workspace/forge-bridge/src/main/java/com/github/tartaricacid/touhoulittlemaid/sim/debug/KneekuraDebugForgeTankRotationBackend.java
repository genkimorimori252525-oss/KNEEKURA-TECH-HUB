package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.entity.EntityTypeTest;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraft.world.phys.AABB;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;

/** Source-owned pre-experiment generation; JSON cannot supply the concrete scoped owner gate. */
final class KneekuraDebugForgeTankRotationBackend implements KneekuraDebugTankRotationController.Backend {
    private static final String OWNER_FILE="kneekura-tank-owner.json",ROOT="control/tank-rotation/";
    private final KneekuraDebugEnv.Config config;
    private final MinecraftServer server;
    private final ServerLevel level;
    private final KneekuraDebugOwnerInputs input;
    private final KneekuraDebugScopedOwnerGate gate;
    private final KneekuraDebugTankRotationPlan.Validated validated;
    private final KneekuraDebugArenaController.Snapshot arena;
    private final Path world;
    private String expectedOwnerHash,installationHash,installationFileHash;
    private boolean reservationWritten,finalReceiptWritten;
    private long tick;
    KneekuraDebugForgeTankRotationBackend(KneekuraDebugEnv.Config config, MinecraftServer server, ServerLevel level,
            KneekuraDebugOwnerInputs input, KneekuraDebugScopedOwnerGate gate, KneekuraDebugTankRotationPlan.Validated validated,
            KneekuraDebugArenaController.Snapshot snapshot) throws IOException {
        this.config=config;this.server=server;this.level=level;this.input=input;this.gate=gate;this.validated=validated;this.arena=snapshot;
        world=server.getWorldPath(LevelResource.ROOT).toAbsolutePath().normalize().toRealPath();expectedOwnerHash=validated.previousOwnerHash();
        if(!world.equals(Path.of(KneekuraDebugOwnerInputs.t(input.world(),"canonicalWorldRoot"))) || level!=server.overworld()
                || !snapshot.idle() || snapshot.unsafe())throw new IOException("TANK_ROTATION_NATIVE_CONTEXT_MISMATCH");
        gate.revalidateBoundary();guard();
    }
    void tick(long value){tick=value;}
    void bindInstallationReceipt(String expectedHash)throws IOException{
        if(installationHash!=null)throw new IOException("TANK_ROTATION_INSTALLATION_ALREADY_BOUND");
        byte[] bytes=KneekuraDebugOwnerFiles.read(input.runDir(),"control/owner-installed.json",null,65536);String fileHash=KneekuraDebugOwnerFiles.sha256(bytes);
        JsonObject receipt=KneekuraDebugOwnerFiles.json(input.runDir(),"control/owner-installed.json",fileHash,65536);
        String hash=KneekuraDebugTankRotationPlan.installationReceiptHash(receipt,input.envelopeHash(),input.grant());
        if(!hash.equals(KneekuraDebugActionJournal.hash(expectedHash)))throw new IOException("TANK_ROTATION_INSTALLATION_HASH_MISMATCH");
        installationHash=hash;installationFileHash=fileHash;
    }
    @Override public void guard() throws IOException {
        gate.requireAuthorized(config,server,input.grant());
        if(!arena.equals(KneekuraDebugArenaRuntime.snapshotOwner()))throw new IOException("TANK_ROTATION_ARENA_CONTEXT_CHANGED");
        KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(arena,0);
        KneekuraDebugOwnerFiles.read(world,OWNER_FILE,expectedOwnerHash,65536);
        if(installationFileHash!=null)KneekuraDebugOwnerFiles.read(input.runDir(),"control/owner-installed.json",installationFileHash,65536);
    }
    @Override public void requireQuiet() throws IOException {
        if(!server.isSameThread())throw new IOException("SERVER_THREAD_REQUIRED");
        // 1.20.1 has no nondestructive region enumeration of scheduled ticks: use conservative whole-level counts.
        if(level.getBlockTicks().count()!=0 || level.getFluidTicks().count()!=0)throw new IOException("TANK_ROTATION_SCHEDULED_TICKS_PRESENT");
        var previous=validated.priorRegions().get(validated.priorRegions().size()-1);
        for(var geometry:new KneekuraDebugTankRotationController.Geometry[]{previous,validated.next()}){
            AABB bounds=new AABB(geometry.x()-1,geometry.y()-1,geometry.z()-1,geometry.x()+geometry.width()+1,geometry.y()+geometry.height()+1,geometry.z()+geometry.depth()+1);
            var occupants=new ArrayList<Entity>();level.getEntities(EntityTypeTest.forClass(Entity.class),bounds,e->!(e instanceof Player),occupants,1);
            if(!occupants.isEmpty())throw new IOException("TANK_ROTATION_NONPLAYER_ENTITY_PRESENT");
        }
    }
    private BlockState stateAt(KneekuraDebugTankRotationController.Cell cell)throws IOException{
        BlockPos position=new BlockPos(cell.x(),cell.y(),cell.z());
        if(!level.hasChunkAt(position))throw new IOException("TANK_ROTATION_CHUNK_NOT_LOADED");
        if(level.getBlockEntity(position)!=null)throw new IOException("TANK_ROTATION_BLOCK_ENTITY_PRESENT");
        return level.getBlockState(position);
    }
    @Override public void preflight(KneekuraDebugTankRotationController.Cell cell,boolean interior)throws IOException{
        if(!stateAt(cell).isAir())throw new IOException("TANK_ROTATION_REGION_NOT_EMPTY");
    }
    @Override public void generate(KneekuraDebugTankRotationController.Cell cell,boolean interior)throws IOException{
        if(!reservationWritten)throw new IOException("TANK_ROTATION_RESERVATION_MISSING");
        preflight(cell,interior);
        if(!interior && !level.setBlock(new BlockPos(cell.x(),cell.y(),cell.z()),Blocks.BLACK_CONCRETE.defaultBlockState(),3))throw new IOException("TANK_ROTATION_BLOCK_WRITE_RETURNED_FALSE");
    }
    @Override public String verify(KneekuraDebugTankRotationController.Cell cell,boolean interior)throws IOException{
        BlockState actual=stateAt(cell);String block=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(actual.getBlock()).toString();
        if(!(interior?block.equals("minecraft:air"):block.equals("minecraft:black_concrete")))throw new IOException("TANK_ROTATION_GEOMETRY_MISMATCH");
        return block;
    }
    @Override public void reserve(KneekuraDebugTankRotationController.Plan plan)throws IOException{
        guard();requireQuiet();gate.revalidateBoundary();
        if(installationHash==null)throw new IOException("TANK_ROTATION_INSTALLATION_NOT_BOUND");
        if(reservationWritten)throw new IOException("TANK_ROTATION_RESERVATION_ALREADY_CONSUMED");
        JsonObject reservation=base("native_rotation_reservation","OUTCOME_UNKNOWN");reservation.addProperty("blockMutationsStarted",false);
        reservation.addProperty("noAutomaticReplay",true);reservation.add("plan",validated.intent());
        KneekuraDebugOwnerFiles.writeNew(input.runDir(),ROOT+"native-reservation.json",reservation);reservationWritten=true;
        JsonObject owner=validated.predecessor();owner.addProperty("status","OUTCOME_UNKNOWN");owner.addProperty("baselineVerified",false);
        owner.addProperty("resetFidelity","NOT_ESTABLISHED");owner.addProperty("rotationId",validated.rotationId());owner.add("pendingRecipe",validated.nextRecipe());
        owner.addProperty("pendingRecipeHash","sha256:"+validated.nextRecipeHash());owner.addProperty("sourceOwnerFileSha256",validated.previousOwnerHash());
        expectedOwnerHash=KneekuraDebugOwnerFiles.replaceExpected(world,OWNER_FILE,expectedOwnerHash,owner);
        KneekuraDebugTankPresentation.clear();
    }
    @Override public void publishVerified(KneekuraDebugTankRotationController.Plan plan,String fingerprint)throws IOException{
        guard();requireQuiet();
        if(!server.saveEverything(false,true,true))throw new IOException("TANK_ROTATION_WORLD_SAVE_RETURNED_FALSE");
        guard();requireQuiet();JsonObject owner=base("saved_tank_geometry","GEOMETRY_VERIFIED");
        owner.add("recipe",validated.nextRecipe());owner.addProperty("recipeHash","sha256:"+validated.nextRecipeHash());
        owner.addProperty("displayMode",validated.nextRecipe().getAsJsonObject("presentation").get("mode").getAsString());
        owner.addProperty("arenaEpoch",plan.previousEpoch()+1); // Saved Tank generation; the old experimental Arena counter is separate.
        JsonArray regions=validated.predecessor().has("reservedRegions")?validated.predecessor().getAsJsonArray("reservedRegions").deepCopy():new JsonArray();
        regions.add(validated.predecessor().get("recipe").deepCopy());owner.add("reservedRegions",regions);
        owner.addProperty("volume",plan.next().allocationCells());owner.addProperty("verifiedCells",plan.next().allocationCells());
        owner.addProperty("geometryFingerprint","sha256:"+fingerprint);owner.addProperty("worldSavedAt",Instant.now().toString());
        owner.addProperty("baselineVerified",false);owner.addProperty("resetFidelity","NOT_ESTABLISHED");owner.addProperty("environmentApplied",false);
        owner.addProperty("freshRunAndRecipeRegistrationRequired",true);
        expectedOwnerHash=KneekuraDebugOwnerFiles.replaceExpected(world,OWNER_FILE,expectedOwnerHash,owner);
        guard();JsonObject checkpoint=base("rotation_geometry_checkpoint","GEOMETRY_READBACK_VERIFIED_NOT_TERMINAL");
        checkpoint.addProperty("geometryFingerprint","sha256:"+fingerprint);checkpoint.addProperty("verifiedCells",plan.next().allocationCells());
        checkpoint.addProperty("savedOwnerFileSha256",expectedOwnerHash);checkpoint.addProperty("worldSaveReturned",true);
        String evidence=KneekuraDebugEvidenceWriter.recordArenaObserved(config,arena.arenaEpoch(),tick,level.getGameTime(),"TANK_ROTATION",
                "KneekuraDebugForgeTankRotationBackend.geometry_checkpoint",checkpoint);
        checkpoint.addProperty("durableObservationPayloadHash",evidence);KneekuraDebugOwnerFiles.writeNew(input.runDir(),ROOT+"geometry-checkpoint.json",checkpoint);
    }
    /** Final bookkeeping only after the controller's last authority check and VERIFIED transition. */
    void complete(KneekuraDebugTankRotationController.Snapshot snapshot)throws IOException{
        if(snapshot.phase()!=KneekuraDebugTankRotationController.Phase.VERIFIED || finalReceiptWritten)throw new IOException("TANK_ROTATION_TERMINAL_CONTEXT_MISMATCH");
        JsonObject receipt=outcome(snapshot,"VERIFIED");KneekuraDebugOwnerFiles.read(world,OWNER_FILE,expectedOwnerHash,65536);
        KneekuraDebugOwnerFiles.writeNew(input.runDir(),ROOT+"receipt.json",receipt);finalReceiptWritten=true;
    }
    @Override public void unknown(KneekuraDebugTankRotationController.Snapshot snapshot)throws IOException{
        if(!server.isSameThread() || !world.equals(server.getWorldPath(LevelResource.ROOT).toAbsolutePath().normalize().toRealPath()))throw new IOException("TANK_ROTATION_UNKNOWN_CONTEXT_CHANGED");
        IOException invalidationFailure=null;
        // Revocation invalidates only metadata; it never resumes or rolls back block operations with an expired lease.
        if(reservationWritten)try{
            JsonObject owner=KneekuraDebugOwnerFiles.json(world,OWNER_FILE,expectedOwnerHash,65536);owner.addProperty("status","OUTCOME_UNKNOWN");owner.addProperty("baselineVerified",false);
            owner.addProperty("resetFidelity","NOT_ESTABLISHED");owner.addProperty("rotationId",validated.rotationId());
            expectedOwnerHash=KneekuraDebugOwnerFiles.replaceExpected(world,OWNER_FILE,expectedOwnerHash,owner);
        }catch(IOException failure){invalidationFailure=failure;}
        JsonObject receipt=outcome(snapshot,"OUTCOME_UNKNOWN");receipt.addProperty("ownerMetadataInvalidated",invalidationFailure==null && reservationWritten);
        KneekuraDebugOwnerFiles.writeNew(input.runDir(),ROOT+"outcome-unknown.json",receipt);KneekuraDebugTankPresentation.clear();
        if(invalidationFailure!=null)throw invalidationFailure;
    }
    private JsonObject outcome(KneekuraDebugTankRotationController.Snapshot snapshot,String status)throws IOException{
        JsonObject row=base("tank_rotation_receipt",status);row.addProperty("preflightCells",snapshot.preflightCells());row.addProperty("generationCells",snapshot.generationCells());
        row.addProperty("verifiedCells",snapshot.verifiedCells());row.addProperty("counterScope","NORMALLY_COMPLETED_CELL_DELEGATES_ONLY_NOT_ALL_PARTIAL_WRITES");
        row.addProperty("geometryFingerprint",snapshot.geometryFingerprint());row.addProperty("error",snapshot.error());row.addProperty("savedOwnerFileSha256",expectedOwnerHash);
        row.addProperty("noAutomaticReplay",true);row.addProperty("freshRunAndRecipeRegistrationRequired",true);return row;
    }
    private JsonObject base(String kind,String status)throws IOException{
        JsonObject row=new JsonObject();row.addProperty("schemaVersion",1);row.addProperty("kind",kind);row.addProperty("status",status);
        row.addProperty("scope","TANK_GEOMETRY_ONLY_NOT_RESET_FIDELITY");row.addProperty("rotationId",validated.rotationId());row.addProperty("debugSessionId",config.debugSessionId());
        row.addProperty("runId",config.runId());row.addProperty("runSnapshotId",config.runSnapshotId());row.addProperty("processEpoch",config.processEpoch());
        row.addProperty("requestHash",input.grant().requestHash());row.addProperty("ownerEnvelopeHash",input.envelopeHash());row.addProperty("grantId",input.grant().grantId());
        row.addProperty("ownerInstallationReceiptHash",installationHash);row.addProperty("ownerInstallationFileSha256",installationFileHash);
        row.addProperty("leaseId",input.grant().leaseId());row.addProperty("experimentalArenaEpoch",arena.arenaEpoch());row.addProperty("previousTankEpoch",validated.previousEpoch());
        row.addProperty("nextTankEpoch",validated.previousEpoch()+1);row.addProperty("previousOwnerFileSha256",validated.previousOwnerHash());row.addProperty("nextRecipeHash",validated.nextRecipeHash());
        row.addProperty("materialDescriptorHash",KneekuraDebugOwnerInputs.t(input.envelope(),"materialDescriptorHash"));row.addProperty("worldRegistrationHash",KneekuraDebugOwnerInputs.t(input.envelope(),"worldRegistrationHash"));
        row.addProperty("fullTargetAttestation","NOT_ESTABLISHED");row.addProperty("transformedClassCertainty","NOT_ESTABLISHED");row.addProperty("observedAt",Instant.now().toString());return row;
    }
}
