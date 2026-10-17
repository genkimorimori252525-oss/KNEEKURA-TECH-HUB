#!/usr/bin/env python3
"""MAID-RENDER-CAPABILITY fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'com/elfmcys/yesstevemodel/OO0oo0O00O0Oo0O00000o0oO', 'com/elfmcys/yesstevemodel/OO0oo0O00O0Oo0O00000o0oO$1', 'com/elfmcys/yesstevemodel/O0oOO0oooooO0O0oooOO0OOO', 'com/elfmcys/yesstevemodel/oOOO00oO000oOo0O000OO0Oo', 'com/elfmcys/yesstevemodel/O00Ooo00ooOO0OOoo0oOO000']
SELECTED=set([('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', '<init>', '(Lnet/minecraft/client/renderer/entity/EntityRendererProvider$Context;)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;)Lcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;)Lcom/github/tartaricacid/touhoulittlemaid/geckolib3/geo/IGeoEntity;'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'addGeoLayerRenderer', '(Lcom/github/tartaricacid/touhoulittlemaid/geckolib3/geo/GeoLayerRenderer;)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;)Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;ILcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O00OoOOOOoOOOO0OOOoO0ooO;)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;Lcom/mojang/blaze3d/vertex/PoseStack;FFF)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'm_7523_', '(Lnet/minecraft/world/entity/LivingEntity;Lcom/mojang/blaze3d/vertex/PoseStack;FFF)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00;FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;ILcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O00OoOOOOoOOOO0OOOoO0ooO;)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'm_5478_', '(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'geoRender', '(Lnet/minecraft/world/entity/Entity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'getGeoEntity', '(Lnet/minecraft/world/entity/Entity;)Lcom/github/tartaricacid/touhoulittlemaid/geckolib3/geo/IGeoEntity;'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;ILcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;)V'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'oOOOo0OOO0ooooo0O00OO0o0', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;)Lcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;)Lcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;'), ('com/elfmcys/yesstevemodel/O00OOo0oo0O000OOooOOooOo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OO0oo0O00O0Oo0O00000o0oO', '<init>', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;)V'), ('com/elfmcys/yesstevemodel/OO0oo0O00O0Oo0O00000o0oO', 'getCapability', '(Lnet/minecraftforge/common/capabilities/Capability;Lnet/minecraft/core/Direction;)Lnet/minecraftforge/common/util/LazyOptional;'), ('com/elfmcys/yesstevemodel/OO0oo0O00O0Oo0O00000o0oO', 'getCapability', '(Lnet/minecraftforge/common/capabilities/Capability;)Lnet/minecraftforge/common/util/LazyOptional;'), ('com/elfmcys/yesstevemodel/OO0oo0O00O0Oo0O00000o0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;'), ('com/elfmcys/yesstevemodel/OO0oo0O00O0Oo0O00000o0oO', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OO0oo0O00O0Oo0O00000o0oO$1', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0oOO0oooooO0O0oooOO0OOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0oOO0oooooO0O0oooOO0OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/compat/ysm/event/YsmMaidClientTickEvent;)V'), ('com/elfmcys/yesstevemodel/O0oOO0oooooO0O0oooOO0OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;)V'), ('com/elfmcys/yesstevemodel/O0oOO0oooooO0O0oooOO0OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;)V'), ('com/elfmcys/yesstevemodel/oOOO00oO000oOo0O000OO0Oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O00Ooo00ooOO0OOoo0oOO000', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O00Ooo00ooOO0OOoo0oOO000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/AttachCapabilitiesEvent;)V'), ('com/elfmcys/yesstevemodel/O00Ooo00ooOO0OOoo0oOO000', '<clinit>', '()V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/client/render/CustomYsmMaidRenderer.java', 'd93f3e0583c223cd154add7a2cc689f322bc8d00f72869b5d80ac0850b84c37f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/capability/YsmMaidCapabilityProvider.java', '1565f25f7b6c8037cdf21fc1c84963b53f14e929b08f2603c2685d218fc99e7c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/capability/YsmMaidCapabilityProvider.java', '1565f25f7b6c8037cdf21fc1c84963b53f14e929b08f2603c2685d218fc99e7c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/client/event/YsmMaidTickEvent.java', '970149450c8cd098c49136e897d470c913129406f9283685bbdaf5c905c0f1c7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/client/event/UpdateRemoteStruct.java', 'e4909b891001a9363c6ade164a9769ec7cbb3a793f1fd90e6b354ac2f787e584', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/client/event/SyncCapability.java', '80bf97ae45efb9340df2ea3dc7613fef9123f0989591416db135ce40141bcaa8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-31-methods',len(ids)==len(set(ids))==31 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==6 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==6 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-maid-render-event-annotations',e.get('event_annotations')==details.get('_event_annotations'))
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'(Lnet/minecraft/client/renderer/entity/EntityRendererProvider$Context;)V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;)V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'()V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-3',lambda x:member(x,3,'()V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-4',lambda x:member(x,4,'()V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-5',lambda x:member(x,5,'()V','<init>')['instructions'].pop())
    neg('missing-event-annotations',lambda x:x['event_annotations'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
