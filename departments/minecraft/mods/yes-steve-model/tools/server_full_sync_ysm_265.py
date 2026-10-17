#!/usr/bin/env python3
"""SERVER-FULL-SYNC fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OoOoOOOOO0ooooo0O0ooo000', 'com/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O', 'com/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/event/CapabilityEvent.java', '3f2aa640f472a1c2ea2df119be2e01943078e4b21c457c6cf281dad345a76458', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/ModelInfoCapability.java', 'b986def6d470e2ed307104acc22375ccda32af7cd0986741957a689a58b28adc', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/SyncModelInfo.java', 'b24e1b7aba4980df67172b606ff05093edc2893e6a3a04d6838d9ce871569de2', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-73-methods',len(ids)==len(set(ids))==73 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
            actual.update({ident(m):m for m in parse_bounded(b,True)})
    details=copy.deepcopy(BOUNDDETAILS);checks=audit(e,actual,decl,details);root=Path(a.source_root)
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
    neg('missing-end-tick-body',lambda x:member(x,0,'(Lnet/minecraftforge/event/TickEvent$ServerTickEvent;)V')['instructions'].pop())
    neg('dirty-gate-inverted',lambda x:op(x,0,'(Lnet/minecraft/server/level/ServerPlayer;Ljava/lang/Boolean;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V',60).update(opcode='0x9a'))
    neg('full-optional-always-send',lambda x:op(x,0,'(Lnet/minecraft/server/level/ServerPlayer;Ljava/lang/Boolean;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V',89)['reference'].update(name='get'))
    neg('missing-dirty-clear-call',lambda x:op(x,0,'(Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O;)V',1)['reference'].update(name='missing'))
    neg('queue-peek-instead-of-drain',lambda x:op(x,1,'(Lnet/minecraft/server/level/ServerPlayer;ZLcom/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0;)Lcom/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O;',28)['reference'].update(name='peek'))
    neg('invented-builder-finally',lambda x:member(x,1,'(Lnet/minecraft/server/level/ServerPlayer;ZLcom/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0;)Lcom/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O;')['exception_handlers'].append({'handler':0}))
    neg('receiver-skips-model-update',lambda x:op(x,2,'(Lcom/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O;Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V',9)['reference'].update(name='missing'))
    neg('receiver-skips-properties',lambda x:op(x,2,'(Lcom/elfmcys/yesstevemodel/O0oOOo0OO0000oooOO0ooo0O;Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V',25)['reference'].update(name='missing'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
