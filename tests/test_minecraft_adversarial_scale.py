"""A09/A15 offline regressions over real JDK-17 classfiles and captured files.

Annotation declarations are fixtures, not a running Mixin transformer. The A09
POTENTIAL requirement is expressed by the API's conditional-candidate and
NOT_DETERMINED states; these tests never establish runtime compatibility.
"""
from __future__ import annotations

import copy
import io
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from kneekura_tech_hub.minecraft import index, interventions
from kneekura_tech_hub.minecraft.classfile import read_class
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical, capture_profile
from test_minecraft_storage import manifest


SEARCH_COUNT = 1000
LEAF_COUNT = 1024
CALLBACK_DESCRIPTOR = '(ILorg/spongepowered/asm/mixin/injection/callback/CallbackInfo;)V'


def _compile(root: Path, sources: dict[str, str]) -> Path:
    javac = shutil.which('javac')
    assert javac, 'These adversarial classfile fixtures require the cached JDK 17'
    files = []
    for relative, content in sources.items():
        path = root / 'java' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        files.append(str(path))
    classes = root / 'classes'
    subprocess.run([javac, '--release', '17', '-g', '-d', str(classes), *files],
                   check=True, capture_output=True, text=True, timeout=60)
    return classes


def _snapshot(root: Path, declaration: dict, *, javap: str | None = None):
    store = Store(root / 'cas')
    profile = capture_profile(declaration, root, store)
    assert profile['coverage']['complete'] is True
    identifier = index.prepare_index(profile, store, javap=javap)['index_snapshot_id']
    return store, profile, identifier


def _changed_snapshot(root: Path, store: Store, declaration: dict) -> str:
    changed = copy.deepcopy(declaration)
    changed['workspace_revision'] = 'c' * 40
    return index.prepare_index(capture_profile(changed, root, store), store)['index_snapshot_id']


def _assert_locator(store: Store, profile: dict, identifier: str, evidence: dict):
    document = next(d for d in profile['documents'] if d['document_id'] == evidence['document_id'])
    assert evidence['index_snapshot_id'] == identifier
    for key in ('root_id', 'path', 'stage', 'namespace', 'content_hash', 'artifact_hash'):
        assert evidence[key] == document[key]
    assert evidence['availability'] == 'AVAILABLE'
    assert evidence['maturity'] == 'RESEARCH_ONLY'
    assert store.read(evidence['content_hash'])
    return document


@pytest.fixture(scope='module')
def compatible_injectors(tmp_path_factory):
    root = tmp_path_factory.mktemp('a09-compatible-injectors')
    sources = {
        'org/spongepowered/asm/mixin/Mixin.java': '''package org.spongepowered.asm.mixin;
            import java.lang.annotation.*;
            @Retention(RetentionPolicy.CLASS) @Target(ElementType.TYPE)
            public @interface Mixin { Class<?>[] value(); }''',
        'org/spongepowered/asm/mixin/injection/At.java': '''package org.spongepowered.asm.mixin.injection;
            import java.lang.annotation.*;
            @Retention(RetentionPolicy.CLASS) public @interface At { String value(); }''',
        'org/spongepowered/asm/mixin/injection/Inject.java': '''package org.spongepowered.asm.mixin.injection;
            import java.lang.annotation.*;
            @Retention(RetentionPolicy.CLASS) @Target(ElementType.METHOD)
            public @interface Inject { String[] method(); At at(); boolean cancellable() default false; int require() default -1; }''',
        'org/spongepowered/asm/mixin/injection/callback/CallbackInfo.java': '''package org.spongepowered.asm.mixin.injection.callback;
            public final class CallbackInfo {}''',
        'demo/Entity.java': '''package demo;
            public class Entity { public void hurt(int amount) {} public void hurt(String message) {} }''',
    }
    for owner, method in [('AlphaMixin', 'beforeAlpha'), ('BetaMixin', 'beforeBeta')]:
        # Both no-op callbacks observe the same HEAD, neither cancels/replaces it.
        sources[f'demo/{owner}.java'] = f'''package demo;
            import org.spongepowered.asm.mixin.Mixin;
            import org.spongepowered.asm.mixin.injection.*;
            import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
            @Mixin(Entity.class) public class {owner} {{
                @Inject(method={{"hurt(I)V"}}, at=@At("HEAD"), cancellable=false, require=1)
                private void {method}(int amount, CallbackInfo info) {{}}
            }}'''
    classes = _compile(root, sources)
    origins = {'alpha': ['demo/AlphaMixin.class'], 'beta': ['demo/BetaMixin.class']}
    origins['support'] = [str(p.relative_to(classes)) for p in sorted(classes.rglob('*.class'))
                          if str(p.relative_to(classes)) not in origins['alpha'] + origins['beta']]
    declaration = manifest('support.jar', 'jar')
    declaration['roots'] = []
    for name, paths in origins.items():
        with zipfile.ZipFile(root / f'{name}.jar', 'w') as archive:
            for path in paths:
                archive.write(classes / path, path)
        declaration['roots'].append(dict(manifest()['roots'][0], id=name, path=f'{name}.jar',
                                         kind='jar', role='binary', stage='distributed'))
    javap = shutil.which('javap')
    assert javap, 'The exact-target overload check requires the cached javap'
    return _snapshot(root, declaration, javap=javap)


def test_a09_same_target_non_cancelling_injectors_remain_potential_candidates(compatible_injectors):
    store, profile, identifier = compatible_injectors
    result = interventions.inspect_interventions(store, identifier, owner='demo/Entity',
                                                 member='hurt', descriptor='(I)V')
    assert result['status'] == 'PARTIAL'
    assert result['compatibility_verdict'] == 'NOT_DETERMINED'
    assert result['coverage']['complete'] is False
    assert result['coverage']['declared_candidates'] == 2
    assert result['canonical_writes'] == 0 and result['run_id'] is None
    assert result['next_cursor'] is None
    assert {r['mixin'] for r in result['results']} == {'demo/AlphaMixin', 'demo/BetaMixin'}
    assert {r['root_id'] for r in result['results']} == {'alpha', 'beta'}
    assert len({r['evidence']['artifact_hash'] for r in result['results']}) == 2
    assert result['evidence'] == [r['evidence'] for r in result['results']]
    for row in result['results']:
        assert row['kind'] == 'mixin_injection' and row['injector'] == 'Inject'
        assert row['target'] == {'owner': 'demo/Entity', 'member': 'hurt', 'descriptor': '(I)V'}
        assert row['source_descriptor'] == CALLBACK_DESCRIPTOR
        assert row['applicability'] == 'CONDITIONAL_NOT_EXECUTED'
        assert row['injection']['cancellable'] is False
        assert row['injection']['require'] == 1
        assert row['injection']['at']['elements']['value'] == 'HEAD'
        document = _assert_locator(store, profile, identifier, row['evidence'])
        assert document['stage'] == 'distributed' and document['namespace'] == 'mojmap'
        with zipfile.ZipFile(io.BytesIO(store.read(document['artifact_hash']))) as archive:
            original = archive.read(document['path'])
        assert original == store.read(document['content_hash'])
        compiled = read_class(original)
        assert compiled['major'] == 61 and compiled['owner'] == row['mixin']
        assert any(m['name'] == row['source_member'] and m['descriptor'] == CALLBACK_DESCRIPTOR
                   for m in compiled['methods'])
    assert any('not executed' in item['reason'].lower() for item in result['coverage']['unresolved'])


def test_a09_overload_and_incoming_relations_preserve_exact_targets_and_origins(compatible_injectors):
    store, profile, identifier = compatible_injectors
    exact = index.find_symbols(store, identifier, 'demo/Entity', member='hurt', descriptor='(I)V')
    assert exact['status'] == 'OK' and len(exact['results']) == 1
    assert exact['results'][0]['descriptor'] == '(I)V'
    overload = interventions.inspect_interventions(store, identifier, owner='demo/Entity',
                                                   member='hurt', descriptor='(Ljava/lang/String;)V')
    assert overload['results'] == [] and overload['coverage']['declared_candidates'] == 0
    assert overload['compatibility_verdict'] == 'NOT_DETERMINED'
    graph = interventions.relations(store, identifier, owner='demo/Entity', depth=1)
    incoming = [e for e in graph['results'] if e['relation'] == 'injects']
    assert len(incoming) == 2
    assert {e['root_id'] for e in incoming} == {'alpha', 'beta'}
    for edge in incoming:
        assert edge['target'] == {'owner': 'demo/Entity', 'member': 'hurt', 'descriptor': '(I)V'}
        assert edge['source']['descriptor'] == CALLBACK_DESCRIPTOR
        assert edge['applicability'] == 'CONDITIONAL_NOT_EXECUTED'
        _assert_locator(store, profile, identifier, edge['evidence'])
    assert graph['coverage']['complete'] is False
    assert any('No dynamic call graph' in warning for warning in graph['warnings'])


@pytest.fixture(scope='module')
def thousand_matches(tmp_path_factory):
    root = tmp_path_factory.mktemp('a15-thousand-search-matches')
    source = root / 'src'
    source.mkdir()
    for number in range(SEARCH_COUNT):
        (source / f'Match{number:04}.java').write_text(f'// scale_match_token {number:04}\n', encoding='utf-8')
    declaration = manifest()
    store, profile, identifier = _snapshot(root, declaration)
    changed = _changed_snapshot(root, store, declaration)
    return store, profile, identifier, changed


@pytest.mark.parametrize('limit', [20, 137, 1000])
def test_a15_all_thousand_search_matches_are_reachable_once_with_bounded_pages(thousand_matches, limit):
    store, profile, identifier, _ = thousand_matches
    expected = {d['document_id'] for d in profile['documents']}
    assert len(expected) == SEARCH_COUNT
    cursor = None
    seen, cursors = set(), set()
    pages = 0
    for _ in range(SEARCH_COUNT + 1):
        # Exercise the actual default top-20 path, not just explicit limits.
        kwargs = {} if limit == 20 else {'limit': limit}
        page = index.search(store, identifier, 'scale_match_token', cursor=cursor, **kwargs)
        pages += 1
        assert page['index_snapshot_id'] == identifier and page['profile_id'] == profile['profile_id']
        assert page['coverage']['matching_documents'] == SEARCH_COUNT
        assert page['coverage']['complete'] is True
        assert page['coverage']['search_scope'] == 'captured_text_and_paths'
        assert page['coverage']['unavailable_documents'] == []
        assert 0 < len(page['results']) <= limit
        assert len(canonical(page['results'])) <= 48 * 1024
        if pages == 1 and limit == 20:
            assert len(page['results']) == 20 and page['next_cursor'] is not None
        keys = {r['document_id'] for r in page['results']}
        assert len(keys) == len(page['results']) and not keys & seen
        seen.update(keys)
        assert [e['document_id'] for e in page['evidence']] == [r['document_id'] for r in page['results']]
        for evidence in page['evidence']:
            _assert_locator(store, profile, identifier, evidence)
        cursor = page['next_cursor']
        assert page['coverage']['truncated'] is bool(cursor)
        assert page['status'] == ('PARTIAL' if cursor else 'OK')
        if cursor is None:
            break
        assert cursor not in cursors and len(cursor) <= 4096
        cursors.add(cursor)
    else:
        pytest.fail('Search pagination did not terminate')
    assert seen == expected and len(seen) == SEARCH_COUNT
    assert pages > 1


def test_a15_search_cursor_is_bound_to_snapshot_query_and_filters(thousand_matches):
    store, _, identifier, changed = thousand_matches
    cursor = index.search(store, identifier, 'scale_match_token')['next_cursor']
    assert changed != identifier and cursor
    for selected, query, filters in [
        (changed, 'scale_match_token', {}), (identifier, 'other_token', {}),
        (identifier, 'scale_match_token', {'scope': 'runtime'}),
        (identifier, 'scale_match_token', {'namespace': 'mojmap'}),
        (identifier, 'scale_match_token', {'track': 'all'}),
    ]:
        result = index.search(store, selected, query, cursor=cursor, **filters)
        assert result['status'] == 'STALE' and not result['results'] and result['next_cursor'] is None
    # Changing only page size preserves continuation identity.
    next_page = index.search(store, identifier, 'scale_match_token', cursor=cursor, limit=7)
    assert len(next_page['results']) == 7
    assert not {r['document_id'] for r in next_page['results']} & {
        r['document_id'] for r in index.search(store, identifier, 'scale_match_token')['results']}


@pytest.mark.parametrize('limit', [0, -1, True, 1.5, 10001])
def test_a15_search_rejects_out_of_contract_limits(thousand_matches, limit):
    store, _, identifier, _ = thousand_matches
    with pytest.raises(ContractError):
        index.search(store, identifier, 'scale_match_token', limit=limit)


@pytest.fixture(scope='module')
def large_relation_graph(tmp_path_factory):
    root = tmp_path_factory.mktemp('a15-large-relation-graph')
    hierarchy = 'package scale; class Ancestor {} class Root extends Ancestor {}\n'
    hierarchy += '\n'.join(f'class Leaf{n:04} extends Root {{}}' for n in range(LEAF_COUNT))
    hierarchy += '\nclass Sibling extends Ancestor {} class Unrelated {}\n'
    classes = _compile(root, {'scale/Hierarchy.java': hierarchy})
    declaration = manifest('classes')
    declaration['roots'][0].update(role='binary', stage='compiled')
    store, profile, identifier = _snapshot(root, declaration)
    assert read_class((classes / 'scale/Root.class').read_bytes())['major'] == 61
    changed = _changed_snapshot(root, store, declaration)
    return store, profile, identifier, changed


def _relation_key(edge: dict):
    return (edge['relation'], edge['source']['owner'], edge['target']['owner'],
            edge['root_id'], edge['evidence']['document_id'])


def test_a15_large_compiled_relation_graph_pages_every_edge_once(large_relation_graph):
    store, profile, identifier, _ = large_relation_graph
    expected = {('extends', f'scale/Leaf{n:04}', 'scale/Root') for n in range(LEAF_COUNT)}
    expected.add(('extends', 'scale/Root', 'scale/Ancestor'))
    cursor = None
    seen, triples, cursors = set(), set(), set()
    pages = 0
    for _ in range(len(expected) + 1):
        # Start at the default, then vary page size without changing the query.
        limit = 50 if pages == 0 else 73
        page = interventions.relations(store, identifier, owner='scale/Root', depth=1,
                                       cursor=cursor, **({} if pages == 0 else {'limit': limit}))
        pages += 1
        assert 0 < len(page['results']) <= limit
        assert page['status'] == 'PARTIAL' and page['coverage']['complete'] is False
        assert page['coverage']['edges'] == len(expected) > 1000
        assert page['coverage']['depth'] == 1
        assert page['index_snapshot_id'] == identifier and page['profile_id'] == profile['profile_id']
        assert page['evidence'] == [e['evidence'] for e in page['results']]
        if pages == 1:
            assert len(page['results']) == 50 and page['next_cursor'] is not None
        for edge in page['results']:
            key = _relation_key(edge)
            assert key not in seen
            seen.add(key)
            triples.add((edge['relation'], edge['source']['owner'], edge['target']['owner']))
            document = _assert_locator(store, profile, identifier, edge['evidence'])
            assert document['stage'] == 'compiled' and edge['namespace'] == 'mojmap'
            assert read_class(store.read(document['content_hash']))['owner'] == edge['source']['owner']
        cursor = page['next_cursor']
        if cursor is None:
            break
        assert cursor not in cursors and len(cursor) <= 4096
        cursors.add(cursor)
    else:
        pytest.fail('Relation pagination did not terminate')
    assert triples == expected and len(seen) == len(expected)
    assert pages > 1  # Multiple complete pages, never a silent top-20 result.


def test_a15_relation_depth_and_cursor_identity_are_preserved_at_scale(large_relation_graph):
    store, _, identifier, changed = large_relation_graph
    first = interventions.relations(store, identifier, owner='scale/Root', depth=1, limit=1)
    cursor = first['next_cursor']
    assert cursor and changed != identifier
    for selected, options in [
        (changed, {}), (identifier, {'owner': 'scale/Ancestor'}), (identifier, {'depth': 2}),
        (identifier, {'scope': 'runtime'}), (identifier, {'namespace': 'mojmap'}),
        (identifier, {'track': 'all'}),
    ]:
        args = {'owner': 'scale/Root', 'depth': 1, **options}
        page = interventions.relations(store, selected, cursor=cursor, **args)
        assert page['status'] == 'STALE' and page['results'] == [] and page['next_cursor'] is None
    assert index.search(store, identifier, 'Leaf', cursor=cursor)['status'] == 'STALE'
    deeper = interventions.relations(store, identifier, owner='scale/Root', depth=2, limit=1000)
    assert deeper['coverage']['depth'] == 2
    assert deeper['coverage']['edges'] == LEAF_COUNT + 3
    assert deeper['next_cursor'] is not None and deeper['coverage']['complete'] is False
    # Depth one excludes Ancestor->Object and its Sibling; depth two discovers them.
    all_edges = deeper['results']
    while deeper['next_cursor']:
        deeper = interventions.relations(store, identifier, owner='scale/Root', depth=2,
                                          limit=1000, cursor=deeper['next_cursor'])
        all_edges += deeper['results']
    triples = {(e['relation'], e['source']['owner'], e['target']['owner']) for e in all_edges}
    assert ('extends', 'scale/Ancestor', 'java/lang/Object') in triples
    assert ('extends', 'scale/Sibling', 'scale/Ancestor') in triples
    assert not any(source == 'scale/Unrelated' for _, source, _ in triples)
    assert len(all_edges) == len(triples) == LEAF_COUNT + 3


@pytest.mark.parametrize('argument,value', [('limit', 0), ('limit', -1), ('limit', True),
                                           ('limit', 1.5), ('limit', 1001),
                                           ('depth', 0), ('depth', True), ('depth', 4)])
def test_a15_relation_limits_and_depth_are_bounded(large_relation_graph, argument, value):
    store, _, identifier, _ = large_relation_graph
    with pytest.raises(ContractError):
        interventions.relations(store, identifier, owner='scale/Root', **{argument: value})
