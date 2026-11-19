#!/usr/bin/env python3
"""Hash-pin original Spore 2.2.0j and inventory explicit GoalSelector.addGoal.

Owned research script; emits only derived metadata and source locators, no original
bytecode or Java sources. Direct calls are not guaranteed reachable/active goals.
"""
import argparse, hashlib, json, re, subprocess, sys, zipfile
from collections import Counter
from pathlib import Path

EXPECTED = 'd20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489'
PREFIX = 'com/Harbinger/Spore/'
GOAL_CALL = 'net/minecraft/world/entity/ai/goal/GoalSelector.m_25352_:'
METHOD_HEAD = re.compile(r'^  (?:public|private|protected|static|final|synchronized).*?(?:\([^\n]*\)|static \{\});(?:.*)?$')
PC = re.compile(r'^\s*(\d+):\s+(\S+)(.*)$')


def hashfile(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def priority_value(instruction):
    if instruction is None:return None
    _,op,arg,_ = instruction
    if op.startswith('iconst_'):
        try:return int(op.split('_')[-1])
        except ValueError:return -1 if op=='iconst_m1' else None
    if op in ('bipush','sipush'):
        match=re.search(r'-?\d+',arg);return int(match.group(0)) if match else None
    if op in ('ldc','ldc_w'):
        match=re.search(r'// int (-?\d+)',arg);return int(match.group(1)) if match else None
    return None


def is_goal_alloc(class_name):
    return class_name.startswith('net/minecraft/world/entity/ai/goal/') or (
        class_name.startswith('com/Harbinger/Spore/Sentities/') and
        ('/AI/' in class_name or '$' in class_name))


def parse_javap(source, owner):
    method=None;in_code=False;history=[];rows=[]
    for line in source.splitlines():
        if METHOD_HEAD.match(line):method=line.strip();in_code=False;history=[]
        if line.strip()=='Code:':in_code=True
        if not in_code:continue
        match=PC.match(line)
        if match is None:continue
        pc,op,arg=int(match.group(1)),match.group(2),match.group(3)
        comment=arg.split('//',1)[-1].strip() if '//' in arg else ''
        inst=(pc,op,arg,comment)
        if op in ('invokevirtual','invokeinterface') and GOAL_CALL in comment:
            receivers=[(i,v) for i,v in enumerate(history) if v[1]=='getfield' and 'GoalSelector;' in v[3]]
            if not receivers:raise ValueError('missing selector receiver '+owner+' '+str(pc))
            i,receiver=receivers[-1]
            in_call=history[i+1:]
            prio=priority_value(in_call[0] if in_call else None)
            allocations=[v[3][6:] for v in in_call if v[1]=='new' and v[3].startswith('class ') and is_goal_alloc(v[3][6:])]
            if len(allocations)!=1 or prio is None:raise ValueError('unresolved goal/priority '+owner+' '+str(pc))
            if 'f_21345_' in receiver[3]:selector='goal'
            elif 'f_21346_' in receiver[3]:selector='target'
            else:raise ValueError('unresolved selector field '+owner+' '+str(pc))
            rows.append({'owner':owner,'method':method,'pc':pc,'selector':selector,'priority':prio,'goal_class':allocations[0]})
        history.append(inst)
    return rows


def summarize(rows):
    calls=Counter(r['selector'] for r in rows)
    owners={r['owner'] for r in rows}
    def select(fragment, owner=None):
        return [r for r in rows if fragment in r['goal_class'] and (not owner or owner in r['owner'])]
    contracts={
      'original_unique_direct_registration_owners_86':len(owners)==86,
      'original_direct_registration_invokes_372':len(rows)==372,
      'original_selector_split_356_16':calls['goal']==356 and calls['target']==16,
      'brute_transport_at_priority_1':any(r['priority']==1 for r in select('/AI/TransportInfected','/Brute.class')),
      'leaper_transport_at_priority_3':any(r['priority']==3 for r in select('/AI/TransportInfected','/Leaper.class')),
      'base_infected_scavenge_at_priority_7':any(r['priority']==7 for r in select('/AI/InfectedConsumeFromRemains','/BaseEntities/Infected.class')),
      'base_infected_search_area_priority_4':any(r['priority']==4 for r in select('/AI/LocHiv/SearchAreaGoal','/BaseEntities/Infected.class')),
      'base_infected_follow_10_twice':len([r for r in select('/AI/LocHiv/FollowOthersGoal','/BaseEntities/Infected.class') if r['priority']==10])==2,
      'witch_three_buff_subclasses_priority_4':set(r['goal_class'].rsplit('/',1)[-1] for r in rows if '/BasicInfected/InfectedWitch$' in r['goal_class'] and r['priority']==4)=={'InfectedWitch$3','InfectedWitch$4','InfectedWitch$5'},
      'calamity_scent_8_at_priority_7':len([r for r in select('/AI/CalamitiesAI/SummonScentInCombat') if r['priority']==7])==8,
      'calamity_burst_8_at_priority_8':len([r for r in select('/AI/CalamitiesAI/SporeBurstSupport') if r['priority']==8])==8,
      'proto_targeting_priority_3':any(r['priority']==3 for r in select('/AI/NeuralProcessing/ProtoAIs/ProtoTargeting','/Organoids/Proto.class')),
      'calamity_vigil_call_priority_7':any(r['priority']==7 for r in select('/AI/CalamitiesAI/CalamityVigilCall','/BaseEntities/Calamity.class')),
      'handler_event_direct_injections_10':len([r for r in rows if r['owner'].endswith('/sEvents/HandlerEvents.class')])==10,
    }
    return calls, contracts


def analyze(jar):
    file_sha=hashfile(jar)
    if file_sha!=EXPECTED:
        return {'status':'BLOCKED_HASH_MISMATCH','expected_sha256':EXPECTED,'actual_sha256':file_sha}
    with zipfile.ZipFile(jar) as z:
        classes=sorted((x for x in z.namelist() if x.startswith(PREFIX) and x.endswith('.class') and b'm_25352_' in z.read(x)))
        hashes={p:hashlib.sha256(z.read(p)).hexdigest() for p in classes}
    rows=[]
    for internal in classes:
        java_name=internal[:-6].replace('/','.')
        cmd=['javap','-c','-p','-classpath',str(jar),java_name]
        r=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=45)
        rows.extend(parse_javap(r.stdout,internal))
    calls,contracts=summarize(rows)
    sub_hierarchy={
      'InfectedWitch$3':'com/Harbinger/Spore/Sentities/AI/BuffAlliesGoal',
      'InfectedWitch$4':'com/Harbinger/Spore/Sentities/AI/BuffAlliesGoal',
      'InfectedWitch$5':'com/Harbinger/Spore/Sentities/AI/BuffAlliesGoal',
      'Busser$4':'com/Harbinger/Spore/Sentities/AI/TransportInfected',
    }
    for inner,sup in sub_hierarchy.items():
        path=next((r['goal_class'] for r in rows if r['goal_class'].endswith('/'+inner)),None)
        if path is None:contracts['subclass_'+inner]=False;continue
        r=subprocess.run(['javap','-p','-classpath',str(jar),path.replace('/','.')],capture_output=True,text=True,check=True,timeout=45)
        contracts['subclass_'+inner]=(' extends '+sup.replace('/','.') in r.stdout)
    # The base helper and class constructors are checked with javap; do not derive
    # live flags for a subclass without checking constructors/inherited overrides.
    base_goal_flags={
      'TransportInfected':('TARGET',),
      'BuffAlliesGoal':('MOVE','LOOK'),
      'SearchAreaGoal':('MOVE',),
      'FollowOthersGoal':('MOVE','LOOK'),
      'LocalTargettingGoal':(),
      'InfectedConsumeFromRemains':(),
      'SporeBurstSupport':(),
      'SummonScentInCombat':(),
      'ProtoTargeting':(),
    }
    for g,flags in base_goal_flags.items():
        internal=next((i for i in zipfile.ZipFile(jar).namelist() if i.endswith('/'+g+'.class') and i.startswith(PREFIX)),None)
        if internal is None:contracts['flag_'+g]=False;continue
        d=subprocess.run(['javap','-p','-c','-classpath',str(jar),internal[:-6].replace('/','.')],capture_output=True,text=True,check=True,timeout=45).stdout
        found=set(re.findall(r'Goal\$Flag\.(MOVE|LOOK|TARGET|JUMP):',d))
        has_set='m_7021_:(Ljava/util/EnumSet;)V' in d
        contracts['flag_'+g]=(found==set(flags) and (has_set==bool(flags)))
    return {
       'schema':'kneekura.spore.goal-registry.v1','status':'PASS_STATIC' if all(contracts.values()) else 'FAIL_STATIC',
       'jar_sha256':file_sha,'minecraft':'1.20.1','loader':'Forge','spore_version':'2.2.0j',
       'direct_owner_classes':len(classes),'direct_registration_calls':len(rows),
       'goal_selector_count':calls['goal'],'target_selector_count':calls['target'],
       'priority_distribution':dict(sorted(Counter(str(r['priority']) for r in rows).items())),
       'method_distribution':dict(Counter(r['method'].split('(')[0] for r in rows)),
       'contracts':contracts,'contracts_passed':sum(contracts.values()),'contracts_total':len(contracts),
       'direct_class_sha256':hashes,
       'registrations':rows,
       'known_goal_constructor_flags':{k:list(v) for k,v in base_goal_flags.items()},
       'limitations':['Direct m_25352_ callsites; not all goals currently registered to a live Mob',
                      'Constructor/helper/inheritance order and dynamic event insertion affect effective sets',
                      'Flag assertions only for listed own Goal implementations and direct constructors',
                      'No server tick, Forge GameTest, live scheduling or TPS measurement',
                      'No original Java source or bytecode bodies copied into this JSON']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('jar',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if not a.jar.is_file():p.error('Missing original user-provided JAR')
    result=analyze(a.jar)
    data=json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+'\n'
    if a.out:a.out.write_text(data,encoding='utf-8')
    else:print(data,end='')
    return 0 if result.get('status')=='PASS_STATIC' else 1
if __name__=='__main__':sys.exit(main())
