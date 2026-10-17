#!/usr/bin/env python3
"""GUI-PREVIEW-STATE fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'com/elfmcys/yesstevemodel/oOoOo0Oo0O00Oo0O0oOOOo0o', 'com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo']
SELECTED=set([('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Z)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'o0OOooo0o0OO00OoOOOo0o0O', '(Z)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'O00OOOooOoooOoo0o0o0oO0O', '(Z)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'O00OOOooOoooOoo0o0o0oO0O', '()Z'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'oOOOo0OOO0ooooo0O00OO0o0', '()Z'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lcom/mojang/blaze3d/vertex/PoseStack;F)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFFFFFLcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Lcom/elfmcys/yesstevemodel/OOoo0o0oO000ooO0Oo00OoOo;Z)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFFLnet/minecraft/client/renderer/MultiBufferSource$BufferSource;)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'o0OOooo0o0OO00OoOOOo0o0O', '(FFFLnet/minecraft/client/renderer/MultiBufferSource$BufferSource;)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FLcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/entity/EntityRenderDispatcher;Lnet/minecraft/client/renderer/MultiBufferSource$BufferSource;)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FLnet/minecraft/world/entity/Entity;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/entity/EntityRenderDispatcher;Lnet/minecraft/client/renderer/MultiBufferSource$BufferSource;Lnet/minecraft/world/entity/Entity;F)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FFFFLcom/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00;Lcom/elfmcys/yesstevemodel/OOoo0o0oO000ooO0Oo00OoOo;ZZ)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/gui/GuiGraphics;Lnet/minecraft/client/player/LocalPlayer;DDFFIF)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/renderer/entity/EntityRenderDispatcher;Lnet/minecraft/client/player/LocalPlayer;FLnet/minecraft/client/gui/GuiGraphics;)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOoo0o0oO000ooO0Oo00OoOo;Lcom/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00;FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource$BufferSource;)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/world/entity/Entity;'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/world/entity/Entity;'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'O00OOOooOoooOoo0o0o0oO0O', '(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/world/entity/Entity;'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo;Lcom/mojang/blaze3d/vertex/PoseStack;FLnet/minecraft/world/entity/LivingEntity;FLnet/minecraft/client/renderer/entity/EntityRenderDispatcher;Lnet/minecraft/client/renderer/MultiBufferSource$BufferSource;FFZLcom/elfmcys/yesstevemodel/OOoo0o0oO000ooO0Oo00OoOo;)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/entity/Entity;FLcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/oOOo0Ooo0oOoo0O0OOOOo0oo;)V'), ('com/elfmcys/yesstevemodel/OoO00Oo00Ooo0OoOoo00o000', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/oOoOo0Oo0O00Oo0O0oOOOo0o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOoOo0Oo0O00Oo0O0oOOOo0o', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'Ooo0O0000OO0OOO0o0Oo0oOO', '()V'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/oO0Ooo00oOOO00O0OO00o0o0;'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'ooOO000o0O0OOOoO0Oo0o0Oo', '()Lcom/elfmcys/yesstevemodel/ooOOOoOOOOo0ooooo0O0O0OO;'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Z)V'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'oo00OoO0Oo0OO0oOoOoOoOo0', '()Z'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'o0oOoOOo0ooo00Oo0oo0o00O', '()Z'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'oOo0oOOOO0ooOOO0oOoOO0oo', '()I'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'o0oOOoOooOoOOO0oOoOOoo00', '()Z'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'o0OOooo0o0OO00OoOOOo0o0O', '(FZ)Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/player/Player;)Z'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;)Z'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'O0o00oO0O0ooOOOo0oo0Oo00', '()Lcom/elfmcys/yesstevemodel/oOO0oO0ooo000OoOO0OOooOo;'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;Z)Lcom/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00$Oo0Oo0o00O00Oo0OOoOOoooo;'), ('com/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;Z)Lcom/elfmcys/yesstevemodel/oOo00OoOO00O000ooO0Oo00o$Oo0Oo0o00O00Oo0OOoOOoooo;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/util/RenderUtil.java', 'b181c57910eeb0db57a69b7b956b5b74dd03275ad285470709e80c9aaaa2fae1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/util/AnimatableCacheUtil.java', 'ffb78e89230046641dca0d962a0f9d85343c80443265e54a9e6873448d412435', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/gui/CustomGuiPlayerEntity.java', 'd835c5c2e24d03466a826fb5698ea4306ee3705758d2cf6799ee0ae141f83275', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-41-methods',len(ids)==len(set(ids))==41 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-gui-preview-link-0',lambda x:member(x,0,'(Z)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-gui-preview-link-1',lambda x:member(x,1,'()V','<clinit>')['instructions'].pop())
    neg('missing-gui-preview-link-2',lambda x:member(x,2,'()V','Ooo0O0000OO0OOO0o0Oo0oOO')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
