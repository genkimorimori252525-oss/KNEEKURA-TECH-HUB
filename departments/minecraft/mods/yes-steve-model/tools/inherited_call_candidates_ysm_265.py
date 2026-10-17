#!/usr/bin/env python3
"""Opt-in nominal ancestry candidates for one declared instance method; NOT JVM dispatch resolution."""
import argparse,hashlib,json,zipfile
from collections import deque
from pathlib import Path
from scan_ysm_265 import parse_class
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from validate_member_targets_ysm_265 import SHA,SIZE,validate_targets

def ancestry(owner,target,classes):
    queue=deque([(owner,[owner])]);seen=set();missing=set()
    while queue:
        node,path=queue.popleft()
        if node==target:return path,sorted(missing)
        if node in seen:continue
        seen.add(node)
        declaration=classes.get(node)
        if declaration is None:
            missing.add(node);continue
        parents=([declaration['super']] if declaration.get('super') else [])+declaration.get('interfaces',[])
        for parent in parents:
            if parent not in seen:queue.append((parent,path+[parent]))
    return None,sorted(missing)

def classify(reference,target,classes):
    owner,name,descriptor=target
    if reference.get('name')!=name or reference.get('descriptor')!=descriptor:return None
    symbolic_owner=reference.get('owner')
    if not isinstance(symbolic_owner,str):return None
    if symbolic_owner==owner:
        return dict(category='EXACT_SYMBOLIC_OWNER',ancestry_path=[owner],dispatch_resolved=False)
    path,missing=ancestry(symbolic_owner,owner,classes)
    declarations=[]
    if path:
        for node in path[:-1]:
            for m in classes[node].get('methods',[]):
                if m['name']==name and m['descriptor']==descriptor:
                    declarations.append(dict(owner=node,access=m['access']))
    return dict(category='NOMINAL_DESCENDANT_CANDIDATE' if path else 'SAME_SIGNATURE_NO_PROVEN_ANCESTRY',
                ancestry_path=path,missing_ancestor_declarations=missing,
                same_signature_declarations_on_path=declarations,dispatch_resolved=False)

def validate_instance_target(target,classes):
    methods={(owner,m['name'],m['descriptor']) for owner,c in classes.items() for m in c['methods']}
    validate_targets([target],dict(methods=methods,fields=set()))
    owner,name,descriptor=target
    m=next(m for m in classes[owner]['methods'] if m['name']==name and m['descriptor']==descriptor)
    if name in ('<init>','<clinit>') or m['access'] & (0x0002|0x0008):
        raise ValueError('Only non-private, non-static ordinary instance methods are supported')
    return m

def capture(jar,target):
    raw=Path(jar).read_bytes()
    if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Wrong exact artifact')
    sites=[];handles=[]
    with zipfile.ZipFile(jar) as z:
        names=sorted(n for n in z.namelist() if n.endswith('.class'))
        classes={n[:-6]:parse_class(z.read(n)) for n in names}
        declaration=validate_instance_target(target,classes)
        for n in names:
            methods=parse_bounded(z.read(n),True)
            for m in methods:
                for op in m.get('instructions',[]):
                    if op['opcode'] not in ('0xb6','0xb7','0xb9'):continue
                    relation=classify(op.get('reference',{}),target,classes)
                    if relation is not None:
                        sites.append(dict(caller={k:m[k] for k in ('owner','name','descriptor')},caller_code_sha256=m.get('code_sha256'),instruction=op,relation=relation))
            for i,b in enumerate(BOUNDDETAILS.get(n[:-6],{}).get('bootstrap_methods',[])):
                for j,arg in enumerate(b.get('arguments',[])):
                    relation=classify(arg.get('reference',{}),target,classes)
                    if relation is not None:handles.append(dict(owner=n[:-6],bootstrap_index=i,argument_index=j,reference=arg['reference'],relation=relation))
    def counts(rows):
        return {kind:sum(row['relation']['category']==kind for row in rows) for kind in ('EXACT_SYMBOLIC_OWNER','NOMINAL_DESCENDANT_CANDIDATE','SAME_SIGNATURE_NO_PROVEN_ANCESTRY')}
    root=Path(__file__).resolve().parent
    dependencies={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ('inherited_call_candidates_ysm_265.py','scan_ysm_265.py','audit_seed_recovery_ysm_265.py','validate_member_targets_ysm_265.py')}
    return dict(format='kneekura.ysm-nominal-inherited-call-candidates.v1',artifact_sha256=SHA,class_count=len(classes),target=list(target),target_declaration=declaration,
                tool_dependencies_sha256=dependencies,sites=sites,bootstrap_argument_sites=handles,site_counts=counts(sites),bootstrap_counts=counts(handles),
                scope='NOMINAL_ANCESTRY_ONLY_NOT_METHOD_RESOLUTION_OR_DYNAMIC_DISPATCH',ancestry_paths_exhaustive=False,nominal_path_strategy='FIRST_BREADTH_FIRST_PATH_WITHIN_ARTIFACT',independent_semantic_review='NOT_RUN',target_executed=False,external_classpath_loaded=False,source_scanned=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('jar','owner','name','descriptor','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args();r=capture(a.jar,(a.owner,a.name,a.descriptor));Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(class_count=r['class_count'],sites=r['site_counts'],bootstrap=r['bootstrap_counts'])))
if __name__=='__main__':main()
