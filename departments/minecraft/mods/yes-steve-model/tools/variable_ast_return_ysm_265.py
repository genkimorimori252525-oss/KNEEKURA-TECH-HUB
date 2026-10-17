#!/usr/bin/env python3
"""Fixed-artifact selected motion query evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', 'com/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0', 'com/elfmcys/yesstevemodel/oOo0O0o0Oooo0o0oO0oOOO0o', 'com/elfmcys/yesstevemodel/o0o0OoOoO0Oo0oOoOOOooOOo', 'com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/molang/parser/ast/IdentifierExpression.java', '2aac7506e92c6cfd3309cf25d57bf3dd09a38ef3244afaee97560ed0dec2af94', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/parser/ast/VariableExpression.java', 'd02fca9664e416036ada51bb76c440b5e4f1a7e8b4da0a92d22e4436f136efbe', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/parser/ast/AssignableVariableExpression.java', 'f2b35fc9a7005e9f4a83dcebea30b330170e80162f1ab44e103147fa72314ecd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/value/MolangValue.java', '91ff48aeb783260a15d81c729d039c680eb9fc7013b51c2212b1b53401ac3acf', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/molang/runtime/ExpressionEvaluatorImpl.java', 'b1f5667dd9fc2e6b61d46fba8f66bc9ab51854e555fc192561ea552654febc2e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]
SELECTED=set([('com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', '<init>', '(Ljava/lang/String;Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Ljava/lang/Object;)Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;'), ('com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Oo0000oo0oo0OoO00000O0O0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', 'toString', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', 'equals', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo', 'hashCode', '()I'), ('com/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0', '<init>', '(Lcom/elfmcys/yesstevemodel/OoOoo0oOoOoo0OOoo0O0o0OO;)V'), ('com/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OoOoo0oOoOoo0OOoo0O0o0OO;'), ('com/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Oo0000oo0oo0OoO00000O0O0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0', 'toString', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0', 'equals', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0', 'hashCode', '()I'), ('com/elfmcys/yesstevemodel/oOo0O0o0Oooo0o0oO0oOOO0o', '<init>', '(Lcom/elfmcys/yesstevemodel/OO00oo0o0o0oo0OoO00OOoOo;)V'), ('com/elfmcys/yesstevemodel/oOo0O0o0Oooo0o0oO0oOOO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OO00oo0o0o0oo0OoO00OOoOo;'), ('com/elfmcys/yesstevemodel/oOo0O0o0Oooo0o0oO0oOOO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/Oo0000oo0oo0OoO00000O0O0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oOo0O0o0Oooo0o0oO0oOOO0o', 'toString', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oOo0O0o0Oooo0o0oO0oOOO0o', 'equals', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/oOo0O0o0Oooo0o0oO0oOOO0o', 'hashCode', '()I'), ('com/elfmcys/yesstevemodel/o0o0OoOoO0Oo0oOoOOOooOOo', '<init>', '(Ljava/util/List;Z)V'), ('com/elfmcys/yesstevemodel/o0o0OoOoO0Oo0oOoOOOooOOo', 'evalUnsafe', '(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Iterable;Z)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOo0O0o0Oooo0o0oO0oOOO0o;)Ljava/lang/Object;')])

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-28-selected-methods',len(ids)==len(set(ids))==28 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('five-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('five-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('five-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    multi='(Ljava/lang/Iterable;Z)Ljava/lang/Object;'
    single='(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;'
    neg('lost-single-finally',lambda x:member(x,4,single)['exception_handlers'].clear())
    neg('lost-multi-finally',lambda x:member(x,4,multi)['exception_handlers'].clear())
    neg('null-return-breaks-loop',lambda x:op(x,4,multi,66).update(opcode='0xc7'))
    neg('returnthrough-clearing-inverted',lambda x:op(x,4,'()Ljava/lang/Object;',9,'O00OOOooOoooOoo0o0o0oO0O').update(opcode='0x99'))
    neg('variable-evaluation-replaced',lambda x:op(x,4,'(Lcom/elfmcys/yesstevemodel/o000o0oO0Ooo00oO0Oo0ooO0;)Ljava/lang/Object;',5)['reference'].update(name='wrong'))
    neg('unknown-identifier-error-changed',lambda x:op(x,4,'(Lcom/elfmcys/yesstevemodel/o0OOOoOOO00O0oOOO0OOOOOo;)Ljava/lang/Object;',4)['reference'].update(string=''))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
