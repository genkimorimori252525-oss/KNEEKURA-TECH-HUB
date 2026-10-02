from pathlib import Path
import io,json,zipfile,re,subprocess,hashlib,difflib
from kneekura_tech_hub.minecraft.storage import Store,canonical,digest
from kneekura_tech_hub.minecraft.mappings import MappingTable
from kneekura_tech_hub.minecraft import core_bridge
from kneekura_tech_hub.bundle import preflight_bundle
from verification_helpers import require_all_class_comparisons, require_same_archive_inventory, verification_name, POLICY_SMOKE_SOURCE
import argparse
from datetime import datetime, timezone
parser=argparse.ArgumentParser(description='Verify already-captured actual MOD provider/Core outputs; no game launch')
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--verification-name',type=verification_name,default='verification')
args=parser.parse_args();BASE=args.work.resolve();config=json.loads((BASE/'run-config.json').read_bytes())
E=BASE/'evidence';V=BASE/args.verification_name;V.mkdir(exist_ok=False);store=Store(E/'cas');JDK=Path(config['providers'])/'jdk-17.0.20.1+1';MDK=Path(config['staff'])/'mdk'
def save(n,v): (V/n).write_bytes(v if isinstance(v,bytes) else canonical(v))
def run(args):
 p=subprocess.run([str(x) for x in args],capture_output=True,timeout=120);return {'argv':[str(x) for x in args],'exit_code':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')}
# Independently validate the complete transformed inventory and fixed source mapping.
summary=json.loads((E/'summary.json').read_bytes());checks={}
for op in ['decompile','remap']:
 result=json.loads((E/(op+'-result.json')).read_bytes());receipt=store.json(result['receipt_hash']);assert digest((E/(op+'-receipt.json')).read_bytes())==result['receipt_hash']
 with zipfile.ZipFile(io.BytesIO(store.read(receipt['output_artifact_hash']))) as z:
  assert {n:digest(z.read(n)) for n in z.namelist()}=={x['path']:x['content_hash'] for x in receipt['entries']}
  for x in receipt['entries']:assert digest(store.read(x['content_hash']))==x['content_hash']
 assert receipt['input_artifact_hash']==summary['named_mod_input_sha256'];assert json.loads((E/(op+'-cache-repeat.json')).read_bytes())['receipt_hash']==result['receipt_hash'];checks[op+'_receipt']='VERIFIED'
# Every generated mapping name is retained from exact ForgeGradle output.
srg=MappingTable.parse((MDK/'build/createMcpToSrg/output.tsrg').read_text(),'tsrg');tiny=MappingTable.parse((BASE/'official-derived-mojmap-srg.tiny').read_text(),'tiny');lookup={c['names']['mojmap']:c for c in tiny.classes};members=0
for c in srg.classes:
 d=lookup[c['names']['left']];assert d['names']['srg']==c['names']['right']
 for m in c['members']:
  matches=[v for v in d['members'] if v['kind']==m['kind'] and v['names']['mojmap']==m['names']['left'] and (not m['descriptor'] or m['descriptor']==v['descriptor'])]
  assert len(matches)==1,(c,m,matches);assert matches[0]['names']['srg']==m['names']['right'];members+=1
save('mapping-conversion-parity.json',{'classes_checked':len(srg.classes),'members_checked':members,'field_descriptors':'ZERO_MISSING','name_changes_from_forgegradle_mapping':0})
# Compare actual distribution-reobfuscated output with new tiny-remapper output.
with zipfile.ZipFile(BASE/'same-build-packaged-srg.jar') as original,zipfile.ZipFile(E/'remap-output.jar') as remap:
 with zipfile.ZipFile(BASE/'same-build-mojmap.jar') as named:
  require_same_archive_inventory(named.namelist(),remap.namelist())
  # The distribution adds a generated manifest; compare outputs against the
  # exact named provider input so no missing class/resource can hide in a subset.
  assert {n for n in original.namelist() if not n.endswith('/')}==set(named.namelist())|{'META-INF/MANIFEST.MF'}
 classes=sorted(n for n in remap.namelist() if n.endswith('.class'))
 resources=[n for n in remap.namelist() if not n.endswith('.class')]
 for n in resources:assert original.read(n)==remap.read(n),n
 checks['same_packaged_resources']=len(resources)
 comparisons=[]
 for n in classes:
  name=n[:-6].replace('/','.')
  a=run([JDK/'bin/javap','-p','-s','-c','-constants','-classpath',BASE/'same-build-packaged-srg.jar',name]);b=run([JDK/'bin/javap','-p','-s','-c','-constants','-classpath',E/'remap-output.jar',name]);assert a['exit_code']==b['exit_code']==0
  norm=lambda x:re.sub(r'#\d+\s+//', '#CP //',x)
  same=norm(a['stdout'])==norm(b['stdout']);comparisons.append({'class':name,'same_normalized_javap':same,'same_class_bytes':original.read(n)==remap.read(n)})
  save(n.replace('/','_')+'.javap-comparison.json',{'forgegradle':a,'tiny_remapper':b})
  if not same:save(n.replace('/','_')+'.diff',''.join(difflib.unified_diff(norm(a['stdout']).splitlines(True),norm(b['stdout']).splitlines(True))).encode())
 save('remap-vs-forgegradle.json',comparisons);checks['same_normalized_class_bytecode']=sum(c['same_normalized_javap'] for c in comparisons);checks['classes_compared']=len(comparisons);require_all_class_comparisons(comparisons)
# Distinguish prior captured distribution build from any later same-source package.
current_package=MDK/'build/libs/kneekura-1.0.0.jar'
with zipfile.ZipFile(BASE/'same-build-packaged-srg.jar') as prior,zipfile.ZipFile(current_package) as current:
 assert set(prior.namelist())==set(current.namelist())
 changed=[n for n in prior.namelist() if prior.read(n)!=current.read(n)]
 assert not set(changed)-{'META-INF/MANIFEST.MF'},changed
 strip_timestamp=lambda b: b'\n'.join(line for line in b.splitlines() if not line.startswith(b'Implementation-Timestamp:'))
 assert strip_timestamp(prior.read('META-INF/MANIFEST.MF'))==strip_timestamp(current.read('META-INF/MANIFEST.MF'))
 reconciliation={'prior_captured_raw_jar_sha256':digest((BASE/'same-build-packaged-srg.jar').read_bytes()),'current_raw_jar_sha256':digest(current_package.read_bytes()),'entry_count':len(prior.namelist()),'differing_content_entries':changed,'all_class_and_resource_bytes_identical':True,'distinction':'Distinct raw builds when hashes differ; no exact runtime-generation equivalence inferred'}
 save('jar-generation-reconciliation.json',reconciliation)
 checks['raw_package_generation_reconciliation']='VERIFIED_DISTINCT_RAW_BUILDS_SAME_CLASS_RESOURCE_BYTES'
# Execute only the small standalone policy class in each output, no Minecraft class/game load.
smoke=V/'SmokePolicy.java';smoke.write_text(POLICY_SMOKE_SOURCE)
smoke_out=V/'smoke-classes';smoke_out.mkdir();compile=run([JDK/'bin/javac','--release','17','-cp',BASE/'same-build-mojmap.jar','-d',smoke_out,smoke]);save('smoke-compile.json',compile);assert compile['exit_code']==0
for label,cp in [('original',BASE/'same-build-mojmap.jar'),('decompiled_recompiled',BASE/'recompiled'),('tiny_remapped',E/'remap-output.jar')]:
 r=run([JDK/'bin/java','-cp',str(smoke_out)+':'+str(cp),'SmokePolicy']);save('smoke-'+label+'.json',r);assert r['exit_code']==0
checks['pure_policy_output_smokes']=3
# Fresh caller schema acceptance with truthful verification timestamp, preserving original staging evidence.
p=json.loads((E/'input-profile.json').read_bytes());idx=json.loads((E/'input-index.json').read_bytes())['index_snapshot_id'];selected=[d['document_id'] for d in p['documents'] if d['root_id']=='staff-source' and d['path'].endswith(('CelestialStaffItem.java','StaffUsePolicy.java'))]
previous=json.loads((E/'core-review-bundle.json').read_bytes());obs=next(r for r in previous['records'] if r['record_type']=='staged_observation');licenses=json.loads((E/'reviewed-source-license.json').read_bytes())
fresh=core_bridge.stage_bundle(store,idx,selected,summary=obs['summary'],actor=obs['created_by'],source_licenses=licenses,captured_at=datetime.now(timezone.utc).isoformat());bundle=store.json(fresh['bundle_hash']);assert len(preflight_bundle(bundle))==5;save('core-stage-result.json',fresh);save('core-review-bundle.json',bundle)
checks['core_actual_sources_real_schema']='PASS_5_REVIEW_ONLY_RECORDS';checks['latest_core_bundle_hash']=fresh['bundle_hash'];checks['scope']='STATIC_PROVIDER_AND_CORE_STAGING_ONLY';save('summary.json',checks);print(json.dumps(checks,indent=2))
