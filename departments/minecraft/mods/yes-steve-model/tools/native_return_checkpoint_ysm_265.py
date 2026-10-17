#!/usr/bin/env python3
"""Fixed seven-part native static checkpoint: metadata, backing, prefixes, local parity; never target execution."""
import argparse,hashlib,json,re,subprocess,sys,time
from pathlib import Path
COHORTS=[('NATIVE-RETURN-FILE-CANDIDATE','native_return_file_candidate'),('NATIVE-RETURN-SLICE','native_return_slice'),('NATIVE-LOAD-FLAG-CHAIN','native_load_flag_chain'),('NATIVE-IMAGE-METADATA','native_image_metadata'),('NATIVE-EXPORT-BACKING','native_export_backing'),('NATIVE-LINUX-PREFIX-FRONTIER','native_linux_prefix_frontier'),('NATIVE-LOAD-PARITY-PROOF','native_load_parity_proof')]
MAP_SHA='dc7abc78b1db9401b89ded2e97e2d8341179ccb62d69aa67698c87d8a7174e30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);a=p.parse_args();root=Path(__file__).resolve().parent.parent;start=time.monotonic();rows=[]
 if sha(root/'OBFUSCATION-MAP-2026-10-05.json')!=MAP_SHA:raise SystemExit('Central map changed')
 for prefix,stem in COHORTS:
  tool=root/'tools'/(stem+'_ysm_265.py');test=root/'tools'/('test_'+stem+'_ysm_265.py');evidence=root/(prefix+'-2026-10-17.json')
  subprocess.run([sys.executable,str(tool),'--jar',a.jar,'--out',str(evidence),'--check'],check=True,capture_output=True,text=True)
  r=subprocess.run([sys.executable,str(test)],check=True,capture_output=True,text=True);n=re.search(r'Ran (\d+) tests?',r.stderr)
  if not n:raise ValueError('No test count')
  rows.append(dict(cohort=prefix,tool_sha256=sha(tool),test_sha256=sha(test),evidence_sha256=sha(evidence),synthetic_tests_passed=int(n.group(1)),recomputed_match=True))
 if sha(root/'OBFUSCATION-MAP-2026-10-05.json')!=MAP_SHA:raise SystemExit('Central map changed')
 r=dict(format='kneekura.ysm-native-return-checkpoint.v1',cohort_manifest=COHORTS,cohorts=rows,synthetic_tests_passed=sum(x['synthetic_tests_passed'] for x in rows),elapsed_seconds=round(time.monotonic()-start,3),target_executed=False,native_emulation_run=False,native_implementations_resolved=False,java_native_bindings_resolved=False,central_mapping_sha256=MAP_SHA,independent_semantic_review='NOT_RUN',whole_project_ci_run=False);Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'cohorts':len(rows),'synthetic_tests':r['synthetic_tests_passed'],'status':'PASS','seconds':r['elapsed_seconds']}))
if __name__=='__main__':main()
