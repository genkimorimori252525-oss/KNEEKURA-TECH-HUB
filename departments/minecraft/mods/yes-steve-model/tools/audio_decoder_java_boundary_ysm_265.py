#!/usr/bin/env python3
"""AUDIO-DECODER-JAVA-BOUNDARY fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o0OO00ooo0OooO0O00o0oOoo', 'com/elfmcys/yesstevemodel/OOoo000Oo0ooooOoO0OOOoo0', 'com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO', 'com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0']
SELECTED=set([('com/elfmcys/yesstevemodel/o0OO00ooo0OooO0O00o0oOoo', '<init>', '(Ljava/nio/ByteBuffer;Lcom/elfmcys/yesstevemodel/oOO0oOO0o0O0o0000oO0o0o0;)V'), ('com/elfmcys/yesstevemodel/o0OO00ooo0OooO0O00o0oOoo', 'm_6206_', '()Ljavax/sound/sampled/AudioFormat;'), ('com/elfmcys/yesstevemodel/o0OO00ooo0OooO0O00o0oOoo', 'm_7118_', '(I)Ljava/nio/ByteBuffer;'), ('com/elfmcys/yesstevemodel/o0OO00ooo0OooO0O00o0oOoo', 'close', '()V'), ('com/elfmcys/yesstevemodel/o0OO00ooo0OooO0O00o0oOoo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/o0OO00ooo0OooO0O00o0oOoo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OOoo000Oo0ooooOoO0OOOoo0', '<init>', '(Ljava/nio/ByteBuffer;Lcom/elfmcys/yesstevemodel/oOO0oOO0o0O0o0000oO0o0o0;)V'), ('com/elfmcys/yesstevemodel/OOoo000Oo0ooooOoO0OOOoo0', 'm_7118_', '(I)Ljava/nio/ByteBuffer;'), ('com/elfmcys/yesstevemodel/OOoo000Oo0ooooOoO0OOOoo0', 'm_6206_', '()Ljavax/sound/sampled/AudioFormat;'), ('com/elfmcys/yesstevemodel/OOoo000Oo0ooooOoO0OOOoo0', 'close', '()V'), ('com/elfmcys/yesstevemodel/OOoo000Oo0ooooOoO0OOOoo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/OOoo000Oo0ooooOoO0OOOoo0', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0;'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0;)V'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO', 'o0OOooo0o0OO00OoOOOo0o0O', '()V'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '(Ljava/lang/Object;I)V'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO$Oo0Oo0o00O00Oo0OOoOOoooo', 'toString', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO$Oo0Oo0o00O00Oo0OOoOOoooo', 'hashCode', '()I'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO$Oo0Oo0o00O00Oo0OOoOOoooo', 'equals', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/Object;'), ('com/elfmcys/yesstevemodel/o0ooOoO0o0o0O0oooOOoOOOO$Oo0Oo0o00O00Oo0OOoOOoooo', 'o0OOooo0o0OO00OoOOOo0o0O', '()I'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/nio/ByteBuffer;)V'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/nio/ByteBuffer;)I'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'o0OOooo0o0OO00OoOOOo0o0O', '()V'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'O00OOOooOoooOoo0o0o0oO0O', '()J'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(JLjava/nio/ByteBuffer;)Z'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'o0OOooo0o0OO00OoOOOo0o0O', '(JLjava/nio/ByteBuffer;)I'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(J)V'), ('com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0', 'o0OOooo0o0OO00OoOOOo0o0O', '(J)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/sound/stream/VorbisAudioStream.java', '10654e2a022b2571b4a9c0ede8a88c58a45f6d8d8dec9ed8ef8e29a2b36bdfe6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/stream/OpusAudioStream.java', '93ec9f833f98ea475358f01b26cd0a859e907c48d5c556793bf69bad99b1a5a1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/decoder/DecoderManager.java', 'db2bb8801a3d33879f9d04fffe868cb88bc34260df8a7aae8f2c460f9a14091d', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/decoder/DecoderManager.java', 'db2bb8801a3d33879f9d04fffe868cb88bc34260df8a7aae8f2c460f9a14091d', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/decoder/OpusDecoder.java', '09da05003ca07cc1883816468d9611f7c119e0c57a150744446b49adc4ce39fe', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-33-methods',len(ids)==len(set(ids))==33 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('five-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('five-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('five-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-audio-adapter-link-0',lambda x:member(x,0,'()Ljavax/sound/sampled/AudioFormat;','m_6206_')['instructions'].pop())
    neg('missing-audio-adapter-link-1',lambda x:member(x,1,'(I)Ljava/nio/ByteBuffer;','m_7118_')['instructions'].pop())
    neg('missing-audio-adapter-link-2',lambda x:member(x,2,'()Lcom/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-audio-adapter-link-3',lambda x:member(x,3,'()Ljava/lang/String;','toString')['instructions'].pop())
    neg('missing-audio-adapter-link-4',lambda x:member(x,4,'(Ljava/nio/ByteBuffer;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
