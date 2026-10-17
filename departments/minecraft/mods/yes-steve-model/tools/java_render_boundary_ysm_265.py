#!/usr/bin/env python3
"""Fixed-artifact animatable frame evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oo0OOoOOOOO0Oo0O0oo0O0OO', 'com/elfmcys/yesstevemodel/ooOOo000OOO0ooO0oo0ooooO', 'com/elfmcys/yesstevemodel/ooOOo000OOO0ooO0oo0ooooO$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/o0oO0OoOoOOOOoOOOOOOo0oo']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/IGeoRenderer.java', '7cefc66e910a0677e3f38e0f5135062101ff1c6f09e28e768ccd04b18bb96604', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/NativeRenderer.java', 'b8fb6c62b2ffa82798ca9832b470515963f6787e739e30f2ac549d5ff3f94076', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/NativeRenderer.java', 'b8fb6c62b2ffa82798ca9832b470515963f6787e739e30f2ac549d5ff3f94076', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/util/EModelRenderCycle.java', 'b17861f9b26e5348480e7d657e18afedd939fd6e9435e025fb3c6eb25c4ee629', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-21-methods',len(ids)==len(set(ids))==21 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('four-declarations',len(ds)==4 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('four-bootstrap-records',len(bs)==4 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('four-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    render='(Lcom/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o;Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;FLnet/minecraft/client/renderer/RenderType;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;ILcom/mojang/blaze3d/vertex/VertexConsumer;IIFFFF)V'
    wrap='(Lcom/mojang/blaze3d/vertex/VertexConsumer;Lcom/mojang/blaze3d/vertex/PoseStack$Pose;Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;[F[FIIIIFFFF)V'
    native='(Lcom/mojang/blaze3d/vertex/VertexConsumer;Lcom/mojang/blaze3d/vertex/PoseStack$Pose;Lorg/joml/Matrix4f;ZLcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;[F[FIIIIFFFFZ)V'
    neg('null-buffer-gate',lambda x:op(x,0,render,2).update(opcode='0xc6'))
    neg('all-render-mode-changed',lambda x:op(x,0,render,41).update(opcode='0x4'))
    neg('input-output-getter-swapped',lambda x:op(x,0,render,32)['reference'].update(name='o0OOooo0o0OO00OoOOOo0o0O'))
    neg('count-render-call-removed',lambda x:op(x,0,render,17)['reference'].update(name='wrong'))
    neg('compatibility-branch-inverted',lambda x:op(x,1,wrap,6).update(opcode='0x99'))
    neg('projection-matrix-operation',lambda x:op(x,1,wrap,40)['reference'].update(name='add'))
    neg('gui-scope-inverted',lambda x:op(x,1,wrap,47).update(opcode='0x99'))
    neg('invented-native-instructions',lambda x:member(x,1,native).update(instructions=[]))
    neg('native-access-removed',lambda x:member(x,1,native).update(access=10))
    neg('writer-negative-count-gate',lambda x:op(x,2,'(Lcom/mojang/blaze3d/vertex/VertexConsumer;I[F[I)V',12).update(opcode='0xa3'))
    neg('writer-normal-z-index',lambda x:op(x,2,'(Lcom/mojang/blaze3d/vertex/VertexConsumer;I[F[I)V',102).update(immediate=10))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
