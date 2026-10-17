#!/usr/bin/env python3
"""LEXER-TOKEN-DIAGNOSTICS fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0', 'com/elfmcys/yesstevemodel/O0Ooo00O0oO0oOOOo0o00OO0', 'com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o', 'com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/O0O0oooO0O0OOO0OOo0OO00o', 'com/elfmcys/yesstevemodel/ooO0Ooo0OO0o000oo0o0o0OO', 'com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo']
SELECTED=set([('com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0', '<init>', '(Ljava/io/Reader;)V'), ('com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;'), ('com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo;'), ('com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo;'), ('com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0', 'close', '()V'), ('com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Lcom/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo;'), ('com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0', 'Ooooo0oooO0oooOOOoO0000O', '()I'), ('com/elfmcys/yesstevemodel/O0Ooo00O0oO0oOOOo0o00OO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0Ooo00O0oO0oOOOo0o00OO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/O0Ooo00O0oO0oOOOo0o00OO0', 'o0OOooo0o0OO00OoOOOo0o0O', '(I)Z'), ('com/elfmcys/yesstevemodel/O0Ooo00O0oO0oOOOo0o00OO0', 'O00OOOooOoooOoo0o0o0oO0O', '(I)Z'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', '<init>', '(II)V'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()I'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'o0OOooo0o0OO00OoOOOo0o0O', '()I'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'O00OOOooOoooOoo0o0o0oO0O', '()I'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)V'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'toString', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'equals', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'hashCode', '()I'), ('com/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo', 'clone', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o', 'values', '()[Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o;'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o', 'valueOf', '(Ljava/lang/String;)Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o;'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o', '<init>', '(Ljava/lang/String;I[Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo;)V'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o', '<init>', '(Ljava/lang/String;I)V'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo;)Z'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()[Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o;'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'values', '()[Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo;'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'valueOf', '(Ljava/lang/String;)Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo;'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '(Ljava/lang/String;I)V'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()[Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo;'), ('com/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/O0O0oooO0O0OOO0OOo0OO00o', '<init>', '(Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;)V'), ('com/elfmcys/yesstevemodel/O0O0oooO0O0OOO0OOo0OO00o', '<init>', '(Ljava/lang/String;Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;)V'), ('com/elfmcys/yesstevemodel/O0O0oooO0O0OOO0OOo0OO00o', '<init>', '(Ljava/lang/Throwable;Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;)V'), ('com/elfmcys/yesstevemodel/O0O0oooO0O0OOO0OOo0OO00o', '<init>', '(Ljava/lang/String;Ljava/lang/Throwable;Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;)V'), ('com/elfmcys/yesstevemodel/O0O0oooO0O0OOO0OOo0OO00o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;'), ('com/elfmcys/yesstevemodel/O0O0oooO0O0OOO0OOo0OO00o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/ooO0Ooo0OO0o000oo0o0o0OO', '<init>', '(Lcom/elfmcys/yesstevemodel/OooOoO0O0O0o00Oo000o00Oo;)V'), ('com/elfmcys/yesstevemodel/ooO0Ooo0OO0o000oo0o0o0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/io/Reader;)Ljava/util/List;'), ('com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo', '<init>', '(Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o;Ljava/lang/String;II)V'), ('com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o;'), ('com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo', 'O00OOOooOoooOoo0o0o0oO0O', '()I'), ('com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo', 'oOOOo0OOO0ooooo0O00OO0o0', '()I'), ('com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo', 'toString', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo', 'equals', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/o00oOO0oooO0ooo00oOo00Oo', 'hashCode', '()I')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/molang/lexer/MolangLexerImpl.java', 'f754cc2b1ede58e929c9430aa3df85a290441889c0c6276756c452ebedfe0179', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/lexer/Characters.java', '5067075a041219d4b2af37cac42ad5c1da8ad31b3fd45f0aceeaaed9ae6bf904', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/lexer/Cursor.java', '3db7038d64caa5de0284a1ef4c91a2a27612e207d7a3ea7adf5dbd0b89605334', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/lexer/TokenKind.java', '10f0f50bb2573c2f94804ebbe4449929ef3e5f8ed66b04cf490546c8aec959f8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/lexer/TokenKind.java', '10f0f50bb2573c2f94804ebbe4449929ef3e5f8ed66b04cf490546c8aec959f8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/parser/ParseException.java', '1db978405ac5d4f8692a3dbc7cce9339fc69affaf786dedf3cfbc87dd80447bf', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/MolangEngineImpl.java', 'ced99998dd565645ff9d770564d08fe6a59a4813fcb06be6e750de68cc91b0b2', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/lexer/Token.java', '915ba269e65d1dd75936e45e331ada0fec1da81cd131ebc3fbd61ca2fbe28d0e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-50-methods',len(ids)==len(set(ids))==50 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==8 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==8 and {r['owner'] for r in bs}==set(OWNERS))
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'()Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'(I)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'()I','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-3',lambda x:member(x,3,'()[Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o;','values')['instructions'].pop())
    neg('missing-model-asset-helper-4',lambda x:member(x,4,'()[Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o$Oo0Oo0o00O00Oo0OOoOOoooo;','values')['instructions'].pop())
    neg('missing-model-asset-helper-5',lambda x:member(x,5,'()Lcom/elfmcys/yesstevemodel/Oo0O00o0O0000OO0O0o0O0Oo;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-6',lambda x:member(x,6,'(Ljava/io/Reader;)Ljava/util/List;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-7',lambda x:member(x,7,'()Lcom/elfmcys/yesstevemodel/OOo0OOOooo0oO0oO00O00o0o;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
