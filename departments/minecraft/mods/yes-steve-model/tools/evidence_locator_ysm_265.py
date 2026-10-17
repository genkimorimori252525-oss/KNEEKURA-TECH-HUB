#!/usr/bin/env python3
"""Opt-in local navigation. Does not run auditors, download tools or promote mappings."""
import argparse
import hashlib
import json
from pathlib import Path

INDEX = 'EVIDENCE-LOCATOR-2026-10-17.json'
MAP = 'OBFUSCATION-MAP-2026-10-05.json'
LOOKUP = 'QUERY-NAME-LOOKUP-2026-10-17.jsonl'
P = 'com/elfmcys/yesstevemodel/'


def normalized_owner(value):
    return value.replace('.', '/')


def build(root):
    files = {}
    owners = {}
    unsupported = []
    for path in sorted(root.glob('*EVIDENCE*.json')):
        if path.name.startswith('EVIDENCE-LOCATOR-'):
            continue
        raw = path.read_bytes()
        data = json.loads(raw)
        members = []
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
    lookup_path = root / LOOKUP
    if lookup_path.exists():
        raw = lookup_path.read_bytes()
        files[LOOKUP] = hashlib.sha256(raw).hexdigest()
        queries = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    documents = sorted(p.name for p in root.glob('*RECOVERY*.md'))
    for name in documents:
        files[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    return {
        'format': 'ysm-opt-in-evidence-locator-v1',
        'scope': 'Top-level members, bounded_dependency_support and constructor_members only; not all references or all repository evidence.',
        'semantic_review': 'NOT_PERFORMED_BY_LOCATOR',
        'source_hashes': files,
        'owners': {key: sorted(value) for key, value in sorted(owners.items())},
        'roles': dict(sorted(roles.items())),
        'queries': queries,
        'documents': documents,
        'unindexed_evidence_schemas': unsupported,
    }


def search(index, *, owner=None, query=None, topic=None, limit=20):
    rows = []
    if query is not None:
        rows = [{'query': r['query'], 'target': r['target'],
                 'evidence': index['owners'].get(normalized_owner(r['target'].get('owner', '')), []),
                 'scope': 'Base query/YSM catalog only; no semantic promotion'}
                for r in index['queries'] if query.casefold() in r['query'].casefold()]
    elif owner is not None:
        needle = normalized_owner(owner).casefold()
        for name in sorted(set(index['owners']) | set(index['roles'])):
            role = index['roles'].get(name)
            if needle in name.casefold() or (role and needle in normalized_owner(role['role']).casefold()):
                rows.append({'owner': name, 'mapping': role, 'evidence': index['owners'].get(name, [])})
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
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--check-selected', action='store_true', help='Hash only files returned by this search; no auditors executed')
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error('--limit must be between 1 and 100')
    path = args.root / INDEX
    if args.build:
        if args.check_selected:
            parser.error('--check-selected requires a search')
        index = build(args.root)
        path.write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')) + '\n')
        print(json.dumps({'owners': len(index['owners']), 'files': len(index['source_hashes']),
                          'unindexed_schemas': len(index['unindexed_evidence_schemas'])}))
        return
    if not path.exists():
        parser.error('Locator missing; explicitly run --build first')
    index = json.loads(path.read_text())
    result = search(index, owner=args.owner, query=args.query, topic=args.topic, limit=args.limit)
    result['freshness'] = 'UNCHECKED_SNAPSHOT'
    if args.check_selected:
        selected = {f for r in result['results'] for f in r.get('evidence', [])}
        selected.update(r['document'] for r in result['results'] if 'document' in r)
        if any(Path(f).name != f or f in ('.', '..') for f in selected):
            parser.error('Unsafe locator path')
        if args.query is not None:
            selected.add(LOOKUP)
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
