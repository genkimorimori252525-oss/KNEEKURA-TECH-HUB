"""Isolated U04 scope fixtures. No Minecraft, remapper, network or native input."""
from copy import deepcopy
import io
import json
from pathlib import Path
import zipfile
import pytest

from kneekura_tech_hub.minecraft import dependencies, contracts, execution, index, runtime, verification, workspace
from kneekura_tech_hub.minecraft.storage import Store, ContractError, ArtifactUnavailable, canonical, digest, key_for
from test_minecraft_dependency_inventory import resolved, project, register_export
from test_minecraft_verification import contract as old_contract, observation

RESOURCES=['twilightforest/entity/boss/Hydra.class','twilightforest/entity/boss/HydraPart.class',
 'twilightforest/entity/boss/HydraHeadContainer.class','twilightforest/client/TFClientSetup.class',
 'twilightforest/client/JappaPackReloadListener.class','twilightforest/client/renderer/entity/HydraRenderer.class',
 'twilightforest/client/model/entity/HydraModel.class']


def archive(rows):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,data in rows.items(): z.writestr(name,data)
    return out.getvalue()


def integrated_contract():
    c=old_contract(); c.update(schema_version=3,session_role='integrated_client',physical_side='client',
        logical_side='server',runtime_scope=dependencies.RUNTIME_SCOPE,dependency_inventory_hash='d'*64,
        target_selection_hash='e'*64,assertion_domain='rendering',expected_tests=[])
    c['assertion_hash']=key_for({'assertion_domain':'rendering','expected_tests':[],'expected_required':{}})
    return c


@pytest.fixture
def selected(resolved):
    store,root,raw,reg,paths=resolved
    entries={n:('fixture mapped '+n).encode() for n in RESOURCES}
    entries.update({'assets/twilightforest/texture.png':b'fixture png','META-INF/mods.toml':b'[[mods]]\nmodId="twilightforest"\n'})
    original=archive(dict(entries,**{RESOURCES[0]:b'fixture original Hydra'})); derived=archive(entries)
    target=paths[0].parent/'twilightforest-derived.jar'; target.write_bytes(derived)
    raw['artifacts'].append({'path':str(target),'scope':'runtime','coordinate':target.name,'sha256':digest(derived),
                            'namespace':'unknown','stage':'resolved_userdev'})
    register_export(store,root,raw,reg)
    provider={'provider':'tiny-remapper','version':'0.11.2','jar_hash':store.put(b'fixture tool'),
              'jdk':{'provider':'jdk-java-cli'},'memory_mib':256,'threads':1}
    receipt={'schema_version':1,'provider':provider,'operation':'remap','root_id':'fixture-original',
             'input_artifact_hash':store.put(original),'output_artifact_hash':store.put(derived),
             'input_namespace':'srg','output_namespace':'mojmap',
             'mapping_hash':store.put(b'tiny\t2\t0\tsrg\tmojmap\nc\told\tnew\n'),
             'classpath_artifact_hashes':[store.put(paths[0].read_bytes())],
             'raw_output_hashes':[store.put(derived)],'log_hash':store.put(b'fixture success'),
             'entries':[{'path':name,'content_hash':store.put(data)} for name,data in entries.items()]}
    receipt['cache_key']=key_for({'input':receipt['input_artifact_hash'],'root_id':receipt['root_id'],
         'operation':'remap','provider':provider,'mapping_hash':receipt['mapping_hash'],
         'from_namespace':'srg','to_namespace':'mojmap','classpath':receipt['classpath_artifact_hashes']})
    reg['target_selection']={'schema_version':1,'kind':'u04_hydra_derived_dependency','coordinate':target.name,
        'sha256':digest(derived),'provider_receipt_hash':store.put_json(receipt),'class_resources':RESOURCES}
    return store,root,raw,reg,target,receipt


def test_schema3_integrated_identity_is_world_bound_without_dedicated_policy():
    c=integrated_contract()
    assert set(verification.identity_fields(c))==set(verification.IDENTITY_FIELDS)|{'session_role','runtime_scope','dependency_inventory_hash','target_selection_hash'}
    assert verification._identity_errors(c,{'identity':c})==[]
    raw=observation(c); raw.update(client_frame_start=50,client_frame_end=52)
    result=verification.evaluate_observation(c,raw)
    assert result['status']=='OK' and result['outcome']=='NOT_RUN' and result['atomic'] is False


@pytest.mark.parametrize('field,value',[('schema_version',1),('schema_version',2),('session_role','dedicated_client'),
    ('physical_side','server'),('logical_side','client'),('target_selection_hash',None),('runtime_scope','ALL'),
    ('connection_policy_hash','a'*64),('connection_policy',{}),('server_contract_hash','a'*64),('player_uuid','x'),
    ('run_directory_id','x')])
def test_integrated_identity_rejects_downgrade_and_foreign_role_authority(field,value):
    c=integrated_contract(); c[field]=value
    assert verification._identity_errors(c,{'identity':c})


def test_selected_dependency_retains_exact_raw_root_and_complete_scope(selected):
    store,root,raw,reg,target,receipt=selected
    profile=dependencies.prepare_target_profile(store,reg,physical_side='client')
    chosen=[r for r in profile['roots'] if r['role']=='dependency']
    assert len(chosen)==1 and chosen[0]['id']=='dependency:3'
    assert chosen[0]['namespace']=='unknown' and chosen[0]['stage']=='resolved_userdev'
    assert chosen[0]['artifact_hash']==reg['target_selection']['sha256']
    assert profile['manifest']['target_selection']==reg['target_selection']
    assert profile['coverage']['complete'] is False and profile['coverage']['target_complete'] is True
    assert profile['coverage']['selected_target_root_ids']==['dependency:3']
    reg['dependency_inventory_hash']=profile['manifest']['dependency_inventory_hash']
    assert dependencies.validate_target_profile(store,reg,profile)


@pytest.mark.parametrize('fault',['coordinate','hash','missing_runtime','duplicate_probe','missing_probe','traversal','foreign_probe','too_many','unknown_field',
    'receipt_output','receipt_input','receipt_tool','receipt_mapping','receipt_classpath','receipt_entries','receipt_cache','receipt_namespace','missing_tool'])
def test_selection_or_provider_chain_cannot_be_asserted_without_matching_bytes(selected,fault):
    store,root,raw,reg,target,receipt=selected; selection=reg['target_selection']
    if fault=='coordinate': selection['coordinate']='other.jar'
    if fault=='hash': selection['sha256']='f'*64
    if fault=='missing_runtime': raw['artifacts'][-1]['scope']='compile'; register_export(store,root,raw,reg)
    if fault=='duplicate_probe': selection['class_resources']=[RESOURCES[0],RESOURCES[0]]
    if fault=='missing_probe': selection['class_resources']=['twilightforest/Missing.class']
    if fault=='traversal': selection['class_resources']=['../Hydra.class']
    if fault=='foreign_probe': selection['class_resources']=['other/Example.class']
    if fault=='too_many': selection['class_resources']=['twilightforest/X'+str(i)+'.class' for i in range(33)]
    if fault=='unknown_field': selection['allow_unknown']=True
    if fault.startswith('receipt_'):
        field={'receipt_output':'output_artifact_hash','receipt_input':'input_artifact_hash','receipt_tool':'provider',
               'receipt_mapping':'mapping_hash','receipt_classpath':'classpath_artifact_hashes','receipt_entries':'entries',
               'receipt_cache':'cache_key','receipt_namespace':'output_namespace'}[fault]
        receipt[field]=dict(receipt['provider'],jar_hash='e'*64) if field=='provider' else [] if field in ('entries','classpath_artifact_hashes') else 'e'*64
        selection['provider_receipt_hash']=store.put_json(receipt)
    if fault=='missing_tool':
        p=store.blob_path(receipt['provider']['jar_hash']); p.rename(p.with_name(p.name+'.moved'))
    with pytest.raises((ContractError,ArtifactUnavailable)):
        dependencies.prepare_target_profile(store,reg,physical_side='client')


@pytest.fixture
def integrated(selected):
    store,root,raw,reg,target,receipt=selected
    (root/'template').mkdir(); reg.update(runtime_role='integrated_client',world_templates=[str(root/'template')],
        runtime_config_files=[],remaining_launches=1,launch_budget_id='u04-fixture',allow_gradle=True,allowed_kinds=['client'])
    # The fixture wrapper is inert; execute receives an injected runner only.
    (root/'gradlew').write_text('#!/bin/sh\nexit 99\n'); (root/'gradlew').chmod(0o700)
    reg['wrapper_sha256']=digest((root/'gradlew').read_bytes())
    raw['source_fingerprint']=workspace.workspace_fingerprint(root); raw['configuration_fingerprint']=workspace.configuration_fingerprint(root)
    register_export(store,root,raw,reg)
    compiled=store.json(reg['build_receipt_hash']); compiled.update(source_generation=raw['source_fingerprint'],source_generation_after=raw['source_fingerprint'])
    reg['build_receipt_hash']=store.put_json(compiled)
    profile=dependencies.prepare_target_profile(store,reg,physical_side='client')
    reg['dependency_inventory_hash']=profile['manifest']['dependency_inventory_hash']
    idx=index.prepare_index(profile,store)['index_snapshot_id']
    owned=execution.prepare_world(store,reg,template=str(root/'template'),request_id='u04',layout='client')
    scenario={'assertion_domain':'rendering','world_seed':0,'expected_tests':[]}
    prepared=contracts.prepare_contract(store,reg,index_id=idx,world=owned['world'],scenario=scenario)
    return store,root,reg,owned,prepared,profile,scenario


def test_integrated_contract_session_distinguishes_marker_and_selected_artifact(integrated):
    store,root,reg,owned,prepared,profile,scenario=integrated; c=prepared['contract']
    assert c['schema_version']==3 and c['session_role']=='integrated_client'
    assert c['target_selection_hash']==key_for(reg['target_selection'])
    assert c['build_artifact_hash']!=reg['target_selection']['sha256']
    session=runtime.create_session(store,dict(reg,world_layout='client'),c,directory=Path(owned['directory']))
    assert session['target_selection']==reg['target_selection'] and session['world']==owned['world']
    assert [p['resource'] for p in session['target_dependency_probes']]==RESOURCES
    assert [p['resource'] for p in session['class_probes']]==['Target.class']
    assert 'connection_policy' not in session and 'server_contract' not in session


def test_integrated_launch_reuses_owned_client_save_and_stays_not_run(integrated):
    store,root,reg,owned,prepared,profile,scenario=integrated; calls=[]
    out=execution.execute(store,reg,kind='client',request_id='offline-run',world=owned['world'],contract=prepared['contract'],
        runner=lambda argv,*a,**kw:calls.append(argv) or {'completed':True,'exit_code':0,'stdout':b'fixture only'})
    assert out['outcome']=='NOT_RUN' and len(calls)==1 and calls[0][-1]=='runClient'
    assert json.loads((Path(owned['directory'])/'.kneekura-run.json').read_bytes())['fresh'] is False


def test_selected_target_cannot_be_removed_from_rehashed_profile(selected):
    store,root,raw,reg,target,receipt=selected; profile=dependencies.prepare_target_profile(store,reg,physical_side='client')
    reg['dependency_inventory_hash']=profile['manifest']['dependency_inventory_hash']
    profile['roots']=[r for r in profile['roots'] if r['role']!='dependency']
    profile['documents']=[d for d in profile['documents'] if d['role']!='dependency']
    profile['coverage']['requested_roots']=profile['coverage']['analyzed_roots']=[r['id'] for r in profile['roots']]
    profile.pop('profile_id');profile.pop('profile_hash');profile['profile_id']=profile['profile_hash']=key_for(profile)
    with pytest.raises(ContractError): dependencies.validate_target_profile(store,reg,profile)


@pytest.mark.parametrize('fault',['omit_required','unrelated_coordinate'])
def test_fixed_u04_selection_rejects_incomplete_or_unrelated_target(selected,fault):
    from kneekura_tech_hub.minecraft.target_selection import validate_shape
    store,root,raw,reg,target,receipt=selected; selection=deepcopy(reg['target_selection'])
    if fault=='omit_required': selection['class_resources']=selection['class_resources'][:-1]
    else: selection['coordinate']='unrelated.jar'
    with pytest.raises(ContractError): validate_shape(selection)


@pytest.mark.parametrize('which',['input','tool','mapping','classpath','raw_output','entry'])
def test_retained_derivation_chain_bytes_are_mandatory_on_revalidation(selected,which):
    store,root,raw,reg,target,receipt=selected
    profile=dependencies.prepare_target_profile(store,reg,physical_side='client')
    reg['dependency_inventory_hash']=profile['manifest']['dependency_inventory_hash']
    h={'input':receipt['input_artifact_hash'],'tool':receipt['provider']['jar_hash'],'mapping':receipt['mapping_hash'],
       'classpath':receipt['classpath_artifact_hashes'][0],'raw_output':receipt['raw_output_hashes'][0],
       'entry':receipt['entries'][0]['content_hash']}[which]
    p=store.blob_path(h); p.rename(p.with_name(p.name+'.moved'))
    with pytest.raises((ContractError,OSError)):
        runtime._profile_dependencies(store,reg,profile)
    assert not p.exists(), 'Read-only validation must not heal missing evidence'


@pytest.mark.parametrize('field',['target_selection_hash','dependency_inventory_hash','runtime_scope','world_id','session_role'])
def test_integrated_native_binding_rejects_changed_target_before_input(receiver,field):
    from kneekura_tech_hub.minecraft import input_route
    from test_minecraft_input_route import request
    store,reg,c,raw,calls=receiver
    c.clear(); c.update(integrated_contract()); raw['identity']={k:c[k] for k in verification.identity_fields(c)}
    raw.update(server_tick_start=20,server_tick_end=21); raw.pop('connection',None); raw.pop('server_tick_scope',None)
    for row in raw['entities']: row.pop('connection',None)
    session_path=Path(reg['session_file']); session=json.loads(session_path.read_bytes()); session['contract']=c
    session_path.write_bytes(canonical(session))
    binding=input_route.bind(store,reg)
    assert binding['identity'][field]==c[field]
    raw['identity'][field]='changed'
    result=input_route.dispatch_registered(store,reg,binding['binding_hash'],request(binding))
    assert result['input_status']=='BLOCKED'
    assert not any(row[0]=='native' and row[1] is not None for row in calls)


@pytest.mark.parametrize('fault',['selection','marker_layout','config','source','profile_selection'])
def test_integrated_session_rejects_stale_selection_or_world_before_write(integrated,fault):
    store,root,reg,owned,prepared,profile,scenario=integrated; reg=deepcopy(reg); c=deepcopy(prepared['contract'])
    if fault=='selection': reg['target_selection']['class_resources']=list(reversed(reg['target_selection']['class_resources']))
    if fault=='marker_layout':
        p=Path(owned['directory'])/'.kneekura-run.json'; marker=json.loads(p.read_bytes()); marker['world_layout']='server'; p.write_bytes(canonical(marker))
    if fault=='config': (root/'x.txt').write_text('different config'); reg['runtime_config_files']=['x.txt']
    if fault=='source': (root/'src/main/java/example/Mob.java').write_text('changed source')
    if fault=='profile_selection':
        snapshot=store.json(c['index_snapshot_id']); p=snapshot['profile']; p['manifest']['target_selection']['class_resources'].reverse()
        p.pop('profile_id');p.pop('profile_hash');p['profile_id']=p['profile_hash']=key_for(p)
        c['profile_id']=p['profile_id'];c['index_snapshot_id']=store.put_json(snapshot)
    with pytest.raises(ContractError): runtime.create_session(store,reg,c,directory=Path(owned['directory']))
    assert not (Path(owned['directory'])/'session.json').exists()


from test_minecraft_dedicated_input import receiver


def test_selected_u04_target_cannot_be_registered_under_dedicated_v2(pair):
    reg=deepcopy(pair['server']['registry']); reg['target_selection']={'unexpected':'selection'}
    with pytest.raises(ContractError): runtime.dedicated_registry(reg)


def test_scope_registration_cannot_silently_fall_back_to_v1(selected):
    store,root,raw,reg,target,receipt=selected
    with pytest.raises(ContractError): runtime.dedicated_registry(reg)


def test_scoped_target_profile_cannot_prepare_legacy_v1_contract_after_registry_downgrade(integrated):
    store,root,reg,owned,prepared,profile,scenario=integrated; reg=deepcopy(reg)
    for key in ('runtime_role','runtime_scope','dependency_inventory_hash','target_selection'): reg.pop(key)
    with pytest.raises(ContractError):
        contracts.prepare_contract(store,reg,index_id=prepared['contract']['index_snapshot_id'],world=owned['world'],scenario=scenario)


from test_minecraft_dedicated_runtime import pair
from test_minecraft_index import class_profile


def test_scoped_target_profile_cannot_create_legacy_v1_session_after_downgrade(integrated):
    store,root,reg,owned,prepared,profile,scenario=integrated; reg=deepcopy(reg); c=deepcopy(prepared['contract'])
    for key in ('runtime_role','runtime_scope','dependency_inventory_hash','target_selection'): reg.pop(key)
    for key in ('session_role','runtime_scope','dependency_inventory_hash','target_selection_hash'): c.pop(key)
    c['schema_version']=1
    with pytest.raises(ContractError): runtime.create_session(store,reg,c,directory=Path(owned['directory']))
    assert not (Path(owned['directory'])/'session.json').exists()
