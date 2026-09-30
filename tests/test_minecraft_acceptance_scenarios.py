"""Offline acceptance-input checks, never live MOD/client acceptance results.

These regressions fail if fixture inputs drift off their pinned upstream tree,
the client scenario weakens an assertion, or a control becomes a passing oracle.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import pytest

from kneekura_tech_hub.minecraft import input_contract, verification
from kneekura_tech_hub.minecraft.__main__ import parser
from test_minecraft_verification import contract, report
from test_minecraft_input_contract import case, dispatch, mutations
from test_minecraft_index import class_profile
from test_minecraft_runtime import session


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'departments/minecraft/mod-ai/acceptance'
SCENARIOS = ROOT / 'tools/ci/mod_ai_staff/scenarios'


def load(path):
    assert path.is_file(), f'Acceptance fixture has not been authored: {path.name}'
    return json.loads(path.read_text())


def test_real_mod_tasks_cover_all_six_without_claiming_execution():
    data = load(FIXTURES / 'real-mod-tasks.json')
    assert [t['id'] for t in data['tasks']] == [f'U{i:02}' for i in range(1, 7)]
    for task in data['tasks']:
        assert task['execution_status'] == 'NOT_RUN'
        assert task['inputs'] and task['steps'] and task['assertions'] and task['blocked_on']
        assert task['target_profile'] == dict(minecraft='1.20.1', loader='forge',
                                             loader_version='47.4.6', java_major=17, track='ANCHOR')
        assert task['profile_id'] is None and task['index_snapshot_id'] is None
        assert task['null_reasons']['profile_id'] and task['null_reasons']['index_snapshot_id']


def test_twilight_inputs_are_exact_pinned_existing_mod_files():
    data = load(FIXTURES / 'real-mod-tasks.json')
    inventory = load(ROOT / 'departments/minecraft/mods/twilight-forest/inventory/anchor-a7dd8f13-files.json')
    entries = {row['path']: row for row in inventory['entries']}
    for task in data['tasks'][:5]:
        assert task['source']['commit'] == inventory['source_commit']
        assert task['source']['binary_sha256'] == '0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778'
        for item in task['inputs']:
            assert item['git_blob_sha1'] == entries[item['path']]['sha']
            assert item['representation_stage'] == 'original_source'
            assert item['descriptor'] is None  # Never guess a descriptor from a filename.
            assert item['descriptor_status'] == 'RESOLVE_FROM_CAPTURED_BYTECODE_IF_REQUIRED'
            assert item['url'] == f"https://github.com/TeamTwilight/twilightforest/blob/{inventory['source_commit']}/{item['path']}"


def test_connector_unknowns_and_frontier_negative_are_preserved():
    task = load(FIXTURES / 'real-mod-tasks.json')['tasks'][5]
    assert task['source']['record_kind'] == 'DESIGN_REFERENCE_NOT_SOURCE_SNAPSHOT'
    assert task['source']['binary_sha256'] is None
    assert task['compatibility_verdict'] == 'UNKNOWN'
    assert task['candidate_fabric_mod'] is None
    assert task['required_dependency_inputs'] == ['Connector', 'Forgified Fabric API', 'candidate Fabric MOD', 'exact mappings']
    assert task['frontier_is_anchor_evidence'] is False
    assert not any(item.get('git_blob_sha1') for item in task['inputs'])


def test_all_research_commands_are_existing_read_only_cli_routes():
    data = load(FIXTURES / 'real-mod-tasks.json')
    for task in data['tasks']:
        for step in task['steps']:
            if 'argv' not in step:
                assert step['kind'] in {'prerequisite', 'review', 'runtime_checkpoint'}
                continue
            args = parser().parse_args(step['argv'])
            assert args.command in {'profile', 'search', 'inspect', 'relations', 'interventions', 'context'}
            if args.command == 'profile':
                assert args.action == 'inspect'
            assert '{index_snapshot_id}' in step['argv']


def test_every_adversarial_case_has_fault_oracle_and_existing_regression():
    data = load(FIXTURES / 'adversarial-cases.json')
    assert [c['id'] for c in data['cases']] == [f'A{i:02}' for i in range(1, 25)]
    for case in data['cases']:
        assert case['input_fault'] and case['oracle'] and case['regression_nodes']
        assert case['real_mod_execution'] == 'NOT_RUN'
        for node in case['regression_nodes']:
            path, name = node.split('::')
            assert re.search(r'^def ' + re.escape(name) + r'\(', (ROOT / path).read_text(), re.M)
    assert data['new_runtime_launches_authorized'] == 0


def test_server_scenario_uses_real_staff_tests_and_fixed_negatives():
    scenario = load(SCENARIOS / 'server-behavior.json')
    fixed = load(ROOT / 'tools/ci/mod_ai_staff/assertions.json')
    assert scenario['assertion_domain'] == 'server_behavior'
    assert scenario['expected_tests'] == [fixed['handler_test'], fixed['expiry_test']]
    assert scenario['expected_required'] == {test: True for test in scenario['expected_tests']}
    assert scenario['negative_controls'] == fixed['negative_controls']
    assert scenario['fixed_assertions_sha256'] == hashlib.sha256((ROOT / scenario['fixed_assertions_file']).read_bytes()).hexdigest()
    source = (ROOT / 'tools/ci/mod_ai_staff/java/org/kneekura/staff/StaffGameTests.java').read_text()
    for name in scenario['expected_tests'] + list(scenario['negative_controls']):
        assert f'void {name}(GameTestHelper helper)' in source


def test_fixed_client_scenario_cannot_claim_gametest_or_dispatch_as_live_success():
    scenario = load(SCENARIOS / 'client-observation.json')
    assert scenario['assertion_domain'] == 'client_observation'
    assert scenario['expected_tests'] == [] and scenario['expected_required'] == {}
    assert scenario['execution_status'] == 'NOT_RUN'
    assert set(scenario['verdicts']) == {'physical_right_click', 'server_behavior', 'visual', 'synchronization', 'runtime_client_handler_mutation'}
    assert set(scenario['verdicts'].values()) == {'NOT_RUN'}
    assert scenario['exact_tick_evidence'] == 'server-behavior.json:staff_expiry'
    assert scenario['launch_policy']['new_launches_authorized'] == 0
    assert scenario['launch_policy']['use_only_existing_registered_budget'] is True
    assert scenario['input']['control'] == 'mouse:right'
    assert 1 <= scenario['input']['hold_ms'] <= 250
    assert scenario['input']['retry_unknown'] is False
    assert scenario['required_views'] == ['inventory', 'first_person', 'third_person']
    assert scenario['view_change_authority'] == 'operator_checkpoint'
    assert scenario['observation_query']['staff_state'] is True
    assert len(scenario['observation_query']['entity_uuids']) == 1
    assert scenario['observation_query']['limit'] == 1
    assert scenario['fixed_assertions_sha256'] == hashlib.sha256((ROOT / scenario['fixed_assertions_file']).read_bytes()).hexdigest()
    for key in ('cli_bind', 'cli_dispatch'):
        args = parser().parse_args(scenario['input'][key])
        assert args.command == 'input'
    c = contract(); c.update(assertion_domain=scenario['assertion_domain'], expected_tests=[])
    assert verification.evaluate_tests(c, report(c))['outcome'] == 'NOT_RUN'


def test_client_cycle_preserves_required_stages_and_no_success_state_injection():
    scenario = load(SCENARIOS / 'client-observation.json')
    assert scenario['cycle'] == ['investigate', 'edit_assets', 'build', 'interact', 'observe', 'repair']
    assert {a['id'] for a in scenario['assertions']} == {
        'native_input', 'self_glow', 'repeat_no_refresh', 'cooldown', 'no_damage',
        'no_consumption_or_wear', 'inventory_view', 'first_person_view', 'third_person_view',
        'dedicated_synchronization', 'client_no_mutation'}
    commands = scenario['command_registry_template']
    assert set(commands) == {'equip_staff'}
    assert 'effect ' not in commands['equip_staff'] and 'data merge' not in commands['equip_staff']
    assert 'minecraft:glowing' not in commands['equip_staff']
    assert scenario['history']['api'] == 'kneekura_tech_hub.minecraft.history.capture_history'
    assert scenario['history']['before_and_after_evidence_required'] is True


@pytest.mark.parametrize('fault', ['missing_expected', 'zero_tests', 'required_flag', 'stale_epoch', 'target_failed'])
def test_predeclared_report_controls_reject_false_success(fault):
    scenarios = load(SCENARIOS / 'client-controls.json')
    case = next(c for c in scenarios['report_controls'] if c['id'] == fault)
    server = load(SCENARIOS / 'server-behavior.json')
    c = contract(); c.update({key: server[key] for key in ('assertion_domain', 'expected_tests', 'expected_required')})
    r = report(c)
    r['tests'] = [{'id': name, 'status': 'PASS', 'required': True} for name in c['expected_tests']]
    r.update(detected_test_ids=list(c['expected_tests']), executed_test_ids=list(c['expected_tests']), detected_count=2, executed_count=2)
    if fault == 'missing_expected':
        r['tests'].pop(); r['executed_test_ids'].pop(); r['executed_count'] = 1
    elif fault == 'zero_tests':
        r.update(tests=[], detected_test_ids=[], executed_test_ids=[], detected_count=0, executed_count=0)
    elif fault == 'required_flag': r['tests'][0]['required'] = False
    elif fault == 'stale_epoch': r['identity']['session_epoch'] = '00000000-0000-4000-8000-000000000001'
    else: r['tests'][0]['status'] = 'FAIL'
    out = verification.evaluate_tests(c, r)
    assert out['outcome'] == case['expected_outcome']


def test_known_bad_optional_results_remain_visible_separately_from_target():
    server = load(SCENARIOS / 'server-behavior.json')
    c = contract(); c.update({key: server[key] for key in ('assertion_domain', 'expected_tests', 'expected_required')})
    r = report(c)
    r['tests'] = [{'id': name, 'status': 'PASS', 'required': True} for name in c['expected_tests']]
    r['tests'] += [{'id': name, 'status': status, 'required': False} for name, status in server['negative_controls'].items()]
    r.update(detected_test_ids=[t['id'] for t in r['tests']], executed_test_ids=[t['id'] for t in r['tests']], detected_count=5, executed_count=5)
    out = verification.evaluate_tests(c, r)
    assert out['outcome'] == 'PASS'
    assert {t['id'] for t in out['unrelated_failures']} == set(server['negative_controls'])
    assert out['evidence_level'] == 'IMPORTED_REPORT_NOT_LIVE_ATTESTATION'


def test_fixture_publication_contains_no_private_receipts_or_credentials():
    paths = list(FIXTURES.glob('*.json')) + list(SCENARIOS.glob('*.json'))
    assert paths
    for path in paths:
        text = path.read_text()
        for private in ('/workspace/', '/home/', '/Users/', 'payload_b64', 'receipt_objects', 'Bearer ', 'session_token'):
            assert private not in text


@pytest.mark.parametrize('fault', ['wrong_focus', 'wrong_epoch', 'outside_viewport', 'press_unknown', 'release_unknown'])
def test_predeclared_input_controls_preserve_no_retry_and_release(case, fault):
    control = next(c for c in load(SCENARIOS / 'client-controls.json')['input_controls'] if c['id'] == fault)
    scenario = load(SCENARIOS / 'client-observation.json')
    c, request, clock, backend = case
    request.update(control=scenario['input']['control'], hold_ms=scenario['input']['hold_ms'])
    if fault == 'wrong_focus': backend.state['foreground'] = False
    elif fault == 'wrong_epoch': backend.state['identity']['session_epoch'] = 'restarted'
    elif fault == 'outside_viewport': request['position'] = backend.state['client_size']
    elif fault == 'press_unknown': backend.press_error = OSError('Completion is unknown')
    else: backend.release_error = OSError('Release is unknown')
    result = dispatch(case)
    assert result['outcome'] == control['expected_outcome']
    assert sum(row[0] == 'press' for row in mutations(backend)) == control['expected_presses']
    assert result['retry_allowed'] is False
    assert result['verification']['actual_right_click'] == 'NOT_RUN'
    if control['expected_presses']:
        assert result['release_attempted'] is True
        assert sum(row[0] == 'release' for row in mutations(backend)) == 1


@pytest.mark.parametrize('name,side,layout', [('server-behavior.json', 'server', 'server'),
                                            ('client-observation.json', 'client', 'client')])
def test_scenario_is_captured_by_existing_contract_without_launch(session, name, side, layout):
    from kneekura_tech_hub.minecraft import contracts, execution, index
    from kneekura_tech_hub.minecraft.storage import capture_profile, key_for
    store, old_contract, registry, _ = session
    scenario = load(SCENARIOS / name)
    snapshot = index._load(store, old_contract['index_snapshot_id'])
    manifest = deepcopy(snapshot['profile']['manifest'])
    manifest['physical_side'] = side
    root = Path(registry['workspace'])
    profile = capture_profile(manifest, root, store)
    current = index.prepare_index(profile, store)['index_snapshot_id']
    template = root / 'world-template'; template.mkdir()
    registry['world_templates'] = [str(template)]
    world = execution.prepare_world(store, registry, template=str(template), request_id='scenario-contract', layout=layout)
    result = contracts.prepare_contract(store, registry, index_id=current, world=world['world'], scenario=scenario)
    assert result['outcome'] == 'NOT_RUN'
    c = result['contract']
    assert c['physical_side'] == side
    assert c['scenario_hash'] == key_for(scenario)
    assert store.json(c['scenario_hash']) == scenario
    assert c['expected_tests'] == scenario['expected_tests']
    assert c['expected_required'] == scenario['expected_required']
    assert not list(root.rglob('endpoint.json')) and not list(root.rglob('eula.txt'))
