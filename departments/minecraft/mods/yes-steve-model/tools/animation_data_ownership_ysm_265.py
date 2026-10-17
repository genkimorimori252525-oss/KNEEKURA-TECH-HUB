#!/usr/bin/env python3
"""ANIMATION-DATA-OWNERSHIP fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/Oo0OOo00Oo00oO00Ooo0O00O', 'com/elfmcys/yesstevemodel/ooOo0OoOoo0ooOOoOO0o000O', 'com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'com/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO', 'com/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0']
SELECTED=set([('com/elfmcys/yesstevemodel/Oo0OOo00Oo00oO00Ooo0O00O', '<init>', '(Ljava/lang/String;DLcom/elfmcys/yesstevemodel/OooOO0OOOoO0oOO0OOOO0Ooo;Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;Ljava/lang/Boolean;[Lcom/elfmcys/yesstevemodel/o0OOOOooooOO00oOoO0o00OO;[Lcom/elfmcys/yesstevemodel/oOO0OoOooOOOooOo0O00Oooo;[Lcom/elfmcys/yesstevemodel/oOo0o0OoO0OO0oO0ooOOoooO;[Lcom/elfmcys/yesstevemodel/oOO0OoOooOOOooOo0O00Oooo;)V'), ('com/elfmcys/yesstevemodel/Oo0OOo00Oo00oO00Ooo0O00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/ooOo0OoOoo0ooOOoOO0o000O', '<init>', '(Ljava/lang/String;[Lcom/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO;)V'), ('com/elfmcys/yesstevemodel/ooOo0OoOoo0ooOOoOO0o000O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()I'), ('com/elfmcys/yesstevemodel/ooOo0OoOoo0ooOOoOO0o000O', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lit/unimi/dsi/fastutil/ints/Int2ReferenceMap;'), ('com/elfmcys/yesstevemodel/ooOo0OoOoo0ooOOoOO0o000O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO;)Lcom/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', '<init>', '(Ljava/lang/String;[Lorg/apache/commons/lang3/tuple/Pair;[Lorg/apache/commons/lang3/tuple/Pair;[Ljava/lang/String;[Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;[Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;Lcom/elfmcys/yesstevemodel/o0OoOoOO0oooO0O000oO0o0o;Z)V'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'o0OOooo0o0OO00OoOOOo0o0O', '()I'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'O00OOOooOoooOoo0o0o0oO0O', '()Z'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'Ooooo0oooO0oooOOOoO0000O', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'oo0OoO00oOoo000O0000o0oo', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'oooooooOOoOOoO00OooOo00O', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'Oo00o0OooOOo0ooOoo0oO0o0', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'o0OOO0o0o0OOo000oO00o00O', '()Lcom/elfmcys/yesstevemodel/o0OoOoOO0oooO0O000oO0o0o;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'O0OooOo0oOOoOoOoOooO000o', '()Z'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)[Lit/unimi/dsi/fastutil/ints/IntReferenceImmutablePair;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lorg/apache/commons/lang3/tuple/Pair;)Lit/unimi/dsi/fastutil/ints/IntReferenceImmutablePair;'), ('com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO', '<init>', '(Ljava/util/Map;)V'), ('com/elfmcys/yesstevemodel/OOo00OOOOO0OOOooOo0OOoOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0', '<init>', '(Ljava/util/Map;)V'), ('com/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/util/Map;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/builder/Animation.java', '7ef7fb6ab61134b362fdb2e899bc54e9b6e8f78035845f4e71351c969fb946b0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/builder/controller/AnimationControllerData.java', 'a019d279b4889fe05554fb1bad791c7990064b222abfae516f390f6d39f3ebfd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/builder/controller/AnimationControllerState.java', '9ba39899756ac5f182dfda234f68ef629d671c2358a0979057d380d9443a82d3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/file/AnimationFile.java', '30d1229bb562b4b3a5e3339ccb8357f362113634960924ef12fca06b4cb27c00', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/file/AnimationControllerFile.java', 'df196ffa0b43d94f86fad1ac71b6aaa9f383a6a298bb3f007089ee9de23ce5bf', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-25-methods',len(ids)==len(set(ids))==25 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('five-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('five-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('five-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-animation-data-link-0',lambda x:member(x,0,'()Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-animation-data-link-1',lambda x:member(x,1,'()I','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-animation-data-link-2',lambda x:member(x,2,'()Ljava/lang/String;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-animation-data-link-3',lambda x:member(x,3,'()Ljava/util/Map;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-animation-data-link-4',lambda x:member(x,4,'()Ljava/util/Map;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
