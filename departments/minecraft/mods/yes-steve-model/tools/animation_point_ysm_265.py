#!/usr/bin/env python3
"""Fixed-JAR AnimationPoint static snapshots, source provenance and negative controls."""
import argparse
import copy
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from scan_ysm_265 import parse_class
from audit_seed_recovery_ysm_265 import parse_bounded, BOUNDDETAILS

SHA = '25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE = 63269843
REV = 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'
PREFIX = 'com/elfmcys/yesstevemodel/'
OWNERS = [PREFIX + x for x in ('oO0O00Oo00o00OO0o0OOOOOO', 'O0O0O00OOO0o00o00ooooOo0',
                               'Oo0oooOOoo00ooOO00OO0OO0', 'O00ooo0O0Ooo0OOO0oo00o0o')]
SOURCE_SET_SHA = 'ba79cb5c48ca51be28531664a5e18c3091a7156dd36f33254a722e5ccf8682c6'
KEYS = ('access', 'instructions', 'supplemental_full_operand_records', 'exception_handlers', 'code_sha256')
DECL_KEYS = ('access', 'super', 'interfaces', 'fields', 'methods')


def identity(row):
    return tuple(row.get(k) for k in ('owner', 'name', 'descriptor'))


def audit(evidence, actual, declarations, details):
    checks = []
    def check(label, passed):
        checks.append({'check': label, 'pass': bool(passed)})
    check('fixed-artifact', evidence.get('artifact', {}).get('sha256') == SHA
          and evidence.get('artifact', {}).get('size') == SIZE)
    check('full-operands', evidence.get('detailed_operands') is True)
    rows = evidence.get('members', []) + evidence.get('bounded_dependency_support', [])
    ids = [identity(row) for row in rows]
    check('complete-fourteen-methods', len(ids) == len(set(ids)) == 14 and set(ids) == set(actual))
    check('seven-reviewed-seven-support', len(evidence.get('members', [])) == 7
          and len(evidence.get('bounded_dependency_support', [])) == 7)
    for row in rows:
        observed = actual.get(identity(row), {})
        check(str(identity(row)) + ':present', bool(observed))
        for field in KEYS:
            check(str(identity(row)) + ':' + field,
                  (field in row) == (field in observed) and row.get(field) == observed.get(field))
    ds = evidence.get('owner_declarations', [])
    check('four-complete-owners', len(ds) == 4 and {r['owner'] for r in ds} == set(OWNERS))
    for row in ds:
        check(row['owner'] + ':declaration', row.get('declaration') == declarations.get(row['owner']))
    bs = evidence.get('bootstrap_and_constant_evidence', [])
    check('four-bootstrap-records', len(bs) == 4 and {r['owner'] for r in bs} == set(OWNERS))
    for row in bs:
        for field in ('constant_values', 'bootstrap_methods'):
            check(row['owner'] + ':' + field, field in row and row[field] == details[row['owner']][field])
    ss = evidence.get('source_tracks', [])
    digest = hashlib.sha256(json.dumps(sorted((r.get('path'), r.get('sha256')) for r in ss), separators=(',', ':')).encode()).hexdigest()
    check('four-fixed-sources', len(ss) == 4 and digest == SOURCE_SET_SHA
          and all(r.get('revision') == REV for r in ss))
    return checks


def controls(evidence, actual, declarations, details):
    result = []
    def member(e, owner, role):
        return next(m for m in e['members'] if m['owner'] == OWNERS[owner] and m['semantic_member'] == role)
    def op(e, owner, role, offset):
        return next(o for o in member(e, owner, role)['instructions'] if o['offset'] == offset)
    def run(name, mutate):
        e = copy.deepcopy(evidence)
        mutate(e)
        fail = [c['check'] for c in audit(e, actual, declarations, details) if not c['pass']]
        result.append({'control': name, 'rejected': bool(fail), 'failed_checks': fail})
    run('wrong-artifact', lambda e: e['artifact'].update(sha256='0'*64))
    run('missing-method', lambda e: e['members'].pop())
    run('missing-abstract-support', lambda e: e['bounded_dependency_support'].pop(1))
    run('missing-instructions', lambda e: member(e, 0, 'getPercentCompleted').pop('instructions'))
    run('missing-owner', lambda e: e['owner_declarations'].pop())
    run('missing-source', lambda e: e['source_tracks'].pop())
    run('missing-bootstrap', lambda e: e['bootstrap_and_constant_evidence'].pop())
    run('base-zero-returns-zero', lambda e: op(e, 0, 'getPercentCompleted', 9).update(opcode='0xb'))
    run('ending-zero-zero-returns-one', lambda e: op(e, 2, 'getPercentCompleted', 18).update(opcode='0xc'))
    run('ending-nonzero-total-branch', lambda e: op(e, 2, 'getPercentCompleted', 6).update(opcode='0x99'))
    run('setup-context-reference', lambda e: op(e, 0, 'setupAnimationContext', 13)['reference'].update(name='wrong'))
    run('begin-cache-null-branch', lambda e: op(e, 1, 'getLerpPoint', 31).update(opcode='0xc6'))
    run('begin-interpolation-dst-alias', lambda e: op(e, 1, 'getLerpPoint', 23).update(opcode='0x2b'))
    run('ending-return-wrong-field', lambda e: op(e, 2, 'getLerpPoint', 38)['reference'].update(name='O00OOOooOoooOoo0o0o0oO0O'))
    run('keyframe-evaluation-target', lambda e: op(e, 3, 'getLerpPoint', 14)['reference'].update(name='wrong'))
    run('invent-context-finally-handler', lambda e: member(e, 1, 'getLerpPoint')['exception_handlers'].append(
        dict(start=0, end=27, handler=27, catch=None)))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('jar', 'evidence', 'source-root', 'out'):
        p.add_argument('--' + flag, required=True)
    a = p.parse_args()
    raw = Path(a.jar).read_bytes()
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != SHA:
        raise SystemExit('Wrong fixed artifact')
    e = json.loads(Path(a.evidence).read_text())
    actual, declarations = {}, {}
    with zipfile.ZipFile(a.jar) as z:
        for owner in OWNERS:
            data = z.read(owner + '.class')
            decl = parse_class(data)
            declarations[owner] = {k: decl[k] for k in DECL_KEYS}
            for m in parse_bounded(data, True):
                actual[identity(m)] = m
        all_classes = [parse_class(z.read(n)) for n in z.namelist()
                       if n.endswith('.class') and not n.startswith('META-INF/versions/')]
    details = copy.deepcopy(BOUNDDETAILS)
    checks = audit(e, actual, declarations, details)
    subclasses = sorted(c['name'] for c in all_classes if c['super'] == OWNERS[0])
    checks.append({'check': 'three-direct-subclasses-in-exact-jar', 'pass': subclasses == sorted(OWNERS[1:])})
    root = Path(a.source_root).resolve()
    rev = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    checks.append({'check': 'pinned-source-revision', 'pass': rev == REV})
    for row in e.get('source_tracks', []):
        f = (root / row['path']).resolve()
        ok = f.is_relative_to(root) and f.is_file()
        checks.append({'check': 'source:' + row['path'], 'pass': ok and hashlib.sha256(f.read_bytes()).hexdigest() == row['sha256']})
    negatives = controls(e, actual, declarations, details)
    result = {'artifact_sha256': SHA, 'checks': checks, 'negative_controls': negatives,
              'failures': [c for c in checks if not c['pass']],
              'negative_failures': [c for c in negatives if not c['rejected']],
              'runtime_executed': False, 'direct_subclasses': subclasses,
              'limit': 'Snapshots/operands verify evidence; semantic roles require independent review. Keyframe generation and external easing remain delegated.'}
    Path(a.out).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'checks': len(checks), 'negative_controls': len(negatives),
                      'failures': len(result['failures']) + len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
