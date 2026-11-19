#!/usr/bin/env python3
"""Spore 2.2.0j original Gargoyl SmashStomp wrong-position bytecode guard."""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys,zipfile
from pathlib import Path
JAR_SHA='d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489'
CLS='com/Harbinger/Spore/Sentities/EvolvedInfected/Gargoyl.class'
CLS_SHA='ff93579d0247e45fc2ca075ff55a5db6184fb47f4eee459c0e395e8a206c5780'

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def analyze(jar:Path):
    observed=digest(jar)
    if observed != JAR_SHA:return {'status':'BLOCKED_HASH_MISMATCH','actual_sha256':observed}
    with zipfile.ZipFile(jar) as z:
        actual_cls=hashlib.sha256(z.read(CLS)).hexdigest()
    if actual_cls!=CLS_SHA:return {'status':'BLOCKED_CLASS_SHA_MISMATCH','class_sha256':actual_cls}
    javap=subprocess.run(['javap','-p','-c','-constants','-classpath',str(jar),CLS[:-6].replace('/','.')],capture_output=True,text=True,check=True).stdout
    start=javap.index('  protected void SmashStomp(')
    end=javap.find('\n  protected void DamageEntities(',start)
    if end<0:raise ValueError('Missing following method')
    body=javap[start:end]
    state_at_candidate=bool(re.search(r'aload\s+13\s*\n\s*\d+: invokevirtual\s+#[0-9]+\s+// Method net/minecraft/world/level/Level\.m_8055_:.*?\n\s*\d+: astore\s+14',body))
    hardness_with_center=len(re.findall(r'aload\s+14\s*\n\s*\d+: aload_1\s*\n\s*\d+: aload_2\s*\n\s*\d+: invokevirtual\s+#[0-9]+\s+// Method net/minecraft/world/level/block/state/BlockState\.m_60800_:',body))
    checks={'retrieves_state_at_candidate_blockpos':state_at_candidate,
            'checks_candidate_hardness_with_center_blockpos_twice':hardness_with_center==2,
            'uses_falling_block_after_hardness':'FallingBlockEntity.m_201971_' in body,
            'may_destroy_candidate_block':'ServerLevel.m_7471_' in body}
    return {'schema':'kneekura.spore.gargoyl-hardness-bytecode.v1','status':'PASS_STATIC_CONTRACT' if all(checks.values()) else 'FAIL_STATIC_CONTRACT',
            'jar_sha256':observed,'class_internal_path':CLS,'class_sha256':actual_cls,'method':'SmashStomp(Level,BlockPos,double,double)',
            'hardness_with_center_position_call_count':hardness_with_center,'checks':checks,
            'direct_observation':'BlockState read at candidate BlockPos but getDestroySpeed called with original center BlockPos; original candidate state and queried coordinates may be inconsistent',
            'upstream_issue':'https://github.com/DynamicTreesTeam/DynamicTrees/issues/1201',
            'runtime_reproduction':'NOT_RUN','issue_reported_crash':'REPORTED','upstream_repair_diff':'NOT_FOUND_OR_NOT_REVIEWED','fix_verified':'NO'}

def main():
    p=argparse.ArgumentParser();p.add_argument('jar',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args();r=analyze(a.jar);s=json.dumps(r,sort_keys=True,indent=2)+'\n'
    if a.out:a.out.write_text(s)
    else:print(s,end='')
    return 0 if r.get('status')=='PASS_STATIC_CONTRACT' else 1
if __name__=='__main__':sys.exit(main())
