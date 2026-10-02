"""Schema3 archive/resource identity guards; fixtures never load a game class."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

from test_minecraft_dedicated_java import JAVA, guard
from test_minecraft_dependency_java import SCOPE
from test_minecraft_dedicated_client_java import hash_value


def identity():
    return dict(schema_version=3,session_role='integrated_client',physical_side='client',logical_side='server',
        runtime_scope=SCOPE,dependency_inventory_hash='d'*64,target_selection_hash='e'*64,
        dirty_hash='c'*64,world_id='w',world_template_hash='f'*64,world_seed=0)


def test_schema3_is_distinct_integrated_world_identity(guard):
    assert guard('role',identity())=='integrated_client'


@pytest.mark.parametrize('field,value',[('schema_version',3.0),('session_role','dedicated_client'),('physical_side','server'),('logical_side','client'),('connection_policy',{}),('connection_policy_hash','d'*64),('server_contract_hash','e'*64),('player_uuid','x'),('run_directory_id','r')])
def test_schema3_rejects_dedicated_identity_substitution(guard,field,value):
    assert guard('role',dict(identity(),**{field:value}))=='BLOCKED'


def test_integrated_client_marker_requires_client_save_layout(guard):
    marker=dict(directory='/fixture/run',world='/fixture/run/saves/world',world_layout='client',fresh=False,
        world_id='w',world_template_hash='f'*64)
    assert guard('marker',marker,json.dumps(identity()))=='OK'
    assert guard('marker',dict(marker,world_layout='server'),json.dumps(identity()))=='BLOCKED'
    assert guard('marker',dict(marker,world='/fixture/run/world'),json.dumps(identity()))=='BLOCKED'


@pytest.fixture(scope='module')
def target_guard(tmp_path_factory):
    gson=os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file():pytest.skip('Explicit cached GSON_JAR required')
    if not shutil.which('javac') or not shutil.which('java'):pytest.skip('Java17-compatible JDK required')
    folder=tmp_path_factory.mktemp('u04-startup-java');harness=folder/'TargetCheck.java'
    harness.write_text('''package org.kneekura.observer;
import com.google.gson.*;import java.nio.file.*;import java.net.*;
public final class TargetCheck {
 public static void main(String[] a) {
  try {
   JsonObject s=JsonParser.parseString(Files.readString(Path.of(a[0]))).getAsJsonObject();JsonObject i=s.getAsJsonObject("contract");
   DedicatedSession.session(s,i);var deps=DependencyInventory.verify(s,i);
   try(URLClassLoader loader=new URLClassLoader(new URL[]{Path.of(a[1]).toUri().toURL()},null)) {
    Class.forName("org.kneekura.observer.TargetDependency").getDeclaredMethod("verify",JsonObject.class,JsonObject.class,DependencyInventory.class,ClassLoader.class).invoke(null,s,i,deps,loader);
   }
   System.out.print("OK");
  } catch(Exception e){System.out.print("BLOCKED");}
 }
}''')
    names=['DedicatedSession.java','DependencyInventory.java']
    if (JAVA/'TargetDependency.java').exists():names.append('TargetDependency.java')
    result=subprocess.run([shutil.which('javac'),'--release','17','-cp',gson,'-d',str(folder),*[str(JAVA/n) for n in names],str(harness)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    def run(session,directory,resources):
        source=directory/'target-session.json';source.write_text(json.dumps(session))
        result=subprocess.run([shutil.which('java'),'-cp',os.pathsep.join((str(folder),gson)),'org.kneekura.observer.TargetCheck',str(source),str(resources)],capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
        return result.stdout
    return run


def target_session(tmp_path):
    resources=tmp_path/'resources';resources.mkdir()
    names=['twilightforest/entity/boss/Hydra.class','twilightforest/entity/boss/HydraPart.class','twilightforest/entity/boss/HydraHeadContainer.class','twilightforest/client/TFClientSetup.class','twilightforest/client/JappaPackReloadListener.class','twilightforest/client/renderer/entity/HydraRenderer.class','twilightforest/client/model/entity/HydraModel.class']
    archive=tmp_path/'twilightforest-derived.jar'
    with zipfile.ZipFile(archive,'w') as z:
        for name in names:
            data=('fixture bytes '+name).encode();z.writestr(name,data)
            path=resources/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    h=hashlib.sha256(archive.read_bytes()).hexdigest();coordinate='twilightforest-1.20.1-4.3.2508-remapped.jar'
    inv=dict(schema_version=1,kind='resolved_dependency_bytes',runtime_scope=SCOPE,export_receipt_hash='a'*64,
        resolved_inputs_hash='b'*64,workspace=str(tmp_path),source_generation='c'*64,configuration_fingerprint='d'*64,
        entries=[dict(order=n,coordinate=coordinate,scope=scope,namespace='UNKNOWN',stage='provider_derived',sha256=h,
            size_bytes=archive.stat().st_size,retention='original_archive_bytes') for n,scope in enumerate(('compile','runtime'))])
    selection=dict(schema_version=1,kind='u04_hydra_derived_dependency',coordinate=coordinate,sha256=h,
        provider_receipt_hash='e'*64,class_resources=names)
    contract=identity();contract.update(dependency_inventory_hash=hash_value(inv),target_selection_hash=hash_value(selection))
    session=dict(contract=contract,world='/fixture/run/saves/world',world_layout='client',dependency_inventory=inv,
        dependency_files=[dict(order=n,path=str(archive),sha256=h,size_bytes=archive.stat().st_size) for n in range(2)],
        target_selection=selection,target_dependency_probes=[dict(resource=name,sha256=hashlib.sha256((resources/name).read_bytes()).hexdigest()) for name in names],
        class_probes=[dict(resource='org/kneekura/fixture/Marker.class',sha256='a'*64)])
    return session,resources


def test_selected_dependency_preserves_unknown_namespace_but_matches_archive_and_resources(target_guard,tmp_path):
    session,resources=target_session(tmp_path)
    assert target_guard(session,tmp_path,resources)=='OK'


@pytest.mark.parametrize('fault',['selection_missing','selection_hash','extra_selection','receipt_hash','wrong_archive','wrong_coordinate','runtime_omitted',
    'probes_missing','probe_extra','probe_omitted','probe_reordered','probe_wrong_hash','loader_wrong_bytes','loader_missing','marker_overlap',
    'traversal','duplicate_resource','backslash','absolute_resource','not_class','probe_extra_field','wrong_layout','session_socket'])
def test_target_dependency_cannot_be_replaced_or_relabel_marker(target_guard,tmp_path,fault):
    s,resources=target_session(tmp_path);sel=s['target_selection'];probes=s['target_dependency_probes']
    if fault=='selection_missing':s.pop('target_selection')
    if fault=='selection_hash':s['contract']['target_selection_hash']='0'*64
    if fault=='extra_selection':sel['namespace']='named'
    if fault=='receipt_hash':sel['provider_receipt_hash']='bad'
    if fault=='wrong_archive':sel['sha256']='0'*64
    if fault=='wrong_coordinate':sel['coordinate']='unrelated:dependency:1'
    if fault=='runtime_omitted':s['dependency_inventory']['entries'][1]['scope']='compile'
    if fault=='probes_missing':s.pop('target_dependency_probes')
    if fault=='probe_extra':probes.append(copy.deepcopy(probes[0]))
    if fault=='probe_omitted':probes.pop()
    if fault=='probe_reordered':probes.reverse()
    if fault=='probe_wrong_hash':probes[0]['sha256']='0'*64
    if fault=='loader_wrong_bytes':(resources/sel['class_resources'][0]).write_bytes(b'different runtime resource')
    if fault=='loader_missing':(resources/sel['class_resources'][0]).unlink()
    if fault=='marker_overlap':s['class_probes'].append(copy.deepcopy(probes[0]))
    changes={'traversal':'../Hydra.class','backslash':'twilightforest\\Hydra.class','absolute_resource':'/Hydra.class','not_class':'Hydra.txt'}
    if fault in changes:sel['class_resources'][0]=changes[fault];probes[0]['resource']=changes[fault]
    if fault=='duplicate_resource':sel['class_resources'][1]=sel['class_resources'][0];probes[1]=copy.deepcopy(probes[0])
    if fault=='probe_extra_field':probes[0]['path']='/arbitrary'
    if fault=='wrong_layout':s['world_layout']='server'
    if fault=='session_socket':s['connection_policy']={}
    if fault!='selection_hash' and 'target_selection' in s:s['contract']['target_selection_hash']=hash_value(sel)
    s['contract']['dependency_inventory_hash']=hash_value(s['dependency_inventory'])
    assert target_guard(s,tmp_path,resources)=='BLOCKED'


@pytest.mark.parametrize('fault',['unrelated_labeled','missing_hydra_model'])
def test_selection_is_the_fixed_twilight_hydra_slice(target_guard,tmp_path,fault):
    s,resources=target_session(tmp_path)
    if fault=='unrelated_labeled':
        s['target_selection']['coordinate']='unrelated-marker.jar'
        for entry in s['dependency_inventory']['entries']:entry['coordinate']='unrelated-marker.jar'
    else:
        s['target_selection']['class_resources'].pop();s['target_dependency_probes'].pop()
    s['contract']['target_selection_hash']=hash_value(s['target_selection'])
    s['contract']['dependency_inventory_hash']=hash_value(s['dependency_inventory'])
    assert target_guard(s,tmp_path,resources)=='BLOCKED'


def test_schema3_startup_and_completed_capture_are_wired_before_readiness():
    observer=(JAVA/'ForgeObserver.java').read_text();probe=(JAVA/'ClientProbe.java').read_text()
    startup=observer.split('private void initialize()',1)[1].split('private void activate()',1)[0]
    assert 'TargetDependency.verify(session,identity,dependencyInventory,getClass().getClassLoader())' in startup
    lifecycle=observer.split('public void started(',1)[1].split('private void verifyServerEndpoint()',1)[0]
    assert '!server.isDedicatedServer()' in lifecycle and 'verifyDirectory' in lifecycle
    assert 'U04HydraProbe.capture(client,session,query,out)' in probe
    assert probe.index('out.addProperty("client_frame_end"') < probe.index('U04HydraProbe.capture')


def test_selection_rejects_delete_control_in_coordinate(target_guard,tmp_path):
    s,resources=target_session(tmp_path)
    coordinate=s['target_selection']['coordinate']+'\x7f'
    s['target_selection']['coordinate']=coordinate
    for entry in s['dependency_inventory']['entries']:entry['coordinate']=coordinate
    s['contract']['target_selection_hash']=hash_value(s['target_selection'])
    s['contract']['dependency_inventory_hash']=hash_value(s['dependency_inventory'])
    assert target_guard(s,tmp_path,resources)=='BLOCKED'


def test_schema3_wording_distinguishes_marker_build_from_selected_dependency():
    source=(JAVA/'ForgeObserver.java').read_text()
    assert 'Marker resource bytes match marker build; selected dependency resource bytes match its separate archive; post-transform memory is not attested' in source
    assert 'Observer ready; marker class resources verified against marker compile receipt; selected dependency resources verified against separate archive bytes' in source
