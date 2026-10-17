#!/usr/bin/env python3
"""Explicit declaration-existence check for exact-symbol inventories; never executes target code."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from scan_ysm_265 import parse_class

SHA = '25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE = 63269843

def declaration_index(archive):
    result = {'methods': set(), 'fields': set(), 'classes': set(), 'class_count': 0}
    for name in archive.namelist():
        if not name.endswith('.class'):
            continue
        declaration = parse_class(archive.read(name))
        result['class_count'] += 1
        result['classes'].add(name[:-6])
        for kind in ('methods', 'fields'):
            for member in declaration[kind]:
                result[kind].add((name[:-6], member['name'], member['descriptor']))
    return result

def validate_targets(targets, declarations):
    normalized = set()
    for target in targets:
        if not isinstance(target, (tuple, list)) or len(target) != 3 or not all(isinstance(v, str) for v in target):
            raise ValueError('Target must be an exact owner/name/descriptor triple')
        normalized.add(tuple(target))
    if not normalized:
        raise ValueError('At least one declared target is required')
    results = []
    for owner, name, descriptor in sorted(normalized):
        kind = 'methods' if descriptor.startswith('(') else 'fields'
        if (owner, name, descriptor) not in declarations[kind]:
            raise ValueError('Target is not declared in this artifact: ' + repr((owner, name, descriptor)))
        results.append(dict(owner=owner, name=name, descriptor=descriptor, kind=kind, declaration_present=True))
    return results

def validate_inventory_targets(targets, declarations):
    if not isinstance(targets, list):
        raise ValueError('No supported targets list')
    if targets and all(isinstance(t, str) for t in targets):
        missing = sorted(set(targets) - declarations['classes'])
        if missing:
            raise ValueError('Class targets absent from artifact: ' + repr(missing))
        return [dict(owner=t, kind='classes', declaration_present=True) for t in sorted(set(targets))]
    return validate_targets(targets, declarations)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jar', required=True)
    ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    choice = ap.add_mutually_exclusive_group(required=True)
    choice.add_argument('--evidence', action='append')
    choice.add_argument('--audit-target-inventories', action='store_true')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    raw = Path(args.jar).read_bytes()
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != SHA:
        raise SystemExit('Wrong exact artifact')
    root = Path(args.root).resolve()
    paths = sorted(root.glob('*EVIDENCE-*.json')) if args.audit_target_inventories else [root / name for name in args.evidence]
    with zipfile.ZipFile(args.jar) as archive:
        declarations = declaration_index(archive)
    checked, failed, skipped = [], [], []
    for path in paths:
        if path.resolve().parent != root:
            raise SystemExit('Evidence resolves outside research root')
        data = json.loads(path.read_text())
        targets = data.get('targets') if isinstance(data, dict) else None
        if targets is None and args.audit_target_inventories:
            skipped.append(path.name)
            continue
        try:
            if not isinstance(targets, list):
                raise ValueError('No supported targets list')
            artifact = data.get('artifact', {})
            declared_sha = data.get('artifact_sha256', artifact.get('sha256') if isinstance(artifact, dict) else None)
            if declared_sha != SHA:
                raise ValueError('Inventory does not declare the fixed artifact')
            checks = validate_inventory_targets(targets, declarations)
            checked.append(dict(evidence=path.name, evidence_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), targets=checks))
        except ValueError as exc:
            failed.append(dict(evidence=path.name, reason=str(exc)))
    report = dict(scope='DECLARED_TARGET_EXISTENCE_ONLY_NOT_CALL_CLOSURE_OR_SEMANTIC_REVIEW',
                  artifact_sha256=SHA, validator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  class_count=declarations['class_count'], checked=checked, failures=failed, status='FAIL' if failed else 'PASS',
                  files_without_target_inventory_skipped=skipped, target_executed=False, source_scanned=False)
    Path(args.out).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(inventories=len(checked), declared_target_rows=sum(len(x['targets']) for x in checked), failures=len(failed))))
    if failed:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
