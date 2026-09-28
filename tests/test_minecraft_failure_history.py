"""History research is not a claim that a bug/fix was reproduced locally."""
import copy
import importlib
import pytest
from kneekura_tech_hub.minecraft.storage import Store, ContractError, capture_profile
from kneekura_tech_hub.minecraft.index import prepare_index
from test_minecraft_storage import manifest


def api():
    spec = importlib.util.find_spec('kneekura_tech_hub.minecraft.history')
    assert spec is not None, 'Failure/repair history record adapter is missing'
    return importlib.import_module(spec.name)


@pytest.fixture
def history(tmp_path):
    root = tmp_path/'src'; root.mkdir()
    (root/'issue.json').write_text('{"state":"closed","body":"reported double damage"}')
    (root/'fix.diff').write_text('- damage();\n+ if (server) damage();\n')
    store = Store(tmp_path/'cas'); profile = capture_profile(manifest(), tmp_path, store)
    snap = prepare_index(profile, store)['index_snapshot_id']
    documents = {d['path']:d['document_id'] for d in profile['documents']}
    evidence = [dict(id='issue', role='issue', index_snapshot_id=snap, document_id=documents['issue.json']),
                dict(id='fix', role='diff', index_snapshot_id=snap, document_id=documents['fix.diff'])]
    unknown = dict(basis='UNKNOWN', text=None, reason='Not established by available history', evidence_ids=[])
    case = dict(case_id='fixture-double-damage', origin='UPSTREAM', track='ANCHOR',
                environment={'minecraft':'1.20.1', 'loader':'forge', 'loader_version':'47.4.0'},
                affected_symbols=['demo/Mob#attack()V'],
                symptom=dict(basis='AUTHOR_CLAIM', text='Double damage reported', evidence_ids=['issue']),
                trigger_conditions=copy.deepcopy(unknown), root_cause=copy.deepcopy(unknown),
                repair=dict(basis='DIRECT_OBSERVATION', text='Diff adds a server-side guard', evidence_ids=['fix']),
                lesson=dict(basis='INFERENCE', text='Review logical-side ownership before changing damage', evidence_ids=['issue','fix']),
                causal_chain=[], before_revision=None, after_revision='b'*40,
                reproduction=dict(state='NOT_RUN', evidence_ids=[]),
                fix_verification=dict(state='REPORTED', evidence_ids=['issue']), evidence=evidence)
    record = dict(format='kneekura.failure-history.v1', repository='https://github.com/example/fixture',
                  scope={'track':'ANCHOR','head_revision':'b'*40,'history_window':'Selected fix only',
                         'queries':['reported double damage']},
                  coverage={'status':'PARTIAL','inspected_evidence_ids':['issue','fix'],
                            'deferred':['Older revisions'], 'unavailable':[]}, cases=[case])
    return store, record


def test_history_pins_original_evidence_without_inventing_root_cause(history):
    store, record = history; original = copy.deepcopy(record)
    result = api().capture_history(store, record)
    assert record == original and result['canonical_writes'] == 0
    saved = store.json(result['history_hash'])
    assert saved['record'] == original
    case = api().query_history(store, result['history_hash'], 'damage')['results'][0]
    assert case['root_cause']['basis'] == 'UNKNOWN'
    assert case['fix_verification']['state'] == 'REPORTED'
    assert case['evidence'][0]['locator']['content_hash'] in store.pinned_hashes()
    assert result['runtime_attestation'] is False


@pytest.mark.parametrize('state', ['VERIFIED_FIXED','PASS','REPRODUCED'])
def test_closed_issue_or_imported_bytes_cannot_become_live_verification(history, state):
    store, record = history; record['cases'][0]['fix_verification']['state'] = state
    with pytest.raises(ContractError): api().capture_history(store, record)


def test_experiment_claim_requires_experiment_evidence_not_merged_pr(history):
    store, record = history
    record['cases'][0]['fix_verification'] = {'state':'RECORDED_EXPERIMENT', 'evidence_ids':['issue']}
    with pytest.raises(ContractError): api().capture_history(store, record)


def test_guessed_cause_needs_its_own_evidence_and_inference_label(history):
    store, record = history
    record['cases'][0]['root_cause'] = dict(basis='INFERENCE', text='Likely side duplication', evidence_ids=[])
    with pytest.raises(ContractError): api().capture_history(store, record)


def test_unknown_needs_explicit_reason_and_no_positive_text(history):
    store, record = history; record['cases'][0]['root_cause']['text'] = 'Definitely a client bug'
    with pytest.raises(ContractError): api().capture_history(store, record)


def test_branch_is_not_a_stable_commit_revision(history):
    store, record = history; record['cases'][0]['after_revision'] = 'main'
    with pytest.raises(ContractError): api().capture_history(store, record)


def test_evidence_cannot_refer_to_an_invented_document(history):
    store, record = history; record['cases'][0]['evidence'][0]['document_id'] = 'f'*64
    with pytest.raises(ContractError): api().capture_history(store, record)


def test_partial_capture_stays_partial_without_hiding_the_other_evidence(history):
    store, record = history; h = api().capture_history(store, record)['history_hash']
    row = api().query_history(store, h, 'damage')['results'][0]
    store.blob_path(row['evidence'][0]['locator']['content_hash']).unlink()
    out = api().query_history(store, h, 'damage')
    assert out['status'] == 'PARTIAL' and out['results']
    assert out['results'][0]['unavailable_evidence_ids'] == ['issue']
    assert out['results'][0]['evidence'][1]['id'] == 'fix'


def test_track_and_environment_are_exact_filters_not_compatibility_predictions(history):
    store, record = history; h = api().capture_history(store, record)['history_hash']
    assert not api().query_history(store, h, 'damage', track='FRONTIER')['results']
    assert not api().query_history(store, h, 'damage', environment={'loader':'fabric'})['results']
    assert api().query_history(store, h, 'damage', environment={'loader':'forge'})['results']


def test_zero_cases_is_a_bounded_search_result_not_no_bugs_exist(history):
    store, record = history; record['cases'] = []
    record['coverage'] = dict(status='NOT_ANALYZED', inspected_evidence_ids=[], deferred=[], unavailable=[])
    out = api().capture_history(store, record)
    assert out['status'] == 'PARTIAL'
    assert api().query_history(store, out['history_hash'], 'anything')['no_match_meaning'] == 'NO_MATCH_IN_RECORDED_SCOPE'


def test_deferred_work_cannot_be_labelled_reviewed_scope(history):
    store, record = history; record['coverage']['status'] = 'REVIEWED_SCOPE'
    with pytest.raises(ContractError): api().capture_history(store, record)


def test_duplicate_ids_are_not_silently_merged(history):
    store, record = history; record['cases'].append(copy.deepcopy(record['cases'][0]))
    with pytest.raises(ContractError): api().capture_history(store, record)


def test_history_cli_round_trip_and_cursor_cannot_change_filters(history, tmp_path):
    import json
    import os
    import subprocess
    import sys
    store, record = history
    record['cases'].append(dict(copy.deepcopy(record['cases'][0]), case_id='second-case'))
    src = tmp_path/'record.json'; src.write_text(json.dumps(record))
    def cli(*args):
        env = dict(os.environ, PYTHONPATH='src')
        p = subprocess.run([sys.executable, '-m', 'kneekura_tech_hub.minecraft.history',
                            '--store', str(store.root), *args], capture_output=True, text=True, env=env)
        assert p.returncode == 0 and p.stdout.strip(), p.stderr
        return json.loads(p.stdout)
    result = cli('import', '--record', str(src))
    page = cli('query', '--history', result['history_hash'], '--query', 'damage', '--limit', '1')
    assert len(page['results']) == 1 and page['next_cursor']
    stale = api().query_history(store, result['history_hash'], 'damage', track='FRONTIER', cursor=page['next_cursor'])
    assert stale['status'] == 'STALE'


def test_missing_scope_evidence_cannot_produce_complete_search(history):
    store, record = history
    record['scope_evidence'] = [dict(record['cases'][0]['evidence'][0], id='inventory', role='search_inventory')]
    record['coverage'] = dict(status='REVIEWED_SCOPE', inspected_evidence_ids=['inventory'], deferred=[], unavailable=[])
    record['cases'] = []
    h = api().capture_history(store, record)['history_hash']
    saved = store.json(h)
    store.blob_path(saved['scope_evidence'][0]['locator']['content_hash']).unlink()
    out = api().query_history(store, h, 'anything')
    assert out['status'] == 'PARTIAL' and out['unavailable_scope_evidence_ids'] == ['inventory']
