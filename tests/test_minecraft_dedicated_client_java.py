"""Execute the real dedicated listener and staff reader with small game API doubles.

These are lifecycle/side-isolation unit fixtures, not Forge lifecycle acceptance.
Exact target linkage is separately checked by the compile-only Forge task.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from test_minecraft_dedicated_java import JAVA, PLAYER, OTHER, POLICY


def hash_value(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def session_value():
    server=dict(schema_version=2,session_role='dedicated_server',physical_side='server',logical_side='server',connection_policy=POLICY,connection_policy_hash=hash_value(POLICY),build_artifact_hash='a'*64,source_revision='b'*40,runtime_scope='TARGET_CODE_AND_DEPENDENCY_BYTES',dependency_inventory_hash='d'*64)
    identity=dict(server,schema_version=2,session_role='dedicated_client',physical_side='client',logical_side='client',player_uuid=PLAYER,server_contract_hash=hash_value(server))
    return dict(contract=identity,connection_policy=POLICY,server_contract=server,server_contract_hash=hash_value(server),player_uuid=PLAYER)


STUBS={
'org/kneekura/observer/StaffPacketTrace.java':'''package org.kneekura.observer;import com.google.gson.*;import net.minecraft.network.Connection;public class StaffPacketTrace {static StaffPacketTrace install(Connection c,String p,int i){throw new IllegalStateException("uninstrumented fixture");}public void close(){}public JsonObject snapshot(){return new JsonObject();}}''',
'net/minecraftforge/eventbus/api/SubscribeEvent.java':'''package net.minecraftforge.eventbus.api; public @interface SubscribeEvent {}''',
'net/minecraftforge/common/MinecraftForge.java':'''package net.minecraftforge.common; public class MinecraftForge {public static final Bus EVENT_BUS=new Bus();public static class Bus {public Object listener;public void register(Object o){listener=o;}}}''',
'net/minecraftforge/client/event/ClientPlayerNetworkEvent.java':'''package net.minecraftforge.client.event;
import net.minecraft.network.Connection;import net.minecraft.client.player.LocalPlayer;
public class ClientPlayerNetworkEvent {
 public static class LoggingIn {private LocalPlayer p;private Connection c;public LoggingIn(LocalPlayer p,Connection c){this.p=p;this.c=c;}public LocalPlayer getPlayer(){return p;}public Connection getConnection(){return c;}}
 public static class LoggingOut {} public static class Clone {}
}''',
'net/minecraft/network/Connection.java':'''package net.minecraft.network;import java.net.*;
public class Connection {public boolean connected=true,memory=false;public Channel channel=new Channel();public Channel channel(){return channel;}public boolean isConnected(){return connected;}public boolean isMemoryConnection(){return memory;}
 public static class Channel {public boolean active=true;public SocketAddress local=new InetSocketAddress("127.0.0.1",49152),remote=new InetSocketAddress("127.0.0.1",25565);public boolean isActive(){return active;}public SocketAddress localAddress(){return local;}public SocketAddress remoteAddress(){return remote;}public Id id(){return new Id();}}
 public static class Id {public String asLongText(){return "fixture-channel";}}
}''',
'net/minecraft/client/multiplayer/ClientPacketListener.java':'''package net.minecraft.client.multiplayer;import net.minecraft.network.Connection;public class ClientPacketListener {public Connection c=new Connection();public Connection getConnection(){return c;}}''',
'net/minecraft/client/Minecraft.java':'''package net.minecraft.client;import java.io.File;import net.minecraft.client.player.LocalPlayer;import net.minecraft.client.multiplayer.ClientPacketListener;
public class Minecraft {private static final Minecraft INSTANCE=new Minecraft();public File gameDirectory=new File(".");public LocalPlayer player;public Level level=new Level();public boolean integrated;public ClientPacketListener listener=new ClientPacketListener();public static Minecraft getInstance(){return INSTANCE;}public void execute(Runnable r){r.run();}public boolean hasSingleplayerServer(){return integrated;}public ClientPacketListener getConnection(){return listener;}
 public static class Level {public Dimension dimension(){return new Dimension();}}
 public static class Dimension {public String location(){return "minecraft:overworld";}}
}''',
'net/minecraft/world/entity/Entity.java':'''package net.minecraft.world.entity;import java.util.UUID;public class Entity {public UUID id;public int getId(){return 7;}public UUID getUUID(){return id;}public double getX(){return 1;}public double getY(){return 2;}public double getZ(){return 3;}public Vec getDeltaMovement(){return new Vec();}public static class Vec{public double x=0,y=0,z=0;}}''',
'net/minecraft/world/entity/player/Player.java':'''package net.minecraft.world.entity.player;import net.minecraft.world.entity.Entity;import net.minecraft.world.item.*;import net.minecraft.world.effect.MobEffectInstance;
public class Player extends Entity {public float health=17;public ItemStack stack=new ItemStack();public MobEffectInstance glow=new MobEffectInstance();public ItemCooldowns cooldown=new ItemCooldowns();public ItemStack getMainHandItem(){return stack;}public MobEffectInstance getEffect(Object effect){return glow;}public ItemCooldowns getCooldowns(){return cooldown;}public float getHealth(){return health;}}''',
'net/minecraft/client/player/LocalPlayer.java':'''package net.minecraft.client.player;public class LocalPlayer extends net.minecraft.world.entity.player.Player {}''',
'net/minecraft/world/item/Item.java':'''package net.minecraft.world.item;public class Item {}''',
'net/minecraft/world/item/ItemStack.java':'''package net.minecraft.world.item;public class ItemStack {public int count=3,damage=4;public Item getItem(){return new Item();}public int getCount(){return count;}public int getDamageValue(){return damage;}}''',
'net/minecraft/world/item/ItemCooldowns.java':'''package net.minecraft.world.item;public class ItemCooldowns {public boolean active=true;public float fraction=0.75f;public boolean isOnCooldown(Item i){return active;}public float getCooldownPercent(Item i,float tick){return fraction;}}''',
'net/minecraft/world/effect/MobEffects.java':'''package net.minecraft.world.effect;public class MobEffects {public static final Object GLOWING=new Object();}''',
'net/minecraft/world/effect/MobEffectInstance.java':'''package net.minecraft.world.effect;public class MobEffectInstance {public int duration=41,amplifier=0;public int getDuration(){return duration;}public int getAmplifier(){return amplifier;}}''',
'net/minecraft/resources/ResourceLocation.java':'''package net.minecraft.resources;public class ResourceLocation {private String id;public ResourceLocation(String a,String b){id=a+":"+b;}public String toString(){return id;}}''',
'net/minecraft/core/registries/BuiltInRegistries.java':'''package net.minecraft.core.registries;import net.minecraft.world.item.Item;import net.minecraft.resources.ResourceLocation;public class BuiltInRegistries {public static final Registry ITEM=new Registry();public static class Registry {public ResourceLocation getKey(Item i){return new ResourceLocation("kneekura","celestial_staff");}public boolean containsKey(ResourceLocation r){return true;}public Item get(ResourceLocation r){return new Item();}}}''',
'org/kneekura/observer/ClientProbe.java':'''package org.kneekura.observer;import java.nio.file.Path;import java.util.concurrent.CompletableFuture;import com.google.gson.JsonObject;public class ClientProbe {static long frame=20,tick=10;public static void install(){}static long frames(){return frame;}static long ticks(){return tick;}public static CompletableFuture<JsonObject> capture(Path d,boolean screenshot){tick+=2;frame+=3;JsonObject o=new JsonObject();o.addProperty("client_frame_start",frame);o.addProperty("client_frame_end",frame);o.addProperty("screen","none");if(screenshot)o.addProperty("png_sha256","fixture-only");return CompletableFuture.completedFuture(o);}}''',
'org/kneekura/observer/ForgeObserver.java':'''package org.kneekura.observer;import com.google.gson.*;import java.nio.file.Path;import java.util.concurrent.CompletableFuture;import java.util.function.Function;
public class ForgeObserver {public JsonObject session;public boolean ready;public Function<JsonObject,CompletableFuture<JsonObject>> capture;public JsonObject receiverSession(){return session;}public void startReceiver(Path p,Function<JsonObject,CompletableFuture<JsonObject>> f){capture=f;ready=true;}public void invalidateReceiver(String why){ready=false;}public JsonObject receiverBase(){JsonObject o=new JsonObject();o.add("identity",session.get("contract").deepCopy());return o;}public Path receiverDirectory(){return Path.of(".");}public long logSequence(){return 7;}public boolean hasVerifiedStaffTrace(){return false;}public JsonObject staffClientTrace(){return StaffTrace.unavailable(false,"fixture uninstrumented");}}''',
}


@pytest.fixture(scope='module')
def listener(tmp_path_factory):
    gson=os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file():pytest.skip('Explicit cached GSON_JAR required')
    if not shutil.which('javac') or not shutil.which('java'):pytest.skip('Java17-compatible JDK required')
    for name in ['DedicatedClientObserver.java','DedicatedSession.java','StaffStateCapture.java','StaffStateQuery.java','StaffTrace.java']:
        assert (JAVA/name).is_file(),f'Missing production Java source: {name}'
    folder=tmp_path_factory.mktemp('dedicated-client-java');files=[]
    for name,source in STUBS.items():
        path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source);files.append(path)
    harness=folder/'org/kneekura/observer/DedicatedFlow.java'
    harness.write_text('''package org.kneekura.observer;
import com.google.gson.*;import java.net.*;import java.util.UUID;import net.minecraft.client.*;import net.minecraft.client.player.*;import net.minecraft.network.*;import net.minecraftforge.common.*;import net.minecraftforge.client.event.*;
public class DedicatedFlow {
 public static void main(String[] a) throws Exception {
  ForgeObserver owner=new ForgeObserver();owner.session=JsonParser.parseString(a[1]).getAsJsonObject();Minecraft c=Minecraft.getInstance();c.player=new LocalPlayer();c.player.id=UUID.fromString(owner.session.get("player_uuid").getAsString());String mode=a[0];
  DedicatedClientObserver.install(owner);var listener=(DedicatedClientObserver)MinecraftForge.EVENT_BUS.listener;
  if(mode.equals("prelogout"))listener.logout(new ClientPlayerNetworkEvent.LoggingOut());
  if(mode.equals("integrated"))c.integrated=true;
  if(mode.equals("wrong_player"))c.player.id=UUID.fromString(a[2]);
  if(mode.equals("wrong_port"))c.listener.c.channel.remote=new InetSocketAddress("127.0.0.1",25566);
  if(mode.equals("memory"))c.listener.c.memory=true;
  listener.login(new ClientPlayerNetworkEvent.LoggingIn(c.player,c.listener.c));
  if(mode.equals("logout"))listener.logout(new ClientPlayerNetworkEvent.LoggingOut());
  if(mode.equals("clone"))listener.clonePlayer(new ClientPlayerNetworkEvent.Clone());
  if(mode.equals("reconnect"))listener.login(new ClientPlayerNetworkEvent.LoggingIn(c.player,c.listener.c));
  JsonObject out=new JsonObject();out.addProperty("ready",owner.ready);
  if(owner.ready){
   if(mode.equals("changed_connection"))c.listener.c=new Connection();
   if(mode.equals("changed_player")){LocalPlayer p=new LocalPlayer();p.id=c.player.id;c.player=p;}
   if(mode.equals("disconnected"))c.listener.c.connected=false;
   JsonObject q=new JsonObject();JsonArray ids=new JsonArray();ids.add(owner.session.get("player_uuid"));q.add("entity_uuids",ids);q.addProperty("dimension","minecraft:overworld");q.addProperty("limit",1);q.addProperty("staff_state",true);q.addProperty("screenshot",true);
   try{out.add("observation",owner.capture.apply(q).join());}catch(Exception e){out.addProperty("capture","BLOCKED");}
  }
  System.out.print(out);
 }
}''');files.append(harness)
    sources=[JAVA/n for n in ['DedicatedClientObserver.java','DedicatedSession.java','StaffStateCapture.java','StaffStateQuery.java','StaffTrace.java']]
    done=subprocess.run([shutil.which('javac'),'--release','17','-cp',gson,'-d',str(folder),*map(str,files+sources)],capture_output=True,text=True)
    assert done.returncode==0,done.stdout+done.stderr
    def run(mode):
        done=subprocess.run([shutil.which('java'),'-cp',os.pathsep.join((str(folder),gson)),'org.kneekura.observer.DedicatedFlow',mode,json.dumps(session_value()),OTHER],capture_output=True,text=True)
        assert done.returncode==0,done.stdout+done.stderr
        return json.loads(done.stdout)
    return run


@pytest.mark.parametrize('mode',['normal','prelogout'])
def test_receiver_starts_without_server_event_and_reads_its_own_state(listener,mode):
    out=listener(mode);assert out['ready'] is True
    observation=out['observation'];row=observation['entities'][0]
    assert observation['observation_side']=='logical_client'
    assert row['health']==17 and row['uuid']==PLAYER
    assert row['staff_state']['observation_side']=='logical_client'
    assert row['staff_state']['main_hand']['count']==3 and row['staff_state']['main_hand']['damage']==4
    assert row['staff_state']['glowing']=={'duration_ticks':41,'amplifier':0}
    assert row['staff_state']['staff_cooldown']['fraction']==0.75
    assert observation['server_tick_start'] is None and observation['server_tick_end'] is None
    assert observation['server_tick_scope']=='NOT_LOCALLY_OBSERVED'
    assert observation['client_tick_start']==10 and observation['client_tick_end']==12
    assert observation['client_frame_start']==20 and observation['client_frame_end']==23
    assert observation['log_sequence_start']==observation['log_sequence_end']==7
    assert observation['atomic'] is False
    assert observation['connection']==row['connection']


@pytest.mark.parametrize('mode',['integrated','wrong_player','wrong_port','memory','logout','clone','reconnect'])
def test_receiver_does_not_remain_ready_for_forbidden_lifecycle(listener,mode):
    assert listener(mode)=={'ready':False}


@pytest.mark.parametrize('mode',['changed_connection','changed_player','disconnected'])
def test_every_capture_revalidates_connection_and_player_instances(listener,mode):
    out=listener(mode);assert out['capture']=='BLOCKED' and 'observation' not in out
