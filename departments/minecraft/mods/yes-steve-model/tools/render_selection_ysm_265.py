#!/usr/bin/env python3
"""Fixed-artifact animatable frame evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o0O0000ooOOO0O0oo0OOOoOo', 'com/elfmcys/yesstevemodel/OOoo0o0oO000ooO0Oo00OoOo', 'com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/event/ClientTickEvent.java', '953c3af0889e057d91d01e9eb508092112502b9d975599c303034aabb5b3eb83', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/GeoReplacedEntityRenderer.java', 'e2304eea61dd72ce6cb32cbeb8ac4832e32ef20a831ed1e2057a36047b8baa5c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/entity/CustomHumanoidEntity.java', 'a5def776d16ae1164d7f559ddb0809a979b253f8c4b0367c471486d81c6246e0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-54-methods',len(ids)==len(set(ids))==54 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    render='(Lcom/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00;Lnet/minecraft/resources/ResourceLocation;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'
    neg('cancel-pre-event-gate',lambda x:op(x,1,render,31).update(opcode='0x9a'))
    neg('missing-animation-skips-tail',lambda x:op(x,1,render,59).update(branch_target=620))
    neg('no-local-player-gate',lambda x:op(x,1,render,67).update(opcode='0xc7'))
    neg('texture-override-null-gate',lambda x:op(x,1,render,309).update(opcode='0xc6'))
    neg('render-type-null-body-gate',lambda x:op(x,1,render,462).update(opcode='0xc7'))
    neg('layer-order-reversed',lambda x:op(x,1,render,432).update(opcode='0x9a'))
    neg('post-event-removed',lambda x:op(x,1,render,614)['reference'].update(name='wrong'))
    neg('invented-pose-finally',lambda x:member(x,1,render)['exception_handlers'].append({'start':0,'end':620,'handler':620,'catch':None}))
    neg('tick-phase-inverted',lambda x:op(x,0,'(Lnet/minecraftforge/event/TickEvent$ClientTickEvent;)V',14).update(opcode='0xa5'))
    neg('texture-tick-order',lambda x:op(x,0,'(Lnet/minecraftforge/event/TickEvent$ClientTickEvent;)V',26)['reference'].update(name='wrong'))
    neg('humanoid-fallback-gate',lambda x:op(x,2,'()Lnet/minecraft/resources/ResourceLocation;',4).update(opcode='0x9a'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
