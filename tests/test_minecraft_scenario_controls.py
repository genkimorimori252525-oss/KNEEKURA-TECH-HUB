"""A23: known-bad controls gate a scenario without rewriting its target verdict."""
import base64
from copy import deepcopy
import hmac
import json
from pathlib import Path

import pytest

from kneekura_tech_hub.minecraft import contracts, execution, runtime, verification
from kneekura_tech_hub.minecraft.storage import ContractError, canonical, key_for
from kneekura_tech_hub.minecraft.workspace import workspace_fingerprint
from test_minecraft_contract import arranged
from test_minecraft_execution import local
from test_minecraft_index import class_profile
from test_minecraft_runtime import session
from test_minecraft_verification import contract, report


def controlled_report(status='FAIL'):
    c = contract()
    c['negative_controls'] = {'demo.weakened_helper': 'FAIL'}
    c['assertion_hash'] = key_for({'assertion_domain': c['assertion_domain'],
                                 'expected_tests': c['expected_tests'], 'expected_required': {},
                                 'negative_controls': c['negative_controls']})
    r = report(c)
    if status != 'MISSING':
        r['tests'].append({'id': 'demo.weakened_helper', 'status': status, 'required': False})
        r['detected_test_ids'].append('demo.weakened_helper')
        r['executed_test_ids'].append('demo.weakened_helper')
        r['detected_count'] = r['executed_count'] = 2
    return c, r


@pytest.mark.parametrize('fault', ['cleared', 'deleted', 'changed', 'target_changed'])
def test_captured_assertion_hash_prevents_removing_or_changing_controls(fault):
    c, r = controlled_report('PASS')
    if fault == 'cleared': c['negative_controls'] = {}
    if fault == 'deleted': del c['negative_controls']
    if fault == 'changed': c['negative_controls'] = {'other.control': 'FAIL'}
    if fault == 'target_changed': c['expected_required'] = {'demo.attack': False}
    result = verification.evaluate_scenario_tests(c, r)
    assert result['outcome'] == 'BLOCKED'
    assert result['assertion_binding'] == 'MISMATCH'


def test_genuine_legacy_contract_without_controls_preserves_target_only_semantics():
    c = contract()
    c['assertion_hash'] = key_for({'assertion_domain': c['assertion_domain'],
                                 'expected_tests': c['expected_tests'], 'expected_required': {}})
    assert verification.evaluate_scenario_tests(c, report(c))['outcome'] == 'PASS'


@pytest.mark.parametrize('control_status,expected', [
    ('FAIL', 'PASS'), ('PASS', 'FAIL'), ('SKIPPED', 'NOT_RUN'),
    ('NOT_RUN', 'NOT_RUN'), ('MISSING', 'NOT_RUN'),
])
def test_known_bad_control_is_required_for_scenario_acceptance(control_status, expected):
    c, r = controlled_report(control_status)
    assert verification.evaluate_tests(c, r)['outcome'] == 'PASS'
    result = verification.evaluate_scenario_tests(c, r)
    assert result['outcome'] == expected
    assert result['target_outcome'] == 'PASS'
    assert result['negative_control_outcome'] == expected
    assert result['tests_executed'] == r['executed_count']
    assert result['evidence_level'] == 'IMPORTED_REPORT_NOT_LIVE_ATTESTATION'


def test_known_bad_controls_do_not_change_unrelated_optional_semantics():
    c, r = controlled_report()
    r['tests'].append({'id': 'unrelated.other', 'status': 'FAIL', 'required': False})
    for key in ('detected_test_ids', 'executed_test_ids'):
        r[key].append('unrelated.other')
    r['detected_count'] = r['executed_count'] = 3
    out = verification.evaluate_scenario_tests(c, r)
    assert out['outcome'] == 'PASS'
    assert {t['id'] for t in out['unrelated_failures']} == {'demo.weakened_helper', 'unrelated.other'}
    assert [t['id'] for t in out['negative_control_results']] == ['demo.weakened_helper']


@pytest.mark.parametrize('fault', ['stale', 'duplicate', 'required', 'not_executed', 'incomplete'])
def test_negative_controls_never_bypass_report_validity(fault):
    c, r = controlled_report()
    if fault == 'stale': r['identity']['session_epoch'] = 'stale'
    if fault == 'duplicate': r['tests'].append(deepcopy(r['tests'][-1]))
    if fault == 'required': r['tests'][-1]['required'] = True
    if fault == 'not_executed':
        r['executed_test_ids'].remove('demo.weakened_helper'); r['executed_count'] = 1
    if fault == 'incomplete': r['completed'] = False
    assert verification.evaluate_scenario_tests(c, r)['outcome'] != 'PASS'


@pytest.mark.parametrize('controls', [None, [], {'': 'FAIL'}, {'demo.attack': 'FAIL'},
                                     {'negative': 'PASS'}, {'negative': True}])
def test_malformed_negative_expectations_are_rejected_before_contract_publication(session, controls):
    store, reg, idx, world, scenario = arranged(session)
    scenario['negative_controls'] = controls
    pins = store.pinned_hashes()
    with pytest.raises(ContractError, match='negative|Negative'):
        contracts.prepare_contract(store, reg, index_id=idx, world=world['world'], scenario=scenario)
    assert store.pinned_hashes() == pins


def test_negative_expectations_are_in_the_immutable_assertion_contract(session):
    store, reg, idx, world, scenario = arranged(session)
    scenario['negative_controls'] = {'demo.weakened_helper': 'FAIL'}
    out = contracts.prepare_contract(store, reg, index_id=idx, world=world['world'], scenario=scenario)
    c = out['contract']
    assert c['negative_controls'] == scenario['negative_controls']
    assert store.json(c['assertion_hash'])['negative_controls'] == scenario['negative_controls']
    scenario['negative_controls'] = {'demo.other_control': 'FAIL'}
    new = contracts.prepare_contract(store, reg, index_id=idx, world=world['world'], scenario=scenario)
    assert new['contract']['assertion_hash'] != c['assertion_hash']


def test_report_cli_cannot_accept_weakened_negative_control(tmp_path):
    from test_minecraft_cli import run_cli
    c, r = controlled_report('PASS')
    contract_path = tmp_path / 'contract.json'; contract_path.write_text(json.dumps(c))
    report_path = tmp_path / 'report.json'; report_path.write_text(json.dumps(r))
    process, result = run_cli(tmp_path / 'store', 'validate', 'report',
                              '--contract', str(contract_path), '--report', str(report_path))
    assert process.returncode != 0
    assert result['outcome'] == 'FAIL' and result['target_outcome'] == 'PASS'


def test_malformed_target_set_with_controls_is_blocked_without_exception():
    c, r = controlled_report()
    c['expected_tests'] = None
    assert verification.evaluate_scenario_tests(c, r)['outcome'] == 'BLOCKED'


@pytest.mark.parametrize('control_status,expected', [('FAIL', 'PASS'), ('PASS', 'FAIL'), ('MISSING', 'NOT_RUN')])
def test_registered_execution_uses_scenario_control_gate(local, monkeypatch, control_status, expected):
    store, reg, root = local
    template = root / 'control-template'; template.mkdir()
    reg['world_templates'] = [str(template)]
    world = execution.prepare_world(store, reg, template=str(template), request_id='control-world')
    c, r = controlled_report(control_status)
    c.update(dirty_hash=workspace_fingerprint(root), world_id=world['world_id'],
             world_template_hash=world['world_template_hash'])
    r['identity'] = dict(c)
    token = 'a' * 64
    def fixture_session(store, registry, actual, *, directory):
        return {'token': token, 'contract': actual, 'path': directory / 'session.json'}
    monkeypatch.setattr(runtime, 'create_session', fixture_session)
    def runner(*args, **kwargs):
        raw = canonical(r)
        envelope = {'payload_b64': base64.b64encode(raw).decode(),
                    'signature': hmac.digest(token.encode(), b'gametest-report\n' + raw, 'sha256').hex()}
        (Path(world['directory']) / 'gametest-report.json').write_bytes(canonical(envelope))
        return {'stdout': b'signed offline fixture; no game', 'completed': True, 'exit_code': 0}
    result = execution.execute(store, reg, kind='gametest', request_id='control-run',
                               world=world['world'], contract=c, runner=runner)
    assert result['outcome'] == expected
    assert result['gametest']['target_outcome'] == 'PASS'
