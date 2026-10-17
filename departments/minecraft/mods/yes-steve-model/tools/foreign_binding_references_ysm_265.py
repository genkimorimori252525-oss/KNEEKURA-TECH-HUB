#!/usr/bin/env python3
"""Fixed-JAR CONSTANT_Class references to the foreign binding pair, not runtime reachability."""
import argparse,copy,hashlib,json,zipfile
from pathlib import Path
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
OUTER='com/elfmcys/yesstevemodel/oO0o00o0o0oOo000OoO000oO'
TARGETS={OUTER,OUTER+'$Oo0Oo0o00O00Oo0OOoOOoooo'}
def capture(jar):
 raw=Path(jar).read_bytes()
 if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong artifact')
 refs=[];count=0
 with zipfile.ZipFile(jar) as z:
  for n in sorted(z.namelist()):
   if not n.endswith('.class'):continue
   count+=1;c=parse_class(z.read(n));hits=sorted(TARGETS.intersection(c['class_refs']))
   if hits:refs.append({'owner':c['name'],'target_class_refs':hits})
 return {'artifact_sha256':SHA,'class_count':count,'targets':sorted(TARGETS),'constant_class_referencers':refs,'external_pair_referencers':[r for r in refs if r['owner'] not in TARGETS],'reflection_strings_native_external_mods_scanned':False,'runtime_executed':False}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ['jar','evidence']:p.add_argument('--'+k,required=True)
 p.add_argument('--capture',action='store_true');p.add_argument('--out');a=p.parse_args();actual=capture(a.jar)
 if a.capture:Path(a.evidence).write_text(json.dumps(actual,indent=2)+'\n');return
 e=json.loads(Path(a.evidence).read_text());checks=[{'check':'complete-fixed-constant-class-scan','pass':e==actual},{'check':'955-classes','pass':actual['class_count']==955}];neg=[]
 for name,mut in [('missing-pair-reference',lambda x:x['constant_class_referencers'].pop()),('invented-external-reference',lambda x:x['external_pair_referencers'].append({'owner':'invented'})),('wrong-target',lambda x:x['targets'].pop()),('invented-native-closure',lambda x:x.update(reflection_strings_native_external_mods_scanned=True))]:
  c=copy.deepcopy(e);mut(c);neg.append({'control':name,'rejected':c!=actual})
 r={'checks':checks,'negative_controls':neg,'failures':[c for c in checks if not c['pass']],'independent_semantic_review':'NOT_RUN','runtime_executed':False};Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'referencers':len(actual['constant_class_referencers']),'external_pair_referencers':len(actual['external_pair_referencers']),'checks':len(checks),'negative_controls':len(neg),'failures':len(r['failures'])}))
 if r['failures'] or any(not c['rejected'] for c in neg):raise SystemExit(1)
if __name__=='__main__':main()
