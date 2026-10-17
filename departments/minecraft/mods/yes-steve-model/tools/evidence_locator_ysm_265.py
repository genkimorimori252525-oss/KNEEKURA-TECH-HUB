#!/usr/bin/env python3
"""Opt-in local navigation. Does not run auditors, download tools or promote mappings."""
import argparse
import hashlib
import json
from pathlib import Path

INDEX = 'EVIDENCE-LOCATOR-2026-10-17.json'
MAP = 'OBFUSCATION-MAP-2026-10-05.json'
LOOKUP = 'QUERY-NAME-LOOKUP-2026-10-17.jsonl'
EXTRA_LOOKUP = 'EXTRA-QUERY-NAME-LOOKUP-2026-10-17.jsonl'
ALIASES = 'NAVIGATION-COMPARISON-ALIASES-2026-10-17.json'
P = 'com/elfmcys/yesstevemodel/'


def normalized_owner(value):
    return value.replace('.', '/')


def build(root):
    files = {}
    owners = {}
    unsupported = []
    source_files = {}
    unindexed_tracks = []
    for path in sorted(root.glob('*EVIDENCE*.json')):
        if path.name.startswith('EVIDENCE-LOCATOR-'):
            continue
        raw = path.read_bytes()
        data = json.loads(raw)
        members = []
        tracks = data.get('source_tracks', []) if isinstance(data, dict) else []
        if not isinstance(tracks, list):
            unindexed_tracks.append({'evidence': path.name, 'reason': 'source_tracks is not a list'})
            tracks = []
        for i, track in enumerate(tracks):
            if (not isinstance(track, dict) or not all(isinstance(track.get(k), str) and track[k]
                    for k in ('path', 'sha256', 'revision'))
                    or len(track['sha256']) != 64 or any(c not in '0123456789abcdef' for c in track['sha256'])):
                unindexed_tracks.append({'evidence': path.name, 'record_index': i, 'reason': 'unsupported source track'})
                continue
            identity = (track['path'], track['sha256'], track['revision'])
            source_files.setdefault(identity, set()).add(path.name)
            files[path.name] = hashlib.sha256(raw).hexdigest()
        if isinstance(data, dict):
            for key in ('members', 'bounded_dependency_support', 'constructor_members'):
                rows = data.get(key, [])
                if isinstance(rows, list):
                    members.extend(r for r in rows if isinstance(r, dict)
                                   and isinstance(r.get('owner'), str)
                                   and isinstance(r.get('name'), str)
                                   and isinstance(r.get('descriptor'), str))
        if not members:
            unsupported.append(path.name)
            continue
        files[path.name] = hashlib.sha256(raw).hexdigest()
        for member in members:
            owner = normalized_owner(member['owner'])
            owners.setdefault(owner, set()).add(path.name)
    roles = {}
    map_path = root / MAP
    if map_path.exists():
        raw = map_path.read_bytes()
        files[MAP] = hashlib.sha256(raw).hexdigest()
        for row in json.loads(raw).get('mappings', []):
            if row.get('kind') == 'class' and row.get('obfuscated_owner') and row.get('semantic_owner'):
                roles[normalized_owner(row['obfuscated_owner'])] = {
                    'role': row['semantic_owner'], 'confidence': row.get('confidence'),
                    'source': MAP,
                }
    queries = []
    for name in (LOOKUP, EXTRA_LOOKUP):
        lookup_path = root / name
        if lookup_path.exists():
            raw = lookup_path.read_bytes()
            files[name] = hashlib.sha256(raw).hexdigest()
            queries.extend({**json.loads(line), 'source_catalog': name}
                           for line in raw.decode().splitlines() if line.strip())
    documents = sorted(p.name for p in root.glob('*RECOVERY*.md'))
    for name in documents:
        files[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    aliases = {}
    alias_path = root / ALIASES
    if alias_path.exists():
        raw = alias_path.read_bytes()
        catalog = json.loads(raw)
        if catalog.get('format') != 'ysm-navigation-comparison-aliases-v1':
            raise ValueError('Unsupported comparison alias catalog')
        seen = set()
        for row in catalog.get('aliases', []):
            if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k]
                    for k in ('owner', 'label', 'evidence', 'evidence_sha256', 'document',
                              'source_path', 'source_sha256', 'review_status')):
                raise ValueError('Malformed comparison alias')
            owner = normalized_owner(row['owner'])
            evidence, document = row['evidence'], row['document']
            if (any(Path(f).name != f or f in ('.', '..') for f in (evidence, document))
                    or evidence not in owners.get(owner, set()) or document not in documents
                    or files.get(evidence) != row['evidence_sha256']
                    or row['review_status'] != 'PRIMARY_STATIC_REVIEW_ONLY'):
                raise ValueError('Unanchored or stale comparison alias: ' + row['label'])
            data = json.loads((root / evidence).read_bytes())
            if not any(t.get('path') == row['source_path'] and t.get('sha256') == row['source_sha256']
                       for t in data.get('source_tracks', [])):
                raise ValueError('Missing comparison source track: ' + row['label'])
            identity = (owner, row['label'].casefold())
            if identity in seen:
                raise ValueError('Duplicate comparison alias: ' + row['label'])
            seen.add(identity)
            aliases.setdefault(owner, []).append({k: row[k] for k in
                ('label', 'evidence', 'document', 'source_path', 'review_status')})
        files[ALIASES] = hashlib.sha256(raw).hexdigest()
    return {
        'format': 'ysm-opt-in-evidence-locator-v1',
        'scope': 'Owner index uses top-level members, bounded_dependency_support and constructor_members; source-path mode indexes declared cohort source_tracks only. Neither is all repository evidence or semantic coverage.',
        'semantic_review': 'NOT_PERFORMED_BY_LOCATOR',
        'source_hashes': files,
        'owners': {key: sorted(value) for key, value in sorted(owners.items())},
        'roles': dict(sorted(roles.items())),
        'comparison_aliases': {k: sorted(v, key=lambda a: a['label']) for k, v in sorted(aliases.items())},
        'alias_policy': 'Explicit source-comparison navigation hints; not formal mappings or proven original symbols.',
        'queries': queries,
        'documents': documents,
        'unindexed_evidence_schemas': unsupported,
        'source_files': [{'source_path': path, 'declared_source_sha256': sha, 'revision': revision,
                          'evidence': sorted(evidence),
                          'association_scope': 'COHORT_SOURCE_TRACK_ONLY_NOT_OWNER_MAPPING_OR_FULL_SEMANTIC_COVERAGE',
                          'source_bytes_rechecked': False}
                         for (path, sha, revision), evidence in sorted(source_files.items())],
        'unindexed_source_track_records': unindexed_tracks,
    }


def search(index, *, owner=None, query=None, topic=None, source_path=None, limit=20):
    rows = []
    if source_path is not None:
        if 'source_files' not in index:
            raise ValueError('Source-path index missing; explicitly run --build once')
        needle = source_path.replace('\\', '/').casefold()
        rows = [dict(row) for row in index['source_files'] if needle in row['source_path'].replace('\\', '/').casefold()]
    elif query is not None:
        rows = [{'query': r['query'], 'target': r['target'],
                 'evidence': index['owners'].get(normalized_owner(r['target'].get('owner', '')), []),
                 'catalog': r.get('source_catalog', LOOKUP),
                 'scope': r.get('scope', 'Base query/YSM catalog only; no semantic promotion')}
                for r in index['queries'] if query.casefold() in r['query'].casefold()]
    elif owner is not None:
        needle = normalized_owner(owner).casefold()
        for name in sorted(set(index['owners']) | set(index['roles'])):
            role = index['roles'].get(name)
            aliases = index.get('comparison_aliases', {}).get(name, [])
            if (needle in name.casefold() or (role and needle in normalized_owner(role['role']).casefold())
                    or any(needle in normalized_owner(a['label']).casefold() for a in aliases)):
                rows.append({'owner': name, 'mapping': role, 'comparison_aliases': aliases,
                             'evidence': index['owners'].get(name, [])})
    elif topic is not None:
        rows = [{'document': name} for name in index['documents'] if topic.casefold() in name.casefold()]
    return {'total_matches': len(rows), 'truncated': len(rows) > limit, 'results': rows[:limit]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--build', action='store_true')
    action.add_argument('--owner')
    action.add_argument('--query')
    action.add_argument('--topic')
    action.add_argument('--source-path', help='Find existing cohort source tracks without inferring owner identity')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--check-selected', action='store_true', help='Hash only files returned by this search; no auditors executed')
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error('--limit must be between 1 and 100')
    if args.source_path is not None and not args.source_path.strip():
        parser.error('--source-path must not be empty')
    path = args.root / INDEX
    if args.build:
        if args.check_selected:
            parser.error('--check-selected requires a search')
        try:
            index = build(args.root)
        except (ValueError, KeyError, TypeError) as exc:
            parser.error(str(exc))
        path.write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')) + '\n')
        print(json.dumps({'owners': len(index['owners']), 'files': len(index['source_hashes']),
                          'unindexed_schemas': len(index['unindexed_evidence_schemas'])}))
        return
    if not path.exists():
        parser.error('Locator missing; explicitly run --build first')
    index = json.loads(path.read_text())
    try:
        result = search(index, owner=args.owner, query=args.query, topic=args.topic, source_path=args.source_path, limit=args.limit)
    except ValueError as exc:
        parser.error(str(exc))
    result['freshness'] = 'UNCHECKED_SNAPSHOT'
    if args.check_selected:
        selected = {f for r in result['results'] for f in r.get('evidence', [])}
        selected.update(r['document'] for r in result['results'] if 'document' in r)
        alias_rows = [a for r in result['results'] for a in r.get('comparison_aliases', [])]
        if alias_rows:
            selected.add(ALIASES)
            selected.update(a['document'] for a in alias_rows)
        if any(Path(f).name != f or f in ('.', '..') for f in selected):
            parser.error('Unsafe locator path')
        if args.query is not None:
            selected.update(name for name in (LOOKUP, EXTRA_LOOKUP) if name in index['source_hashes'])
        if args.owner is not None:
            selected.add(MAP)
        result['selected_hashes'] = {f: (args.root / f).is_file() and
            hashlib.sha256((args.root / f).read_bytes()).hexdigest() == index['source_hashes'].get(f)
            for f in sorted(selected)}
        result['freshness'] = 'SELECTED_FILES_MATCH' if all(result['selected_hashes'].values()) else 'STALE_OR_MISSING_SELECTED_FILE'
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['freshness'] == 'STALE_OR_MISSING_SELECTED_FILE':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
