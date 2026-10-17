#!/usr/bin/env python3
"""SERVER-PROPERTY-PRODUCER fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/Ooo0O0000OO0OOO0o0Oo0oOO', 'com/elfmcys/yesstevemodel/O00O00O0OoO0O0Oo0Oooo0o0', 'com/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/capability/ServerDrivenPlayerPropertiesTracker.java', '6fb5cc4e2448159627821f62a286b540f523495fadebd581b80a6afc74a6a22d', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/util/TokenBucket.java', 'f281a173e85ebe454a9942d69f2d074546cba1190274d3e3d289a7544ecda2ab', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/DispatchServerDrivenProperty.java', '5d30671bf5303fc7fc01cb6a044f95c169630147e33d77c4991ef3f07949bc50', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-39-methods',len(ids)==len(set(ids))==39 and set(ids)==set(actual))
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
    neg('sync-clear-gate-inverted',lambda x:op(x,0,'(Lnet/minecraft/server/level/ServerPlayer;Z)Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;',1,'o0OOooo0o0OO00OoOOOo0o0O').update(opcode='0x9a'))
    neg('empty-send-gate-inverted',lambda x:op(x,0,'(Lnet/minecraft/server/level/ServerPlayer;)V',7).update(opcode='0x99'))
    neg('rate-send-gate-inverted',lambda x:op(x,0,'(Lnet/minecraft/server/level/ServerPlayer;)V',17).update(opcode='0x9a'))
    neg('invented-send-finally',lambda x:member(x,0,'(Lnet/minecraft/server/level/ServerPlayer;)V')['exception_handlers'].append({'handler':0}))
    neg('wrong-rate-clock',lambda x:op(x,1,'()Z',0)['reference'].update(name='nanoTime'))
    neg('wrong-equality-rate-boundary',lambda x:op(x,1,'()Z',10).update(opcode='0x9d'))
    neg('wrong-next-time-reduction',lambda x:op(x,1,'()Z',78)['reference'].update(name='max'))
    neg('full-shield-conditional-inverted',lambda x:op(x,0,'(Lnet/minecraft/server/level/ServerPlayer;Z)Lcom/elfmcys/yesstevemodel/O00OO0Oo0O0Oo0O0Ooo0o00O;',296,'Oo0Oo0o00O00Oo0OOoOOoooo').update(opcode='0x9a'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
