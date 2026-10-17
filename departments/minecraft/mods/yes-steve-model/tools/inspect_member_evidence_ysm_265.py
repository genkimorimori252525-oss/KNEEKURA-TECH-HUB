#!/usr/bin/env python3
"""Opt-in one-file evidence viewer; no artifact execution, scans, downloads or audits."""
import argparse
import hashlib
import json
from pathlib import Path

COLLECTIONS = ('members', 'bounded_dependency_support', 'constructor_members', 'caller_methods', 'writer_methods')

def inspect(root, evidence, owner, name=None, descriptor=None, full=False, offset=0, limit=20):
    root = Path(root).resolve()
    if Path(evidence).name != evidence or '/' in evidence or '\\' in evidence or not evidence.endswith('.json'):
        raise ValueError('Evidence must be one flat JSON filename inside the research directory')
    path = (root / evidence).resolve()
    if path.parent != root:
        raise ValueError('Evidence resolves outside the research directory')
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError('Offset must be nonnegative and limit between 1 and 100')
    if full and (name is None or descriptor is None):
        raise ValueError('Full view requires exact owner, name and descriptor')
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('Evidence must be a JSON object')
    artifact = data.get('artifact', {})
    if not isinstance(artifact, dict):
        raise ValueError('Artifact metadata must be a JSON object when present')
    found_schema = False
    members = {}
    locations = {}
    for key in COLLECTIONS:
        if key not in data:
            continue
        found_schema = True
        if not isinstance(data[key], list):
            raise ValueError('Unsupported member collection: ' + key)
        for row in data[key]:
            if not isinstance(row, dict) or not all(isinstance(row.get(k), str) for k in ('owner', 'name', 'descriptor')):
                raise ValueError('Malformed member in ' + key)
            ident = tuple(row[k] for k in ('owner', 'name', 'descriptor'))
            if ident in members and members[ident] != row:
                raise ValueError('Conflicting duplicate member: ' + repr(ident))
            members[ident] = row
            locations.setdefault(ident, []).append(key)
    if not found_schema:
        raise ValueError('No supported method collection; this viewer does not guess another schema')
    owner = owner.replace('.', '/')
    selected = [(i, row) for i, row in sorted(members.items()) if i[0] == owner
                and (name is None or i[1] == name) and (descriptor is None or i[2] == descriptor)]
    result = {
        'scope': 'ONE_FILE_EVIDENCE_VIEW_ONLY', 'evidence': evidence,
        'evidence_sha256': hashlib.sha256(raw).hexdigest(),
        'declared_artifact_sha256': data.get('artifact_sha256', artifact.get('sha256')),
        'artifact_rechecked': False, 'source_rechecked': False, 'auditors_run': False,
        'target_executed': False, 'semantic_confidence_changed': False,
        'total_matches': len(selected),
    }
    if full:
        if len(selected) != 1:
            raise ValueError('Full view requires exactly one matching member, found ' + str(len(selected)))
        ident, row = selected[0]
        result.update(collections=locations[ident], member=row)
    else:
        page = selected[offset:offset + limit]
        result.update(offset=offset, limit=limit, truncated=offset + len(page) < len(selected), members=[])
        for ident, row in page:
            summary = dict(zip(('owner', 'name', 'descriptor'), ident))
            summary.update(collections=locations[ident], access=row.get('access'),
                           has_code='instructions' in row,
                           instruction_count=len(row['instructions']) if 'instructions' in row else None,
                           code_sha256=row.get('code_sha256'))
            result['members'].append(summary)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--name')
    parser.add_argument('--descriptor')
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    try:
        result = inspect(args.root, args.evidence, args.owner, args.name, args.descriptor, args.full, args.offset, args.limit)
    except (ValueError, OSError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
