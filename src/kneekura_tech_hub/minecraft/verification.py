"""Pure, run-bound verification adapters; importing reports never starts a game.

Normalized reports must be produced by the registered local runner. Matching
identifiers prove consistency, not the honesty of an external producer. This
module intentionally does not claim a successful live Minecraft execution.
"""
from __future__ import annotations

import math
import os
import re
import uuid
from pathlib import Path
from typing import Callable

from .storage import ContractError, valid_hash, key_for

IDENTITY_FIELDS = ('schema_version', 'run_id', 'session_epoch', 'profile_id', 'index_snapshot_id',
                   'build_artifact_hash', 'source_revision', 'dirty_hash', 'scenario_hash',
                   'assertion_hash', 'world_id', 'physical_side', 'logical_side', 'world_seed',
                   'world_template_hash', 'config_hash', 'adapter_id', 'adapter_version')
EVIDENCE_LEVEL = 'IMPORTED_REPORT_NOT_LIVE_ATTESTATION'


V2_COMMON_FIELDS = ('schema_version', 'session_role', 'run_id', 'session_epoch', 'profile_id',
                    'index_snapshot_id', 'build_artifact_hash', 'source_revision', 'dirty_hash',
                    'scenario_hash', 'assertion_hash', 'config_hash', 'physical_side', 'logical_side',
                    'adapter_id', 'adapter_version', 'connection_policy_hash',
                    'runtime_scope', 'dependency_inventory_hash')
V2_ROLE_FIELDS = {
    'dedicated_server': ('world_id', 'world_template_hash', 'world_seed'),
    'dedicated_client': ('run_directory_id', 'run_directory_template_hash', 'server_contract_hash', 'player_uuid'),
}


INTEGRATED_FIELDS = IDENTITY_FIELDS + ('session_role', 'runtime_scope', 'dependency_inventory_hash', 'target_selection_hash')
INTEGRATED_FORBIDDEN = ('connection_policy', 'connection_policy_hash', 'server_contract', 'server_contract_hash',
                        'player_uuid', 'run_directory_id', 'run_directory_template_hash')


def identity_fields(contract: dict) -> tuple[str, ...]:
    """Select identity authority by exact schema/role; v1 remains unchanged."""
    if not isinstance(contract, dict) or type(contract.get('schema_version')) is not int:
        raise ContractError('Contract schema_version must be an integer')
    if contract['schema_version'] == 1:
        if any(k in contract for k in ('session_role', 'connection_policy_hash', 'runtime_scope', 'dependency_inventory_hash', 'target_selection_hash', *V2_ROLE_FIELDS['dedicated_client'])):
            raise ContractError('Dedicated role fields cannot use schema1 identity')
        return IDENTITY_FIELDS
    if contract['schema_version'] == 2 and isinstance(contract.get('session_role'), str) and contract['session_role'] in V2_ROLE_FIELDS:
        return V2_COMMON_FIELDS + V2_ROLE_FIELDS[contract['session_role']]
    if contract['schema_version'] == 3 and contract.get('session_role') == 'integrated_client':
        return INTEGRATED_FIELDS
    raise ContractError('Unsupported contract schema/role')


def _canonical_uuid(value):
    if not isinstance(value, str): raise ContractError('Canonical player UUID required')
    try: normalized = str(uuid.UUID(value))
    except ValueError: raise ContractError('Canonical player UUID required') from None
    if value != normalized: raise ContractError('Canonical player UUID required')
    return value


def validate_connection_policy(value: object) -> dict:
    if (not isinstance(value, dict) or set(value) != {'host', 'port', 'player_uuids'}
            or value['host'] != '127.0.0.1' or type(value['port']) is not int
            or not 1 <= value['port'] <= 65535 or not isinstance(value['player_uuids'], list)
            or not 1 <= len(value['player_uuids']) <= 2):
        raise ContractError('Explicit bounded literal-loopback connection policy required')
    players = [_canonical_uuid(player) for player in value['player_uuids']]
    if len(set(players)) != len(players): raise ContractError('Distinct selected player UUIDs required')
    return {'host': '127.0.0.1', 'port': value['port'], 'player_uuids': players}


def validate_connection(contract: dict, value: object) -> dict:
    role = contract.get('session_role')
    if type(contract.get('schema_version')) is not int or contract['schema_version'] != 2 or not isinstance(role, str) or role not in V2_ROLE_FIELDS:
        raise ContractError('Dedicated contract required for connection validation')
    policy = validate_connection_policy(contract.get('connection_policy'))
    if key_for(policy) != contract.get('connection_policy_hash'):
        raise ContractError('Connection policy differs from its captured hash')
    if (not isinstance(value, dict) or set(value) != {'player_uuid', 'connected', 'memory', 'channel_id', 'local', 'remote'}
            or value['connected'] is not True or value['memory'] is not False
            or not isinstance(value['channel_id'], str) or not 1 <= len(value['channel_id']) <= 256):
        raise ContractError('Current bounded non-memory player connection required')
    player = _canonical_uuid(value['player_uuid'])
    if player not in policy['player_uuids'] or role == 'dedicated_client' and player != contract.get('player_uuid'):
        raise ContractError('Connection belongs to an unselected player')
    endpoints = {}
    for key in ('local', 'remote'):
        endpoint = value[key]
        if (not isinstance(endpoint, dict) or set(endpoint) != {'host', 'port'}
                or endpoint['host'] != '127.0.0.1' or type(endpoint['port']) is not int
                or not 1 <= endpoint['port'] <= 65535):
            raise ContractError('Exact literal-loopback TCP endpoints required')
        endpoints[key] = dict(endpoint)
    server_end = 'remote' if role == 'dedicated_client' else 'local'
    if endpoints[server_end]['port'] != policy['port']:
        raise ContractError('Connection port differs from registered server policy')
    return dict(value, **endpoints)


def _identity_errors(contract: dict, report: dict) -> list[str]:
    actual = report.get('identity', {})
    if not isinstance(actual, dict): return ['Report identity is not an object']
    try: fields = identity_fields(contract)
    except ContractError as exc: return [str(exc)]
    errors = []
    for key in fields:
        value = contract.get(key)
        if value is None or value == '' or type(actual.get(key)) is not type(value) or actual.get(key) != value:
            errors.append(f'Identity missing/mismatch: {key}')
    v2 = contract['schema_version'] == 2
    integrated = contract['schema_version'] == 3
    role = contract.get('session_role')
    if integrated:
        if (contract.get('physical_side') != 'client' or contract.get('logical_side') != 'server'
                or contract.get('runtime_scope') != 'TARGET_CODE_AND_DEPENDENCY_BYTES'
                or any(k in contract or k in actual for k in INTEGRATED_FORBIDDEN)):
            errors.append('Invalid integrated-client scope or foreign dedicated authority')
    elif v2:
        if 'target_selection_hash' in contract or 'target_selection_hash' in actual:
            errors.append('Integrated target selection requires schema3')
        if contract.get('runtime_scope') != 'TARGET_CODE_AND_DEPENDENCY_BYTES':
            errors.append('Explicit target-code/dependency-byte runtime scope required')
        forbidden = V2_ROLE_FIELDS['dedicated_server' if role == 'dedicated_client' else 'dedicated_client']
        if any(key in contract or key in actual for key in forbidden):
            errors.append('Foreign role identity fields are forbidden')
        side = 'client' if role == 'dedicated_client' else 'server'
        if contract.get('physical_side') != side or contract.get('logical_side') != side:
            errors.append('Dedicated physical/logical side mismatch')
        if 'connection_policy' in contract:
            try:
                policy = validate_connection_policy(contract['connection_policy'])
                if key_for(policy) != contract.get('connection_policy_hash'):
                    errors.append('Connection policy hash mismatch')
                if role == 'dedicated_client' and contract.get('player_uuid') not in policy['player_uuids']:
                    errors.append('Client player is outside connection policy')
            except ContractError as exc: errors.append(str(exc))
    elif any(key in actual for key in ('session_role', 'connection_policy_hash', 'runtime_scope', 'dependency_inventory_hash', 'target_selection_hash', *V2_ROLE_FIELDS['dedicated_client'])):
        errors.append('Dedicated identity fields cannot be appended to schema1')
    hashes = ['profile_id', 'index_snapshot_id', 'build_artifact_hash', 'dirty_hash', 'scenario_hash', 'assertion_hash', 'config_hash']
    hashes += ['connection_policy_hash', 'dependency_inventory_hash'] if v2 else ['dependency_inventory_hash', 'target_selection_hash'] if integrated else []
    hashes += ['run_directory_template_hash', 'server_contract_hash'] if role == 'dedicated_client' else ['world_template_hash']
    for key in hashes:
        try: valid_hash(contract.get(key))
        except ContractError: errors.append(f'Unpinned identity: {key}')
    revision = contract.get('source_revision')
    if not isinstance(revision, str) or not re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})', revision):
        errors.append('Unpinned source_revision')
    for key in ('physical_side', 'logical_side'):
        if contract.get(key) not in ('client', 'server'): errors.append(f'Unresolved side: {key}')
    if role == 'dedicated_client':
        try: _canonical_uuid(contract.get('player_uuid'))
        except ContractError as exc: errors.append(str(exc))
    else:
        seed = contract.get('world_seed')
        if type(seed) is not int or not -(2**63) <= seed < 2**63:
            errors.append('world_seed must be an exact signed 64-bit integer')
    for key in ('run_id', 'session_epoch', 'adapter_id', 'adapter_version',
                'run_directory_id' if role == 'dedicated_client' else 'world_id'):
        if not isinstance(contract.get(key), str) or not contract[key]:
            errors.append(f'Unresolved identity: {key}')
    return errors


def _result(contract: dict, outcome: str, reasons: list[str], *, status: str = 'OK', **extra) -> dict:
    scope = ({'runtime_scope': contract.get('runtime_scope'),
              'dependency_inventory_hash': contract.get('dependency_inventory_hash'),
              'target_coverage': 'TARGET_CODE',
              'dependency_coverage': 'RESOLVED_BYTES_IDENTITY_ONLY',
              'loaded_class_attestation': 'NOT_ESTABLISHED_BY_IDENTITY'}
             if contract.get('schema_version') in (2,3) else {})
    if contract.get('schema_version') == 3: scope['target_selection_hash'] = contract.get('target_selection_hash')
    return {'schema_version': 1, 'status': status, 'outcome': outcome, 'reasons': reasons, **scope,
            'run_id': contract.get('run_id'), 'session_epoch': contract.get('session_epoch'),
            'profile_id': contract.get('profile_id'), 'index_snapshot_id': contract.get('index_snapshot_id'),
            'build_artifact_hash': contract.get('build_artifact_hash'),
            'assertion_domain': contract.get('assertion_domain'), 'evidence_level': EVIDENCE_LEVEL, **extra}


def evaluate_tests(contract: dict, report: dict) -> dict:
    """Check ID sets and per-test outcomes instead of trusting exit code alone."""
    errors = _identity_errors(contract, report)
    if errors: return _result(contract, 'BLOCKED', errors, status='STALE')
    if report.get('kind') != 'gametest':
        return _result(contract, 'NOT_RUN', ['This oracle accepts normalized GameTest reports only'], status='UNSUPPORTED')
    if contract.get('assertion_domain') != 'server_behavior':
        return _result(contract, 'NOT_RUN', ['GameTest does not establish rendering/client/network/performance assertions'])
    expected = contract.get('expected_tests')
    if not isinstance(expected, list) or not expected:
        return _result(contract, 'NOT_RUN', ['No explicit expected test set'])
    if (any(not isinstance(x, str) or not x for x in expected) or len(set(expected)) != len(expected)):
        return _result(contract, 'BLOCKED', ['Malformed/duplicate expected test IDs'], status='ERROR')
    if report.get('completed') is not True:
        return _result(contract, 'BLOCKED', ['Missing same-run completion; interruption/timeout is not success'])
    tests = report.get('tests', [])
    if not isinstance(tests, list) or any(not isinstance(t, dict) or not isinstance(t.get('id'), str) for t in tests):
        return _result(contract, 'BLOCKED', ['Malformed per-test report'], status='ERROR')
    if any(type(t.get('required')) is not bool or t.get('status') not in ('PASS', 'FAIL', 'SKIPPED', 'NOT_RUN') for t in tests):
        return _result(contract, 'BLOCKED', ['Every test needs a boolean required flag and a known status'], status='ERROR')
    expected_required = contract.get('expected_required', {})
    if (not isinstance(expected_required, dict) or any(k not in expected or type(v) is not bool for k, v in expected_required.items())):
        return _result(contract, 'BLOCKED', ['Malformed expected required/optional flags'], status='ERROR')
    ids = [t['id'] for t in tests]
    if len(set(ids)) != len(ids):
        return _result(contract, 'BLOCKED', ['Duplicate test results; ambiguous retry/attempt'], status='ERROR')
    for label in ('detected', 'executed'):
        listed = report.get(label + '_test_ids')
        count = report.get(label + '_count')
        if (not isinstance(listed, list) or any(not isinstance(x, str) for x in listed)
                or len(set(listed)) != len(listed) or type(count) is not int or count != len(listed)):
            return _result(contract, 'BLOCKED', [f'{label} IDs/count disagree'], status='ERROR')
    detected = set(report['detected_test_ids']); executed = set(report['executed_test_ids'])
    if not executed:
        return _result(contract, 'NOT_RUN', ['Zero tests executed'])
    if not executed <= detected or not set(ids) <= detected:
        return _result(contract, 'BLOCKED', ['Executed/reported test was not detected'], status='ERROR')
    def observed_result(outcome, reasons, **extra):
        # ID/count structure is validated above. Preserve this observation even
        # when target selection or exit metadata cannot establish acceptance.
        return _result(contract, outcome, reasons, tests_executed=report['executed_count'], **extra)

    by_id = {t['id']: t for t in tests}
    missing = set(expected) - (detected & executed & set(ids))
    if missing:
        return observed_result('NOT_RUN', ['Expected tests missing: ' + ', '.join(sorted(missing))])
    if any(by_id[k]['required'] != v for k, v in expected_required.items()):
        return observed_result('BLOCKED', ['Required/optional mode changed for an expected test'], status='ERROR')
    failures = [by_id[t] for t in expected if by_id[t].get('status') != 'PASS']
    unrelated = [t for t in tests if t['id'] not in expected and t.get('status') == 'FAIL']
    reasons = ['Target tests failed/skipped/not run'] if failures else []
    if type(report.get('exit_code')) is not int:
        return observed_result('BLOCKED', ['No completed process exit record'], status='ERROR')
    if report['exit_code'] != 0:
        # A failure outside the declared target set is preserved separately. An
        # otherwise unexplained process failure cannot become a clean success.
        if not unrelated and not failures:
            return observed_result('BLOCKED', ['Unexplained nonzero runner exit'])
        reasons.append('Nonzero process exit is recorded separately from target assertion outcomes')
    return observed_result('FAIL' if failures else 'PASS', reasons,
                   target_results=[by_id[t] for t in expected], unrelated_failures=unrelated,
                   process_exit_code=report['exit_code'], required_flags_compared=bool(expected_required))


def validate_negative_controls(value: object, expected: list[str]) -> dict:
    """Fixed known-bad tests are optional GameTests expected to fail, not targets."""
    if (not isinstance(expected, list) or not isinstance(value, dict) or len(value) > 1000
            or any(not isinstance(k, str) or not 1 <= len(k) <= 256
                   or k in expected or v != 'FAIL' for k, v in value.items())):
        raise ContractError('Negative controls must name distinct non-target tests expected to FAIL')
    return dict(value)


def evaluate_scenario_tests(contract: dict, report: dict) -> dict:
    """Gate declared controls separately while retaining the target-only A22 verdict."""
    target = evaluate_tests(contract, report)
    assertions = {'assertion_domain': contract.get('assertion_domain'),
                  'expected_tests': contract.get('expected_tests'),
                  'expected_required': contract.get('expected_required', {})}
    if 'negative_controls' in contract:
        assertions['negative_controls'] = contract['negative_controls']
    if key_for(assertions) != contract.get('assertion_hash'):
        return dict(target, outcome='BLOCKED', status='ERROR', target_outcome=target['outcome'],
                    assertion_binding='MISMATCH', negative_control_outcome='NOT_RUN',
                    negative_control_results=[],
                    reasons=[*target['reasons'], 'Assertions differ from the captured assertion hash'])
    target = dict(target, assertion_binding='MATCH')
    try:
        controls = validate_negative_controls(contract.get('negative_controls', {}),
                                              contract.get('expected_tests', []))
    except ContractError as exc:
        return dict(target, outcome='BLOCKED', status='ERROR', target_outcome=target['outcome'],
                    negative_control_outcome='BLOCKED', negative_control_results=[],
                    reasons=[*target['reasons'], str(exc)])
    if not controls:
        return target
    out = dict(target, target_outcome=target['outcome'], negative_control_outcome='NOT_RUN',
               negative_control_results=[])
    # Only consume controls after the existing oracle has validated identity,
    # completion, report shape/counts, selected IDs, modes and process metadata.
    if 'target_results' not in target:
        return out
    by_id = {row['id']: row for row in report['tests']}
    executed = set(report['executed_test_ids'])
    reasons = []
    control_outcomes = []
    for name, expected in controls.items():
        row = by_id.get(name)
        actual = row['status'] if row else 'MISSING'
        result = {'id': name, 'expected': expected, 'observed': actual}
        if row is None or name not in executed or actual in ('SKIPPED', 'NOT_RUN'):
            verdict = 'NOT_RUN'
            reasons.append('Negative control was not executed: ' + name)
        elif row['required'] is not False:
            verdict = 'BLOCKED'
            reasons.append('Negative control must remain optional: ' + name)
        elif actual != expected:
            verdict = 'FAIL'
            reasons.append('Known-bad control unexpectedly passed: ' + name)
        else:
            verdict = 'PASS'
        result['outcome'] = verdict
        out['negative_control_results'].append(result)
        control_outcomes.append(verdict)
    priority = {'PASS': 0, 'NOT_RUN': 1, 'FAIL': 2, 'BLOCKED': 3}
    control_outcome = max(control_outcomes, key=priority.__getitem__)
    out.update(negative_control_outcome=control_outcome,
               outcome=max((target['outcome'], control_outcome), key=priority.__getitem__),
               reasons=[*target['reasons'], *reasons])
    if control_outcome == 'BLOCKED': out['status'] = 'ERROR'
    elif control_outcome == 'NOT_RUN': out['status'] = 'PARTIAL'
    return out


def _finite_number(value) -> bool:
    if type(value) not in (int, float): return False
    try: return math.isfinite(value)
    except OverflowError: return False


def _finite_vector(value) -> bool:
    return (isinstance(value, list) and len(value) == 3
            and all(_finite_number(x) for x in value))


def evaluate_observation(contract: dict, observation: dict) -> dict:
    errors = _identity_errors(contract, observation)
    if errors: return _result(contract, 'BLOCKED', errors, status='STALE', atomic=False, results=[])
    receiver = contract.get('session_role') == 'dedicated_client'
    dedicated = contract.get('schema_version') == 2
    required_intervals = ('client_tick', 'client_frame', 'log_sequence') if receiver else ('server_tick', 'log_sequence')
    if receiver and (observation.get('observation_side') != 'logical_client'
                     or observation.get('server_tick_start') is not None
                     or observation.get('server_tick_end') is not None
                     or observation.get('server_tick_scope') != 'NOT_LOCALLY_OBSERVED'):
        errors.append('Receiving client cannot claim local server ticks or a server-side observation')
    for name in required_intervals:
        start, end = observation.get(name + '_start'), observation.get(name + '_end')
        if type(start) is not int or type(end) is not int or start < 0 or end < start:
            errors.append(f'Missing/invalid {name} interval')
    fs, fe = observation.get('client_frame_start'), observation.get('client_frame_end')
    if fs is not None or fe is not None:
        if type(fs) is not int or type(fe) is not int or fs < 0 or fe < fs:
            errors.append('Invalid client frame interval')
    if contract.get('assertion_domain') == 'rendering' and (fs is None or contract.get('physical_side') != 'client'):
        errors.append('No client rendering observation')
    entities = observation.get('entities')
    if not isinstance(entities, list): entities = []; errors.append('Entity list missing')
    if receiver and len(entities) != 1: errors.append('Exactly one selected local player is required')
    top_connection = None
    if receiver:
        try: top_connection = validate_connection(contract, observation.get('connection'))
        except ContractError as exc: errors.append(str(exc))
    valid = []; seen = set()
    for entity in entities:
        try:
            identity = (str(uuid.UUID(entity['uuid'])), entity['dimension'])
            if not isinstance(identity[1], str) or not identity[1] or identity in seen:
                raise ValueError('Duplicate/missing entity dimension identity')
            seen.add(identity)
            if dedicated:
                connected = validate_connection(contract, entity.get('connection'))
                if connected['player_uuid'] != identity[0]: raise ValueError('Selected entity/connection UUID mismatch')
                if receiver and (identity[0] != contract['player_uuid'] or connected != top_connection):
                    raise ValueError('Receiving-client player or connection changed')
            if not _finite_vector(entity.get('position')) or not _finite_vector(entity.get('velocity')):
                raise ValueError('Entity position/velocity missing or nonfinite')
            health = entity.get('health')
            if not (health is None and entity.get('health_applicable') is False) and not _finite_number(health):
                raise ValueError('Entity health missing or nonfinite')
            if 'target_uuid' not in entity: raise ValueError('Target field missing (use null for no target)')
            if entity['target_uuid'] is not None: uuid.UUID(entity['target_uuid'])
            valid.append(entity)
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            errors.append(f'Invalid entity observation: {exc}')
    extra = {'observation_side': 'logical_client', 'server_tick_scope': 'NOT_LOCALLY_OBSERVED'} if receiver else {}
    return _result(contract, 'NOT_RUN', errors, status='PARTIAL' if errors else 'OK',
                   atomic=False, results=valid, **extra,
                   observation_interval={k: observation.get(k) for k in ('server_tick_start', 'server_tick_end',
                       'client_frame_start', 'client_frame_end', 'log_sequence_start', 'log_sequence_end',
                       *(['client_tick_start', 'client_tick_end'] if receiver else []))},
                   note='A captured observation is not itself a behavioral assertion pass')


def evaluate_operation_receipt(contract: dict, receipt: dict, *,
                               expected_request_id: str | None = None,
                               expected_command_id: str | None = None) -> dict:
    """A completed command is a command result, never a behavior-test assertion."""
    errors = _identity_errors(contract, receipt)
    if errors:
        return _result(contract, 'UNKNOWN', errors, status='STALE', retry_allowed=False,
                       assertion_domain='command_execution')
    request_id = receipt.get('request_id')
    if (not isinstance(request_id, str) or not request_id or receipt.get('completed') is not True
            or ('accepted' in receipt and receipt['accepted'] is not True)):
        errors.append('Acceptance is not completion; reconcile before any retry')
    if expected_request_id is not None and request_id != expected_request_id:
        errors.append('Receipt belongs to a different requested operation')
    if expected_command_id is not None and receipt.get('command_id') != expected_command_id:
        errors.append('Receipt belongs to a different registered command')
    outcome = receipt.get('outcome')
    if outcome not in ('PASS', 'FAIL'):
        errors.append('Final operation outcome unavailable')
    if 'success' in receipt and (type(receipt['success']) is not bool
                                 or receipt['success'] != (outcome == 'PASS')):
        errors.append('Success flag contradicts the explicit final outcome')
    return _result(contract, 'UNKNOWN' if errors else outcome, errors, retry_allowed=False,
                   assertion_domain='command_execution')


def validation_plan(kind: str, registry: dict, *, world: str | None = None, run_directory: str | None = None) -> dict:
    """Read a caller-supplied trusted registry; do not execute or change its budget."""
    tasks = {'compile': 'build', 'unit': 'test', 'gametest': 'runGameTestServer', 'client': 'runClient', 'server': 'runServer'}
    if kind not in tasks: raise ContractError('Unknown validation kind')
    result = {'schema_version': 1, 'status': 'OK', 'outcome': 'NOT_RUN', 'kind': kind,
              'argv': None, 'reasons': [], 'delegated_to': 'registered_existing_runner'}
    workspace = registry.get('workspace')
    if not isinstance(workspace, str) or not Path(workspace).is_dir():
        return dict(result, outcome='BLOCKED', reasons=['Registered workspace unavailable'])
    if (kind in ('gametest', 'client', 'server') and registry.get('runtime_role') is not None
            or kind == 'server' or run_directory is not None):
        from .runtime import dedicated_registry
        from .execution import _registry, _owned_world, _owned_client_directory
        try:
            role, _ = dedicated_registry(registry)
            root, _ = _registry(registry, kind)
            if type(registry.get('remaining_launches')) is not int or registry['remaining_launches'] < 1:
                raise ContractError('No remaining explicitly permitted game launches')
            if kind == 'server' and role == 'dedicated_server' and run_directory is None:
                _owned_world(root, world, layout='server')
            elif kind == 'client' and role == 'integrated_client' and run_directory is None:
                _owned_world(root, world, layout='client')
            elif kind == 'client' and role == 'dedicated_client' and world is None:
                _owned_client_directory(root, run_directory)
            else: raise ContractError('Dedicated role/owned path differs from launch kind')
        except (ContractError, OSError) as exc:
            return dict(result, outcome='BLOCKED', reasons=[str(exc)])
        wrapper = str(root / ('gradlew.bat' if os.name == 'nt' else 'gradlew'))
        return dict(result, argv=[wrapper, tasks[kind]], workspace=str(root), world=world, run_directory=run_directory)
    if kind in ('gametest', 'client'):
        allowed = registry.get('test_worlds', [])
        budget = registry.get('remaining_launches')
        if type(budget) is not int or budget <= 0:
            return dict(result, outcome='BLOCKED', reasons=['No remaining explicitly permitted game launches'])
        if not isinstance(world, str) or not world or not Path(world).is_dir() or Path(world).is_symlink():
            return dict(result, outcome='BLOCKED', reasons=['Registered test world unavailable'])
        if str(Path(world).resolve()) not in {str(Path(x).resolve()) for x in allowed}:
            return dict(result, outcome='BLOCKED', reasons=['World is not a registered test world'])
    wrapper = str(Path(workspace).resolve() / ('gradlew.bat' if os.name == 'nt' else 'gradlew'))
    result.update(argv=[wrapper, tasks[kind]], workspace=str(Path(workspace).resolve()), world=world)
    return result


def delegate_run(plan: dict, runner: Callable[[dict], dict] | None = None) -> dict:
    """An embedding host may supply its existing permission-aware runner adapter."""
    if plan.get('outcome') == 'BLOCKED': return plan
    if runner is None:
        return {'schema_version': 1, 'status': 'UNSUPPORTED', 'outcome': 'NOT_RUN',
                'reasons': ['No registered runner adapter attached; nothing was executed']}
    return runner(plan)
