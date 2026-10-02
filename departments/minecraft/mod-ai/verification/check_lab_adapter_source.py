#!/usr/bin/env python3
"""Paired-repository adapter source fixture. Never launches Minecraft or claims runtime proof."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from kneekura_tech_hub.minecraft import experiment_adapter, experiment_bridge, index, storage
from kneekura_tech_hub.minecraft.storage import Store, canonical, digest
from test_minecraft_experiment_contract import request
from test_minecraft_storage import manifest


def verify(lab_root, work_root):
    lab_root=Path(lab_root).resolve()
    work_root=Path(work_root).resolve()
    (work_root/'src').mkdir(); (work_root/'src/Fixture.java').write_text('class Fixture {}')
    store=Store(work_root/'cas'); m=manifest(); m['workspace_revision']='a'*40
    profile=storage.capture_profile(m,work_root,store); idx=index.prepare_index(profile,store)['index_snapshot_id']
    req=request(); req['visual_rig']['fov']=60.0; req['initial_state'][0]['rotation']=[-0.0,0.0]
    req['target'].update(profile_id=profile['profile_id'],index_snapshot_id=idx,source_revision=m['workspace_revision'],dirty_hash=m['dirty_hash'],build_artifact_hash=store.put(b'fixture-build'),config_hash=store.put(b'fixture-config'),resource_hash=store.put(b'fixture-resource'))
    prepared=experiment_bridge.prepare_experiment(store,req)
    for name in ('runtime','inputs'): (work_root/name).mkdir()
    owner=work_root/'owner.json';owner.write_bytes(canonical({'schemaVersion':1,'runtimeRoot':str(work_root/'runtime'),'inputRoot':str(work_root/'inputs'),'run':None}))
    node=Path(shutil.which('node')).resolve()
    with node.open('rb') as f: node_hash=hashlib.file_digest(f,'sha256').hexdigest()
    registry={'schema_version':1,'enabled':True,'backend':experiment_adapter.BACKEND,'workspace':str(lab_root),'source_revision':'a'*40,
      'executable':str(node),'executable_hash':node_hash,'module_hashes':{name:digest((lab_root/'debug-workspace/bridge'/name).read_bytes()) for name in experiment_adapter.MODULES},
      'owner_file':str(owner),'owner_hash':digest(owner.read_bytes()),'timeout_seconds':10}
    first=experiment_adapter.register_request(store,registry,prepared['request_hash'])
    assert first['status']=='OK',first
    assert first['reported']['status']=='REGISTERED'
    second=experiment_adapter.register_request(store,registry,prepared['request_hash'])
    inspection=experiment_adapter.inspect_registration(store,registry,prepared['request_hash'])
    assert first['reported']==second['reported']==inspection['reported']
    assert first['runtime_attestation']=='NOT_ESTABLISHED'
    assert (work_root/'inputs'/prepared['request_hash']/'request.json').read_bytes()==canonical(req)
    return {'scope':'SOURCE_FIXTURE_ONLY','status':'PASS','request_hash':prepared['request_hash'],
      'registration_hash':first['reported']['registrationHash'],'numeric_cases':['60.0','-0.0','0.0'],
      'runtime_attestation':'NOT_ESTABLISHED','minecraft_launch':'NOT_RUN'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--lab-root',required=True);args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='lab-adapter-source-') as temporary:
        print(json.dumps(verify(args.lab_root,temporary),sort_keys=True))
