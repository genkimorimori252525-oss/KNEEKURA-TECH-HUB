#!/usr/bin/env python3
"""SOUND-DATA-PCM-CACHE fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo', 'com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00', 'com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo$Oo0Oo0o00O00Oo0OOoOOoooo', 'com/elfmcys/yesstevemodel/oOO0oOO0o0O0o0000oO0o0o0', 'com/elfmcys/yesstevemodel/O0oo00O0OOOo000oOo0ooOOo', 'com/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO', 'com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$1']
SELECTED=set([('com/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo', '<init>', '(Ljava/nio/ByteBuffer;IIJ)V'), ('com/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()J'), ('com/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo', 'o0OOooo0o0OO00OoOOOo0o0O', '()I'), ('com/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo', 'O00OOOooOoooOoo0o0o0oO0O', '()Lcom/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO;'), ('com/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo', 'oOOOo0OOO0ooooo0O00OO0o0', '()Ljava/nio/ByteBuffer;'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;)Lcom/elfmcys/yesstevemodel/o0O0o0OO0o0oOooOoO000O00;'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;)V'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;)V'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo;Ljava/nio/ByteBuffer;Lit/unimi/dsi/fastutil/ints/IntArrayList;)V'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo;)Lcom/elfmcys/yesstevemodel/oooOoOoOoOoOO0Oo0OOo00oo;'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo$Oo0Oo0o00O00Oo0OOoOOoooo', '<init>', '(Ljava/nio/ByteBuffer;Ljavax/sound/sampled/AudioFormat;Lit/unimi/dsi/fastutil/ints/IntArrayList;)V'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo$Oo0Oo0o00O00Oo0OOoOOoooo', 'toString', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo$Oo0Oo0o00O00Oo0OOoOOoooo', 'hashCode', '()I'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo$Oo0Oo0o00O00Oo0OOoOOoooo', 'equals', '(Ljava/lang/Object;)Z'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo$Oo0Oo0o00O00Oo0OOoOOoooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/nio/ByteBuffer;'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo$Oo0Oo0o00O00Oo0OOoOOoooo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Ljavax/sound/sampled/AudioFormat;'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo$Oo0Oo0o00O00Oo0OOoOOoooo', 'O00OOOooOoooOoo0o0o0oO0O', '()Lit/unimi/dsi/fastutil/ints/IntArrayList;'), ('com/elfmcys/yesstevemodel/oOO0oOO0o0O0o0000oO0o0o0', '<init>', '(Lcom/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$Oo0Oo0o00O00Oo0OOoOOoooo;Lcom/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo;)V'), ('com/elfmcys/yesstevemodel/oOO0oOO0o0O0o0000oO0o0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/nio/ByteBuffer;)V'), ('com/elfmcys/yesstevemodel/oOO0oOO0o0O0o0000oO0o0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/O0oo00O0OOOo000oOo0ooOOo', '<init>', '(Ljava/nio/ByteBuffer;Lit/unimi/dsi/fastutil/ints/IntArrayList;Ljavax/sound/sampled/AudioFormat;)V'), ('com/elfmcys/yesstevemodel/O0oo00O0OOOo000oOo0ooOOo', 'm_6206_', '()Ljavax/sound/sampled/AudioFormat;'), ('com/elfmcys/yesstevemodel/O0oo00O0OOOo000oOo0ooOOo', 'm_7118_', '(I)Ljava/nio/ByteBuffer;'), ('com/elfmcys/yesstevemodel/O0oo00O0OOOo000oOo0ooOOo', 'close', '()V'), ('com/elfmcys/yesstevemodel/O0oo00O0OOOo000oOo0ooOOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/O0oo00O0OOOo000oOo0ooOOo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO', 'values', '()[Lcom/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO;'), ('com/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO', 'valueOf', '(Ljava/lang/String;)Lcom/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO;'), ('com/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO', '<init>', '(Ljava/lang/String;I)V'), ('com/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()[Lcom/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO;'), ('com/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/o0OOOoOoO0oO000Oo0OOoO00$1', '<clinit>', '()V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/sound/data/SoundData.java', '49ff3fc0a5324d09980daa58053db7fbc6a1021755d84079de0a572a18feb79d', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/data/SoundDataManager.java', '970da1fc38057f840f9a2e86a15ce838bbff6330775eb9ddebad5603f037a1bd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/data/SoundDataManager.java', '970da1fc38057f840f9a2e86a15ce838bbff6330775eb9ddebad5603f037a1bd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/data/SoundDataManager.java', '970da1fc38057f840f9a2e86a15ce838bbff6330775eb9ddebad5603f037a1bd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/data/BuildingPcmCache.java', '774bcb675f88f66806a44fb9148076839939e7362d4a846602fd6106ecb3d390', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/stream/PcmAudioStream.java', 'c40b9861274d6e1dcd139d502a5c5d19f2795ccfc1a63a12a323fe54a915a8fa', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/data/SoundFormat.java', '25285b326eb186446e1fcc7154dca0e4fcba36ba5b0f341bea56e53c70280cd8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/sound/data/SoundDataManager.java', '970da1fc38057f840f9a2e86a15ce838bbff6330775eb9ddebad5603f037a1bd', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-35-methods',len(ids)==len(set(ids))==35 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('eight-declarations',len(ds)==8 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('eight-bootstrap-records',len(bs)==8 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('eight-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
    neg('missing-sound-cache-link-0',lambda x:member(x,0,'()J','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-sound-cache-link-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;)Lcom/elfmcys/yesstevemodel/o0O0o0OO0o0oOooOoO000O00;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-sound-cache-link-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/ooOooOoo00oo0ooOOoOOo0oo;Ljava/nio/ByteBuffer;Lit/unimi/dsi/fastutil/ints/IntArrayList;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-sound-cache-link-3',lambda x:member(x,3,'()Ljava/lang/String;','toString')['instructions'].pop())
    neg('missing-sound-cache-link-4',lambda x:member(x,4,'(Ljava/nio/ByteBuffer;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-sound-cache-link-5',lambda x:member(x,5,'()Ljavax/sound/sampled/AudioFormat;','m_6206_')['instructions'].pop())
    neg('missing-sound-cache-link-6',lambda x:member(x,6,'()[Lcom/elfmcys/yesstevemodel/O0Oooooo0000Oo0o00oOoooO;','values')['instructions'].pop())
    neg('missing-sound-cache-link-7',lambda x:member(x,7,'()V','<clinit>')['instructions'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
