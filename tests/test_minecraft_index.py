import importlib
import shutil
import subprocess
import zipfile

import pytest
from test_minecraft_storage import manifest


def mod(name):
    return importlib.import_module('kneekura_tech_hub.minecraft.' + name)


@pytest.fixture
def captured(tmp_path):
    s = mod('storage'); folder = tmp_path / 'src'; folder.mkdir()
    for i in range(25):
        (folder / f'File{i:02}.java').write_text(f'// hit {i}\nclass File{i} {{}}\n')
    store = s.Store(tmp_path / 'cache')
    p = s.capture_profile(manifest(), tmp_path, store)
    return store, p, tmp_path


def test_search_pagination_is_complete_and_snapshot_bound(captured):
    store, p, _ = captured; a = mod('index'); idx = a.prepare_index(p, store)
    first = a.search(store, idx['index_snapshot_id'], 'hit', limit=20)
    assert first['status'] == 'PARTIAL'
    assert len(first['results']) == 20
    assert first['coverage']['matching_documents'] == 25
    second = a.search(store, idx['index_snapshot_id'], 'hit', cursor=first['next_cursor'])
    assert len(second['results']) == 5
    assert second['next_cursor'] is None
    assert len({r['document_id'] for r in first['results'] + second['results']}) == 25


def test_cursor_cannot_cross_snapshot_or_query(captured):
    store, p, base = captured; a = mod('index'); one = a.prepare_index(p, store)
    cursor = a.search(store, one['index_snapshot_id'], 'hit', limit=1)['next_cursor']
    (base / 'src/File00.java').write_text('new hit')
    new = mod('storage').capture_profile(manifest(), base, store)
    two = a.prepare_index(new, store)
    assert a.search(store, two['index_snapshot_id'], 'hit', cursor=cursor)['status'] == 'STALE'
    assert a.search(store, one['index_snapshot_id'], 'other', cursor=cursor)['status'] == 'STALE'


def test_partial_inputs_never_report_not_found(captured):
    store, _, base = captured; a = mod('index'); m = manifest()
    m['roots'].append(dict(m['roots'][0], id='lost', path='lost.jar', kind='jar'))
    p = mod('storage').capture_profile(m, base, store); idx = a.prepare_index(p, store)
    assert a.search(store, idx['index_snapshot_id'], 'nonexistent')['status'] == 'PARTIAL'
    assert a.search(store, idx['index_snapshot_id'], 'hit')['results']


def test_complete_declared_text_scope_may_report_not_found(captured):
    store, p, _ = captured; a = mod('index'); idx = a.prepare_index(p, store)
    result = a.search(store, idx['index_snapshot_id'], 'absent')
    assert result['status'] == 'NOT_FOUND'
    assert result['coverage']['search_scope'] == 'captured_text_and_paths'


def test_source_read_is_full_paged_and_immutable(captured):
    store, p, base = captured; a = mod('index'); idx = a.prepare_index(p, store)
    d = p['documents'][0]
    (base / 'src/File00.java').write_text('changed')
    first = a.inspect_document(store, idx['index_snapshot_id'], d['document_id'], size=5)
    text = first['results'][0]['text']; cur = first['next_cursor']
    while cur:
        page = a.inspect_document(store, idx['index_snapshot_id'], d['document_id'], size=5, cursor=cur)
        text += page['results'][0]['text']; cur = page['next_cursor']
    assert text.encode() == store.read(d['content_hash'])


def test_utf8_page_boundary_does_not_drop_bytes(tmp_path):
    s = mod('storage'); a = mod('index'); (tmp_path / 'src').mkdir()
    text = '霊夢😀の攻撃\n' * 9
    (tmp_path / 'src/Unicode.java').write_text(text)
    store = s.Store(tmp_path / 'cache'); p = s.capture_profile(manifest(), tmp_path, store)
    idx = a.prepare_index(p, store); cur = None; out = ''
    while True:
        page = a.inspect_document(store, idx['index_snapshot_id'], p['documents'][0]['document_id'], size=5, cursor=cur)
        out += page['results'][0]['text']; cur = page['next_cursor']
        if not cur: break
    assert out == text


def test_buildscript_and_frontier_not_silently_anchor(captured):
    store, _, base = captured; a = mod('index'); m = manifest()
    m['roots'][0]['scope'] = 'buildscript'
    p = mod('storage').capture_profile(m, base, store); idx = a.prepare_index(p, store)
    assert not a.search(store, idx['index_snapshot_id'], 'hit')['results']
    assert a.search(store, idx['index_snapshot_id'], 'hit', scope='buildscript')['results']
    m['roots'][0]['scope'] = 'research'; m['roots'][0]['track'] = 'FRONTIER'
    p = mod('storage').capture_profile(m, base, store); idx = a.prepare_index(p, store)
    assert not a.search(store, idx['index_snapshot_id'], 'hit')['results']
    r = a.search(store, idx['index_snapshot_id'], 'hit', track='all')
    assert r['results'][0]['track'] == 'FRONTIER'


def test_missing_blob_does_not_hide_other_readable_results(captured):
    store, p, _ = captured; a = mod('index'); idx = a.prepare_index(p, store)
    store.blob_path(p['documents'][0]['content_hash']).unlink()
    result = a.search(store, idx['index_snapshot_id'], 'hit')
    assert result['status'] == 'PARTIAL' and result['results']
    assert result['coverage']['unavailable_documents']
    assert a.inspect_document(store, idx['index_snapshot_id'], p['documents'][0]['document_id'])['status'] == 'ARTIFACT_UNAVAILABLE'


@pytest.mark.parametrize('limit', [0, -1, True, 10001])
def test_bad_query_limits_rejected(captured, limit):
    store, p, _ = captured; a = mod('index'); idx = a.prepare_index(p, store)
    with pytest.raises(mod('storage').ContractError): a.search(store, idx['index_snapshot_id'], 'hit', limit=limit)


@pytest.fixture
def class_profile(tmp_path):
    if not shutil.which('javac') or not shutil.which('javap'):
        pytest.skip('JDK required for real classfile fixture')
    (tmp_path / 'src/demo').mkdir(parents=True)
    (tmp_path / 'src/demo/Example.java').write_text('''package demo;
public class Example {
  public int attack(int x) { return helper(x); }
  public int attack(String x) { return x.length(); }
  private int helper(int x) { return x + 1; }
}''')
    subprocess.run(['javac', '--release', '17', '-g', '-d', str(tmp_path / 'classes'),
                    str(tmp_path / 'src/demo/Example.java')], check=True, capture_output=True)
    with zipfile.ZipFile(tmp_path / 'mod.jar', 'w') as z:
        z.write(tmp_path / 'classes/demo/Example.class', 'demo/Example.class')
    s = mod('storage'); store = s.Store(tmp_path / 'cache'); m = manifest()
    m['roots'].append(dict(m['roots'][0], id='mod', path='mod.jar', kind='jar', role='binary', stage='distributed'))
    return store, s.capture_profile(m, tmp_path, store), tmp_path


def test_real_class_overloads_and_call_references(class_profile):
    store, p, _ = class_profile; a = mod('index')
    idx = a.prepare_index(p, store, javap=shutil.which('javap'))
    r = a.find_symbols(store, idx['index_snapshot_id'], 'demo/Example', member='attack')
    assert r['status'] == 'AMBIGUOUS'
    assert {x['descriptor'] for x in r['results']} == {'(I)I', '(Ljava/lang/String;)I'}
    r = a.find_symbols(store, idx['index_snapshot_id'], 'demo/Example', member='attack', descriptor='(I)I')
    assert r['status'] == 'OK'
    assert r['results'][0]['stage'] == 'distributed'
    assert any(e['name'] == 'helper' for e in r['results'][0]['references'])
    assert 'reflection' in ' '.join(r['warnings']).lower()


def test_same_class_in_multiple_roots_is_ambiguous(class_profile):
    store, _, base = class_profile; a = mod('index'); s = mod('storage'); m = manifest('mod.jar', 'jar')
    m['roots'].append(dict(m['roots'][0], id='other'))
    p = s.capture_profile(m, base, store); idx = a.prepare_index(p, store, javap=shutil.which('javap'))
    r = a.find_symbols(store, idx['index_snapshot_id'], 'demo/Example', member='attack', descriptor='(I)I')
    assert r['status'] == 'AMBIGUOUS'
    assert {x['root_order'] for x in r['results']} == {0, 1}


def test_unprepared_bytecode_is_partial_not_absent(class_profile):
    store, p, _ = class_profile; a = mod('index'); idx = a.prepare_index(p, store)
    assert a.find_symbols(store, idx['index_snapshot_id'], 'demo/Example', member='attack')['status'] == 'PARTIAL'


def test_bytecode_inspect_and_warm_cache_reuse(class_profile):
    store, p, _ = class_profile; a = mod('index'); one = a.prepare_index(p, store, javap=shutil.which('javap'))
    two = a.prepare_index(p, store, javap=shutil.which('javap'))
    assert one['index_snapshot_id'] == two['index_snapshot_id']
    assert two['cache']['hits'] == 1 and two['cache']['misses'] == 0
    doc = next(d for d in p['documents'] if d['media'] == 'class')
    page = a.inspect_document(store, one['index_snapshot_id'], doc['document_id'], view='bytecode')
    assert 'invokevirtual' in page['results'][0]['text']
    assert page['evidence'][0]['stage'] == 'distributed'
    assert a.inspect_document(store, one['index_snapshot_id'], doc['document_id'], view='source')['status'] == 'UNSUPPORTED'


def test_invalid_class_reports_coverage_failure(tmp_path):
    s = mod('storage'); a = mod('index'); (tmp_path / 'src').mkdir()
    (tmp_path / 'src/Bad.class').write_bytes(b'not a class')
    store = s.Store(tmp_path / 'cache'); p = s.capture_profile(manifest(), tmp_path, store)
    idx = a.prepare_index(p, store, javap=shutil.which('javap'))
    assert a.find_symbols(store, idx['index_snapshot_id'], 'Bad')['status'] == 'PARTIAL'


def test_wrong_cached_output_cannot_be_reused_for_another_class(class_profile):
    import json
    store, p, _ = class_profile; a = mod('index')
    one = a.prepare_index(p, store, javap=shutil.which('javap'))
    snapshot = store.json(one['index_snapshot_id'])
    details = next(iter(snapshot['bytecode'].values()))
    original = store.read(details['text_hash']).decode()
    doc = next(d for d in p['documents'] if d['media'] == 'class')
    wrong = original.replace('sha256:' + doc['content_hash'], 'sha256:' + '0' * 64)
    receipt_path = next((store.root / 'derived').glob('*.json'))
    receipt = json.loads(receipt_path.read_bytes())
    receipt['text_hash'] = store.put(wrong.encode())
    receipt_path.write_text(json.dumps(receipt))
    two = a.prepare_index(p, store, javap=shutil.which('javap'))
    assert two['status'] == 'PARTIAL'
    assert not store.json(two['index_snapshot_id'])['bytecode']
    assert 'identity' in two['bytecode_unresolved'][0]['reason'].lower()


@pytest.mark.parametrize('missing', ['input', 'output'])
def test_symbol_lookup_does_not_claim_missing_evidence_is_available(class_profile, missing):
    store, p, _ = class_profile; a = mod('index')
    prepared = a.prepare_index(p, store, javap=shutil.which('javap'))
    snapshot = store.json(prepared['index_snapshot_id'])
    doc = next(d for d in p['documents'] if d['media'] == 'class')
    key = doc['content_hash'] if missing == 'input' else snapshot['bytecode'][doc['document_id']]['text_hash']
    store.blob_path(key).unlink()
    result = a.find_symbols(store, prepared['index_snapshot_id'], 'demo/Example', member='attack', descriptor='(I)I')
    assert result['status'] == 'PARTIAL'
    assert not result['results']
    assert result['coverage']['unavailable_documents']


def test_symbol_pagination_keeps_ambiguity_and_query_binding(class_profile):
    store, p, _ = class_profile; a = mod('index')
    prepared = a.prepare_index(p, store, javap=shutil.which('javap'))
    identifier = prepared['index_snapshot_id']
    first = a.find_symbols(store, identifier, 'demo/Example', member='attack', limit=1)
    assert first['status'] == 'AMBIGUOUS' and len(first['results']) == 1
    assert first['coverage']['matching_symbols'] == 2
    second = a.find_symbols(store, identifier, 'demo/Example', member='attack', cursor=first['next_cursor'])
    assert len(second['results']) == 1 and second['next_cursor'] is None
    assert second['results'][0]['descriptor'] != first['results'][0]['descriptor']
    changed = a.find_symbols(store, identifier, 'demo/Example', member='helper', cursor=first['next_cursor'])
    assert changed['status'] == 'STALE'


@pytest.mark.parametrize('filters', [{'scope': 'banana'}, {'namespace': 'parchment'}, {'track': 'ancHor'}])
def test_invalid_filters_do_not_become_false_not_found(captured, filters):
    store, p, _ = captured; a = mod('index'); prepared = a.prepare_index(p, store)
    with pytest.raises(mod('storage').ContractError):
        a.search(store, prepared['index_snapshot_id'], 'hit', **filters)


def test_provider_identity_includes_jdk_image_not_just_launcher(tmp_path):
    home = tmp_path / 'jdk'; (home / 'bin').mkdir(parents=True); (home / 'lib').mkdir()
    launcher = home / 'bin/javap'; launcher.write_text('fixture launcher'); launcher.chmod(0o755)
    (home / 'release').write_text('JAVA_VERSION="21.0.11"')
    image = home / 'lib/modules'; image.write_bytes(b'image1')
    first = mod('bytecode').provider_identity(str(launcher))
    image.write_bytes(b'image2')
    second = mod('bytecode').provider_identity(str(launcher))
    assert first['executable_hash'] == second['executable_hash']
    assert first != second


def test_missing_original_does_not_hide_verified_disassembly(class_profile):
    store, p, _ = class_profile; a = mod('index')
    prepared = a.prepare_index(p, store, javap=shutil.which('javap'))
    doc = next(d for d in p['documents'] if d['media'] == 'class')
    store.blob_path(doc['content_hash']).unlink()
    result = a.inspect_document(store, prepared['index_snapshot_id'], doc['document_id'], view='bytecode')
    assert result['status'] == 'PARTIAL'
    assert 'invokevirtual' in result['results'][0]['text']
    assert result['evidence'][0]['input_availability'] == 'ARTIFACT_UNAVAILABLE'


def test_reference_preview_is_bounded_without_losing_full_disassembly(class_profile):
    store, _, base = class_profile; a = mod('index'); s = mod('storage')
    source = base / 'src/demo/Example.java'
    source.write_text('package demo; public class Example { public int attack(int x) { '
                      + 'x = helper(x);' * 150 + 'return x; } private int helper(int x) { return x+1; }}')
    subprocess.run(['javac', '--release', '17', '-g', '-d', str(base / 'classes'), str(source)],
                   check=True, capture_output=True)
    p = s.capture_profile(manifest('classes'), base, store)
    prepared = a.prepare_index(p, store, javap=shutil.which('javap'))
    result = a.find_symbols(store, prepared['index_snapshot_id'], 'demo/Example', member='attack', descriptor='(I)I')
    symbol = result['results'][0]
    assert len(symbol['references']) == 100 and symbol['reference_count'] == 150
    assert symbol['references_truncated'] is True
    assert store.read(symbol['bytecode_hash']).count(b'// Method helper:') == 150
