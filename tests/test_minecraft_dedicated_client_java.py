"""Execute the real dedicated listener and staff reader with small game API doubles.

These are lifecycle/side-isolation unit fixtures, not Forge lifecycle acceptance.
Exact target linkage is separately checked by the compile-only Forge task.
"""
import hashlib
import json
import os
import re
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
'org/kneekura/observer/StaffPacketTrace.java':'''package org.kneekura.observer;import com.google.gson.*;import net.minecraft.network.Connection;import net.minecraft.client.Minecraft;public class StaffPacketTrace {static int installedId=-1,installs,closes;static boolean fail;static StaffPacketTrace install(Connection c,String p,int i){if(fail)throw new IllegalStateException("trace failure");if(c!=Minecraft.getInstance().listener.c || i!=Minecraft.getInstance().player.getId())throw new IllegalStateException("wrong final trace identity");installedId=i;installs++;return new StaffPacketTrace();}public void close(){closes++;}public JsonObject snapshot(){JsonObject o=new JsonObject();o.addProperty("entity_id",installedId);return o;}}''',
'net/minecraftforge/event/TickEvent.java':'''package net.minecraftforge.event;public class TickEvent {public enum Phase {START,END}public static class ClientTickEvent {public final Phase phase;public ClientTickEvent(Phase p){phase=p;}}}''',
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
 public static class Channel {public boolean active=true;public SocketAddress local=new InetSocketAddress("127.0.0.1",49152),remote=new InetSocketAddress("127.0.0.1",25565);public boolean isActive(){return active;}public SocketAddress localAddress(){return local;}public SocketAddress remoteAddress(){return remote;}public String identity="fixture-channel";public Id id(){return new Id(identity);}}
 public static class Id {private final String value;public Id(String value){this.value=value;}public String asLongText(){return value;}}
}''',
'net/minecraft/client/multiplayer/ClientPacketListener.java':'''package net.minecraft.client.multiplayer;import net.minecraft.network.Connection;public class ClientPacketListener {public Connection c=new Connection();public Connection getConnection(){return c;}}''',
'net/minecraft/client/Minecraft.java':'''package net.minecraft.client;import java.io.File;import net.minecraft.client.player.LocalPlayer;import net.minecraft.client.multiplayer.ClientPacketListener;
public class Minecraft {private static final Minecraft INSTANCE=new Minecraft();public File gameDirectory=new File(".");public LocalPlayer player;public Level level=new Level();public boolean integrated;public ClientPacketListener listener=new ClientPacketListener();public static Minecraft getInstance(){return INSTANCE;}public void execute(Runnable r){r.run();}public boolean hasSingleplayerServer(){return integrated;}public ClientPacketListener getConnection(){return listener;}
 public static class Level {public Dimension dimension(){return new Dimension();}}
 public static class Dimension {public String location(){return "minecraft:overworld";}}
}''',
'net/minecraft/world/entity/Entity.java':'''package net.minecraft.world.entity;import java.util.UUID;public class Entity {public UUID id;public int entityId=1;public int getId(){return entityId;}public void setId(int value){entityId=value;}public UUID getUUID(){return id;}public double getX(){return 1;}public double getY(){return 2;}public double getZ(){return 3;}public Vec getDeltaMovement(){return new Vec();}public static class Vec{public double x=0,y=0,z=0;}}''',
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
'org/kneekura/observer/ForgeObserver.java':'''package org.kneekura.observer;import com.google.gson.*;import java.nio.file.Path;import java.util.concurrent.CompletableFuture;import java.util.concurrent.Callable;import java.util.function.Function;
public class ForgeObserver {public JsonObject session;public boolean ready,verifiedTrace,traceReadyAtStart,initialized,failActivation;public int starts;public Function<JsonObject,CompletableFuture<JsonObject>> capture;public JsonObject receiverSession(){return session;}private String role;private Path directory;private Function<JsonObject,CompletableFuture<JsonObject>> receiverCapture;private void initialize() throws Exception {initialized=true;role="dedicated_client";directory=Path.of(".").toRealPath();}private void marker(){}private static void require(boolean ok,String message){if(!ok)throw new IllegalStateException(message);}private void activate(){if(failActivation)throw new IllegalStateException("activation failed");traceReadyAtStart=!verifiedTrace || StaffPacketTrace.installs==1;capture=receiverCapture;ready=true;starts++;}@START_RECEIVER_METHOD@public void invalidateReceiver(String why){ready=false;}public JsonObject receiverBase(){JsonObject o=new JsonObject();o.add("identity",session.get("contract").deepCopy());return o;}public Path receiverDirectory(){return Path.of(".");}public long logSequence(){return 7;}public boolean hasVerifiedStaffTrace(){if(!initialized)throw new IllegalStateException("session is not initialized");return verifiedTrace;}public JsonObject staffClientTrace(){return StaffTrace.unavailable(false,"fixture uninstrumented");}}''',
}


@pytest.fixture(scope='module')
def listener(tmp_path_factory):
    gson=os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file():pytest.skip('Explicit cached GSON_JAR required')
    if not shutil.which('javac') or not shutil.which('java'):pytest.skip('Java17-compatible JDK required')
    for name in ['DedicatedClientObserver.java','DedicatedSession.java','StaffStateCapture.java','StaffStateQuery.java','StaffTrace.java']:
        assert (JAVA/name).is_file(),f'Missing production Java source: {name}'
    folder=tmp_path_factory.mktemp('dedicated-client-java');files=[]
    # Exercise the production receiver initialization/activation order as well as
    # the complete production listener; only infrastructure operations are doubles.
    observer=(JAVA/'ForgeObserver.java').read_text()
    start=observer.index('    void startReceiver(')
    end=observer.index('    JsonObject receiverSession()',start)
    receiver_method=observer[start:end]
    for name,source in STUBS.items():
        source=source.replace('@START_RECEIVER_METHOD@',receiver_method)
        path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source);files.append(path)
    harness=folder/'org/kneekura/observer/DedicatedFlow.java'
    harness.write_text('''package org.kneekura.observer;
import com.google.gson.*;import java.net.*;import java.util.UUID;import net.minecraft.client.*;import net.minecraft.client.player.*;import net.minecraft.network.*;import net.minecraftforge.common.*;import net.minecraftforge.client.event.*;
public class DedicatedFlow {
 static void tick(DedicatedClientObserver listener,net.minecraftforge.event.TickEvent.Phase phase) throws Exception {
  // Replay a real event boundary without requiring the old implementation to have a tick method.
  var event=new net.minecraftforge.event.TickEvent.ClientTickEvent(phase);
  for(var method:listener.getClass().getMethods())if(java.util.Arrays.equals(method.getParameterTypes(),new Class<?>[]{event.getClass()}))method.invoke(listener,event);
 }
 public static void main(String[] a) throws Exception {
  ForgeObserver owner=new ForgeObserver();owner.session=JsonParser.parseString(a[1]).getAsJsonObject();Minecraft c=Minecraft.getInstance();c.player=new LocalPlayer();c.player.id=UUID.fromString(owner.session.get("player_uuid").getAsString());String mode=a[0];
  DedicatedClientObserver.install(owner);var listener=(DedicatedClientObserver)MinecraftForge.EVENT_BUS.listener;
  if(mode.equals("prelogout"))listener.logout(new ClientPlayerNetworkEvent.LoggingOut());
  if(mode.equals("integrated"))c.integrated=true;
  if(mode.equals("wrong_player"))c.player.id=UUID.fromString(a[2]);
  if(mode.equals("wrong_port"))c.listener.c.channel.remote=new InetSocketAddress("127.0.0.1",25566);
  if(mode.equals("memory"))c.listener.c.memory=true;
  boolean deferred=mode.startsWith("deferred_");owner.verifiedTrace=deferred;
  listener.login(new ClientPlayerNetworkEvent.LoggingIn(c.player,c.listener.c));
  boolean beforeEnd=owner.ready;int beforeEndStarts=owner.starts;
  c.player.setId(mode.equals("deferred_unchanged_id")?1:2);
  if(mode.equals("deferred_player_swap")){LocalPlayer p=new LocalPlayer();p.id=c.player.id;p.entityId=2;c.player=p;}
  if(mode.equals("deferred_connection_swap"))c.listener.c=new Connection();
  if(mode.equals("deferred_channel_swap"))c.listener.c.channel.identity="changed-channel";
  if(mode.equals("deferred_channel_instance_swap"))c.listener.c.channel=new Connection.Channel();
  if(mode.equals("deferred_uuid_swap"))c.player.id=UUID.fromString(a[2]);
  if(mode.equals("deferred_disconnect"))c.listener.c.connected=false;
  if(mode.equals("deferred_logout"))listener.logout(new ClientPlayerNetworkEvent.LoggingOut());
  if(mode.equals("deferred_clone"))listener.clonePlayer(new ClientPlayerNetworkEvent.Clone());
  if(mode.equals("deferred_reconnect"))listener.login(new ClientPlayerNetworkEvent.LoggingIn(c.player,c.listener.c));
  if(mode.equals("deferred_trace_failure"))StaffPacketTrace.fail=true;
  if(mode.equals("deferred_activation_failure"))owner.failActivation=true;
  tick(listener,net.minecraftforge.event.TickEvent.Phase.START);boolean afterStart=owner.ready;
  if(!mode.equals("deferred_start_only"))tick(listener,net.minecraftforge.event.TickEvent.Phase.END);
  StaffPacketTrace.fail=false;owner.failActivation=false;
  tick(listener,net.minecraftforge.event.TickEvent.Phase.START);
  if(!mode.equals("deferred_start_only"))tick(listener,net.minecraftforge.event.TickEvent.Phase.END);
  if(mode.equals("logout"))listener.logout(new ClientPlayerNetworkEvent.LoggingOut());
  if(mode.equals("clone"))listener.clonePlayer(new ClientPlayerNetworkEvent.Clone());
  if(mode.equals("reconnect"))listener.login(new ClientPlayerNetworkEvent.LoggingIn(c.player,c.listener.c));
  JsonObject out=new JsonObject();out.addProperty("ready",owner.ready);
  if(deferred){out.addProperty("before_end",beforeEnd);out.addProperty("before_end_starts",beforeEndStarts);out.addProperty("after_start",afterStart);out.addProperty("starts",owner.starts);out.addProperty("trace_installs",StaffPacketTrace.installs);out.addProperty("trace_closes",StaffPacketTrace.closes);out.addProperty("trace_id",StaffPacketTrace.installedId);out.addProperty("trace_before_receiver",owner.traceReadyAtStart);}
  if(mode.equals("deferred_changed_id_after"))c.player.setId(3);
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


@pytest.mark.parametrize('mode,entity_id',[('deferred_assigned_id',2),('deferred_unchanged_id',1)])
def test_login_defers_receiver_and_packet_trace_until_final_player_id(listener,mode,entity_id):
    out=listener(mode)
    assert out['before_end'] is False and out['before_end_starts']==0
    assert out['after_start'] is False
    assert out['ready'] is True and out['starts']==1 and out['trace_installs']==1
    assert out['trace_id']==entity_id and out['trace_before_receiver'] is True
    assert out['observation']['staff_packet_trace']['entity_id']==entity_id


@pytest.mark.parametrize('mode',['player_swap','connection_swap','channel_swap','channel_instance_swap','uuid_swap','disconnect','logout','clone','reconnect','trace_failure','start_only'])
def test_pending_login_never_publishes_after_identity_loss_or_before_end(listener,mode):
    out=listener('deferred_'+mode)
    assert out['before_end'] is False and out['after_start'] is False
    assert out['ready'] is False and out['starts']==0
    assert out['trace_installs']==0


def test_final_entity_id_remains_fixed_after_receiver_publication(listener):
    out=listener('deferred_changed_id_after')
    assert out['ready'] is True and out['starts']==1 and out['trace_id']==2
    assert out['capture']=='BLOCKED' and 'observation' not in out


def test_cached_patched_login_event_precedes_server_entity_id_assignment():
    archive=os.environ.get('MINECRAFT_FORGE_JAR')
    if not archive or not Path(archive).is_file():
        pytest.skip('Explicit cached MINECRAFT_FORGE_JAR required for patched lifecycle ordering')
    javap=shutil.which('javap')
    if not javap:pytest.skip('Java17-compatible javap required')
    def method(class_name,signature):
        result=subprocess.run([javap,'-c','-p','-classpath',archive,class_name],capture_output=True,text=True,check=True)
        start=result.stdout.index(signature)
        return re.split(r'\n  (?:public|private|protected)',result.stdout[start:],maxsplit=1)[0]
    login=method('net.minecraft.client.multiplayer.ClientPacketListener','public void handleLogin(')
    assert login.index('ForgeHooksClient.firePlayerLogin')<login.index('ClientboundLoginPacket.playerId')<login.index('LocalPlayer.setId')<login.index('ClientLevel.addPlayer')
    hook=method('net.minecraftforge.client.ForgeHooksClient','public static void firePlayerLogin(')
    assert hook.index('ClientPlayerNetworkEvent$LoggingIn')<hook.index('IEventBus.post')


def test_activation_failure_closes_trace_and_never_retries_on_later_tick(listener):
    out=listener('deferred_activation_failure')
    assert out['before_end'] is False and out['after_start'] is False
    assert out['ready'] is False and out['starts']==0
    assert out['trace_installs']==1 and out['trace_closes']==1
