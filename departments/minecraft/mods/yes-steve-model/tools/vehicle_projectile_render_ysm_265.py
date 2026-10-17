#!/usr/bin/env python3
"""VEHICLE-PROJECTILE-RENDER fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oo00OO0OO0o000oo0oOOoo0O', 'com/elfmcys/yesstevemodel/O0Oo000OO0O00oooO00Oo0OO', 'com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', 'com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO']
SELECTED=set([('com/elfmcys/yesstevemodel/oo00OO0OO0o000oo0oOOoo0O', '<init>', '(Lnet/minecraft/client/renderer/entity/EntityRendererProvider$Context;)V'), ('com/elfmcys/yesstevemodel/oo00OO0OO0o000oo0oOOoo0O', 'm_7392_', '(Lnet/minecraft/world/entity/Entity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/oo00OO0OO0o000oo0oOOoo0O', 'm_5478_', '(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/oo00OO0OO0o000oo0oOOoo0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;ILcom/elfmcys/yesstevemodel/oOOo0Ooo0oOoo0O0OOOOo0oo;)V'), ('com/elfmcys/yesstevemodel/O0Oo000OO0O00oooO00Oo0OO', '<init>', '(Lnet/minecraft/client/renderer/entity/EntityRendererProvider$Context;)V'), ('com/elfmcys/yesstevemodel/O0Oo000OO0O00oooO00Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/projectile/Projectile;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/O0Oo000OO0O00oooO00Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/projectile/Projectile;)Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/O0Oo000OO0O00oooO00Oo0OO', 'm_5478_', '(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/O0Oo000OO0O00oooO00Oo0OO', 'm_7392_', '(Lnet/minecraft/world/entity/Entity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/O0Oo000OO0O00oooO00Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;ILcom/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO;)V'), ('com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', '<init>', '(Lnet/minecraft/client/renderer/entity/EntityRendererProvider$Context;)V'), ('com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Lcom/mojang/blaze3d/vertex/PoseStack;FLnet/minecraft/client/renderer/MultiBufferSource;Lcom/mojang/blaze3d/vertex/VertexConsumer;IIFFFF)V'), ('com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;F)I'), ('com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/O0oOO0o0O0OOO0000ooooooo;'), ('com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0oOO0o0O0OOO0000ooooooo;)V'), ('com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/renderer/MultiBufferSource;)V'), ('com/elfmcys/yesstevemodel/oOoOOO0OOOoo000O0o0oo0OO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lnet/minecraft/client/renderer/MultiBufferSource;'), ('com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO', '<init>', '(Lnet/minecraft/client/renderer/entity/EntityRendererProvider$Context;)V'), ('com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Lcom/mojang/blaze3d/vertex/PoseStack;FLnet/minecraft/client/renderer/MultiBufferSource;Lcom/mojang/blaze3d/vertex/VertexConsumer;IIFFFF)V'), ('com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;F)I'), ('com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/O0oOO0o0O0OOO0000ooooooo;'), ('com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0oOO0o0O0OOO0000ooooooo;)V'), ('com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/renderer/MultiBufferSource;)V'), ('com/elfmcys/yesstevemodel/Oo00o0oOoo00O00ooooOo0OO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lnet/minecraft/client/renderer/MultiBufferSource;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/renderer/CustomVehicleRenderer.java', '4d7ef22e2ce968648818cd639b042af3abe6fa065d32107ff749a18df4cb4662', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/renderer/CustomProjectileRenderer.java', 'f0cd8f5a457a3a2f043ad3b079c2eea0d24078da6ac02cc647a98ef810008608', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/GeoEntityRenderer.java', 'b75697f58f987fd99cb108eae7fd5366e97ecf71fad50fc9e50ef038adde818b', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/GeoProjectilesRenderer.java', '2a10be03ffc043417e4989c342552656709e1f99c1c4eb80a05d47c9483d0386', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-26-methods',len(ids)==len(set(ids))==26 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('four-declarations',len(ds)==4 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('four-bootstrap-records',len(bs)==4 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('four-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-vehicle-projectile-render-link-0',lambda x:member(x,0,'(Lnet/minecraft/world/entity/Entity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V','m_7392_')['instructions'].pop())
    neg('missing-vehicle-projectile-render-link-1',lambda x:member(x,1,'(Lnet/minecraft/world/entity/projectile/Projectile;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-vehicle-projectile-render-link-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-vehicle-projectile-render-link-3',lambda x:member(x,3,'(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
