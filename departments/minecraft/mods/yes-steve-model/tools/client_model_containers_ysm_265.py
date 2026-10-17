#!/usr/bin/env python3
"""CLIENT-MODEL-CONTAINERS fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'com/elfmcys/yesstevemodel/OoOoOOoO0oO0o00Oo00o0Oo0', 'com/elfmcys/yesstevemodel/ooO0Oooo00ooo0oo00OOoooO', 'com/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O']
SELECTED=set([('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', '<init>', '(Lcom/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00;Ljava/util/Map;Ljava/util/Map;Lcom/elfmcys/yesstevemodel/OoO00O0oOo0000oo0OOO0oO0;Lcom/elfmcys/yesstevemodel/o0OoOo0OOOo0oOo0oOO0O0oO;Lcom/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O;Ljava/util/List;)V'), ('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00;'), ('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/OoO00O0oOo0000oo0OOO0oO0;'), ('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'oOOOo0OOO0ooooo0O00OO0o0', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'Ooooo0oooO0oooOOOoO0000O', '()Lcom/elfmcys/yesstevemodel/o0OoOo0OOOo0oOo0oOO0O0oO;'), ('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'oo0OoO00oOoo000O0000o0oo', '()Lcom/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O;'), ('com/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', '<init>', '(Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;Lcom/elfmcys/yesstevemodel/oO0OoOoo00ooooO00OoOO00O;Lcom/elfmcys/yesstevemodel/ooOoooooO0OoOOOO0oO0OooO;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;Lcom/elfmcys/yesstevemodel/O0OO0oooo0oO0oOOo0OOooO0;Ljava/lang/String;Lnet/minecraft/client/renderer/texture/AbstractTexture;Lcom/elfmcys/yesstevemodel/OoO00O0oOo0000oo0OOO0oO0;)V'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'O00OOOooOoooOoo0o0o0oO0O', '()Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Lcom/elfmcys/yesstevemodel/oO0OoOoo00ooooO00OoOO00O;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'Ooooo0oooO0oooOOOoO0000O', '()Lcom/elfmcys/yesstevemodel/ooOoooooO0OoOOOO0oO0OooO;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'oo0OoO00oOoo000O0000o0oo', '()Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'oooooooOOoOOoO00OooOo00O', '()Lcom/elfmcys/yesstevemodel/O0OO0oooo0oO0oOOo0OOooO0;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'Oo00o0OooOOo0ooOoo0oO0o0', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'o0OOO0o0o0OOo000oO00o00O', '()Lnet/minecraft/client/renderer/texture/AbstractTexture;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'O0OooOo0oOOoOoOoOooO000o', '()Ljava/util/function/Consumer;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'ooOO000o0O0OOOoO0Oo0o0Oo', '()Ljava/util/function/Consumer;'), ('com/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00', 'OOOo0OOOoOO0O00Oo00ooOOO', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OoOoOOoO0oO0o00Oo00o0Oo0', '<init>', '(Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;Lnet/minecraft/client/renderer/texture/AbstractTexture;Lcom/elfmcys/yesstevemodel/OoO00O0oOo0000oo0OOO0oO0;)V'), ('com/elfmcys/yesstevemodel/OoOoOOoO0oO0o00Oo00o0Oo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;'), ('com/elfmcys/yesstevemodel/OoOoOOoO0oO0o00Oo00o0Oo0', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;'), ('com/elfmcys/yesstevemodel/OoOoOOoO0oO0o00Oo00o0Oo0', 'O00OOOooOoooOoo0o0o0oO0O', '()Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;'), ('com/elfmcys/yesstevemodel/OoOoOOoO0oO0o00Oo00o0Oo0', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lnet/minecraft/client/renderer/texture/AbstractTexture;'), ('com/elfmcys/yesstevemodel/OoOoOOoO0oO0o00Oo00o0Oo0', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Ljava/util/function/Consumer;'), ('com/elfmcys/yesstevemodel/ooO0Oooo00ooo0oo00OOoooO', '<init>', '(Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;Lnet/minecraft/client/renderer/texture/AbstractTexture;Lcom/elfmcys/yesstevemodel/OoO00O0oOo0000oo0OOO0oO0;)V'), ('com/elfmcys/yesstevemodel/ooO0Oooo00ooo0oo00OOoooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;'), ('com/elfmcys/yesstevemodel/ooO0Oooo00ooo0oo00OOoooO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;'), ('com/elfmcys/yesstevemodel/ooO0Oooo00ooo0oo00OOoooO', 'O00OOOooOoooOoo0o0o0oO0O', '()Lit/unimi/dsi/fastutil/objects/Object2ReferenceMap;'), ('com/elfmcys/yesstevemodel/ooO0Oooo00ooo0oo00OOoooO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lnet/minecraft/client/renderer/texture/AbstractTexture;'), ('com/elfmcys/yesstevemodel/ooO0Oooo00ooo0oo00OOoooO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Ljava/util/function/Consumer;'), ('com/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O', '<init>', '(Ljava/lang/String;ZLjava/util/Map;Ljava/util/Map;)V'), ('com/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Z)V'), ('com/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lnet/minecraft/client/renderer/texture/AbstractTexture;'), ('com/elfmcys/yesstevemodel/OO0oO0000O0O00o0O0oo0O0O', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Lnet/minecraft/client/renderer/texture/AbstractTexture;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/model/ClientModel.java', '65fb2a79d2a37ff17cf515c2e1a1aeacb87d0399af63160c9969f37dfc29c6ab', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/PlayerModel.java', 'dbc92edc7437667bdbdf2368aa4974f8e63c8201ad9016c16d6ee1baa7fd1522', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/ProjectileModel.java', 'a0078cf8d1eddbcaf519db5d70d3632ffc33b4821c9e294df90da85d450d7d44', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/VehicleModel.java', '5299d0b1f6e9d835d1881a0ebf3b3e7b610a0df283f2864421ad237d11b880ff', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/ClientModelInfo.java', '8d1cb9e7f7c7381c8a0a7fd07ed88440afa65934f587e157f02c41d26d8e5d9c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-42-methods',len(ids)==len(set(ids))==42 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'()Lcom/elfmcys/yesstevemodel/Oo0o0o0o0OOo0000ooo00o00;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-3',lambda x:member(x,3,'()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-4',lambda x:member(x,4,'()Ljava/lang/String;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
