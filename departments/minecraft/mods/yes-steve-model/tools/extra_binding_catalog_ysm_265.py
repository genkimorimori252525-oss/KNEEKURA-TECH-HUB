#!/usr/bin/env python3
"""Fixed-artifact ctrl/tlm/math literal registration sites; not runtime reachability or semantic review."""
import argparse
import copy
import hashlib
import json
import zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded, BOUNDDETAILS

SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
P='com/elfmcys/yesstevemodel/'
BINDING=P+'oOoOoO0O000OOoo000O0OO00'
ROOTS={'ctrl':P+'OoOOOOOo0oo0000oooOOOoOO','tlm':P+'oOO0O0o0ooO0O0o0oo0oOooO','math':P+'O0OOoOoOOOoOOOoo0oO0oOo0'}


def capture(jar):
    raw=Path(jar).read_bytes()
    if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:
        raise ValueError('Wrong fixed artifact')
    cache={}; hashes={}; rows=[]; visited=[]; edges=[]
    with zipfile.ZipFile(jar) as archive:
        def methods(owner):
            if owner not in cache:
                data=archive.read(owner+'.class')
                hashes[owner]=hashlib.sha256(data).hexdigest()
                cache[owner]=parse_bounded(data,True)
            return cache[owner]
        bindings={(m['name'],m['descriptor']) for m in methods(BINDING)
                  if m['descriptor'].startswith('(Ljava/lang/String;') and m['descriptor'].endswith(')V')}
        for namespace,root in ROOTS.items():
            work=[(root,'<init>','()V')]; seen=set(); adapter_desc='(L'+root+';)V'
            while work:
                ident=work.pop(0)
                if ident in seen:continue
                seen.add(ident)
                matches=[m for m in methods(ident[0]) if (m['owner'],m['name'],m['descriptor'])==ident]
                if len(matches)!=1:raise ValueError(('ambiguous method',ident))
                method=matches[0]; ops=method.get('instructions',[])
                visited.append({'namespace':namespace,'owner':ident[0],'name':ident[1],'descriptor':ident[2],'code_sha256':method.get('code_sha256')})
                start=0
                for i,op in enumerate(ops):
                    ref=op.get('reference',{})
                    if op['opcode']=='0xb8' and ref.get('descriptor')==adapter_desc and ref.get('owner','').startswith(P):
                        target=tuple(ref[k] for k in ('owner','name','descriptor'))
                        work.append(target)
                        edges.append({'namespace':namespace,'caller':list(ident),'offset':op['offset'],'target':list(target)})
                    key=(ref.get('name'),ref.get('descriptor'))
                    direct=ref.get('owner') in (root,BINDING) and key in bindings
                    priority=(namespace=='ctrl' and ref.get('owner')==root and ref.get('descriptor','').startswith('(Ljava/lang/String;I') and ref.get('descriptor','').endswith(')V'))
                    if op['opcode'] not in ('0xb6','0xb7') or not (direct or priority):continue
                    segment=ops[start:i]
                    names=[x for x in segment if 'string' in x.get('reference',{})]
                    if len(names)!=1:raise ValueError(('ambiguous literal',ident,op,names))
                    name=names[0]['reference']['string']
                    selected=[x for x in segment if x['offset']>=names[0]['offset']]
                    bootstrap=[]
                    for x in selected:
                        if x['opcode']=='0xba':
                            n=x['reference']['bootstrap_index']
                            bootstrap.append({'index':n,'value':copy.deepcopy(BOUNDDETAILS[ident[0]]['bootstrap_methods'][n])})
                    rows.append({'query':namespace+'.'+name,'namespace':namespace,'caller':list(ident),
                        'registration_offset':op['offset'],'registration_method':ref,
                        'kind':'priority-condition' if priority else 'binding-registration',
                        'value_instruction_slice':selected,'value_bootstraps':bootstrap,
                        'caller_code_sha256':method.get('code_sha256'),
                        'runtime_branch':'NOT_EVALUATED','semantic_review':'NOT_INFERRED_FROM_CATALOG'})
                    start=i+1
    rows.sort(key=lambda r:(r['query'],r['caller'],r['registration_offset']))
    return {'artifact_sha256':SHA,'roots':ROOTS,'scope':'Constructors plus statically reached namespace-typed adapter registration methods only; both runtime branches retained.',
            'class_hashes':dict(sorted(hashes.items())),'visited_methods':visited,'adapter_call_edges':edges,'entries':rows,
            'unique_names':len({r['query'] for r in rows}),'global_runtime_complete':False,'target_runtime_executed':False}


def lookup(data):
    return [{'query':r['query'],'target':{'kind':'registration-site','owner':r['caller'][0],'name':r['caller'][1],'descriptor':r['caller'][2]},
             'registration_offset':r['registration_offset'],'scope':'Static ctrl/tlm/math registration site; runtime branch not evaluated; may have multiple real/fallback sites.'}
            for r in data['entries']]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('jar','evidence','lookup'):p.add_argument('--'+arg,required=True)
    p.add_argument('--capture',action='store_true');p.add_argument('--out')
    a=p.parse_args();data=capture(a.jar);lines=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in lookup(data))
    if a.capture:
        Path(a.evidence).write_text(json.dumps(data,indent=2)+'\n');Path(a.lookup).write_text(lines);return
    e=json.loads(Path(a.evidence).read_text())
    checks=[{'check':'exact-fixed-registration-graph','pass':e==data},{'check':'exact-lookup-projection','pass':Path(a.lookup).read_text()==lines}]
    negatives=[]
    for name,mut in [('missing-entry',lambda x:x['entries'].pop()),('wrong-name',lambda x:x['entries'][0].update(query='invented')),
        ('wrong-branch-claim',lambda x:x['entries'][0].update(runtime_branch='ALWAYS_TAKEN')),
        ('missing-adapter-edge',lambda x:x['adapter_call_edges'].pop()),('wrong-artifact',lambda x:x.update(artifact_sha256='0'*64)),
        ('invented-runtime-closure',lambda x:x.update(global_runtime_complete=True))]:
        c=copy.deepcopy(e);mut(c);negatives.append({'control':name,'rejected':c!=data})
    report={'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],
            'sites':len(data['entries']),'unique_names':data['unique_names'],'independent_semantic_review':'NOT_RUN','target_runtime_executed':False,'central_mapping_promoted':False}
    if not a.out:p.error('--out required for verification')
    Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('sites','unique_names','failures')}))
    if report['failures'] or any(not n['rejected'] for n in negatives):raise SystemExit(1)

if __name__=='__main__':main()
