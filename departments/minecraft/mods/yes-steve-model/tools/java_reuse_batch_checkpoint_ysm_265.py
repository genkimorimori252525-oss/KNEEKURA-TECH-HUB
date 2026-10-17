#!/usr/bin/env python3
"""Fixed substantial Java reuse batch: deduplicated model/geometry/parser/maid/input cohorts and their explicit anchors; not all-repository CI."""
import argparse,hashlib,json,subprocess,sys,tempfile,time
from pathlib import Path
COHORTS=[('ANIMATION-DATA-OWNERSHIP', 'animation_data_ownership', True), ('PARTICLE-KEYFRAME-READERS', 'particle_keyframe_readers', False), ('MODEL-ASSET-HELPERS', 'model_asset_helpers', True), ('CONDITIONAL-ANIMATION-NAMES', 'conditional_animation_names', True), ('MOLANG-EVENT-WRAPPER', 'molang_event_wrapper', True), ('GEOMETRY-AUTHORED-DEFAULTS', 'geometry_authored_defaults', True), ('GEOMETRY-DEFAULT-CALLERS', 'geometry_default_callers', False), ('TLM-LOCATION-ADAPTER', 'tlm_location_adapter', True), ('LOCATOR-MATRIX-PREPARATION', 'locator_matrix_preparation', True), ('TYPED-FUNCTION-GUARDS', 'typed_function_guards', True), ('DEBUG-MESSAGE-DELIVERY', 'debug_message_delivery', True), ('EQUIPMENT-EFFECT-QUERY', 'equipment_effect_query', True), ('INSTRUCTION-DEBUG-EVALUATION', 'instruction_debug_evaluation', True), ('LEXER-TOKEN-DIAGNOSTICS', 'lexer_token_diagnostics', True), ('PARSER-BINDING-STORAGE', 'parser_binding_storage', True), ('PARSER-POOL-LIFETIME', 'parser_pool_lifetime', True), ('PARSER-ENTRY-OWNERSHIP', 'parser_entry_ownership', True), ('MODEL-INPUT-CARRIERS', 'model_input_carriers', True), ('MODEL-LANGUAGE-FALLBACK', 'model_language_fallback', True), ('ORDERED-SEGMENT-TRANSITION', 'ordered_segment_transition', True), ('NATIVE-TEXTURE-JAVA-BOUNDARY', 'native_texture_java_boundary', True), ('TEXTURE-HOLDER-LIFETIME', 'texture_holder_lifetime', True), ('SHADER-BUFFER-ADAPTERS', 'shader_buffer_adapters', True), ('MAID-ENTITY-CONTROL', 'maid_entity_control', True), ('MAID-CONTROLLER-REGISTRATION', 'maid_controller_registration', True), ('MAID-QUERY-ADAPTER', 'maid_query_adapter', True), ('PLAYER-CONTROLLER-ASSEMBLY', 'player_controller_assembly', True), ('MAID-RENDER-CAPABILITY', 'maid_render_capability', True), ('RENDER-SELECTION', 'render_selection', True), ('CLIENT-VIEW-MOVEMENT', 'client_view_movement', True), ('FIRST-PERSON-RENDER-REGISTRY', 'first_person_render_registry', True), ('ARM-REPLACEMENT-EVENTS', 'arm_replacement_events', True), ('EXTRA-ANIMATION-KEY-ROUTING', 'extra_animation_key_routing', True), ('INPUT-SYNC-DEFER', 'input_sync_defer', True), ('CLIENT-COMPAT-INITIALIZATION', 'client_compat_initialization', True)]
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
 report={'format':'kneekura.ysm-java-reuse-batch-checkpoint.v1','cohort_manifest':COHORTS,'cohorts':receipts,'cohort_count':len(COHORTS),'overlapping_method_snapshots_compared':overlaps,'overlap_conflicts':0,'unique_method_snapshots':len(seen),'unique_owner_declarations':len(owner_seen),'overlapping_owner_declarations_compared':owner_overlaps,'counts_are_semantic_completion':False,'central_mapping_sha256':MAP_SHA,'central_mapping_promoted':False,'independent_semantic_review':'NOT_RUN','target_runtime_executed':False,'whole_project_ci_run':False,'earlier_fixed17_checkpoint_modified':False,'earlier_fixed10_checkpoint_modified':False,'earlier_fixed9_checkpoint_modified':False,'elapsed_seconds':round(time.monotonic()-start,3)}
 Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cohorts':len(COHORTS),'overlap_comparisons':overlaps,'status':'PASS','seconds':report['elapsed_seconds']}))
if __name__=='__main__':main()
