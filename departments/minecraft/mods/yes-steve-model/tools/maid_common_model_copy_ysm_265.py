#!/usr/bin/env python3
"""MAID-COMMON-MODEL-COPY fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', 'com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo']
SELECTED=set([('com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', 'o0OOooo0o0OO00OoOOOo0o0O', '()V'), ('com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)Z'), ('com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/projectile/Projectile;Lnet/minecraft/world/entity/Entity;)V'), ('com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Ljava/lang/String;I)V'), ('com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0;)V'), ('com/elfmcys/yesstevemodel/OOOo0ooOO0000oOOOoOoOOo0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;)Z'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/projectile/Projectile;Lnet/minecraft/world/entity/Entity;)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/entity/Entity;)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Ljava/lang/String;I)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/oOOo0oO0oOOooOOoO0oOooO0;)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;ILcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;Lcom/elfmcys/yesstevemodel/oOoOOo00o00O0ooooOOO0oO0;)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/oOOOooO00oo0oOooooOO0Oo0;)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/entity/passive/EntityMaid;Lnet/minecraft/world/entity/projectile/Projectile;Lcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;)V'), ('com/elfmcys/yesstevemodel/OooOO0oOoOo0o0OoOOOOo00O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Lcom/elfmcys/yesstevemodel/Ooo0OOOOOoooo0oo00OoO0oO;)V'), ('com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent$RightClickBlock;)V'), ('com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/tileentity/TileEntityStatue;Lnet/minecraft/world/entity/player/Player;)V'), ('com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/github/tartaricacid/touhoulittlemaid/tileentity/TileEntityGarageKit;Lnet/minecraft/world/entity/player/Player;)V'), ('com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/nbt/CompoundTag;)V'), ('com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/nbt/CompoundTag;Lcom/elfmcys/yesstevemodel/oooooooOOoOOoO00OooOo00O;)V'), ('com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/nbt/CompoundTag;Lcom/github/tartaricacid/touhoulittlemaid/tileentity/TileEntityGarageKit;Lnet/minecraft/world/entity/EntityType;)V'), ('com/elfmcys/yesstevemodel/OoOo0OOoOOOOO0ooo0O000oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/nbt/CompoundTag;Lcom/github/tartaricacid/touhoulittlemaid/tileentity/TileEntityStatue;Lnet/minecraft/world/entity/EntityType;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/TlmCommonCompat.java', '821199d49dc8fa88dee7b11d373da8f586efb6e1c2a779b3637c86951e4761c3', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/TlmCommonCompatInner.java', '577a56c502a86c53154c97099c3bbf089990c3165adb82b89f597966aa23d06a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/event/CopyYsmModelEvent.java', '3160a32bfb3e42bb87f7c100b5bec3f4eff06eb04e42c01fb5872ef4b98ccb21', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-27-methods',len(ids)==len(set(ids))==27 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('three-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('three-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('three-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-common-side-and-client-only-annotations',e.get('event_annotations')==details.get('_event_annotations'))
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
    neg('missing-model-asset-helper-0',lambda x:member(x,0,'()Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-1',lambda x:member(x,1,'(Lnet/minecraft/world/entity/Entity;)Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-model-asset-helper-2',lambda x:member(x,2,'(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent$RightClickBlock;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-event-annotations',lambda x:x['event_annotations'].pop())
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
