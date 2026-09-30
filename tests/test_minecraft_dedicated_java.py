"""Actual Java role/socket/lifetime guards; these fixtures never start Minecraft."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

JAVA = Path(__file__).resolve().parents[1] / 'departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer'
PLAYER = '00000000-0000-4000-8000-000000000001'
OTHER = '00000000-0000-4000-8000-000000000002'
POLICY = {'host':'127.0.0.1','port':25565,'player_uuids':[PLAYER]}


def test_dedicated_java_guard_and_client_lifecycle_exist():
    assert (JAVA / 'DedicatedSession.java').is_file(), 'Missing strict dedicated role/socket/lifetime guard'
    assert (JAVA / 'DedicatedClientObserver.java').is_file(), 'Missing dedicated client event lifecycle'


@pytest.fixture(scope='module')
def guard(tmp_path_factory):
    if not (JAVA / 'DedicatedSession.java').is_file():
        pytest.skip('Missing implementation is reported by existence test')
    gson = os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file(): pytest.skip('Explicit cached GSON_JAR required')
    if not shutil.which('javac') or not shutil.which('java'): pytest.skip('Java17-compatible JDK required')
    folder = tmp_path_factory.mktemp('dedicated-java')
    harness = folder/'DedicatedCheck.java'
    harness.write_text('''package org.kneekura.observer;
import com.google.gson.*;
import java.net.*;
public final class DedicatedCheck {
 public static void main(String[] a) {
  try {
   JsonObject q=JsonParser.parseString(a[1]).getAsJsonObject();
   switch(a[0]) {
    case "session" -> { DedicatedSession.session(q,q.getAsJsonObject("contract")); System.out.print("OK"); }
    case "marker" -> { DedicatedSession.class.getDeclaredMethod("marker",JsonObject.class,JsonObject.class,String.class).invoke(null,q,JsonParser.parseString(a[2]).getAsJsonObject(),"/fixture/run"); System.out.print("OK"); }
    case "policy" -> { DedicatedSession.policy(q); System.out.print("OK"); }
    case "role" -> System.out.print(DedicatedSession.role(q));
    case "query" -> { DedicatedSession.query(q, a[2], "minecraft:overworld"); System.out.print("OK"); }
    case "socket" -> {
     var p=JsonParser.parseString(a[2]).getAsJsonObject();
     var local=q.get("unresolved").getAsBoolean()?InetSocketAddress.createUnresolved(q.get("local_host").getAsString(),q.get("local_port").getAsInt()):new InetSocketAddress(InetAddress.getByName(q.get("local_host").getAsString()),q.get("local_port").getAsInt());
     var remote=new InetSocketAddress(InetAddress.getByName(q.get("remote_host").getAsString()),q.get("remote_port").getAsInt());
     System.out.print(DedicatedSession.connection(p,a[3],q.get("receiver").getAsBoolean(),q.get("connected").getAsBoolean(),q.get("memory").getAsBoolean(),q.get("channel").getAsString(),local,remote));
    }
    case "lifetime" -> {
     var l=new DedicatedSession.Lifetime(); Object c=new Object();
     l.bind(c,"one",a[2]); l.check(c,"one",a[2]);
     String fault=q.get("fault").getAsString();
     if(fault.equals("connection"))l.check(new Object(),"one",a[2]);
     if(fault.equals("channel"))l.check(c,"two",a[2]);
     if(fault.equals("player"))l.check(c,"one",a[3]);
     if(fault.equals("rebind"))l.bind(c,"one",a[2]);
     if(fault.equals("logout")){l.invalidate();l.check(c,"one",a[2]);}
     if(fault.equals("reconnect")){l.invalidate();l.bind(new Object(),"two",a[2]);}
     System.out.print("OK");
    }
    default -> throw new IllegalArgumentException();
   }
  } catch(Exception e) {System.out.print("BLOCKED");}
 }
}''')
    result=subprocess.run([shutil.which('javac'),'--release','17','-cp',gson,'-d',str(folder),str(JAVA/'DedicatedSession.java'),str(harness)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    def run(mode,value,*args):
        result=subprocess.run([shutil.which('java'),'-cp',os.pathsep.join((str(folder),gson)),'org.kneekura.observer.DedicatedCheck',mode,json.dumps(value),*args],capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
        return result.stdout
    return run


def test_policy_accepts_only_explicit_bounded_shape(guard):
    assert guard('policy',POLICY)=='OK'


@pytest.mark.parametrize('change',[{'host':'localhost'},{'host':'0.0.0.0'},{'port':True},{'port':25565.0},{'port':'25565'},{'port':0},{'port':65536},{'port':4294992861},{'player_uuids':[]},{'player_uuids':[PLAYER,PLAYER]},{'player_uuids':['1-1-1-1-1']},{'player_uuids':[PLAYER,OTHER,'00000000-0000-4000-8000-000000000003']},{'extra':True}])
def test_policy_rejects_coercion_and_scope_growth(guard,change):
    assert guard('policy',dict(POLICY,**change))=='BLOCKED'


def test_role_preserves_legacy_and_separates_receiving_client(guard):
    assert guard('role',{'schema_version':1})=='legacy'
    assert guard('role',{'schema_version':2,'session_role':'dedicated_client','physical_side':'client','logical_side':'client'})=='dedicated_client'
    assert guard('role',{'schema_version':2,'session_role':'dedicated_server','physical_side':'server','logical_side':'server'})=='dedicated_server'


@pytest.mark.parametrize('change',[{'schema_version':True},{'schema_version':2.0},{'session_role':'integrated'},{'physical_side':'server'},{'logical_side':'server'},{'world_id':'fake'},{'world_seed':0},{'world_template_hash':'a'*64}])
def test_receiver_role_rejects_fake_world_and_type_changes(guard,change):
    q={'schema_version':2,'session_role':'dedicated_client','physical_side':'client','logical_side':'client'}
    assert guard('role',dict(q,**change))=='BLOCKED'


def test_receiver_query_is_one_actual_local_player(guard):
    assert guard('query',{},PLAYER)=='OK'
    assert guard('query',{'entity_uuids':[PLAYER],'dimension':'minecraft:overworld','limit':1,'staff_state':True,'screenshot':True},PLAYER)=='OK'


@pytest.mark.parametrize('change',[{'entity_uuids':[OTHER]},{'entity_uuids':[]},{'entity_uuids':[PLAYER,OTHER]},{'limit':True},{'limit':1.0},{'dimension':'minecraft:the_nether'},{'screenshot':'true'},{'staff_state':1},{'command':'effect give'},{'blocks':[]}])
def test_receiver_query_never_selects_other_entity_or_mutation(guard,change):
    assert guard('query',change,PLAYER)=='BLOCKED'


def socket_query():
    return dict(local_host='127.0.0.1',local_port=49152,remote_host='127.0.0.1',remote_port=25565,channel='channel-one',connected=True,memory=False,receiver=True,unresolved=False)


def test_socket_shape_uses_real_numeric_loopback_tuple(guard):
    out=json.loads(guard('socket',socket_query(),json.dumps(POLICY),PLAYER))
    assert out==dict(player_uuid=PLAYER,connected=True,memory=False,channel_id='channel-one',local={'host':'127.0.0.1','port':49152},remote={'host':'127.0.0.1','port':25565})
    q=socket_query();q.update(receiver=False,local_port=25565,remote_port=49152)
    assert json.loads(guard('socket',q,json.dumps(POLICY),PLAYER))['local']['port']==25565


@pytest.mark.parametrize('change',[{'local_host':'127.0.0.2'},{'remote_host':'192.0.2.1'},{'remote_port':25566},{'memory':True},{'connected':False},{'channel':''},{'channel':'x'*257},{'unresolved':True},{'local_port':0}])
def test_socket_rejects_wrong_peer_or_unconnected_scope(guard,change):
    assert guard('socket',dict(socket_query(),**change),json.dumps(POLICY),PLAYER)=='BLOCKED'


@pytest.mark.parametrize('fault',['connection','channel','player','rebind','logout','reconnect'])
def test_lifetime_cannot_reuse_epoch_after_connection_changes(guard,fault):
    assert guard('lifetime',{'fault':fault},PLAYER,OTHER)=='BLOCKED'


def test_lifetime_accepts_only_original_bound_instance(guard):
    assert guard('lifetime',{'fault':'none'},PLAYER,OTHER)=='OK'


def marker_value():
    return dict(kind='client_run_directory',directory='/fixture/run',run_directory_id='r',run_directory_template_hash='a'*64,fresh=False)

def marker_identity():
    return dict(schema_version=2,session_role='dedicated_client',physical_side='client',logical_side='client',run_directory_id='r',run_directory_template_hash='a'*64)

def test_consumed_directory_marker_preserves_distinct_receiver_identity(guard):
    assert guard('marker',marker_value(),json.dumps(marker_identity()))=='OK'

@pytest.mark.parametrize('change',[{'kind':'world'},{'fresh':True},{'fresh':0},{'directory':'/elsewhere'},{'run_directory_id':'other'},{'run_directory_template_hash':'b'*64},{'world':'/fake-world'}])
def test_receiver_marker_rejects_world_substitution_or_changed_ownership(guard,change):
    assert guard('marker',dict(marker_value(),**change),json.dumps(marker_identity()))=='BLOCKED'


@pytest.mark.parametrize('field',['run_directory_id','run_directory_template_hash','server_contract_hash','player_uuid'])
def test_server_role_rejects_receiving_client_identity_fields(guard,field):
    q=dict(schema_version=2,session_role='dedicated_server',physical_side='server',logical_side='server')
    q[field]='unexpected'
    assert guard('role',q)=='BLOCKED'


def test_receiver_session_rechecks_full_server_policy_body(guard):
    from test_minecraft_dedicated_client_java import session_value,hash_value
    s=session_value()
    assert guard('session',s)=='OK'
    s['server_contract']['connection_policy']=dict(s['server_contract']['connection_policy'],port=25566)
    s['server_contract_hash']=s['contract']['server_contract_hash']=hash_value(s['server_contract'])
    assert guard('session',s)=='BLOCKED'


@pytest.mark.parametrize('target',['contract','server_contract'])
@pytest.mark.parametrize('field,value',[('runtime_scope',None),('runtime_scope','FULL_BYTECODE_VERIFIED'),('dependency_inventory_hash',None),('dependency_inventory_hash',True),('dependency_inventory_hash','a'*63)])
def test_v2_session_requires_explicit_dependency_scope_on_each_role(guard,target,field,value):
    from test_minecraft_dedicated_client_java import session_value,hash_value
    s=session_value()
    if value is None:s[target].pop(field)
    else:s[target][field]=value
    if target=='server_contract':s['server_contract_hash']=s['contract']['server_contract_hash']=hash_value(s[target])
    assert guard('session',s)=='BLOCKED'


def test_receiver_and_server_may_have_distinct_receipt_bound_dependency_inventories(guard):
    from test_minecraft_dedicated_client_java import session_value,hash_value
    s=session_value();s['server_contract']['dependency_inventory_hash']='e'*64
    s['server_contract_hash']=s['contract']['server_contract_hash']=hash_value(s['server_contract'])
    assert guard('session',s)=='OK'


@pytest.mark.parametrize('field,value',[('runtime_scope','TARGET_CODE_AND_DEPENDENCY_BYTES'),('dependency_inventory_hash','d'*64)])
def test_legacy_identity_cannot_claim_v2_dependency_scope(guard,field,value):
    assert guard('role',{'schema_version':1,field:value})=='BLOCKED'
