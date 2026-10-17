#!/usr/bin/env python3
"""MODEL-INPUT-CARRIERS fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', 'com/elfmcys/yesstevemodel/oooOOO0o0O0oOoOO0OoOo0oo', 'com/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo', 'com/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00', 'com/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO', 'com/elfmcys/yesstevemodel/o0OOOOooooOO00oOoO0o00OO', 'com/elfmcys/yesstevemodel/oOo0o0OoO0OO0oO0ooOOoooO']
SELECTED=set([('com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', '<init>', '(Lcom/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo;[Lcom/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00;[Lcom/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO;Lcom/elfmcys/yesstevemodel/oooOOO0o0O0oOoOO0OoOo0oo;Lcom/elfmcys/yesstevemodel/o0OoOo0OOOo0oOo0oOO0O0oO;Ljava/util/Map;Ljava/util/Map;)V'), ('com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo;'), ('com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', 'o0OOooo0o0OO00OoOOOo0o0O', '()[Lcom/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00;'), ('com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', 'O00OOOooOoooOoo0o0o0oO0O', '()[Lcom/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO;'), ('com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lcom/elfmcys/yesstevemodel/oooOOO0o0O0oOoOO0OoOo0oo;'), ('com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', 'Ooooo0oooO0oooOOOoO0000O', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO', 'oo0OoO00oOoo000O0000o0oo', '()Lcom/elfmcys/yesstevemodel/o0OoOo0OOOo0oOo0oOO0O0oO;'), ('com/elfmcys/yesstevemodel/oooOOO0o0O0oOoOO0OoOo0oo', '<init>', '(Ljava/util/Map;Ljava/util/Map;Ljava/util/Map;)V'), ('com/elfmcys/yesstevemodel/oooOOO0o0O0oOoOO0OoOo0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/oooOOO0o0O0oOoOO0OoOo0oo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/oooOOO0o0O0oOoOO0OoOo0oo', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo', '<init>', '([Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Ljava/util/Map;[Lcom/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0;Lcom/elfmcys/yesstevemodel/O0OO0oooo0oO0oOOo0OOooO0;)V'), ('com/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lcom/elfmcys/yesstevemodel/O0OO0oooo0oO0oOOo0OOooO0;'), ('com/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00', '<init>', '([Ljava/lang/String;Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lcom/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO;Lcom/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0;Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;)V'), ('com/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()[Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;'), ('com/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO;'), ('com/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lcom/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0;'), ('com/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;'), ('com/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO', '<init>', '([Ljava/lang/String;Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lcom/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO;Lcom/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0;Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;)V'), ('com/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()[Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;'), ('com/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO;'), ('com/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lcom/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0;'), ('com/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;'), ('com/elfmcys/yesstevemodel/o0OOOOooooOO00oOoO0o00OO', '<init>', '(Ljava/lang/String;Ljava/util/List;Ljava/util/List;Ljava/util/List;)V'), ('com/elfmcys/yesstevemodel/oOo0o0OoO0OO0oO0ooOOoooO', '<init>', '(DLjava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/model/data/ClientModelData.java', '2a631db3292cda0e6b9bc5371340116bcf7836a453e5f35ab7028e1f7ef96bb4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/data/CommonAssetData.java', 'ea6b95c8881bccce30605fac3a3567cc23a39fd22c5f309e2adc4571082c7d24', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/data/PlayerModelData.java', 'f6c1c5ccb7e8d31d7cb5de9b52303b396c153644249b586c7db7846088161050', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/data/ProjectileModelData.java', '094b6ce60a9af0b237ce1f19bd6fa168859863089b6481d2497e8e17bc65e46b', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/data/VehicleModelData.java', 'd2ba7b0b7638c57ea6a749df7e840ddade5a0a509ce719e1c210c691a176918c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/keyframe/BoneAnimation.java', 'a658f987bbdb028b5d816a14e7cfa1bba37a9505aef9d4b2d31f51615c274cfe', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/keyframe/event/ParticleEventKeyFrame.java', 'f80bfc48bbbfcb201cddf74a89999e987d1bb40ec354427018612b2cefbdd040', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

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
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==7 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==7 and {r['owner'] for r in bs}==set(OWNERS))
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo;[Lcom/elfmcys/yesstevemodel/OO0o00OOO0oOOOo0O0Oo0O00;[Lcom/elfmcys/yesstevemodel/O0O00OoOoo0ooOOOooOOo0OO;Lcom/elfmcys/yesstevemodel/oooOOO0o0O0oOoOO0OoOo0oo;Lcom/elfmcys/yesstevemodel/o0OoOo0OOOo0oOo0oOO0O0oO;Ljava/util/Map;Ljava/util/Map;)V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'(Ljava/util/Map;Ljava/util/Map;Ljava/util/Map;)V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'([Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Ljava/util/Map;[Lcom/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0;Lcom/elfmcys/yesstevemodel/O0OO0oooo0oO0oOOo0OOooO0;)V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-3',lambda x:member(x,3,'([Ljava/lang/String;Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lcom/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO;Lcom/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0;Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;)V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-4',lambda x:member(x,4,'([Ljava/lang/String;Lcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;Lcom/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO;Lcom/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0;Lcom/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0;)V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-5',lambda x:member(x,5,'(Ljava/lang/String;Ljava/util/List;Ljava/util/List;Ljava/util/List;)V','<init>')['instructions'].pop())
    neg('missing-model-asset-helper-6',lambda x:member(x,6,'(DLjava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V','<init>')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
