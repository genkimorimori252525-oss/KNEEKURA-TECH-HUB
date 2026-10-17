#!/usr/bin/env python3
"""RENDER-BRIDGE-PAPERDOLL-ENTRY fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O00OOOooOoooOoo0o0o0oO0O', 'com/elfmcys/yesstevemodel/mixin/client/LivingRendererMixin', 'com/elfmcys/yesstevemodel/O0O00oOoOoooOOooo0OOOoO0', 'com/elfmcys/yesstevemodel/o0Oo00ooo0o0o0ooO0ooo0oo']
SELECTED=set([('com/elfmcys/yesstevemodel/O00OOOooOoooOoo0o0o0oO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/mixin/client/LivingRendererMixin', '<init>', '(Lnet/minecraft/client/renderer/entity/EntityRendererProvider$Context;)V'), ('com/elfmcys/yesstevemodel/mixin/client/LivingRendererMixin', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/LivingEntity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/O0O00oOoOoooOOooo0OOOoO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0O00oOoOoooOOooo0OOOoO0', 'render', '(Lnet/minecraftforge/client/gui/overlay/ForgeGui;Lnet/minecraft/client/gui/GuiGraphics;FII)V'), ('com/elfmcys/yesstevemodel/o0Oo00ooo0o0o0ooO0ooo0oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0Oo00ooo0o0o0ooO0ooo0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/common/ForgeConfigSpec$Builder;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/api/ILivingRenderer.java', '64aad3c77824d4bf551cf929b0cde5f2db7a4bbdf13af7dccda7ced224b78901', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/client/LivingRendererMixin.java', 'd6ce6193a16072f68490390cf17ee23bc28f9c9823eb933aee1ac7f68153a63e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/gui/overlay/ExtraPlayerScreen.java', 'ff88487045a1838148ac4ce6856201e3f0d4f81652eaa3e2adebb648e0794dd3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/config/ExtraPlayerScreenConfig.java', 'b61949e050953d9de7a58644a4ce545a89837a3c959fc6cf70ef259ce60a473d', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-7-methods',len(ids)==len(set(ids))==7 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('fixed-owner-declarations',len(ds)==4 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('fixed-bootstrap-records',len(bs)==4 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-render-entry-annotations',e.get('event_annotations')==details.get('_event_annotations'))
    ck('exact-render-bridge-metadata',e.get('bridge_mixin_metadata')==details.get('_bridge_metadata'))
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
    with zipfile.ZipFile(a.jar) as z:
        details['_event_annotations']=[annotations(z.read(o+'.class')) for o in OWNERS]
        cfg=json.loads(z.read('yes_steve_model.mixins.json'));ref=json.loads(z.read('yes_steve_model.refmap.json'))
        details['_bridge_metadata']={'configured_client':'client.LivingRendererMixin' in cfg.get('client',[]),'refmap':ref.get('mappings',{}).get(OWNERS[1]),'runtime_injection_verified':False}
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
    neg('changed-render-entry-owner-0',lambda x:member(x,0,'(Lnet/minecraft/world/entity/LivingEntity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V','Oo0Oo0o00O00Oo0OOoOOoooo').update(instructions=[]))
    neg('changed-render-entry-owner-1',lambda x:member(x,1,'(Lnet/minecraft/client/renderer/entity/EntityRendererProvider$Context;)V','<init>')['instructions'].pop())
    neg('changed-render-entry-owner-2',lambda x:member(x,2,'()V','<init>')['instructions'].pop())
    neg('changed-render-entry-owner-3',lambda x:member(x,3,'()V','<init>')['instructions'].pop())
    neg('missing-bridge-metadata',lambda x:x.pop('bridge_mixin_metadata'))
    neg('missing-entry-annotations',lambda x:x['event_annotations'].pop())
    neg('invented-live-injection',lambda x:x['bridge_mixin_metadata'].update(runtime_injection_verified=True))
    neg('wrong-super-invocation',lambda x:op(x,1,'(Lnet/minecraft/world/entity/LivingEntity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V',10).update(opcode='0xb6'))
    neg('reversed-overlay-disable-gate',lambda x:op(x,2,'(Lnet/minecraftforge/client/gui/overlay/ForgeGui;Lnet/minecraft/client/gui/GuiGraphics;FII)V',12).update(opcode='0x9a'))
    neg('wrong-frame-clock-call',lambda x:op(x,2,'(Lnet/minecraftforge/client/gui/overlay/ForgeGui;Lnet/minecraft/client/gui/GuiGraphics;FII)V',120)['reference'].update(name='missing'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
