import copy
import importlib
import uuid

import pytest
from kneekura_tech_hub.minecraft.storage import key_for


def api(): return importlib.import_module('kneekura_tech_hub.minecraft.verification')


def contract():
    out = {'schema_version': 1, 'run_id': str(uuid.uuid4()), 'session_epoch': str(uuid.uuid4()),
            'profile_id': '1' * 64, 'index_snapshot_id': '2' * 64, 'build_artifact_hash': '3' * 64,
            'source_revision': 'a' * 40, 'dirty_hash': '4' * 64, 'scenario_hash': '5' * 64,
            'assertion_hash': '6' * 64, 'world_id': 'test-world', 'physical_side': 'server',
            'world_seed': 0, 'world_template_hash': '7' * 64, 'config_hash': '8' * 64,
            'adapter_id': 'test-fixture', 'adapter_version': '1.0.0',
            'logical_side': 'server', 'expected_tests': ['demo.attack'], 'assertion_domain': 'server_behavior'}
    out['assertion_hash'] = key_for({'assertion_domain': out['assertion_domain'],
                                    'expected_tests': out['expected_tests'], 'expected_required': {}})
    return out


def report(c):
    return {'identity': {k: v for k, v in c.items() if k not in ('expected_tests', 'assertion_domain')},
            'kind': 'gametest', 'completed': True, 'exit_code': 0, 'detected_test_ids': ['demo.attack'],
            'executed_test_ids': ['demo.attack'], 'detected_count': 1, 'executed_count': 1,
            'tests': [{'id': 'demo.attack', 'status': 'PASS', 'required': True}]}


def test_matching_report_passes_only_its_observed_scope():
    c = contract(); r = api().evaluate_tests(c, report(c))
    assert r['outcome'] == 'PASS'
    assert r['evidence_level'] == 'IMPORTED_REPORT_NOT_LIVE_ATTESTATION'
    assert r['assertion_domain'] == 'server_behavior'


@pytest.mark.parametrize('field', ['run_id', 'session_epoch', 'profile_id', 'build_artifact_hash', 'assertion_hash', 'dirty_hash', 'world_id', 'physical_side'])
def test_foreign_or_stale_report_never_passes(field):
    c = contract(); r = report(c); r['identity'][field] = 'other'
    out = api().evaluate_tests(c, r)
    assert out['status'] == 'STALE' and out['outcome'] == 'BLOCKED'


@pytest.mark.parametrize('mode', ['zero', 'missing', 'optional_failure', 'skipped', 'unfinished', 'duplicates', 'count_lie'])
def test_exit_zero_is_not_sufficient(mode):
    c = contract(); r = report(c)
    if mode == 'zero':
        r.update(tests=[], detected_test_ids=[], executed_test_ids=[], detected_count=0, executed_count=0)
    if mode == 'missing': r['tests'] = []
    if mode == 'optional_failure': r['tests'][0].update(required=False, status='FAIL')
    if mode == 'skipped': r['tests'][0]['status'] = 'SKIPPED'
    if mode == 'unfinished': r['completed'] = False
    if mode == 'duplicates': r['tests'].append(dict(r['tests'][0]))
    if mode == 'count_lie': r['executed_count'] = 15
    assert api().evaluate_tests(c, r)['outcome'] != 'PASS'


def test_unrelated_optional_failure_does_not_fail_target():
    c = contract(); r = report(c)
    r['tests'].append({'id': 'unrelated.render', 'status': 'FAIL', 'required': False})
    r['detected_test_ids'].append('unrelated.render'); r['executed_test_ids'].append('unrelated.render')
    r['detected_count'] = r['executed_count'] = 2
    out = api().evaluate_tests(c, r)
    assert out['outcome'] == 'PASS'
    assert out['unrelated_failures'][0]['id'] == 'unrelated.render'


def test_rendering_not_proven_by_gametest():
    c = contract(); c['assertion_domain'] = 'rendering'
    assert api().evaluate_tests(c, report(c))['outcome'] == 'NOT_RUN'


def test_missing_expected_tests_not_success():
    c = contract(); c['expected_tests'] = []
    assert api().evaluate_tests(c, report(c))['outcome'] == 'NOT_RUN'


def observation(c):
    return {'identity': report(c)['identity'], 'server_tick_start': 10, 'server_tick_end': 12,
            'log_sequence_start': 1, 'log_sequence_end': 5, 'client_frame_start': None, 'client_frame_end': None,
            'entities': [{'uuid': str(uuid.uuid4()), 'dimension': 'minecraft:overworld',
                          'position': [1.0, 2.0, 3.0], 'velocity': [0.0, 0.0, 0.0],
                          'health': 20.0, 'target_uuid': None}]}


def test_observation_uses_epoch_uuid_and_nonatomic_interval():
    c = contract(); o = observation(c); out = api().evaluate_observation(c, o)
    assert out['status'] == 'OK' and out['atomic'] is False
    assert out['results'][0]['uuid'] == o['entities'][0]['uuid']
    o['identity']['session_epoch'] = str(uuid.uuid4())
    assert api().evaluate_observation(c, o)['status'] == 'STALE'


@pytest.mark.parametrize('bad', ['id_only', 'nan', 'wrong_interval', 'missing_tick', 'bad_uuid'])
def test_malformed_observation_cannot_be_success(bad):
    c = contract(); o = observation(c)
    if bad == 'id_only': o['entities'][0] = {'entity_id': 7}
    if bad == 'nan': o['entities'][0]['position'][0] = float('nan')
    if bad == 'wrong_interval': o['server_tick_end'] = 1
    if bad == 'missing_tick': del o['server_tick_start']
    if bad == 'bad_uuid': o['entities'][0]['uuid'] = 'not-uuid'
    assert api().evaluate_observation(c, o)['status'] != 'OK'


def test_unknown_operation_completion_must_not_be_retried():
    c = contract(); receipt = {'identity': report(c)['identity'], 'request_id': 'summon-1',
                              'accepted': True, 'completed': False}
    r = api().evaluate_operation_receipt(c, receipt)
    assert r['outcome'] == 'UNKNOWN' and r['retry_allowed'] is False


def test_production_world_and_launch_budget_guard(tmp_path):
    workspace = tmp_path / 'work'; workspace.mkdir(); world = workspace / 'test-world'; world.mkdir()
    registry = {'workspace': str(workspace), 'test_worlds': [str(world)], 'remaining_launches': 1}
    out = api().validation_plan('gametest', registry, world=str(world))
    assert out['outcome'] == 'NOT_RUN' and out['argv'][-1] == 'runGameTestServer'
    assert api().validation_plan('gametest', registry, world=str(tmp_path / 'production'))['outcome'] == 'BLOCKED'
    registry['remaining_launches'] = 0
    assert api().validation_plan('gametest', registry, world=str(world))['outcome'] == 'BLOCKED'
    assert not (workspace / 'gradlew').exists()  # Plan did not write or execute a wrapper.


def test_requesting_run_without_runner_returns_unsupported(tmp_path):
    assert api().delegate_run({'outcome': 'NOT_RUN', 'argv': ['anything']})['status'] == 'UNSUPPORTED'


@pytest.mark.parametrize('field', ['config_hash', 'world_seed', 'world_template_hash', 'adapter_id', 'adapter_version'])
def test_same_build_with_different_world_or_adapter_is_not_same_run(field):
    c = contract(); r = report(c); r['identity'][field] = 'different'
    assert api().evaluate_tests(c, r)['outcome'] == 'BLOCKED'


@pytest.mark.parametrize('field,value', [('schema_version', True), ('build_artifact_hash', 'unknown'),
                                         ('profile_id', 'latest'), ('logical_side', 'both')])
def test_agreeing_but_malformed_identities_cannot_pass(field, value):
    c = contract(); c[field] = value
    assert api().evaluate_tests(c, report(c))['outcome'] == 'BLOCKED'


def test_report_requires_boolean_required_flag():
    c = contract(); r = report(c); del r['tests'][0]['required']
    assert api().evaluate_tests(c, r)['outcome'] == 'BLOCKED'


def test_expected_required_mode_cannot_silently_change():
    c = contract(); c['expected_required'] = {'demo.attack': True}
    r = report(c); r['tests'][0]['required'] = False
    assert api().evaluate_tests(c, r)['outcome'] == 'BLOCKED'


def test_overflowing_number_is_invalid_observation_not_a_crash():
    c = contract(); o = observation(c); o['entities'][0]['position'][0] = 10**400
    assert api().evaluate_observation(c, o)['status'] == 'PARTIAL'


@pytest.mark.parametrize('fault',['missing_target','required_mode','missing_exit'])
def test_valid_observed_count_survives_non_success_target_decisions(fault):
    c=contract();r=report(c)
    if fault=='missing_target': c['expected_tests']=['different.target']
    elif fault=='required_mode': c['expected_required']={'demo.attack':False}
    else: r['exit_code']=None
    result=api().evaluate_tests(c,r)
    assert result['outcome'] in ('NOT_RUN','BLOCKED')
    assert result['tests_executed']==1
