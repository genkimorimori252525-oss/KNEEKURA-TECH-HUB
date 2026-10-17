#!/usr/bin/env python3
"""Batch rerun the October17 Java continuation cohorts, not whole-repo CI."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
COHORTS=[('BEDROCK-CONTROLLER','bedrock_controller',True),('ANIMATABLE-FRAME','animatable_frame',True),('ASYNC-ANIMATION','async_animation',True),('ANIMATABLE-OVERRIDE','animatable_override',False),('WORLD-RENDER-HOOK','mixin_annotations',False),('MODEL-READINESS-SCOPE','model_readiness_scope',True),('TEXTURE-HOLDER-LIFETIME','texture_holder_lifetime',True),('RENDER-SELECTION','render_selection',True),('JAVA-RENDER-BOUNDARY','java_render_boundary',True),('STATE-TRACKER-INPUT','state_tracker_input',True),('MOVEMENT-QUERY','movement_query',True),('VARIABLE-CONVERSION','variable_conversion',True),('VARIABLE-AST-RETURN','variable_ast_return',True),('PARSER-BINDING-STORAGE','parser_binding_storage',True),('RUNTIME-STORAGE-FRAMES','runtime_storage_frames',True),('STORAGE-CALLERS','storage_callers',False),('FUNCTION-LOOP-ORDER','function_loop_order',True)]
MAP_SHA='dc7abc78b1db9401b89ded2e97e2d8341179ccb62d69aa67698c87d8a7174e30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--jar',required=True);ap.add_argument('--source-root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();base=Path(__file__).resolve().parent.parent;rows=[];seen={};conflicts=[];captured=0
 with tempfile.TemporaryDirectory(prefix='ysm-pipeline-') as td:
  for prefix,tool,source in COHORTS:
   evidence=base/(prefix+'-EVIDENCE-2026-10-17.json');script=base/'tools'/(tool+'_ysm_265.py');out=Path(td)/(tool+'.json');cmd=[sys.executable,str(script),'--jar',a.jar,'--evidence',str(evidence),'--out',str(out)]
   if source:cmd+=['--source-root',a.source_root]
   proc=subprocess.run(cmd,capture_output=True,text=True);r=json.loads(out.read_text()) if out.exists() else {};checks=r.get('checks',[]);neg=r.get('negative_controls',[]);ok=proc.returncode==0 and bool(checks) and all(c.get('pass') for c in checks) and all(n.get('rejected') for n in neg)
   rows.append({'cohort':prefix,'tool':script.name,'tool_sha256':sha(script),'evidence_sha256':sha(evidence),'checks':len(checks),'negative_controls':len(neg),'pass':ok,'independent_semantic_review':'NOT_RUN',**({'error':proc.stderr[-2000:]} if not ok else {})})
   e=json.loads(evidence.read_text());members=e.get('members',[])+e.get('caller_methods',[])+[m for d in e.get('descendants',[]) for m in d.get('methods',[])]
   for m in members:
    captured+=1;k=tuple(m[f] for f in ['owner','name','descriptor']);body={f:m.get(f) for f in ['access','code_sha256','instructions','supplemental_full_operand_records','exception_handlers']}
    if k in seen and seen[k]!=body:conflicts.append(list(k))
    seen[k]=body
 mapfile=base/'OBFUSCATION-MAP-2026-10-05.json';mapping=json.loads(mapfile.read_text());map_ok=sha(mapfile)==MAP_SHA and len(mapping['mappings'])==669
 result={'checkpoint':'2026-10-17-JAVA-CONTINUATION','artifact_sha256':sha(Path(a.jar)),'cohorts':rows,'captured_method_records_including_overlap':captured,'unique_captured_method_declarations':len(seen),'owners_with_captured_methods':len({k[0] for k in seen}),'overlap_conflicts':conflicts,'central_map_sha256':sha(mapfile),'central_map_669_unchanged':map_ok,'runtime_executed':False,'whole_repo_ci_run':False,'semantic_completion_percentage':None,'counts_are_evidence_inventory_not_semantic_completion':True,'pass':all(r['pass'] for r in rows) and not conflicts and map_ok}
 Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['pass','unique_captured_method_declarations','owners_with_captured_methods','central_map_669_unchanged']}))
 if not result['pass']:raise SystemExit(1)
if __name__=='__main__':main()
