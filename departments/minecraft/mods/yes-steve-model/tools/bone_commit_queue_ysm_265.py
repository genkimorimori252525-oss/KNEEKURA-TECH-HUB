#!/usr/bin/env python3
"""Hash-fixed bone/queue evidence audit. Static parsing only; no target execution.

Snapshot/operand/closure checks reject corrupt evidence. Semantic prose still
requires human/independent review; callee behavior is not implied by call identity.
"""
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
REVISION = 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'
BASE = 'com/elfmcys/yesstevemodel/'
OWNERS = [BASE + s for s in (
    'oOO0o0oOOOoOoo00oOO0Oo00', 'O0oOOO0o0OoO0Oo0OOOoOoOo',
    'OO00000oOOOoO0o00o00OOo0', 'oooO000oOoOooooOooo00oOO',
    'O0OO0Oo0Oo0O0oOO0OOoO000',
    'O00Oo0oo0Ooo0oOOOo0OO0oO$o0OOooo0o0OO00OoOOOo0o0O',
    'oo000oooo0OOoo00O0o0OOOO$Oo0Oo0o00O00Oo0OOoOOoooo',
    'oo0Oo0O00oooOoOo0O0oOOOo$Oo0Oo0o00O00Oo0OOoOOoooo')]
BONE = BASE + 'Oo0o00oOOo0OO000000O0oO0'
PROCESSOR = BASE + 'OOOooo0o0OOOO0O0OOoOo0OO'
IDS_SHA = 'f81e1b4978e46de8c0b27103fba6a23c9b276b2a0aef9ac5b256463fa5e9c634'
SOURCES_SHA = '4408ddc09d898d49c3efd2a569893a60e426f33df6be81e4967705bbabbd5d8e'
LINKS_SHA = '1f60e4df72981932270013e8aeeffc48f2f4783e395d9dfef0f6cfb8cffc5fe3'
METHOD_KEYS = ('access', 'code_sha256', 'instructions', 'supplemental_full_operand_records', 'exception_handlers')
DECL_KEYS = ('access', 'super', 'interfaces', 'fields', 'methods')


def digest(value, sort_keys=False):
    return hashlib.sha256(json.dumps(value, sort_keys=sort_keys, separators=(',', ':')).encode()).hexdigest()


def identity(row):
    return tuple(row.get(k) for k in ('owner', 'name', 'descriptor'))


def audit(evidence, actual, declarations, details, callers):
    checks = []
    def check(name, passed):
        checks.append({'check': name, 'pass': bool(passed)})
    check('fixed-artifact', evidence.get('artifact', {}).get('sha256') == SHA
          and evidence.get('artifact', {}).get('size') == SIZE)
    check('full-operands-enabled', evidence.get('detailed_operands') is True)
    rows = evidence.get('members', []) + evidence.get('bounded_dependency_support', [])
    ids = [identity(row) for row in rows]
    check('complete-53-method-identities', len(ids) == len(set(ids)) == 53
          and set(ids) == set(actual) and digest(sorted(ids)) == IDS_SHA)
    check('thirteen-reviewed-forty-support', len(evidence.get('members', [])) == 13
          and len(evidence.get('bounded_dependency_support', [])) == 40)
    for row in rows:
        observed = actual.get(identity(row), {})
        check(str(identity(row)) + ':exists', bool(observed))
        for key in METHOD_KEYS:
            # Abstract interface methods must have NO fabricated Code data.
            check(str(identity(row)) + ':' + key,
                  (key in row) == (key in observed) and row.get(key) == observed.get(key))
    decls = evidence.get('owner_declarations', [])
    check('eight-owner-declarations', len(decls) == 8 and {r['owner'] for r in decls} == set(OWNERS))
    for row in decls:
        observed = declarations.get(row['owner'], {})
        check(row['owner'] + ':full-declaration', row.get('declaration') == observed)
    bone = evidence.get('bone_interface_declaration', {})
    check('bone-interface-declaration', bone.get('owner') == BONE and bone.get('declaration') == declarations[BONE])
    boots = evidence.get('bootstrap_and_constant_evidence', [])
    check('eight-owner-bootstrap-records', len(boots) == 8 and {r['owner'] for r in boots} == set(OWNERS))
    for row in boots:
        for key in ('constant_values', 'bootstrap_methods'):
            check(row['owner'] + ':' + key, key in row and row[key] == details.get(row['owner'], {}).get(key))
    links = evidence.get('boundary_links', [])
    check('complete-ten-boundary-links', len(links) == 10 and digest(links, True) == LINKS_SHA)
    for link in links:
        caller = link['caller']
        m = callers.get(identity(caller), {})
        matches = [op for op in m.get('instructions', []) if op['offset'] == link['offset']]
        expected = {k: link[k] for k in ('offset', 'opcode', 'reference')}
        check('boundary:' + str(identity(caller)) + '@' + str(link['offset']),
              caller.get('access') == m.get('access') and matches == [expected])
    tracks = evidence.get('source_tracks', [])
    check('nine-fixed-source-records', len(tracks) == 9
          and digest(sorted((r.get('path'), r.get('sha256')) for r in tracks)) == SOURCES_SHA
          and all(r.get('revision') == REVISION for r in tracks))
    return checks


def negative_controls(evidence, actual, declarations, details, callers):
    results = []
    def member(e, role, owner=None):
        return next(m for m in e['members'] if m['semantic_member'] == role
                    and (owner is None or m['owner'] == owner))
    def op(e, role, offset, owner=None):
        return next(o for o in member(e, role, owner)['instructions'] if o['offset'] == offset)
    def run(name, mutate):
        e = copy.deepcopy(evidence)
        mutate(e)
        failures = [c['check'] for c in audit(e, actual, declarations, details, callers) if not c['pass']]
        results.append({'control': name, 'rejected': bool(failures), 'failed_checks': failures})
    run('wrong-artifact', lambda e: e['artifact'].update(sha256='0'*64))
    run('missing-commit', lambda e: e['members'].pop(0))
    run('missing-support-method', lambda e: e['bounded_dependency_support'].pop())
    run('missing-instructions', lambda e: member(e, 'commit').pop('instructions'))
    run('missing-owner-declaration', lambda e: e['owner_declarations'].pop())
    run('missing-bootstrap-owner', lambda e: e['bootstrap_and_constant_evidence'].pop())
    run('missing-boundary-call', lambda e: e['boundary_links'].pop())
    run('missing-source-record', lambda e: e['source_tracks'].pop())
    run('rotation-add-to-subtract', lambda e: op(e, 'commit', 42).update(opcode='0x66'))
    run('cached-reset-zero-to-one', lambda e: op(e, 'commit', 190).update(opcode='0xc'))
    run('invent-commit-handler', lambda e: member(e, 'commit')['exception_handlers'].append(
        dict(start=0, end=186, handler=186, catch=None)))
    run('minimum-nan-direction', lambda e: op(e, 'setEndingTransitionPercentProgressIfLess', 5).update(opcode='0x95'))
    run('apply-zero-branch', lambda e: op(e, 'apply', 8).update(opcode='0x99'))
    run('rotation-destination-alias', lambda e: op(e, 'applyRotation', 24).update(opcode='0x2c'))
    run('single-null-gate', lambda e: op(e, 'pollRotationPoint', 9, OWNERS[6]).update(opcode='0xc6'))
    run('blend-condition-polarity', lambda e: op(e, 'pollRotationPoint', 69, OWNERS[5]).update(opcode='0x99'))
    run('blend-epsilon-boundary', lambda e: op(e, 'pollRotationPoint', 265, OWNERS[5]).update(opcode='0x9b'))
    run('scale-weighted-helper', lambda e: op(e, 'pollScalePoint', 105, OWNERS[6])['reference'].update(name='wrong'))
    run('vehicle-empty-to-null', lambda e: op(e, 'pollPositionPoint', 0, OWNERS[7]).update(opcode='0x1'))
    return results


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
    actual, declarations, callers = {}, {}, {}
    with zipfile.ZipFile(args.jar) as archive:
        for owner in OWNERS + [BONE]:
            raw_class = archive.read(owner + '.class')
            decl = parse_class(raw_class)
            declarations[owner] = {k: decl[k] for k in DECL_KEYS}
            if owner in OWNERS:
                for row in parse_bounded(raw_class, True):
                    actual[identity(row)] = row
        for row in parse_bounded(archive.read(PROCESSOR + '.class'), True):
            callers[identity(row)] = row
    details = copy.deepcopy(BOUNDDETAILS)
    checks = audit(evidence, actual, declarations, details, callers)
    source = Path(args.source_root).resolve()
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    checks.append({'check': 'pinned-source-revision', 'pass': revision == REVISION})
    for row in evidence.get('source_tracks', []):
        p = (source / row['path']).resolve()
        ok = p.is_relative_to(source) and p.is_file()
        checks.append({'check': 'source:' + row['path'], 'pass': ok and hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256']})
    negatives = negative_controls(evidence, actual, declarations, details, callers)
    result = {'artifact_sha256': SHA, 'checks': checks, 'negative_controls': negatives,
              'failures': [c for c in checks if not c['pass']],
              'negative_failures': [c for c in negatives if not c['rejected']],
              'runtime_executed': False,
              'limit': 'Full snapshots and boundary identity checks are not proofs of semantic prose or whole-callee equivalence.'}
    Path(args.out).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'checks': len(checks), 'negative_controls': len(negatives),
                      'failures': len(result['failures']) + len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
