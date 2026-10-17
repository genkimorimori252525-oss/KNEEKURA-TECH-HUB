#!/usr/bin/env python3
"""CLIENT-MODEL-SYNC-STATE fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O', 'com/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo']
SELECTED=set([('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()Lnet/minecraft/resources/ResourceLocation;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo;)Lcom/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Ooooo0oooO0oooOOOoO0000O', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/nio/ByteBuffer;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'oo0OoO00oOoo000O0000o0oo', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'oooooooOOoOOoO00OooOo00O', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'O0OooOo0oOOoOoOoOooO000o', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo00o0OooOOo0ooOoo0oO0o0', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'o0OOO0o0o0OOo000oO00o00O', '()I'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lit/unimi/dsi/fastutil/objects/Object2ReferenceOpenHashMap;Lcom/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'ooOO000o0O0OOOoO0Oo0o0Oo', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'OOOo0OOOoOO0O00Oo00ooOOO', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(ILcom/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'o0OOooo0o0OO00OoOOOo0o0O', '(I)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'o0OOooo0o0OO00OoOOOo0o0O', '(ILcom/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'oOo0o0000OOOO0OooooO00oo', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'O0ooooOO0oOo000O0Oo00OOO', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo', 'o0OOooo0o0OO00OoOOOo0o0O', '()I'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo', 'O00OOOooOoooOoo0o0o0oO0O', '()I'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O', 'values', '()[Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O', 'valueOf', '(Ljava/lang/String;)Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O', '<init>', '(Ljava/lang/String;I)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()[Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O;'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo', 'O00OOOooOoooOoo0o0o0oO0O', '()V'), ('com/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo', 'oOOOo0OOO0ooooo0O00OO0o0', '()V'), ('com/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/Map;)V'), ('com/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(II)V'), ('com/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/util/Map;)V'), ('com/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo', 'OOOOo0O0oO0OOo0O0O0Oo0O0', '()V'), ('com/elfmcys/yesstevemodel/O0000ooOo00o0OoO0OoOOOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/chat/Component;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/ClientModelManager.java', 'd62ea0045faf280e7f0e0cacc3ca87ecbac076ab0527ddecf6bc6aae4f85debe', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/ClientModelManager.java', 'd62ea0045faf280e7f0e0cacc3ca87ecbac076ab0527ddecf6bc6aae4f85debe', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/ClientModelManager.java', 'd62ea0045faf280e7f0e0cacc3ca87ecbac076ab0527ddecf6bc6aae4f85debe', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/model/ClientModelSyncListener.java', '243a3f359a1ce6b0f33bcabb9c9d78b570070f8c7845fd2b3cf13e27502002de', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-48-methods',len(ids)==len(set(ids))==48 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('four-declarations',len(ds)==4 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('four-bootstrap-records',len(bs)==4 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('four-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-client-model-state-link-0',lambda x:member(x,0,'()Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$Oo0Oo0o00O00Oo0OOoOOoooo;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-client-model-state-link-1',lambda x:member(x,1,'()Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-client-model-state-link-2',lambda x:member(x,2,'()[Lcom/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO$o0OOooo0o0OO00OoOOOo0o0O;','values')['instructions'].pop())
    neg('missing-client-model-state-link-3',lambda x:member(x,3,'()V','O00OOOooOoooOoo0o0o0oO0O')['instructions'].pop())
    neg('changed-completion-equality',lambda x:op(x,0,'()V',33,'OOOo0OOOoOO0O00Oo00ooOOO').update(opcode='0xa2'))
    neg('invented-native-Code',lambda x:member(x,0,'(Ljava/nio/ByteBuffer;)V','o0OOooo0o0OO00OoOOOo0o0O').update(instructions=[]))
    neg('removed-listener-handler',lambda x:member(x,0,'(Ljava/util/function/Consumer;)V','Oo0Oo0o00O00Oo0OOoOOoooo').update(exception_handlers=[]))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
