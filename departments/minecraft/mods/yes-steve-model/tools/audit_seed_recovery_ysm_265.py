#!/usr/bin/env python3
"""Audit hash-fixed YSM seed declarations and bounded Java reference paths.

Requires the official hash-fixed artifact locally; does not emit method bodies,
extract native entries, decrypt models, or establish binary/source equivalence.
"""
import argparse
import hashlib
import io
import json
import re
import struct
import zipfile
from pathlib import Path
from scan_ysm_265 import parse_class

BOUNDATTRS = {}
BOUNDDETAILS = {}

def parse_bounded(raw, detailed_operands=False):
    b=io.BytesIO(raw)
    def u(n): return int.from_bytes(b.read(n),'big')
    assert u(4)==0xcafebabe
    u(2);u(2); cp=[None]*u(2);i=1
    while i<len(cp):
        t=u(1)
        if t==1: cp[i]=(t,b.read(u(2)).decode('utf-8','replace'))
        elif t in (3,4): cp[i]=(t,b.read(4))
        elif t in (5,6): cp[i]=(t,b.read(8));i+=1
        elif t in (7,8,16,19,20): cp[i]=(t,u(2))
        elif t in (9,10,11,12,17,18): cp[i]=(t,u(2),u(2))
        elif t==15: cp[i]=(t,u(1),u(2))
        else: raise ValueError(t)
        i+=1
    def utf(i):return cp[i][1]
    def value(i):
        x=cp[i];t=x[0]
        if t==1:return x[1]
        if t in (7,8,16):return dict(cp_tag=t,value=value(x[1]))
        if t in (9,10,11):return dict(cp_tag=t,owner=value(cp[x[1]][1]),name=value(cp[x[2]][1]),descriptor=value(cp[x[2]][2]))
        if t==15:return dict(cp_tag=15,reference_kind=x[1],reference=value(x[2]))
        if t in (3,4,5,6):return dict(cp_tag=t,value=struct.unpack({3:'>i',4:'>f',5:'>q',6:'>d'}[t],x[1])[0])
        return dict(cp_tag=t)
    def ref(i):
        x=cp[i]
        if x[0] in (9,10,11):
            nt=cp[x[2]]
            return dict(owner=utf(cp[x[1]][1]),name=utf(nt[1]),descriptor=utf(nt[2]),cp_tag=x[0])
        if x[0]==7:return dict(class_name=utf(x[1]),cp_tag=7)
        if x[0]==18:
            nt=cp[x[2]]
            return dict(name=utf(nt[1]),descriptor=utf(nt[2]),bootstrap_index=x[1],cp_tag=18)
        if x[0]==8:return dict(string=utf(x[1]),cp_tag=8)
        if detailed_operands and x[0] in (3,4,5,6):
            value=struct.unpack({3:'>i',4:'>f',5:'>q',6:'>d'}[x[0]],x[1])[0]
            return dict(cp_tag=x[0],value=value)
        return dict(cp_tag=x[0])
    u(2);owner=utf(cp[u(2)][1]);u(2)
    for _ in range(u(2)):u(2)
    result=[];constants={}
    for kind in ('fields','methods'):
        for _ in range(u(2)):
            access,name,desc=u(2),utf(u(2)),utf(u(2));attrs={}
            for __ in range(u(2)):
                aname=utf(u(2));attrs[aname]=b.read(u(4))
            if kind!='methods':
                if 'ConstantValue' in attrs:constants[name]=value(int.from_bytes(attrs['ConstantValue'],'big'))
                continue
            rec=dict(owner=owner,name=name,descriptor=desc,access=access)
            if 'Code' in attrs:
                cb=attrs['Code'];n=int.from_bytes(cb[4:8],'big');code=cb[8:8+n]
                rec['code_sha256']=hashlib.sha256(code).hexdigest()
                ep=8+n;count=int.from_bytes(cb[ep:ep+2],'big');ep+=2
                rec['exception_handlers']=[]
                for _ in range(count):
                    start,end,handler,catch=struct.unpack('>HHHH',cb[ep:ep+8]);ep+=8
                    rec['exception_handlers'].append(dict(start=start,end=end,handler=handler,catch=utf(cp[catch][1]) if catch else None))
                ops=[];fullops=[];pos=0
                while pos<len(code):
                    start=pos;op=code[pos];length=1
                    if op in [0x10,0x12,*range(0x15,0x1a),*range(0x36,0x3b),0xa9,0xbc]:length=2
                    if op in [0x11,0x13,0x14,0x84,*range(0x99,0xa9),*range(0xb2,0xb9),0xbb,0xbd,0xc0,0xc1,0xc6,0xc7]:length=3
                    if op in [0xb9,0xba,0xc8,0xc9]:length=5
                    if op==0xc5:length=4
                    if op==0xc4:length=6 if code[pos+1]==0x84 else 4
                    if op in (0xaa,0xab):
                        p=pos+1
                        while p%4:p+=1
                        if op==0xaa:
                            lo=int.from_bytes(code[p+4:p+8],'big',signed=True);hi=int.from_bytes(code[p+8:p+12],'big',signed=True);length=p-pos+12+4*(hi-lo+1)
                        else:length=p-pos+8+8*int.from_bytes(code[p+4:p+8],'big')
                    inst=dict(offset=start,opcode=hex(op))
                    if detailed_operands and op in (0x10,0x11):inst['immediate']=int.from_bytes(code[pos+1:pos+length],'big',signed=True)
                    if detailed_operands and op in (0xaa,0xab):
                        inst['switch_default']=start+int.from_bytes(code[p:p+4],'big',signed=True)
                        if op==0xaa:
                            inst['switch_cases']={str(k):start+int.from_bytes(code[p+12+4*(k-lo):p+16+4*(k-lo)],'big',signed=True) for k in range(lo,hi+1)}
                        else:
                            inst['switch_cases']={str(int.from_bytes(code[q:q+4],'big',signed=True)):start+int.from_bytes(code[q+4:q+8],'big',signed=True) for q in range(p+8,pos+length,8)}
                    if op in [*range(0x99,0xa9),0xc6,0xc7]:inst['branch_target']=start+int.from_bytes(code[pos+1:pos+3],'big',signed=True)
                    if op in (0xc8,0xc9):inst['branch_target']=start+int.from_bytes(code[pos+1:pos+5],'big',signed=True)
                    if op in [*range(0xb2,0xbb),0xbb,0xbd,0xc0,0xc1]:inst['reference']=ref(int.from_bytes(code[pos+1:pos+3],'big'))
                    if op in (0x12,0x13):inst['reference']=ref(code[pos+1] if op==0x12 else int.from_bytes(code[pos+1:pos+3],'big'))
                    if detailed_operands and op==0x14:inst['reference']=ref(int.from_bytes(code[pos+1:pos+3],'big'))
                    operand=dict(offset=start,opcode=hex(op),encoded_operands_hex=code[pos+1:pos+length].hex())
                    if op in [*range(0x15,0x1a),*range(0x36,0x3b),0xa9]:operand['local_index']=code[pos+1]
                    if op==0x84:operand.update(local_index=code[pos+1],increment=int.from_bytes(code[pos+2:pos+3],'big',signed=True))
                    if op==0xb9:operand.update(argument_slot_count=code[pos+3],reserved_zero=code[pos+4])
                    fullops.append(operand);ops.append(inst);pos+=length
                assert pos==len(code)
                rec['instructions']=ops
                rec['supplemental_full_operand_records']=fullops
            result.append(rec)
    ca={};bootstraps=[]
    for _ in range(u(2)):
        name=utf(u(2));body=b.read(u(4))
        if name=='BootstrapMethods':
            bb=io.BytesIO(body)
            def bu():return int.from_bytes(bb.read(2),'big')
            for _ in range(bu()):
                handle=bu();arguments=[bu() for _ in range(bu())]
                bootstraps.append(dict(method_handle=value(handle),arguments=[value(i) for i in arguments]))
        if name=='NestHost':ca[name]=utf(cp[int.from_bytes(body,'big')][1])
        if name=='NestMembers':ca[name]=[utf(cp[int.from_bytes(body[p:p+2],'big')][1]) for p in range(2,len(body),2)]
        if name=='InnerClasses':
            ca[name]=[]
            for p in range(2,len(body),8):
                a,c,d,f=struct.unpack('>HHHH',body[p:p+8])
                ca[name].append(dict(inner=utf(cp[a][1]) if a else None,outer=utf(cp[c][1]) if c else None,inner_name=utf(d) if d else None,access=f))
    BOUNDATTRS[owner]=ca
    BOUNDDETAILS[owner]=dict(constant_values=constants,bootstrap_methods=bootstraps)
    return result


def normalized_shape(c):
    def norm(s):
        return re.sub(r'Lcom/elfmcys/yesstevemodel/[^;]+;', 'LYSM;', s)
    return {
        'access': c['access'],
        'super': norm('L' + c['super'] + ';') if c['super'] else None,
        'interfaces': sorted(norm('L' + x + ';') for x in c['interfaces']),
        'fields': sorted((x['access'], norm(x['descriptor'])) for x in c['fields']),
        'methods': sorted((x['access'], norm(x['descriptor'])) for x in c['methods']),
    }

def reference_path(m):
    return [op for op in m.get('instructions', []) if 'reference' in op]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--jar', required=True)
    ap.add_argument('--evidence', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    evidence=json.loads(Path(args.evidence).read_text())
    raw=Path(args.jar).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=evidence['artifact']['sha256'] or len(raw)!=evidence['artifact']['size']:
        raise SystemExit('Wrong artifact hash or size; no audit performed')
    classes={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in z.namelist():
            if n.endswith('.class') and not n.startswith('META-INF/versions/'):
                c=parse_class(z.read(n));classes[c['name']]=c
        support=evidence.get('bounded_dependency_support',[])
        owners={c['owner'] for c in evidence['classes']} | {m['owner'] for m in evidence['members']+support}
        details=evidence.get('bootstrap_and_constant_evidence',[])
        owners |= {r['owner'] for r in ([details] if isinstance(details,dict) else details)}
        connections=evidence.get('bootstrap_member_connections',[])
        owners |= {link['caller']['owner'] for row in connections+([details] if isinstance(details,dict) else details) for link in row.get('links',[])}
        owners |= {c['registration_anchor']['owner'] for c in evidence['classes'] if c.get('registration_anchor')}
        owners |= {r['owner'] for r in evidence.get('field_mapping_candidates',[])}
        bounded={owner:parse_bounded(z.read(owner+'.class'),evidence.get('detailed_operands',False)) for owner in sorted(owners)}
    checks=[]
    for row in evidence['classes']:
        owner=row['owner'];actual=classes[owner];expected=row['declaration']
        for k in ['access','super','interfaces']:
            checks.append({'check':owner+':'+k,'pass':actual[k]==expected[k]})
        for k in ['fields','methods']:
            shape=lambda v:sorted((x['access'],x['name'],x['descriptor']) for x in v)
            checks.append({'check':owner+':'+k,'pass':shape(actual[k])==shape(expected[k])})
        shape=normalized_shape(actual)
        matches=sorted(k for k,c in classes.items() if normalized_shape(c)==shape)
        shape_matches=matches
        if row.get('return_type_anchor'):
            anchor=row['return_type_anchor']
            methods=[m for m in classes[anchor['owner']]['methods'] if m['name']==anchor['name'] and m['descriptor']==anchor['descriptor']]
            returns={m['descriptor'].split(')',1)[1] for m in methods}
            matches=[k for k in matches if 'L'+k+';' in returns]
        if row.get('literal_anchors'):
            matches=[k for k in matches if all(s in classes[k]['utf8'] for s in row['literal_anchors'])]
        if row.get('required_reference_owners'):
            selected=[]
            for candidate in matches:
                if candidate not in bounded:
                    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                        bounded[candidate]=parse_bounded(archive.read(candidate+'.class'),evidence.get('detailed_operands',False))
                references={op.get('reference',{}).get('owner') for method in bounded[candidate] if method['name']=='<init>' for op in method.get('instructions',[])}
                if set(row['required_reference_owners'])<=references:selected.append(candidate)
            matches=selected
        if row.get('registration_anchor'):
            anchor=row['registration_anchor'];targets=set()
            for method in bounded[anchor['owner']]:
                if method['name']!=anchor['name'] or method['descriptor']!=anchor['descriptor']:continue
                ops=method.get('instructions',[])
                for i,op in enumerate(ops[:-4]):
                    path=ops[i:i+5]
                    if op.get('reference',{}).get('string')!=anchor['literal'] or [p['opcode'] for p in path][1:]!=['0xbb','0x59','0xb7','0xb6']:continue
                    target=path[1]['reference']['class_name'];constructor=path[3]['reference'];binding=path[4]['reference']
                    if constructor.get('owner')==target and constructor.get('name')=='<init>' and constructor.get('descriptor')=='()V' and binding.get('owner')==anchor['owner'] and binding.get('descriptor')==anchor.get('binding_descriptor'):
                        targets.add(target)
            matches=[k for k in matches if k in targets]
        checks.append({'check':owner+':unique-declaration-and-relations','pass':matches==[owner],'population':len(classes),'shape_matches':shape_matches,'matches':matches})
        if row.get('nesting_attributes'):
            checks.append({'check':owner+':nesting','pass':BOUNDATTRS[owner]==row['nesting_attributes']})
        if owner.endswith('/YesSteveModel'):
            anchors=['Lnet/minecraftforge/fml/common/Mod;','yes_steve_model','yes_steve_model-common.toml','yes_steve_model-client.toml']
            checks.append({'check':owner+':mod-config-anchors','pass':all(x in actual['utf8'] for x in anchors)})
    for row in evidence['members']+support:
        identity=row.get('mapping_id',row['owner']+'.'+row['name']+row['descriptor'])
        matches=[m for m in bounded[row['owner']] if m['name']==row['name'] and m['descriptor']==row['descriptor'] and m['access']==row['access']]
        ok=len(matches)==1
        checks.append({'check':identity+':flags-name-descriptor','pass':ok})
        if ok:
            expected_path=row.get('reference_path',[op for op in row.get('instructions',[]) if 'reference' in op])
            checks.append({'check':identity+':bounded-reference-path','pass':reference_path(matches[0])==expected_path})
            if row.get('instructions') is not None:
                checks.append({'check':identity+':opcode-control-flow','pass':matches[0].get('instructions')==row['instructions']})
            if row.get('supplemental_full_operand_records') is not None:
                checks.append({'check':identity+':encoded-operands','pass':matches[0].get('supplemental_full_operand_records')==row['supplemental_full_operand_records']})
            if row.get('code_sha256') is not None:
                checks.append({'check':identity+':code-digest','pass':matches[0].get('code_sha256')==row['code_sha256']})
            if row.get('exception_handlers') is not None:
                checks.append({'check':identity+':exception-handlers','pass':matches[0].get('exception_handlers')==row['exception_handlers']})
            if row.get('simple_opcodes') is not None:
                checks.append({'check':identity+':simple-opcodes','pass':[op['opcode'] for op in matches[0]['instructions']]==row['simple_opcodes']})
    details=evidence.get('bootstrap_and_constant_evidence',[])
    for row in ([details] if isinstance(details,dict) else details):
        actual=BOUNDDETAILS[row['owner']]
        for key in ('constant_values','bootstrap_methods'):
            if key in row:checks.append({'check':row['owner']+':'+key,'pass':actual[key]==row[key]})
    for row in evidence.get('bootstrap_member_connections',[])+([details] if isinstance(details,dict) else details):
        for link in row.get('links',[]):
            caller=link['caller'];identity=caller['owner']+'.'+caller['name']+caller['descriptor']+'@'+str(link['offset'])
            methods=[m for m in bounded[caller['owner']] if all(m[k]==caller[k] for k in ('name','descriptor','access'))]
            sites=[op for m in methods for op in m.get('instructions',[]) if op['offset']==link['offset'] and op['opcode']=='0xba' and op.get('reference')==link['call_site']]
            checks.append({'check':identity+':bootstrap-callsite','pass':len(methods)==1 and len(sites)==1})
            if len(sites)==1:
                bootstrap=BOUNDDETAILS[caller['owner']]['bootstrap_methods'][sites[0]['reference']['bootstrap_index']]
                handles=[arg['reference'] for arg in bootstrap['arguments'] if arg.get('cp_tag')==15]
                checks.append({'check':identity+':bootstrap-handle-relation','pass':bootstrap==link['bootstrap'] and handles==link['implementation_handles']})
    for row in evidence.get('field_mapping_candidates',[]):
        identity=row['mapping_id']
        matches=[f for f in classes[row['owner']]['fields'] if f['name']==row['name'] and f['descriptor']==row['descriptor'] and f['access']==row['access']]
        checks.append({'check':identity+':flags-name-descriptor','pass':len(matches)==1})
        if row.get('implementation_method_mapping_id'):
            target=next(m for m in evidence['members'] if m['mapping_id']==row['implementation_method_mapping_id']);links=[]
            for method in bounded[row['owner']]:
                if method['name']!='<clinit>':continue
                ops=method.get('instructions',[])
                for i,op in enumerate(ops[:-1]):
                    if op['opcode']!='0xba':continue
                    put=ops[i+1].get('reference',{});boot=BOUNDDETAILS[row['owner']]['bootstrap_methods'][op['reference']['bootstrap_index']]
                    method_handle=boot['method_handle'].get('reference',{})
                    for arg in boot['arguments'][1:2]:
                        ref=arg.get('reference',{})
                        if method_handle.get('owner')=='java/lang/invoke/LambdaMetafactory' and method_handle.get('name')=='metafactory' and put.get('name')==row['name'] and put.get('descriptor')==row['descriptor'] and all(ref.get(k)==target[k] for k in ('owner','name','descriptor')):links.append(ref)
            checks.append({'check':identity+':bootstrap-body-link','pass':len(links)==1})
    result={'artifact_sha256':evidence['artifact']['sha256'],'classes':len(classes),'seed_declarations':len(evidence['classes']),'member_paths':len(evidence['members']),'checks':checks,'failures':[x for x in checks if not x['pass']]}
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
    if result['failures']:raise SystemExit(1)

if __name__=='__main__':
    main()
