#!/usr/bin/env python3
"""SERVER-MODEL-SYNC-JAVA fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$1', 'com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$Oo0Oo0o00O00Oo0OOoOOoooo']
SELECTED=set([('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/util/Map;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljava/util/Set;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Ljava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Ljava/lang/String;Ljava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/function/Consumer;Ljava/util/function/Consumer;)Z'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/Collection;)[Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '([Ljava/util/UUID;[Ljava/lang/String;[Ljava/lang/String;Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/UUID;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/UUID;Ljava/nio/ByteBuffer;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/util/UUID;)Lnet/minecraft/network/Connection;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/UUID;Ljava/nio/ByteBuffer;Lcom/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$Oo0Oo0o00O00Oo0OOoOOoooo;)Z'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/nio/ByteBuffer;)Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/UUID;Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$Oo0Oo0o00O00Oo0OOoOOoooo;)Z'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/Connection;Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$Oo0Oo0o00O00Oo0OOoOOoooo;)Z'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'O00OOOooOoooOoo0o0o0oO0O', '()Lorg/apache/commons/lang3/tuple/Pair;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOoOO0OO0o0Oooo00OOOOoO0;Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Lcom/elfmcys/yesstevemodel/oOOOo0OOO0ooooo0O00OO0o0;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;)Z'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;Ljava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/function/Consumer;Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)[Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/server/level/ServerPlayer;)Ljava/util/Optional;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/util/function/Consumer;Ljava/util/function/Consumer;Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/MinecraftServer;Ljava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'o0OOooo0o0OO00OoOOOo0o0O', '(I)[Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'O00OOOooOoooOoo0o0o0oO0O', '(Lnet/minecraft/server/level/ServerPlayer;)Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'O00OOOooOoooOoo0o0o0oO0O', '(I)[Ljava/util/UUID;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/MinecraftServer;Lnet/minecraft/server/level/ServerPlayer;Ljava/util/function/Consumer;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lit/unimi/dsi/fastutil/floats/FloatReferencePair;Lit/unimi/dsi/fastutil/floats/FloatReferencePair;)I'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$1', '<init>', '(Ljava/util/concurrent/atomic/AtomicInteger;)V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$1', 'm_243096_', '()V'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$1', 'm_243103_', '()Lnet/minecraft/network/protocol/Packet;'), ('com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '()V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/model/ServerModelManager.java', '8c226a2cd9dd4351392736932226493b839b64ec3c33d1aa813f4f489f2b78e6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/model/ServerModelManager.java', '8c226a2cd9dd4351392736932226493b839b64ec3c33d1aa813f4f489f2b78e6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/model/ServerModelManager.java', '8c226a2cd9dd4351392736932226493b839b64ec3c33d1aa813f4f489f2b78e6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-40-methods',len(ids)==len(set(ids))==40 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('fixed-owner-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('fixed-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('changed-server_model_sync_java-owner-0',lambda x:member(x,0,'()V','<init>')['instructions'].pop())
    neg('changed-server_model_sync_java-owner-1',lambda x:member(x,1,'(Ljava/util/concurrent/atomic/AtomicInteger;)V','<init>')['instructions'].pop())
    neg('changed-server_model_sync_java-owner-2',lambda x:member(x,2,'()V','<init>')['instructions'].pop())
    neg('invented-native-code',lambda x:member(x,0,'(Ljava/lang/Object;)Z').update(instructions=[]))
    neg('wrong-high-water-source',lambda x:op(x,0,'(Lnet/minecraft/network/Connection;Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$Oo0Oo0o00O00Oo0OOoOOoooo;)Z',27)['reference'].update(name='size'))
    neg('wrong-count-comparison-source',lambda x:op(x,0,'(Lnet/minecraft/network/Connection;Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$Oo0Oo0o00O00Oo0OOoOOoooo;)Z',67)['reference'].update(name='totalPendingWriteBytes'))
    neg('wrong-pending-wait-guard',lambda x:op(x,0,'(Lnet/minecraft/network/Connection;Ljava/lang/Object;Lcom/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00$Oo0Oo0o00O00Oo0OOoOOoooo;)Z',121).update(opcode='0x99'))
    neg('wrong-success-status',lambda x:op(x,1,'()V',4,'m_243096_').update(opcode='0x2'))
    neg('invented-reload-finally',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;Ljava/lang/Object;)V')['exception_handlers'].append({'handler':0}))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
