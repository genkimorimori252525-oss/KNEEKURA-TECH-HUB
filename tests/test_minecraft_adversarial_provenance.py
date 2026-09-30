"""Bounded offline A06/A07/A14/A20 regressions using the existing adapters.

The Java variants are tiny test-owned inputs, not a real Forge/Mixin transform.
Faults are injected at filesystem calls; no disk exhaustion, evidence deletion,
garbage collection, game launch, or live synchronization is performed.
"""
from copy import deepcopy
import errno
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

import pytest

from kneekura_tech_hub.minecraft import index, storage, verification
from test_minecraft_storage import manifest
from test_minecraft_verification import contract, observation


@pytest.fixture(scope='module')
def distinct_java_inputs(tmp_path_factory):
    javac, javap = shutil.which('javac'), shutil.which('javap')
    if not javac or not javap:
        pytest.skip('Installed JDK compiler and javap required; no tools are downloaded')
    base = tmp_path_factory.mktemp('adversarial-provenance-java')
    original_source = (
        'package proof; public class StageExample {\n'
        ' public static int value() { return 7; }\n'
        ' private static int target() { return value(); }\n'
        ' public static int attack() { return target(); }\n'
        '}\n'
    )
    changed_source = original_source.replace('return 7;', 'return 23;').replace(
        'return target();', 'int ignored = target(); return target();')
    jars = {}
    for label, text in [('original', original_source), ('changed', changed_source)]:
        directory = base / label
        source = directory / 'proof/StageExample.java'
        source.parent.mkdir(parents=True)
        source.write_text(text)
        classes = directory / 'classes'
        subprocess.run([javac, '--release', '17', '-g', '-d', str(classes), str(source)],
                       check=True, capture_output=True, timeout=20)
        data = (classes / 'proof/StageExample.class').read_bytes()
        assert data[:4] == b'\xca\xfe\xba\xbe' and int.from_bytes(data[6:8], 'big') == 61
        jar = base / (label + '.jar')
        with zipfile.ZipFile(jar, 'w') as archive:
            archive.writestr('proof/StageExample.class', data)
        jars[label] = jar
    source_jar = base / 'claimed-sources.jar'
    with zipfile.ZipFile(source_jar, 'w') as archive:
        archive.writestr('proof/StageExample.java', original_source)
    return {'base': base, 'javap': javap, 'jars': jars,
            'source_jar': source_jar, 'original_source': original_source}


def _root(name, path, *, role, stage):
    return dict(manifest()['roots'][0], id=name, path=str(path), kind='jar',
                role=role, stage=stage)


def test_a06_disagreeing_source_jar_and_distribution_remain_readable_but_unmatched(
        distinct_java_inputs, tmp_path):
    fixture = distinct_java_inputs
    store = storage.Store(tmp_path / 'cas')
    declared = manifest()
    declared['roots'] = [
        _root('claimed-source', fixture['source_jar'], role='source', stage='source_jar'),
        _root('distribution', fixture['jars']['changed'], role='binary', stage='distributed'),
    ]
    profile = storage.capture_profile(declared, fixture['base'], store)
    prepared = index.prepare_index(profile, store, javap=fixture['javap'])
    snapshot = prepared['index_snapshot_id']
    assert prepared['status'] == 'OK'
    docs = {doc['root_id']: doc for doc in profile['documents']}
    source = index.inspect_document(store, snapshot, docs['claimed-source']['document_id'])
    binary = index.inspect_document(store, snapshot, docs['distribution']['document_id'], view='bytecode')
    assert source['status'] == binary['status'] == 'OK'
    assert source['results'][0]['text'] == fixture['original_source']
    assert 'return 7;' in source['results'][0]['text']
    assert re.search(r'bipush\s+23\b', binary['results'][0]['text'])
    assert not re.search(r'bipush\s+7\b', binary['results'][0]['text'])
    for root in profile['roots']:
        assert store.read(root['artifact_hash']) == Path(root['path']).read_bytes()
    assert docs['claimed-source']['artifact_hash'] != docs['distribution']['artifact_hash']
    hits = index.search(store, snapshot, 'StageExample')
    assert {hit['root_id'] for hit in hits['results']} == set(docs)
    assert all(hit['source_binary_match'] == 'UNRESOLVED' for hit in hits['results'])
    assert all(hit['applicability'] == 'RESEARCH_NOT_RUNTIME_EVIDENCE' for hit in hits['results'])
    symbol = index.find_symbols(store, snapshot, 'proof/StageExample', member='value', descriptor='()I')
    assert symbol['results'][0]['source_binary_match'] == 'UNRESOLVED'
    assert profile['resolution'] == 'CAPTURED_NOT_RUNTIME_VERIFIED'
    assert hits['run_id'] is None and symbol['run_id'] is None
    assert source['evidence'][0]['stage'] == 'source_jar'
    assert binary['evidence'][0]['stage'] == 'distributed'
    assert all(e['maturity'] == 'RESEARCH_ONLY' for e in hits['evidence'])


def test_a07_changed_instruction_positions_keep_distinct_static_stage_locators(
        distinct_java_inputs, tmp_path):
    fixture = distinct_java_inputs
    store = storage.Store(tmp_path / 'cas')
    declared = manifest()
    stages = {'original': 'distributed', 'changed': 'changed_instruction_fixture'}
    declared['roots'] = [_root(name, fixture['jars'][name], role='binary', stage=stage)
                         for name, stage in stages.items()]
    profile = storage.capture_profile(declared, fixture['base'], store)
    snapshot = index.prepare_index(profile, store, javap=fixture['javap'])['index_snapshot_id']
    found = index.find_symbols(store, snapshot, 'proof/StageExample', member='attack', descriptor='()I')
    assert found['status'] == 'AMBIGUOUS'  # Neither static stage is a loaded-class selection.
    assert len(found['results']) == 2
    assert len({symbol['symbol_id'] for symbol in found['results']}) == 2
    assert len({symbol['content_hash'] for symbol in found['results']}) == 2
    offsets = {}
    for symbol, evidence in zip(found['results'], found['evidence']):
        name = symbol['root_id']
        assert symbol['stage'] == evidence['stage'] == stages[name]
        assert evidence['document_id'] == symbol['document_id']
        assert evidence['content_hash'] == symbol['bytecode_hash']
        assert evidence['member'] == 'attack' and evidence['descriptor'] == '()I'
        page = index.inspect_document(store, snapshot, symbol['document_id'], view='bytecode')
        assert page['status'] == 'OK' and page['evidence'][0]['stage'] == stages[name]
        # Match actual javap instruction offsets, not a fabricated source ordinal.
        offsets[name] = [int(value) for value in re.findall(
            r'^\s*(\d+):\s+invokestatic\s+#[0-9]+\s+// Method target:\(\)I',
            page['results'][0]['text'], re.M)]
        references = [ref for ref in symbol['references'] if ref['name'] == 'target']
        assert len(references) == len(offsets[name])
        assert all(ref['relation'] == 'static_reference' for ref in references)
        lines = page['results'][0]['text'].splitlines()
        assert all('Method target:()I' in lines[ref['disassembly_line'] - 1] for ref in references)
    assert len(offsets['original']) == 1 and len(offsets['changed']) == 2
    assert offsets['changed'][-1] > offsets['original'][0]
    assert found['run_id'] is None and 'Static analysis' in found['null_reasons']['run_id']
    assert any('do not prove post-Mixin loaded bytecode' in warning for warning in found['warnings'])
    assert all(e['maturity'] == 'RESEARCH_ONLY' for e in found['evidence'])


@pytest.mark.parametrize('operation', ['put', 'pin'])
def test_a14_injected_enospc_preserves_existing_pinned_evidence(tmp_path, monkeypatch, operation):
    store = storage.Store(tmp_path / 'cas')
    original = b'previously pinned evidence must survive an unrelated write failure'
    key = store.put(original)
    store.pin(key, 'claim:existing')
    before = {p.relative_to(store.root): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    new_bytes = b'new evidence that cannot be durably published'

    def no_space(_fd):
        raise OSError(errno.ENOSPC, 'Injected fixture fsync failure')

    with monkeypatch.context() as patch:
        patch.setattr(storage.os, 'fsync', no_space)
        with pytest.raises(OSError) as failure:
            if operation == 'put':
                store.put(new_bytes)
            else:
                store.pin(key, 'claim:new-reference')
        assert failure.value.errno == errno.ENOSPC
    reopened = storage.Store(store.root)
    assert reopened.read(key) == original
    assert reopened.pinned_hashes() == {key}
    assert not reopened.blob_path(storage.digest(new_bytes)).exists()
    after = {p.relative_to(store.root): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    assert after == before  # Original blob/pin bytes are unchanged; no leftover partial publication.


def test_a14_interrupted_read_reports_unavailable_without_removing_pinned_evidence(tmp_path, monkeypatch):
    source = tmp_path / 'src'
    source.mkdir()
    (source / 'Affected.java').write_text('class Affected {}\n')
    (source / 'Readable.java').write_text('class Readable {}\n')
    store = storage.Store(tmp_path / 'cas')
    profile = storage.capture_profile(manifest(), tmp_path, store)
    snapshot = index.prepare_index(profile, store)['index_snapshot_id']
    docs = {doc['path']: doc for doc in profile['documents']}
    for doc in docs.values():
        store.pin(doc['content_hash'], 'claim:' + doc['path'])
    store.pin(snapshot, 'index:retained')
    before = {p.relative_to(store.root): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    pins = store.pinned_hashes()
    affected = docs['Affected.java']
    unavailable_path = store.blob_path(affected['content_hash'])
    read_bytes = Path.read_bytes

    def interrupted_read(path):
        if path == unavailable_path:
            raise InterruptedError(errno.EINTR, 'Injected fixture interrupted evidence read')
        return read_bytes(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, 'read_bytes', interrupted_read)
        with pytest.raises(storage.ArtifactUnavailable):
            store.read(affected['content_hash'])
        page = index.inspect_document(store, snapshot, affected['document_id'])
        assert page['status'] == 'ARTIFACT_UNAVAILABLE' and page['results'] == []
        assert page['evidence'][0]['availability'] == 'ARTIFACT_UNAVAILABLE'
        assert page['evidence'][0]['content_hash'] == affected['content_hash']
        search = index.search(store, snapshot, 'class')
        assert search['status'] == 'PARTIAL'
        assert [item['document_id'] for item in search['results']] == [docs['Readable.java']['document_id']]
        assert search['coverage']['unavailable_documents'] == [affected['document_id']]
        assert store.pinned_hashes() == pins
    reopened = storage.Store(store.root)
    assert reopened.read(affected['content_hash']) == b'class Affected {}\n'
    assert reopened.pinned_hashes() == pins
    after = {p.relative_to(store.root): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    assert after == before
    assert index.inspect_document(reopened, snapshot, affected['document_id'])['status'] == 'OK'


def test_a20_distinct_nonnull_tick_frame_and_log_intervals_remain_nonatomic():
    expected = contract()
    expected.update(physical_side='client', assertion_domain='rendering')
    captured = observation(expected)
    intervals = dict(server_tick_start=101, server_tick_end=107,
                     client_frame_start=405, client_frame_end=419,
                     log_sequence_start=901, log_sequence_end=903)
    captured.update(intervals)
    before = deepcopy(captured)
    result = verification.evaluate_observation(expected, captured)
    assert result['status'] == 'OK' and result['reasons'] == []
    assert result['observation_interval'] == intervals
    assert result['atomic'] is False
    assert result['outcome'] == 'NOT_RUN'
    assert result['evidence_level'] == 'IMPORTED_REPORT_NOT_LIVE_ATTESTATION'
    assert result['results'] == captured['entities']
    assert captured == before
