"""Opt-in, exact-source client trace checks; never launch a game or download data."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest

from kneekura_tech_hub.minecraft.storage import ContractError

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
SOURCE=HERE/'java/org/kneekura/staff/CelestialStaffItem.java'
HELPER=HERE/'instrumentation/ClientUseTrace.java'
PIN='4e190bf983d18946791a16f88f21eb48db037e7bdc9be8a0239af08137ab4b04'


def api():
    spec=importlib.util.spec_from_file_location('staff_trace_pilot',HERE/'pilot.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def mdk(path):
    path.mkdir();(path/'gradlew').write_text('#!/bin/sh\nexit 0\n')
    (path/'gradle.properties').write_text('minecraft_version=1.20.1\nforge_version=47.4.6\n')
    return path


def snapshot(root):return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_client_trace_is_explicit_and_default_sources_stay_exact(tmp_path):
    assert HELPER.is_file(), 'Opt-in client trace is missing'
    plain=mdk(tmp_path/'plain');disabled=mdk(tmp_path/'disabled');traced=mdk(tmp_path/'traced')
    module=api();module.configure(plain);module.configure(disabled,client_trace=False)
    assert snapshot(plain)==snapshot(disabled)
    assert (plain/'src/main/java/org/kneekura/staff/CelestialStaffItem.java').read_bytes()==SOURCE.read_bytes()
    assert not list(plain.rglob('ClientUseTrace*'))
    result=module.configure(traced,client_trace=True)
    metadata=result['client_trace']; assert metadata['schema_version']==1
    assert metadata['original_source_sha256']==hashlib.sha256(SOURCE.read_bytes()).hexdigest()==PIN
    assert metadata['instrumented_source_sha256']==hashlib.sha256((traced/'src/main/java/org/kneekura/staff/CelestialStaffItem.java').read_bytes()).hexdigest()
    assert metadata['helper_source_sha256']==hashlib.sha256(HELPER.read_bytes()).hexdigest()
    assert metadata['enabled'] is True
    assert json.loads((traced/'src/main/resources/META-INF/kneekura-client-trace.json').read_text())==metadata
    assert metadata['original_source_sha256']!=metadata['instrumented_source_sha256']
    assert (traced/'src/main/java/org/kneekura/staff/ClientUseTrace.java').read_bytes()==HELPER.read_bytes()
    assert not list(traced.rglob('eula.txt'))


@pytest.mark.parametrize('value',[None,0,1,'true',[],{}])
def test_client_trace_flag_refuses_coercion_without_writes(tmp_path,value):
    module=api();root=mdk(tmp_path/'mdk');before=snapshot(root)
    assert 'client_trace' in __import__('inspect').signature(module.configure).parameters, 'Opt-in flag missing'
    with pytest.raises(ContractError,match='bool'):module.configure(root,client_trace=value)
    assert snapshot(root)==before


def test_instrumenter_is_exact_source_guard_not_general_transformer():
    module=api();assert hasattr(module,'client_trace_sources'), 'Guarded trace generator missing'
    result,helper,metadata=module.client_trace_sources(SOURCE.read_bytes())
    assert helper==HELPER.read_bytes() and metadata['original_source_sha256']==PIN
    assert b'ClientUseTrace.begin(level, player, stack)' in result
    body=SOURCE.read_text().split('        ItemStack stack = player.getItemInHand(hand);\n',1)[1].rsplit('    }\n}',1)[0]
    stripped=result
    for site in ('effect','cooldown'):
        hook=f'        try {{ if (clientTrace != null) clientTrace.mutationAttempt("{site}"); }} catch (Throwable ignored) {{}}\n'.encode()
        stripped=stripped.replace(hook,b'')
    assert body.encode() in stripped, 'Original method statements must remain byte-for-byte after removing the exact probe hooks' 
    for changed in [SOURCE.read_bytes()+b'\n',SOURCE.read_bytes().replace(b'CLIENT_ACK',b'COOLDOWN'),b'other source']:
        with pytest.raises(ContractError,match='source|drift'):module.client_trace_sources(changed)


def test_configure_rejects_drift_before_writing(tmp_path,monkeypatch):
    module=api();assert hasattr(module,'client_trace_sources'), 'Guarded trace generator missing'
    fake=tmp_path/'fixture';(fake/'java/org/kneekura/staff').mkdir(parents=True)
    (fake/'java/org/kneekura/staff/CelestialStaffItem.java').write_bytes(SOURCE.read_bytes()+b'\n')
    monkeypatch.setattr(module,'HERE',fake)
    root=mdk(tmp_path/'mdk');before=snapshot(root)
    with pytest.raises(ContractError,match='source|drift'):module.configure(root,client_trace=True)
    assert snapshot(root)==before


def test_helper_contains_no_game_state_mutators_or_acceptance_override():
    assert HELPER.is_file(), 'Opt-in client trace is missing'
    text=HELPER.read_text()
    for mutator in ['addEffect(', 'removeEffect(', 'addCooldown(', 'removeCooldown(', 'setHealth(', 'hurt(', 'shrink(', 'setCount(', 'setDamageValue(']:
        assert mutator not in text
    assert 'static Map<String, Object> snapshot()' in text
    assert 'setOutcome' not in text and 'forcePass' not in text


STUBS={
'net/minecraft/world/InteractionHand.java':'package net.minecraft.world; public enum InteractionHand { MAIN_HAND, OFF_HAND }',
'net/minecraft/world/InteractionResultHolder.java':'''package net.minecraft.world;
public class InteractionResultHolder<T> {
 public final String result; public final T object;
 private InteractionResultHolder(String r,T o){result=r;object=o;}
 public static <T> InteractionResultHolder<T> success(T o){return new InteractionResultHolder<>("success",o);}
 public static <T> InteractionResultHolder<T> fail(T o){return new InteractionResultHolder<>("fail",o);}
 public static <T> InteractionResultHolder<T> consume(T o){return new InteractionResultHolder<>("consume",o);}
}''',
'net/minecraft/world/level/Level.java':'package net.minecraft.world.level; public class Level { public final boolean isClientSide; public Level(boolean c){isClientSide=c;} }',
'net/minecraft/world/item/Item.java':'''package net.minecraft.world.item; public class Item {
 public String id="kneekura:celestial_staff"; public Item(Properties p){}
 public static class Properties { public Properties stacksTo(int n){return this;} }
 public net.minecraft.world.InteractionResultHolder<ItemStack> use(net.minecraft.world.level.Level l,net.minecraft.world.entity.player.Player p,net.minecraft.world.InteractionHand h){return null;}
}''',
'net/minecraft/world/item/ItemStack.java':'''package net.minecraft.world.item; public class ItemStack {
 public Item item; public int count=1,damage=0; public ItemStack(Item i){item=i;}
 public Item getItem(){return item;} public int getCount(){return count;} public int getDamageValue(){return damage;}
}''',
'net/minecraft/world/item/ItemCooldowns.java':'''package net.minecraft.world.item; public class ItemCooldowns {
 public boolean active=false; public float fraction=0; public int writes=0;
 public boolean isOnCooldown(Item i){return active;} public float getCooldownPercent(Item i,float partial){return fraction;}
 public void addCooldown(Item i,int n){writes++;active=true;fraction=1;}
}''',
'net/minecraft/world/effect/MobEffects.java':'package net.minecraft.world.effect; public class MobEffects { public static final Object GLOWING=new Object(); }',
'net/minecraft/world/effect/MobEffectInstance.java':'''package net.minecraft.world.effect; public class MobEffectInstance {
 public int duration,amplifier; public MobEffectInstance(Object e,int d,int a){duration=d;amplifier=a;}
 public int getDuration(){return duration;} public int getAmplifier(){return amplifier;}
}''',
'net/minecraft/core/registries/BuiltInRegistries.java':'''package net.minecraft.core.registries; public class BuiltInRegistries {
 public static final Registry ITEM=new Registry(); public static class Registry {
  public String getKey(net.minecraft.world.item.Item i){return i.id;}
 }
}''',
'net/minecraft/world/entity/player/Player.java':'''package net.minecraft.world.entity.player;
import net.minecraft.world.item.*; import net.minecraft.world.effect.*;
public class Player {
 public ItemStack stack; public float health=20; public MobEffectInstance effect; public ItemCooldowns cooldown=new ItemCooldowns();
 public boolean broken=false; public int effectWrites=0,cooldownReads=0,throwCooldownAt=0;
 public final RuntimeException originalFailure=new RuntimeException("original-use-failure");
 public Player(Item i){stack=new ItemStack(i);} public ItemStack getItemInHand(net.minecraft.world.InteractionHand h){return stack;}
 public ItemStack getMainHandItem(){return stack;} public float getHealth(){if(broken)throw new IllegalStateException("probe-read");return health;}
 public java.util.UUID getUUID(){return java.util.UUID.fromString("00000000-0000-4000-8000-000000000001");}
 public MobEffectInstance getEffect(Object e){return effect;} public ItemCooldowns getCooldowns(){if(++cooldownReads==throwCooldownAt)throw originalFailure;return cooldown;}
 public boolean addEffect(MobEffectInstance e){effectWrites++;effect=e;return true;}
}''',
}
HARNESS='''package org.kneekura.staff;
import java.util.*; import net.minecraft.world.*; import net.minecraft.world.level.*; import net.minecraft.world.item.*;
import net.minecraft.world.effect.*; import net.minecraft.world.entity.player.*;
public class TraceAssertions {
 static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
 @SuppressWarnings("unchecked") static List<Map<String,Object>> records(){return (List<Map<String,Object>>)ClientUseTrace.snapshot().get("records");}
 static long count(String k){return ((Number)ClientUseTrace.snapshot().get(k)).longValue();}
 static void unknown(Map<String,Object> r){check(Boolean.FALSE.equals(r.get("completed"))&&r.get("unchanged")==null,"must remain UNKNOWN");}
 @SuppressWarnings({"unchecked","rawtypes"}) public static void main(String[] args)throws Exception {
  String mode=args[0]; CelestialStaffItem item=new CelestialStaffItem(); Player p=new Player(item);Level client=new Level(true);
  if(mode.equals("stable")) {
   var result=item.use(client,p,InteractionHand.MAIN_HAND);check(result.result.equals("success")&&result.object==p.stack,"return changed");
   check(count("started")==1&&count("completed")==1&&count("unknown")==0,"counter mismatch");
   var row=records().get(0);check(Boolean.TRUE.equals(row.get("unchanged")),"unchanged state not recorded");
   check(p.effectWrites==0&&p.cooldown.writes==0,"probe wrote game state");
   check(((Number)row.get("effect_mutation_attempts")).longValue()==0&&((Number)row.get("cooldown_mutation_attempts")).longValue()==0,"stable call has mutations");
   check(row.get("player_uuid").equals(p.getUUID().toString()),"wrong player");
  } else if(mode.equals("restore-known-sites")) {
   var scope=ClientUseTrace.begin(client,p,p.stack);
   scope.mutationAttempt("effect");p.effect=new MobEffectInstance(MobEffects.GLOWING,60,0);p.effect=null;
   scope.mutationAttempt("cooldown");p.cooldown.active=true;p.cooldown.fraction=1;p.cooldown.active=false;p.cooldown.fraction=0;
   scope.close();var row=records().get(0);
   check(Boolean.TRUE.equals(row.get("unchanged")),"restoration should be boundary-equal");
   check(((Number)row.get("effect_mutation_attempts")).longValue()==1&&((Number)row.get("cooldown_mutation_attempts")).longValue()==1,"known writes were hidden by restoration");
  } else if(mode.equals("unknown-site")) {
   var scope=ClientUseTrace.begin(client,p,p.stack);scope.mutationAttempt("unregistered");scope.close();unknown(records().get(0));
  } else if(mode.equals("closed-attempt")) {
   var scope=ClientUseTrace.begin(client,p,p.stack);scope.close();scope.mutationAttempt("effect");unknown(records().get(0));check(count("unknown")>0,"closed attempt accepted");
  } else if(mode.equals("foreign-attempt")) {
   var scope=ClientUseTrace.begin(client,p,p.stack);Thread t=new Thread(()->scope.mutationAttempt("effect"));t.start();t.join();scope.close();unknown(records().get(0));
  } else if(mode.equals("server")) {
   var result=item.use(new Level(false),p,InteractionHand.MAIN_HAND);check(result.result.equals("consume"),"server semantics changed");
   check(p.effectWrites==1&&p.cooldown.writes==1&&count("started")==0,"server trace must be no-op");
  } else if(mode.startsWith("mutate-")) {
   var scope=ClientUseTrace.begin(client,p,p.stack);
   switch(mode.substring(7)) {
    case "effect" -> p.effect=new MobEffectInstance(MobEffects.GLOWING,60,0);
    case "duration" -> {p.effect=new MobEffectInstance(MobEffects.GLOWING,61,1);}
    case "cooldown" -> {p.cooldown.active=true;p.cooldown.fraction=1;}
    case "health" -> p.health=19;
    case "stack" -> p.stack.count=0;
    case "damage" -> p.stack.damage=1;
    case "item" -> {p.stack=new ItemStack(new Item(new Item.Properties()));p.stack.item.id="minecraft:stick";}
    default -> throw new AssertionError();
   }
   scope.close();check(Boolean.FALSE.equals(records().get(0).get("unchanged")),"known-bad mutation escaped");
   check(count("completed")==1&&count("unknown")==0,"known change mislabeled UNKNOWN");
  } else if(mode.equals("before-failure")) {
   p.broken=true;var scope=ClientUseTrace.begin(client,p,p.stack);p.broken=false;scope.close();unknown(records().get(0));check(count("unknown")==1&&count("completed")==0,"read failure accepted");
  } else if(mode.equals("after-failure")) {
   var scope=ClientUseTrace.begin(client,p,p.stack);p.broken=true;scope.close();unknown(records().get(0));
  } else if(mode.equals("probe-failure-does-not-change-return")) {
   p.broken=true;var result=item.use(client,p,InteractionHand.MAIN_HAND);check(result.result.equals("success"),"probe exception escaped");unknown(records().get(0));
  } else if(mode.equals("original-exception")) {
   p.throwCooldownAt=2;try{item.use(client,p,InteractionHand.MAIN_HAND);throw new AssertionError("original exception swallowed");}catch(RuntimeException e){check(e==p.originalFailure,"original exception replaced");}
  } else if(mode.equals("bound")) {
   for(int i=0;i<20;i++)item.use(client,p,InteractionHand.MAIN_HAND);
   check(records().size()==16&&count("started")==20&&count("completed")==20&&count("dropped")==4,"unbounded or lost counters");
   check(((Number)records().get(0).get("sequence")).longValue()==5,"wrong retained sequence");
  } else if(mode.equals("foreign-thread")) {
   item.use(client,p,InteractionHand.MAIN_HAND);Thread t=new Thread(()->{var scope=ClientUseTrace.begin(client,p,p.stack);scope.close();});t.start();t.join();
   unknown(records().get(1));check(count("unknown")==1,"foreign thread accepted");
  } else if(mode.equals("cross-thread-close")) {
   var scope=ClientUseTrace.begin(client,p,p.stack);Thread t=new Thread(scope::close);t.start();t.join();unknown(records().get(0));
  } else if(mode.equals("duplicate-close")) {
   var scope=ClientUseTrace.begin(client,p,p.stack);scope.close();scope.close();check(count("completed")==1&&records().size()==1,"duplicate completion");
  } else if(mode.equals("immutable")) {
   item.use(client,p,InteractionHand.MAIN_HAND);Map snap=ClientUseTrace.snapshot();List rows=(List)snap.get("records");Map record=(Map)rows.get(0);Map before=(Map)record.get("before");Map hand=(Map)before.get("main_hand");
   for(Map m:List.of(snap,record,before,hand))try{m.put("fake",true);throw new AssertionError("mutable map");}catch(UnsupportedOperationException expected){}
   try{rows.clear();throw new AssertionError("mutable list");}catch(UnsupportedOperationException expected){}
   item.use(client,p,InteractionHand.MAIN_HAND);check(rows.size()==1,"snapshot changed after return");
  } else throw new AssertionError("unknown mode");
  System.out.print("CLIENT_TRACE_FIXTURE_PASS_NOT_GAMEPLAY");
 }
}'''


@pytest.fixture(scope='module')
def java_trace(tmp_path_factory):
    if not HELPER.is_file():pytest.skip('Missing helper is asserted separately')
    jdk=Path(os.environ.get('JAVA_HOME',str(REPO.parent/'provider-acceptance/jdk-17.0.20.1+1')))
    if not (jdk/'bin/javac').is_file():pytest.skip('Explicit Java17 JDK required')
    folder=tmp_path_factory.mktemp('staff-client-trace');sources=[]
    for name,body in STUBS.items():
        p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body);sources.append(p)
    target=folder/'org/kneekura/staff';target.mkdir(parents=True)
    generated,_,_=api().client_trace_sources(SOURCE.read_bytes())
    (target/'CelestialStaffItem.java').write_bytes(generated)
    (target/'TraceAssertions.java').write_text(HARNESS)
    sources += [target/'CelestialStaffItem.java',target/'TraceAssertions.java',HELPER,HERE/'java/org/kneekura/staff/StaffUsePolicy.java']
    result=subprocess.run([str(jdk/'bin/javac'),'--release','17','-d',str(folder),*map(str,sources)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    def run(mode):
        result=subprocess.run([str(jdk/'bin/java'),'-cp',str(folder),'org.kneekura.staff.TraceAssertions',mode],capture_output=True,text=True,timeout=10)
        assert result.returncode==0,result.stdout+result.stderr
        assert result.stdout=='CLIENT_TRACE_FIXTURE_PASS_NOT_GAMEPLAY'
    run.classes=folder;run.jdk=jdk
    return run


@pytest.mark.parametrize('mode',['stable','restore-known-sites','unknown-site','closed-attempt','foreign-attempt','server','mutate-effect','mutate-duration','mutate-cooldown','mutate-health','mutate-stack','mutate-damage','mutate-item','before-failure','after-failure','probe-failure-does-not-change-return','original-exception','bound','foreign-thread','cross-thread-close','duplicate-close','immutable'])
def test_actual_java_trace_and_original_hook(java_trace,mode):java_trace(mode)


def test_build_trace_provenance_is_verified_against_generated_bytes(tmp_path):
    module=api();assert hasattr(module,'validate_client_trace_sources'), 'Build trace provenance check missing'
    plain=mdk(tmp_path/'plain');module.configure(plain);assert module.validate_client_trace_sources(plain) is None
    root=mdk(tmp_path/'traced');result=module.configure(root,client_trace=True)
    assert module.validate_client_trace_sources(root)==result['client_trace']
    path=root/'src/main/java/org/kneekura/staff/CelestialStaffItem.java';original=path.read_bytes();path.write_bytes(original+b'\n')
    with pytest.raises(ContractError,match='trace|Trace'):module.validate_client_trace_sources(root)
    path.write_bytes(original)
    metadata=root/'src/main/resources/META-INF/kneekura-client-trace.json';metadata.unlink()
    with pytest.raises(ContractError,match='trace|Trace'):module.validate_client_trace_sources(root)


@pytest.mark.parametrize('fault',['helper','metadata','helper_missing','metadata_symlink'])
def test_build_trace_provenance_rejects_drift_and_missing_sources(tmp_path,fault):
    module=api();assert hasattr(module,'validate_client_trace_sources'), 'Build trace provenance check missing'
    root=mdk(tmp_path/'traced');module.configure(root,client_trace=True)
    helper=root/'src/main/java/org/kneekura/staff/ClientUseTrace.java';metadata=root/'src/main/resources/META-INF/kneekura-client-trace.json'
    if fault=='helper':helper.write_bytes(helper.read_bytes()+b'\n')
    elif fault=='helper_missing':helper.unlink()
    elif fault=='metadata':
        obj=json.loads(metadata.read_text());obj['original_source_sha256']='a'*64;metadata.write_text(json.dumps(obj))
    else:
        alternate=tmp_path/'metadata-copy';metadata.rename(alternate);metadata.symlink_to(alternate)
    with pytest.raises(ContractError,match='trace|Trace'):module.validate_client_trace_sources(root)


def test_trace_cli_requires_fresh_configuration_without_writes(tmp_path):
    root=mdk(tmp_path/'mdk');before=snapshot(root)
    result=subprocess.run([__import__('sys').executable,str(HERE/'pilot.py'),'--workspace',str(root),'--client-trace'],
                          env=dict(os.environ,PYTHONPATH=str(REPO/'src')),capture_output=True,text=True,timeout=10)
    assert result.returncode!=0 and '--client-trace requires fresh --configure' in result.stderr
    assert snapshot(root)==before


def test_generated_trace_compiles_against_cached_forge_without_launch(tmp_path):
    """Optional real API compile; cache inputs only, never Gradle/network/game execution."""
    classpath=Path(os.environ.get('STAFF_FORGE_CLASSPATH_FILE',str(REPO.parent/'staff-client-acceptance/mdk/build/classpath/runClient_minecraftClasspath.txt')))
    jdk=Path(os.environ.get('JAVA_HOME',str(REPO.parent/'provider-acceptance/jdk-17.0.20.1+1')))
    if not classpath.is_file() or not (jdk/'bin/javac').is_file():pytest.skip('Explicit cached Forge classpath and Java17 JDK required')
    entries=[Path(x) for x in classpath.read_text().splitlines() if x.strip()]
    if not entries or not all(p.is_file() or p.is_dir() for p in entries):pytest.skip('Cached Forge classpath is incomplete')
    generated,_,_=api().client_trace_sources(SOURCE.read_bytes())
    target=tmp_path/'org/kneekura/staff/CelestialStaffItem.java';target.parent.mkdir(parents=True);target.write_bytes(generated)
    result=subprocess.run([str(jdk/'bin/javac'),'--release','17','-proc:none','-cp',os.pathsep.join(map(str,entries)),
                           '-d',str(tmp_path),str(target),str(HELPER),str(HERE/'java/org/kneekura/staff/StaffUsePolicy.java')],
                          capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    assert (tmp_path/'org/kneekura/staff/ClientUseTrace.class').is_file()
    assert (tmp_path/'org/kneekura/staff/ClientUseTrace$Scope.class').is_file()


def test_actual_hook_counts_verified_write_sites_even_when_client_state_is_restored(java_trace,tmp_path):
    """Test-only bad policy reaches both original sites, then hides boundary state changes."""
    generated,_,_=api().client_trace_sources(SOURCE.read_bytes())
    variant=generated.replace(
        b'var decision = StaffUsePolicy.decide(level.isClientSide, player.getCooldowns().isOnCooldown(this));',
        b'var decision = StaffUsePolicy.Decision.APPLY;')
    variant=variant.replace(b'        return InteractionResultHolder.consume(stack);',
        b'        player.effect = null; player.cooldown.active = false; player.cooldown.fraction = 0;\n        return InteractionResultHolder.consume(stack);')
    source=tmp_path/'org/kneekura/staff/CelestialStaffItem.java';source.parent.mkdir(parents=True);source.write_bytes(variant)
    harness=tmp_path/'RestoreControl.java';harness.write_text('''
import java.util.*;import org.kneekura.staff.*;import net.minecraft.world.*;import net.minecraft.world.level.*;import net.minecraft.world.entity.player.*;
public class RestoreControl {
 public static void main(String[] args) {
  CelestialStaffItem item=new CelestialStaffItem();Player player=new Player(item);
  var result=item.use(new Level(true),player,InteractionHand.MAIN_HAND);
  Map<?,?> row=(Map<?,?>)((List<?>)ClientUseTrace.snapshot().get("records")).get(0);
  if(!result.result.equals("consume")||player.effectWrites!=1||player.cooldown.writes!=1)throw new AssertionError("known sites did not execute");
  if(!Boolean.TRUE.equals(row.get("unchanged")))throw new AssertionError("control did not restore boundary state");
  if(((Number)row.get("effect_mutation_attempts")).longValue()!=1||((Number)row.get("cooldown_mutation_attempts")).longValue()!=1)throw new AssertionError("mutate-then-restore escaped instrumentation");
  System.out.print("KNOWN_SITE_MUTATE_RESTORE_DETECTED_NOT_GAMEPLAY");
 }
}''')
    result=subprocess.run([str(java_trace.jdk/'bin/javac'),'--release','17','-cp',str(java_trace.classes),'-d',str(tmp_path),str(source),str(harness)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    result=subprocess.run([str(java_trace.jdk/'bin/java'),'-cp',os.pathsep.join((str(tmp_path),str(java_trace.classes))),'RestoreControl'],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stdout+result.stderr
    assert result.stdout=='KNOWN_SITE_MUTATE_RESTORE_DETECTED_NOT_GAMEPLAY'
