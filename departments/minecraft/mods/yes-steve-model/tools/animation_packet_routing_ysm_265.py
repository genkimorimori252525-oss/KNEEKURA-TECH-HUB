#!/usr/bin/env python3
"""ANIMATION-PACKET-ROUTING fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', 'com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO']
SELECTED=set([('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', '<init>', '(ILjava/lang/String;I)V'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', '<init>', '(ILjava/lang/String;)V'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(I)Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;Lnet/minecraft/server/level/ServerPlayer;)V'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0;)V'), ('com/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/network/NetworkEvent$Context;Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;)V'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', '<init>', '(Lcom/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0;)V'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o;'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o;Lnet/minecraft/server/level/ServerLevel;)V'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;Lcom/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Lcom/elfmcys/yesstevemodel/oOOOooO00oo0oOooooOO0Oo0;)V'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOOOooO00oo0oOooooOO0Oo0;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;Lit/unimi/dsi/fastutil/objects/Object2FloatOpenHashMap;)V'), ('com/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o;Lnet/minecraft/server/level/ServerPlayer;)V'), ('com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', '<init>', '(ILjava/lang/String;)V'), ('com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', '<init>', '([ILjava/lang/String;)V'), ('com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO;'), ('com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO;)V'), ('com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V'), ('com/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lcom/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO;)V'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/Connection;Ljava/lang/String;)Z'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/server/level/ServerPlayer;)Z'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/Connection;)Z'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'o0OOooo0o0OO00OoOOOo0o0O', '()V'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Object;Lnet/minecraft/world/entity/player/Player;)V'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/Object;)V'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/Object;Lnet/minecraft/world/entity/Entity;)V'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/Object;Lnet/minecraft/world/entity/player/Player;)V'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/player/Player;)Lnet/minecraft/world/entity/Entity;'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/world/entity/Entity;'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/world/entity/player/Player;)Lnet/minecraft/server/level/ServerPlayer;'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)Z'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'o0OOooo0o0OO00OoOOOo0o0O', '(Ljava/lang/String;)Z'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', 'O00OOOooOoooOoo0o0o0oO0O', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/OO00OoOOOOooO0ooOoOoOooO', '<clinit>', '()V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/network/message/SetPlayAnimation.java', '16678db7ae30648c7e6fe93baa458cff01940951e7b51923c6bfbd7034e4164b', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/SubmitRoamingVarsChanges.java', '53d526daa9a4378cb53312122dd26d5e310bc759f7de2958e1191f617917b544', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/ExecuteMolang.java', '4f682ff7dab5fafcc61d1ba02c9733abf8b29b302e4deaa45c305938404b6fc1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/NetworkHandler.java', 'a0ec09dad1a79f6d4cf544ac6de5cdf5702293512a47b1d55cb4b0d1a13a05fe', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-46-methods',len(ids)==len(set(ids))==46 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==4 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==4 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-packet-client-only-annotations',e.get('event_annotations')==details.get('_event_annotations'))
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'()Lcom/elfmcys/yesstevemodel/OO00OOoo0ooO0o000O0oO0oO;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'(Lcom/elfmcys/yesstevemodel/oOOoOo0o0OOOooo00OOo0O0o;Lnet/minecraft/network/FriendlyByteBuf;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'(Lcom/elfmcys/yesstevemodel/o0oo0O0o0oO0O0o0OoOOOoOO;Lnet/minecraft/network/FriendlyByteBuf;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-3',lambda x:member(x,3,'(Lnet/minecraft/network/Connection;Ljava/lang/String;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-packet-annotations',lambda x:x['event_annotations'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
