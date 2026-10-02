import importlib
import json
import os
from pathlib import Path
import pytest

from kneekura_tech_hub.minecraft.storage import Store, ContractError
from kneekura_tech_hub.minecraft.workspace import file_hash, workspace_fingerprint


def mod():
    try: return importlib.import_module('kneekura_tech_hub.minecraft.execution')
    except ImportError: pytest.fail('Local registered execution is not implemented')


@pytest.fixture
def local(tmp_path):
    workspace=tmp_path/'project'; workspace.mkdir()
    (workspace/'src').mkdir(); (workspace/'src/Foo.java').write_text('class Foo {}')
    wrapper=workspace/'gradlew'; wrapper.write_text('#!/bin/sh\nmkdir -p build/libs\nprintf "fixture-output" > build/libs/demo.jar\necho called >> build/calls\n')
    wrapper.chmod(0o700)
    reg={'workspace':str(workspace),'allow_gradle':True,'wrapper_sha256':file_hash(wrapper),
         'allowed_kinds':['compile','unit','gametest'],'build_outputs':['build/libs/demo.jar'],
         'remaining_launches':1,'launch_budget_id':'one-session'}
    return Store(tmp_path/'store'),reg,workspace


def test_real_registered_subprocess_build_capture_and_no_duplicate_run(local):
    store,reg,workspace=local
    result=mod().execute(store,reg,kind='compile',request_id='compile-1')
    assert result['outcome']=='PASS' and result['assertion_domain']=='compile_only'
    receipt=store.json(result['receipt_hash'])
    assert receipt['source_generation']==workspace_fingerprint(workspace)
    assert store.read(receipt['outputs'][0]['content_hash'])==b'fixture-output'
    same=mod().execute(store,reg,kind='compile',request_id='compile-1')
    assert same['receipt_hash']==result['receipt_hash'] and same['replayed_execution'] is False
    assert (workspace/'build/calls').read_text().count('called')==1


def test_tampered_wrapper_and_unapproved_dispatch_are_rejected(local):
    store,reg,workspace=local; reg['allow_gradle']=False
    with pytest.raises(ContractError): mod().execute(store,reg,kind='compile',request_id='a')
    reg['allow_gradle']=True; (workspace/'gradlew').write_text('#!/bin/sh\necho bad')
    with pytest.raises(ContractError): mod().execute(store,reg,kind='compile',request_id='a')
    assert not (workspace/'build/calls').exists()


def test_changing_sources_during_build_is_not_success(local):
    store,reg,workspace=local
    wrapper=workspace/'gradlew'; wrapper.write_text('#!/bin/sh\nprintf "class Changed {}" > src/Foo.java\nmkdir -p build/libs\necho x > build/libs/demo.jar\n'); reg['wrapper_sha256']=file_hash(wrapper)
    result=mod().execute(store,reg,kind='compile',request_id='a')
    assert result['outcome']=='BLOCKED' and 'changed' in str(result['reasons'])


def test_same_request_with_changed_kind_or_inputs_is_not_reexecuted(local):
    store,reg,workspace=local; mod().execute(store,reg,kind='compile',request_id='x')
    with pytest.raises(ContractError): mod().execute(store,reg,kind='unit',request_id='x')
    (workspace/'src/Foo.java').write_text('class Different {}')
    with pytest.raises(ContractError): mod().execute(store,reg,kind='compile',request_id='x')


def test_missing_build_outputs_cannot_claim_packaging_success(local):
    store,reg,workspace=local; reg['build_outputs']=['build/libs/absent.jar']
    result=mod().execute(store,reg,kind='compile',request_id='x')
    assert result['outcome']=='BLOCKED'


def test_unit_exit_zero_with_zero_tests_is_not_pass(local):
    store,reg,workspace=local
    result=mod().execute(store,reg,kind='unit',request_id='x')
    assert result['outcome']=='NOT_RUN' and result['tests_executed']==0


def test_unit_xml_test_failure_is_not_masked_by_exit_zero(local):
    store,reg,workspace=local
    wrapper=workspace/'gradlew'; wrapper.write_text('''#!/bin/sh
mkdir -p build/test-results/test
cat > build/test-results/test/TEST-demo.xml <<'XML'
<testsuite tests="1"><testcase classname="demo" name="bad"><failure message="oops"/></testcase></testsuite>
XML
'''); reg['wrapper_sha256']=file_hash(wrapper)
    result=mod().execute(store,reg,kind='unit',request_id='x')
    assert result['outcome']=='FAIL' and result['tests_executed']==1


def test_game_cannot_reuse_unowned_world(local):
    store,reg,workspace=local; world=workspace/'saves/production'; world.mkdir(parents=True)
    reg['test_worlds']=[str(world)]
    with pytest.raises(ContractError): mod().execute(store,reg,kind='gametest',world=str(world),request_id='x')
    assert not (workspace/'build/calls').exists()


def test_world_provision_preserves_template_and_never_overwrites(local):
    store,reg,workspace=local; template=workspace/'templates/small'; template.mkdir(parents=True)
    (template/'level.dat').write_bytes(b'fixture-world')
    reg['world_templates']=[str(template)]
    result=mod().prepare_world(store,reg,template=str(template),request_id='world-1')
    destination=Path(result['world']); assert destination!=template
    assert (destination/'level.dat').read_bytes()==b'fixture-world'
    assert (destination.parent/'.kneekura-run.json').is_file()
    with pytest.raises(ContractError): mod().prepare_world(store,reg,template=str(template),request_id='world-1')
    assert (template/'level.dat').read_bytes()==b'fixture-world'


def test_request_receipt_is_unknown_after_interruption_not_retried(local):
    store,reg,workspace=local
    def interrupted(*a,**kw): raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt): mod().execute(store,reg,kind='compile',request_id='x',runner=interrupted)
    result=mod().execute(store,reg,kind='compile',request_id='x')
    assert result['outcome']=='UNKNOWN' and result['retry_allowed'] is False
    assert not (workspace/'build/calls').exists()

def test_userdev_directory_output_is_captured_as_exact_inventory(local):
    store,reg,workspace=local
    reg['build_outputs']=['build/libs']
    out=mod().execute(store,reg,kind='compile',request_id='dir-build')
    assert out['outcome']=='PASS'
    artifact=out['outputs'][0]
    assert artifact['kind']=='directory'
    listing=store.json(artifact['content_hash'])
    assert listing[0]['path']=='demo.jar' and store.read(listing[0]['hash'])==b'fixture-output'


@pytest.mark.parametrize('tampered',[False,True])
def test_signed_gametest_counts_are_not_left_at_unit_default(local,monkeypatch,tampered):
    import base64
    import hmac
    from kneekura_tech_hub.minecraft import runtime
    from kneekura_tech_hub.minecraft.storage import canonical
    from test_minecraft_verification import contract, report
    store,reg,root=local
    template=root/'empty';template.mkdir();reg['world_templates']=[str(template)]
    world=mod().prepare_world(store,reg,template=str(template),request_id='counter-world')
    c=contract();c.update(dirty_hash=workspace_fingerprint(root),world_id=world['world_id'],
                          world_template_hash=world['world_template_hash'])
    token='a'*64
    def fixture_session(store,registry,actual,*,directory):
        return {'token':token,'contract':actual,'path':directory/'session.json'}
    monkeypatch.setattr(runtime,'create_session',fixture_session)
    def fixture_runner(*args,**kwargs):
        data=report(c)
        data['tests'].append({'id':'optional.control','required':False,'status':'FAIL'})
        for key in ('detected_test_ids','executed_test_ids'): data[key].append('optional.control')
        data.update(detected_count=2,executed_count=2)
        raw=canonical(data)
        envelope={'payload_b64':base64.b64encode(raw).decode(),
                  'signature':hmac.digest(token.encode(),b'gametest-report\n'+raw,'sha256').hex()}
        if tampered: envelope['signature']='0'*64
        (Path(world['directory'])/'gametest-report.json').write_bytes(canonical(envelope))
        return {'stdout':b'fixture producer, not a game','completed':True,'exit_code':0}
    result=mod().execute(store,reg,kind='gametest',request_id='counter-run',
                         world=world['world'],contract=c,runner=fixture_runner)
    assert result['tests_executed']==(0 if tampered else 2)
    assert result['outcome']==('NOT_RUN' if tampered else 'PASS')


@pytest.mark.parametrize('layout,relative', [('server','proof-world'), ('client','saves/proof-world')])
def test_prepared_world_layout_matches_game_save_location(local,layout,relative):
    store,reg,root=local
    template=root/'templates/small'; template.mkdir(parents=True)
    (template/'level.dat').write_bytes(b'fixture-world')
    reg['world_templates']=[str(template)]
    result=mod().prepare_world(store,reg,template=str(template),request_id='layout-world',
                               world_name='proof-world',layout=layout)
    run=Path(result['directory']); world=Path(result['world'])
    assert world==run/relative
    assert result['world_layout']==layout
    assert (world/'level.dat').read_bytes()==b'fixture-world'
    marker,marker_path=mod()._owned_world(root,str(world))
    assert marker['world_layout']==layout and marker_path==run/'.kneekura-run.json'
    assert json.loads(marker_path.read_bytes())['world']==str(world)
    with pytest.raises(ContractError,match='overwrite/reuse'):
        mod().prepare_world(store,reg,template=str(template),request_id='layout-world',layout=layout)
    assert (template/'level.dat').read_bytes()==b'fixture-world'


@pytest.mark.parametrize('damage', ['changed','used','layout','marker','saves_symlink','run_symlink','world_symlink'])
def test_client_world_retains_freshness_ownership_and_symlink_guards(local,damage):
    store,reg,root=local
    template=root/'templates/small'; template.mkdir(parents=True)
    (template/'level.dat').write_bytes(b'fixture-world'); reg['world_templates']=[str(template)]
    result=mod().prepare_world(store,reg,template=str(template),request_id='layout-world',layout='client')
    run=Path(result['directory']); world=Path(result['world']); marker_path=run/'.kneekura-run.json'
    if damage=='changed': (world/'level.dat').write_bytes(b'edited')
    elif damage in ('used','layout'):
        marker=json.loads(marker_path.read_bytes())
        marker['fresh' if damage=='used' else 'world_layout']=False if damage=='used' else 'server'
        marker_path.write_text(json.dumps(marker))
    elif damage=='marker': marker_path.unlink()
    else:
        original={'saves_symlink':world.parent,'run_symlink':run,'world_symlink':world}[damage]
        moved=original.with_name(original.name+'-moved'); original.rename(moved)
        original.symlink_to(moved,target_is_directory=True)
    with pytest.raises(ContractError): mod()._owned_world(root,str(world))


@pytest.mark.parametrize('layout', ['unknown','../client','',None])
def test_unknown_world_layout_is_rejected_without_creating_run(local,layout):
    store,reg,root=local
    template=root/'empty'; template.mkdir(); reg['world_templates']=[str(template)]
    with pytest.raises(ContractError,match='layout'):
        mod().prepare_world(store,reg,template=str(template),request_id='layout-world',layout=layout)
    assert not (root/'.kneekura-runs').exists()


@pytest.mark.parametrize('layout,kind', [('server','client'), ('client','gametest')])
def test_launch_kind_cannot_reuse_the_other_world_layout(local,layout,kind):
    store,reg,root=local; reg['allowed_kinds'].append('client')
    template=root/'empty'; template.mkdir(); reg['world_templates']=[str(template)]
    world=mod().prepare_world(store,reg,template=str(template),request_id='layout-world',layout=layout)
    with pytest.raises(ContractError,match='layout'):
        mod().execute(store,reg,kind=kind,request_id='wrong-layout',world=world['world'],contract={})
    assert json.loads((Path(world['directory'])/'.kneekura-run.json').read_bytes())['fresh'] is True
    assert not (store.root/'launches').exists()
    assert not (root/'build/calls').exists()


def test_client_launch_passes_exact_prepared_layout_to_session(local,monkeypatch):
    from kneekura_tech_hub.minecraft import runtime
    from test_minecraft_verification import contract
    store,reg,root=local; reg['allowed_kinds'].append('client')
    template=root/'empty'; template.mkdir(); reg['world_templates']=[str(template)]
    world=mod().prepare_world(store,reg,template=str(template),request_id='layout-world',
                              world_name='proof-world',layout='client')
    c=contract(); c.update(dirty_hash=workspace_fingerprint(root),world_id=world['world_id'],
                          world_template_hash=world['world_template_hash'],physical_side='client')
    observed={}
    def fixture_session(store,registry,actual,*,directory):
        observed.update(registry=registry,directory=directory)
        return {'path':directory/'session.json'}
    monkeypatch.setattr(runtime,'create_session',fixture_session)
    def fixture_runner(argv,cwd,**kwargs):
        observed['argv']=argv
        return {'stdout':b'fixture, not a game','completed':True,'exit_code':0}
    result=mod().execute(store,reg,kind='client',request_id='client-layout',world=world['world'],
                         contract=c,runner=fixture_runner)
    assert observed['registry']['world_layout']=='client'
    assert observed['registry']['world_directory_name']=='proof-world'
    assert observed['directory']==Path(world['directory'])
    assert '-PkneekuraRunDirectory='+world['directory'] in observed['argv']
    assert observed['argv'][-1]=='runClient'
    assert result['outcome']=='NOT_RUN' and result['tests_executed']==0
    assert json.loads((Path(world['directory'])/'.kneekura-run.json').read_bytes())['fresh'] is False


def test_client_preparation_ignores_unrelated_workspace_saves(local):
    store,reg,root=local
    template=root/'empty'; template.mkdir(); reg['world_templates']=[str(template)]
    unrelated=root/'other-saves'; unrelated.mkdir()
    (root/'saves').symlink_to(unrelated,target_is_directory=True)
    result=mod().prepare_world(store,reg,template=str(template),request_id='isolated-client',layout='client')
    assert Path(result['world'])==Path(result['directory'])/'saves/gametestserver'
    assert list(unrelated.iterdir())==[]


def test_legacy_server_marker_remains_owned_without_layout_field(local):
    store,reg,root=local
    template=root/'empty'; template.mkdir(); reg['world_templates']=[str(template)]
    world=mod().prepare_world(store,reg,template=str(template),request_id='legacy-server')
    marker_path=Path(world['directory'])/'.kneekura-run.json'
    marker=json.loads(marker_path.read_bytes()); marker.pop('world_layout')
    marker_path.write_text(json.dumps(marker))
    owned,path=mod()._owned_world(root,world['world'],layout='server')
    assert owned==marker and path==marker_path
    with pytest.raises(ContractError,match='layout'):
        mod()._owned_world(root,world['world'],layout='client')
