#!/usr/bin/env python3
"""UTILITY-NOISE-DEBUG fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/Ooo000O0OO0O0OOO0oO0OOOo', 'com/elfmcys/yesstevemodel/OoO0o00oooo00oO000oO0ooo', 'com/elfmcys/yesstevemodel/oOOOO00ooooO0O0ooO000o00', 'com/elfmcys/yesstevemodel/Oo0ooOo0OOOO00o0OOO0o0OO', 'com/elfmcys/yesstevemodel/o0OoOoOO000OOo0OOOO0oOoO', 'com/elfmcys/yesstevemodel/Oo0OoooO00o00OooO0Oo000o', 'com/elfmcys/yesstevemodel/Oo0o0O0000OooOoooO0OO0o0']
SELECTED=set([('com/elfmcys/yesstevemodel/Ooo000O0OO0O0OOO0oO0OOOo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/Ooo000O0OO0O0OOO0oO0OOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/Ooo000O0OO0O0OOO0oO0OOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OoO0o00oooo00oO000oO0ooo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OoO0o00oooo00oO000oO0ooo', 'evaluate', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OoO0o00oooo00oO000oO0ooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/OoO0o00oooo00oO000oO0ooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/fml/ModContainer;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oOOOO00ooooO0O0ooO000o00', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOOOO00ooooO0O0ooO000o00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/oOOOO00ooooO0O0ooO000o00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/Oo0ooOo0OOOO00o0OOO0o0OO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/Oo0ooOo0OOOO00o0OOO0o0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/Oo0ooOo0OOOO00o0OOO0o0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/o0OoOoOO000OOo0OOOO0oOoO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0OoOoOO000OOo0OOOO0oOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0OoOoOO000OOo0OOOO0oOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/o0OoOoOO000OOo0OOOO0oOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lnet/minecraft/tags/TagKey;)V'), ('com/elfmcys/yesstevemodel/Oo0OoooO00o00OooO0Oo000o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/Oo0OoooO00o00OooO0Oo000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/Oo0OoooO00o00OooO0Oo000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z'), ('com/elfmcys/yesstevemodel/Oo0OoooO00o00OooO0Oo000o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lnet/minecraft/tags/TagKey;)V'), ('com/elfmcys/yesstevemodel/Oo0o0O0000OooOoooO0OO0o0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/Oo0o0O0000OooOoooO0OO0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/Oo0o0O0000OooOoooO0OO0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Z')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/PerlinNoiseFunction.java', '16cb600c9f5aafbd76e2434e0271d0af4be78255f970ff34b677a00583d43f6a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/ModVersion.java', '3092213bf46ce6707df4074f5d13624e8b9f64d60452f4f46764bf082916c1c0', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/RelativeBlockName.java', '309361014aeff09e8f68153f2b2efa6a8cafa1acc512de7f825f961051b12b98', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/RelativeBlockNameAny.java', '759d88d77118929dead15251defb70350ac9e1fad5d09e66b920d8719ba66070', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/DumpRelativeBlock.java', 'f43e9605ea9051e24bf6d54c3d1b84be39098e9fc79ef09bad7b097910595dd4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/functions/DumpEquippedItem.java', 'e53bd037985686e59361eed29491a76ebbabd378efab3a163f3681804955e0f1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/builtin/query/DebugOutput.java', '2b2d1cc114d91e4a4fb760aef9b115f6fb0eeb40e22216b821f1a6cc9a64fdab', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-24-methods',len(ids)==len(set(ids))==24 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('seven-declarations',len(ds)==7 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('seven-bootstrap-records',len(bs)==7 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('seven-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-utility-link-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-utility-link-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','evaluate')['instructions'].pop())
    neg('missing-utility-link-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-utility-link-3',lambda x:member(x,3,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-utility-link-4',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-utility-link-5',lambda x:member(x,5,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-utility-link-6',lambda x:member(x,6,'(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
