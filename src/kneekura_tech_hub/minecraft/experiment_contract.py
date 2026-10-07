"""Strict, inert X0 experiment contracts. Validation is not runtime attestation.

Requests carry bounded intent, never executable paths, shell commands or launch
permission. Result consistency does not establish that reported facts occurred.
The LAB execution authority and its immutable evidence remain separate.
"""
from __future__ import annotations

import math
from functools import wraps
import re
import uuid

from .asset_contract import decode_json
from .storage import ContractError, canonical, key_for, valid_hash

TARGET_FIELDS = frozenset(('profile_id', 'index_snapshot_id', 'build_artifact_hash',
                          'source_revision', 'dirty_hash', 'config_hash', 'resource_hash'))
_REQUEST_FIELDS = {'schema_version', 'experiment_id', 'generation', 'target', 'arena',
                   'subjects', 'initial_state', 'actions', 'observation_scopes',
                   'visual_rig', 'assertions', 'budgets'}
_RESULT_FIELDS = {'schema_version', 'experiment_id', 'generation', 'request_hash',
                  'run_snapshot_id', 'run_snapshot_content_hash', 'execution',
                  'observations', 'assertions', 'gaps', 'evidence'}
LANES = frozenset(('SERVER_TICK', 'CLIENT_TICK', 'TARGET_TRACKED', 'ENTITY_STATE',
    'SERVER_TARGET_TRACKED', 'SERVER_ENTITY_STATE', 'AI_TARGET', 'BRAIN_MEMORY',
    'RUNNING_BEHAVIORS', 'BEHAVIOR_TRANSITION', 'NAVIGATION', 'PACKET_SEND',
    'PACKET_RECEIVE', 'PACKET_HANDLER', 'RENDER_ENTERED', 'YSM_ENTERED',
    'YSM_COMPLETED', 'ACTION_APPLIED', 'OBSERVATION_WRITTEN'))
UNRESOLVED = frozenset(('UNKNOWN', 'NOT_RUN', 'NOT_TRACKED', 'NOT_RENDERED',
                        'NOT_LOADED', 'INCONCLUSIVE'))
EVIDENCE_KINDS = frozenset(('structured', 'timeline', 'raw_scene', 'human_composite',
    'derived_visual', 'visual_bundle', 'action_receipt', 'cleanup_receipt', 'finding'))
VISUAL_CHECKS = frozenset(('feet_below_ground', 'mesh_clipping', 'texture_present',
    'wrong_facing', 'displaced_part', 'projectile_obstacle_side', 'subject_visible'))


def _contract_boundary(operation):
    @wraps(operation)
    def checked(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except (TypeError, KeyError, AttributeError, OverflowError) as exc:
            raise ContractError('Malformed experiment field type') from exc
    return checked


def _require(condition, label):
    if not condition:
        raise ContractError(label)


def _keys(value, fields, label):
    _require(isinstance(value, dict) and set(value) == set(fields), f'Invalid {label} fields')


def _detach(value, limit=1024 * 1024):
    try:
        return decode_json(canonical(value), max_bytes=limit)
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ContractError('Experiment data must be bounded finite JSON') from exc


def _integer(value, lo, hi, label):
    _require(type(value) is int and lo <= value <= hi, f'Invalid {label}')


def _id(value, label='identifier'):
    _require(isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}', value),
             f'Invalid {label}')
    return value


def _resource(value):
    _require(isinstance(value, str) and len(value) <= 128 and
             re.fullmatch(r'[a-z0-9_]+:[a-z0-9_./-]+', value) and
             all(p not in ('', '.', '..') for p in value.split(':')[1].split('/')), 'Invalid resource ID')


def _vector(value, count, lo, hi, label):
    _require(isinstance(value, list) and len(value) == count and
             all(type(n) in (int, float) and math.isfinite(n) and lo <= n <= hi for n in value),
             f'Invalid {label}')


def _list(value, maximum, label, minimum=0):
    _require(isinstance(value, list) and minimum <= len(value) <= maximum, f'Invalid {label}')


def _unique_ids(rows, field, label):
    ids = [_id(row.get(field), label) if isinstance(row, dict) else _id(None, label) for row in rows]
    _require(len(set(ids)) == len(ids), f'Duplicate {label}')
    return set(ids)


@_contract_boundary
def validate_target(value):
    """Exact material identity, independent of any current runtime claim."""
    _keys(value, TARGET_FIELDS, 'target')
    for field in TARGET_FIELDS - {'source_revision'}:
        valid_hash(value[field])
    _require(isinstance(value['source_revision'], str) and
             re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', value['source_revision']), 'Exact source revision required')
    return _detach(value)


def _position(value, bounds, *, block=False):
    _vector(value, 3, -30000000, 30000000, 'position')
    _require(all(bounds['min'][i] <= n < bounds['max'][i] for i, n in enumerate(value)),
             'Action is outside declared Arena bounds')
    if block:
        _require(all(type(n) is int for n in value), 'Block coordinates must be integers')


def _action(value, subjects, bounds):
    _require(isinstance(value, dict), 'Action must be an object')
    operation = value.get('operation')
    fields = {'action_id', 'operation'}
    if operation == 'wait_ticks':
        _keys(value, fields | {'ticks'}, 'wait_ticks')
        _integer(value['ticks'], 1, 1200, 'wait ticks')
    elif operation == 'teleport_subject':
        _keys(value, fields | {'subject_id', 'position', 'rotation'}, 'teleport_subject')
        _require(value['subject_id'] in subjects, 'Unknown action subject')
        _position(value['position'], bounds)
        _vector(value['rotation'], 2, -180, 180, 'rotation')
        _require(-90 <= value['rotation'][1] <= 90, 'Invalid pitch')
    elif operation == 'use_item':
        _keys(value, fields | {'subject_id', 'hand', 'ticks'}, 'use_item')
        _require(value['subject_id'] in subjects and value['hand'] in ('main_hand', 'off_hand'), 'Invalid item-use subject/hand')
        _integer(value['ticks'], 1, 20, 'item-use ticks')
    elif operation == 'set_block':
        _keys(value, fields | {'position', 'block'}, 'set_block')
        _position(value['position'], bounds, block=True)
        _resource(value['block'])
    else:
        raise ContractError('Unsupported typed experiment action')


def _assertion(value, subjects, visual):
    _require(isinstance(value, dict), 'Assertion must be an object')
    base = {'assertion_id', 'kind', 'subject_id', 'expected'}
    _require(value.get('subject_id') in subjects, 'Unknown assertion subject')
    if value.get('kind') == 'visual':
        _keys(value, base | {'check'}, 'visual assertion')
        _require(visual and value['check'] in VISUAL_CHECKS and value['expected'] in ('YES', 'NO'),
                 'Unsupported visual check')
    elif value.get('kind') == 'structured':
        _keys(value, base | {'field', 'operator'}, 'structured assertion')
        field = value['field']
        _require(isinstance(field, str) and (field in ('health', 'alive', 'target_uuid', 'position', 'velocity', 'collision')
                 or field.startswith('effect.')), 'Unsupported structured field')
        if field.startswith('effect.'):
            _resource(field[len('effect.'):])
        _require(value['operator'] in ('equals', 'less_than', 'greater_than'), 'Unsupported assertion operator')
        expected = value['expected']
        if field in ('alive', 'collision') or field.startswith('effect.'):
            _require(type(expected) is bool and value['operator'] == 'equals', 'Boolean assertion must use equals')
        elif field in ('position', 'velocity'):
            _vector(expected, 3, -30000000, 30000000, 'expected vector')
            _require(value['operator'] == 'equals', 'Vector assertion must use equals')
        elif field == 'target_uuid':
            _uuid(expected)
            _require(value['operator'] == 'equals', 'Identity assertion must use equals')
        else:
            _require(type(expected) in (int, float) and math.isfinite(expected) and 0 <= expected <= 1024,
                     'Invalid expected health')
    else:
        raise ContractError('Unsupported assertion kind')


def _uuid(value):
    try:
        _require(isinstance(value, str) and str(uuid.UUID(value)) == value, 'Canonical UUID required')
    except (ValueError, AttributeError, TypeError) as exc:
        raise ContractError('Canonical UUID required') from exc


@_contract_boundary
def validate_experiment_request(value: dict) -> dict:
    """Pure whole-request validation; all text fields are finite enum/ID data."""
    r = _detach(value, 128 * 1024)
    _keys(r, _REQUEST_FIELDS, 'ExperimentRequest')
    _integer(r['schema_version'], 1, 1, 'schema version')
    _integer(r['generation'], 1, 1000000, 'experiment generation')
    _id(r['experiment_id'], 'experiment ID')
    validate_target(r['target'])
    arena = r['arena']
    _keys(arena, {'arena_id', 'preset', 'baseline_hash', 'bounds'}, 'Arena')
    _id(arena['arena_id']); _id(arena['preset']); valid_hash(arena['baseline_hash'])
    bounds = arena['bounds']; _keys(bounds, {'min', 'max'}, 'Arena bounds')
    for field in ('min', 'max'):
        _vector(bounds[field], 3, -30000000, 30000000, 'Arena bounds')
        _require(all(type(n) is int for n in bounds[field]), 'Integer Arena bounds required')
    _require(all(0 < bounds['max'][i] - bounds['min'][i] <= 64 for i in range(3)), 'Arena maximum edge is 64 blocks')
    _require(-64 <= bounds['min'][1] < bounds['max'][1] <= 320, 'Arena height is outside Forge 1.20.1 limits')
    _list(r['subjects'], 16, 'subjects', 1)
    subjects = _unique_ids(r['subjects'], 'subject_id', 'subject ID')
    uuids = []
    for row in r['subjects']:
        _keys(row, {'subject_id', 'uuid', 'entity_type'}, 'subject')
        _uuid(row['uuid']); _resource(row['entity_type']); uuids.append(row['uuid'])
    _require(len(set(uuids)) == len(uuids), 'Duplicate subject UUID')
    for field in ('initial_state', 'actions'):
        _list(r[field], 32, field)
    actions = r['initial_state'] + r['actions']
    _require(len(actions) <= 32, 'At most 32 total actions')
    _unique_ids(actions, 'action_id', 'action ID')
    for action in actions:
        _action(action, subjects, bounds)
    _list(r['observation_scopes'], 16, 'observation scopes', 1)
    scope_ids = set()
    for scope in r['observation_scopes']:
        _keys(scope, {'kind', 'subject_id', 'lanes', 'level'}, 'observation scope')
        _require(scope['kind'] == 'ENTITY_UUID' and scope['subject_id'] in subjects and
                 scope['level'] in ('L0', 'L1', 'L2', 'L3', 'L4'), 'Unsupported observation scope')
        _list(scope['lanes'], 16, 'observation lanes', 1)
        _require(all(isinstance(x, str) and x in LANES for x in scope['lanes']) and
                 len(set(scope['lanes'])) == len(scope['lanes']), 'Invalid observation lanes')
        identity = (scope['subject_id'], scope['level'])
        _require(identity not in scope_ids, 'Duplicate observation scope'); scope_ids.add(identity)
    rig = r['visual_rig']; _require(isinstance(rig, dict), 'Visual rig must be an object')
    visual = rig.get('mode') == 'cardinal-4-snapshot-v1'
    mob_pov = rig.get('mode') == 'mob-eye-live-v1'
    if visual or mob_pov:
        _keys(rig, {'mode', 'fov', 'viewport'}, 'visual rig')
        _require(type(rig['fov']) in (int, float) and math.isfinite(rig['fov']) and 30 <= rig['fov'] <= 100,
                 'Visual FOV must be 30..100 degrees')
        _vector(rig['viewport'], 2, 64, 2048, 'viewport')
        _require(all(type(n) is int for n in rig['viewport']), 'Integer viewport required')
    else:
        _keys(rig, {'mode'}, 'visual rig')
        _require(rig['mode'] == 'none', 'Unsupported visual rig')
    _list(r['assertions'], 32, 'assertions', 1)
    _unique_ids(r['assertions'], 'assertion_id', 'assertion ID')
    for assertion in r['assertions']:
        _assertion(assertion, subjects, visual)
    budgets = r['budgets']; _keys(budgets, {'time_budget_ms', 'max_actions', 'max_captures'}, 'budgets')
    _integer(budgets['time_budget_ms'], 1, 120000, 'time budget')
    _integer(budgets['max_actions'], 0, 32, 'action budget')
    _integer(budgets['max_captures'], 0, 16, 'capture budget')
    _require(len(actions) <= budgets['max_actions'], 'Actions exceed declared budget')
    _require((visual and budgets['max_captures'] >= 4) or mob_pov or
             (not visual and budgets['max_captures'] == 0),
             'Visual capture budget does not match rig')
    _require(sum(action.get('ticks', 0) for action in actions) * 50 <= budgets['time_budget_ms'],
             'Declared tick actions exceed the wall-time budget')
    return r


def experiment_binding(request: dict) -> dict:
    r = validate_experiment_request(request)
    return {'schema_version': 1, 'experiment_id': r['experiment_id'], 'generation': r['generation'],
            'request_hash': key_for(r), 'target': r['target'], 'arena_id': r['arena']['arena_id'],
            'arena_baseline_hash': r['arena']['baseline_hash'], 'assertions_hash': key_for(r['assertions'])}


@_contract_boundary
def validate_experiment_result(value: dict, request: dict) -> dict:
    """Validate a reported result without promoting it to authenticated evidence."""
    req = validate_experiment_request(request)
    r = _detach(value)
    _keys(r, _RESULT_FIELDS, 'ExperimentResult')
    _integer(r['schema_version'], 1, 1, 'result schema version')
    _integer(r['generation'], 1, 1000000, 'result generation')
    _require((r['experiment_id'], r['generation'], r['request_hash']) ==
             (req['experiment_id'], req['generation'], key_for(req)), 'Result request identity mismatch')
    _id(r['run_snapshot_id']); valid_hash(r['run_snapshot_content_hash'])
    _list(r['evidence'], 128, 'result evidence')
    evidence = {}
    total_bytes = 0
    for row in r['evidence']:
        _keys(row, {'kind', 'content_hash', 'size_bytes'}, 'evidence')
        _require(isinstance(row['kind'], str) and row['kind'] in EVIDENCE_KINDS, 'Unknown evidence kind')
        h = valid_hash(row['content_hash'])
        _require(h not in evidence, 'Duplicate evidence hash')
        _integer(row['size_bytes'], 1, 16 * 1024 * 1024, 'evidence size')
        total_bytes += row['size_bytes']; evidence[h] = row
    _require(total_bytes <= 64 * 1024 * 1024, 'Result evidence exceeds 64 MiB')
    execution = r['execution']
    _keys(execution, {'status', 'action_receipts', 'cleanup'}, 'execution')
    _require(execution['status'] in ('COMPLETED', 'PARTIAL', 'FAILED', 'UNKNOWN', 'NOT_RUN'), 'Invalid execution status')
    _require(execution['cleanup'] in ('CONFIRMED', 'FAILED', 'UNKNOWN', 'NOT_RUN'), 'Invalid cleanup status')
    actions = req['initial_state'] + req['actions']
    _list(execution['action_receipts'], 32, 'action receipts')
    ids = _unique_ids(execution['action_receipts'], 'action_id', 'action receipt ID')
    _require(ids == {a['action_id'] for a in actions}, 'Action receipt coverage mismatch')
    _require([a['action_id'] for a in execution['action_receipts']] == [a['action_id'] for a in actions],
             'Action receipt order mismatch')
    all_applied = True
    for row in execution['action_receipts']:
        _keys(row, {'action_id', 'status', 'evidence_hash'}, 'action receipt')
        _require(row['status'] in ('APPLIED', 'REJECTED', 'UNKNOWN', 'NOT_RUN'), 'Invalid action completion')
        all_applied &= row['status'] == 'APPLIED'
        if row['evidence_hash'] is not None:
            h = valid_hash(row['evidence_hash'])
            _require(h in evidence and evidence[h]['kind'] == 'action_receipt', 'Action evidence unavailable')
        else:
            _require(row['status'] in ('UNKNOWN', 'NOT_RUN'), 'Applied/rejected action requires evidence')
    _require(execution['status'] != 'COMPLETED' or all_applied, 'Completed execution has unapplied actions')
    if execution['status'] == 'NOT_RUN':
        _require(execution['cleanup'] == 'NOT_RUN' and all(row['status'] == 'NOT_RUN'
                 for row in execution['action_receipts']), 'NOT_RUN execution contains applied/uncertain work')
    _keys(r['observations'], {'structured_summary', 'timeline_summary', 'visual_bundle'}, 'observations')
    for field, kind in [('structured_summary', 'structured'), ('timeline_summary', 'timeline'),
                        ('visual_bundle', 'visual_bundle')]:
        h = r['observations'][field]
        if h is not None:
            valid_hash(h)
            _require(h in evidence and evidence[h]['kind'] == kind, 'Summary evidence unavailable or wrong plane')
    _list(r['assertions'], 32, 'assertion results')
    assertions = {a['assertion_id']: a for a in req['assertions']}
    _require(_unique_ids(r['assertions'], 'assertion_id', 'assertion result ID') == set(assertions),
             'Assertion coverage mismatch')
    definitive_allowed = execution['status'] == 'COMPLETED' and all_applied and execution['cleanup'] == 'CONFIRMED'
    for row in r['assertions']:
        _keys(row, {'assertion_id', 'status', 'evidence_hashes'}, 'assertion result')
        status = row['status']
        _require(isinstance(status, str) and status in UNRESOLVED | {'PASS', 'FAIL'}, 'Invalid assertion status')
        _list(row['evidence_hashes'], 16, 'assertion evidence')
        refs = [valid_hash(h) for h in row['evidence_hashes']]
        _require(len(set(refs)) == len(refs) and set(refs) <= set(evidence), 'Assertion evidence unavailable')
        if status in ('PASS', 'FAIL'):
            _require(definitive_allowed and bool(refs), 'Uncertain execution/cleanup cannot establish behavior result')
            kinds = {'structured', 'timeline'} if assertions[row['assertion_id']]['kind'] == 'structured' else {'raw_scene', 'visual_bundle'}
            _require(any(evidence[h]['kind'] in kinds for h in refs), 'Assertion lacks its evidence plane')
    _list(r['gaps'], 64, 'gaps')
    for gap in r['gaps']:
        _keys(gap, {'code', 'assertion_id'}, 'gap')
        _require(gap['code'] in ('MISSING', 'STALE', 'UNAVAILABLE', 'PARTIAL', 'UNKNOWN',
                                'NOT_TRACKED', 'NOT_RENDERED', 'NOT_LOADED', 'PERTURBED'), 'Unknown gap code')
        _require(gap['assertion_id'] is None or gap['assertion_id'] in assertions, 'Unknown gap assertion')
        for assertion in r['assertions']:
            if gap['assertion_id'] in (None, assertion['assertion_id']):
                _require(assertion['status'] not in ('PASS', 'FAIL'), 'Unresolved gap conflicts with definitive assertion')
    return r


@_contract_boundary
def compare_requests(before: dict, after: dict, changed_target_fields: list[str]) -> dict:
    """Compare declared repair semantics; different generations are explicit lineage.

    Exact declared target changes are permitted, never silently ignored. Matching
    request setup alone is not evidence that actual cameras or runtime matched.
    """
    left, right = validate_experiment_request(before), validate_experiment_request(after)
    _list(changed_target_fields, len(TARGET_FIELDS), 'declared target changes')
    _require(all(isinstance(f, str) and f in TARGET_FIELDS for f in changed_target_fields) and
             len(set(changed_target_fields)) == len(changed_target_fields), 'Invalid target change allowlist')
    actual = sorted(k for k in TARGET_FIELDS if left['target'][k] != right['target'][k])
    differences = sorted(k for k in _REQUEST_FIELDS - {'generation', 'target'} if left[k] != right[k])
    if actual != sorted(changed_target_fields):
        differences.append('target_change_allowlist')
    if key_for(left) != key_for(right) and right['generation'] <= left['generation']:
        differences.append('generation_lineage')
    return {'status': 'COMPARABLE' if not differences else 'NON_COMPARABLE',
            'before_request_hash': key_for(left), 'after_request_hash': key_for(right),
            'before_generation': left['generation'], 'after_generation': right['generation'],
            'changed_target_fields': actual, 'differences': differences,
            'comparison_domain': 'declared_experiment_semantics', 'verification': 'NOT_RUN'}
