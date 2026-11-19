#!/usr/bin/env python3
"""Narrow, reproducible ORIGINAL Spore 2.2.0j group/command bytecode checks.

Checks bytecode *structure* of the user's JAR; never loads the mod/game, and
never stores third-party bytecode or decompiled source in output. MIT-style
original KNEEKURA-owned analysis script, not copied from the Mod.
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

TARGET_SHA = 'd20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489'
ROOT = 'com/Harbinger/Spore/'
PINS = {
 'Sentities/Organoids/Proto':'8ab88d4e784512d910643831d8ec2caaeb4b9acf15a319a28752a3b9c5fcade3',
 'Sentities/Organoids/Vigil':'412bcdb542512b5da496f358879c8c1278e030659b7ef641581450026aeb32fb',
 'Sentities/AI/CalamitiesAI/CalamityVigilCall':'bc18e952a90ce82bae7376a5331468648c5d1b8f28687766cad8a740522c1e86',
 'Sentities/AI/CalamitiesAI/CalamityInfectedCommand':'fc9e48ca7025f8d752b63e54a2871938e49eb28886ed0a0d439db27dad7aa144',
 'Sentities/AI/NeuralProcessing/ProtoAIs/ProtoTargeting':'a12fa4539b2721057b0f01d506aa4fa92a6dfbe0a93c32278bfbffc0585ab2ba',
 'Sentities/AI/LocHiv/LocalTargettingGoal':'c509b646ceab8f1af24e33fbeaa5bdcae0ca7d7cceca2a479a78de7cadbe47b5',
 'Sentities/AI/LocHiv/FollowOthersGoal':'ab20d22c738b6322fd8baf6c3d2d91d6b074ccd65e12022aacd3b9d0069d159d',
 'Sentities/AI/LocHiv/SearchAreaGoal':'bc9b4933031c5ef1388d68f7bf3b8aeb8b4498d97efd4e358bc5bb93a19aee7d',
 'Sentities/BaseEntities/Calamity':'ca7b48770085457460fbcc422d395254c71c2cb5a8fe31b2f81993b70593fa76',
 'Sentities/Signal':'8cc22fe364f92e5dea0aea438540ba05e0a0f0b3dd6ee376e62101f92c634e15',
 'Sentities/Organoids/Womb':'7ac7824e6164b688caf695976bb892473014d377f99a9151daa2a1ccec213ccc',
}

def filehash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as src:
        for chunk in iter(lambda:src.read(2**20), b''):
            h.update(chunk)
    return h.hexdigest()


def method(body:str, name:str) -> str:
    lines=body.splitlines()
    reg=r'^  (?:public|private|protected|static) .+\b'+re.escape(name)+r'\('
    start=next((i for i,l in enumerate(lines) if re.search(reg,l)),None)
    if start is None:raise ValueError('Missing method '+name)
    end=next((i for i in range(start+1,len(lines)) if re.match(r'^  (?:public|private|protected|static) ',lines[i])),len(lines))
    return '\n'.join(lines[start:end])

def regex(s,pattern):return re.search(pattern,s,re.S | re.M) is not None

def verify(jar:Path) -> dict:
    actual=filehash(jar)
    if actual!=TARGET_SHA:
        return {'status':'BLOCKED_HASH_MISMATCH','observed_jar_sha256':actual,'expected_sha256':TARGET_SHA}
    with zipfile.ZipFile(jar) as z:
        bad=[c for c,h in PINS.items() if hashlib.sha256(z.read(ROOT+c+'.class')).hexdigest()!=h]
    if bad:return {'status':'BLOCKED_CLASS_HASH_MISMATCH','affected_classes':bad,'artifact_sha256':actual}
    dumps={}
    for c in PINS:
        r=subprocess.run(['javap','-p','-c','-constants','-classpath',str(jar),(ROOT+c).replace('/','.')],capture_output=True,text=True,check=True)
        dumps[c.split('/')[-1]]=r.stdout
    proto=dumps['Proto']; vigil=dumps['Vigil']; pat=dumps['ProtoTargeting']; local=dumps['LocalTargettingGoal']; cc=dumps['CalamityInfectedCommand']; vc=dumps['CalamityVigilCall']; follow=dumps['FollowOthersGoal']; search=dumps['SearchAreaGoal']
    vm=method(vigil,'TimeToLeave')
    pm=method(proto,'checkForCalamities')
    ps=method(proto,'m_8119_')
    checks={
        'proto_target_activation_one_of_six':regex(method(pat,'m_8036_'),r'iconst_0\n.*?iconst_5\n.*?RandomSource\.m_216339_.*?iconst_3\n.*?if_icmpne'),
        'linked_local_target_activation_one_of_ten':regex(method(local,'m_8036_'),r'Infected\.getLinked:.*?bipush\s+10.*?RandomSource\.m_188503_'),
        'calamity_command_activation_one_of_hundred':regex(method(cc,'m_8036_'),r'bipush\s+100.*?RandomSource\.m_188503_.*?getSearchArea'),
        'calamity_low_health_vigil_one_of_two_hundred':regex(method(vc,'m_8036_'),r'Calamity\.m_21223_.*?Calamity\.m_21233_.*?fconst_2.*?fdiv.*?sipush\s+200'),
        'calamity_constructs_vigil_parent':regex(method(vc,'m_8056_'),r'new\s+.*?class com/Harbinger/Spore/Sentities/Organoids/Vigil.*?Vigil\.setProto:.*?Level\.m_7967_'),
        'vigil_third_or_later_trigger_signals_proto':regex(vm,r'iconst_3\n.*?if_icmplt.*?new\s+.*?class com/Harbinger/Spore/Sentities/Signal.*?setSignal:'),
        'vigil_first_matching_proto_signal_only':regex(vm,r'setSignal:.*?goto\s+184.*?goto\s+103'),
        'proto_redirects_or_attempts_new_womb':regex(ps,r'getSignal:.*?Signal\.active:.*?checkForCalamities:.*?SummonConstructor:'),
        'proto_redirect_uses_half_chance':regex(pm,r'Math\.random:.*?double 0\.5d.*?Calamity\.setSearchArea:.*?setSignal:'),
        'proto_womb_path_constructs_reconstructor':regex(method(proto,'SummonConstructor'),r'new\s+.*?class com/Harbinger/Spore/Sentities/Organoids/Womb.*?Sentities\.RECONSTRUCTOR:.*?Womb.*?Level\.m_7967_'),
        'calamity_command_requires_existing_receiver_search':regex(method(cc,'Targeting'),r'Infected\.getSearchPos:.*?ifnull\s+158.*?Calamity\.getSearchArea:.*?Infected\.setSearchPos:'),
        'local_search_starts_for_no_target':regex(method(search,'m_8036_'),r'Infected\.getSearchPos:.*?ifnull.*?Infected\.m_5448_:'),
        'local_search_repath_40_goal_ticks':regex(method(search,'shouldRecalculatePath'),r'bipush\s+40.*?irem'),
        'local_search_clears_with_radius_nine':regex(method(search,'m_8037_'),r'double 9\.0d.*?BlockPos\.m_203195_:.*?Infected\.setSearchPos:'),
        'follow_partner_scan_every_twenty_canUse_checks':regex(method(follow,'m_8036_'),r'bipush\s+20.*?searchCooldown:.*?findNearestPartner:'),
        'follow_path_reconsidered_each_twenty_entity_ticks':regex(method(follow,'shouldRepath'),r'bipush\s+20.*?irem'),
        'follow_clears_partner_at_distance_sq_4096':regex(method(follow,'m_8045_'),r'double 4096\.0d.*?Infected\.setFollowPartner:'),
        'follow_tick_has_position_warp_at_distance_sq_4096':regex(method(follow,'m_8037_'),r'double 4096\.0d.*?Infected\.m_6021_:'),
        'vigil_summons_infected_on_waves':regex(method(vigil,'m_8107_'),r'bipush\s+20.*?SummonInfected:\(\)V.*?setWaveSize:'),
    }
    return {
        'schema':'kneekura.spore.group-ai-static-gate.v1',
        'status':'PASS_STATIC_BYTECODE' if all(checks.values()) else 'FAIL_STATIC_BYTECODE',
        'target':'Spore 2.2.0j / Minecraft 1.20.1 Forge',
        'artifact_sha256':actual,
        'class_hashes_verified':len(PINS),
        'contracts_passed':sum(checks.values()),
        'contracts_total':len(checks),
        'checks':checks,
        'derived_probabilities_conditional_on_canUse_evaluation':{'ProtoTargeting':'1/6','LocalTargettingGoal':'1/10','CalamityInfectedCommand':'1/100','CalamityVigilCall':'1/200 AND below half health AND target exists'},
        'scope':'Bytecode syntactic method patterns and class hashes, not gameplay execution or measured TPS',
        'runtime':'NOT_RUN', 'licensing':'No original Java source, JAR or assets redistributed'
    }

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('jar',type=Path)
    cli.add_argument('--out',type=Path)
    a=cli.parse_args()
    if not a.jar.is_file():cli.error('JAR missing')
    r=verify(a.jar)
    data=json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if a.out:a.out.write_text(data,encoding='utf-8')
    else:print(data,end='')
    return 0 if r['status']=='PASS_STATIC_BYTECODE' else 1
if __name__=='__main__':sys.exit(main())
