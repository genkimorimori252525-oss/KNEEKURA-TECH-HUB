#!/usr/bin/env python3
"""Audit immutable Spore 2.2.0j mods.toml metadata. Does not launch Minecraft."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib
import zipfile

TARGET_SHA256 = 'd20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489'


def filehash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def version_tuple(v: str):
    if not re.fullmatch(r'\d+(?:\.\d+)*', v):
        return None
    return tuple(map(int, v.split('.')))


def compare_versions(v1: str, v2: str):
    a, b = version_tuple(v1), version_tuple(v2)
    if a is None or b is None:
        return None
    length = max(len(a), len(b))
    a, b = a + (0,)*(length-len(a)), b + (0,)*(length-len(b))
    return (a > b) - (a < b)


def range_contains(rng: str, version: str):
    match = re.fullmatch(r'\s*([\[(])\s*([0-9.]+)\s*,\s*([0-9.]*)\s*([\])])\s*', rng)
    if not match:
        return None
    left, lower, upper, right = match.groups()
    lo = compare_versions(version, lower)
    hi = compare_versions(version, upper) if upper else None
    if lo is None or (upper and hi is None):
        return None
    return (lo > 0 or (lo == 0 and left == '[')) and (hi is None or hi < 0 or (hi == 0 and right == ']'))


def inspect_toml(raw: bytes):
    doc = tomllib.loads(raw.decode('utf-8'))
    ids = [m.get('modId') for m in doc.get('mods', [])]
    depmap = doc.get('dependencies', {})
    foreign = sorted(set(depmap) - set(ids))
    for_mod = {modid: depmap.get(modid, []) for modid in ids}
    mismatched_range = [
        {'declaring_key': key, 'target_modid': dep.get('modId'), 'range': dep.get('versionRange'), 'contains_1_20_1':range_contains(dep.get('versionRange',''), '1.20.1')}
        for key, deps in depmap.items() for dep in deps
        if dep.get('modId') == 'minecraft'
    ]
    findings = []
    if 'spore' in ids and 'spore' not in depmap and 'examplemod' in depmap:
        findings.append({'id': 'SPORE-META-1', 'basis':'DIRECT_ARTIFACT_AND_FORGE_SPEC', 'summary':'mods.toml dependency table is dependencies.examplemod but actual modId is spore', 'runtime':'NOT_RUN'})
    if any(x['range']=='[1.20,1.20.1)' and x['contains_1_20_1'] is False for x in mismatched_range):
        findings.append({'id':'SPORE-META-2','basis':'DIRECT_ARTIFACT_AND_RANGE_ARITHMETIC','summary':'declared examplemod minecraft range excludes 1.20.1; not a valid Spore dependency declaration','runtime':'NOT_RUN'})
    return {'schema':'kneekura.spore.mods-toml-audit.v1','scope':'uploaded immutable JAR mods.toml only; no Forge runtime loader semantics verified',
        'mods_toml_sha256':hashlib.sha256(raw).hexdigest(),'declared_mod_ids':ids,
        'dependency_table_names':sorted(depmap),'unmatched_dependency_table_names':foreign,
        'dependencies_for_declared_mod_ids':for_mod,
        'minecraft_ranges_found':mismatched_range,'findings':findings,
        'status':'STATIC_FINDINGS' if findings else 'NO_TEMPLATE_MISMATCH_FOUND',
        'runtime':'NOT_RUN'}


def audit(path: Path, require_exact: bool=True):
    observed = filehash(path)
    if require_exact and observed != TARGET_SHA256:
        return {'status':'BLOCKED_HASH_MISMATCH','observed_sha256':observed,'expected_sha256':TARGET_SHA256}
    with zipfile.ZipFile(path) as z:
        data = z.read('META-INF/mods.toml')
    result = inspect_toml(data)
    result['artifact_sha256'] = observed
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jar',type=Path)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if not args.jar.is_file(): parser.error('JAR not found')
    report=audit(args.jar)
    payload=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if args.out: args.out.write_text(payload,encoding='utf-8')
    else: print(payload,end='')
    return 0 if report['status']!='BLOCKED_HASH_MISMATCH' else 2

if __name__=='__main__':sys.exit(main())
