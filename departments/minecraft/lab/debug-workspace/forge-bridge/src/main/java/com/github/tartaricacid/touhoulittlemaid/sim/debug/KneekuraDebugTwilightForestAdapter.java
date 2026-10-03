package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.control.MoveControl;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.versions.forge.ForgeVersion;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** Pinned ANCHOR cached Boss state. No TF getter, phase setter, AI, sensor or search is replayed. */
final class KneekuraDebugTwilightForestAdapter implements KneekuraDebugDecisionAdapter {
    private static final String PREFIX="twilightforest.entity.boss.";
    private static final Set<String> SUBJECTS=Set.of(PREFIX+"Hydra",PREFIX+"SnowQueen",PREFIX+"KnightPhantom",PREFIX+"UrGhast");
    private Boolean compatible;
    private ClassLoader provenLoader;
    @Override public JsonObject descriptor(){return KneekuraDebugTwilightForestDescriptor.descriptor();}
    @Override public boolean supports(Mob entity){return entity!=null&&SUBJECTS.contains(entity.getClass().getName());}
    @Override public JsonObject describeCapabilities() {
        JsonObject caps=new JsonObject();JsonObject state=new JsonObject(),transitions=new JsonObject();
        state.addProperty("status","NOT_CAPTURED");state.addProperty("detail","SOURCE_COMPATIBLE_SNAPSHOT_REQUIRED");
        transitions.addProperty("status","NOT_EXPOSED");transitions.addProperty("detail","ORIGINAL_MOD_TRANSITIONS_NOT_REGISTERED");
        caps.add("twilightforest:boss_state",state);caps.add("twilightforest:original_transitions",transitions);return caps;
    }
    private boolean compatible(Mob entity) {
        if(compatible!=null&&provenLoader==entity.getClass().getClassLoader())return compatible;
        provenLoader=entity.getClass().getClassLoader();
        compatible=false;
        try {
            JsonObject d=descriptor();
            if(!SharedConstants.getCurrentVersion().getName().equals(d.get("minecraftVersion").getAsString())||
                    !ForgeVersion.getVersion().equals(d.get("loaderVersion").getAsString()))return false;
            var mod=ModList.get().getModContainerById("twilightforest").orElse(null);
            if(mod==null||!mod.getModInfo().getVersion().toString().equals(d.get("modVersion").getAsString()))return false;
            Map<String,String> hashes=new LinkedHashMap<>();
            d.getAsJsonObject("classHashes").entrySet().forEach(e->hashes.put(e.getKey(),e.getValue().getAsString()));
            compatible=KneekuraDebugAdapterSourceProof.verify(mod.getModInfo().getOwningFile().getFile().getFilePath(),
                d.get("mappedArtifactSha256").getAsString(),hashes,owner->{
                    try(var input=entity.getClass().getClassLoader().getResourceAsStream(owner.replace('.','/')+".class")) {
                        return input==null?null:input.readNBytes(KneekuraDebugAdapterSourceProof.MAX_CLASS_BYTES+1);
                    }
                });
        }catch(Exception|LinkageError unavailable){compatible=false;}
        return compatible;
    }
    @Override public JsonObject captureSnapshot(Mob entity,KneekuraDebugDecisionBurstBudget.Context context,Limits limits)throws Exception {
        if(!supports(entity)||!entity.getUUID().toString().equals(context.subjectUuid()))throw new IllegalArgumentException("TF_EXACT_SUBJECT_REQUIRED");
        JsonObject root=new JsonObject();root.add("descriptor",descriptor());
        root.addProperty("compatibilityStatus",compatible(entity)?"MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION":"NOT_EXPOSED_SOURCE_MISMATCH");
        JsonObject data=new JsonObject();root.add("data",data);data.addProperty("status","NOT_EXPOSED");
        if(!compatible)return root;
        data.addProperty("bossKind",entity.getClass().getSimpleName());
        data.addProperty("stateSemantics","CACHED_STATE_NOT_ORIGINAL_TRANSITION_OR_REASON");
        try {
            JsonObject state=switch(entity.getClass().getSimpleName()) {
                case "Hydra" -> hydra(entity,limits);
                case "SnowQueen" -> snow(entity);
                case "KnightPhantom" -> knight(entity);
                case "UrGhast" -> urGhast(entity);
                default -> throw new IllegalArgumentException("TF_SUBJECT_UNSUPPORTED");
            };
            data.add("state",state);data.addProperty("status","AVAILABLE");
        }catch(ReflectiveOperationException|RuntimeException unavailable) {
            data.addProperty("detail",unavailable.getClass().getSimpleName());
        }
        if(root.toString().getBytes(StandardCharsets.UTF_8).length>limits.maxBytes()) {
            data.remove("state");data.addProperty("status","NOT_EXPOSED");data.addProperty("detail","ADAPTER_BYTE_BUDGET");
        }
        return root;
    }
    private JsonObject hydra(Mob mob,Limits limits)throws ReflectiveOperationException {
        Object[] containers=(Object[])read(mob,"hc");
        int count=(Integer)read(mob,"numHeads");
        if(count!=7||containers.length!=7||limits.maxEntries()<7)throw new IllegalStateException("TF_HEAD_BOUNDARY_UNAVAILABLE");
        JsonObject state=new JsonObject();JsonArray heads=new JsonArray();state.add("heads",heads);
        state.addProperty("numHeads",count);state.addProperty("scope","SELECTED_COORDINATOR_STORED_HEAD_CONTAINERS");
        for(Object container:containers) {
            if(container==null||!container.getClass().getName().equals(PREFIX+"HydraHeadContainer")||read(container,"hydra")!=mob)
                throw new IllegalStateException("TF_HEAD_OWNER_MISMATCH");
            JsonObject head=new JsonObject();head.addProperty("headNum",(Integer)read(container,"headNum"));
            head.addProperty("prevState",enumName(read(container,"prevState")));
            head.addProperty("currentState",enumName(read(container,"currentState")));
            Object next=read(container,"nextState");head.addProperty("nextState",next==null?null:enumName(next));
            head.addProperty("nextStateSemantics",next==null?"AUTOMATIC_SENTINEL":"STORED_REQUESTED_STATE");
            head.addProperty("ticksNeeded",(Integer)read(container,"ticksNeeded"));head.addProperty("ticksProgress",(Integer)read(container,"ticksProgress"));
            uuid(head,"targetUuid",read(container,"targetEntity"));uuid(head,"headUuid",read(container,"headEntity"));heads.add(head);
        }
        return state;
    }
    private JsonObject snow(Mob mob)throws ReflectiveOperationException {
        JsonObject state=new JsonObject();int phase=(Byte)synched(mob,"PHASE_FLAG");
        if(phase<0||phase>2)throw new IllegalStateException("TF_PHASE_UNAVAILABLE");
        state.addProperty("phase",new String[]{"SUMMON","DROP","BEAM"}[phase]);state.addProperty("beamActive",(Boolean)synched(mob,"BEAM_FLAG"));
        for(String key:new String[]{"summonsRemaining","successfulDrops","maxDrops","damageWhileBeaming"})state.addProperty(key,(Integer)read(mob,key));
        return state;
    }
    private JsonObject knight(Mob mob)throws ReflectiveOperationException {
        JsonObject state=new JsonObject();state.addProperty("number",(Integer)read(mob,"number"));
        state.addProperty("ticksProgress",(Integer)read(mob,"ticksProgress"));state.addProperty("currentFormation",enumName(read(mob,"currentFormation")));
        Object position=read(mob,"chargePos");
        if(position!=null&&position.getClass()==BlockPos.class) {
            BlockPos pos=(BlockPos)position;JsonObject point=new JsonObject();point.addProperty("x",pos.getX());point.addProperty("y",pos.getY());point.addProperty("z",pos.getZ());state.add("chargePos",point);
        }else state.addProperty("chargePosStatus","NOT_EXPOSED");
        state.addProperty("groupIdentityStatus","NOT_EXPOSED");state.addProperty("leaderStatus","NOT_EXPOSED");return state;
    }
    private JsonObject urGhast(Mob mob)throws ReflectiveOperationException {
        JsonObject state=new JsonObject();state.addProperty("inTantrum",(Boolean)synched(mob,"DATA_TANTRUM"));
        float damage=(Float)read(mob,"damageUntilNextPhase");if(!Float.isFinite(damage))throw new IllegalStateException("TF_DAMAGE_COUNTER_UNAVAILABLE");
        state.addProperty("damageUntilNextPhase",damage);state.addProperty("nextTantrumCry",(Integer)read(mob,"nextTantrumCry"));
        Class<?> parent=Class.forName("twilightforest.entity.monster.CarminiteGhastguard",false,mob.getClass().getClassLoader());
        float wander=(Float)KneekuraDebugDecisionSnapshot.read(parent,"wanderFactor",mob);
        if(!Float.isFinite(wander))throw new IllegalStateException("TF_WANDER_COUNTER_UNAVAILABLE");state.addProperty("wanderFactor",wander);
        Object control=KneekuraDebugDecisionSnapshot.read(Mob.class,"moveControl",mob);
        JsonObject flight=new JsonObject();flight.addProperty("controllerClass",control.getClass().getName());
        flight.addProperty("candidatePopulationStatus","NOT_EXPOSED");flight.addProperty("aStarExplanationStatus","NOT_EXPOSED");
        if(!control.getClass().getName().equals("twilightforest.entity.ai.control.NoClipMoveControl")||read(control,"parentEntity")!=mob)
            throw new IllegalStateException("TF_CUSTOM_FLIGHT_OWNER_MISMATCH");
        flight.addProperty("courseChangeCooldown",(Integer)read(control,"courseChangeCooldown"));
        flight.addProperty("operation",enumName(KneekuraDebugDecisionSnapshot.read(MoveControl.class,"operation",control)));
        for(String key:new String[]{"wantedX","wantedY","wantedZ","speedModifier"}) {
            double value=(Double)KneekuraDebugDecisionSnapshot.read(MoveControl.class,key,control);
            if(!Double.isFinite(value))throw new IllegalStateException("TF_FLIGHT_VALUE_UNAVAILABLE");flight.addProperty(key,value);
        }
        state.add("customFlight",flight);return state;
    }
    private Object synched(Mob mob,String field)throws ReflectiveOperationException {
        Object data=KneekuraDebugDecisionSnapshot.read(Entity.class,"entityData",mob);
        if(data.getClass()!=SynchedEntityData.class)throw new IllegalStateException("CUSTOM_SYNCHED_DATA_UNSUPPORTED");
        Object accessor=KneekuraDebugDecisionSnapshot.read(mob.getClass(),field,null);
        if(accessor.getClass()!=EntityDataAccessor.class)throw new IllegalStateException("CUSTOM_DATA_ACCESSOR_UNSUPPORTED");
        return KneekuraDebugSynchedCached.read(data,accessor);
    }
    private static Object read(Object owner,String field)throws ReflectiveOperationException{return KneekuraDebugDecisionSnapshot.read(owner.getClass(),field,owner);}
    private static String enumName(Object value){if(!(value instanceof Enum<?> e))throw new IllegalStateException("TF_ENUM_UNAVAILABLE");return e.name();}
    private static void uuid(JsonObject out,String key,Object value)throws ReflectiveOperationException {
        if(value==null){out.addProperty(key,(String)null);return;}
        if(!(value instanceof Entity))throw new IllegalStateException("TF_ENTITY_REFERENCE_UNAVAILABLE");
        out.addProperty(key,((java.util.UUID)KneekuraDebugDecisionSnapshot.read(Entity.class,"uuid",value)).toString());
    }
}
