"""Actual Netty forwarding with fake vanilla packet types; never opens a socket."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import pytest
from test_minecraft_dedicated_java import JAVA, PLAYER


def test_staff_packet_witness_exists():
    assert (JAVA/'StaffPacketTrace.java').is_file(), 'Missing narrow selected vanilla receive witness'


@pytest.fixture(scope='module')
def packets(tmp_path_factory):
    if not (JAVA/'StaffPacketTrace.java').is_file():pytest.skip('Missing implementation reported separately')
    deps=[os.environ.get('GSON_JAR',''),*os.environ.get('NETTY_CLASSPATH','').split(os.pathsep)]
    if len(deps)<4 or not all(p and Path(p).is_file() for p in deps):pytest.skip('Explicit cached Gson and Netty common/buffer/transport classpath required')
    folder=tmp_path_factory.mktemp('staff-packet-java')
    sources={
      'net/minecraft/network/Connection.java':'''package net.minecraft.network;import io.netty.channel.*;public class Connection extends ChannelInboundHandlerAdapter {public Channel channel;public Channel channel(){return channel;}public boolean isConnected(){return channel.isActive();}public boolean isMemoryConnection(){return false;}}''',
      'net/minecraft/world/effect/MobEffects.java':'''package net.minecraft.world.effect;public class MobEffects {public static final Object GLOWING=new Object();}''',
      'net/minecraft/core/registries/BuiltInRegistries.java':'''package net.minecraft.core.registries;public class BuiltInRegistries {public static final Registry ITEM=new Registry();public static class Registry {public String getKey(Object item){return String.valueOf(item);}}}''',
      'net/minecraft/network/protocol/game/ClientboundUpdateMobEffectPacket.java':'''package net.minecraft.network.protocol.game;public class ClientboundUpdateMobEffectPacket {public int id,duration=60;public Object effect;public boolean fault;public ClientboundUpdateMobEffectPacket(int id,Object effect){this.id=id;this.effect=effect;}public int getEntityId(){if(fault)throw new IllegalStateException("fixture decode fault");return id;}public Object getEffect(){return effect;}public byte getEffectAmplifier(){return 0;}public int getEffectDurationTicks(){return duration;}}''',
      'net/minecraft/network/protocol/game/ClientboundCooldownPacket.java':'''package net.minecraft.network.protocol.game;public class ClientboundCooldownPacket {public String item;public ClientboundCooldownPacket(String item){this.item=item;}public String getItem(){return item;}public int getDuration(){return 100;}}''',
      'org/kneekura/observer/PacketCheck.java':'''package org.kneekura.observer;import io.netty.channel.embedded.EmbeddedChannel;import net.minecraft.network.Connection;import net.minecraft.network.protocol.game.*;import net.minecraft.world.effect.MobEffects;import com.google.gson.*;
public class PacketCheck {public static void main(String[] a)throws Exception {EmbeddedChannel channel=new EmbeddedChannel();Connection connection=new Connection();connection.channel=channel;channel.pipeline().addLast("packet_handler",connection);StaffPacketTrace trace=StaffPacketTrace.install(connection,a[1],7);String mode=a[0];java.util.List<Object> messages=new java.util.ArrayList<>();
 if(mode.equals("selected")){messages.add(new ClientboundUpdateMobEffectPacket(7,MobEffects.GLOWING));messages.add(new ClientboundCooldownPacket("kneekura:celestial_staff"));}
 if(mode.equals("wrong")){messages.add(new ClientboundUpdateMobEffectPacket(8,MobEffects.GLOWING));messages.add(new ClientboundUpdateMobEffectPacket(7,new Object()));messages.add(new ClientboundCooldownPacket("minecraft:stick"));messages.add(new Object());}
 if(mode.equals("overflow"))for(int i=0;i<20;i++)messages.add(new ClientboundCooldownPacket("kneekura:celestial_staff"));
 if(mode.equals("fault")){var p=new ClientboundUpdateMobEffectPacket(7,MobEffects.GLOWING);p.fault=true;messages.add(p);}
 if(mode.equals("disabled")){trace.close();messages.add(new ClientboundCooldownPacket("kneekura:celestial_staff"));}
 if(mode.equals("changed_connection")){connection.channel=new EmbeddedChannel();messages.add(new ClientboundCooldownPacket("kneekura:celestial_staff"));}
 boolean same=true;for(Object m:messages){channel.writeInbound(m);same &= channel.readInbound()==m;same &= channel.readInbound()==null;}
 JsonObject out=trace.snapshot();out.addProperty("forwarded_exactly_once",same);out.addProperty("sent",messages.size());System.out.print(out);trace.close();channel.finishAndReleaseAll();}}
'''}
    files=[]
    for name,value in sources.items():
        path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value);files.append(path)
    cp=os.pathsep.join(deps)
    done=subprocess.run([shutil.which('javac'),'--release','17','-cp',cp,'-d',str(folder),*map(str,files),str(JAVA/'StaffPacketTrace.java')],capture_output=True,text=True)
    assert done.returncode==0,done.stdout+done.stderr
    def run(mode):
        done=subprocess.run([shutil.which('java'),'-cp',os.pathsep.join((str(folder),cp)),'org.kneekura.observer.PacketCheck',mode,PLAYER],capture_output=True,text=True)
        assert done.returncode==0,done.stdout+done.stderr
        return json.loads(done.stdout)
    return run


def test_selected_packets_are_counted_and_forwarded_exactly_once(packets):
    out=packets('selected');assert out['forwarded_exactly_once'] is True
    assert out['glowing_count']==out['cooldown_count']==1
    assert out['sequence']==2 and out['player_uuid']==PLAYER
    assert [r['kind'] for r in out['records']]==['glowing','cooldown']


@pytest.mark.parametrize('mode',['wrong','disabled','changed_connection'])
def test_unselected_or_stale_scope_is_forwarded_without_counting(packets,mode):
    out=packets(mode);assert out['forwarded_exactly_once'] is True
    assert out['sequence']==out['glowing_count']==out['cooldown_count']==0 and out['records']==[]


def test_trace_failure_never_drops_or_duplicates_packet(packets):
    out=packets('fault');assert out['forwarded_exactly_once'] is True
    assert out['unknown']==1 and out['sequence']==0


def test_packet_history_is_bounded_and_drops_are_explicit(packets):
    out=packets('overflow');assert out['forwarded_exactly_once'] is True
    assert out['cooldown_count']==20 and len(out['records'])==16 and out['dropped']==4
    assert out['records'][0]['sequence']==5 and out['records'][-1]['sequence']==20
