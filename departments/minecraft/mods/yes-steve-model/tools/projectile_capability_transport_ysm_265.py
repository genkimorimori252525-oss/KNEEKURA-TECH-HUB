#!/usr/bin/env python3
"""PROJECTILE-CAPABILITY-TRANSPORT fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
from mixin_annotations_ysm_265 import annotations
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO', 'com/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo', 'com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', 'com/elfmcys/yesstevemodel/Ooooo0oooO0oooOOOoO0000O', 'com/elfmcys/yesstevemodel/oo0OoO00oOoo000O0000o0oo', 'com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', 'com/elfmcys/yesstevemodel/mixin/ProjectileEntityMixin']
SELECTED=set([('com/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO', '<init>', '(Lnet/minecraft/world/entity/projectile/Projectile;)V'), ('com/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;)V'), ('com/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lit/unimi/dsi/fastutil/ints/Int2FloatOpenHashMap;)V'), ('com/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(FZ)V'), ('com/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo', '<init>', '(Lnet/minecraft/world/entity/projectile/Projectile;)V'), ('com/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO;'), ('com/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo', 'getCapability', '(Lnet/minecraftforge/common/capabilities/Capability;Lnet/minecraft/core/Direction;)Lnet/minecraftforge/common/util/LazyOptional;'), ('com/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO;'), ('com/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', '<init>', '()V'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Ljava/lang/String;Lit/unimi/dsi/fastutil/objects/Object2FloatOpenHashMap;)V'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;)V'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Ljava/lang/String;'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'o0OOooo0o0OO00OoOOOo0o0O', '()Z'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'O00OOOooOoooOoo0o0o0oO0O', '()Lit/unimi/dsi/fastutil/objects/Object2FloatOpenHashMap;'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'oOOOo0OOO0ooooo0O00OO0o0', '()Lnet/minecraft/nbt/CompoundTag;'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/nbt/CompoundTag;)V'), ('com/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/nbt/CompoundTag;Lit/unimi/dsi/fastutil/objects/Object2FloatMap$Entry;)V'), ('com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', 'getCapability', '(Lnet/minecraftforge/common/capabilities/Capability;Lnet/minecraft/core/Direction;)Lnet/minecraftforge/common/util/LazyOptional;'), ('com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;'), ('com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lnet/minecraft/nbt/CompoundTag;'), ('com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/nbt/CompoundTag;)V'), ('com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', 'deserializeNBT', '(Lnet/minecraft/nbt/Tag;)V'), ('com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', 'serializeNBT', '()Lnet/minecraft/nbt/Tag;'), ('com/elfmcys/yesstevemodel/OO0ooO00OoO00o0OO0OOooO0', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/Ooooo0oooO0oooOOOoO0000O', '<init>', '(Lcom/elfmcys/yesstevemodel/O0o00oO0O0ooOOOo0oo0Oo00;Lcom/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo;)V'), ('com/elfmcys/yesstevemodel/Ooooo0oooO0oooOOOoO0000O', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/O0o00oO0O0ooOOOo0oo0Oo00;'), ('com/elfmcys/yesstevemodel/Ooooo0oooO0oooOOOoO0000O', 'o0OOooo0o0OO00OoOOOo0o0O', '()Lcom/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo;'), ('com/elfmcys/yesstevemodel/oo0OoO00oOoo000O0000o0oo', '<init>', '(Lcom/elfmcys/yesstevemodel/O0o00oO0O0ooOOOo0oo0Oo00;Lcom/elfmcys/yesstevemodel/oOo0o0000OOOO0OooooO00oo;)V'), ('com/elfmcys/yesstevemodel/oo0OoO00oOoo000O0000o0oo', 'getCapability', '(Lnet/minecraftforge/common/capabilities/Capability;Lnet/minecraft/core/Direction;)Lnet/minecraftforge/common/util/LazyOptional;'), ('com/elfmcys/yesstevemodel/oo0OoO00oOoo000O0000o0oo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Lcom/elfmcys/yesstevemodel/Ooooo0oooO0oooOOOoO0000O;'), ('com/elfmcys/yesstevemodel/oo0OoO00oOoo000O0000o0oo', '<clinit>', '()V'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', '<init>', '(ILcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;Lit/unimi/dsi/fastutil/ints/Int2FloatOpenHashMap;)V'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', '<init>', '(ILcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;)V'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo;Lnet/minecraft/network/FriendlyByteBuf;)V'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/network/FriendlyByteBuf;)Lcom/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo;'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo;Ljava/util/function/Supplier;)V'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;Lit/unimi/dsi/fastutil/ints/Int2FloatOpenHashMap;)V'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;Lit/unimi/dsi/fastutil/ints/Int2FloatOpenHashMap;Lcom/elfmcys/yesstevemodel/Ooooo0oooO0oooOOOoO0000O;)V'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lcom/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo;Lnet/minecraft/world/entity/Entity;)V'), ('com/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lit/unimi/dsi/fastutil/ints/Int2FloatOpenHashMap;Lit/unimi/dsi/fastutil/objects/Object2FloatMap$Entry;)V'), ('com/elfmcys/yesstevemodel/mixin/ProjectileEntityMixin', '<init>', '()V'), ('com/elfmcys/yesstevemodel/mixin/ProjectileEntityMixin', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/world/entity/Entity;Lorg/spongepowered/asm/mixin/injection/callback/CallbackInfo;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/capability/ProjectileAnimatableCapability.java', '303fd98205b0afe0b4341d849c44993669ea4758b4f847dfbbd22ee297aa0e1a', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/ProjectileAnimatableCapabilityProvider.java', '5f73256f9ddae669866b2790872941aed6031cf9b00027e580c605075a275e66', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/ProjectileModelInfoCapability.java', '7435fb9132eda1239aead64b2a84339220417a49023bcd055d84693a0c059471', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/ProjectileModelInfoCapabilityProvider.java', 'e29c473db14184d21b0d2ab8b537bc903b6b82d9e82444978e0704facdadf033', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/ClientLazyCapability.java', 'a13ba1830677baf967c6e6f4c8146890e5d497f470b0ec2c2f4a0e47caadf872', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/capability/ClientLazyCapabilityProvider.java', 'cee49faef29a78ddb8cfebe35bc01f094fe7e89c12c4f0b26cf93a91846ca248', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/network/message/SyncProjectileModelInfo.java', '82910686c26bf121c3154d6a2187b6bdde624ec031c6c0b172eeee3e77405579', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/mixin/ProjectileEntityMixin.java', 'b78bb62518beb56adbf26411ee21278e3adda98068a9a089e8d171bcda393f88', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-44-methods',len(ids)==len(set(ids))==44 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('fixed-owner-declarations',len(ds)==8 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('fixed-bootstrap-records',len(bs)==8 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    ck('exact-client-mixin-annotations',e.get('event_annotations')==details.get('_event_annotations'))
    ck('exact-projectile-mixin-metadata',e.get('projectile_mixin_metadata')==details.get('_projectile_mixin_metadata'))
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
    with zipfile.ZipFile(a.jar) as z:
        details['_event_annotations']=[annotations(z.read(o+'.class')) for o in OWNERS]
        ref=json.loads(z.read('yes_steve_model.refmap.json'));cfg=json.loads(z.read('yes_steve_model.mixins.json'))
        details['_projectile_mixin_metadata']={'configured':'ProjectileEntityMixin' in cfg.get('mixins',[]),'refmap':ref.get('mappings',{}).get(OWNERS[-1]),'runtime_injection_verified':False}
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
    neg('missing-projectile-transport-owner-0',lambda x:member(x,0,'(Ljava/lang/String;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-projectile-transport-owner-1',lambda x:member(x,1,'()Lcom/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-projectile-transport-owner-2',lambda x:member(x,2,'(Ljava/lang/String;Lit/unimi/dsi/fastutil/objects/Object2FloatOpenHashMap;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-projectile-transport-owner-3',lambda x:member(x,3,'(Lnet/minecraftforge/common/capabilities/Capability;Lnet/minecraft/core/Direction;)Lnet/minecraftforge/common/util/LazyOptional;','getCapability')['instructions'].pop())
    neg('missing-projectile-transport-owner-4',lambda x:member(x,4,'()Lcom/elfmcys/yesstevemodel/O0o00oO0O0ooOOOo0oo0Oo00;','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-projectile-transport-owner-5',lambda x:member(x,5,'(Lnet/minecraftforge/common/capabilities/Capability;Lnet/minecraft/core/Direction;)Lnet/minecraftforge/common/util/LazyOptional;','getCapability')['instructions'].pop())
    neg('missing-projectile-transport-owner-6',lambda x:member(x,6,'(Lcom/elfmcys/yesstevemodel/OOOOoO00oo0000OO0ooo0OOo;Lnet/minecraft/network/FriendlyByteBuf;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-projectile-transport-owner-7',lambda x:member(x,7,'(Lnet/minecraft/world/entity/Entity;Lorg/spongepowered/asm/mixin/injection/callback/CallbackInfo;)V','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('missing-client-mixin-annotations',lambda x:x['event_annotations'].pop())
    neg('invented-runtime-injection',lambda x:x['projectile_mixin_metadata'].update(runtime_injection_verified=True))
    neg('reversed-provider-lazy-gate',lambda x:op(x,1,'()Lcom/elfmcys/yesstevemodel/OOOo0OOOoOO0O00Oo00ooOOO;',4).update(opcode='0xc6'))
    neg('missing-map-replacement',lambda x:op(x,0,'(Lit/unimi/dsi/fastutil/ints/Int2FloatOpenHashMap;)V',13).update(opcode='0x00'))
    neg('invented-copy-clone',lambda x:op(x,2,'(Lcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;)V',21).update(opcode='0xb6'))
    neg('wrong-nbt-clear',lambda x:op(x,2,'(Lnet/minecraft/nbt/CompoundTag;)V',24)['reference'].update(name='putAll'))
    neg('invented-receiver-finally',lambda x:member(x,6,'(Lcom/elfmcys/yesstevemodel/O0ooooOO0oOo000O0Oo00OOO;Lit/unimi/dsi/fastutil/ints/Int2FloatOpenHashMap;Lcom/elfmcys/yesstevemodel/Ooooo0oooO0oooOOOoO0000O;)V')['exception_handlers'].append({'handler':0}))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
