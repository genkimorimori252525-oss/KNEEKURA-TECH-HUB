"""Actual Java/Gson startup archive-byte verification, without a game launch."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from test_minecraft_dedicated_java import JAVA
from test_minecraft_dedicated_client_java import hash_value

SCOPE = 'TARGET_CODE_AND_DEPENDENCY_BYTES'


@pytest.fixture(scope='module')
def dependency_guard(tmp_path_factory):
    gson = os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file(): pytest.skip('Explicit cached GSON_JAR required')
    if not shutil.which('javac') or not shutil.which('java'): pytest.skip('Java17-compatible JDK required')
    folder = tmp_path_factory.mktemp('dependency-java')
    harness = folder / 'DependencyCheck.java'
    harness.write_text('''package org.kneekura.observer;
import com.google.gson.*;import java.nio.file.*;import java.nio.file.attribute.FileTime;
public final class DependencyCheck {
 public static void main(String[] args) {
  try {
   JsonObject session=JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonObject();
   Class<?> cls=Class.forName("org.kneekura.observer.DependencyInventory");
   Object guard=cls.getDeclaredMethod("verify",JsonObject.class,JsonObject.class).invoke(null,session,session.getAsJsonObject("contract"));
   if(!args[1].equals("none")) {
    Path p=Path.of(session.getAsJsonArray("dependency_files").get(0).getAsJsonObject().get("path").getAsString());
    if(args[1].equals("touch"))Files.setLastModifiedTime(p,FileTime.fromMillis(Files.getLastModifiedTime(p).toMillis()+5000));
    if(args[1].equals("replace")){Path other=p.resolveSibling("replacement.jar");Files.writeString(other,"replacement");Files.move(other,p,StandardCopyOption.REPLACE_EXISTING);}
    if(args[1].equals("remove"))Files.delete(p);
    if(args[1].equals("symlink")){Path other=p.resolveSibling("original.jar");Files.move(p,other);Files.createSymbolicLink(p,other);}
   }
   guard.getClass().getDeclaredMethod("checkUnchanged").invoke(guard);
   System.out.print("OK");
  } catch(Exception e) { System.out.print("BLOCKED"); }
 }
}''')
    sources = [JAVA / 'DedicatedSession.java']
    if (JAVA / 'DependencyInventory.java').exists(): sources.append(JAVA / 'DependencyInventory.java')
    result = subprocess.run([shutil.which('javac'),'--release','17','-cp',gson,'-d',str(folder),*map(str,sources),str(harness)],capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    def run(session, directory, action='none'):
        path = directory / 'session.json'; path.write_text(json.dumps(session))
        result = subprocess.run([shutil.which('java'),'-cp',os.pathsep.join((str(folder),gson)),'org.kneekura.observer.DependencyCheck',str(path),action],capture_output=True,text=True)
        assert result.returncode == 0,result.stdout+result.stderr
        return result.stdout
    return run


def sample(tmp_path):
    jar = tmp_path / 'dependency.jar';jar.write_bytes(b'original fixture dependency bytes')
    digest=hashlib.sha256(jar.read_bytes()).hexdigest()
    entries=[dict(order=i,coordinate='example:dependency:1',scope=scope,namespace='official',stage='resolved',sha256=digest,size_bytes=jar.stat().st_size,retention='original_archive_bytes') for i,scope in enumerate(('compile','runtime'))]
    inventory=dict(schema_version=1,kind='resolved_dependency_bytes',runtime_scope=SCOPE,export_receipt_hash='a'*64,resolved_inputs_hash='b'*64,workspace=str(tmp_path),source_generation='c'*64,configuration_fingerprint='d'*64,entries=entries)
    identity=dict(schema_version=2,session_role='dedicated_server',physical_side='server',logical_side='server',runtime_scope=SCOPE,dependency_inventory_hash=hash_value(inventory),dirty_hash='c'*64)
    return dict(contract=identity,dependency_inventory=inventory,dependency_files=[dict(order=e['order'],path=str(jar),sha256=digest,size_bytes=e['size_bytes']) for e in entries])


def resign(s):
    s['contract']['dependency_inventory_hash']=hash_value(s['dependency_inventory'])


def test_java_verifies_ordered_inventory_with_repeated_jar_across_scopes(dependency_guard,tmp_path):
    assert dependency_guard(sample(tmp_path),tmp_path)=='OK'


def test_java_preserves_legacy_without_dependency_scope(dependency_guard,tmp_path):
    assert dependency_guard({'contract':{'schema_version':1}},tmp_path)=='OK'


@pytest.mark.parametrize('fault',['scope_missing','scope_wrong','hash_missing','hash_wrong','inventory_missing','files_missing','inventory_extra','file_extra','omitted','extra','reordered','duplicate_order','wrong_path_hash','wrong_size','wrong_order_type','absent','symlink','relative','noncanonical','entry_order','entry_hash','entry_size','entry_scope','entry_retention','entry_extra','empty','boolean_size','float_size','source_generation','archive_limit','inventory_scope'])
def test_java_rejects_incomplete_or_mismatched_archive_binding(dependency_guard,tmp_path,fault):
    s=sample(tmp_path);inventory=s['dependency_inventory'];files=s['dependency_files'];entry=inventory['entries'][0]
    if fault=='scope_missing':s['contract'].pop('runtime_scope')
    if fault=='scope_wrong':s['contract']['runtime_scope']='FULL_BYTECODE_VERIFIED'
    if fault=='hash_missing':s['contract'].pop('dependency_inventory_hash')
    if fault=='hash_wrong':s['contract']['dependency_inventory_hash']='0'*64
    if fault=='inventory_missing':s.pop('dependency_inventory')
    if fault=='files_missing':s.pop('dependency_files')
    if fault=='inventory_extra':inventory['extra']=True;resign(s)
    if fault=='file_extra':files[0]['extra']=True
    if fault=='omitted':files.pop()
    if fault=='extra':files.append(copy.deepcopy(files[0]))
    if fault=='reordered':files.reverse()
    if fault=='duplicate_order':files[1]['order']=0
    if fault=='wrong_path_hash':Path(files[0]['path']).write_bytes(b'X'*entry['size_bytes'])
    if fault=='wrong_size':files[0]['size_bytes']+=1
    if fault=='wrong_order_type':files[0]['order']=False
    if fault=='absent':Path(files[0]['path']).unlink()
    if fault=='symlink':
        p=Path(files[0]['path']);target=p.with_name('target.jar');p.rename(target);p.symlink_to(target)
    if fault=='relative':files[0]['path']='dependency.jar'
    if fault=='noncanonical':files[0]['path']=str(tmp_path)+'/../'+tmp_path.name+'/dependency.jar'
    if fault=='entry_order':entry['order']=1;resign(s)
    if fault=='entry_hash':entry['sha256']='0'*64;resign(s)
    if fault=='entry_size':entry['size_bytes']+=1;resign(s)
    if fault=='entry_scope':entry['scope']='arbitrary';resign(s)
    if fault=='entry_retention':entry['retention']='decompiled';resign(s)
    if fault=='entry_extra':entry['path']=files[0]['path'];resign(s)
    if fault=='empty':inventory['entries']=[];files.clear();resign(s)
    if fault=='boolean_size':entry['size_bytes']=True;files[0]['size_bytes']=True;resign(s)
    if fault=='float_size':entry['size_bytes']=1.0;files[0]['size_bytes']=1.0;resign(s)
    if fault=='source_generation':inventory['source_generation']='e'*64;resign(s)
    if fault=='archive_limit':entry['size_bytes']=512*1024*1024+1;files[0]['size_bytes']=entry['size_bytes'];resign(s)
    if fault=='inventory_scope':inventory['runtime_scope']='FULL_BYTECODE_VERIFIED';resign(s)
    assert dependency_guard(s,tmp_path)=='BLOCKED'


@pytest.mark.parametrize('action',['touch','replace','remove','symlink'])
def test_java_invalidates_observed_file_identity_change_without_rehash_claim(dependency_guard,tmp_path,action):
    assert dependency_guard(sample(tmp_path),tmp_path,action)=='BLOCKED'


def test_java_receiver_keeps_own_dependency_inventory(dependency_guard,tmp_path):
    s=sample(tmp_path);s['contract'].update(session_role='dedicated_client',physical_side='client',logical_side='client')
    assert dependency_guard(s,tmp_path)=='OK'


def test_observer_dependency_verifier_is_part_of_startup_and_every_request():
    source=(JAVA/'ForgeObserver.java').read_text()
    startup=source.split('private void initialize()',1)[1].split('private void activate()',1)[0]
    assert 'dependencyInventory=DependencyInventory.verify(session,identity);' in startup
    request=source.split('private String request(',1)[1].split('private String receiverRequest(',1)[0]
    assert request.index('checkDependencyIdentity();') < request.index('if(role.equals("dedicated_client"))')


def test_java_accepts_registered_uppercase_jar_suffix(dependency_guard,tmp_path):
    s=sample(tmp_path);old=Path(s['dependency_files'][0]['path']);new=old.with_suffix('.JAR');old.rename(new)
    for entry in s['dependency_files']:entry['path']=str(new)
    assert dependency_guard(s,tmp_path)=='OK'


def test_java_requires_both_export_scopes(dependency_guard,tmp_path):
    s=sample(tmp_path)
    for entry in s['dependency_inventory']['entries']:entry['scope']='compile'
    resign(s)
    assert dependency_guard(s,tmp_path)=='BLOCKED'


@pytest.mark.parametrize('suffix',['.zip','.ZIP'])
def test_java_retains_required_original_mapping_archive(dependency_guard,tmp_path,suffix):
    s=sample(tmp_path);old=Path(s['dependency_files'][0]['path']);new=old.with_suffix(suffix);old.rename(new)
    for entry in s['dependency_files']:entry['path']=str(new)
    assert dependency_guard(s,tmp_path)=='OK'
