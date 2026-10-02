"""Dedicated contracts/runners on test-owned files and injected process receipts."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil

import pytest

from kneekura_tech_hub.minecraft import contracts, execution, index, runtime, storage, verification, dependencies, workspace
from kneekura_tech_hub.minecraft.storage import ContractError, Store, key_for, capture_profile
from kneekura_tech_hub.minecraft.workspace import workspace_fingerprint, file_hash
from test_minecraft_execution import local
from test_minecraft_index import class_profile
from test_minecraft_storage import manifest
from test_minecraft_cli import run_cli
from test_minecraft_dedicated_identity import PLAYER, policy


@pytest.fixture
def client_directory(local):
    store,reg,root=local
    template=root/'templates/client'; template.mkdir(parents=True)
    (template/'options.txt').write_text('fixture-options')
    (template/'empty-folder').mkdir()
    reg['client_templates']=[str(template)]
    out=execution.prepare_client_directory(store,reg,template=str(template),request_id='receiver')
    return store,reg,root,template,out


def test_client_directory_is_private_fresh_and_not_a_world(client_directory):
    store,reg,root,template,out=client_directory; directory=Path(out['directory'])
    assert out['kind']=='client_run_directory' and out['fresh'] is True
    assert not {'world','world_id','world_template_hash','world_seed','world_layout'} & set(out)
    assert (directory/'options.txt').read_bytes()==(template/'options.txt').read_bytes()
    assert (directory/'empty-folder').is_dir()
    if os.name!='nt': assert directory.stat().st_mode & 0o077==0
    marker,path=execution._owned_client_directory(root,str(directory))
    assert path==directory/'.kneekura-run.json' and marker['run_directory_id']==directory.name
    assert store.json(out['marker_hash'])==marker
    with pytest.raises(ContractError): execution.prepare_client_directory(store,reg,template=str(template),request_id='receiver')
    with pytest.raises(ContractError): execution._owned_world(root,str(directory))


@pytest.mark.parametrize('fault',['changed','used','wrong_kind','world_field','symlink_file','symlink_dir','symlink_marker','symlink_run'])
def test_client_directory_rejects_stale_or_interchanged_ownership(client_directory,fault):
    store,reg,root,template,out=client_directory; directory=Path(out['directory']); marker_path=directory/'.kneekura-run.json'
    if fault=='changed': (directory/'options.txt').write_text('changed')
    elif fault=='symlink_file': (directory/'options.txt').unlink(); (directory/'options.txt').symlink_to(template/'options.txt')
    elif fault=='symlink_dir': (directory/'new').symlink_to(template,target_is_directory=True)
    elif fault=='symlink_marker':
        moved=directory/'moved-marker'; marker_path.rename(moved); marker_path.symlink_to(moved)
    elif fault=='symlink_run':
        moved=directory.with_name(directory.name+'moved'); directory.rename(moved); directory.symlink_to(moved,target_is_directory=True)
    else:
        marker=json.loads(marker_path.read_bytes())
        if fault=='used': marker['fresh']=False
        if fault=='wrong_kind': marker['kind']='world'
        if fault=='world_field': marker['world']=str(directory/'gametestserver')
        marker_path.write_text(json.dumps(marker))
    with pytest.raises(ContractError): execution._owned_client_directory(root,str(directory))


def test_world_marker_cannot_be_reinterpreted_as_client_directory(local):
    store,reg,root=local; template=root/'template'; template.mkdir(); reg['world_templates']=[str(template)]
    world=execution.prepare_world(store,reg,template=str(template),request_id='world')
    with pytest.raises(ContractError): execution._owned_client_directory(root,world['directory'])
    path=Path(world['directory'])/'.kneekura-run.json'; marker=json.loads(path.read_bytes())
    marker['kind']='client_run_directory'; path.write_text(json.dumps(marker))
    with pytest.raises(ContractError): execution._owned_world(root,world['world'])


@pytest.mark.parametrize('reserved',['session.json','endpoint.json','.kneekura-run.json','.session-started','.input-attempts'])
def test_client_template_cannot_supply_runtime_authority(local,reserved):
    store,reg,root=local; template=root/'template'; template.mkdir(); (template/reserved).write_text('untrusted')
    reg['client_templates']=[str(template)]
    with pytest.raises(ContractError): execution.prepare_client_directory(store,reg,template=str(template),request_id='bad')
    assert not (root/'.kneekura-runs').exists()


@pytest.fixture
def pair(class_profile,tmp_path,monkeypatch):
    monkeypatch.setattr(workspace,'_revision',lambda root:'a'*40)
    store,original,fixture_root=class_profile
    server_root=tmp_path/'server-workspace'; client_root=tmp_path/'client-workspace'
    for root in (server_root,client_root):
        root.mkdir(); shutil.copytree(fixture_root/'src',root/'src')
        shutil.copyfile(fixture_root/'mod.jar',root/'mod.jar')
    result={'store':store}
    for side,root in [('server',server_root),('client',client_root)]:
        (root/'gradlew').write_text('#!/bin/sh\nexit 99\n'); (root/'gradlew').chmod(0o700)
        (root/'gradle.properties').write_text('fixture.role='+side)
        m=deepcopy(original['manifest']); m.update(physical_side=side,logical_side=side,
                                                 workspace=str(root),dirty_hash=workspace_fingerprint(root))
        artifact=file_hash(root/'mod.jar'); current=workspace_fingerprint(root)
        receipt={'source_generation':current,'source_generation_after':current,
                 'request':{'kind':'compile','workspace':str(root)},'outputs':[{'path':'mod.jar','content_hash':artifact}],
                 'result':{'outcome':'PASS'}}
        reg={'workspace':str(root),'build_artifact':'mod.jar','build_receipt_hash':store.put_json(receipt),
             'runtime_config_files':['gradle.properties'],'runtime_role':'dedicated_'+side,'connection_policy':policy(),
             'allow_gradle':True,'allowed_kinds':[side],'wrapper_sha256':file_hash(root/'gradlew'),
             'remaining_launches':1,'launch_budget_id':'fixture-'+side,'timeout_seconds':2}
        from test_minecraft_workspace import export_data
        from test_minecraft_dependency_inventory import register_export
        raw=export_data(root); raw.update(source_roots=['src'],resource_roots=[],output_roots=['mod.jar'])
        raw['artifacts']=[{'path':str(fixture_root/'mod.jar'),'scope':scope,'namespace':'mojmap',
                          'stage':'resolved_userdev','coordinate':'fixture:dependency:1','sha256':artifact}
                         for scope in ('compile','runtime')]
        register_export(store,root,raw,reg)
        profile=dependencies.prepare_target_profile(store,reg,physical_side=side)
        reg.update(runtime_scope=dependencies.RUNTIME_SCOPE,
                   dependency_inventory_hash=profile['manifest']['dependency_inventory_hash'])
        idx=index.prepare_index(profile,store)['index_snapshot_id']
        template=root/'template'; template.mkdir()
        if side=='server':
            reg['world_templates']=[str(template)]
            owned=execution.prepare_world(store,reg,template=str(template),request_id='dedicated-server')
            arguments={'world':owned['world']}
        else:
            (template/'options.txt').write_text('fixture-client')
            reg['client_templates']=[str(template)]; reg.update(server_contract_hash=result['server']['prepared']['contract_hash'],player_uuid=PLAYER)
            owned=execution.prepare_client_directory(store,reg,template=str(template),request_id='dedicated-client')
            arguments={'run_directory':owned['directory']}
        scenario={'assertion_domain':side+'_observation','expected_tests':[],'expected_required':{}}
        if side=='server': scenario['world_seed']=0
        prepared=contracts.prepare_contract(store,reg,index_id=idx,scenario=scenario,**arguments)
        result[side]={'root':root,'registry':reg,'index':idx,'owned':owned,'scenario':scenario,'prepared':prepared,'arguments':arguments}
    return result


def test_dedicated_contracts_preserve_distinct_profile_config_and_world_authority(pair):
    server=pair['server']['prepared']['contract']; client=pair['client']['prepared']['contract']
    assert server['schema_version']==client['schema_version']==2
    assert server['session_role']=='dedicated_server' and client['session_role']=='dedicated_client'
    assert server['build_artifact_hash']==client['build_artifact_hash']
    assert server['source_revision']==client['source_revision']
    assert server['profile_id']!=client['profile_id'] and server['config_hash']!=client['config_hash']
    assert server['dirty_hash']!=client['dirty_hash']
    assert client['server_contract_hash']==pair['server']['prepared']['contract_hash']
    assert not {'world_id','world_seed','world_template_hash'} & set(client)
    assert client['connection_policy_hash']==key_for(client['connection_policy'])
    for side in ('server','client'):
        assert pair[side]['prepared']['outcome']=='NOT_RUN'
        assert verification._identity_errors(pair[side]['prepared']['contract'],{'identity':pair[side]['prepared']['contract']})==[]


@pytest.mark.parametrize('side',['server','client'])
def test_session_binds_owned_role_without_fabricating_receiver_world(pair,side):
    data=pair[side]; c=data['prepared']['contract']; reg=data['registry']
    s=runtime.create_session(pair['store'],reg,c,directory=Path(data['owned']['directory']))
    assert s['schema_version']==2 and s['connection_policy']==policy()
    assert s['expected_runtime']=={'minecraft':'1.20.1','forge':'47.4.0','java_major':17}
    if side=='client':
        assert s['server_contract']==pair['server']['prepared']['contract'] and s['player_uuid']==PLAYER
        assert s['server_contract_hash']==c['server_contract_hash']
        assert 'world' not in s and 'world_layout' not in s
    else: assert s['world']==data['owned']['world']


@pytest.mark.parametrize('fault',['source','index','build','config','receipt','server_ref','server_artifact','server_policy','server_role','server_version','player','role','directory'])
def test_stale_or_foreign_receiver_authority_rejected_before_session_write(pair,fault):
    data=pair['client']; reg=deepcopy(data['registry']); c=deepcopy(data['prepared']['contract']); store=pair['store']
    if fault=='source': (data['root']/'src/Changed.java').write_text('class Changed {}')
    if fault=='index': c['index_snapshot_id']=pair['server']['index']
    if fault=='build': (data['root']/'mod.jar').write_bytes(b'changed')
    if fault=='config': (data['root']/'extra.txt').write_text('config'); reg['runtime_config_files'].append('extra.txt')
    if fault=='receipt': reg['build_receipt_hash']=pair['server']['registry']['build_receipt_hash']
    if fault=='server_ref': reg['server_contract_hash']='f'*64
    if fault in ('server_artifact','server_policy','server_role','server_version'):
        server=deepcopy(pair['server']['prepared']['contract'])
        if fault=='server_artifact': server['build_artifact_hash']='f'*64
        if fault=='server_policy': server['connection_policy']['port']=25566; server['connection_policy_hash']=key_for(server['connection_policy'])
        if fault=='server_role': server['session_role']='dedicated_client'
        if fault=='server_version':
            snapshot=store.json(server['index_snapshot_id']); snapshot['profile']['manifest']['loader_version']='47.4.6'
            server['index_snapshot_id']=store.put_json(snapshot)
        reg['server_contract_hash']=store.put_json(server); c['server_contract_hash']=reg['server_contract_hash']
    if fault=='player': reg['player_uuid']='33333333-3333-4333-8333-333333333333'
    if fault=='role': reg.pop('runtime_role')
    if fault=='directory': c['run_directory_id']='foreign'
    with pytest.raises((ContractError,OSError)):
        runtime.create_session(store,reg,c,directory=Path(data['owned']['directory']))
    assert not (Path(data['owned']['directory'])/'session.json').exists()
    assert not (store.root/'launches').exists()


@pytest.mark.parametrize('side',['server','client'])
def test_registered_dedicated_runner_consumes_exact_directory_once_and_never_claims_pass(pair,side):
    data=pair[side]; called=[]
    def runner(argv,cwd,**kwargs):
        called.append((argv,cwd,kwargs))
        marker=json.loads((Path(data['owned']['directory'])/'.kneekura-run.json').read_bytes())
        assert marker['fresh'] is False
        return {'stdout':b'offline fixture only','completed':True,'exit_code':0}
    result=execution.execute(pair['store'],data['registry'],kind=side,request_id='fixture-launch',
                             contract=data['prepared']['contract'],runner=runner,**data['arguments'])
    assert result['outcome']=='NOT_RUN' and result['tests_executed']==0
    assert result['assertion_domain']==side+'_observation'
    assert len(called)==1 and called[0][0][-1]==('runServer' if side=='server' else 'runClient')
    assert called[0][2]['timeout']==2
    replay=execution.execute(pair['store'],data['registry'],kind=side,request_id='fixture-launch',
                             contract=data['prepared']['contract'],runner=runner,**data['arguments'])
    assert replay['receipt_hash']==result['receipt_hash'] and len(called)==1


def test_receiver_run_rejects_world_argument_without_launch_or_budget_consumption(pair):
    data=pair['client']; calls=[]
    with pytest.raises(ContractError):
        execution.execute(pair['store'],data['registry'],kind='client',request_id='bad',world=pair['server']['owned']['world'],
                          run_directory=data['owned']['directory'],contract=data['prepared']['contract'],runner=lambda *a,**k:calls.append(a))
    assert calls==[] and not (pair['store'].root/'launches').exists()


def test_client_directory_cli_is_explicit_and_contract_world_alternative_parses(local,tmp_path):
    from kneekura_tech_hub.minecraft.__main__ import parser
    store,reg,root=local; template=root/'template'; template.mkdir(); reg['client_templates']=[str(template)]
    path=tmp_path/'registry.json'; path.write_text(json.dumps(reg))
    p,out=run_cli(store.root,'client-directory','prepare','--registry',str(path),'--template',str(template),'--request-id','cli')
    assert p.returncode==0,p.stderr
    assert out['kind']=='client_run_directory' and 'world' not in out
    args=parser().parse_args(['contract','prepare','--registry','r','--index','i','--run-directory','d','--scenario','s'])
    assert args.run_directory=='d' and args.world is None
    args=parser().parse_args(['validate','run','--registry','r','--kind','server','--request-id','id','--world','w'])
    assert args.kind=='server'


def test_dedicated_plan_is_read_only_and_binds_owned_receiver_directory(pair):
    data=pair['client']; before=set(Path(data['owned']['directory']).iterdir())
    plan=verification.validation_plan('client',data['registry'],run_directory=data['owned']['directory'])
    assert plan['outcome']=='NOT_RUN' and plan['argv'][-1]=='runClient'
    assert plan['run_directory']==data['owned']['directory'] and plan.get('world') is None
    assert set(Path(data['owned']['directory']).iterdir())==before
    assert json.loads((Path(data['owned']['directory'])/'.kneekura-run.json').read_bytes())['fresh'] is True


def test_init_gradle_instruments_server_without_auto_connect_or_network_changes():
    text=Path('src/kneekura_tech_hub/minecraft/resources/kneekura-run.init.gradle').read_text()
    assert "'runServer'" in text and "'server'" in text
    assert 'workingDir runDir' in text
    assert '--server' not in text and 'online-mode' not in text and 'eula' not in text.lower()


@pytest.mark.parametrize('side',['server','client'])
@pytest.mark.parametrize('process,expected',[({'completed':False,'exit_code':None},'BLOCKED'),({'completed':True,'exit_code':7},'FAIL')])
def test_dedicated_observation_launch_keeps_process_failure_conservative(pair,side,process,expected):
    data=pair[side]
    result=execution.execute(pair['store'],data['registry'],kind=side,request_id='failed-launch',
                             contract=data['prepared']['contract'],runner=lambda *a,**k:dict(process,stdout=b'fixture'),**data['arguments'])
    assert result['outcome']==expected


def test_unreadable_client_template_is_not_silently_an_empty_success(local,monkeypatch):
    store,reg,root=local; template=root/'template'; template.mkdir(); reg['client_templates']=[str(template)]
    original=execution.os.scandir
    def unreadable(path):
        if Path(path)==template: raise PermissionError('fixture unreadable')
        return original(path)
    monkeypatch.setattr(execution.os,'scandir',unreadable)
    with pytest.raises((ContractError,OSError)):
        execution.prepare_client_directory(store,reg,template=str(template),request_id='blocked')
    assert not (root/'.kneekura-runs').exists()


def test_observe_pair_cli_is_explicit_read_only_and_delegates_exact_scope(tmp_path,monkeypatch):
    from kneekura_tech_hub.minecraft import __main__,runtime_pair
    calls=[]
    monkeypatch.setattr(runtime_pair,'observe_pair',lambda store,**kwargs: calls.append(kwargs) or {'outcome':'NOT_RUN'})
    args=__main__.parser().parse_args(['--store',str(tmp_path/'cas'),'observe-pair','--server-session','server.json',
                                      '--client-session','client.json','--player-uuid',PLAYER,'--screenshot'])
    assert __main__.dispatch(args)['outcome']=='NOT_RUN'
    assert calls==[{'server_session':'server.json','client_session':'client.json','player_uuid':PLAYER,
                    'dimension':'minecraft:overworld','timeout':10,'screenshot':True}]


@pytest.mark.parametrize('operation',['contract','session'])
def test_dedicated_target_rejects_unpinned_forge_profile(pair,operation):
    data=pair['server']; store=pair['store']; current=data['prepared']['contract']
    m=deepcopy(store.json(data['index'])['profile']['manifest']); m['loader_version']='47.4.x'
    profile=capture_profile(m,data['root'],store); idx=index.prepare_index(profile,store)['index_snapshot_id']
    if operation=='contract':
        with pytest.raises(ContractError,match='pinned|profile|exact'):
            contracts.prepare_contract(store,data['registry'],index_id=idx,scenario=data['scenario'],**data['arguments'])
    else:
        c=dict(current,index_snapshot_id=idx,profile_id=profile['profile_id'])
        with pytest.raises(ContractError,match='pinned|profile|exact'):
            runtime.create_session(store,data['registry'],c,directory=Path(data['owned']['directory']))


def test_dedicated_registration_does_not_block_independent_compile_plan(pair):
    data=pair['server']; registry=deepcopy(data['registry']); registry['allowed_kinds'].append('compile')
    out=verification.validation_plan('compile',registry)
    assert out['outcome']=='NOT_RUN' and out['argv'][-1]=='build'
