import importlib
import json
import sys
import zipfile
from pathlib import Path
import pytest
from test_minecraft_index import class_profile
from kneekura_tech_hub.minecraft import index
from kneekura_tech_hub.minecraft.storage import ContractError, Store, digest


def api(name='providers'):
    spec = importlib.util.find_spec('kneekura_tech_hub.minecraft.'+name)
    assert spec is not None, name+' adapter not implemented'
    return importlib.import_module(spec.name)


def config(tmp_path):
    tool = tmp_path/'trusted-tool.jar'; tool.write_bytes(b'protocol-fixture-not-a-decompiler')
    return {'java':'java','jar':str(tool),'jar_sha256':digest(tool.read_bytes()),
            'version':'protocol-test','allow_execute':True,'memory_mib':256,'threads':1}


def test_external_provider_output_is_full_readable_and_has_exact_parents(class_profile):
    store,p,base = class_profile; idx = index.prepare_index(p,store)
    calls = []
    def fixture_runner(argv,cwd,**kwargs):
        calls.append(argv)
        output = Path(argv[-1]); output.mkdir()
        (output/'Example.java').write_text('class Example { int attack(int x) { return x+1; } }')
        return {'exit_code':0,'completed':True,'stdout':b'fixture wire protocol only','timed_out':False}
    r = api().prepare_transform(store,idx['index_snapshot_id'],'mod','decompile',config(base),runner=fixture_runner)
    assert r['status'] == 'OK' and r['parent_index_snapshot_id'] == idx['index_snapshot_id']
    found = index.search(store,r['index_snapshot_id'],'attack')
    derived = [d for d in found['results'] if d['role']=='decompiled_source'][0]
    assert derived['source_binary_match'] == 'CANDIDATE'
    assert derived['derivation']['input_artifact_hash'] == p['roots'][1]['artifact_hash']
    text = index.inspect_document(store,r['index_snapshot_id'],derived['document_id'])
    assert 'return x+1' in text['results'][0]['text']
    assert '--remove-synthetic=0' in calls[0]
    cached = api().prepare_transform(store,idx['index_snapshot_id'],'mod','decompile',config(base),runner=fixture_runner)
    assert cached['cache_hit'] is True and len(calls)==1


def test_unregistered_provider_is_never_executed(class_profile):
    store,p,base = class_profile; idx=index.prepare_index(p,store)
    c=config(base); c['allow_execute']=False
    with pytest.raises(ContractError,match='allow_execute'):
        api().prepare_transform(store,idx['index_snapshot_id'],'mod','decompile',c)


def test_provider_hash_drift_rejected_before_execution(class_profile):
    store,p,base=class_profile; idx=index.prepare_index(p,store); c=config(base)
    Path(c['jar']).write_bytes(b'changed tool')
    with pytest.raises(ContractError,match='tool'):
        api().prepare_transform(store,idx['index_snapshot_id'],'mod','decompile',c)


def test_provider_failure_does_not_cache_partial_output(class_profile):
    store,p,base=class_profile; idx=index.prepare_index(p,store)
    def fail(argv,cwd,**kw):
        out=Path(argv[-1]); out.mkdir(); (out/'Half.java').write_text('partial')
        return {'exit_code':1,'completed':True,'stdout':b'failed','timed_out':False}
    r=api().prepare_transform(store,idx['index_snapshot_id'],'mod','decompile',config(base),runner=fail)
    assert r['status']=='ERROR' and 'index_snapshot_id' not in r
    assert not list((store.root/'providers').glob('*.json'))


def test_provider_output_zip_traversal_is_not_imported(class_profile):
    store,p,base=class_profile; idx=index.prepare_index(p,store)
    def bad(argv,cwd,**kw):
        out=Path(argv[-1]); out.mkdir()
        with zipfile.ZipFile(out/'sources.jar','w') as z: z.writestr('../Escape.java','class Bad{}')
        return {'exit_code':0,'completed':True,'stdout':b'', 'timed_out':False}
    r=api().prepare_transform(store,idx['index_snapshot_id'],'mod','decompile',config(base),runner=bad)
    assert r['status']=='ERROR'


def test_remap_plan_rejects_namespace_mismatch(class_profile):
    store,p,base=class_profile; idx=index.prepare_index(p,store)
    mappings=store.put(b'tiny\t2\t0\tintermediary\tmojmap\nc\ta\tdemo/Example\n')
    with pytest.raises(ContractError,match='namespace'):
        api().prepare_transform(store,idx['index_snapshot_id'],'mod','remap',config(base),
                                mapping_hash=mappings,from_namespace='intermediary',to_namespace='mojmap')


def test_bounded_process_real_success_and_no_shell(tmp_path):
    r=api('process').run_process([sys.executable,'-c','import sys; print(sys.argv[1])','$(touch BAD)'],tmp_path,
                                  timeout=5,max_output_bytes=10000)
    assert r['exit_code']==0 and r['stdout'].strip()==b'$(touch BAD)'
    assert not (tmp_path/'BAD').exists()


def test_bounded_process_timeout_and_output_caps(tmp_path):
    m=api('process')
    timeout=m.run_process([sys.executable,'-c','import time; time.sleep(9)'],tmp_path,timeout=0.1,max_output_bytes=1000)
    assert timeout['timed_out'] is True and not timeout['completed']
    noisy=m.run_process([sys.executable,'-c','import sys; sys.stdout.write("X"*10000)'],tmp_path,timeout=2,max_output_bytes=100)
    assert noisy['output_limited'] is True and len(noisy['stdout'])<=100


def test_cache_tampering_is_not_reused(class_profile):
    store,p,base=class_profile; idx=index.prepare_index(p,store)
    def produce(argv,cwd,**kw):
        out=Path(argv[-1]); out.mkdir(); (out/'Example.java').write_text('class Example{}')
        return {'exit_code':0,'completed':True,'stdout':b'', 'timed_out':False}
    cfg=config(base)
    api().prepare_transform(store,idx['index_snapshot_id'],'mod','decompile',cfg,runner=produce)
    cache=next((store.root/'providers').glob('*.json'))
    payload=json.loads(cache.read_text()); payload['receipt_hash']='f'*64; cache.write_text(json.dumps(payload))
    with pytest.raises((ContractError,OSError)):
        api().prepare_transform(store,idx['index_snapshot_id'],'mod','decompile',cfg,runner=produce)
