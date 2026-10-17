#!/usr/bin/env python3
"""SOUND-INSTANCE-LIFETIME fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', 'com/elfmcys/yesstevemodel/o0000oo0oOO00O00O0o0o0O0', 'com/elfmcys/yesstevemodel/OOO000o0OO0O0Oo0oo00ooOO']
SELECTED=set([('com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', '<init>', '(Lnet/minecraft/sounds/SoundEvent;Lnet/minecraft/world/entity/Entity;)V'), ('com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', 'm_7788_', '()V'), ('com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(F)V'), ('com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', 'o0OOooo0o0OO00OoOOOo0o0O', '(F)V'), ('com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', 'o0OOooo0o0OO00OoOOOo0o0O', '()V'), ('com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Z)V'), ('com/elfmcys/yesstevemodel/Oo0OoO0O00o00oOOooo00OOO', 'O00OOOooOoooOoo0o0o0oO0O', '()V'), ('com/elfmcys/yesstevemodel/o0000oo0oOO00O00O0o0o0O0', '<init>', '(Lnet/minecraft/sounds/SoundEvent;Lcom/elfmcys/yesstevemodel/O0o0O0ooO0OO00o0OOoO0ooo;Lnet/minecraft/world/entity/Entity;)V'), ('com/elfmcys/yesstevemodel/o0000oo0oOO00O00O0o0o0O0', 'getStream', '(Lnet/minecraft/client/sounds/SoundBufferLibrary;Lnet/minecraft/client/resources/sounds/Sound;Z)Ljava/util/concurrent/CompletableFuture;'), ('com/elfmcys/yesstevemodel/o0000oo0oOO00O00O0o0o0O0', 'm_7801_', '()Z'), ('com/elfmcys/yesstevemodel/o0000oo0oOO00O00O0o0o0O0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(ZLjava/util/concurrent/CompletableFuture;)V'), ('com/elfmcys/yesstevemodel/OOO000o0OO0O0Oo0oo00ooOO', '<init>', '(Lcom/elfmcys/yesstevemodel/O0o0O0ooO0OO00o0OOoO0ooo;)V'), ('com/elfmcys/yesstevemodel/OOO000o0OO0O0Oo0oo00ooOO', 'm_6206_', '()Ljavax/sound/sampled/AudioFormat;'), ('com/elfmcys/yesstevemodel/OOO000o0OO0O0Oo0oo00ooOO', 'm_7118_', '(I)Ljava/nio/ByteBuffer;'), ('com/elfmcys/yesstevemodel/OOO000o0OO0O0Oo0oo00ooOO', 'close', '()V'), ('com/elfmcys/yesstevemodel/OOO000o0OO0O0Oo0oo00ooOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/OOO000o0OO0O0Oo0oo00ooOO', 'o0OOooo0o0OO00OoOOOo0o0O', '()V'), ('com/elfmcys/yesstevemodel/OOO000o0OO0O0Oo0oo00ooOO', '<clinit>', '()V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/sound/instance/MinecraftSoundInstance.java', 'd6c4c6c4e6c0316fa2f9a07e5b0b10f776082ce8cc5f1673f458177ba79f5604', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/instance/CustomSoundInstance.java', 'fd62ab43277558ab4f1c9ced3257c2d33d6d786634c5720124821ea0295589f1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/stream/LoopingAudioStream.java', 'e9223a120cd72c68866885fedceac9c527e2ce86caae103ade503972051a88bb', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-19-methods',len(ids)==len(set(ids))==19 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-sound-lifetime-link-0',lambda x:member(x,0,'()V','m_7788_')['instructions'].pop())
    neg('missing-sound-lifetime-link-1',lambda x:member(x,1,'(Lnet/minecraft/client/sounds/SoundBufferLibrary;Lnet/minecraft/client/resources/sounds/Sound;Z)Ljava/util/concurrent/CompletableFuture;','getStream')['instructions'].pop())
    neg('missing-sound-lifetime-link-2',lambda x:member(x,2,'()Ljavax/sound/sampled/AudioFormat;','m_6206_')['instructions'].pop())
    neg('removed-loop-null-before-clear',lambda x:op(x,2,'(I)Ljava/nio/ByteBuffer;',27,'m_7118_').update(opcode='0x00'))
    neg('removed-future-exception-handler',lambda x:member(x,1,'(ZLjava/util/concurrent/CompletableFuture;)V','Oo0Oo0o00O00Oo0OOoOOoooo').update(exception_handlers=[]))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
