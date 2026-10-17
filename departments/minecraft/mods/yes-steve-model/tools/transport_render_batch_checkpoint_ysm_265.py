#!/usr/bin/env python3
"""Fixed connected expression/state/model/render transport batch:13 later cohorts and14 explicit anchors; not all-repository CI."""
import argparse,hashlib,json,subprocess,sys,tempfile,time
from pathlib import Path
COHORTS=[('MAID-COMMON-MODEL-COPY', 'maid_common_model_copy', True), ('MAID-VEHICLE-CALLERS', 'maid_vehicle_callers', False), ('ANIMATION-PACKET-ROUTING', 'animation_packet_routing', True), ('MOLANG-COMMAND-PRODUCER', 'molang_command_producer', True), ('EXECUTE-MOLANG-PRODUCERS', 'execute_molang_producers', False), ('ROULETTE-EXPRESSION-UI', 'roulette_expression_ui', True), ('ROULETTE-SUBMISSION-PRODUCERS', 'roulette_submission_producers', False), ('ROULETTE-FORM-OWNERSHIP', 'roulette_form_ownership', True), ('ROULETTE-SOUND-CONSUMERS', 'roulette_sound_consumers', False), ('PARSER-ENTRY-FLAG-CALLERS', 'parser_entry_flag_callers', False), ('CLIENT-MODEL-CONTAINERS', 'client_model_containers', True), ('COLOR-CHANNEL-CONTRACT', 'color_channel_contract', True), ('COLOR-CHANNEL-CONSUMERS', 'color_channel_consumers', False), ('MODEL-ASSET-HELPERS', 'model_asset_helpers', True), ('CONDITIONAL-ANIMATION-NAMES', 'conditional_animation_names', True), ('JAVA-RENDER-BOUNDARY', 'java_render_boundary', True), ('RENDER-SELECTION', 'render_selection', True), ('VEHICLE-PROJECTILE-RENDER', 'vehicle_projectile_render', True), ('PARSER-BINDING-STORAGE', 'parser_binding_storage', True), ('PARSER-POOL-LIFETIME', 'parser_pool_lifetime', True), ('STRUCT-COPY-CHANGE', 'struct_copy_change', True), ('POOLED-NAME-CHANGE-CODEC', 'pooled_name_change_codec', True), ('ROAMING-STATE-MERGE', 'roaming_state_merge', True), ('TEXTURE-HOLDER-LIFETIME', 'texture_holder_lifetime', True), ('MODEL-READINESS-SCOPE', 'model_readiness_scope', True), ('GUI-PREVIEW-STATE', 'gui_preview_state', True), ('MAID-ENTITY-CONTROL', 'maid_entity_control', True)]
MAP_SHA='dc7abc78b1db9401b89ded2e97e2d8341179ccb62d69aa67698c87d8a7174e30'
KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ['jar','source-root','out']:ap.add_argument('--'+k,required=True)
 a=ap.parse_args();root=Path(__file__).resolve().parent.parent;start=time.monotonic();receipts=[];seen={};overlaps=0;owner_seen={};owner_overlaps=0
 assert digest(root/'OBFUSCATION-MAP-2026-10-05.json')==MAP_SHA,'mapping changed'
 with tempfile.TemporaryDirectory() as td:
  for prefix,tool,source in COHORTS:
   script=root/'tools'/(tool+'_ysm_265.py');evidence=root/(prefix+'-EVIDENCE-2026-10-17.json');out=Path(td)/(prefix+'.json')
   cmd=[sys.executable,str(script),'--jar',str(Path(a.jar).resolve()),'--evidence',str(evidence),'--out',str(out)]
   if source:cmd+=['--source-root',str(Path(a.source_root).resolve())]
   if tool=='extra_binding_catalog':cmd+=['--lookup',str(root/'EXTRA-QUERY-NAME-LOOKUP-2026-10-17.jsonl')]
   run=subprocess.run(cmd,check=True,text=True,capture_output=True);r=json.loads(out.read_text());assert not r.get('failures') and not r.get('negative_failures')
   assert all(c.get('pass') for c in r['checks']);assert all(c.get('rejected') for c in r['negative_controls'])
   e=json.loads(evidence.read_text())
   for key in ['members','writer_methods','caller_methods']:
    for m in e.get(key,[]):
     ident=tuple(m[k] for k in ['owner','name','descriptor']);body={k:m[k] for k in KEYS if k in m}
     canonical=json.dumps(body,sort_keys=True,separators=(',',':'))
     if ident in seen:assert canonical==seen[ident],('overlap mismatch',ident);overlaps+=1
     seen[ident]=canonical
   for row in e.get('owner_declarations',[]):
    owner=row['owner'];canonical=json.dumps(row['declaration'],sort_keys=True,separators=(',',':'))
    if owner in owner_seen:assert canonical==owner_seen[owner],('owner declaration mismatch',owner);owner_overlaps+=1
    owner_seen[owner]=canonical
   receipts.append({'cohort':prefix,'tool_sha256':digest(script),'evidence_sha256':digest(evidence),'rerun_receipt_sha256':digest(out),'checks':len(r['checks']),'negative_controls':len(r['negative_controls']),'status':'PASS'})
 assert digest(root/'OBFUSCATION-MAP-2026-10-05.json')==MAP_SHA
 report={'format':'kneekura.ysm-transport-render-batch-checkpoint.v1','cohort_manifest':COHORTS,'cohorts':receipts,'cohort_count':len(COHORTS),'overlapping_method_snapshots_compared':overlaps,'overlap_conflicts':0,'unique_method_snapshots':len(seen),'unique_owner_declarations':len(owner_seen),'overlapping_owner_declarations_compared':owner_overlaps,'counts_are_semantic_completion':False,'central_mapping_sha256':MAP_SHA,'central_mapping_promoted':False,'independent_semantic_review':'NOT_RUN','target_runtime_executed':False,'whole_project_ci_run':False,'earlier_fixed17_checkpoint_modified':False,'earlier_fixed10_checkpoint_modified':False,'earlier_fixed9_checkpoint_modified':False,'elapsed_seconds':round(time.monotonic()-start,3)}
 Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cohorts':len(COHORTS),'overlap_comparisons':overlaps,'status':'PASS','seconds':report['elapsed_seconds']}))
if __name__=='__main__':main()
