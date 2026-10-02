"""Regression cases found while reviewing the connected end-to-end paths."""
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_minecraft_index import class_profile
from test_minecraft_workspace import project, export_data
from test_minecraft_execution import local
from test_minecraft_providers import config
from kneekura_tech_hub.minecraft import index, providers
from kneekura_tech_hub.minecraft.storage import Store, ContractError, capture_profile, digest, key_for
from kneekura_tech_hub.minecraft.workspace import import_resolved, workspace_fingerprint


def test_resolved_artifact_changed_between_import_and_capture_is_unavailable(project,tmp_path):
    import zipfile
    jar=project/'dep.jar'
    with zipfile.ZipFile(jar,'w') as z: z.writestr('Before.java','class Before{}')
    data=export_data(project); data['output_roots']=[]
    data['artifacts']=[{'path':str(jar),'coordinate':'dep:mod:1','scope':'runtime','namespace':'mojmap','sha256':digest(jar.read_bytes())}]
    manifest=import_resolved(data,project)
    with zipfile.ZipFile(jar,'w') as z: z.writestr('After.java','class After{}')
    captured=capture_profile(manifest,project,Store(tmp_path/'store'))
    assert not captured['coverage']['complete']
    assert not any(d['path']=='After.java' for d in captured['documents'])


def test_derived_cache_cannot_relabel_output_namespace(class_profile):
    store,p,base=class_profile; idx=index.prepare_index(p,store)['index_snapshot_id']
    def produce(argv,cwd,**kw):
        out=Path(argv[-1]); out.mkdir(); (out/'Example.java').write_text('class Example{}')
        return {'exit_code':0,'completed':True,'stdout':b''}
    cfg=config(base)
    out=providers.prepare_transform(store,idx,'mod','decompile',cfg,runner=produce)
    receipt=store.json(out['receipt_hash']); receipt['output_namespace']='srg'
    cache=next((store.root/'providers').glob('*.json')); cache.write_text(json.dumps({'receipt_hash':store.put_json(receipt)}))
    with pytest.raises(ContractError): providers.prepare_transform(store,idx,'mod','decompile',cfg,runner=produce)


def test_directory_build_inventory_has_one_cross_language_order(local):
    from kneekura_tech_hub.minecraft.execution import execute
    from kneekura_tech_hub.minecraft.workspace import file_hash
    store,reg,root=local
    wrapper=root/'gradlew'; wrapper.write_text('#!/bin/sh\nmkdir -p build/classes/a\nprintf a > build/classes/a/Z.class\nprintf b > build/classes/z.class\n')
    reg.update(wrapper_sha256=file_hash(wrapper),build_outputs=['build/classes'])
    out=execute(store,reg,kind='compile',request_id='sorted-directory')
    paths=[r['path'] for r in store.json(out['outputs'][0]['content_hash'])]
    assert paths==sorted(paths)


def test_runtime_workdir_does_not_invalidate_source_fingerprint(project):
    before=workspace_fingerprint(project)
    root=project/'.kneekura-runs/example/some-mod/src'; root.mkdir(parents=True)
    (root/'Something.java').write_text('runtime incidental file')
    assert workspace_fingerprint(project)==before


def test_provider_process_cannot_leave_late_writing_descendant(tmp_path):
    if os.name=='nt': pytest.skip('POSIX group regression; Windows cleanup requires Windows runner')
    from kneekura_tech_hub.minecraft.process import run_process
    marker=tmp_path/'late'
    ready=tmp_path/'ready'
    child='import time,pathlib; pathlib.Path('+repr(str(ready))+').touch(); time.sleep(0.5); pathlib.Path('+repr(str(marker))+').write_text("leaked")'
    parent='import subprocess,sys,time,pathlib; subprocess.Popen([sys.executable,"-c",'+repr(child)+']); p=pathlib.Path('+repr(str(ready))+')\nwhile not p.exists(): time.sleep(0.01)'
    out=run_process([sys.executable,'-c',parent],tmp_path,timeout=2)
    time.sleep(0.7)
    assert (tmp_path/'ready').exists() and not marker.exists()
    assert out['exit_code']==0


def test_handshake_supplies_json_object_to_actual_java_handler(tmp_path):
    from kneekura_tech_hub.minecraft.runtime import BridgeClient
    from test_minecraft_verification import contract
    java=Path('departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer/BridgeTransport.java')
    main=tmp_path/'Handshake.java'
    main.write_text('''import org.kneekura.observer.BridgeTransport;
public class Handshake { public static void main(String[] a) throws Exception {
 var s=new BridgeTransport(a[0],a[1],a[2],(path,body,nonce)-> {
   if (!body.equals("{}")) throw new IllegalStateException("Not a JSON request object");
   return "{\\"ready\\":true}";
 }); System.out.println(s.start()); System.out.flush(); Thread.sleep(30000); s.close();
}}''')
    subprocess.run([shutil.which('javac'),'--release','17','-d',str(tmp_path),str(java),str(main)],check=True,capture_output=True)
    c=contract(); token='a'*64
    peer=subprocess.Popen([shutil.which('java'),'-cp',str(tmp_path),'Handshake',token,c['run_id'],c['session_epoch']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        port=int(peer.stdout.readline().strip())
        result=BridgeClient(f'http://127.0.0.1:{port}',token,c).request('/v1/handshake')
        assert result['ready'] is True
    finally: peer.terminate(); peer.wait(timeout=5)


def test_core_specific_database_failure_retains_research_without_dsn(class_profile):
    from kneekura_tech_hub.minecraft.core_bridge import context
    class DatabaseConnectionError(Exception): pass
    store,p,_=class_profile; idx=index.prepare_index(p,store)['index_snapshot_id']
    def fail(*a,**kw): raise DatabaseConnectionError('password=DO_NOT_PRINT')
    out=context(store,idx,'attack',entity_id='ke:attack',repository=object(),explain=fail)
    assert out['status']=='PARTIAL' and out['research']['results']
    assert 'DO_NOT_PRINT' not in json.dumps(out)

def test_runtime_rejects_old_index_even_with_fresh_build_receipt(class_profile,tmp_path):
    from kneekura_tech_hub.minecraft import runtime
    from test_minecraft_verification import contract
    from kneekura_tech_hub.minecraft.workspace import file_hash
    store,p,root=class_profile; idx=index.prepare_index(p,store)['index_snapshot_id']
    c=contract(); c.update(profile_id=p['profile_id'],index_snapshot_id=idx,
        dirty_hash=workspace_fingerprint(root),build_artifact_hash=file_hash(root/'mod.jar'),
        config_hash=key_for([]),adapter_id='kneekura-forge-observer',adapter_version='1.0.0')
    receipt={'request':{'kind':'compile','workspace':str(root)},'result':{'outcome':'PASS'},
             'source_generation':c['dirty_hash'],'source_generation_after':c['dirty_hash'],
             'outputs':[{'content_hash':c['build_artifact_hash']}]}
    reg={'workspace':str(root),'build_artifact':'mod.jar','build_receipt_hash':store.put_json(receipt)}
    directory=root/'session'; directory.mkdir()
    assert p['manifest']['dirty_hash']!=c['dirty_hash']
    with pytest.raises(ContractError,match='Index source'):
        runtime.create_session(store,reg,c,directory=directory)

def test_read_only_observe_route_cannot_dispatch_a_mutation(tmp_path):
    from test_minecraft_cli import run_cli
    p,out=run_cli(tmp_path/'cas','observe','--session',str(tmp_path/'missing-session.json'),'--operation','command','--query-json','{"command_id":"summon","operation_id":"one"}')
    assert p.returncode!=0
    # Rejection must occur at the route boundary, before loading a session.
    assert (out and 'read-only' in str(out).lower()) or 'invalid choice' in p.stderr
    assert not (tmp_path/'cas').exists()
