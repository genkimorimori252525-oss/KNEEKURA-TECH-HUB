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

from .storage import ContractError, valid_hash

IDENTITY_FIELDS = ('schema_version', 'run_id', 'session_epoch', 'profile_id', 'index_snapshot_id',
                   'build_artifact_hash', 'source_revision', 'dirty_hash', 'scenario_hash',
                   'assertion_hash', 'world_id', 'physical_side', 'logical_side', 'world_seed',
                   'world_template_hash', 'config_hash', 'adapter_id', 'adapter_version')
EVIDENCE_LEVEL = 'IMPORTED_REPORT_NOT_LIVE_ATTESTATION'


def _identity_errors(contract: dict, report: dict) -> list[str]:
    actual = report.get('identity', {})
    if not isinstance(actual, dict): return ['Report identity is not an object']
    errors = []
    for key in IDENTITY_FIELDS:
        value = contract.get(key)
        if value is None or value == '' or type(actual.get(key)) is not type(value) or actual.get(key) != value:
            errors.append(f'Identity missing/mismatch: {key}')
    if type(contract.get('schema_version')) is not int or contract['schema_version'] != 1:
        errors.append('Contract schema_version must be integer 1')
    for key in ('profile_id', 'index_snapshot_id', 'build_artifact_hash', 'dirty_hash',
                'scenario_hash', 'assertion_hash', 'world_template_hash', 'config_hash'):
        try: valid_hash(contract.get(key))
        except ContractError: errors.append(f'Unpinned identity: {key}')
    revision = contract.get('source_revision')
    if not isinstance(revision, str) or not re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})', revision):
        errors.append('Unpinned source_revision')
    for key in ('physical_side', 'logical_side'):
        if contract.get(key) not in ('client', 'server'): errors.append(f'Unresolved side: {key}')
    seed = contract.get('world_seed')
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        errors.append('world_seed must be an exact signed 64-bit integer')
    for key in ('run_id', 'session_epoch', 'world_id', 'adapter_id', 'adapter_version'):
        if not isinstance(contract.get(key), str) or not contract[key]:
            errors.append(f'Unresolved identity: {key}')
    return errors


def _result(contract: dict, outcome: str, reasons: list[str], *, status: str = 'OK', **extra) -> dict:
    return {'schema_version': 1, 'status': status, 'outcome': outcome, 'reasons': reasons,
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
    by_id = {t['id']: t for t in tests}
    missing = set(expected) - (detected & executed & set(ids))
    if missing:
        return _result(contract, 'NOT_RUN', ['Expected tests missing: ' + ', '.join(sorted(missing))])
    if any(by_id[k]['required'] != v for k, v in expected_required.items()):
        return _result(contract, 'BLOCKED', ['Required/optional mode changed for an expected test'], status='ERROR')
    failures = [by_id[t] for t in expected if by_id[t].get('status') != 'PASS']
    unrelated = [t for t in tests if t['id'] not in expected and t.get('status') == 'FAIL']
    reasons = ['Target tests failed/skipped/not run'] if failures else []
    if type(report.get('exit_code')) is not int:
        return _result(contract, 'BLOCKED', ['No completed process exit record'], status='ERROR')
    if report['exit_code'] != 0:
        # A failure outside the declared target set is preserved separately. An
        # otherwise unexplained process failure cannot become a clean success.
        if not unrelated and not failures:
            return _result(contract, 'BLOCKED', ['Unexplained nonzero runner exit'])
        reasons.append('Nonzero process exit is recorded separately from target assertion outcomes')
    return _result(contract, 'FAIL' if failures else 'PASS', reasons,
                   target_results=[by_id[t] for t in expected], unrelated_failures=unrelated,
                   process_exit_code=report['exit_code'], required_flags_compared=bool(expected_required))


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
    for name in ('server_tick', 'log_sequence'):
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
    valid = []; seen = set()
    for entity in entities:
        try:
            identity = (str(uuid.UUID(entity['uuid'])), entity['dimension'])
            if not isinstance(identity[1], str) or not identity[1] or identity in seen:
                raise ValueError('Duplicate/missing entity dimension identity')
            seen.add(identity)
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
    return _result(contract, 'NOT_RUN', errors, status='PARTIAL' if errors else 'OK',
                   atomic=False, results=valid,
                   observation_interval={k: observation.get(k) for k in ('server_tick_start', 'server_tick_end',
                       'client_frame_start', 'client_frame_end', 'log_sequence_start', 'log_sequence_end')},
                   note='A captured observation is not itself a behavioral assertion pass')


def evaluate_operation_receipt(contract: dict, receipt: dict) -> dict:
    errors = _identity_errors(contract, receipt)
    if errors: return _result(contract, 'UNKNOWN', errors, status='STALE', retry_allowed=False)
    if not receipt.get('request_id') or receipt.get('completed') is not True:
        return _result(contract, 'UNKNOWN', ['Acceptance is not completion; reconcile before any retry'], retry_allowed=False)
    outcome = receipt.get('outcome')
    if outcome not in ('PASS', 'FAIL'):
        return _result(contract, 'UNKNOWN', ['Final operation outcome unavailable'], retry_allowed=False)
    return _result(contract, outcome, [], retry_allowed=False)


def validation_plan(kind: str, registry: dict, *, world: str | None = None) -> dict:
    """Read a caller-supplied trusted registry; do not execute or change its budget."""
    tasks = {'compile': 'build', 'unit': 'test', 'gametest': 'runGameTestServer', 'client': 'runClient'}
    if kind not in tasks: raise ContractError('Unknown validation kind')
    result = {'schema_version': 1, 'status': 'OK', 'outcome': 'NOT_RUN', 'kind': kind,
              'argv': None, 'reasons': [], 'delegated_to': 'registered_existing_runner'}
    workspace = registry.get('workspace')
    if not isinstance(workspace, str) or not Path(workspace).is_dir():
        return dict(result, outcome='BLOCKED', reasons=['Registered workspace unavailable'])
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
