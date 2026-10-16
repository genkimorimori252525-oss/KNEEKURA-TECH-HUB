#!/usr/bin/env python3
"""Hash-fixed static binary-evaluator audit and bounded corrupt-evidence controls.

No JVM execution, source compilation, native extraction or model decryption.
The existing auditor checks declarations and full bytecode records; this companion
also joins retained enum names via explicit index arguments to array slots and
LambdaMetafactory implementation handles. Labels remain reviewed semantic claims.
"""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded, BOUNDDETAILS

OWNER = 'com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO'
ARTIFACT_SHA256 = '25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
ARTIFACT_SIZE = 63269843
MEMBER_IDENTITIES_SHA256 = '571c5d51f20824db8511a9ab0e0bb52598599ec48e41f43a7366765a54eed5b8'
SUPPORT_IDENTITIES_SHA256 = 'd7f83d5a5ee8d8575e141419cf0b58376095e87616ce08ddbb54d876a057dc05'
ENUM = 'com/elfmcys/yesstevemodel/oo00OOOoo00000Oo0Oooo0Oo$Oo0Oo0o00O00Oo0OOoOOoooo'


def ident(m):
    return tuple(m[k] for k in ('owner', 'name', 'descriptor'))


def integer(op):
    code = int(op['opcode'], 16)
    if 2 <= code <= 8:
        return code - 3
    if code in (0x10, 0x11):
        return op['immediate']
    raise ValueError('Expected encoded integer constant')


def scoped_checks(evidence, actual, bootstraps):
    checks = []
    def check(name, passed):
        checks.append({'check': name, 'pass': bool(passed)})
    for key, expected, count in [('members', MEMBER_IDENTITIES_SHA256, 20),
                                 ('bounded_dependency_support', SUPPORT_IDENTITIES_SHA256, 20)]:
        fingerprint = hashlib.sha256(json.dumps(sorted(ident(m) for m in evidence.get(key, [])),
                                               separators=(',', ':')).encode()).hexdigest()
        check(key + ':exact-cohort-identity-set', fingerprint == expected and len(evidence.get(key, [])) == count)
    links = [(ident(l['caller']), l['offset']) for row in evidence.get('bootstrap_member_connections', []) for l in row.get('links', [])]
    link_fingerprint = hashlib.sha256(json.dumps(sorted(links), separators=(',', ':')).encode()).hexdigest()
    check('exact-25-bootstrap-callsites', len(links) == 25 and link_fingerprint == '630c71d6a75b449a335d1129d4343a9d0b081b555128b846e6a5da6101deb972')
    fields = evidence.get('field_mapping_candidates', [])
    check('exact-table-field-candidate', len(fields) == 1 and fields[0].get('mapping_id') == 'ysm265.field.expression-evaluator-impl-binary-evaluators')
    check('exact-16-table-rows', len(evidence.get('operator_table', [])) == 16)
    for row in evidence['members'] + evidence['bounded_dependency_support']:
        observed = actual.get(ident(row), {})
        for key in ('access', 'instructions', 'supplemental_full_operand_records',
                    'exception_handlers', 'code_sha256'):
            check(str(ident(row)) + ':' + key, key in row and row[key] == observed.get(key))
    init = actual[(OWNER, '<clinit>', '()V')]['instructions']
    enum_init = actual[(ENUM, '<clinit>', '()V')]['instructions']
    check('exact-16-array-length', integer(init[0]) == 16)
    stores = [op['reference'] for op in init if op['opcode'] == '0xb3']
    check('table-field-matches-initializer-store', len(fields) == 1 and len(stores) == 1
          and all(fields[0].get(k) == stores[0].get(k) for k in ('owner', 'name', 'descriptor'))
          and fields[0].get('access') == 26)
    seen = []
    for row in evidence['operator_table']:
        label = row['operation']
        names = [i for i, op in enumerate(enum_init)
                 if op.get('reference', {}).get('string') == label]
        check(label + ':unique-retained-name', len(names) == 1)
        if len(names) != 1:
            continue
        p = names[0]
        # Constructor descriptor is String + ordinal + precedence + explicit index.
        constructor = enum_init[p + 4]
        index = integer(enum_init[p + 3])
        check(label + ':explicit-index', index == row['index'])
        check(label + ':enum-constructor', constructor['offset'] == row['enum_constructor_offset']
              and constructor['reference']['descriptor'] == '(Ljava/lang/String;III)V')
        check(label + ':enum-name-field', enum_init[p]['offset'] == row['enum_name_offset']
              and enum_init[p + 5]['opcode'] == '0xb3'
              and enum_init[p + 5]['reference'] == row['enum_field'])
        sites = [i for i, op in enumerate(init) if op['opcode'] == '0xba'
                 and integer(init[i - 1]) == index]
        check(label + ':unique-array-slot', len(sites) == 1)
        if len(sites) != 1:
            continue
        q = sites[0]
        site = init[q]
        after = q + 2 if init[q + 1]['opcode'] == '0xb8' else q + 1
        check(label + ':slot-store', init[q - 2]['opcode'] == '0x59'
              and init[after]['opcode'] == '0x53')
        check(label + ':slot-callsite', site['offset'] == row['clinit_callsite_offset']
              and site['reference']['bootstrap_index'] == row['bootstrap_index'])
        boot = bootstraps[site['reference']['bootstrap_index']]
        check(label + ':lambda-metafactory', boot['method_handle']['reference']['owner']
              == 'java/lang/invoke/LambdaMetafactory')
        handles = [x['reference'] for x in boot['arguments'] if x.get('cp_tag') == 15]
        check(label + ':slot-implementation', len(handles) == 1
              and ident(handles[0]) == ident(row['implementation']))
        members = [m for m in evidence['members'] if m['mapping_id'] == row['mapping_id']]
        check(label + ':mapping-implementation', len(members) == 1
              and ident(members[0]) == ident(row['implementation']))
        seen.append(index)
    check('all-16-distinct-slots', sorted(seen) == list(range(16)))
    return checks


def controls(evidence, actual, bootstraps):
    results = []
    def run(name, mutate):
        modified = copy.deepcopy(evidence)
        mutate(modified)
        failed = [c['check'] for c in scoped_checks(modified, actual, bootstraps) if not c['pass']]
        results.append({'control': name, 'rejected': bool(failed), 'failed_checks': failed})
    def member(e, role):
        return next(m for m in e['members'] if m['semantic_member'] == role)
    def instruction(e, role, offset):
        return next(o for o in member(e, role)['instructions'] if o['offset'] == offset)
    run('enum-index-to-wrong-slot', lambda e: e['operator_table'][0].update(index=1))
    run('slot-to-wrong-implementation', lambda e: e['operator_table'][0].update(
        implementation=copy.deepcopy(e['operator_table'][1]['implementation'])))
    run('and-branch-polarity', lambda e: instruction(e, 'binaryAnd', 6).update(opcode='0x9a'))
    run('or-short-circuit-target', lambda e: instruction(e, 'binaryOr', 6).update(branch_target=22))
    run('lt-nan-compare-polarity', lambda e: instruction(e, 'binaryLt', 12).update(opcode='0x95'))
    run('division-zero-guard', lambda e: instruction(e, 'binaryDiv', 17).update(branch_target=20))
    run('division-arithmetic-opcode', lambda e: instruction(e, 'binaryDiv', 24).update(opcode='0x6a'))
    run('assignment-rhs-first-local', lambda e: instruction(e, 'binaryAssign', 0).update(opcode='0x2b'))
    def arrow(e):
        m = member(e, 'binaryArrow')
        next(o for o in m['supplemental_full_operand_records'] if o['offset'] == 32).update(
            encoded_operands_hex='00', local_index=0)
    run('arrow-return-copy-source-local', arrow)
    def add_order(e):
        ops = member(e, 'binaryAdd')['instructions']
        a = next(i for i, o in enumerate(ops) if o['offset'] == 10)
        b = next(i for i, o in enumerate(ops) if o['offset'] == 18)
        ops[a]['reference'], ops[b]['reference'] = ops[b]['reference'], ops[a]['reference']
    run('add-convert-before-second-visit', add_order)
    run('missing-assign-instructions', lambda e: member(e, 'binaryAssign').pop('instructions'))
    run('missing-support-thunk-row', lambda e: e['bounded_dependency_support'].pop(3))
    run('missing-operator-row', lambda e: e['operator_table'].pop())
    run('missing-bootstrap-link', lambda e: e['bootstrap_member_connections'][0]['links'].pop())
    run('missing-table-field', lambda e: e['field_mapping_candidates'].clear())
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jar', required=True)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    evidence = json.loads(Path(args.evidence).read_text())
    raw = Path(args.jar).read_bytes()
    if (hashlib.sha256(raw).hexdigest() != ARTIFACT_SHA256
            or len(raw) != ARTIFACT_SIZE
            or evidence['artifact']['sha256'] != ARTIFACT_SHA256
            or evidence['artifact']['size'] != ARTIFACT_SIZE):
        raise SystemExit('Wrong artifact hash or size')
    owners = {m['owner'] for m in evidence['members'] + evidence['bounded_dependency_support']}
    actual = {}
    with zipfile.ZipFile(args.jar) as archive:
        for owner in owners:
            for method in parse_bounded(archive.read(owner + '.class'), True):
                actual[ident(method)] = method
    bootstraps = BOUNDDETAILS[OWNER]['bootstrap_methods']
    with tempfile.TemporaryDirectory(prefix='ysm-binary-audit-') as tmp:
        base_out = Path(tmp) / 'base.json'
        process = subprocess.run([sys.executable,
            str(Path(__file__).with_name('audit_seed_recovery_ysm_265.py')),
            '--jar', args.jar, '--evidence', args.evidence, '--out', str(base_out)],
            capture_output=True, text=True)
        if not base_out.exists():
            raise SystemExit(process.stderr or process.stdout)
        base = json.loads(base_out.read_text())
    checks = scoped_checks(evidence, actual, bootstraps)
    negatives = controls(evidence, actual, bootstraps)
    result = dict(artifact_sha256=evidence['artifact']['sha256'],
        base_checks=len(base['checks']), base_failures=base['failures'],
        relation_and_scoped_checks=checks, failures=[c for c in checks if not c['pass']],
        negative_controls=negatives, negative_failures=[n for n in negatives if not n['rejected']],
        runtime_executed=False)
    Path(args.out).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(base_checks=len(base['checks']), scoped_checks=len(checks),
                         negative_controls=len(negatives), failures=len(base['failures'])
                         + len(result['failures']) + len(result['negative_failures']))))
    if process.returncode or result['failures'] or result['negative_failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
