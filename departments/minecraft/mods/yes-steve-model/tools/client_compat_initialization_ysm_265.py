#!/usr/bin/env python3
"""CLIENT-COMPAT-INITIALIZATION fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', 'com/elfmcys/yesstevemodel/oO0OOOoO0oooO0OOo0ooOoOo']
SELECTED=set([('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/fml/event/lifecycle/FMLClientSetupEvent;)V'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/Optional;)V'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/client/event/RegisterKeyMappingsEvent;)V'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/client/event/RegisterGuiOverlaysEvent;)V'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'o0OOooo0o0OO00OoOOOo0o0O', '()V'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lorg/apache/commons/lang3/tuple/Pair;)V'), ('com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo', 'O00OOOooOoooOoo0o0o0oO0O', '()V'), ('com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo;'), ('com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo;)V'), ('com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;'), ('com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo;'), ('com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;)Z'), ('com/elfmcys/yesstevemodel/O00o0ooOoo00o00o0OOOO0o0', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/oO0OOOoO0oooO0OOo0ooOoOo', '<init>', '(Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/oO0OOOoO0oooO0OOo0ooOoOo', 'initialize', '()Ljava/lang/Object;')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/event/ClientSetupEvent.java', '1ac075fbe173567f74e576530166215c1ce43a6e879fe7edf10d6bae81122588', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/CustomMolangParser.java', '02250e2f1d5e92f3cd26038e264717275006a4fdecbbd0d269e5fed898bfd7d5', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/util/LazyValue.java', 'a795e6c114c7ea84ca5eb08c507190840280c33e8e56eea65fae8819f71dd542', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-20-methods',len(ids)==len(set(ids))==20 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-client-setup-annotations',e.get('client_setup_annotations')==details.get('_client_setup_annotations'))
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
    with zipfile.ZipFile(a.jar) as z:details['_client_setup_annotations']=annotations(z.read(OWNERS[0]+'.class'))
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
    neg('missing-client-init-link-0',lambda x:member(x,0,'(Lnet/minecraftforge/fml/event/lifecycle/FMLClientSetupEvent;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-client-init-link-1',lambda x:member(x,1,'()Lcom/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-client-init-link-2',lambda x:member(x,2,'()Ljava/lang/Object;','initialize')['instructions'].pop())
    neg('missing-client-annotation',lambda x:x['client_setup_annotations'].pop('annotations'))
    neg('invented-native-code',lambda x:member(x,0,'()Ljava/lang/Object;').update(instructions=[{'offset':0,'opcode':'0xb0'}]))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
