package org.kneekura.observer;

import com.google.gson.*;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import java.security.MessageDigest;
import java.util.*;

/** Fixed, read-only U04 dispatcher/resource observation; never a draw-call or visibility witness. */
public final class U04HydraProbe {
    private static final Gson JSON=new GsonBuilder().disableHtmlEscaping().serializeNulls().create();
    private static final String ARCHIVE="twilightforest-1.20.1-4.3.2508-tiny-remapper-0.11.2-mojmap.jar";
    private static final String ARTIFACT="69e27b79067a9ce3bff3da18abd7b09b1ef4bc99625c07ea0c09424712df72bb";
    private static final String PROVIDER="c005d50d88496d977b9afea730ba0bd585f076cd04a67251381b384127d0243c";
    private static final String ENTITY="twilightforest.entity.boss.Hydra";
    private static final String RENDERER="twilightforest.client.renderer.entity.HydraRenderer";
    private static final String TEXTURE="twilightforest:textures/model/hydra4.png";
    private static final int TEXTURE_LIMIT=1024*1024, IMAGE_LIMIT=8*1024*1024;
    private U04HydraProbe() {}
    private static void require(boolean value,String reason) {if(!value)throw new IllegalArgumentException(reason);}
    private static String string(JsonObject o,String key) {
        JsonElement e=o.get(key);require(e!=null && e.isJsonPrimitive() && e.getAsJsonPrimitive().isString(),"string:"+key);return e.getAsString();
    }
    private static long integer(JsonObject o,String key,long max) {
        JsonElement e=o.get(key);require(e!=null && e.isJsonPrimitive() && e.getAsJsonPrimitive().isNumber() && e.getAsString().matches("0|[1-9][0-9]*"),"integer:"+key);
        long n=Long.parseLong(e.getAsString());require(n<=max,"bound:"+key);return n;
    }
    private static void number(JsonObject o,String key) {
        JsonElement e=o.get(key);require(e!=null && e.isJsonPrimitive() && e.getAsJsonPrimitive().isNumber() && Double.isFinite(e.getAsDouble()),"number:"+key);
    }
    private static String hash(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    private static JsonElement sorted(JsonElement v) {
        if(v.isJsonObject()){JsonObject o=new JsonObject();for(String k:new TreeSet<>(v.getAsJsonObject().keySet()))o.add(k,sorted(v.getAsJsonObject().get(k)));return o;}
        if(v.isJsonArray()){JsonArray a=new JsonArray();for(JsonElement e:v.getAsJsonArray())a.add(sorted(e));return a;}return v;
    }
    private static String selection(JsonObject session) throws Exception {
        JsonObject identity=session.getAsJsonObject("contract"),target=session.getAsJsonObject("target_selection");
        require(integer(identity,"schema_version",3)==3 && string(identity,"session_role").equals("integrated_client"),"role");
        require(string(identity,"physical_side").equals("client") && string(identity,"logical_side").equals("server"),"sides");
        require(string(identity,"runtime_scope").equals("TARGET_CODE_AND_DEPENDENCY_BYTES"),"scope");
        require(target.keySet().equals(Set.of("schema_version","kind","coordinate","sha256","provider_receipt_hash","class_resources")),"target fields");
        require(integer(target,"schema_version",1)==1 && string(target,"kind").equals("u04_hydra_derived_dependency"),"target kind");
        require(string(target,"coordinate").equals(ARCHIVE) && string(target,"sha256").equals(ARTIFACT) && string(target,"provider_receipt_hash").equals(PROVIDER),"target identity");
        JsonArray resources=target.getAsJsonArray("class_resources");require(resources.size()>=2 && resources.size()<=32,"class bound");
        Set<String> names=new HashSet<>();for(JsonElement e:resources){require(e.isJsonPrimitive() && e.getAsJsonPrimitive().isString(),"class resource");require(names.add(e.getAsString()),"duplicate class");}
        require(names.contains(ENTITY.replace('.','/')+".class") && names.contains(RENDERER.replace('.','/')+".class"),"required classes");
        String h=hash(JSON.toJson(sorted(target)).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        require(h.equals(string(identity,"target_selection_hash")),"selection binding");return h;
    }
    private static JsonObject frame(JsonObject query,JsonObject input) throws Exception {
        JsonElement requested=query.get("screenshot");require(requested!=null && requested.isJsonPrimitive() && requested.getAsJsonPrimitive().isBoolean() && requested.getAsBoolean(),"screenshot required");
        String encoded=string(input,"png_b64");require(encoded.length()<=4*((IMAGE_LIMIT+2)/3),"image bound");
        byte[] bytes=Base64.getDecoder().decode(encoded);require(bytes.length>0 && bytes.length<=IMAGE_LIMIT,"image bound");
        require(hash(bytes).equals(string(input,"png_sha256")),"image hash");
        long start=integer(input,"client_frame_start",Long.MAX_VALUE),end=integer(input,"client_frame_end",Long.MAX_VALUE);
        require(start==end,"frame changed");
        require(integer(input,"width",8192)>0 && integer(input,"height",8192)>0,"image dimensions");
        JsonObject camera=input.getAsJsonObject("camera");for(String key:List.of("x","y","z","pitch","yaw"))number(camera,key);
        JsonObject out=new JsonObject();for(String key:List.of("png_sha256","width","height","client_frame_start","client_frame_end"))out.add(key,input.get(key).deepCopy());
        out.add("camera",camera.deepCopy());return out;
    }
    /** Called on the client thread only, after the existing route has captured its screenshot. */
    public static JsonObject capture(Minecraft client,JsonObject session,JsonObject query,JsonObject completedFrame) {
        JsonObject out=new JsonObject();out.addProperty("schema_version",1);out.addProperty("supported",false);out.addProperty("status","UNSUPPORTED");
        String selectionHash;
        try {selectionHash=selection(session);}catch(Exception unavailable){out.addProperty("reason","Exact U04 integrated selection unavailable");return out;}
        out.addProperty("supported",true);out.addProperty("status","UNKNOWN");out.addProperty("target_selection_hash",selectionHash);
        out.addProperty("atomic",false);out.addProperty("visibility","NOT_ESTABLISHED");
        out.addProperty("renderer_evidence","DISPATCHER_SELECTION_NOT_DRAW_CALL_ATTESTATION");
        try {
            require(client!=null && client.isSameThread(),"client thread required");
            require(Set.of("entity_uuids","dimension","limit","screenshot").containsAll(query.keySet()),"unsupported query");
            JsonArray ids=query.getAsJsonArray("entity_uuids");require(ids.size()==1 && ids.get(0).isJsonPrimitive() && ids.get(0).getAsJsonPrimitive().isString(),"one UUID required");
            String id=ids.get(0).getAsString();require(UUID.fromString(id).toString().equals(id),"canonical UUID required");
            require(integer(query,"limit",1)==1,"exact entity limit");String dimension=string(query,"dimension");
            JsonObject binding=frame(query,completedFrame);
            if(client.level==null){out.addProperty("status","UNAVAILABLE");out.addProperty("reason","Client level unavailable");return out;}
            require(client.level.dimension().location().toString().equals(dimension),"client dimension mismatch");
            Entity selected=null;int scanned=0;
            for(Entity entity:client.level.entitiesForRendering()) {
                require(++scanned<=100000,"entity scan bound");
                if(entity.getUUID().toString().equals(id)){selected=entity;break;}
            }
            if(selected==null){out.addProperty("status","UNAVAILABLE");out.addProperty("reason","Selected UUID absent from client level");return out;}
            require(ENTITY.equals(selected.getClass().getName()) && selected instanceof LivingEntity,"selected class mismatch");
            String type=BuiltInRegistries.ENTITY_TYPE.getKey(selected.getType()).toString();require(type.equals("twilightforest:hydra"),"selected type mismatch");
            var renderer=client.getEntityRenderDispatcher().getRenderer(selected);
            require(renderer!=null && RENDERER.equals(renderer.getClass().getName()),"default renderer mismatch");
            var resourceManager=client.getResourceManager();boolean marker=resourceManager.getResource(new ResourceLocation("twilightforest:jappa_models.marker")).isPresent();
            out.addProperty("jappa_marker_present",marker);require(!marker,"JAPPA marker present; default branch unavailable");
            ResourceLocation texture=renderer.getTextureLocation(selected);require(texture!=null && TEXTURE.equals(texture.toString()),"texture location mismatch");
            var resource=resourceManager.getResource(texture);require(resource.isPresent(),"texture resource unavailable");
            byte[] textureBytes;try(var stream=resource.get().open()){textureBytes=stream.readNBytes(TEXTURE_LIMIT+1);}
            require(textureBytes.length>0 && textureBytes.length<=TEXTURE_LIMIT,"texture resource bound");
            String pack=resource.get().sourcePackId();require(pack!=null && pack.length()<=256,"resource source bound");
            JsonObject pose=new JsonObject();pose.addProperty("x",selected.getX());pose.addProperty("y",selected.getY());pose.addProperty("z",selected.getZ());
            pose.addProperty("pitch",selected.getXRot());pose.addProperty("yaw",selected.getYRot());
            pose.addProperty("body_yaw",((LivingEntity)selected).yBodyRot);pose.addProperty("head_yaw",((LivingEntity)selected).yHeadRot);
            for(String key:List.of("x","y","z","pitch","yaw","body_yaw","head_yaw"))number(pose,key);
            pose.addProperty("pose",selected.getPose().toString());pose.addProperty("entity_tick",selected.tickCount);
            out.addProperty("entity_uuid",id);out.addProperty("entity_type",type);out.addProperty("entity_class",selected.getClass().getName());
            out.addProperty("dimension",dimension);out.addProperty("renderer_class",renderer.getClass().getName());
            out.addProperty("texture_location",texture.toString());out.addProperty("texture_sha256",hash(textureBytes));out.addProperty("texture_source_pack",pack);
            out.add("entity_pose",pose);out.add("frame",binding);out.addProperty("status","CAPTURED");
            out.addProperty("timing","Client-thread pose sampled with captured framebuffer; not an atomic pose-to-draw assertion");
        } catch(Exception | LinkageError unavailable) {
            out.addProperty("status","UNKNOWN");out.addProperty("reason","Required U04 observation unavailable or mismatched: "+unavailable.getClass().getSimpleName());
        }
        return out;
    }
}
