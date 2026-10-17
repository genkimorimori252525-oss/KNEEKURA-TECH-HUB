#!/usr/bin/env python3
"""TYPED-QUERY-GUARDS fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/O0OooO0o0000O0OOoO000O0O', 'com/elfmcys/yesstevemodel/O0o0OO0oO0o0o00oOoOOO0O0', 'com/elfmcys/yesstevemodel/OOO00ooO0O000o0ooOoooO0o', 'com/elfmcys/yesstevemodel/OOO0O00OO000OOO0000OOoOO', 'com/elfmcys/yesstevemodel/OOOO00o000o00OoOOo0o0oOO', 'com/elfmcys/yesstevemodel/Oo00oo000oO00o000OOoO0oO', 'com/elfmcys/yesstevemodel/Oo00ooOO0O0o00OOO00oOO00', 'com/elfmcys/yesstevemodel/Oo0oO0oo000oOo0Oo00oOOOO', 'com/elfmcys/yesstevemodel/OooOOo00Oo0OOo0oO0OO0OOO', 'com/elfmcys/yesstevemodel/o0OO000oOOO00O0OoOo0OOo0', 'com/elfmcys/yesstevemodel/o0OOooOo00oOo00oO0oooOoO', 'com/elfmcys/yesstevemodel/o0Oo0ooOoOo0ooOOo0Ooo0O0', 'com/elfmcys/yesstevemodel/oo00OO0oO0oOoo00o0OoOoOo', 'com/elfmcys/yesstevemodel/oo0ooOO00ooO0ooOO0OOoOoO', 'com/elfmcys/yesstevemodel/ooOO0oo0o0OOoOoOO0oOo00O', 'com/elfmcys/yesstevemodel/ooo0oo00O0o00Oo0OO0o0oo0', 'com/elfmcys/yesstevemodel/oooo0Ooo00oO0oOoo00ooO0o', 'com/elfmcys/yesstevemodel/oOO0OOooo00oo0oOOOOoO00O', 'com/elfmcys/yesstevemodel/OOooOO0OoOOOOOOoO000oOOO', 'com/elfmcys/yesstevemodel/oOoOoO0O000OOoo000O0OO00']
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/TamableEntityVariable.java', '4398c2447cbd89aff4c5678d28cc634ee83f798b49712c2b0feaa3136cfe588c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/PlayerVariable.java', 'c7d18797e59f2ebcc16b8533304127c53edbe4605f0920be360f4c1729624999', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/block/AbstractBlockVariable.java', '4095f0e90128cd2961aaa0f4d329b8e575ef0a7448c2d44c74374c59281c5627', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/AbstractArrowVariable.java', '1e3429ec3c2517be06994cffa89551668513470f066c9ba71b1f8224546640e4', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/EntityVariable.java', '51ffcd03cdb4926065ca91fa421593d567e5f41a3bf2b8e981e410b14848527e', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/FishingHookVariable.java', 'c0b1d71ee4f3c46d2da4508339c31f56fb73e05623f112b55f08f6cce21892c9', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/ClientPlayerVariable.java', '7b6e45ee869452042d5df3f0d7afd282812a11df83f568bb43e4dae20586cc5f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/ArrowVariable.java', 'c6cc8f1242f297abe7b3f335f5eb55fe213b0bb6a4450c5bb495e15696f1dcd7', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/LivingEntityVariable.java', '1fcd0337f3c086783b7cdd72a83588546629b729cab4f6c510747a46e4a2c7f2', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/block/BlockStateVariable.java', '752ad6ad63d994924e211e419cc087c4300f49b055da1d8a318f1491cee3ed3f', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/item/ItemStackVariable.java', 'd855e0076fcdc477382c6182410271aa188ad4f60813a106289067923699f255', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/LocalPlayerVariable.java', 'a8b4abc82f713cb0352386c13ef5ea255c7d8964680db1884fc716477da04032', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/ThrowableItemProjectileVariable.java', '01014156fd68f2cdbb69bba9967a3fd3eee05cc2a3d6b2293bb9ce40a0a436d1', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/ProjectileVariable.java', 'bab8c1bd6eaded6e7c9b2a183223b3e5890e13ac525afa5283dda2a283b81360', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/entity/MobEntityVariable.java', '72f0cfbf32ae7b2fc60e3137a1020a8d8ac74cbe76b42a396924b788ee09e147', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/item/ItemVariable.java', '730441984663b9caf1a75d0bb031fb571ee06c6a2209c79c6f1da0a43bcf9d2c', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/block/BlockVariable.java', 'cda3dfb0569632e3f40dbeb6a93524a574f3dd132e211df3dd854c95148eab73', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/ContextVariable.java', '3974af193316d8cf3648a68860fa2012cdb05866aeb2e537474737c2df7f1e71', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/variable/LambdaVariable.java', '3a92785de4a5f3958b8ba19cdfecd97940db003fbe00e83a22ebcaaa34a67e41', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/molang/binding/ContextBinding.java', '6e2940901a533435fdafcbdc2e2f6c8deb6b46fe034ac3f49f9c95d98fb1c134', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

GUARDS=[{'owner': 'com/elfmcys/yesstevemodel/O0OooO0o0000O0OOoO000O0O', 'predicate_types': ['net/minecraft/world/entity/TamableAnimal']}, {'owner': 'com/elfmcys/yesstevemodel/O0o0OO0oO0o0o00oOoOOO0O0', 'predicate_types': ['net/minecraft/world/entity/player/Player']}, {'owner': 'com/elfmcys/yesstevemodel/OOO00ooO0O000o0ooOoooO0o', 'predicate_types': ['net/minecraft/world/level/block/state/BlockBehaviour']}, {'owner': 'com/elfmcys/yesstevemodel/OOO0O00OO000OOO0000OOoOO', 'predicate_types': ['net/minecraft/world/entity/projectile/AbstractArrow']}, {'owner': 'com/elfmcys/yesstevemodel/OOOO00o000o00OoOOo0o0oOO', 'predicate_types': ['net/minecraft/world/entity/Entity']}, {'owner': 'com/elfmcys/yesstevemodel/Oo00oo000oO00o000OOoO0oO', 'predicate_types': ['net/minecraft/world/entity/projectile/FishingHook']}, {'owner': 'com/elfmcys/yesstevemodel/Oo00ooOO0O0o00OOO00oOO00', 'predicate_types': ['net/minecraft/client/player/AbstractClientPlayer']}, {'owner': 'com/elfmcys/yesstevemodel/Oo0oO0oo000oOo0Oo00oOOOO', 'predicate_types': ['net/minecraft/world/entity/projectile/Arrow']}, {'owner': 'com/elfmcys/yesstevemodel/OooOOo00Oo0OOo0oO0OO0OOO', 'predicate_types': ['net/minecraft/world/entity/LivingEntity']}, {'owner': 'com/elfmcys/yesstevemodel/o0OO000oOOO00O0OoOo0OOo0', 'predicate_types': ['net/minecraft/world/level/block/state/BlockState']}, {'owner': 'com/elfmcys/yesstevemodel/o0OOooOo00oOo00oO0oooOoO', 'predicate_types': ['net/minecraft/world/item/ItemStack']}, {'owner': 'com/elfmcys/yesstevemodel/o0Oo0ooOoOo0ooOOo0Ooo0O0', 'predicate_types': ['net/minecraft/client/player/LocalPlayer']}, {'owner': 'com/elfmcys/yesstevemodel/oo00OO0oO0oOoo00o0OoOoOo', 'predicate_types': ['net/minecraft/world/entity/projectile/ThrowableItemProjectile']}, {'owner': 'com/elfmcys/yesstevemodel/oo0ooOO00ooO0ooOO0OOoOoO', 'predicate_types': ['net/minecraft/world/entity/projectile/Projectile']}, {'owner': 'com/elfmcys/yesstevemodel/ooOO0oo0o0OOoOoOO0oOo00O', 'predicate_types': ['net/minecraft/world/entity/Mob']}, {'owner': 'com/elfmcys/yesstevemodel/ooo0oo00O0o00Oo0OO0o0oo0', 'predicate_types': ['net/minecraft/world/item/Item']}, {'owner': 'com/elfmcys/yesstevemodel/oooo0Ooo00oO0oOoo00ooO0o', 'predicate_types': ['net/minecraft/world/level/block/Block']}]
KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    ck('closed-direct-lambda-family',e.get('direct_lambda_subclasses')==GUARDS)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('complete-63-methods',len(ids)==len(set(ids))==63 and set(ids)==set(actual))
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('twenty-declarations',len(ds)==20 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('twenty-bootstrap-records',len(bs)==20 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('twenty-fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
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
            actual.update({ident(m):m for m in parse_bounded(b,True)})
    with zipfile.ZipFile(a.jar) as z:
        family=[]
        for path in sorted(n for n in z.namelist() if n.endswith('.class')):
            c=parse_class(z.read(path))
            if c['super']=='com/elfmcys/yesstevemodel/OOooOO0OoOOOOOOoO000oOOO':
                ms=parse_bounded(z.read(path),True)
                family.append({'owner':c['name'],'predicate_types':[op['reference']['class_name'] for m in ms for op in m.get('instructions',[]) if op['opcode']=='0xc1']})
        if family!=e.get('direct_lambda_subclasses') or {r['owner'] for r in family}!=set(OWNERS[:17]):raise SystemExit('Typed guard family mismatch')
    details=copy.deepcopy(BOUNDDETAILS);checks=audit(e,actual,decl,details);root=Path(a.source_root)
    revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    checks.append({'check':'source-revision','pass':revision==SOURCES[0][2]})
    for path,sha,rev in SOURCES:checks.append({'check':'source:'+path,'pass':hashlib.sha256((root/path).read_bytes()).hexdigest()==sha})
    negatives=[]
    def member(x,owner,desc,name=None):return next(m for m in x['members'] if m['owner']==OWNERS[owner] and m['descriptor']==desc and (name is None or m['name']==name))
    def op(x,owner,desc,offset,name=None):return next(o for o in member(x,owner,desc,name)['instructions'] if o['offset']==offset)
    def neg(name,mutate):
        x=copy.deepcopy(e);mutate(x);fail=[c for c in audit(x,actual,decl,details) if not c['pass']];negatives.append({'control':name,'rejected':bool(fail)})
    neg('missing-typed-family-member',lambda x:x['direct_lambda_subclasses'].pop())
    neg('missing-method',lambda x:x['members'].pop())
    neg('missing-owner',lambda x:x['owner_declarations'].pop())
    neg('missing-source',lambda x:x['source_tracks'].pop())
    neg('missing-bootstrap',lambda x:x['bootstrap_and_constant_evidence'].pop())
    neg('wrong-artifact',lambda x:x['artifact'].update(sha256='0'*64))
    neg('wrong-predicate-0',lambda x:op(x,0,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-1',lambda x:op(x,1,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-2',lambda x:op(x,2,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-3',lambda x:op(x,3,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-4',lambda x:op(x,4,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-5',lambda x:op(x,5,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-6',lambda x:op(x,6,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-7',lambda x:op(x,7,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-8',lambda x:op(x,8,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-9',lambda x:op(x,9,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-10',lambda x:op(x,10,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-11',lambda x:op(x,11,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-12',lambda x:op(x,12,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-13',lambda x:op(x,13,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-14',lambda x:op(x,14,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-15',lambda x:op(x,15,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    neg('wrong-predicate-16',lambda x:op(x,16,'(Lcom/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O;)Z',6)['reference'].update(class_name='java/lang/Object'))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
