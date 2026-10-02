"""Offline dependency-byte scope and receipt binding; no game, Gradle or downloads."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

from kneekura_tech_hub.minecraft import storage, verification, runtime, workspace
from kneekura_tech_hub.minecraft.storage import Store, ContractError, canonical, key_for, digest
from test_minecraft_workspace import project, export_data

SCOPE='TARGET_CODE_AND_DEPENDENCY_BYTES'


def api():
    spec=importlib.util.find_spec('kneekura_tech_hub.minecraft.dependencies')
    assert spec is not None, 'immutable resolved dependency inventory adapter is missing'
    return importlib.import_module(spec.name)


def register_export(store,root,raw,reg):
    destination=root/'build/kneekura/resolved-inputs.json'; destination.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(raw,indent=2).encode(); destination.write_bytes(data)
    source=workspace.workspace_fingerprint(root); config=workspace.configuration_fingerprint(root)
    receipt={'schema_version':1,'request':{'kind':'export','workspace':str(root),'source_generation':source,
             'configuration_fingerprint':config},'source_generation':source,'source_generation_after':source,
             'process':{'completed':True,'exit_code':0},'result':{'outcome':'PASS'},
             'outputs':[{'path':str(destination),'content_hash':store.put(data)}]}
    reg['export_receipt_hash']=store.put_json(receipt)
    return receipt


@pytest.fixture
def resolved(project,tmp_path,monkeypatch):
    root=project; store=Store(tmp_path/'cas'); raw=export_data(root)
    monkeypatch.setattr(workspace,'_revision',lambda root:'a'*40)
    output=root/'build/classes/java/main'; output.mkdir(parents=True); (output/'Target.class').write_bytes(b'fixture class bytes')
    deps=tmp_path/'dependencies'; deps.mkdir(); paths=[]
    for name in ('a','b'):
        p=deps/(name+'.jar')
        with zipfile.ZipFile(p,'w') as archive: archive.writestr('fixture.txt',name)
        paths.append(p)
    raw['resource_roots'].append('src/generated/resources')
    raw['artifacts']=[{'path':str(p),'scope':scope,'coordinate':'fixture:'+p.stem+':1',
                      'sha256':digest(p.read_bytes()),'namespace':'unknown','stage':'resolved_userdev'}
                     for p,scope in [(paths[1],'compile'),(paths[0],'runtime'),(paths[1],'runtime')]]
    reg={'workspace':str(root),'runtime_scope':SCOPE,'build_artifact':'build/classes/java/main'}
    compile_hash=store.put_json([{'path':'Target.class','hash':store.put(b'fixture class bytes')}])
    source=workspace.workspace_fingerprint(root)
    reg['build_receipt_hash']=store.put_json({'request':{'workspace':str(root),'kind':'compile'},
        'source_generation':source,'source_generation_after':source,'result':{'outcome':'PASS'},
        'outputs':[{'path':'build/classes/java/main','content_hash':compile_hash}]})
    register_export(store,root,raw,reg)
    return store,root,raw,reg,paths


def capture(resolved):
    store,root,raw,reg,paths=resolved; result=api().prepare_dependency_inventory(store,reg)
    reg['dependency_inventory_hash']=result['dependency_inventory_hash']
    return result


def test_complete_ordered_export_and_original_archives_are_retained(resolved):
    store,root,raw,reg,paths=resolved; result=capture(resolved); inventory=result['dependency_inventory']
    assert inventory['export_receipt_hash']==reg['export_receipt_hash']
    assert inventory['resolved_inputs_hash']==digest((root/'build/kneekura/resolved-inputs.json').read_bytes())
    assert inventory['source_generation']==workspace.workspace_fingerprint(root)
    assert inventory['configuration_fingerprint']==workspace.configuration_fingerprint(root)
    assert inventory['runtime_scope']==SCOPE and key_for(inventory)==result['dependency_inventory_hash']
    assert [r['order'] for r in inventory['entries']]==[0,1,2]
    assert [(r['coordinate'],r['scope'],r['sha256']) for r in inventory['entries']]==[(r['coordinate'],r['scope'],r['sha256']) for r in raw['artifacts']]
    assert [r['path'] for r in result['dependency_files']]==[r['path'] for r in raw['artifacts']]
    for entry in inventory['entries']:
        assert len(store.read(entry['sha256']))==entry['size_bytes']
        assert entry['sha256'] in store.pinned_hashes()
        assert 'path' not in entry
    assert api().validate_dependency_inventory(store,reg)==result


@pytest.mark.parametrize('fault',['omit','extra','reorder','coordinate','scope','hash','size','receipt','raw_hash'])
def test_inventory_cannot_weaken_or_replace_complete_registered_export(resolved,fault):
    store,root,raw,reg,paths=resolved; result=capture(resolved); value=deepcopy(result['dependency_inventory'])
    if fault=='omit': value['entries'].pop()
    if fault=='extra': value['entries'].append(deepcopy(value['entries'][0]))
    if fault=='reorder': value['entries'].reverse()
    if fault in ('coordinate','scope'): value['entries'][0][fault]='wrong'
    if fault=='hash': value['entries'][0]['sha256']='a'*64
    if fault=='size': value['entries'][0]['size_bytes']+=1
    if fault=='receipt': value['export_receipt_hash']='e'*64
    if fault=='raw_hash': value['resolved_inputs_hash']=store.put_json(raw)
    reg['dependency_inventory_hash']=store.put_json(value)
    with pytest.raises(ContractError): api().validate_dependency_inventory(store,reg)


@pytest.mark.parametrize('fault',['changed_jar','missing_jar','symlink','stale_source','stale_config','changed_export','missing_export','unresolved','no_runtime','bad_scope','no_receipt','failed_receipt','foreign_receipt','stale_receipt','changed_cas'])
def test_missing_changed_unresolved_or_stale_runtime_input_fails_closed(resolved,fault):
    store,root,raw,reg,paths=resolved; result=capture(resolved)
    if fault=='changed_jar': paths[0].write_bytes(b'changed')
    if fault=='missing_jar': paths[0].rename(paths[0].with_suffix('.moved'))
    if fault=='symlink': paths[0].rename(paths[0].with_suffix('.moved')); paths[0].symlink_to(paths[0].with_suffix('.moved'))
    if fault=='stale_source': (root/'src/main/java/example/Mob.java').write_text('changed')
    if fault=='stale_config': (root/'build.gradle').write_text('changed')
    if fault=='changed_export': (root/'build/kneekura/resolved-inputs.json').write_bytes(canonical(raw))
    if fault=='missing_export': (root/'build/kneekura/resolved-inputs.json').rename(root/'build/kneekura/moved.json')
    if fault in ('unresolved','no_runtime','bad_scope'):
        if fault=='unresolved': raw['unresolved']=[{'scope':'runtime','reason':'missing'}]
        if fault=='no_runtime': raw['artifacts']=[r for r in raw['artifacts'] if r['scope']=='compile']
        if fault=='bad_scope': raw['artifacts'][0]['scope']='unknown'
        register_export(store,root,raw,reg)
    if fault=='no_receipt': reg.pop('export_receipt_hash')
    if fault in ('failed_receipt','foreign_receipt','stale_receipt'):
        receipt=store.json(reg['export_receipt_hash'])
        if fault=='failed_receipt': receipt['result']['outcome']='BLOCKED'
        if fault=='foreign_receipt': receipt['request']['workspace']=str(root.parent)
        if fault=='stale_receipt': receipt['source_generation_after']='a'*64
        reg['export_receipt_hash']=store.put_json(receipt)
    if fault=='changed_cas': store.blob_path(raw['artifacts'][0]['sha256']).write_bytes(b'corrupt')
    with pytest.raises(ContractError): api().validate_dependency_inventory(store,reg)


def test_target_profile_is_explicit_and_does_not_relabel_broad_unknown(resolved):
    store,root,raw,reg,paths=resolved
    broad=storage.capture_profile(workspace.import_resolved(raw,root),root,store); before=canonical(broad)
    assert broad['identity_status']=='UNKNOWN' and broad['coverage']['complete'] is False
    profile=api().prepare_target_profile(store,reg,physical_side='server')
    assert canonical(broad)==before
    assert profile['identity_status']=='PINNED_TARGET_CODE'
    assert profile['coverage']['complete'] is False and profile['coverage']['target_complete'] is True
    assert profile['coverage']['scope']=='TARGET_CODE'
    assert profile['manifest']['runtime_scope']==SCOPE
    assert profile['manifest']['dependency_inventory_hash']
    assert not any(r['id'].startswith('dependency:') for r in profile['roots'])
    assert profile['coverage']['absent_target_roots'][0]['id']=='resource_roots:1'
    runtime._pinned_dedicated_profile(profile)
    with pytest.raises(ContractError): runtime._pinned_dedicated_profile(broad)


@pytest.mark.parametrize('fault',['scope','inventory','target_complete','whole_complete','status','loader'])
def test_profile_scope_cannot_be_forged_by_relabeling(resolved,fault):
    store,root,raw,reg,paths=resolved; profile=api().prepare_target_profile(store,reg)
    if fault=='scope': profile['manifest']['runtime_scope']='WHOLE_RUNTIME'
    if fault=='inventory': profile['manifest']['dependency_inventory_hash']='unknown'
    if fault=='target_complete': profile['coverage']['target_complete']=False
    if fault=='whole_complete': profile['coverage']['complete']=True
    if fault=='status': profile['identity_status']='PINNED'
    if fault=='loader': profile['manifest']['loader_version']='47.4.x'
    profile.pop('profile_id'); profile.pop('profile_hash'); profile['profile_id']=profile['profile_hash']=key_for(profile)
    with pytest.raises(ContractError): runtime._pinned_dedicated_profile(profile)


@pytest.mark.parametrize('field,value',[('runtime_scope',None),('runtime_scope','WHOLE_RUNTIME'),('dependency_inventory_hash',None),('dependency_inventory_hash','unknown')])
def test_v2_scope_and_inventory_are_strict_identity_authority(field,value):
    from test_minecraft_dedicated_identity import dedicated_contract
    c=dedicated_contract(); c.update(runtime_scope=SCOPE,dependency_inventory_hash='d'*64)
    assert {'runtime_scope','dependency_inventory_hash'} <= set(verification.identity_fields(c))
    actual=deepcopy(c); actual[field]=value
    assert verification._identity_errors(c,{'identity':actual})
    c[field]=value
    assert verification._identity_errors(c,{'identity':c})


@pytest.mark.parametrize('side',['server','client'])
def test_session_contains_exact_immutable_inventory_and_private_mapping(pair,side):
    data=pair[side]; store=pair['store']; c=data['prepared']['contract']; reg=data['registry']
    s=runtime.create_session(store,reg,c,directory=Path(data['owned']['directory']))
    assert c['runtime_scope']==SCOPE and c['dependency_inventory_hash']==reg['dependency_inventory_hash']
    assert key_for(s['dependency_inventory'])==c['dependency_inventory_hash']
    assert s['dependency_inventory']['source_generation']==c['dirty_hash']
    assert len(s['dependency_files'])==len(s['dependency_inventory']['entries'])==2
    assert 'dependency_files' not in c
    assert all('path' not in row for row in s['dependency_inventory']['entries'])


@pytest.mark.parametrize('fault',['scope','hash','profile_inventory','export_receipt','jar','omit_inventory','source'])
def test_session_dependency_authority_fails_before_file_or_launch(pair,fault):
    data=pair['client']; store=pair['store']; c=deepcopy(data['prepared']['contract']); reg=deepcopy(data['registry'])
    if fault=='scope': reg['runtime_scope']='WHOLE_RUNTIME'
    if fault=='hash': reg['dependency_inventory_hash']=pair['server']['registry']['dependency_inventory_hash']
    if fault=='profile_inventory':
        snapshot=store.json(c['index_snapshot_id']); profile=snapshot['profile']
        profile['manifest']['dependency_inventory_hash']=pair['server']['registry']['dependency_inventory_hash']
        profile.pop('profile_id'); profile.pop('profile_hash'); profile['profile_id']=profile['profile_hash']=key_for(profile)
        c['profile_id']=profile['profile_id']; c['index_snapshot_id']=store.put_json(snapshot)
    if fault=='export_receipt': reg['export_receipt_hash']=pair['server']['registry']['export_receipt_hash']
    if fault=='jar':
        value=store.json(reg['dependency_inventory_hash'])
        raw=store.json(value['resolved_inputs_hash']); Path(raw['artifacts'][0]['path']).write_bytes(b'changed dependency')
    if fault=='omit_inventory': c.pop('dependency_inventory_hash')
    if fault=='source': (data['root']/'src/Drift.java').write_text('class Drift {}')
    with pytest.raises(ContractError): runtime.create_session(store,reg,c,directory=Path(data['owned']['directory']))
    assert not (Path(data['owned']['directory'])/'session.json').exists()
    assert not (store.root/'launches').exists()


@pytest.mark.parametrize('field',['runtime_scope','dependency_inventory_hash'])
def test_native_input_rejects_dependency_identity_drift_before_press(receiver,field):
    from kneekura_tech_hub.minecraft import input_route
    from test_minecraft_input_route import request
    store,reg,c,raw,calls=receiver; bound=input_route.bind(store,reg)
    assert bound['identity'][field]==c[field]
    raw['identity'][field]='wrong'
    result=input_route.dispatch_registered(store,reg,bound['binding_hash'],request(bound))
    assert result['input_status']=='BLOCKED'
    assert not any(row[0]=='native' and row[1] is not None for row in calls)


from test_minecraft_dedicated_runtime import pair
from test_minecraft_index import class_profile
from test_minecraft_dedicated_input import receiver


def test_actual_forge_mapping_zip_is_retained_as_mandatory_runtime_entry(resolved):
    store,root,raw,reg,paths=resolved; mapping=paths[0].with_suffix('.zip'); mapping.write_bytes(paths[0].read_bytes())
    raw['artifacts'][1].update(path=str(mapping),coordinate='net.minecraft:mappings_official:1.20.1')
    register_export(store,root,raw,reg); result=capture(resolved)
    assert len(result['dependency_inventory']['entries'])==3
    assert result['dependency_files'][1]['path']==str(mapping)
    assert store.read(result['dependency_inventory']['entries'][1]['sha256'])==mapping.read_bytes()


def test_total_read_budget_counts_distinct_paths_even_with_identical_bytes(resolved,monkeypatch):
    store,root,raw,reg,paths=resolved
    paths[0].write_bytes(paths[1].read_bytes()); raw['artifacts'][1]['sha256']=digest(paths[0].read_bytes())
    register_export(store,root,raw,reg); monkeypatch.setattr(api(),'MAX_TOTAL_BYTES',paths[0].stat().st_size)
    with pytest.raises(ContractError,match='budget'): capture(resolved)


@pytest.mark.parametrize('field',['coordinate','namespace','stage'])
def test_control_characters_in_export_labels_are_rejected(resolved,field):
    store,root,raw,reg,paths=resolved; raw['artifacts'][0][field]='unsafe\nlabel'
    register_export(store,root,raw,reg)
    with pytest.raises(ContractError): capture(resolved)


def test_broad_unknown_profile_cannot_gain_runtime_scope_by_metadata_relabeling(resolved):
    store,root,raw,reg,paths=resolved; bundle=capture(resolved)
    broad=storage.capture_profile(workspace.import_resolved(raw,root),root,store)
    assert broad['identity_status']=='UNKNOWN'
    broad['identity_status']='PINNED_TARGET_CODE'
    broad['coverage'].update(complete=False,target_complete=True,scope='TARGET_CODE',dependency_bytes_complete=True)
    broad['manifest'].update(runtime_scope=SCOPE,dependency_inventory_hash=bundle['dependency_inventory_hash'])
    broad.pop('profile_id'); broad.pop('profile_hash'); broad['profile_id']=broad['profile_hash']=key_for(broad)
    with pytest.raises(ContractError): runtime._pinned_dedicated_profile(broad)


@pytest.mark.parametrize('fault',['missing_root','changed_output','failed_compile'])
def test_target_profile_cannot_omit_required_target_or_compile_provenance(resolved,fault):
    store,root,raw,reg,paths=resolved
    if fault=='missing_root': raw['source_roots'].append('missing-source'); register_export(store,root,raw,reg)
    if fault=='changed_output': (root/'build/classes/java/main/Target.class').write_bytes(b'other bytecode')
    if fault=='failed_compile':
        receipt=store.json(reg['build_receipt_hash']); receipt['result']['outcome']='FAIL'
        reg['build_receipt_hash']=store.put_json(receipt)
    with pytest.raises(ContractError): api().prepare_target_profile(store,reg)


@pytest.mark.parametrize('fault',['changed_jar','missing_cas','stale_source','omitted_entry'])
def test_runner_rejects_dependency_drift_without_process_budget_or_marker_consumption(pair,fault):
    from kneekura_tech_hub.minecraft import execution
    data=pair['server']; store=pair['store']; reg=deepcopy(data['registry']); c=deepcopy(data['prepared']['contract'])
    inventory=store.json(c['dependency_inventory_hash']); raw=store.json(inventory['resolved_inputs_hash'])
    if fault=='changed_jar': Path(raw['artifacts'][0]['path']).write_bytes(b'changed')
    if fault=='missing_cas':
        p=store.blob_path(inventory['entries'][0]['sha256']); p.rename(p.with_name(p.name+'.moved'))
    if fault=='stale_source': (data['root']/'src/Drift.java').write_text('class Drift {}')
    if fault=='omitted_entry':
        inventory['entries'].pop(); reg['dependency_inventory_hash']=c['dependency_inventory_hash']=store.put_json(inventory)
    calls=[]
    expected_error = storage.ArtifactUnavailable if fault=='missing_cas' else ContractError
    with pytest.raises(expected_error):
        execution.execute(store,reg,kind='server',request_id='blocked-dependency',contract=c,
                          runner=lambda *args,**kwargs:calls.append(args),**data['arguments'])
    assert calls==[]
    directory=Path(data['owned']['directory'])
    assert json.loads((directory/'.kneekura-run.json').read_bytes())['fresh'] is True
    assert not (directory/'session.json').exists()
    assert not list((store.root/'launches').glob('**/*.json'))


@pytest.mark.parametrize('field',['runtime_scope','dependency_inventory_hash'])
def test_scope_identity_cannot_be_smuggled_into_legacy_v1(field):
    from test_minecraft_verification import contract
    c=contract(); actual=deepcopy(c); actual[field]='d'*64
    assert verification._identity_errors(c,{'identity':actual})
    c[field]='d'*64
    with pytest.raises(ContractError): verification.identity_fields(c)


def test_scoped_observation_output_separates_bytes_from_loaded_class_attestation():
    from test_minecraft_dedicated_identity import dedicated_contract,dedicated_observation
    c=dedicated_contract(); out=verification.evaluate_observation(c,dedicated_observation(c))
    assert out['outcome']=='NOT_RUN'
    assert out['runtime_scope']==SCOPE and out['dependency_inventory_hash']==c['dependency_inventory_hash']
    assert out['target_coverage']=='TARGET_CODE'
    assert out['dependency_coverage']=='RESOLVED_BYTES_IDENTITY_ONLY'
    assert out['loaded_class_attestation']=='NOT_ESTABLISHED_BY_IDENTITY'


@pytest.mark.parametrize('fault',['all_target_roots','source_root','binary_root','resource_root','document','root_name','root_bytes','manifest_roots','extra_document'])
def test_rehashed_profile_cannot_replace_export_derived_target_closure(resolved,fault):
    store,root,raw,reg,paths=resolved; profile=api().prepare_target_profile(store,reg)
    reg['dependency_inventory_hash']=profile['manifest']['dependency_inventory_hash']
    if fault in ('all_target_roots','source_root','binary_root','resource_root'):
        roles={'source','binary'} if fault=='all_target_roots' else {'source' if fault=='source_root' else 'resources' if fault=='resource_root' else 'binary'}
        gone={r['id'] for r in profile['roots'] if r['role'] in roles}
        profile['roots']=[r for r in profile['roots'] if r['id'] not in gone]
        profile['documents']=[d for d in profile['documents'] if d['root_id'] not in gone]
        profile['coverage']['requested_roots']=profile['coverage']['analyzed_roots']=[r['id'] for r in profile['roots']]
    if fault=='document': profile['documents'].pop()
    if fault=='root_name':
        r=profile['roots'][0]; old=r['id']; r['id']='forged-name'
        for field in ('requested_roots','analyzed_roots'):
            profile['coverage'][field]=['forged-name' if v==old else v for v in profile['coverage'][field]]
        for d in profile['documents']:
            if d['root_id']==old: d['root_id']='forged-name'
    if fault=='root_bytes': next(r for r in profile['roots'] if r['role']=='binary')['artifact_hash']='e'*64
    if fault=='manifest_roots': profile['manifest']['roots']=[]
    if fault=='extra_document': profile['documents'].append(deepcopy(profile['documents'][0]))
    profile.pop('profile_id'); profile.pop('profile_hash'); profile['profile_id']=profile['profile_hash']=key_for(profile)
    with pytest.raises(ContractError): runtime._profile_dependencies(store,reg,profile)


def test_contract_prepare_rejects_profile_with_all_target_roots_stripped(pair):
    from kneekura_tech_hub.minecraft import contracts
    store=pair['store']; data=pair['server']; snapshot=store.json(data['index']); profile=snapshot['profile']
    profile['roots']=[r for r in profile['roots'] if r['role']=='configuration']
    profile['documents']=[d for d in profile['documents'] if d['role']=='configuration']
    profile['coverage']['requested_roots']=profile['coverage']['analyzed_roots']=[r['id'] for r in profile['roots']]
    profile.pop('profile_id'); profile.pop('profile_hash'); profile['profile_id']=profile['profile_hash']=key_for(profile)
    forged=store.put_json(snapshot)
    with pytest.raises(ContractError):
        contracts.prepare_contract(store,data['registry'],index_id=forged,scenario=data['scenario'],**data['arguments'])


def test_complete_target_revalidation_does_not_write_or_prepare_evidence(resolved,monkeypatch):
    store,root,raw,reg,paths=resolved; profile=api().prepare_target_profile(store,reg)
    reg['dependency_inventory_hash']=profile['manifest']['dependency_inventory_hash']
    before={str(p):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    def forbidden(*args,**kwargs): raise AssertionError('Validation must not prepare or write evidence')
    monkeypatch.setattr(store,'put',forbidden); monkeypatch.setattr(store,'pin',forbidden)
    assert runtime._profile_dependencies(store,reg,profile)['dependency_inventory_hash']==reg['dependency_inventory_hash']
    assert {str(p):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}==before
