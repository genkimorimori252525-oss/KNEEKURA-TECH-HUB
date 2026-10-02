from verification_helpers import bound_mod_revision
"""Existing provider/Core acceptance on real staff MOD inputs. No launches or canonical writes."""
from pathlib import Path
import json,io,zipfile,hashlib,subprocess,sys,time
from kneekura_tech_hub.minecraft import index,providers,core_bridge
from kneekura_tech_hub.minecraft.storage import Store,Limits,canonical,digest,capture_profile
from kneekura_tech_hub.minecraft.mappings import MappingTable
from kneekura_tech_hub.bundle import preflight_bundle,ingest_bundle,BundleValidationError
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine
import argparse
from datetime import datetime, timezone
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work',type=Path,required=True,help='Fresh local output directory')
parser.add_argument('--repository',type=Path,required=True,help='Requested tech-hub checkout')
parser.add_argument('--staff',type=Path,required=True,help='Existing staff acceptance root containing mdk/ and review-evidence/')
parser.add_argument('--providers',type=Path,required=True,help='Existing pinned provider acceptance root')
args=parser.parse_args()
BASE=args.work.resolve(); REPO=args.repository.resolve(); STAFF=args.staff.resolve(); MDK=STAFF/'mdk'; PREV=args.providers.resolve(); JDK=PREV/'jdk-17.0.20.1+1'; E=BASE/'evidence'
BASE.mkdir(parents=True,exist_ok=False)
(BASE/'run-config.json').write_bytes(canonical({'repository':str(REPO),'staff':str(STAFF),'providers':str(PREV)}))
# Invoke only the mapping-io code already bundled in the exact pinned tool.
converter=Path(__file__).with_name('ConvertMappings.java');(BASE/'ConvertMappings.java').write_bytes(converter.read_bytes())
tool=PREV/'downloads/tiny-remapper-0.11.2-fat.jar'
assert digest(tool.read_bytes())=='0376b17b92f858956e018da672affb5485c18085db681f9547664996e82b6688'
assert digest((PREV/'downloads/vineflower-1.11.1.jar').read_bytes())=='a615d07ddbbcd489369674f40e42df639c32be95410890b38f173d5c1e2ea39c'
assert digest((JDK/'release').read_bytes())=='973f28729da43962dfba2e39b2a27ab736122f3a1bf829e06abfbde2a731c711'
assert digest((JDK/'bin/java').read_bytes())=='f5aed21d3a0b0f4b05d3a3f9fe71263916d5bc0d47b53aa52a3340b90f0b4805'
assert digest((JDK/'bin/javac').read_bytes())=='50d09f424b513525af1f0b05cd948ed7890a8d60fef7f7797e20892705b0067d'
assert digest((JDK/'bin/javap').read_bytes())=='f90ade56cebc2168984c1b0011b5325326953c05b4315074a2a434e4ba12add9'
mc=STAFF/'gradle-home/caches/forge_gradle/minecraft_repo/versions/1.20.1'
conversion_compile=subprocess.run([str(JDK/'bin/javac'),'-cp',str(tool),'-d',str(BASE),str(converter)],capture_output=True,timeout=120)
assert conversion_compile.returncode==0,conversion_compile.stderr.decode(errors='replace')
conversion=subprocess.run([str(JDK/'bin/java'),'-cp',str(BASE)+':'+str(tool),'ConvertMappings',str(mc/'client_mappings.txt'),str(mc/'server_mappings.txt'),str(MDK/'build/createMcpToSrg/output.tsrg'),str(BASE/'official-derived-mojmap-srg.tiny')],capture_output=True,timeout=120)
(BASE/'mapping-conversion.log').write_bytes(conversion.stdout+conversion.stderr)
assert conversion.returncode==0,conversion.stderr.decode(errors='replace')
E.mkdir(exist_ok=False); store=Store(E/'cas'); start=time.monotonic()
def save(name,obj):
 b=obj if isinstance(obj,bytes) else canonical(obj);(E/name).write_bytes(b);h=store.put(b);store.pin(h,'real-mod:'+name);return h
def log(msg): print(msg,flush=True)
def run(args,timeout=180):
 p=subprocess.run([str(x) for x in args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);return {'argv':[str(x) for x in args],'exit_code':p.returncode,'stdout':p.stdout.decode(errors='replace')}
resolved=json.loads((MDK/'build/kneekura/resolved-inputs.json').read_bytes());summary=json.loads((STAFF/'review-evidence/summary.json').read_bytes());assert resolved['source_fingerprint']==summary['source_generation']; assert resolved['minecraft']=='1.20.1' and resolved['loader_version']=='47.4.6'
save('resolved-inputs.json',resolved);save('original-build-summary.json',summary)
prior=Store(STAFF/'review-evidence/cas');jar=BASE/'same-build-packaged-srg.jar';jar.write_bytes(prior.read(summary['jar_sha256']));assert digest(jar.read_bytes())==summary['jar_sha256']
prior_profile=json.loads((STAFF/'review-evidence/profile.json').read_bytes())
mod_revision=bound_mod_revision(prior_profile,resolved['source_fingerprint'])
adapter_revision=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
save('adapter-provenance.json',{'adapter_repository_revision':adapter_revision,'reproducer_sha256':digest(Path(__file__).read_bytes()),'mod_source_revision':mod_revision})
for d in prior_profile['documents']:
 if d['root_id']=='output_roots:0': assert digest((MDK/'build/classes/java/main'/d['path']).read_bytes())==d['content_hash'],d['path']
save('same-build-compiled-class-binding.json',[d for d in prior_profile['documents'] if d['root_id']=='output_roots:0'])
original_inputs=json.loads((STAFF/'review-evidence/inputs.json').read_bytes())
for f in original_inputs: assert digest((MDK/f['path']).read_bytes())==f['sha256'],f
save('original-source-binding.json',original_inputs)
# Deterministic packaging of the exact same-build compiled named classes/resources; no recompilation.
named=BASE/'same-build-mojmap.jar'; inventory=[]
with zipfile.ZipFile(named,'w',zipfile.ZIP_DEFLATED) as out:
 for root in [MDK/'build/classes/java/main',MDK/'build/resources/main']:
  for path in sorted(root.rglob('*')):
   if not path.is_file():continue
   rel=path.relative_to(root).as_posix();b=path.read_bytes();info=zipfile.ZipInfo(rel,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;out.writestr(info,b);inventory.append({'path':str(path),'jar_entry':rel,'sha256':digest(b)})
save('named-input-inventory.json',inventory)
# Pin source-issued official mapping bytes against Mojang's captured version manifest.
mc=STAFF/'gradle-home/caches/forge_gradle/minecraft_repo/versions/1.20.1';meta=json.loads((MDK/'build/downloadMCMeta/version.json').read_bytes());maps=[]
for side in ('client','server'):
 path=mc/(side+'_mappings.txt');b=path.read_bytes();entry=meta['downloads'][side+'_mappings'];assert len(b)==entry['size'] and hashlib.sha1(b).hexdigest()==entry['sha1'];maps.append({'path':str(path),'sha256':digest(b),'verified_mojang_metadata':entry});save(side+'-mapping-original.txt',b)
for path in [MDK/'build/createMcpToSrg/output.tsrg',BASE/'official-derived-mojmap-srg.tiny',BASE/'ConvertMappings.java',BASE/'mapping-conversion.log']:
 maps.append({'path':str(path),'sha256':digest(path.read_bytes())});save(path.parent.name+'-'+path.name,path.read_bytes())
mapping=(BASE/'official-derived-mojmap-srg.tiny').read_bytes();mapping_hash=store.put(mapping);table=MappingTable.parse(mapping.decode(),'tiny');assert table.namespaces==['mojmap','srg']
use_desc='(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/InteractionResultHolder;'
lookup=table.resolve('mojmap','srg','net/minecraft/world/item/Item','use',use_desc);assert lookup['results'][0]['name']=='m_7203_';save('official-item-use-lookup.json',lookup)
save('mapping-provenance.json',{'inputs':maps,'conversion':'Already bundled mapping-io merges official client/server ProGuard descriptors and exact ForgeGradle createMcpToSrg TSRG2 names, then writes Tiny v2; no names invented. Converted file is derived, not an upstream-distributed Tiny file.'})
roots=[]
def root(id,path,kind,role,namespace='mojmap',scope='research',stage='same_build'):
 return {'id':id,'path':str(path),'kind':kind,'scope':scope,'role':role,'namespace':namespace,'stage':stage,'classloader':'forge_userdev','track':'ANCHOR'}
roots.append(root('staff-mojmap',named,'jar','binary'))
roots.append(root('staff-packaged-srg',jar,'jar','binary','srg',stage='forge_reobfJar'))
roots.append(root('staff-source',MDK/'src/main/java','directory','source'))
roots.append(root('staff-resources',MDK/'src/main/resources','directory','resource'))
libs=[x for x in resolved['artifacts'] if x['scope']=='compile'];lib_ids=[]
for i,a in enumerate(libs):
 p=Path(a['path']);assert digest(p.read_bytes())==a['sha256'];rid='compile:'+str(i);lib_ids.append(rid);r=root(rid,p,'jar','dependency',a['namespace'],'compile',a['stage']);r.update(resolved_sha256=a['sha256'],coordinate=a['coordinate']);roots.append(r)
manifest={'schema_version':1,'minecraft':'1.20.1','loader':'forge','loader_version':'47.4.6','java_major':17,'namespace':'mojmap','physical_side':'server','logical_side':'server','track':'ANCHOR','workspace_revision':mod_revision,'dirty_hash':resolved['source_fingerprint'],'toolchain':resolved['toolchain'],'roots':roots,'acceptance_scope':'REAL_LOCAL_STAFF_MOD_STATIC_PROVIDERS_AND_CORE_REVIEW_STAGING','source_generation':resolved['source_fingerprint']}
save('manifest.json',manifest);log('capture: 2 real MOD JAR namespaces + sources/resources + all 101 exact ordered compile dependencies')
p=capture_profile(manifest,BASE,store,limits=Limits(max_files=100000));save('input-profile.json',p)
for rid in lib_ids: assert next(r for r in p['roots'] if r['id']==rid)['artifact_hash'],rid
idx=index.prepare_index(p,store,javap=str(JDK/'bin/javap'),max_classes=14);save('input-index.json',idx);identifier=idx['index_snapshot_id'];log('index: prepared 14 actual staff classes; dependency bytecode intentionally remains unprepared')
save('input-staff-use.json',index.find_symbols(store,identifier,'org/kneekura/staff/CelestialStaffItem',member='use',descriptor=use_desc,namespace='mojmap',track='ANCHOR'))
results={}
for op,tool,version in [('decompile','vineflower-1.11.1.jar','1.11.1'),('remap','tiny-remapper-0.11.2-fat.jar','0.11.2')]:
 cfg={'allow_execute':True,'java':str(JDK/'bin/java'),'jar':str(PREV/'downloads'/tool),'jar_sha256':digest((PREV/'downloads'/tool).read_bytes()),'version':version,'memory_mib':1024,'threads':2,'timeout_seconds':180,'classpath_root_ids':lib_ids};save(op+'-config.json',cfg)
 kwargs={} if op=='decompile' else {'mapping_hash':mapping_hash,'from_namespace':'mojmap','to_namespace':'srg'}
 log(op+': existing adapter on actual MOD input');r=providers.prepare_transform(store,identifier,'staff-mojmap',op,cfg,**kwargs);save(op+'-result.json',r);results[op]=r
 if r['status']!='OK':
  if r.get('log_hash'):save(op+'-stdout.txt',store.read(r['log_hash']))
  raise AssertionError(r)
 receipt=store.json(r['receipt_hash']);save(op+'-receipt.json',receipt);save(op+'-stdout.txt',store.read(receipt['log_hash']));archive=store.read(receipt['output_artifact_hash']);save(op+'-output.jar',archive)
 assert receipt['classpath_artifact_hashes']==[a['sha256'] for a in libs]
 repeat=providers.prepare_transform(store,identifier,'staff-mojmap',op,cfg,**kwargs);save(op+'-cache-repeat.json',repeat);assert repeat['cache_hit'] and repeat['receipt_hash']==r['receipt_hash'];log(op+': OK, pinned receipt and exact-input cache reuse')
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  if op=='decompile':
   text=z.read('org/kneekura/staff/CelestialStaffItem.java').decode(); assert 'MobEffects.GLOWING' in text and 'use(' in text
   extracted=BASE/'decompiled';extracted.mkdir()
   for n in z.namelist():
    if n.endswith('.java'):
     dest=extracted/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(n))
   out=BASE/'recompiled';out.mkdir();recompile=run([JDK/'bin/javac','--release','17','-classpath',':'.join(a['path'] for a in libs),'-d',out,*sorted(extracted.rglob('*.java'))]);save('decompile-recompile.json',recompile);log('decompile recompile exit '+str(recompile['exit_code']))
   assert recompile['exit_code']==0,recompile
  else:
   dest=BASE/'remapped';dest.mkdir()
   for n in z.namelist():
    if n.endswith('.class'):
     path=dest/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(n))
   check=run([JDK/'bin/javap','-p','-s','-c','-classpath',dest,'org.kneekura.staff.CelestialStaffItem']);save('remapped-staff-bytecode.json',check);assert check['exit_code']==0 and ' m_7203_(' in check['stdout'];assert 'MobEffects.f_19619_' in check['stdout'];assert 'getCooldowns' not in check['stdout'];log('remap: real inherited Item.use and referenced Minecraft symbols resolved to SRG')
# Existing caller on actual MOD source, never fabricated canonical identities or validation.
source_docs=[d for d in p['documents'] if d['root_id']=='staff-source'];selection=[d['document_id'] for d in source_docs if d['path'].endswith(('CelestialStaffItem.java','StaffUsePolicy.java'))];assert len(selection)==2
assert 'mod_license=All Rights Reserved' in (MDK/'gradle.properties').read_text();license={'staff-source':{'state':'KNOWN','declared_expression':'All Rights Reserved','handling_policy':'Local user-requested MOD analysis only; declaration observed in exact pilot gradle.properties. No redistribution, human license approval, or canonical ingestion inferred.'}};save('reviewed-source-license.json',license)
stage=core_bridge.stage_bundle(store,identifier,selection,summary='Static source observation on the same-build Forge 1.20.1/47.4.6 staff MOD: CelestialStaffItem.use branches on client side and cooldown, applies self GLOWING for StaffUsePolicy.GLOW_TICKS=60, then COOLDOWN_TICKS=100. Derived bytecode was inspected separately. This observation does not assert real right-click, client rendering, or runtime compatibility.',actor={'actor_type':'ai','actor_id':'mod-ai-real-input-acceptance'},captured_at=datetime.now(timezone.utc).isoformat(),source_licenses=license);save('core-stage-result.json',stage);bundle=store.json(stage['bundle_hash']);save('core-review-bundle.json',bundle);assert len(preflight_bundle(bundle))==5
assert {r['record_type'] for r in bundle['records']}=={'source','source_snapshot','evidence','staged_observation'};assert next(r for r in bundle['records'] if r['record_type']=='staged_observation')['status']=='NEW'
repo=MemoryRepository()
try:ingest_bundle(CurationEngine(repo),bundle,actor={'actor_type':'ai','actor_id':'mod-ai-real-input-acceptance'})
except BundleValidationError as e:save('core-ai-ingestion-rejected.json',{'error_type':type(e).__name__,'reason':str(e),'repository_records':len(repo.list())})
else:raise AssertionError('AI ingestion unexpectedly accepted')
assert not repo.list()
context=core_bridge.context(store,identifier,'GLOW_TICKS',scope='research',namespace='mojmap',track='ANCHOR');save('core-context-real-source.json',context);assert context['research']['results'] and context['governed']['status']=='NOT_REQUESTED' and context['canonical_writes']==0
for f in original_inputs: assert digest((MDK/f['path']).read_bytes())==f['sha256'],f
summary={'schema_version':1,'acceptance_scope':'REAL_LOCAL_STAFF_MOD_STATIC_ACCEPTANCE','same_build_source_generation':resolved['source_fingerprint'],'original_packaged_mod_sha256':digest(jar.read_bytes()),'named_mod_input_sha256':digest(named.read_bytes()),'mapping_sha256':mapping_hash,'compile_classpath_count':len(libs),'mapping_origin':'OFFICIAL_MOJANG_PLUS_EXACT_FORGEGRADLE_DERIVATION_CONVERTED_WITH_BUNDLED_MAPPING_IO','results':results,'core_stage':stage,'core_ai_ingestion':'REJECTED_NO_WRITES','core_deployed_backend':'NOT_RUN','canonical_human_review':'NOT_RUN','runtime_launches':0,'upstream_twilight_connector_acceptance':'NOT_RUN','index_coverage':'PARTIAL_DEPENDENCY_BYTECODE_UNPREPARED_AND_EXISTING_MULTI_RELEASE_CAPTURE_LIMITATIONS','providers_source_sha256':digest(Path(providers.__file__).read_bytes()),'core_bridge_source_sha256':digest(Path(core_bridge.__file__).read_bytes()),'elapsed_seconds':time.monotonic()-start}
save('summary.json',summary);log(json.dumps(summary,indent=2))
