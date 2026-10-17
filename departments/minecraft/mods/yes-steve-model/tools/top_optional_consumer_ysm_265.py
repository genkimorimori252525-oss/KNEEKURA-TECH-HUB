#!/usr/bin/env python3
"""TOP-OPTIONAL-CONSUMER fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o', 'com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/o0oO0OO0oo00o0O00oOO000o']
SELECTED=set([('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lmcjty/theoneprobe/api/ITheOneProbe;)Ljava/lang/Void;'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o', 'apply', '(Ljava/lang/Object;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'addProbeEntityInfo', '(Lmcjty/theoneprobe/api/ProbeMode;Lmcjty/theoneprobe/api/IProbeInfo;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/Entity;Lmcjty/theoneprobe/api/IProbeHitEntityData;)V'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'getID', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lmcjty/theoneprobe/api/IProbeInfo;Lcom/elfmcys/yesstevemodel/oOOOooO00oo0oOooooOO0Oo0;)V'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lmcjty/theoneprobe/api/IProbeInfo;Lcom/elfmcys/yesstevemodel/oOOOooO00oo0oOooooOO0Oo0;Lcom/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0;)V'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0;)Z'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Lmcjty/theoneprobe/api/IProbeInfo;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lmcjty/theoneprobe/api/IProbeInfo;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Lcom/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0;)V'), ('com/elfmcys/yesstevemodel/oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/o0oO0OO0oo00o0O00oOO000o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0oO0OO0oo00o0O00oOO000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/fml/event/lifecycle/InterModEnqueueEvent;)V'), ('com/elfmcys/yesstevemodel/o0oO0OO0oo00o0O00oOO000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/Object;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/compat/top/TopPlugin.java', '05d3f8a0198de9ef4d6e440dd575e428ec24021b2673fdc4b1ba16e8583d8e1f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/top/TopPlugin.java', '05d3f8a0198de9ef4d6e440dd575e428ec24021b2673fdc4b1ba16e8583d8e1f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/event/InterModMsg.java', 'a4ad5a82494df7a98c39d71357b11ff73e089e45d00ce477bdc03a3dff740242', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-15-methods',len(ids)==len(set(ids))==15 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-top-annotations',e.get('event_annotations')==details.get('_event_annotations'))
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
    neg('changed-top_optional_consumer-owner-0',lambda x:member(x,0,'()V','<init>')['instructions'].pop())
    neg('changed-top_optional_consumer-owner-1',lambda x:member(x,1,'()V','<init>')['instructions'].pop())
    neg('changed-top_optional_consumer-owner-2',lambda x:member(x,2,'()V','<init>')['instructions'].pop())
    neg('missing-top-annotations',lambda x:x['event_annotations'].pop())
    neg('changed-registration-target',lambda x:op(x,2,'(Lnet/minecraftforge/fml/event/lifecycle/InterModEnqueueEvent;)V',9)['reference'].update(name='missing'))
    neg('changed-vehicle-predicate',lambda x:op(x,1,'(Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0;)Z',1)['reference'].update(name='missing'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
