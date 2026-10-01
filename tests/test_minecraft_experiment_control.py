"""Scoped transport is separate authority; protocol fixtures never run Minecraft."""
import copy
import importlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from kneekura_tech_hub.minecraft import experiment_bridge as bridge
from kneekura_tech_hub.minecraft.storage import ContractError, canonical, digest
from test_minecraft_experiment_bridge import prepared, tree


def api():
    spec = importlib.util.find_spec('kneekura_tech_hub.minecraft.experiment_control')
    assert spec is not None, 'scoped-control transport is not implemented'
    return importlib.import_module(spec.name)


@pytest.fixture
def control(prepared, tmp_path):
    store, req = prepared
    request_hash = bridge.prepare_experiment(store, req)['request_hash']
    root = tmp_path / 'lab'
    for name in api().MODULES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('// pinned protocol fixture\n')
    entry = root / 'debug-workspace/bridge/owner-control-cli.mjs'
    entry.write_text("""import fs from 'node:fs';
const r=JSON.parse(fs.readFileSync(process.argv[5]));
const owner=JSON.parse(fs.readFileSync(process.argv[3]));
if (['LD_PRELOAD','LD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES','PRIVATE_CONTROL_SECRET'].some(k=>process.env[k])) throw new Error('INHERITED_ENV');
let out={schemaVersion:1,operation:r.operation,requestHash:r.requestHash,status:'OWNER_RECORDED',runtimeAttestation:'NOT_ESTABLISHED'};
if(r.operation==='inspect_owner') out.ownerEnvelopeHash=owner.run.ownerEnvelopeHash;
if(r.operation==='submit_action') Object.assign(out,{status:'REQUESTED',selectedActionId:r.selectedActionId});
if(r.operation==='request_capture') Object.assign(out,{status:'REQUESTED',captureIndex:r.captureIndex});
if(r.operation==='inspect_action') Object.assign(out,{status:'NEVER_SEEN',selectedActionId:r.selectedActionId,recordedStatus:null,evidenceHashes:[],dispatchAllowed:false});
console.log(JSON.stringify(out));
""")
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node unavailable')
    node = Path(node).resolve()
    inputs = tmp_path / 'inputs'; inputs.mkdir(mode=0o700)
    runtime = tmp_path / 'runtime'; runtime.mkdir(mode=0o700)
    run = runtime / 'run-01'; (run / 'control').mkdir(parents=True, mode=0o700)
    identity = {'debugSessionId':'session-01','runId':'run-01','runSnapshotId':'snapshot-01',
                'processEpoch':1,'experimentId':req['experiment_id'],'requestHash':request_hash}
    envelope = {'schemaVersion':1,'debugSessionId':identity['debugSessionId'],'runId':identity['runId'],
        'runSnapshotId':identity['runSnapshotId'],'processEpoch':1,'handshakeNonce':'private-nonce-not-in-public-receipt',
        'requestHash':request_hash,'grantHash':'1'*64,'materialDescriptorHash':'2'*64,
        'worldRegistrationHash':'3'*64,'controlMode':'BOUNDED_DIAGNOSTIC_CONTROL'}
    path = run / 'control/owner-envelope.json'; path.write_bytes(canonical(envelope)); path.chmod(0o600)
    owner = {'schemaVersion':1,'runtimeRoot':str(runtime),'inputRoot':str(inputs),
        'run':{'runDir':str(run),'identity':identity,'ownerEnvelopeHash':digest(canonical(envelope))}}
    owner_file = tmp_path / 'owner.json'; owner_file.write_bytes(canonical(owner)); owner_file.chmod(0o600)
    registry = {'schema_version':1,'enabled':True,'backend':'kneekura.lab.scoped-control.v1',
        'workspace':str(root),'source_revision':'a'*40,'executable':str(node),
        'executable_hash':digest(node.read_bytes()),'module_hashes':{name:digest((root/name).read_bytes()) for name in api().MODULES},
        'owner_file':str(owner_file),'owner_hash':digest(owner_file.read_bytes()),'timeout_seconds':5}
    return store, req, registry, owner


def test_new_scoped_registry_is_required():
    assert api().BACKEND == 'kneekura.lab.scoped-control.v1'


def test_registry_inspection_is_inert_and_reports_no_live_authority(control, monkeypatch):
    store, _, registry, _ = control; before = tree(store.root)
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('registry spawned'))
    result = api().inspect_registry(registry)
    assert result['status'] == 'REGISTERED'
    assert result['runtime_attestation'] == 'NOT_ESTABLISHED'
    assert result['execution'] == 'NOT_RUN'
    assert str(Path(registry['owner_file']).parent) not in json.dumps(result)
    assert tree(store.root) == before


@pytest.mark.parametrize('change', ['legacy','missing_module','changed_module','extra_module','owner','envelope',
    'foreign_identity','owner_symlink','envelope_symlink','bool_epoch','run_escape','extra_field'])
def test_invalid_pinned_authority_rejects_before_process(control, monkeypatch, change):
    store, _, registry, owner = control
    if change == 'legacy': registry['backend'] = 'kneekura.lab.local-bridge.v1'
    if change == 'missing_module': registry['module_hashes'].pop(next(iter(registry['module_hashes'])))
    if change == 'changed_module': (Path(registry['workspace'])/next(iter(registry['module_hashes']))).write_text('changed')
    if change == 'extra_module': registry['module_hashes']['../../other.mjs'] = '1'*64
    if change == 'owner': registry['owner_hash'] = '0'*64
    if change == 'envelope': owner['run']['ownerEnvelopeHash'] = '0'*64
    if change == 'foreign_identity': owner['run']['identity']['runId'] = 'foreign'
    if change == 'bool_epoch': owner['run']['identity']['processEpoch'] = True
    if change == 'run_escape': owner['run']['runDir'] = owner['inputRoot']
    if change == 'extra_field': registry['args'] = ['--eval', 'process.exit(0)']
    if change in ('envelope','foreign_identity','bool_epoch','run_escape'):
        Path(registry['owner_file']).write_bytes(canonical(owner)); registry['owner_hash'] = digest(canonical(owner))
    if change in ('owner_symlink','envelope_symlink'):
        path = Path(registry['owner_file']) if change == 'owner_symlink' else Path(owner['run']['runDir'])/'control/owner-envelope.json'
        original = path.with_suffix('.original'); path.rename(original); path.symlink_to(original.name)
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('invalid authority spawned'))
    with pytest.raises((ContractError, OSError)):
        api().inspect_registry(registry)


def test_fixed_submission_only_selects_saved_action_and_keeps_pending(control, monkeypatch):
    store, req, registry, owner = control
    monkeypatch.setenv('PRIVATE_CONTROL_SECRET', 'not-in-child')
    action_id = (req['initial_state'] + req['actions'])[0]['action_id']
    value = api().submit_action(store, registry, owner['run']['identity']['requestHash'], action_id)
    assert value['status'] == 'REQUESTED'
    assert value['can_replay'] is False
    assert value['next_operation'] == 'experiment.inspect_action'
    assert value['runtime_attestation'] == 'NOT_ESTABLISHED'
    retained = store.json(value['receipt_hash'])
    assert retained['reported']['selectedActionId'] == action_id
    assert 'COMPLETED' not in json.dumps(retained) and 'PASS' not in json.dumps(retained)
    assert str(Path(registry['owner_file']).parent) not in json.dumps(retained)
    assert 'private-nonce' not in json.dumps(retained)


@pytest.mark.parametrize('selection', ['missing', '../escape', 'x; launch', {'operation':'set_block'}])
def test_action_selection_cannot_supply_new_action(control, monkeypatch, selection):
    store, _, registry, owner = control
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('invalid selection spawned'))
    with pytest.raises(ContractError):
        api().submit_action(store, registry, owner['run']['identity']['requestHash'], selection)


@pytest.mark.parametrize('failure', ['timeout','output_limit','exit','raise','foreign','success_claim','extra'])
def test_ambiguous_subprocess_retains_unknown_and_never_retries(control, monkeypatch, failure):
    store, req, registry, owner = control; calls = []
    action_id = (req['initial_state'] + req['actions'])[0]['action_id']
    def run(*args, **kwargs):
        calls.append((args, kwargs))
        if failure == 'raise': raise OSError('/private/error-after-possible-submission')
        response = {'schemaVersion':1,'operation':'submit_action','requestHash':owner['run']['identity']['requestHash'],
            'status':'REQUESTED','runtimeAttestation':'NOT_ESTABLISHED','selectedActionId':action_id}
        if failure == 'foreign': response['requestHash'] = 'f'*64
        if failure == 'success_claim': response['status'] = 'COMPLETED'
        if failure == 'extra': response['stdout'] = 'private log'
        return {'completed':failure not in ('timeout','output_limit'),'exit_code':1 if failure == 'exit' else 0,
            'timed_out':failure == 'timeout','output_limited':failure == 'output_limit','stdout':canonical(response)}
    monkeypatch.setattr(api(), 'run_process', run)
    result = api().submit_action(store, registry, owner['run']['identity']['requestHash'], action_id)
    assert len(calls) == 1
    assert result['status'] == 'OUTCOME_UNKNOWN' and result['reported'] is None
    assert result['can_replay'] is False and result['next_operation'] == 'experiment.inspect_action'
    assert 'private' not in json.dumps(store.json(result['receipt_hash']))
    assert calls[0][1]['inherit_environment'] is False


def test_receipt_is_available_before_possible_submission(control, monkeypatch):
    store, req, registry, owner = control
    action_id = (req['initial_state'] + req['actions'])[0]['action_id']
    before = store.pinned_hashes()
    def interrupted(*args, **kwargs):
        assert any(store.json(h).get('status') == 'OUTCOME_UNKNOWN' for h in store.pinned_hashes() - before)
        raise KeyboardInterrupt()
    monkeypatch.setattr(api(), 'run_process', interrupted)
    with pytest.raises(KeyboardInterrupt):
        api().submit_action(store, registry, owner['run']['identity']['requestHash'], action_id)


def test_request_owner_mismatch_rejects_before_process(control, monkeypatch):
    store, _, registry, _ = control
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('foreign request spawned'))
    with pytest.raises((ContractError, OSError)):
        api().inspect_owner(store, registry, '0'*64)


@pytest.mark.parametrize('index', [-1, True, 1, 3, 4, 16, 1.5, '0'])
def test_capture_index_is_bounded_integer(control, monkeypatch, index):
    store, _, registry, owner = control
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('invalid capture spawned'))
    with pytest.raises(ContractError):
        api().request_capture(store, registry, owner['run']['identity']['requestHash'], index)


def test_capture_request_is_one_bounded_cardinal_four_slot(control):
    store, _, registry, owner = control
    result = api().request_capture(store, registry, owner['run']['identity']['requestHash'], 0)
    assert result['status'] == 'REQUESTED' and result['can_replay'] is False
    assert api().inspect_receipt(store, result['receipt_hash'])['requires_reconciliation'] is True


def test_inspect_action_is_read_only_and_no_replay(control):
    store, req, registry, owner = control
    action_id = (req['initial_state'] + req['actions'])[0]['action_id']
    result = api().inspect_action(store, registry, owner['run']['identity']['requestHash'], action_id)
    assert result['status'] == 'NEVER_SEEN'
    assert result['reported']['dispatchAllowed'] is False and result['can_replay'] is False


@pytest.mark.parametrize('selection', ['abc', ['same','same'], ['id']*33, [{'path':'/private'}]])
def test_export_selection_is_an_explicit_bounded_list(control, monkeypatch, selection):
    store, _, registry, owner = control
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('invalid export selection spawned'))
    with pytest.raises(ContractError):
        api().export_result(store, registry, owner['run']['identity']['requestHash'], observation_ids=selection)


@pytest.mark.parametrize('status,recorded,evidence', [('VERIFIED','OUTCOME_UNKNOWN',['1'*64]),
    ('NEVER_SEEN','REQUESTED',[]), ('VERIFIED','VERIFIED',[]), ('NEVER_SEEN',None,['1'*64])])
def test_reconciliation_cannot_erase_contradictory_or_unbacked_status(control, monkeypatch, status, recorded, evidence):
    store, req, registry, owner = control
    action_id = (req['initial_state']+req['actions'])[0]['action_id']
    response = {'schemaVersion':1,'operation':'inspect_action','requestHash':owner['run']['identity']['requestHash'],
        'status':status,'runtimeAttestation':'NOT_ESTABLISHED','selectedActionId':action_id,
        'recordedStatus':recorded,'evidenceHashes':evidence,'dispatchAllowed':False}
    monkeypatch.setattr(api(),'run_process',lambda *a,**k:{'completed':True,'exit_code':0,'stdout':canonical(response)})
    got = api().inspect_action(store,registry,owner['run']['identity']['requestHash'],action_id)
    assert got['status']=='OUTCOME_UNKNOWN' and got['reported'] is None


def test_failed_export_recommends_read_only_inspection_without_missing_manifest(control,monkeypatch):
    store,_,registry,owner=control
    monkeypatch.setattr(api(),'run_process',lambda *a,**k:{'completed':False,'exit_code':2,'stdout':b'blocked'})
    got=api().export_result(store,registry,owner['run']['identity']['requestHash'])
    assert got['status']=='OUTCOME_UNKNOWN' and got['next_operation']=='experiment.inspect_owner'


@pytest.mark.parametrize('suffix', ['', 'nested-run'])
def test_derived_export_directory_cannot_overlap_sealed_run(control, suffix):
    _, _, registry, owner = control
    inputs = Path(owner['inputRoot'])
    destination = inputs/'exports'/owner['run']['identity']['requestHash']
    if suffix: destination /= suffix
    destination.parent.mkdir(parents=True)
    Path(owner['run']['runDir']).rename(destination)
    owner['runtimeRoot'] = str(inputs); owner['run']['runDir'] = str(destination)
    Path(registry['owner_file']).write_bytes(canonical(owner)); registry['owner_hash'] = digest(canonical(owner))
    with pytest.raises(ContractError): api().inspect_registry(registry)
