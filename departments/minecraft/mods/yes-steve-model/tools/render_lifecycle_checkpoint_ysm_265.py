#!/usr/bin/env python3
"""Fixed render-lifecycle checkpoint: six new cohorts plus two prior overlap anchors; not whole-project CI."""
import argparse,hashlib,json,subprocess,sys,tempfile,time
from pathlib import Path
COHORTS=[('VEHICLE-PROJECTILE-RENDER', 'vehicle_projectile_render', True), ('DISPATCHER-RENDER-REPLACEMENT', 'dispatcher_render_replacement', True), ('PLAYER-REPLACEMENT-VIEW-GATES', 'player_replacement_view_gates', True), ('SHADER-BUFFER-ADAPTERS', 'shader_buffer_adapters', True), ('GUI-PREVIEW-STATE', 'gui_preview_state', True), ('GUI-PREVIEW-CALLERS', 'gui_preview_callers', False), ('VIEW-TEXTURE-INPUT', 'view_texture_input', True), ('EXTRA-PREVIEW-CONTROLLERS', 'extra_preview_controllers', True)]
MAP_SHA='dc7abc78b1db9401b89ded2e97e2d8341179ccb62d69aa67698c87d8a7174e30'
KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ['jar','source-root','out']:ap.add_argument('--'+k,required=True)
 a=ap.parse_args();root=Path(__file__).resolve().parent.parent;start=time.monotonic();receipts=[];seen={};overlaps=0
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
     if ident in seen:assert body==seen[ident],('overlap mismatch',ident);overlaps+=1
     seen[ident]=body
   receipts.append({'cohort':prefix,'tool_sha256':digest(script),'evidence_sha256':digest(evidence),'rerun_receipt_sha256':digest(out),'checks':len(r['checks']),'negative_controls':len(r['negative_controls']),'status':'PASS'})
 assert digest(root/'OBFUSCATION-MAP-2026-10-05.json')==MAP_SHA
 report={'format':'kneekura.ysm-render-lifecycle-checkpoint.v1','cohort_manifest':COHORTS,'cohorts':receipts,'cohort_count':len(COHORTS),'overlapping_method_snapshots_compared':overlaps,'overlap_conflicts':0,'central_mapping_sha256':MAP_SHA,'central_mapping_promoted':False,'independent_semantic_review':'NOT_RUN','target_runtime_executed':False,'whole_project_ci_run':False,'earlier_fixed17_checkpoint_modified':False,'earlier_fixed10_checkpoint_modified':False,'earlier_fixed9_checkpoint_modified':False,'earlier_fixed14_checkpoint_modified':False,'attachment_fixed9_checkpoint_modified':False,'elapsed_seconds':round(time.monotonic()-start,3)}
 Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cohorts':len(COHORTS),'overlap_comparisons':overlaps,'status':'PASS','seconds':report['elapsed_seconds']}))
if __name__=='__main__':main()
