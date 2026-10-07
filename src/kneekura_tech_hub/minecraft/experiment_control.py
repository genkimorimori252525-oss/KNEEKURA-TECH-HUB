"""Explicit pinned LAB scoped-control transport, never a launch service.

The private owner registration is separate from ExperimentRequest and from the
legacy registration-only adapter. LAB's shared journal and Java gate retain all
replay, ordering and runtime authority. These CAS receipts only retain what the
transport reported; they cannot establish completion or loaded-target identity.
"""
from __future__ import annotations

import math
from pathlib import Path
import re
import time

from .asset_contract import decode_json
from .experiment_adapter import _directory, _exclusive, _file, _FIELDS
from .experiment_bridge import _read_bounded, load_experiment
from .experiment_contract import validate_experiment_request
from .process import run_process
from .storage import ContractError, IntegrityError, Store, canonical, key_for, valid_hash

BACKEND = 'kneekura.lab.scoped-control.v1'
MODULES = (
    'debug-workspace/bridge/action-journal.mjs', 'debug-workspace/bridge/arena-contract.mjs',
    'debug-workspace/bridge/json.mjs', 'debug-workspace/bridge/materials.mjs',
    'debug-workspace/bridge/owner-action-adapter.mjs', 'debug-workspace/bridge/owner-control-cli.mjs',
    'debug-workspace/bridge/owner-grant.mjs', 'debug-workspace/bridge/owner-prelaunch.mjs',
    'debug-workspace/bridge/owner-tank-rotation.mjs',
    'debug-workspace/bridge/mob-pov.mjs',
    'debug-workspace/bridge/owner-trigger-config.mjs', 'debug-workspace/bridge/owner-trigger-source.mjs',
    'debug-workspace/bridge/registration.mjs', 'debug-workspace/bridge/result-export-source.mjs',
    'debug-workspace/bridge/result-export.mjs', 'debug-workspace/bridge/selected-action.mjs',
    'debug-workspace/bridge/tank-preflight.mjs', 'debug-workspace/bridge/tank-resource.mjs',
    'debug-workspace/evidence/broker.mjs', 'debug-workspace/evidence/capture.mjs',
    'debug-workspace/evidence/ingest.mjs', 'debug-workspace/evidence/ring-buffer.mjs',
    'debug-workspace/evidence/runtime.mjs', 'debug-workspace/evidence/schema.mjs',
    'debug-workspace/evidence/store.mjs', 'debug-workspace/evidence/visual-capture.mjs',
    'debug-workspace/evidence/tank-contract.mjs',
    'debug-workspace/evidence/trigger-capture.mjs', 'debug-workspace/evidence/watchpoints.mjs',
    'debug-workspace/evidence/visual-packet.mjs', 'debug-workspace/evidence/visual-request-contract.mjs',
    'simlab/golden/png.mjs')
_ID_FIELDS = {'debugSessionId', 'runId', 'runSnapshotId', 'processEpoch', 'experimentId', 'requestHash'}
_ENVELOPE_FIELDS = {'schemaVersion', 'debugSessionId', 'runId', 'runSnapshotId', 'processEpoch',
    'handshakeNonce', 'requestHash', 'grantHash', 'materialDescriptorHash', 'worldRegistrationHash', 'controlMode'}
_COMMON = {'schemaVersion', 'operation', 'requestHash', 'status', 'runtimeAttestation'}
_SUBMISSIONS = {'submit_action', 'request_capture', 'request_cleanup'}
_JOURNAL = {'REQUESTED', 'NOT_RUN', 'VERIFIED', 'FAILED', 'PARTIAL_APPLY', 'OUTCOME_UNKNOWN'}
_RECEIPT_FIELDS = {'schema_version', 'record_type', 'registry_hash', 'request_hash', 'command',
    'status', 'reported', 'runtime_attestation', 'timed_out', 'output_limited', 'can_replay'}


def _id(value):
    if not isinstance(value, str) or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}', value):
        raise ContractError('Bounded control identity required')
    return value


def _timeout(registry):
    value = registry.get('timeout_seconds') if isinstance(registry, dict) else None
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 10:
        raise ContractError('Scoped-control deadline must be at most ten seconds')
    return value


def _trigger_config(value, request):
    fields = {'enabled', 'triggerKinds', 'offsetsMs', 'toleranceMs', 'cooldownMs',
              'maxWindows', 'captureBudget', 'timeoutMs', 'captureIndices'}
    if (not isinstance(value, dict) or set(value) != fields or value['enabled'] is not True
            or value['triggerKinds'] != ['ARENA_EXIT'] or request['visual_rig']['mode'] != 'cardinal-4-snapshot-v1'):
        raise ContractError('Exact selected owner trigger configuration required')
    offsets = value['offsetsMs']; slots = value['captureIndices']
    if (not isinstance(offsets, list) or not 1 <= len(offsets) <= 21
            or any(type(n) is not int or not -10000 <= n <= 10000 for n in offsets)
            or any(b-a < 250 for a, b in zip(offsets, offsets[1:]))):
        raise ContractError('Bounded sorted trigger sample offsets required')
    bounds = {'toleranceMs':(0,250), 'cooldownMs':(1000,60000), 'maxWindows':(1,8),
              'captureBudget':(1,4), 'timeoutMs':(max(1,*offsets),min(20000,request['budgets']['time_budget_ms']))}
    if any(type(value[k]) is not int or not lo <= value[k] <= hi for k,(lo,hi) in bounds.items()):
        raise ContractError('Trigger bounds exceed the retained request')
    if (not isinstance(slots, list) or len(slots) != value['captureBudget']
            or any(type(n) is not int or not 0 <= n < request['budgets']['max_captures']//4 for n in slots)
            or len(set(slots)) != len(slots)):
        raise ContractError('Unique declared trigger capture slots required')
    return value


def _registry(value, *, deadline=None, require_triggers=False):
    if (not isinstance(value, dict) or set(value) != _FIELDS or type(value['schema_version']) is not int
            or value['schema_version'] != 1 or value['enabled'] is not True or value['backend'] != BACKEND):
        raise ContractError('Separate enabled scoped-control registry required')
    _timeout(value)
    if not isinstance(value['source_revision'], str) or not re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}', value['source_revision']):
        raise ContractError('Exact declared source revision required')
    root = _directory(value['workspace'])
    modules = value['module_hashes']
    if not isinstance(modules, dict) or set(modules) != set(MODULES):
        raise ContractError('Exact scoped-control module closure required')
    for name in MODULES:
        _file(root/name, 1024*1024, expected=modules[name], retain=False, deadline=deadline)
    _file(value['executable'], 256*1024*1024, expected=value['executable_hash'], retain=False, deadline=deadline)
    owner = decode_json(_file(value['owner_file'], 65536, expected=value['owner_hash'], deadline=deadline), max_bytes=65536)
    if (not isinstance(owner, dict) or set(owner) != {'schemaVersion', 'runtimeRoot', 'inputRoot', 'run'}
            or type(owner['schemaVersion']) is not int or owner['schemaVersion'] != 1):
        raise ContractError('Exact private scoped owner configuration required')
    runtime = _directory(owner['runtimeRoot']); inputs = _directory(owner['inputRoot'])
    run = owner['run']
    if not isinstance(run, dict) or set(run) != {'runDir', 'identity', 'ownerEnvelopeHash'}:
        raise ContractError('Explicit pinned run owner required')
    run_dir = _directory(run['runDir'])
    if run_dir == runtime or not run_dir.is_relative_to(runtime) or inputs.is_relative_to(run_dir):
        raise ContractError('Owner run and transport directory scope invalid')
    identity = run['identity']
    if not isinstance(identity, dict) or set(identity) != _ID_FIELDS:
        raise ContractError('Exact registered run identity required')
    for name in ('debugSessionId', 'runId', 'runSnapshotId', 'experimentId'): _id(identity[name])
    if type(identity['processEpoch']) is not int or not 1 <= identity['processEpoch'] <= 2147483647:
        raise ContractError('Invalid owner process epoch')
    valid_hash(identity['requestHash'])
    export_root = inputs/'exports'/identity['requestHash']
    if export_root.is_relative_to(run_dir) or run_dir.is_relative_to(export_root):
        raise ContractError('Private export transport overlaps the sealed run')
    envelope = decode_json(_file(run_dir/'control/owner-envelope.json', 128*1024,
        expected=run['ownerEnvelopeHash'], deadline=deadline), max_bytes=128*1024)
    if (not isinstance(envelope, dict) or set(envelope) not in (_ENVELOPE_FIELDS, _ENVELOPE_FIELDS | {'triggerConfigHash'}, _ENVELOPE_FIELDS | {'tankRotationHash'})
            or type(envelope['schemaVersion']) is not int or envelope['schemaVersion'] != 1
            or envelope['controlMode'] != 'BOUNDED_DIAGNOSTIC_CONTROL'
            or type(envelope['processEpoch']) is not int):
        raise ContractError('Exact bounded owner envelope required')
    _id(envelope['handshakeNonce'])
    if len(envelope['handshakeNonce']) < 16: raise ContractError('Invalid owner nonce')
    for name in ('requestHash', 'grantHash', 'materialDescriptorHash', 'worldRegistrationHash'): valid_hash(envelope[name])
    for name in ('debugSessionId', 'runId', 'runSnapshotId', 'processEpoch', 'requestHash'):
        if envelope[name] != identity[name]: raise IntegrityError('Owner envelope identity mismatch')
    if 'triggerConfigHash' in envelope:
        valid_hash(envelope['triggerConfigHash'])
        config = decode_json(_file(run_dir/'control/owner-trigger-config.json', 16384,
            expected=envelope['triggerConfigHash'], deadline=deadline), max_bytes=16384)
        request = validate_experiment_request(decode_json(_file(run_dir/'control/owner-experiment-request.json', 128*1024,
            expected=identity['requestHash'], deadline=deadline), max_bytes=128*1024))
        if request['experiment_id'] != identity['experimentId']: raise IntegrityError('Trigger request identity mismatch')
        _trigger_config(config, request)
    elif require_triggers:
        raise ContractError('Explicit sealed owner trigger configuration required')
    if 'tankRotationHash' in envelope:
        # Closure pins only. The pinned Node parser and concrete Java owner independently validate maintenance permissions/geometry.
        valid_hash(envelope['tankRotationHash'])
        plan=decode_json(_file(run_dir/'control/owner-tank-rotation.json',16384,
            expected=envelope['tankRotationHash'],deadline=deadline),max_bytes=16384)
        fields={'schemaVersion','scope','rotationId','debugSessionId','runId','runSnapshotId','processEpoch','handshakeNonce',
            'requestHash','grantId','leaseId','arenaId','expectedArenaEpoch','expectedArenaRevision','previousOwnerFileSha256',
            'previousRecipeHash','previousTankEpoch','nextRecipeHash','nextRecipe'}
        if (not isinstance(plan,dict) or set(plan)!=fields or type(plan['schemaVersion']) is not int or plan['schemaVersion']!=1
                or plan['scope']!='PRE_EXPERIMENT_TANK_ROTATION' or not isinstance(plan['nextRecipe'],dict)):
            raise ContractError('Exact sealed Tank rotation pin required')
        for name in ('debugSessionId','runId','runSnapshotId','processEpoch','handshakeNonce','requestHash'):
            if type(plan[name]) is not type(envelope[name]) or plan[name]!=envelope[name]:raise IntegrityError('Tank pin identity mismatch')
        for name in ('rotationId','grantId','leaseId','arenaId'):_id(plan[name])
        for name in ('previousOwnerFileSha256','previousRecipeHash','nextRecipeHash'):valid_hash(plan[name])
        for name in ('expectedArenaEpoch','expectedArenaRevision','previousTankEpoch'):
            maximum=9007199254740990 if name=='previousTankEpoch' else 9007199254740991
            if type(plan[name]) is not int or not 0<=plan[name]<=maximum:raise ContractError('Invalid Tank pin counter')
        _file(run_dir/'control/owner-tank-predecessor.json',65536,expected=plan['previousOwnerFileSha256'],deadline=deadline)
    return root, owner


def inspect_registry(registry):
    """Read pinned local bytes only; reported ownership is not live attestation."""
    try:
        _registry(registry)
    except OSError:
        raise IntegrityError('Registered scoped-control inputs unavailable') from None
    return {'schema_version':1, 'status':'REGISTERED', 'backend':BACKEND, 'registry_hash':key_for(registry),
        'declared_source_revision':registry['source_revision'], 'identity_verification':'PINNED_EXECUTABLE_MODULES_AND_OWNER',
        'execution':'NOT_RUN', 'runtime_attestation':'NOT_ESTABLISHED'}


def _command(value, request=None):
    if not isinstance(value, dict): raise ContractError('Fixed scoped-control command required')
    operation = value.get('operation')
    extra = {'inspect_owner':set(), 'submit_action':{'selectedActionId'}, 'inspect_action':{'selectedActionId'},
        'request_capture':{'captureIndex'}, 'request_cleanup':set(), 'inspect_cleanup':set(), 'watch_triggers':set(),
        'mob_pov':{'commandIndex','cameraOperation'}, 'inspect_mob_pov':{'commandIndex'},
        'export_result':{'observationIds', 'timelineObservationIds', 'visualPacketHash'}}
    if operation == 'mob_pov' and value.get('cameraOperation') == 'attach':
        extra['mob_pov'] |= {'subjectUuid','durationMs'}
    if (not isinstance(operation, str) or operation not in extra or set(value) != {'schemaVersion', 'operation', 'requestHash'} | extra[operation]
            or type(value['schemaVersion']) is not int or value['schemaVersion'] != 1):
        raise ContractError('Unsupported scoped-control command')
    valid_hash(value['requestHash'])
    if operation in ('mob_pov','inspect_mob_pov'):
        if type(value['commandIndex']) is not int or not 0 <= value['commandIndex'] < 32:
            raise ContractError('Bounded camera command index required')
    if operation == 'mob_pov':
        if value['cameraOperation'] not in ('attach','snapshot','return'):
            raise ContractError('Fixed camera operation required')
        if request is not None and request['visual_rig']['mode'] != 'mob-eye-live-v1':
            raise ContractError('Retained mob POV request required')
        if value['cameraOperation'] == 'attach':
            if (type(value['durationMs']) is not int or not 1 <= value['durationMs'] <= 120000
                    or not isinstance(value['subjectUuid'],str)
                    or not re.fullmatch(r'[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}',value['subjectUuid'])
                    or request is not None and value['subjectUuid'] not in {s['uuid'] for s in request['subjects']}):
                raise ContractError('Exact registered subject and bounded camera duration required')
        if value['cameraOperation'] == 'snapshot' and request is not None and request['budgets']['max_captures'] == 0:
            raise ContractError('View-only request cannot capture an image')
    if operation in ('submit_action', 'inspect_action'):
        _id(value['selectedActionId'])
        if request is not None and value['selectedActionId'] not in {a['action_id'] for a in request['initial_state'] + request['actions']}:
            raise ContractError('Action must select the retained request')
    if operation == 'request_capture':
        index = value['captureIndex']
        if type(index) is not int or not 0 <= index < 4:
            raise ContractError('Bounded capture index required')
        if request is not None and (index >= request['budgets']['max_captures'] // 4 or request['visual_rig']['mode'] != 'cardinal-4-snapshot-v1'):
            raise ContractError('Capture exceeds retained visual request')
    if operation == 'export_result':
        for field in ('observationIds', 'timelineObservationIds'):
            rows = value[field]
            if not isinstance(rows, list) or len(rows) > 32: raise ContractError('Bounded observation selection required')
            for row in rows: _id(row)
            if len(set(rows)) != len(rows): raise ContractError('Duplicate observation selection')
        if value['visualPacketHash'] is not None: valid_hash(value['visualPacketHash'])
    return value


def _response(value, command, envelope_hash=None):
    if (not isinstance(value, dict) or type(value.get('schemaVersion')) is not int or value['schemaVersion'] != 1
            or value.get('operation') != command['operation'] or value.get('requestHash') != command['requestHash']
            or value.get('runtimeAttestation') != 'NOT_ESTABLISHED'):
        raise IntegrityError('Scoped-control response identity mismatch')
    op = command['operation']; fields = set(_COMMON)
    if op == 'inspect_owner':
        fields.add('ownerEnvelopeHash'); valid_hash(value.get('ownerEnvelopeHash'))
        if value['status'] != 'OWNER_RECORDED' or envelope_hash is not None and value['ownerEnvelopeHash'] != envelope_hash:
            raise IntegrityError('Reported owner mismatch')
    elif op == 'mob_pov':
        fields.update(('commandIndex','execution'))
        if value.get('status') == 'REQUESTED':
            fields.add('markerHash'); valid_hash(value.get('markerHash'))
        if (value.get('status') not in ('REQUESTED','ALREADY_REQUESTED') or value.get('execution') != 'NOT_CONFIRMED'
                or type(value.get('commandIndex')) is not int or value['commandIndex'] != command['commandIndex']):
            raise IntegrityError('Invalid pending camera command receipt')
    elif op == 'inspect_mob_pov':
        fields.update(('commandIndex','cameraOperation','restoration','imageHash','error','execution'))
        expected={'attach':'ATTACHED','snapshot':'CAPTURED','return':'RETURNED'}
        if (type(value.get('commandIndex')) is not int or value['commandIndex'] != command['commandIndex']
                or value.get('cameraOperation') not in expected or value.get('execution') != 'REPORTED_BY_OWNER'
                or value.get('status') not in (expected.get(value.get('cameraOperation')),'REJECTED','OUTCOME_UNKNOWN')
                or value.get('restoration') not in (None,'NOT_RUN','RESTORED','UNKNOWN','UNKNOWN_EVIDENCE_WRITE')
                or value.get('error') is not None and (not isinstance(value['error'],str) or len(value['error']) > 256)
                or value.get('status') == 'CAPTURED' and value.get('imageHash') is None):
            raise IntegrityError('Invalid reported camera operation receipt')
        if value.get('imageHash') is not None: valid_hash(value['imageHash'])
    elif op in _SUBMISSIONS:
        key = {'submit_action':'selectedActionId', 'request_capture':'captureIndex'}.get(op)
        if key is not None: fields.add(key)
        if (value['status'] not in ('REQUESTED', 'ALREADY_RECORDED', 'OUTCOME_UNKNOWN')
                or key is not None and (type(value.get(key)) is not type(command[key]) or value[key] != command[key])):
            raise IntegrityError('Submission response is not a pending scoped receipt')
    elif op in ('inspect_action', 'inspect_cleanup'):
        fields.update(('recordedStatus', 'evidenceHashes', 'dispatchAllowed'))
        if op == 'inspect_action': fields.add('selectedActionId')
        if ((op == 'inspect_action' and value.get('selectedActionId') != command['selectedActionId'])
                or value.get('dispatchAllowed') is not False
                or value.get('status') not in _JOURNAL | {'NEVER_SEEN'}
                or value.get('recordedStatus') not in _JOURNAL | {'ACCEPTED', 'APPLIED', None}
                or not isinstance(value.get('evidenceHashes'), list) or len(value['evidenceHashes']) > 32):
            raise IntegrityError('Invalid read-only control reconciliation')
        for h in value['evidenceHashes']: valid_hash(h)
        if len(set(value['evidenceHashes'])) != len(value['evidenceHashes']): raise IntegrityError('Duplicate evidence identity')
        status = value['status']; recorded = value['recordedStatus']
        expected = 'OUTCOME_UNKNOWN' if recorded in ('ACCEPTED', 'APPLIED') else recorded
        if ((recorded is None and status not in ('NEVER_SEEN', 'OUTCOME_UNKNOWN'))
                or recorded is not None and status != expected
                or status == 'NEVER_SEEN' and value['evidenceHashes']
                or recorded in ('APPLIED', 'VERIFIED', 'PARTIAL_APPLY') and not value['evidenceHashes']):
            raise IntegrityError('Contradictory or unbacked journal summary')
    elif op == 'watch_triggers':
        fields.add('captureWindowIds')
        windows = value.get('captureWindowIds')
        if (value.get('status') not in ('WINDOWS_FINISHED', 'OWNER_WATCH_DEADLINE', 'OWNER_NOT_ACTIVE')
                or not isinstance(windows, list) or len(windows) > 8):
            raise IntegrityError('Invalid bounded trigger watch summary')
        for window in windows: _id(window)
        if len(set(windows)) != len(windows): raise IntegrityError('Duplicate trigger window identity')
    else:
        fields.add('manifestHash'); valid_hash(value.get('manifestHash'))
        if value['status'] != 'EXPORTED': raise IntegrityError('Invalid export response')
    if set(value) != fields: raise IntegrityError('Unexpected scoped-control response fields')
    return value


def _next(command, status):
    return {'inspect_owner':'experiment.inspect_owner', 'submit_action':'experiment.inspect_action',
        'inspect_action':'experiment.inspect_action', 'request_capture':'experiment.inspect_owner',
        'request_cleanup':'experiment.inspect_cleanup', 'inspect_cleanup':'experiment.inspect_cleanup',
        'watch_triggers':'experiment.inspect_owner',
        'mob_pov':'experiment.inspect_mob_pov', 'inspect_mob_pov':'experiment.inspect_mob_pov',
        'export_result':'experiment.import_export' if status == 'EXPORTED' else 'experiment.inspect_owner'}[command['operation']]


def _record(registry, command, response=None, result=None):
    result = result or {}
    return {'schema_version':1, 'record_type':'experiment_control_receipt', 'registry_hash':key_for(registry),
        'request_hash':command['requestHash'], 'command':command,
        'status':response['status'] if response is not None else 'OUTCOME_UNKNOWN', 'reported':response,
        'runtime_attestation':'NOT_ESTABLISHED', 'timed_out':result.get('timed_out') is True,
        'output_limited':result.get('output_limited') is True, 'can_replay':False}


def _retain(store, record):
    h = store.put_json(record); store.pin(h, 'experiment-control:' + record['request_hash'])
    return dict(record, receipt_hash=h, next_operation=_next(record['command'], record['status']))


def _invoke(store, registry, command):
    ordinary_timeout = _timeout(registry)
    deadline = time.monotonic() + ordinary_timeout
    request = load_experiment(store, command['requestHash']); _command(command, request)
    watching = command['operation'] == 'watch_triggers'
    root, owner = _registry(registry, deadline=deadline, require_triggers=watching)
    if (owner['run']['identity']['requestHash'] != command['requestHash']
            or owner['run']['identity']['experimentId'] != request['experiment_id']):
        raise IntegrityError('Registered owner is for another experiment')
    command_file = _directory(owner['inputRoot']) / ('control-' + key_for(command) + '.json')
    _exclusive(command_file, canonical(command))
    _registry(registry, deadline=deadline, require_triggers=watching)
    remaining = deadline - time.monotonic()
    if remaining <= 0: raise ContractError('Scoped-control deadline exhausted before invocation')
    # Persist uncertainty first so interruption after process start cannot erase
    # the possible submission. This is an immutable receipt, not a replay ledger.
    pending = _retain(store, _record(registry, command))
    result = {}; response = None
    if watching:
        # Only this fixed explicit operation may observe for the retained budget.
        # LAB enforces the original nonrenewable owner lease and finite slots.
        deadline += request['budgets']['time_budget_ms'] / 1000
        remaining = deadline - time.monotonic()
    try:
        result = run_process([registry['executable'], str(root/'debug-workspace/bridge/owner-control-cli.mjs'),
            '--owner', registry['owner_file'], '--request', str(command_file)], root,
            timeout=remaining, max_output_bytes=65536, env={'NODE_OPTIONS':'', 'NODE_PATH':''}, inherit_environment=False)
        if not result['completed'] or result['exit_code'] != 0: raise ContractError('Scoped-control subprocess incomplete')
        _registry(registry, deadline=deadline)
        response = _response(decode_json(result['stdout'], max_bytes=65536), command, owner['run']['ownerEnvelopeHash'])
    except Exception:
        # Every failure after possible dispatch preserves UNKNOWN and omits raw
        # paths/logs. There is deliberately no retry branch.
        response = None
    if not isinstance(result, dict): result = {}
    return _retain(store, _record(registry, command, response, result)) if result or response is not None else pending


def inspect_owner(store: Store, registry: dict, request_hash: str):
    return _invoke(store, registry, {'schemaVersion':1, 'operation':'inspect_owner', 'requestHash':valid_hash(request_hash)})


def mob_pov(store: Store, registry: dict, request_hash: str, command_index: int, operation: str,
            *, subject_uuid: str | None = None, duration_ms: int | None = None):
    command={'schemaVersion':1,'operation':'mob_pov','requestHash':valid_hash(request_hash),'commandIndex':command_index,'cameraOperation':operation}
    if subject_uuid is not None: command['subjectUuid']=subject_uuid
    if duration_ms is not None: command['durationMs']=duration_ms
    return _invoke(store,registry,command)


def inspect_mob_pov(store: Store, registry: dict, request_hash: str, command_index: int):
    return _invoke(store,registry,{'schemaVersion':1,'operation':'inspect_mob_pov','requestHash':valid_hash(request_hash),'commandIndex':command_index})


def submit_action(store: Store, registry: dict, request_hash: str, selected_action_id: str):
    return _invoke(store, registry, {'schemaVersion':1, 'operation':'submit_action', 'requestHash':valid_hash(request_hash), 'selectedActionId':_id(selected_action_id)})


def request_capture(store: Store, registry: dict, request_hash: str, capture_index: int):
    return _invoke(store, registry, {'schemaVersion':1, 'operation':'request_capture', 'requestHash':valid_hash(request_hash), 'captureIndex':capture_index})


def inspect_action(store: Store, registry: dict, request_hash: str, selected_action_id: str):
    return _invoke(store, registry, {'schemaVersion':1, 'operation':'inspect_action', 'requestHash':valid_hash(request_hash), 'selectedActionId':_id(selected_action_id)})


def request_cleanup(store: Store, registry: dict, request_hash: str):
    """Request the already scoped owner reset once; never infer cleanup completion."""
    return _invoke(store, registry, {'schemaVersion':1, 'operation':'request_cleanup', 'requestHash':valid_hash(request_hash)})


def inspect_cleanup(store: Store, registry: dict, request_hash: str):
    return _invoke(store, registry, {'schemaVersion':1, 'operation':'inspect_cleanup', 'requestHash':valid_hash(request_hash)})


def watch_triggers(store: Store, registry: dict, request_hash: str):
    """Explicit foreground observation may publish only sealed trigger capture slots."""
    return _invoke(store, registry, {'schemaVersion':1, 'operation':'watch_triggers', 'requestHash':valid_hash(request_hash)})


def export_result(store: Store, registry: dict, request_hash: str, *, observation_ids=(), timeline_ids=(), visual_packet_hash=None):
    if any(not isinstance(rows, (tuple, list)) or len(rows) > 32 for rows in (observation_ids, timeline_ids)):
        raise ContractError('Explicit bounded observation lists required')
    return _invoke(store, registry, {'schemaVersion':1, 'operation':'export_result', 'requestHash':valid_hash(request_hash),
        'observationIds':list(observation_ids), 'timelineObservationIds':list(timeline_ids), 'visualPacketHash':visual_packet_hash})


def inspect_receipt(store: Store, receipt_hash: str, *, registry=None):
    """Validate a retained transport receipt without invoking the adapter."""
    record = decode_json(_read_bounded(store, receipt_hash, 128*1024), max_bytes=128*1024)
    if (not isinstance(record, dict) or set(record) != _RECEIPT_FIELDS
            or type(record['schema_version']) is not int or record['schema_version'] != 1
            or record['record_type'] != 'experiment_control_receipt' or record['runtime_attestation'] != 'NOT_ESTABLISHED'
            or record['can_replay'] is not False or type(record['timed_out']) is not bool or type(record['output_limited']) is not bool):
        raise ContractError('Invalid retained control receipt')
    valid_hash(record['registry_hash']); valid_hash(record['request_hash'])
    request = load_experiment(store, record['request_hash']); _command(record['command'], request)
    if record['command']['requestHash'] != record['request_hash'] or key_for(record) != receipt_hash:
        raise IntegrityError('Control receipt request mismatch')
    if registry is not None and record['registry_hash'] != key_for(registry):
        raise IntegrityError('Control receipt registry mismatch')
    response = record['reported']
    if response is not None:
        _response(response, record['command'])
        if record['status'] != response['status'] or record['timed_out'] or record['output_limited']:
            raise IntegrityError('Contradictory control receipt')
    elif record['status'] != 'OUTCOME_UNKNOWN':
        raise IntegrityError('Missing reported control outcome')
    # Even a VERIFIED cleanup only covers the owner's supported reset classes;
    # it cannot reconcile the wider experiment or clear earlier unsafe outcomes.
    # A stopped trigger watcher likewise proves no capture completion.
    uncertain = (record['command']['operation'] in ('request_cleanup', 'inspect_cleanup', 'watch_triggers','mob_pov','inspect_mob_pov')
                 or record['status'] in ('OUTCOME_UNKNOWN', 'PARTIAL_APPLY', 'REQUESTED', 'ALREADY_RECORDED', 'FAILED')
                 or response is not None and response.get('recordedStatus') in ('ACCEPTED', 'APPLIED'))
    return {'schema_version':1, 'receipt_hash':receipt_hash, 'request_hash':record['request_hash'],
        'registry_hash':record['registry_hash'], 'operation':record['command']['operation'], 'status':record['status'],
        'requires_reconciliation':uncertain, 'next_operation':_next(record['command'], record['status']),
        'runtime_attestation':'NOT_ESTABLISHED', 'can_replay':False}
