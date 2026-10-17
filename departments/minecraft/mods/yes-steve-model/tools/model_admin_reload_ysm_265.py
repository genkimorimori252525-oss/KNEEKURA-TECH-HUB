#!/usr/bin/env python3
"""MODEL-ADMIN-RELOAD fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'com/elfmcys/yesstevemodel/oO0000ooOOOo0OOoOo0o0O00']
SELECTED=set([('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/mojang/brigadier/builder/LiteralArgumentBuilder;'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/mojang/brigadier/context/CommandContext;)I'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/mojang/brigadier/context/CommandContext;Z)I'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/mojang/brigadier/context/CommandContext;)I'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'O00OOOooOoooOoo0o0o0oO0O', '(Lcom/mojang/brigadier/context/CommandContext;)I'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(ZLcom/mojang/brigadier/context/CommandContext;Ljava/lang/String;Lnet/minecraft/server/level/ServerPlayer;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(ZLcom/mojang/brigadier/context/CommandContext;Ljava/lang/String;Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Lnet/minecraft/server/level/ServerPlayer;)Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lorg/apache/commons/lang3/time/StopWatch;Lcom/mojang/brigadier/context/CommandContext;Lcom/elfmcys/yesstevemodel/oOoOO0OO0o0Oooo00OOOOoO0;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/mojang/brigadier/context/CommandContext;Lorg/apache/commons/lang3/time/StopWatch;Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Ljava/lang/String;Lcom/mojang/brigadier/context/CommandContext;Lnet/minecraft/server/level/ServerPlayer;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Ljava/lang/String;Ljava/lang/String;Lcom/mojang/brigadier/context/CommandContext;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Ljava/lang/String;Lcom/mojang/brigadier/context/CommandContext;Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oOOOo0OOO0ooooo0O00OO0o0;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;Lnet/minecraft/server/level/ServerPlayer;)Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'O00OOOooOoooOoo0o0o0oO0O', '(Ljava/lang/String;Lnet/minecraft/server/level/ServerPlayer;)Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;Ljava/lang/String;Lcom/mojang/brigadier/context/CommandContext;Lnet/minecraft/server/level/ServerPlayer;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Ljava/lang/String;Lcom/mojang/brigadier/context/CommandContext;Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'oOOOo0OOO0ooooo0O00OO0o0', '(Ljava/lang/String;Lnet/minecraft/server/level/ServerPlayer;)Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Lnet/minecraft/network/chat/Component;'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'oOOOo0OOO0ooooo0O00OO0o0', '(Lcom/mojang/brigadier/context/CommandContext;)I'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/commands/CommandSourceStack;)Z'), ('com/elfmcys/yesstevemodel/oOo0ooooOO0OOoo0Ooo0oOO0', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/oO0000ooOOOo0OOoOo0o0O00', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oO0000ooOOOo0OOoOo0o0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/server/ServerAboutToStartEvent;)V'), ('com/elfmcys/yesstevemodel/oO0000ooOOOo0OOoOo0o0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/server/ServerAboutToStartEvent;Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;)V'), ('com/elfmcys/yesstevemodel/oO0000ooOOOo0OOoOo0o0O00', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/command/sub/ModelCommand.java', 'abbc1c1518d91c19d655de9de253912ac9236439f879a1a366376965b1276b05', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/event/ServerStartingEvent.java', 'aec84b18515844c8e3d312eece95f19e910585e84c8064de02d2c82fb0f2dfcb', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-28-methods',len(ids)==len(set(ids))==28 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==2 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==2 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-admin-annotations',e.get('event_annotations')==details.get('_event_annotations'))
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
    neg('changed-render-entry-owner-0',lambda x:member(x,0,'()V','<init>')['instructions'].pop())
    neg('changed-render-entry-owner-1',lambda x:member(x,1,'()V','<init>')['instructions'].pop())
    neg('missing-admin-annotations',lambda x:x['event_annotations'].pop())
    neg('changed-default-texture-access',lambda x:op(x,0,'(Lcom/mojang/brigadier/context/CommandContext;Z)I',118)['reference'].update(name='missing'))
    neg('changed-startup-reload',lambda x:op(x,1,'(Lnet/minecraftforge/event/server/ServerAboutToStartEvent;)V',14)['reference'].update(name='missing'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
