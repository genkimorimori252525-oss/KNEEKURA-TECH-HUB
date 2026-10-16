#!/usr/bin/env python3
"""Static processor snapshot regression checks; does not execute the MOD or prove prose."""
import argparse
import copy
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded, BOUNDDETAILS

SHA = '25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE = 63269843
OWNER = 'com/elfmcys/yesstevemodel/OOOooo0o0OOOO0O0OOoOo0OO'
INNER = OWNER + '$Oo0Oo0o00O00Oo0OOoOOoooo'
REVISION = 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'
KEYS = ('access', 'instructions', 'supplemental_full_operand_records', 'exception_handlers', 'code_sha256')


def identity(row):
    return tuple(row.get(k) for k in ('owner', 'name', 'descriptor'))


def audit(evidence, actual, details):
    checks = []
    def check(name, ok):
        checks.append({'check': name, 'pass': bool(ok)})
    check('fixed-artifact', evidence.get('artifact', {}).get('sha256') == SHA
          and evidence.get('artifact', {}).get('size') == SIZE)
    check('full-operands-enabled', evidence.get('detailed_operands') is True)
    rows = evidence.get('members', []) + evidence.get('bounded_dependency_support', [])
    ids = [identity(m) for m in rows]
    check('all-27-method-identities-exact-once', len(ids) == len(set(ids)) == 27 and set(ids) == set(actual))
    for row in rows:
        key = identity(row)
        observed = actual.get(key, {})
        for field in KEYS:
            check(str(key) + ':' + field, field in row and row[field] == observed.get(field))
    expected = {r.get('owner'): r for r in evidence.get('bootstrap_and_constant_evidence', [])}
    check('both-owner-bootstrap-records', len(evidence.get('bootstrap_and_constant_evidence', [])) == 2
          and set(expected) == {OWNER, INNER})
    for owner in (OWNER, INNER):
        for field in ('bootstrap_methods', 'constant_values'):
            check(owner + ':' + field, field in expected.get(owner, {})
                  and expected[owner][field] == details[owner][field])
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jar', required=True)
    ap.add_argument('--evidence', required=True)
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    raw = Path(args.jar).read_bytes()
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != SHA:
        raise SystemExit('Wrong fixed artifact')
    evidence = json.loads(Path(args.evidence).read_text())
    actual = {}
    with zipfile.ZipFile(args.jar) as z:
        for owner in (OWNER, INNER):
            for row in parse_bounded(z.read(owner + '.class'), True):
                actual[identity(row)] = row
    details = copy.deepcopy(BOUNDDETAILS)
    checks = audit(evidence, actual, details)
    root = Path(args.source_root).resolve()
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    checks.append({'check': 'pinned-source-revision', 'pass': revision == REVISION})
    source_rows = evidence.get('source_tracks', [])
    expected_path = 'src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/processor/AnimationProcessor.java'
    checks.append({'check': 'exact-source-record', 'pass': len(source_rows) == 1
                   and source_rows[0].get('path') == expected_path
                   and source_rows[0].get('revision') == REVISION})
    for row in source_rows:
        path = (root / row['path']).resolve()
        ok = path.is_relative_to(root) and path.is_file()
        checks.append({'check': 'source-sha256', 'pass': ok and hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']})
    negatives = []
    def member(e, role):
        return next(m for m in e['members'] if m['semantic_member'] == role)
    def change_op(e, role, offset, **kwargs):
        next(o for o in member(e, role)['instructions'] if o['offset'] == offset).update(kwargs)
    def control(name, mutate):
        e = copy.deepcopy(evidence)
        mutate(e)
        failed = [c['check'] for c in audit(e, actual, details) if not c['pass']]
        negatives.append({'control': name, 'rejected': bool(failed)})
    control('wrong-fixed-artifact', lambda e: e['artifact'].update(sha256='0'*64))
    control('missing-processor-method', lambda e: e['members'].pop())
    control('missing-task-record-method', lambda e: e['bounded_dependency_support'].pop())
    control('missing-instructions', lambda e: member(e, 'executeMolangTask').pop('instructions'))
    control('should-tick-branch-target', lambda e: change_op(e, 'tickAnimation', 153, branch_target=199))
    control('pre-post-polarity', lambda e: change_op(e, 'preProcess', 31, opcode='0x9a'))
    control('task-handler-removed', lambda e: member(e, 'executeMolangTask')['exception_handlers'].pop())
    control('callback-null-branch', lambda e: change_op(e, 'executeMolangTask', 32, branch_target=149))
    control('callback-outside-handler-falsified', lambda e: member(e, 'executeMolangTask')['exception_handlers'][0].update(end=159))
    control('cleanup-false-to-true', lambda e: change_op(e, 'executeMolangTask', 124, opcode='0x4'))
    control('bootstrap-record-omitted', lambda e: e['bootstrap_and_constant_evidence'].pop())
    result = {'artifact_sha256': SHA, 'checks': checks, 'negative_controls': negatives,
              'failures': [c for c in checks if not c['pass']],
              'negative_failures': [c for c in negatives if not c['rejected']],
              'runtime_executed': False, 'independent_semantic_review': 'NOT_RUN',
              'limit': 'Snapshot/operand regression detects evidence corruption; semantic prose requires separate review.'}
    Path(args.out).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'checks': len(checks), 'negative_controls': len(negatives),
                      'failures': len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
