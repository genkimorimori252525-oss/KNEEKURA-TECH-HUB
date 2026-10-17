#!/usr/bin/env python3
"""OPAQUE-MODEL-DATA-TRANSPORT fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O', 'com/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O', 'com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO']
SELECTED=set([('com/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O', '<init>', '(Ljava/nio/ByteBuffer;)V'), ('com/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O;'), ('com/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O', '<init>', '(Ljava/nio/ByteBuffer;)V'), ('com/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O;'), ('com/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/nio/ByteBuffer;)V'), ('com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/Connection;Ljava/nio/ByteBuffer;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/network/message/SyncDataToClient.java', '0cd5a29b43bdb260fd7f5e6ed1964361e3ca971abef35cf10a67fe3e75e91751', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/SyncDataToServer.java', '3ab2618f800df88a10c81998930232449c6ccd43a107754623e0007a5963119d', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/ClientModelManager.java', 'd62ea0045faf280e7f0e0cacc3ca87ecbac076ab0527ddecf6bc6aae4f85debe', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-10-methods',len(ids)==len(set(ids))==10 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
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
    neg('changed-render-entry-owner-0',lambda x:member(x,0,'(Ljava/nio/ByteBuffer;)V','<init>')['instructions'].pop())
    neg('changed-render-entry-owner-1',lambda x:member(x,1,'(Ljava/nio/ByteBuffer;)V','<init>')['instructions'].pop())
    neg('changed-render-entry-owner-2',lambda x:member(x,2,'(Ljava/nio/ByteBuffer;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('changed-client-reception-guard',lambda x:op(x,0,'(Lcom/elfmcys/yesstevemodel/O0oo00oo00OoOooO000oO00O;Ljava/util/function/Supplier;)V',20).update(opcode='0x9a'))
    neg('changed-direct-allocation',lambda x:op(x,1,'(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/oo00oOo0OOO0OoOOo0O0oO0O;',4)['reference'].update(name='allocate'))
    neg('changed-connection-write',lambda x:op(x,2,'(Lnet/minecraft/network/Connection;Ljava/nio/ByteBuffer;)V',1)['reference'].update(name='missing'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
