#!/usr/bin/env python3
"""Fixed-artifact selected motion query evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OoooO0ooO0OO0o0OO0O0oooO', 'com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/event/EntityLoadEvent.java', '338df9d1f4ff645dd1bc5296a74605fa97497f7eafd8f96d0b7e4e0734318950', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/DispatchServerDrivenProperty.java', '5d30671bf5303fc7fc01cb6a044f95c169630147e33d77c4991ef3f07949bc50', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]
SELECTED=set([('com/elfmcys/yesstevemodel/OoooO0ooO0OO0o0OO0O0oooO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OoooO0ooO0OO0o0OO0O0oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/entity/EntityJoinLevelEvent;)V'), ('com/elfmcys/yesstevemodel/OoooO0ooO0OO0o0OO0O0oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(ILjava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/OoooO0ooO0OO0o0OO0O0oooO', 'o0OOooo0o0OO00OoOOOo0o0O', '(ILjava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/OoooO0ooO0OO0o0OO0O0oooO', 'O00OOOooOoooOoo0o0o0oO0O', '(ILjava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/OoooO0ooO0OO0o0OO0O0oooO', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;)V'), ('com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V'), ('com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;Lnet/minecraft/world/entity/Entity;)V')])

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-11-selected-methods',len(ids)==len(set(ids))==11 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('two-declarations',len(ds)==2 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('two-bootstrap-records',len(bs)==2 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('two-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('invented-join-event-finally',lambda x:member(x,0,'(Lnet/minecraftforge/event/entity/EntityJoinLevelEvent;)V')['exception_handlers'].append({'start':0,'end':100,'handler':100,'catch':None}))
    neg('full-flag-inverted',lambda x:op(x,1,'()Z',6).update(opcode='0x9a'))
    neg('full-bit-changed',lambda x:op(x,1,'()Z',4).update(opcode='0x5'))
    neg('deferral-time-value',lambda x:op(x,0,'()V',3,'<clinit>')['reference'].update(value=300))
    neg('deferral-access-vs-write',lambda x:op(x,0,'()V',9,'<clinit>')['reference'].update(name='expireAfterWrite'))
    neg('null-level-branch',lambda x:op(x,0,'(ILjava/util/function/Consumer;)V',8,'O00OOOooOoooOoo0o0o0oO0O').update(opcode='0xc7'))
    neg('missing-entity-branch',lambda x:op(x,0,'(ILjava/util/function/Consumer;)V',18,'O00OOOooOoooOoo0o0o0oO0O').update(opcode='0xc7'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
