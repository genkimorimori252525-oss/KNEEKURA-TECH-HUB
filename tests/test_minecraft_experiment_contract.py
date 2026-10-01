"""Offline experiment contract checks; fixtures are not runtime evidence."""
import copy
import importlib
import importlib.util
import uuid

import pytest

from kneekura_tech_hub.minecraft.storage import ContractError, key_for


def api():
    name = 'kneekura_tech_hub.minecraft.experiment_contract'
    assert importlib.util.find_spec(name) is not None, 'experiment contracts are not implemented'
    return importlib.import_module(name)


def request():
    return {
        'schema_version': 1, 'experiment_id': 'staff-repair-01', 'generation': 1,
        'target': {**{k: 'a' * 64 for k in ('profile_id', 'index_snapshot_id', 'build_artifact_hash',
                    'dirty_hash', 'config_hash', 'resource_hash')}, 'source_revision': 'b' * 40},
        'arena': {'arena_id': 'staff-arena', 'preset': 'normal', 'baseline_hash': 'c' * 64,
                  'bounds': {'min': [0, 60, 0], 'max': [16, 80, 16]}},
        'subjects': [{'subject_id': 'player', 'uuid': '00000000-0000-4000-8000-000000000001',
                      'entity_type': 'minecraft:player'}],
        'initial_state': [{'action_id': 'place', 'operation': 'teleport_subject',
                           'subject_id': 'player', 'position': [8, 64, 8], 'rotation': [0, 0]}],
        'actions': [{'action_id': 'use', 'operation': 'use_item', 'subject_id': 'player',
                     'hand': 'main_hand', 'ticks': 1},
                    {'action_id': 'settle', 'operation': 'wait_ticks', 'ticks': 2}],
        'observation_scopes': [{'kind': 'ENTITY_UUID', 'subject_id': 'player',
                                'lanes': ['ENTITY_STATE', 'ACTION_APPLIED'], 'level': 'L2'}],
        'visual_rig': {'mode': 'cardinal-4-snapshot-v1', 'fov': 60, 'viewport': [320, 320]},
        'assertions': [{'assertion_id': 'glow', 'kind': 'structured', 'subject_id': 'player',
                        'field': 'effect.minecraft:glowing', 'operator': 'equals', 'expected': True},
                       {'assertion_id': 'visible', 'kind': 'visual', 'subject_id': 'player',
                        'check': 'texture_present', 'expected': 'YES'}],
        'budgets': {'time_budget_ms': 30000, 'max_actions': 8, 'max_captures': 4},
    }


def result(req=None):
    req = req or request()
    evidence = [{'kind': kind, 'content_hash': h * 64, 'size_bytes': 12}
                for kind, h in [('structured', 'd'), ('raw_scene', 'e'), ('action_receipt', 'f')]]
    return {
        'schema_version': 1, 'experiment_id': req['experiment_id'], 'generation': req['generation'],
        'request_hash': key_for(req), 'run_snapshot_id': 'snapshot-01',
        'run_snapshot_content_hash': '1' * 64,
        'execution': {'status': 'COMPLETED',
                      'action_receipts': [{'action_id': a['action_id'], 'status': 'APPLIED',
                                           'evidence_hash': 'f' * 64}
                                          for a in req['initial_state'] + req['actions']],
                      'cleanup': 'CONFIRMED'},
        'observations': {'structured_summary': 'd' * 64, 'timeline_summary': None, 'visual_bundle': None},
        'assertions': [{'assertion_id': 'glow', 'status': 'PASS', 'evidence_hashes': ['d' * 64]},
                       {'assertion_id': 'visible', 'status': 'PASS', 'evidence_hashes': ['e' * 64]}],
        'gaps': [], 'evidence': evidence,
    }


def test_request_is_strict_detached_and_hash_binding_is_exact():
    req = request(); actual = api().validate_experiment_request(req)
    assert actual == req and actual is not req
    actual['actions'][0]['ticks'] = 2
    assert req['actions'][0]['ticks'] == 1
    b = api().experiment_binding(req)
    assert b == {'schema_version': 1, 'experiment_id': req['experiment_id'], 'generation': 1,
                 'request_hash': key_for(req), 'target': req['target'],
                 'arena_id': 'staff-arena', 'arena_baseline_hash': 'c' * 64,
                 'assertions_hash': key_for(req['assertions'])}


@pytest.mark.parametrize('key', list(request()) + ['path', 'command', 'executable', 'permission'])
def test_request_missing_or_extra_fields_rejected(key):
    value = request()
    if key in value: del value[key]
    else: value[key] = 'unsafe'
    with pytest.raises(ContractError): api().validate_experiment_request(value)


@pytest.mark.parametrize('value', [True, 1.0, '1', 0, None])
def test_version_and_generation_are_strict_integers(value):
    for field in ('schema_version', 'generation'):
        req = request(); req[field] = value
        with pytest.raises(ContractError): api().validate_experiment_request(req)


@pytest.mark.parametrize('field', list(request()['target']))
def test_every_target_identity_is_mandatory_and_valid(field):
    req = request(); req['target'][field] = 'HEAD'
    with pytest.raises(ContractError): api().validate_experiment_request(req)


@pytest.mark.parametrize('change', ['duplicate_action','duplicate_subject','duplicate_assertion',
                                   'unknown_subject','unknown_operation','extra_action_key',
                                   'out_of_arena','nan','overflow','budget','capture_budget',
                                   'unbounded_time','negative_ticks','boolean_ticks','unsafe_resource',
                                   'unsafe_assertion','extra_scope_key','unknown_lane','viewport'])
def test_malformed_or_unsafe_nested_request_is_rejected(change):
    req = request()
    if change == 'duplicate_action': req['actions'][0]['action_id'] = 'place'
    if change == 'duplicate_subject': req['subjects'].append(copy.deepcopy(req['subjects'][0]))
    if change == 'duplicate_assertion': req['assertions'].append(copy.deepcopy(req['assertions'][0]))
    if change == 'unknown_subject': req['actions'][0]['subject_id'] = 'someone_else'
    if change == 'unknown_operation': req['actions'][0]['operation'] = 'minecraft_command'
    if change == 'extra_action_key': req['actions'][0]['command'] = '/op someone'
    if change == 'out_of_arena': req['initial_state'][0]['position'] = [17, 64, 8]
    if change == 'nan': req['initial_state'][0]['position'][0] = float('nan')
    if change == 'overflow': req['initial_state'][0]['position'][0] = float('inf')
    if change == 'budget': req['budgets']['max_actions'] = 2
    if change == 'capture_budget': req['budgets']['max_captures'] = 3
    if change == 'unbounded_time': req['budgets']['time_budget_ms'] = 120001
    if change == 'negative_ticks': req['actions'][1]['ticks'] = -1
    if change == 'boolean_ticks': req['actions'][1]['ticks'] = True
    if change == 'unsafe_resource': req['subjects'][0]['entity_type'] = '../secret'
    if change == 'unsafe_assertion': req['assertions'][0]['field'] = '__proto__.command'
    if change == 'extra_scope_key': req['observation_scopes'][0]['query'] = '*'
    if change == 'unknown_lane': req['observation_scopes'][0]['lanes'] = ['EVERYTHING']
    if change == 'viewport': req['visual_rig']['viewport'] = [10000, 10000]
    with pytest.raises(ContractError): api().validate_experiment_request(req)


def test_set_block_is_integer_bounded_and_resource_only():
    req = request(); req['initial_state'] = [{'action_id': 'floor', 'operation': 'set_block',
        'position': [8, 63, 8], 'block': 'minecraft:stone'}]
    assert api().validate_experiment_request(req) == req
    req['initial_state'][0]['position'][0] = 8.5
    with pytest.raises(ContractError): api().validate_experiment_request(req)


def test_none_visual_rig_has_no_hidden_camera_parameters():
    req = request(); req['visual_rig'] = {'mode': 'none'}; req['budgets']['max_captures'] = 0
    req['assertions'] = req['assertions'][:1]
    assert api().validate_experiment_request(req) == req
    req['visual_rig']['fov'] = 60
    with pytest.raises(ContractError): api().validate_experiment_request(req)


def test_reported_result_consistency_does_not_assert_runtime_truth():
    assert api().validate_experiment_result(result(), request()) == result()


@pytest.mark.parametrize('field', ['experiment_id','generation','request_hash'])
def test_result_stale_or_unrelated_identity_rejected(field):
    value = result(); value[field] = 2 if field == 'generation' else 'x'
    with pytest.raises(ContractError): api().validate_experiment_result(value, request())


@pytest.mark.parametrize('change', ['unknown_action','missing_action','duplicate_action','unknown_assertion',
 'missing_assertion','duplicate_assertion','missing_evidence','wrong_plane','size_bool','duplicate_hash',
 'execution_unknown','cleanup_unknown','action_unknown','extra_authority','summary_not_in_inventory'])
def test_result_gaps_do_not_become_pass(change):
    value = result()
    if change == 'unknown_action': value['execution']['action_receipts'][0]['action_id'] = 'other'
    if change == 'missing_action': value['execution']['action_receipts'].pop()
    if change == 'duplicate_action': value['execution']['action_receipts'].append(value['execution']['action_receipts'][0])
    if change == 'unknown_assertion': value['assertions'][0]['assertion_id'] = 'other'
    if change == 'missing_assertion': value['assertions'].pop()
    if change == 'duplicate_assertion': value['assertions'].append(value['assertions'][0])
    if change == 'missing_evidence': value['assertions'][0]['evidence_hashes'] = ['0' * 64]
    if change == 'wrong_plane': value['assertions'][0]['evidence_hashes'] = ['e' * 64]
    if change == 'size_bool': value['evidence'][0]['size_bytes'] = True
    if change == 'duplicate_hash': value['evidence'].append(value['evidence'][0])
    if change == 'execution_unknown': value['execution']['status'] = 'UNKNOWN'
    if change == 'cleanup_unknown': value['execution']['cleanup'] = 'UNKNOWN'
    if change == 'action_unknown': value['execution']['action_receipts'][0]['status'] = 'UNKNOWN'
    if change == 'extra_authority': value['runtime_attestation'] = 'PASS'
    if change == 'summary_not_in_inventory': value['observations']['structured_summary'] = '0' * 64
    with pytest.raises(ContractError): api().validate_experiment_result(value, request())


@pytest.mark.parametrize('status', ['UNKNOWN','NOT_RUN','NOT_TRACKED','NOT_RENDERED','NOT_LOADED','INCONCLUSIVE'])
def test_nondefinitive_assertion_statuses_remain_distinct(status):
    value = result(); value['execution']['status'] = 'UNKNOWN'; value['execution']['cleanup'] = 'UNKNOWN'
    for row in value['assertions']: row.update(status=status, evidence_hashes=[])
    assert api().validate_experiment_result(value, request())['assertions'][0]['status'] == status


def test_generation_change_is_not_silently_ignored_in_comparison():
    before = request(); after = copy.deepcopy(before); after['generation'] = 2
    after['target']['build_artifact_hash'] = '9' * 64
    comparison = api().compare_requests(before, after, ['build_artifact_hash'])
    assert comparison['status'] == 'COMPARABLE'
    assert comparison['before_request_hash'] != comparison['after_request_hash']
    assert comparison['changed_target_fields'] == ['build_artifact_hash']
    assert comparison['verification'] == 'NOT_RUN'
    assert api().compare_requests(before, after, [])['status'] == 'NON_COMPARABLE'
    after['assertions'][0]['expected'] = False
    assert 'assertions' in api().compare_requests(before, after, ['build_artifact_hash'])['differences']


@pytest.mark.parametrize('field', ['arena','subjects','actions','initial_state','observation_scopes','visual_rig','budgets'])
def test_comparison_rejects_changed_setup(field):
    before = request(); after = copy.deepcopy(before)
    if field == 'arena': after[field]['baseline_hash'] = '9' * 64
    elif field == 'subjects': after[field][0]['uuid'] = str(uuid.uuid4())
    elif field == 'actions': after[field][1]['ticks'] = 3
    elif field == 'initial_state': after[field][0]['position'][0] = 9
    elif field == 'observation_scopes': after[field][0]['level'] = 'L1'
    elif field == 'visual_rig': after[field]['fov'] = 75
    elif field == 'budgets': after[field]['time_budget_ms'] = 31000
    assert api().compare_requests(before, after, [])['status'] == 'NON_COMPARABLE'


@pytest.mark.parametrize('path', [('actions',0,'subject_id'),('assertions',0,'subject_id'),
    ('assertions',1,'check'),('observations',),('evidence',0,'kind')])
def test_nonhashable_field_values_produce_contract_error(path):
    value = result() if path[0] in ('evidence','observations') else request()
    cursor = value
    for key in path[:-1]: cursor = cursor[key]
    cursor[path[-1]] = []
    with pytest.raises(ContractError):
        if path[0] in ('evidence','observations'): api().validate_experiment_result(value, request())
        else: api().validate_experiment_request(value)


def test_not_run_execution_cannot_hide_applied_action_receipts():
    response = result(); response['execution'].update(status='NOT_RUN', cleanup='NOT_RUN')
    for row in response['assertions']: row.update(status='NOT_RUN', evidence_hashes=[])
    with pytest.raises(ContractError): api().validate_experiment_result(response, request())
    for row in response['execution']['action_receipts']: row.update(status='NOT_RUN', evidence_hash=None)
    assert api().validate_experiment_result(response, request())['execution']['status'] == 'NOT_RUN'
