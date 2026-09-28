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
