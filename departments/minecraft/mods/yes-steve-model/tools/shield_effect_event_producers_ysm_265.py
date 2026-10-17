#!/usr/bin/env python3
"""SHIELD-EFFECT-EVENT-PRODUCERS fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOOOo00OoOo0000oo000OOO0', 'com/elfmcys/yesstevemodel/OO00Oo0O00oOo0O00OoO0O00']
SELECTED=set([('com/elfmcys/yesstevemodel/OOOOo00OoOo0000oo000OOO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOOOo00OoOo0000oo000OOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/entity/living/ShieldBlockEvent;)V'), ('com/elfmcys/yesstevemodel/OOOOo00OoOo0000oo000OOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/entity/living/LivingEvent$LivingTickEvent;)V'), ('com/elfmcys/yesstevemodel/OOOOo00OoOo0000oo000OOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;)Z'), ('com/elfmcys/yesstevemodel/OO00Oo0O00oOo0O00OoO0O00', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OO00Oo0O00oOo0O00OoO0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/entity/living/MobEffectEvent$Added;)V'), ('com/elfmcys/yesstevemodel/OO00Oo0O00oOo0O00OoO0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/entity/living/MobEffectEvent$Remove;)V'), ('com/elfmcys/yesstevemodel/OO00Oo0O00oOo0O00OoO0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/entity/living/MobEffectEvent$Expired;)V'), ('com/elfmcys/yesstevemodel/OO00Oo0O00oOo0O00OoO0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraftforge/event/entity/living/MobEffectEvent$Expired;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/OO00Oo0O00oOo0O00OoO0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraftforge/event/entity/living/MobEffectEvent$Remove;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/OO00Oo0O00oOo0O00OoO0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraft/world/effect/MobEffectInstance;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/event/LivingShieldBlockEvent.java', 'ccb211fcf7d70a83d0cd80bd172a0fba5480c751158befa5708b6ba5452151bf', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/event/MobEffectSyncEvent.java', '3bc7d444bee36fab578c37b664206093bc03cb5c91d9e059fb4841b9b6f12551', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-11-methods',len(ids)==len(set(ids))==11 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('fixed-owner-declarations',len(ds)==2 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('fixed-bootstrap-records',len(bs)==2 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-event-annotations',e.get('event_annotations')==details.get('_event_annotations'))
    return checks

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('jar','evidence','source-root','out'):ap.add_argument('--'+k,required=True)
    a=ap.parse_args();raw=Path(a.jar).read_bytes()
    if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:raise SystemExit('Wrong fixed artifact')
    e=json.loads(Path(a.evidence).read_text());actual={};decl={}
    with zipfile.ZipFile(a.jar) as z:
        for owner in OWNERS:
            b=z.read(owner+'.class');c=parse_class(b);decl[owner]={k:c[k] for k in DECL}
            actual.update({ident(m):m for m in parse_bounded(b,True) if ident(m) in SELECTED})
    details=copy.deepcopy(BOUNDDETAILS)
    with zipfile.ZipFile(a.jar) as z:details['_event_annotations']=[annotations(z.read(o+'.class')) for o in OWNERS]
    checks=audit(e,actual,decl,details);root=Path(a.source_root)
    revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    checks.append({'check':'source-revision','pass':revision==SOURCES[0][2]})
    for path,sha,rev in SOURCES:checks.append({'check':'source:'+path,'pass':hashlib.sha256((root/path).read_bytes()).hexdigest()==sha})
    negatives=[]
    def member(x,owner,desc,name=None):return next(m for m in x['members'] if m['owner']==OWNERS[owner] and m['descriptor']==desc and (name is None or m['name']==name))
    def op(x,owner,desc,offset,name=None):return next(o for o in member(x,owner,desc,name)['instructions'] if o['offset']==offset)
    def neg(name,mutate):
        x=copy.deepcopy(e);mutate(x);fail=[c for c in audit(x,actual,decl,details) if not c['pass']];negatives.append({'control':name,'rejected':bool(fail)})
    neg('missing-method',lambda x:x['members'].pop())
    neg('missing-owner',lambda x:x['owner_declarations'].pop())
    neg('missing-source',lambda x:x['source_tracks'].pop())
    neg('missing-bootstrap',lambda x:x['bootstrap_and_constant_evidence'].pop())
    neg('wrong-artifact',lambda x:x['artifact'].update(sha256='0'*64))
    neg('missing-state-event-owner-0',lambda x:member(x,0,'(Lnet/minecraftforge/event/entity/living/ShieldBlockEvent;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-state-event-owner-1',lambda x:member(x,1,'(Lnet/minecraftforge/event/entity/living/MobEffectEvent$Added;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-event-annotations',lambda x:x['event_annotations'].pop())
    neg('wrong-initial-cooldown',lambda x:op(x,0,'(Lnet/minecraftforge/event/entity/living/ShieldBlockEvent;)V',11).update(opcode='0x03'))
    neg('wrong-zero-removal-test',lambda x:op(x,0,'(Lnet/minecraftforge/event/entity/living/LivingEvent$LivingTickEvent;)V',28).update(opcode='0x9b'))
    neg('wrong-effect-side-gate',lambda x:op(x,1,'(Lnet/minecraftforge/event/entity/living/MobEffectEvent$Added;)V',16).update(opcode='0x9a'))
    neg('wrong-amplifier-level-shift',lambda x:op(x,1,'(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraft/world/effect/MobEffectInstance;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V',14).update(opcode='0x64'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
