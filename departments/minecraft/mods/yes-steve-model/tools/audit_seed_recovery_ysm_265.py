#!/usr/bin/env python3
"""Audit the five bounded YSM seed declarations and sixteen Java reference paths.

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

def parse_bounded(raw):
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
        return dict(cp_tag=x[0])
    u(2);owner=utf(cp[u(2)][1]);u(2)
    for _ in range(u(2)):u(2)
    result=[]
    for kind in ('fields','methods'):
        for _ in range(u(2)):
            access,name,desc=u(2),utf(u(2)),utf(u(2));attrs={}
            for __ in range(u(2)):
                aname=utf(u(2));attrs[aname]=b.read(u(4))
            if kind!='methods':continue
            rec=dict(owner=owner,name=name,descriptor=desc,access=access)
            if 'Code' in attrs:
                cb=attrs['Code'];n=int.from_bytes(cb[4:8],'big');code=cb[8:8+n]
                ops=[];pos=0
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
                    if op in [*range(0xb2,0xbb),0xbb,0xbd,0xc0,0xc1]:inst['reference']=ref(int.from_bytes(code[pos+1:pos+3],'big'))
                    if op in (0x12,0x13):inst['reference']=ref(code[pos+1] if op==0x12 else int.from_bytes(code[pos+1:pos+3],'big'))
                    ops.append(inst);pos+=length
                assert pos==len(code)
                rec['instructions']=ops
            result.append(rec)
    ca={}
    for _ in range(u(2)):
        name=utf(u(2));body=b.read(u(4))
        if name=='NestHost':ca[name]=utf(cp[int.from_bytes(body,'big')][1])
        if name=='NestMembers':ca[name]=[utf(cp[int.from_bytes(body[p:p+2],'big')][1]) for p in range(2,len(body),2)]
        if name=='InnerClasses':
            ca[name]=[]
            for p in range(2,len(body),8):
                a,c,d,f=struct.unpack('>HHHH',body[p:p+8])
                ca[name].append(dict(inner=utf(cp[a][1]) if a else None,outer=utf(cp[c][1]) if c else None,inner_name=utf(d) if d else None,access=f))
    BOUNDATTRS[owner]=ca
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
        bounded={owner:parse_bounded(z.read(owner+'.class')) for owner in [c['owner'] for c in evidence['classes']]}
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
        checks.append({'check':owner+':unique-normalized-shape','pass':matches==[owner],'population':len(classes),'matches':matches})
        if row.get('nesting_attributes'):
            checks.append({'check':owner+':nesting','pass':BOUNDATTRS[owner]==row['nesting_attributes']})
        if owner.endswith('/YesSteveModel'):
            anchors=['Lnet/minecraftforge/fml/common/Mod;','yes_steve_model','yes_steve_model-common.toml','yes_steve_model-client.toml']
            checks.append({'check':owner+':mod-config-anchors','pass':all(x in actual['utf8'] for x in anchors)})
    for row in evidence['members']:
        matches=[m for m in bounded[row['owner']] if m['name']==row['name'] and m['descriptor']==row['descriptor'] and m['access']==row['access']]
        ok=len(matches)==1
        checks.append({'check':row['mapping_id']+':flags-name-descriptor','pass':ok})
        if ok:
            checks.append({'check':row['mapping_id']+':bounded-reference-path','pass':reference_path(matches[0])==row['reference_path']})
            if row.get('simple_opcodes') is not None:
                checks.append({'check':row['mapping_id']+':simple-opcodes','pass':[op['opcode'] for op in matches[0]['instructions']]==row['simple_opcodes']})
    result={'artifact_sha256':evidence['artifact']['sha256'],'classes':len(classes),'seed_declarations':len(evidence['classes']),'member_paths':len(evidence['members']),'checks':checks,'failures':[x for x in checks if not x['pass']]}
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
    if result['failures']:raise SystemExit(1)

if __name__=='__main__':
    main()
