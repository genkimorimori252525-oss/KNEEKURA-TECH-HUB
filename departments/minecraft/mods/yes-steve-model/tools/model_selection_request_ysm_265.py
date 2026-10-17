#!/usr/bin/env python3
"""MODEL-SELECTION-REQUEST fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', 'com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'com/elfmcys/yesstevemodel/OoO000oOOOoO00OoOoOOo0OO']
SELECTED=set([('com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', '<init>', '(Ljava/lang/String;Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;'), ('com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;Lnet/minecraft/server/level/ServerPlayer;)V'), ('com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oOOOo0OOO0ooooo0O00OO0o0;)V'), ('com/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/network/NetworkEvent$Context;Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;)V'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', '<init>', '(IIZLcom/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo;Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;)V'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo;Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;)Lnet/minecraft/network/chat/MutableComponent;'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'm_6035_', '()Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'm_5691_', '()V'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'm_87963_', '(Lnet/minecraft/client/gui/GuiGraphics;IIF)V'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/gui/GuiGraphics;Lnet/minecraft/client/gui/screens/Screen;II)V'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'm_93680_', '(DD)Z'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/gui/GuiGraphics;IIILcom/elfmcys/yesstevemodel/o0o0Oooo00OoOoOOOooo0000;)V'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/gui/components/Button;)V'), ('com/elfmcys/yesstevemodel/o0o0oO0O0oo00o000000OOOO', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OoO000oOOOoO00OoOoOOo0OO', '<init>', '(IILcom/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo;Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;)V'), ('com/elfmcys/yesstevemodel/OoO000oOOOoO00OoOoOOo0OO', 'm_5691_', '()V'), ('com/elfmcys/yesstevemodel/OoO000oOOOoO00OoOoOOo0OO', 'm_87963_', '(Lnet/minecraft/client/gui/GuiGraphics;IIF)V'), ('com/elfmcys/yesstevemodel/OoO000oOOOoO00OoOoOOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/gui/GuiGraphics;F)V'), ('com/elfmcys/yesstevemodel/OoO000oOOOoO00OoOoOOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V'), ('com/elfmcys/yesstevemodel/OoO000oOOOoO00OoOoOOo0OO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/gui/components/Button;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/network/message/SetModelAndTexture.java', '7138987b3ad3cebb40f8b64a84ea77ed3c91caabdad10bd55e0679bb968b16a6', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/gui/button/ModelButton.java', 'ad313d958c7f15d69e4e914f3a79566d62ac6c2859bedcd5906c6970875597ce', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/gui/button/TextureButton.java', 'cc18b9587291e30d15abe0e52b99885b472c12fd6695bfa81f090a3cc600a1cc', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-25-methods',len(ids)==len(set(ids))==25 and set(ids)==set(actual)==SELECTED)
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
    neg('missing-model-selection-owner-0',lambda x:member(x,0,'(Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;Lnet/minecraft/network/FriendlyByteBuf;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-selection-owner-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/O00000oOo0o0o00OOoo0O0oo;Lcom/elfmcys/yesstevemodel/oOo0oO0OOo0ooOoo0oOo0oOo;)Lnet/minecraft/network/chat/MutableComponent;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-selection-owner-2',lambda x:member(x,2,'()V','m_5691_')['instructions'].pop())
    neg('reversed-server-direction',lambda x:op(x,0,'(Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;Ljava/util/function/Supplier;)V',20).update(opcode='0x9a'))
    neg('reversed-model-switch-gate',lambda x:op(x,0,'(Lnet/minecraftforge/network/NetworkEvent$Context;Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;)V',22).update(opcode='0x9a'))
    neg('missing-animation-stop',lambda x:op(x,0,'(Lcom/elfmcys/yesstevemodel/O0Oo0oooOoOOO0oOoOOoOooo;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oOOOo0OOO0ooooo0O00OO0o0;)V',95)['reference'].update(name='missing'))
    neg('reversed-cached-roaming-gate',lambda x:op(x,1,'(Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V',23).update(opcode='0x9a'))
    neg('missing-local-texture-update',lambda x:op(x,2,'(Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V',8)['reference'].update(name='missing'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
