#!/usr/bin/env python3
"""MOLANG-COMMAND-PRODUCER fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/o0o000oO00o0O0OOO0O0OOoo', 'com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', 'com/elfmcys/yesstevemodel/OOoO0ooOOoO00oOoo0OOOoo0', 'com/elfmcys/yesstevemodel/OoOo0000o0o0o00o0o0Oo00o', 'com/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo']
SELECTED=set([('com/elfmcys/yesstevemodel/o0o000oO00o0O0OOO0O0OOoo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/o0o000oO00o0O0OOO0O0OOoo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/mojang/brigadier/builder/LiteralArgumentBuilder;'), ('com/elfmcys/yesstevemodel/o0o000oO00o0O0OOO0O0OOoo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/mojang/brigadier/context/CommandContext;)I'), ('com/elfmcys/yesstevemodel/o0o000oO00o0O0OOO0O0OOoo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Ljava/util/Collection;)I'), ('com/elfmcys/yesstevemodel/o0o000oO00o0O0OOO0O0OOoo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/commands/CommandSourceStack;)Z'), ('com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/chat/Component;)Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)Z'), ('com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;I)Z'), ('com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/commands/CommandSourceStack;I)Z'), ('com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/commands/CommandSourceStack;Lnet/minecraft/network/chat/Component;Z)V'), ('com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/commands/CommandSourceStack;Lnet/minecraft/server/MinecraftServer;Lnet/minecraft/network/chat/Component;Z)V'), ('com/elfmcys/yesstevemodel/OOO00O0Oo00oooooo0ooo00O', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/network/chat/Component;)Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/OOoO0ooOOoO00oOoo0OOOoo0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOoO0ooOOoO00oOoo0OOOoo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/mojang/brigadier/CommandDispatcher;)V'), ('com/elfmcys/yesstevemodel/OOoO0ooOOoO00oOoo0OOOoo0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/mojang/brigadier/CommandDispatcher;)V'), ('com/elfmcys/yesstevemodel/OOoO0ooOOoO00oOoo0OOOoo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/mojang/brigadier/context/CommandContext;)I'), ('com/elfmcys/yesstevemodel/OoOo0000o0o0o00o0o0Oo00o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/RegisterCommandsEvent;)V'), ('com/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo', '<init>', '(Ljava/lang/String;I)V'), ('com/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo;'), ('com/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo;Ljava/util/function/Supplier;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/command/sub/MolangCommand.java', 'ee583caa89c5bbf3b6237d711c0e54ffe2d1fa92cd37a5da21eb035596f8a311', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/util/CommandUtil.java', 'b06968b1c1c27debefdfb9da85f8054d43cb19113b80c6577578be3133b42535', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/command/RootCommand.java', '03081333e4c8f9a0bb6a2c6d3ae0d90761de93641da22b08122678a8ba88aa17', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/event/CommandRegistry.java', '50c9fa537c8848b54ab1f2ed79b1b68efe940b45ab201f54b825f88184c05a39', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/SubmitRouletteConfig.java', 'b7f80fbbc249c3e4dc8ce0f6c4a56abc3d8511cf0236f48038e2bbae26838bf4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

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
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==5 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==5 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-command-registration-annotations',e.get('event_annotations')==details.get('_event_annotations'))
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
    with zipfile.ZipFile(a.jar) as z:details['_event_annotations']=[annotations(z.read(o+'.class')) for o in OWNERS]
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'()Lcom/mojang/brigadier/builder/LiteralArgumentBuilder;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'(Lnet/minecraft/network/chat/Component;)Lnet/minecraft/network/chat/Component;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'(Lcom/mojang/brigadier/CommandDispatcher;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-3',lambda x:member(x,3,'(Lnet/minecraftforge/event/RegisterCommandsEvent;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-4',lambda x:member(x,4,'(Lcom/elfmcys/yesstevemodel/oOooOooO0Oo0oo0o0o00O0Oo;Lnet/minecraft/network/FriendlyByteBuf;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-registration-annotations',lambda x:x['event_annotations'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
