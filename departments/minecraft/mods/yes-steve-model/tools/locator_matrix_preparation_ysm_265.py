#!/usr/bin/env python3
"""LOCATOR-MATRIX-PREPARATION fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'com/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0']
SELECTED=set([('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)V'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)V'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)Z'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'oOOOo0OOO0ooooo0O00OO0o0', '(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)V'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)V'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'Ooooo0oooO0oooOOOoO0000O', '(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)V'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'oo0OoO00oOoo000O0000o0oo', '(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)Z'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/mojang/blaze3d/vertex/PoseStack;Ljava/util/List;)Z'), ('com/elfmcys/yesstevemodel/o000OO00oooOo00000ooo0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lorg/joml/Matrix4f;Lorg/joml/Matrix4f;)Lorg/joml/Matrix4f;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', '<init>', '(Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;)V'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lit/unimi/dsi/fastutil/ints/IntList;)Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()[F'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'o0OOooo0o0OO00OoOOOo0o0O', '()[F'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'O00OOOooOoooOoo0o0o0oO0O', '()Lit/unimi/dsi/fastutil/ints/Int2ReferenceMap;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'Ooooo0oooO0oooOOOoO0000O', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'oo0OoO00oOoo000O0000o0oo', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'oooooooOOoOOoO00OooOo00O', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'Oo00o0OooOOo0ooOoo0oO0o0', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'o0OOO0o0o0OOo000oO00o00O', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'O0OooOo0oOOoOoOoOooO000o', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'ooOO000o0O0OOOoO0Oo0o0Oo', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'OOOo0OOOoOO0O00Oo00ooOOO', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'oOo0o0000OOOO0OooooO00oo', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'O0ooooOO0oOo000O0Oo00OOO', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'OO0ooO00OoO00o0OO0OOooO0', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'Ooo0O0000OO0OOO0o0Oo0oOO', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'o0o0Oooo00OoOoOOOooo0000', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'ooooO0o00oO0Oo0OOo0O0O0o', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'oOOo0Ooo0oOoo0O0OOOOo0oo', '()Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'O0o00oO0O0ooOOOo0oo0Oo00', '()Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'oOOOooO00oo0oOooooOO0Oo0', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'OO0O00oO0OOO00oOO0OoO0OO', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lit/unimi/dsi/fastutil/objects/ReferenceArrayList;I)V'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lit/unimi/dsi/fastutil/ints/IntList;)V'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'O00OOOooOoooOoo0o0o0oO0O', '(Lit/unimi/dsi/fastutil/ints/IntList;)V'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', 'oOOOo0OOO0ooooo0O00OO0o0', '(Lit/unimi/dsi/fastutil/ints/IntList;)V'), ('com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0', '<init>', '([Lcom/elfmcys/yesstevemodel/oO0OO0OooO0Oo0OoO0oOooo0;[[Ljava/lang/String;[ZLcom/elfmcys/yesstevemodel/OOoOoO0000OooOOoO0ooOOOo;[ZJ)V'), ('com/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '([Ljava/lang/String;)Lit/unimi/dsi/fastutil/ints/IntList;'), ('com/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0', 'o0OOooo0o0OO00OoOOOo0o0O', '()[F'), ('com/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(J)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/util/RenderUtils.java', 'e535b135c19ab0f5a1ece295741a5d76c672c9d42d154e9587529c60d176050c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/model/GeoModelState.java', '9076ef19fa5757ceb38ef4898985fe53d5be06d5e7f88d56ce163f86a8752424', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/render/built/GeoModel.java', '5d0da0ded47ce366e85c248251ffe0268646969870876c2086548126863947cb', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-46-methods',len(ids)==len(set(ids))==46 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-locator-matrix-link-0',lambda x:member(x,0,'(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/elfmcys/yesstevemodel/Oo0o00oOOo0OO000000O0oO0;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-locator-matrix-link-1',lambda x:member(x,1,'(Lit/unimi/dsi/fastutil/ints/IntList;)Ljava/util/List;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-locator-matrix-link-2',lambda x:member(x,2,'([Ljava/lang/String;)Lit/unimi/dsi/fastutil/ints/IntList;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
