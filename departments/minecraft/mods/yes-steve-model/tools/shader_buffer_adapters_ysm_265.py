#!/usr/bin/env python3
"""SHADER-BUFFER-ADAPTERS fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$o0OOooo0o0OO00OoOOOo0o0O', 'com/elfmcys/yesstevemodel/oo0OO00OOOOo0ooOOoOOo0O0', 'com/elfmcys/yesstevemodel/o0oOo0ooO00oOoooOOOoOOo0', 'com/elfmcys/yesstevemodel/mixin/client/BufferSourceMixin']
SELECTED=set([('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'O00OOOooOoooOoo0o0o0oO0O', '()Z'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()J'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'Ooooo0oooO0oooOOOoO0000O', '()J'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'oOOOo0OOO0ooooo0O00OO0o0', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/fml/ModContainer;)V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;Lnet/minecraft/server/packs/resources/ResourceManager;Lnet/coderbot/iris/texture/pbr/loader/PBRTextureLoader$PBRTextureConsumer;)V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$Oo0Oo0o00O00Oo0OOoOOoooo', 'load', '(Lnet/minecraft/client/renderer/texture/AbstractTexture;Lnet/minecraft/server/packs/resources/ResourceManager;Lnet/coderbot/iris/texture/pbr/loader/PBRTextureLoader$PBRTextureConsumer;)V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$Oo0Oo0o00O00Oo0OOoOOoooo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$o0OOooo0o0OO00OoOOOo0o0O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$o0OOooo0o0OO00OoOOOo0o0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;Lnet/minecraft/server/packs/resources/ResourceManager;Lnet/irisshaders/iris/texture/pbr/loader/PBRTextureLoader$PBRTextureConsumer;)V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$o0OOooo0o0OO00OoOOOo0o0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$o0OOooo0o0OO00OoOOOo0o0O', 'load', '(Lnet/minecraft/client/renderer/texture/AbstractTexture;Lnet/minecraft/server/packs/resources/ResourceManager;Lnet/irisshaders/iris/texture/pbr/loader/PBRTextureLoader$PBRTextureConsumer;)V'), ('com/elfmcys/yesstevemodel/OO0oooO0OO0o00oOOoOoOoOo$o0OOooo0o0OO00OoOOOo0o0O', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/oo0OO00OOOOo0ooOOoOOo0O0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oo0OO00OOOOo0ooOOoOOo0O0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/oo0OO00OOOOo0ooOOoOOo0O0', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/o0oOo0ooO00oOoooOOOoOOo0', '<init>', '(Lnet/minecraft/resources/ResourceLocation;)V'), ('com/elfmcys/yesstevemodel/o0oOo0ooO00oOoooOOOoOOo0', '<init>', '(Lnet/minecraft/client/renderer/RenderType;)V'), ('com/elfmcys/yesstevemodel/o0oOo0ooO00oOoooOOOoOOo0', 'm_5492_', '()Z'), ('com/elfmcys/yesstevemodel/o0oOo0ooO00oOoooOOOoOOo0', 'm_7280_', '()Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/o0oOo0ooO00oOoooOOOoOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/resources/ResourceLocation;)Lcom/elfmcys/yesstevemodel/o0oOo0ooO00oOoooOOOoOOo0;'), ('com/elfmcys/yesstevemodel/o0oOo0ooO00oOoooOOOoOOo0', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/mixin/client/BufferSourceMixin', '<init>', '()V'), ('com/elfmcys/yesstevemodel/mixin/client/BufferSourceMixin', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/compat/IrisCompat.java', '7e3dd22456e2e1ba9ee7661039170d981a9e4fa6118681ad96232b44afe141e6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/IrisCompat.java', '7e3dd22456e2e1ba9ee7661039170d981a9e4fa6118681ad96232b44afe141e6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/IrisCompat.java', '7e3dd22456e2e1ba9ee7661039170d981a9e4fa6118681ad96232b44afe141e6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/OptifineCompat.java', '0194068c097c18f02f34af4da3d84e23471dd8af82d7630bbb5cc6842be30b14', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/CustomTranslucentRenderType.java', 'a2110b652d21809f1437d4a67d4955fe10096b740cb83d7c27667cf0fe2e03fc', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/client/BufferSourceMixin.java', '2ee9b010b46f69e465eb37ea9caab02b1b800a00398a2fe922312870bd04d14a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-30-methods',len(ids)==len(set(ids))==30 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('six-declarations',len(ds)==6 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('six-bootstrap-records',len(bs)==6 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('six-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-buffer-mixin-annotations',e.get('mixin_annotations')==details.get('_mixin_annotations'))
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
    with zipfile.ZipFile(a.jar) as z:details['_mixin_annotations']=annotations(z.read(OWNERS[5]+'.class'))
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
    neg('missing-shader-buffer-link-0',lambda x:member(x,0,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-shader-buffer-link-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;Lnet/minecraft/server/packs/resources/ResourceManager;Lnet/coderbot/iris/texture/pbr/loader/PBRTextureLoader$PBRTextureConsumer;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-shader-buffer-link-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;Lnet/minecraft/server/packs/resources/ResourceManager;Lnet/irisshaders/iris/texture/pbr/loader/PBRTextureLoader$PBRTextureConsumer;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-shader-buffer-link-3',lambda x:member(x,3,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-shader-buffer-link-4',lambda x:member(x,4,'()Z','m_5492_')['instructions'].pop())
    neg('missing-shader-buffer-link-5',lambda x:member(x,5,'()V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-mixin-annotation-records',lambda x:x['mixin_annotations'].pop('fields'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
