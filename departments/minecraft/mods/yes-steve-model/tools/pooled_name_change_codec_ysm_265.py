#!/usr/bin/env python3
"""Fixed-artifact selected motion query evidence audit. Never runs target classes."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOO0OO0oO0oooo00OooooO0O', 'com/elfmcys/yesstevemodel/OoOO0oOo00o0oOO00OooOO00', 'com/elfmcys/yesstevemodel/oO0O0OO0oo0o0Oo0OO0o0O0O', 'com/elfmcys/yesstevemodel/o0Oo0O0oo000ooo0o0Oooo0o', 'com/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0', 'com/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/util/StringPool.java', '49d6d71d5279fe98ba6622384d78cc3a22c35474d8d7fb5eedf470f8d931b363', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/util/PooledStringHashMap.java', '41161815ecfba6e15f45dce803bcab66f4d05778a89b2d68d3f002a0b3790bd9', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/util/PooledStringHashSet.java', '06c11ecbf0ff2daf23afd60ad3209846d0b22fbd5fc24673eecc9d26aa1e65b6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/animation/molang/roaming/VariableChanges.java', 'cfd23a6af014e0420f1e8c66b31342936a789fcf3f32773d6c8d62134d94892c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/data/RoamingVarsChanges.java', 'bac68f7a32b1641f7e2eb38de6e78fff9ef5f0c8e23a6b1dc14d2a24e7181984', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/PlayerAnimatableCapability.java', '3296261fbf5d1f060ec5904da0a7c5d932e1f316694db78d8db370cfffcef78b', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]
SELECTED=set([('com/elfmcys/yesstevemodel/oOO0OO0oO0oooo00OooooO0O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOO0OO0oO0oooo00OooooO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)I'), ('com/elfmcys/yesstevemodel/oOO0OO0oO0oooo00OooooO0O', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;)I'), ('com/elfmcys/yesstevemodel/oOO0OO0oO0oooo00OooooO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/util/Set;'), ('com/elfmcys/yesstevemodel/oOO0OO0oO0oooo00OooooO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/oOO0OO0oO0oooo00OooooO0O', 'O00OOOooOoooOoo0o0o0oO0O', '(Ljava/lang/String;)Ljava/lang/Integer;'), ('com/elfmcys/yesstevemodel/oOO0OO0oO0oooo00OooooO0O', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OoOO0oOo00o0oOO00OooOO00', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OoOO0oOo00o0oOO00OooOO00', '<init>', '(I)V'), ('com/elfmcys/yesstevemodel/OoOO0oOo00o0oOO00OooOO00', '<init>', '(Lit/unimi/dsi/fastutil/ints/Int2ReferenceOpenHashMap;)V'), ('com/elfmcys/yesstevemodel/OoOO0oOo00o0oOO00OooOO00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OoOO0oOo00o0oOO00OooOO00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/oO0O0OO0oo0o0Oo0OO0o0O0O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oO0O0OO0oo0o0Oo0OO0o0O0O', '<init>', '(I)V'), ('com/elfmcys/yesstevemodel/oO0O0OO0oo0o0Oo0OO0o0O0O', '<init>', '(Ljava/util/Collection;)V'), ('com/elfmcys/yesstevemodel/oO0O0OO0oo0o0Oo0OO0o0O0O', '<init>', '(Lit/unimi/dsi/fastutil/ints/IntOpenHashSet;)V'), ('com/elfmcys/yesstevemodel/oO0O0OO0oo0o0Oo0OO0o0O0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Z'), ('com/elfmcys/yesstevemodel/oO0O0OO0oo0o0Oo0OO0o0O0O', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;)Z'), ('com/elfmcys/yesstevemodel/o0Oo0O0oo000ooo0o0Oooo0o', '<init>', '(II)V'), ('com/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0', '<init>', '(ILit/unimi/dsi/fastutil/objects/Object2FloatArrayMap;Lit/unimi/dsi/fastutil/ints/Int2FloatArrayMap;I)V'), ('com/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;Z)Lcom/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0;'), ('com/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;Lit/unimi/dsi/fastutil/objects/Object2FloatMap$Entry;)V'), ('com/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()V')])

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-24-selected-methods',len(ids)==len(set(ids))==24 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('six-declarations',len(ds)==6 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('six-bootstrap-records',len(bs)==6 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('six-fixed-sources',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-outgoing-change-tail',lambda x:member(x,5,'()V')['instructions'].pop())
    neg('invented-outgoing-change-finally',lambda x:member(x,5,'()V')['exception_handlers'].append({'start':0,'end':300,'handler':300,'catch':None}))
    def call(x,owner,name):return next(o for m in x['members'] if m['owner']==OWNERS[owner] for o in m.get('instructions',[]) if o.get('reference',{}).get('name')==name)
    neg('codec-count-kind',lambda x:call(x,4,'readByte')['reference'].update(name='readInt'))
    neg('codec-name-read-kind',lambda x:call(x,4,'m_130277_')['reference'].update(name='readVarInt'))
    neg('codec-value-kind',lambda x:call(x,4,'writeFloat')['reference'].update(name='writeDouble'))
    neg('outgoing-name-length',lambda x:next(o for m in x['members'] if m['owner']==OWNERS[5] for o in m['instructions'] if o.get('immediate')==32).update(immediate=64))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
