#!/usr/bin/env python3
"""KNEEKURA owned summary-only audit of Spore 2.2.0j AI classes.

Does not load Spore, Forge or a Minecraft world. Publishes only hashes,
method counts and boolean patterns from javap, never third-party class bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ORIGINAL_SHA = 'd20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489'
PREFIX = 'com/Harbinger/Spore/Sentities/AI/'
PINS = {
    'TransportInfected': '8a7cc28be43269c748b7d8fb7b76f705b3ce431118ccbeec03aa6e1607e086a7',
    'BuffAlliesGoal': '94fe50ffbc82eac3a038d0481b9835b70aba14ebc4d2b370ab97dccf54a3d4b0',
    'InfectedConsumeFromRemains': '587fddabc788d6adfab3412f1a2641486dbb458175ad2107268911bd9deec0ef',
    'CalamitiesAI/SporeBurstSupport': '11b3a441f33429b8e9a2273f3c593bfca5642292f377e16d293f87d00c7f8f79',
    'CalamitiesAI/SummonScentInCombat': 'f529908ca2742d2b92ff38ec18212c272891141721895dfbe76ee3a23fe49b71',
    'HurtTargetGoal': 'd0a015681f82959c9330348c8fdcfb7df56c771598eb2943dfd35c63b1ad2767',
    'AerialRangedGoal': '43467119ab9ff1bb8ce4f03ac2c8c0037e197f41871737fa726ecb48c1ee47f4',
}

def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):h.update(chunk)
    return h.hexdigest()

def extract_method(src, name):
    lines=src.splitlines()
    start=None
    for i,line in enumerate(lines):
        if line.startswith('  ') and not line.startswith('    ') and '(' in line and line.rstrip().endswith(';') and re.search(r'\b'+re.escape(name)+r'\(',line):
            start=i;break
    if start is None:raise ValueError('missing method '+name)
    end=next((i for i in range(start+1,len(lines)) if lines[i].startswith('  ') and not lines[i].startswith('    ') and '(' in lines[i] and lines[i].rstrip().endswith(';')),len(lines))
    return '\n'.join(lines[start:end])

def inspect(p):
    observed=sha_file(p)
    if observed != ORIGINAL_SHA:
        return {'status':'BLOCKED_HASH_MISMATCH','actual_sha256':observed,'expected_sha256':ORIGINAL_SHA}
    with zipfile.ZipFile(p) as z:
        names=sorted(n for n in z.namelist() if n.startswith(PREFIX) and n.endswith('.class'))
        if len(names)!=48:
            return {'status':'BLOCKED_CLASS_INVENTORY_MISMATCH','actual_count':len(names),'expected_count':48}
        classes={n[len(PREFIX):-6]:hashlib.sha256(z.read(n)).hexdigest() for n in names}
    mismatched=[name for name,expected in PINS.items() if classes.get(name)!=expected]
    if mismatched:return {'status':'BLOCKED_CLASS_PIN_MISMATCH','pin_mismatch':mismatched}
    dumps={}
    for name in PINS:
        binary=(PREFIX+name).replace('/','.')
        res=subprocess.run(['javap','-p','-c','-constants','-classpath',str(p),binary],text=True,capture_output=True,check=True)
        dumps[name]=res.stdout
    m=lambda n,method:extract_method(dumps[n],method)
    checks={
        'transport_uses_AABB_32': 'double 32.0d' in m('TransportInfected','getFreePartner'),
        'transport_targeting_range_16': 'double 16.0d' in m('TransportInfected','TransportInfected'),
        'transport_rescan_tick20': 'bipush        20' in m('TransportInfected','m_8036_'),
        'transport_ride_when_dist_sq_lt9': ('double 9.0d' in m('TransportInfected','m_8037_') and 'equip:()V' in m('TransportInfected','m_8037_') and 'm_20329_' in m('TransportInfected','equip')),
        'buff_canUse_looks_up_partner_twice': m('BuffAlliesGoal','m_8036_').count('Method getFreePartner:()Lnet/minecraft/world/entity/Mob;')==2,
        'buff_ranged_support_callback': 'RangedBuff.performRangedBuff' in m('BuffAlliesGoal','m_8037_'),
        'buff_selects_nearest_from_follow_range': 'Attributes.f_22277_' in m('BuffAlliesGoal','getFreePartner') and 'm_20280_' in m('BuffAlliesGoal','getFreePartner'),
        'hungry_goal_0_to_10_gate': 'bipush        10' in m('InfectedConsumeFromRemains','m_8036_') and 'm_216339_:(II)I' in m('InfectedConsumeFromRemains','m_8036_'),
        'hungry_canUse_mutates_blocks': 'm_7471_' in m('InfectedConsumeFromRemains','isCorpse'),
        'hungry_rewards_evo_and_kills': all(s in m('InfectedConsumeFromRemains','isCorpse') for s in ('setHunger','setEvoPoints','setKills','Math.random','double 0.1d')),
        'burst_gate_one_of_300': 'sipush        300' in m('CalamitiesAI/SporeBurstSupport','m_8036_'),
        'burst_target_distance_sq_lt200': 'double 200.0d' in m('CalamitiesAI/SporeBurstSupport','m_8036_'),
        'burst_stun_60_and_chemical': all(s in m('CalamitiesAI/SporeBurstSupport','m_8056_') for s in ('bipush        60','setStun','chemicalRange','sporeBurst','killCDUs')),
        'burst_scans_blocks_and_replaces_CDU': all(s in m('CalamitiesAI/SporeBurstSupport','killCDUs') for s in ('BlockPos.m_121976_','Sblocks.CDU','CDUBlock.replaceCDU')),
        'scent_gate_by_config_and_400': all(s in m('CalamitiesAI/SummonScentInCombat','m_8036_') for s in ('scent_spawn','sipush        400','checkForScent')),
        'scent_cap_lt2_in_AABB8': all(s in m('CalamitiesAI/SummonScentInCombat','checkForScent') for s in ('double 8.0d','List.size','iconst_2')),
        'scent_spawn_stuns_for80': all(s in m('CalamitiesAI/SummonScentInCombat','m_8056_') for s in ('SummonScent:()V','bipush        80','setStun')),
        'hurt_goal_alerts_other_mobs': 'alertOther:' in m('HurtTargetGoal','alertOthers') and 'm_6710_' in m('HurtTargetGoal','alertOther'),
        'aerial_ranged_uses_scattershot': 'ScatterShotRangedGoal' in dumps['AerialRangedGoal'] and 'm_8036_' in m('AerialRangedGoal','m_8036_'),
        'aerial_movement_orbit': 'Vec3.m_82524_' in m('AerialRangedGoal','Orbit'),
    }
    return {
        'schema':'kneekura.spore.ai-goal-layer.v1',
        'status':'PASS_STATIC_BYTECODE' if all(checks.values()) else 'FAIL_STATIC_BYTECODE',
        'target_artifact_sha256':observed,
        'minecraft':'1.20.1','loader':'Forge','mod_version':'2.2.0j',
        'class_total':1350,'ai_prefix_class_count':len(names),
        'neural_processing_class_count':sum(n.startswith(PREFIX+'NeuralProcessing/') for n in names),
        'pinned_classes_verified':len(PINS),
        'checks_passed':sum(checks.values()),'checks_total':len(checks),
        'checks':checks,
        'ai_classes': [{'path':PREFIX+n+'.class','sha256':classes[n]} for n in sorted(classes)],
        'limitations':['Static JAR binary inspection only','No simulation of Forge scheduler or world','Not all 48 AI classes semantically decoded','No Spore runtime or performance measurements','FRONTIER NeoForge not acquired','ARR class bodies/assets not published']
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('jar',type=Path)
    ap.add_argument('--out',type=Path)
    opt=ap.parse_args()
    if not opt.jar.is_file():ap.error('missing JAR')
    d=inspect(opt.jar)
    text=json.dumps(d,indent=2,ensure_ascii=False,sort_keys=True)+'\n'
    if opt.out:opt.out.write_text(text,encoding='utf-8')
    else:print(text,end='')
    return 0 if d['status']=='PASS_STATIC_BYTECODE' else 1
if __name__=='__main__':sys.exit(main())
