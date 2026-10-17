#!/usr/bin/env python3
"""Fixed-JAR Keyframe producer static snapshots, source provenance and negative controls."""
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
OWNERS = [PREFIX + x for x in ('OOOo0OooOOoOooooooo000O0', 'OooOo0o00OO00O000oOOo0O0',
    'OO000ooOooO0Ooooooo000Oo', 'OO0O0OoO000OoOo0OO00O0OO', 'o0oO0ooOo0o0OOO0oo0Ooooo')]
SOURCE_SET_SHA = '3e4879c370f770ae84c9e2384c871c48f914f33c0902f3ec93ac1c1b45f441b2'
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
    check('complete-sixteen-methods', len(ids) == len(set(ids)) == 16 and set(ids) == set(actual))
    check('seven-reviewed-nine-support', len(evidence.get('members', [])) == 7
          and len(evidence.get('bounded_dependency_support', [])) == 9)
    for row in rows:
        observed = actual.get(identity(row), {})
        check(str(identity(row)) + ':present', bool(observed))
        for field in KEYS:
            check(str(identity(row)) + ':' + field,
                  (field in row) == (field in observed) and row.get(field) == observed.get(field))
    ds = evidence.get('owner_declarations', [])
    check('five-complete-owners', len(ds) == 5 and {r['owner'] for r in ds} == set(OWNERS))
    for row in ds:
        check(row['owner'] + ':declaration', row.get('declaration') == declarations.get(row['owner']))
    bs = evidence.get('bootstrap_and_constant_evidence', [])
    check('five-bootstrap-records', len(bs) == 5 and {r['owner'] for r in bs} == set(OWNERS))
    for row in bs:
        for field in ('constant_values', 'bootstrap_methods'):
            check(row['owner'] + ':' + field, field in row and row[field] == details[row['owner']][field])
    ss = evidence.get('source_tracks', [])
    digest = hashlib.sha256(json.dumps(sorted((r.get('path'), r.get('sha256')) for r in ss), separators=(',', ':')).encode()).hexdigest()
    check('five-fixed-sources', len(ss) == 5 and digest == SOURCE_SET_SHA
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
    run('missing-instructions', lambda e: member(e, 0, 'isBegin').pop('instructions'))
    run('missing-owner', lambda e: e['owner_declarations'].pop())
    run('missing-source', lambda e: e['source_tracks'].pop())
    run('missing-bootstrap', lambda e: e['bootstrap_and_constant_evidence'].pop())
    run('begin-missing-double-promotion', lambda e: op(e, 0, 'isBegin', 1).update(opcode='0x0'))
    run('begin-nan-comparison-flipped', lambda e: op(e, 0, 'isBegin', 5).update(opcode='0x97'))
    run('begin-strict-branch-flipped', lambda e: op(e, 0, 'isBegin', 6).update(opcode='0x9d'))
    run('end-strict-branch-flipped', lambda e: op(e, 0, 'isEnd', 4).update(opcode='0x9b'))
    run('transition-end-gate-flipped', lambda e: op(e, 1, 'getLerpPoint', 4).update(opcode='0x99'))
    run('transition-destination-reference', lambda e: op(e, 1, 'getTransitionDst', 1)['reference'].update(name='wrong'))
    run('linear-begin-gate-flipped', lambda e: op(e, 2, 'getLerpPoint', 4).update(opcode='0x9a'))
    run('linear-end-field-reference', lambda e: op(e, 2, 'getLerpPoint', 24)['reference'].update(name='wrong'))
    run('catmull-first-value-reference', lambda e: op(e, 3, 'getLerpPoint', 33)['reference'].update(name='wrong'))
    run('catmull-delegate-reference', lambda e: op(e, 3, 'getLerpPoint', 79)['reference'].update(name='wrong'))
    run('vector-middle-component-reference', lambda e: op(e, 4, 'eval', 15)['reference'].update(name='wrong'))
    run('vector-last-evaluation-reference', lambda e: op(e, 4, 'eval', 29)['reference'].update(name='wrong'))
    run('invent-local-catch', lambda e: member(e, 4, 'eval')['exception_handlers'].append(
        dict(start=0, end=34, handler=34, catch=None)))
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
    checks.append({'check': 'three-direct-subclasses-in-exact-jar', 'pass': subclasses == sorted(OWNERS[1:4])})
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
              'limit': 'Snapshots/operands verify evidence; semantic roles require independent review. Factory selection and external value evaluation remain delegated.'}
    Path(a.out).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'checks': len(checks), 'negative_controls': len(negatives),
                      'failures': len(result['failures']) + len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
