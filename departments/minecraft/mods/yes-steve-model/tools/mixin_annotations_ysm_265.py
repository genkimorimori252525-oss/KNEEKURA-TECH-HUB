#!/usr/bin/env python3
"""Read exact JVM annotation structures without loading or executing classes."""
import argparse,copy,hashlib,io,json,struct,zipfile
from pathlib import Path
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
OWNER='com/elfmcys/yesstevemodel/mixin/client/WorldRendererMixin'
def annotations(raw):
    b=io.BytesIO(raw)
    def u(n):
        v=b.read(n)
        if len(v)!=n:raise ValueError('Truncated class')
        return int.from_bytes(v,'big')
    if u(4)!=0xcafebabe:raise ValueError('Class magic')
    u(2);u(2);cp=[None]*u(2);i=1
    while i<len(cp):
        t=u(1)
        if t==1:cp[i]=b.read(u(2)).decode('utf-8','replace')
        elif t in (3,4,5,6):
            cp[i]=struct.unpack({3:'>i',4:'>f',5:'>q',6:'>d'}[t],b.read(8 if t in (5,6) else 4))[0]
            if t in (5,6):i+=1
        elif t in (7,8,16,19,20):cp[i]=u(2)
        elif t in (9,10,11,12,17,18):cp[i]=(u(2),u(2))
        elif t==15:cp[i]=(u(1),u(2))
        else:raise ValueError(t)
        i+=1
    def decode(data):
        r=io.BytesIO(data)
        def v(n):
            x=r.read(n)
            if len(x)!=n:raise ValueError('Truncated annotation')
            return int.from_bytes(x,'big')
        def element():
            t=chr(v(1))
            if t in 'BCDFIJSZs':return {'tag':t,'value':cp[v(2)]}
            if t=='e':return {'tag':t,'type':cp[v(2)],'constant':cp[v(2)]}
            if t=='c':return {'tag':t,'descriptor':cp[v(2)]}
            if t=='@':return {'tag':t,'annotation':annotation()}
            if t=='[':return {'tag':t,'values':[element() for _ in range(v(2))]}
            raise ValueError('Unknown annotation element '+t)
        def annotation():
            typ=cp[v(2)];pairs=[]
            for _ in range(v(2)):pairs.append({'name':cp[v(2)],'value':element()})
            return {'type':typ,'elements':pairs}
        result=[annotation() for _ in range(v(2))]
        if r.read():raise ValueError('Unconsumed annotation bytes')
        return result
    def attrs():
        out={}
        for _ in range(u(2)):
            name=cp[u(2)];data=b.read(u(4))
            if name in ('RuntimeVisibleAnnotations','RuntimeInvisibleAnnotations'):out[name]=decode(data)
        return out
    access=u(2);owner=cp[cp[u(2)]];parent=cp[cp[u(2)]]
    for _ in range(u(2)):u(2)
    members={}
    for kind in ['fields','methods']:
        rows=[]
        for _ in range(u(2)):
            ac,name,desc=u(2),cp[u(2)],cp[u(2)];a=attrs();rows.append({'access':ac,'name':name,'descriptor':desc,'annotations':a})
        members[kind]=rows
    a=attrs()
    if b.read():raise ValueError('Unconsumed class bytes')
    return {'owner':owner,'super':parent,'access':access,'class_sha256':hashlib.sha256(raw).hexdigest(),'annotations':a,**members}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--evidence',required=True);p.add_argument('--out');p.add_argument('--capture',action='store_true');a=p.parse_args();raw=Path(a.jar).read_bytes()
    if len(raw)!=63269843 or hashlib.sha256(raw).hexdigest()!=SHA:raise SystemExit('Wrong fixed artifact')
    with zipfile.ZipFile(a.jar) as z:
        config=json.loads(z.read('yes_steve_model.mixins.json'));refmap=json.loads(z.read('yes_steve_model.refmap.json'))
        d={'artifact_sha256':SHA,'class':annotations(z.read(OWNER+'.class')),'mixin_config':config,'refmap_owner_mapping':refmap.get('mappings',{}).get(OWNER),'runtime_injection_verified':False}
    if a.capture:Path(a.evidence).write_text(json.dumps(d,indent=2)+'\n');return
    e=json.loads(Path(a.evidence).read_text());checks=[{'check':'exact-decoded-annotations','pass':e==d}];neg=[]
    for label,mut in [('missing-method',lambda x:x['class']['methods'].pop()),('wrong-artifact',lambda x:x.update(artifact_sha256='0'*64)),('missing-class-annotations',lambda x:x['class']['annotations'].clear()),('invented-runtime-proof',lambda x:x.update(runtime_injection_verified=True)),('lost-injection-annotation',lambda x:x['class']['methods'][1]['annotations'].clear())]:
        y=copy.deepcopy(e);mut(y);neg.append({'control':label,'rejected':y!=d})
    r={'checks':checks,'negative_controls':neg,'failures':[c for c in checks if not c['pass']],'runtime_executed':False,'independent_review':'NOT_RUN'};Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(neg),'failures':len(r['failures'])}))
    if r['failures'] or any(not n['rejected'] for n in neg):raise SystemExit(1)
if __name__=='__main__':main()
