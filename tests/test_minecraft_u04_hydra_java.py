"""Inert API fixtures test the narrow probe; these are not live rendering tests."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
import pytest
JAVA=Path(__file__).resolve().parents[1]/'departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer'
UUID='00000000-0000-4000-8000-000000000004'

def test_u04_hydra_probe_exists():
    assert (JAVA/'U04HydraProbe.java').is_file(),'Missing fixed U04 renderer observation helper'

@pytest.fixture(scope='module')
def probe(tmp_path_factory):
    if not (JAVA/'U04HydraProbe.java').is_file():pytest.skip('Missing implementation reported separately')
    gson=os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file():pytest.skip('Explicit cached Gson required')
    root=tmp_path_factory.mktemp('u04-hydra-java')
    sources={
    'net/minecraft/resources/ResourceLocation.java':'package net.minecraft.resources;public record ResourceLocation(String value){public String toString(){return value;}}',
    'net/minecraft/resources/ResourceKey.java':'package net.minecraft.resources;public record ResourceKey(ResourceLocation location){}',
    'net/minecraft/world/entity/Entity.java':'''package net.minecraft.world.entity;import java.util.*;public class Entity {public UUID id=UUID.fromString("'''+UUID+'''");public String type="twilightforest:hydra";public int tickCount=41;public UUID getUUID(){return id;}public Object getType(){return type;}public double getX(){return 1;}public double getY(){return 65;}public double getZ(){return 3;}public float getXRot(){return 4;}public float getYRot(){return 5;}public Object getPose(){return "STANDING";}}''',
    'net/minecraft/world/entity/LivingEntity.java':'package net.minecraft.world.entity;public class LivingEntity extends Entity{public float yBodyRot=6,yHeadRot=7;}',
    'twilightforest/entity/boss/Hydra.java':'package twilightforest.entity.boss;public class Hydra extends net.minecraft.world.entity.LivingEntity{}',
    'net/minecraft/core/registries/BuiltInRegistries.java':'package net.minecraft.core.registries;import net.minecraft.resources.ResourceLocation;public class BuiltInRegistries{public static final Registry ENTITY_TYPE=new Registry();public static class Registry{public ResourceLocation getKey(Object type){return new ResourceLocation(type.toString());}}}',
    'net/minecraft/client/multiplayer/ClientLevel.java':'package net.minecraft.client.multiplayer;import net.minecraft.world.entity.*;import net.minecraft.resources.*;import java.util.*;public class ClientLevel{public List<Entity> entities=new ArrayList<>();public String dim="minecraft:overworld";public Iterable<Entity> entitiesForRendering(){return entities;}public ResourceKey dimension(){return new ResourceKey(new ResourceLocation(dim));}}',
    'net/minecraft/client/renderer/entity/EntityRenderer.java':'package net.minecraft.client.renderer.entity;import net.minecraft.world.entity.Entity;import net.minecraft.resources.ResourceLocation;public class EntityRenderer<T extends Entity>{public String texture="twilightforest:textures/model/hydra4.png";public ResourceLocation getTextureLocation(T entity){return new ResourceLocation(texture);}}',
    'twilightforest/client/renderer/entity/HydraRenderer.java':'package twilightforest.client.renderer.entity;public class HydraRenderer extends net.minecraft.client.renderer.entity.EntityRenderer<net.minecraft.world.entity.Entity>{}',
    'net/minecraft/client/renderer/entity/EntityRenderDispatcher.java':'package net.minecraft.client.renderer.entity;import net.minecraft.world.entity.Entity;public class EntityRenderDispatcher{public EntityRenderer<Entity> renderer=new twilightforest.client.renderer.entity.HydraRenderer();public <T extends Entity> EntityRenderer<T> getRenderer(T entity){return (EntityRenderer<T>)renderer;}}',
    'net/minecraft/server/packs/resources/Resource.java':'package net.minecraft.server.packs.resources;import java.io.*;public class Resource{public byte[] bytes="fixture-texture".getBytes();public boolean fail;public InputStream open()throws IOException{if(fail)throw new IOException("fixture");return new ByteArrayInputStream(bytes);}public String sourcePackId(){return "fixture-pack";}}',
    'net/minecraft/server/packs/resources/ResourceManager.java':'package net.minecraft.server.packs.resources;import java.util.*;import net.minecraft.resources.ResourceLocation;public class ResourceManager{public boolean marker,missing;public int reads;public Resource texture=new Resource();public Optional<Resource> getResource(ResourceLocation id){reads++;return id.toString().equals("twilightforest:jappa_models.marker")?(marker?Optional.of(new Resource()):Optional.empty()):(missing?Optional.empty():Optional.of(texture));}}',
    'net/minecraft/client/Minecraft.java':'package net.minecraft.client;import net.minecraft.client.multiplayer.ClientLevel;import net.minecraft.client.renderer.entity.*;import net.minecraft.server.packs.resources.*;public class Minecraft{public ClientLevel level=new ClientLevel();public EntityRenderDispatcher dispatcher=new EntityRenderDispatcher();public ResourceManager resources=new ResourceManager();public boolean onThread=true;public boolean isSameThread(){return onThread;}public EntityRenderDispatcher getEntityRenderDispatcher(){return dispatcher;}public ResourceManager getResourceManager(){return resources;}}',
    'org/kneekura/observer/U04Check.java':'''package org.kneekura.observer;import com.google.gson.*;import net.minecraft.client.Minecraft;import net.minecraft.world.entity.*;public class U04Check{public static void main(String[]a){Minecraft c=new Minecraft();Entity e=new twilightforest.entity.boss.Hydra();c.level.entities.add(e);String m=a[0];if(m.equals("absent"))c.level.entities.clear();if(m.equals("wrong_uuid"))e.id=java.util.UUID.randomUUID();if(m.equals("wrong_type"))e.type="minecraft:pig";if(m.equals("wrong_class")){c.level.entities.clear();c.level.entities.add(new LivingEntity());}if(m.equals("renderer"))c.dispatcher.renderer=new net.minecraft.client.renderer.entity.EntityRenderer<>();if(m.equals("texture"))c.dispatcher.renderer.texture="minecraft:other";if(m.equals("marker"))c.resources.marker=true;if(m.equals("missing_resource"))c.resources.missing=true;if(m.equals("io"))c.resources.texture.fail=true;if(m.equals("oversized"))c.resources.texture.bytes=new byte[1048577];if(m.equals("thread"))c.onThread=false;if(m.equals("dimension"))c.level.dim="minecraft:the_nether";if(m.equals("no_level"))c.level=null;JsonObject out=U04HydraProbe.capture(c,JsonParser.parseString(a[1]).getAsJsonObject(),JsonParser.parseString(a[2]).getAsJsonObject(),JsonParser.parseString(a[3]).getAsJsonObject());out.addProperty("fixture_resource_reads",c.resources.reads);System.out.print(out);}}'''}
    files=[]
    for name,source in sources.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source);files.append(str(p))
    done=subprocess.run([shutil.which('javac'),'--release','17','-cp',gson,'-d',str(root),*files,str(JAVA/'U04HydraProbe.java')],capture_output=True,text=True)
    assert done.returncode==0,done.stdout+done.stderr
    selection={'schema_version':1,'kind':'u04_hydra_derived_dependency','coordinate':'twilightforest-1.20.1-4.3.2508-tiny-remapper-0.11.2-mojmap.jar','sha256':'69e27b79067a9ce3bff3da18abd7b09b1ef4bc99625c07ea0c09424712df72bb','provider_receipt_hash':'c005d50d88496d977b9afea730ba0bd585f076cd04a67251381b384127d0243c','class_resources':['twilightforest/entity/boss/Hydra.class','twilightforest/client/renderer/entity/HydraRenderer.class']}
    def run(mode='ok',change_session=None,change_query=None,change_frame=None):
        s={'contract':{'schema_version':3,'session_role':'integrated_client','physical_side':'client','logical_side':'server','runtime_scope':'TARGET_CODE_AND_DEPENDENCY_BYTES','target_selection_hash':hashlib.sha256(json.dumps(selection,sort_keys=True,separators=(',',':')).encode()).hexdigest()},'target_selection':selection.copy()}
        q={'entity_uuids':[UUID],'dimension':'minecraft:overworld','limit':1,'screenshot':True}
        f={'png_b64':'ZnJhbWU=','png_sha256':hashlib.sha256(b'frame').hexdigest(),'width':640,'height':480,'client_frame_start':42,'client_frame_end':42,'camera':{'x':0,'y':70,'z':-20,'pitch':10,'yaw':0}}
        if change_session:change_session(s)
        if change_query:change_query(q)
        if change_frame:change_frame(f)
        result=subprocess.run([shutil.which('java'),'-cp',os.pathsep.join((str(root),gson)),'org.kneekura.observer.U04Check',mode,json.dumps(s),json.dumps(q),json.dumps(f)],capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
        return json.loads(result.stdout)
    return run

def test_exact_hydra_observation_is_bound_to_actual_captured_frame(probe):
    o=probe();assert o['status']=='CAPTURED' and o['supported'] is True
    assert o['entity_uuid']==UUID and o['entity_type']=='twilightforest:hydra'
    assert o['entity_class']=='twilightforest.entity.boss.Hydra' and o['renderer_class']=='twilightforest.client.renderer.entity.HydraRenderer'
    assert o['jappa_marker_present'] is False and o['texture_location']=='twilightforest:textures/model/hydra4.png'
    assert o['texture_sha256']==hashlib.sha256(b'fixture-texture').hexdigest()
    assert o['frame']['png_sha256']==hashlib.sha256(b'frame').hexdigest()
    assert o['frame']['client_frame_start']==o['frame']['client_frame_end']==42
    assert o['frame']['camera']['y']==70 and o['entity_pose']['y']==65
    assert o['atomic'] is False and o['visibility']=='NOT_ESTABLISHED'
    assert o['renderer_evidence']=='DISPATCHER_SELECTION_NOT_DRAW_CALL_ATTESTATION' and 'outcome' not in o

@pytest.mark.parametrize('field,value',[('sha256','0'*64),('kind','arbitrary_renderer'),('coordinate','another.jar'),('provider_receipt_hash','0'*64)])
def test_other_selection_never_reads_game_resources(probe,field,value):
    o=probe(change_session=lambda s:s['target_selection'].update({field:value}));assert o['status']=='UNSUPPORTED' and o['fixture_resource_reads']==0

@pytest.mark.parametrize('change',[lambda s:s['contract'].update(schema_version=1),lambda s:s['contract'].update(session_role='dedicated_client'),lambda s:s['contract'].update(target_selection_hash='0'*64),lambda s:s.pop('target_selection')])
def test_unbound_or_wrong_role_selection_is_not_observed(probe,change):
    o=probe(change_session=change);assert o['status']=='UNSUPPORTED' and o['fixture_resource_reads']==0

@pytest.mark.parametrize('change',[lambda q:q.update(entity_uuids=[]),lambda q:q.update(entity_uuids=[UUID,UUID]),lambda q:q.update(entity_uuids=['bad']),lambda q:q.update(screenshot=False),lambda q:q.update(screenshot='true'),lambda q:q.pop('screenshot'),lambda q:q.update(limit=2)])
def test_exact_uuid_and_screenshot_are_mandatory(probe,change):
    o=probe(change_query=change);assert o['status']=='UNKNOWN' and o['fixture_resource_reads']==0

@pytest.mark.parametrize('change',[lambda f:f.pop('png_b64'),lambda f:f.update(png_sha256='0'*64),lambda f:f.update(client_frame_end=43),lambda f:f.pop('camera'),lambda f:f.update(width=0),lambda f:f['camera'].update(y='70')])
def test_missing_or_mismatched_frame_is_not_bound(probe,change):
    o=probe(change_frame=change);assert o['status']=='UNKNOWN' and o['fixture_resource_reads']==0

@pytest.mark.parametrize('mode',['absent','wrong_uuid','no_level'])
def test_missing_selected_entity_has_no_fallback(probe,mode):
    o=probe(mode);assert o['status']=='UNAVAILABLE' and 'entity_uuid' not in o

@pytest.mark.parametrize('mode',['wrong_type','wrong_class','renderer','texture','marker','missing_resource','io','oversized','thread','dimension'])
def test_mismatch_and_unavailable_reads_never_claim_default_capture(probe,mode):
    o=probe(mode);assert o['status'] in {'UNKNOWN','UNAVAILABLE'} and 'outcome' not in o and o.get('visibility')!='PASS'
