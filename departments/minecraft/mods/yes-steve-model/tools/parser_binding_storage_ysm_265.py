#!/usr/bin/env python3
"""Fixed-artifact animatable frame evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOOOoooooO00ooo0o0OOOooO', 'com/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo', 'com/elfmcys/yesstevemodel/ooOO0OoOO00Ooo000o0O0o0O', 'com/elfmcys/yesstevemodel/ooo0oooo0OoO0oO0OOooO00o', 'com/elfmcys/yesstevemodel/ooo0oooo0OoO0oO0OOooO00o$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/OOoOOoOo0OoOo00ooOoo0ooo', 'com/elfmcys/yesstevemodel/OOoOOoOo0OoOo00ooOoo0ooo$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/oo0oO0o0ooo0oo0oO0oOo00O', 'com/elfmcys/yesstevemodel/oo0oO0o0ooo0oo0oO0oOo00O$Oo0Oo0o00O00Oo0OOoOOoooo']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/PrimaryBinding.java', 'a41e54a4d23aef86337ed1819d3261f714d12e42013e7d4c0a41d8e8038d69b2', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/MolangParser.java', '2bc8d31a5952adb06f14b4e0889da4da056b595eee6a51ecc3503770eec19f80', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/parser/MolangParserImpl.java', '5a4aaacfd4eef8c44e301347a0b33535e04a14ba24e03d3904cb5d27896f1608', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/variable/ScopedVariableBinding.java', '2192e29766c51f32e166319ae40d2d5dac8a2ca502cfc2f4b27ad602f0cae060', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/variable/ScopedVariableBinding.java', '2192e29766c51f32e166319ae40d2d5dac8a2ca502cfc2f4b27ad602f0cae060', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/variable/ContextVariableBinding.java', '6c17d769162e4f88608d7a50527987f710735f2a4c71af5b2424c3778a61cc46', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/variable/ContextVariableBinding.java', '6c17d769162e4f88608d7a50527987f710735f2a4c71af5b2424c3778a61cc46', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/variable/TempVariableBinding.java', 'f4e69689757582d7ec4a480edbd5aa334d0ab7fbd5f7abc356035efb1e372ee7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/variable/TempVariableBinding.java', 'f4e69689757582d7ec4a480edbd5aa334d0ab7fbd5f7abc356035efb1e372ee7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-43-methods',len(ids)==len(set(ids))==43 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('nine-declarations',len(ds)==9 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('nine-bootstrap-records',len(bs)==9 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('nine-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    parse='(Ljava/lang/String;Z)Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;'
    neg('parser-catch-Throwable',lambda x:member(x,1,parse,'Oo0Oo0o00O00Oo0OOoOOoooo')['exception_handlers'][0].update(catch='java/lang/Throwable'))
    neg('invented-unsafe-parse-finally',lambda x:member(x,1,parse,'o0OOooo0o0OO00OoOOOo0o0O')['exception_handlers'].append({'start':0,'end':50,'handler':50,'catch':None}))
    neg('missing-temp-reset-body',lambda x:member(x,7,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('user-function-comment-gate',lambda x:op(x,1,parse,9,'o0OOooo0o0OO00OoOOOo0o0O').update(opcode='0x9a'))
    neg('transient-reset-call-removed',lambda x:op(x,1,parse,34,'o0OOooo0o0OO00OoOOOo0o0O')['reference'].update(name='wrong'))
    neg('context-null-read-gate',lambda x:op(x,6,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;)Ljava/lang/Object;',16).update(opcode='0xc7'))
    neg('context-null-write-gate',lambda x:op(x,6,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Ljava/lang/Object;)V',16).update(opcode='0xc7'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
