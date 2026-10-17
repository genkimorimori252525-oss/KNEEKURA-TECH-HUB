#!/usr/bin/env python3
"""PARSER-ENTRY-OWNERSHIP fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o00oO0OOoOOooOoOOoO0Oooo', 'com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO']
SELECTED=set([('com/elfmcys/yesstevemodel/o00oO0OOoOOooOoOOoO0Oooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/io/Reader;)Ljava/util/List;'), ('com/elfmcys/yesstevemodel/o00oO0OOoOOooOoOOoO0Oooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Ljava/util/List;'), ('com/elfmcys/yesstevemodel/o00oO0OOoOOooOoOOoO0Oooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OooOoO0O0O0o00Oo000o00Oo;)Lcom/elfmcys/yesstevemodel/o00oO0OOoOOooOoOOoO0Oooo;'), ('com/elfmcys/yesstevemodel/o00oO0OOoOOooOoOOoO0Oooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/o00oO0OOoOOooOoOOoO0Oooo;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OoO00O0O0ooo0oO0O00Oo00o;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'close', '()V'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OoO00O0O0ooo0oO0O00Oo00o;Lcom/elfmcys/yesstevemodel/OooOoO0O0O0o00Oo000o00Oo;)Lcom/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/io/Reader;Lcom/elfmcys/yesstevemodel/OooOoO0O0O0o00Oo000o00Oo;)Lcom/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Lcom/elfmcys/yesstevemodel/OooOoO0O0O0o00Oo000o00Oo;)Lcom/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/io/Reader;Lcom/elfmcys/yesstevemodel/OooOoO0O0O0o00Oo000o00Oo;)Ljava/util/List;'), ('com/elfmcys/yesstevemodel/oOOOOO00OO00oOO0ooO0OooO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;Lcom/elfmcys/yesstevemodel/OooOoO0O0O0o00Oo000o00Oo;)Ljava/util/List;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/molang/MolangEngine.java', '4c632e21880c126cfe0464e733d8f653919730c85b42672f22c96fa5222d0d80', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/parser/MolangParser.java', '4d08ab5f844c7a0b57de54981b5304bfd77a8ff1a77ffa3717539f8d1888f5eb', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-15-methods',len(ids)==len(set(ids))==15 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==2 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==2 and {r['owner'] for r in bs}==set(OWNERS))
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'(Ljava/lang/String;)Ljava/util/List;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'()Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;','o0OOooo0o0OO00OoOOOo0o0O')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
