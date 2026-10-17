#!/usr/bin/env python3
"""Decode projectile mixin targets/annotations/refmap without runtime injection."""
import argparse,copy,hashlib,json,zipfile
from pathlib import Path
from mixin_annotations_ysm_265 import annotations,SHA
OWNERS=['com/elfmcys/yesstevemodel/mixin/AbstractArrowEntityMixin','com/elfmcys/yesstevemodel/mixin/client/ArrowEntityAccessor','com/elfmcys/yesstevemodel/mixin/client/FishingHookAccessor','com/elfmcys/yesstevemodel/mixin/client/ThrowableItemProjectileAccessor']
def capture(jar):
 raw=Path(jar).read_bytes()
 if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong artifact')
 with zipfile.ZipFile(jar) as z:
  cfg=json.loads(z.read('yes_steve_model.mixins.json'));ref=json.loads(z.read('yes_steve_model.refmap.json'))
  return {'artifact_sha256':SHA,'classes':[annotations(z.read(o+'.class')) for o in OWNERS],'mixin_config':cfg,'refmap_owner_mappings':{o:ref.get('mappings',{}).get(o) for o in OWNERS},'runtime_injection_verified':False}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ['jar','evidence']:p.add_argument('--'+k,required=True)
 p.add_argument('--capture',action='store_true');p.add_argument('--out');a=p.parse_args();d=capture(a.jar)
 if a.capture:Path(a.evidence).write_text(json.dumps(d,indent=2)+'\n');return
 e=json.loads(Path(a.evidence).read_text());checks=[{'check':'exact-four-mixin-contracts','pass':e==d}];neg=[]
 for name,mut in [('missing-class',lambda x:x['classes'].pop()),('missing-target-annotation',lambda x:x['classes'][0]['annotations'].clear()),('missing-refmap',lambda x:x['refmap_owner_mappings'].clear()),('missing-config',lambda x:x['mixin_config'].clear()),('invented-runtime-injection',lambda x:x.update(runtime_injection_verified=True))]:
  c=copy.deepcopy(e);mut(c);neg.append({'control':name,'rejected':c!=d})
 r={'checks':checks,'negative_controls':neg,'failures':[c for c in checks if not c['pass']],'runtime_executed':False,'independent_semantic_review':'NOT_RUN'};Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(neg),'failures':len(r['failures'])}))
 if r['failures'] or any(not c['rejected'] for c in neg):raise SystemExit(1)
if __name__=='__main__':main()
