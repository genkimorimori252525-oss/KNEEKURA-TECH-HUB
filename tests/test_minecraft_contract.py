import copy
import importlib
from pathlib import Path
import pytest
from test_minecraft_runtime import session
from test_minecraft_index import class_profile
from kneekura_tech_hub.minecraft import index
from kneekura_tech_hub.minecraft.storage import ContractError, capture_profile
from kneekura_tech_hub.minecraft.workspace import workspace_fingerprint
from kneekura_tech_hub.minecraft.execution import prepare_world


def api():
    module=importlib.util.find_spec('kneekura_tech_hub.minecraft.contracts')
    assert module is not None, 'Run contract assembly is not connected'
    return importlib.import_module(module.name)


def arranged(session):
    store,c,reg,directory=session; root=Path(reg['workspace'])
    m=copy.deepcopy(index._load(store,c['index_snapshot_id'])['profile']['manifest'])
    m.update(dirty_hash=workspace_fingerprint(root),workspace=str(root))
    p=capture_profile(m,root,store); idx=index.prepare_index(p,store)['index_snapshot_id']
    template=root/'templates/empty'; template.mkdir(parents=True)
    reg['world_templates']=[str(template)]
    world=prepare_world(store,reg,template=str(template),request_id='world')
    scenario={'world_seed':0,'assertion_domain':'server_behavior','expected_tests':['demo.attack'],
              'expected_required':{'demo.attack':True},'purpose':'Check attack'}
    return store,reg,idx,world,scenario


def test_contract_assembled_from_actual_receipt_and_owned_world(session):
    store,reg,idx,world,scenario=arranged(session)
    out=api().prepare_contract(store,reg,index_id=idx,world=world['world'],scenario=scenario)
    c=store.json(out['contract_hash'])
    assert c['index_snapshot_id']==idx and c['world_id']==world['world_id']
    assert c['build_artifact_hash']==store.json(reg['build_receipt_hash'])['outputs'][0]['content_hash']
    assert c['adapter_id']=='kneekura-forge-observer'
    assert c['expected_tests']==['demo.attack'] and out['outcome']=='NOT_RUN'
    again=api().prepare_contract(store,reg,index_id=idx,world=world['world'],scenario=scenario)
    assert store.json(again['contract_hash'])['session_epoch']!=c['session_epoch']


def test_contract_rejects_stale_index_and_unknown_world_seed(session):
    store,reg,idx,world,scenario=arranged(session)
    bad=dict(scenario,world_seed='0')
    with pytest.raises(ContractError): api().prepare_contract(store,reg,index_id=idx,world=world['world'],scenario=bad)
    root=Path(reg['workspace']); (root/'src/Changed.java').write_text('class Changed {}')
    with pytest.raises(ContractError): api().prepare_contract(store,reg,index_id=idx,world=world['world'],scenario=scenario)


def test_contract_requires_tests_for_behavior_and_no_fabricated_build(session):
    store,reg,idx,world,scenario=arranged(session)
    with pytest.raises(ContractError): api().prepare_contract(store,reg,index_id=idx,world=world['world'],scenario=dict(scenario,expected_tests=[]))
    receipt=store.json(reg['build_receipt_hash']); receipt['result']['outcome']='FAIL'; reg['build_receipt_hash']=store.put_json(receipt)
    with pytest.raises(ContractError): api().prepare_contract(store,reg,index_id=idx,world=world['world'],scenario=scenario)

def test_contract_cli_writes_complete_nonsecret_run_identity(session,tmp_path):
    import json
    from test_minecraft_cli import run_cli
    store,reg,idx,world,scenario=arranged(session)
    registry=tmp_path/'registry.json'; registry.write_text(json.dumps(reg))
    scenario_file=tmp_path/'scenario.json'; scenario_file.write_text(json.dumps(scenario))
    dest=tmp_path/'contract.json'
    p,out=run_cli(store.root,'contract','prepare','--registry',str(registry),'--index',idx,
                  '--world',world['world'],'--scenario',str(scenario_file),'--output',str(dest))
    assert p.returncode==0,p.stderr
    assert json.loads(dest.read_bytes())==out['contract']
    assert 'token' not in out['contract']
