#!/usr/bin/env python3
"""PAPERDOLL-CONFIG-MUTATION fixed-artifact integrity audit; does not execute target classes or independently prove prose semantics."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from audit_seed_recovery_ysm_265 import parse_bounded,BOUNDDETAILS
from scan_ysm_265 import parse_class
SHA='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
SIZE=63269843
OWNERS=['com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0$1', 'com/elfmcys/yesstevemodel/OOooOo000o0OoooOOO0OoO0o']
SELECTED=set([('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', '<init>', '()V'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'm_7856_', '()V'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'm_88315_', '(Lnet/minecraft/client/gui/GuiGraphics;IIF)V'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'm_6375_', '(DDI)Z'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'm_6348_', '(DDI)Z'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'm_7979_', '(DDIDD)Z'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'm_5534_', '(CI)Z'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()V'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'm_7379_', '()V'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/gui/components/Button;)V'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0$1', '<init>', '(Lcom/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0;IIIILnet/minecraft/network/chat/Component;ZZ)V'), ('com/elfmcys/yesstevemodel/oO0o0o0OOOo0OoOOo0OoO0o0$1', 'm_5691_', '()V'), ('com/elfmcys/yesstevemodel/OOooOo000o0OoooOOO0OoO0o', '<init>', '()V'), ('com/elfmcys/yesstevemodel/OOooOo000o0OoooOOO0OoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '()Z'), ('com/elfmcys/yesstevemodel/OOooOo000o0OoooOOO0OoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/gui/screens/PauseScreen;)Ljava/util/List;'), ('com/elfmcys/yesstevemodel/OOooOo000o0OoooOOO0OoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/Minecraft;Lnet/minecraft/client/gui/components/Button;)V'), ('com/elfmcys/yesstevemodel/OOooOo000o0OoooOOO0OoO0o', 'Oo0Oo0o00O00Oo0OOoOOoooo', '(Lnet/minecraft/client/Minecraft;Lcom/elfmcys/yesstevemodel/o0OOO0o0o0OOo000oO00o00O;)V'), ('com/elfmcys/yesstevemodel/OOooOo000o0OoooOOO0OoO0o', 'o0OOooo0o0OO00OoOOOo0o0O', '(Lnet/minecraft/client/Minecraft;Lnet/minecraft/client/gui/components/Button;)V'), ('com/elfmcys/yesstevemodel/OOooOo000o0OoooOOO0OoO0o', 'O00OOOooOoooOoo0o0o0oO0O', '(Lnet/minecraft/client/Minecraft;Lnet/minecraft/client/gui/components/Button;)V')])
SOURCES=[('src/main/java/com/elfmcys/yesstevemodel/client/gui/ExtraPlayerConfigScreen.java', '9387b87060719698c1be2cefef499fa67bd93b95e2c60d7cedd297626a50d5c8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/gui/ExtraPlayerConfigScreen.java', '9387b87060719698c1be2cefef499fa67bd93b95e2c60d7cedd297626a50d5c8', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6'), ('src/main/java/com/elfmcys/yesstevemodel/client/gui/AndroidCompat.java', '173c345117a9dc2f13c510a930ff735345506173cf372785417f089f0db5e744', 'f184edabd1b5115ce5a24cb6d155ba5a669f5ba6')]

KEYS=('access','instructions','supplemental_full_operand_records','exception_handlers','code_sha256')
DECL=('access','super','interfaces','fields','methods')
def ident(m):return tuple(m.get(k) for k in ('owner','name','descriptor'))
def audit(e,actual,decl,details):
    checks=[]
    def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
    ck('fixed-artifact',e.get('artifact',{}).get('sha256')==SHA and e.get('artifact',{}).get('size')==SIZE)
    ck('detailed-operands',e.get('detailed_operands') is True)
    rows=e.get('members',[]);ids=[ident(m) for m in rows]
    ck('selected-19-methods',len(ids)==len(set(ids))==19 and set(ids)==set(actual)==SELECTED)
    for m in rows:
        a=actual.get(ident(m),{})
        for k in KEYS:ck(str(ident(m))+':'+k,(k in m)==(k in a) and m.get(k)==a.get(k))
    ds=e.get('owner_declarations',[]);ck('fixed-owner-declarations',len(ds)==3 and {r['owner'] for r in ds}==set(OWNERS))
    for r in ds:ck(r['owner']+':declaration',r['declaration']==decl.get(r['owner']))
    bs=e.get('bootstrap_and_constant_evidence',[]);ck('fixed-bootstrap-records',len(bs)==3 and {r['owner'] for r in bs}==set(OWNERS))
    for r in bs:
        for k in ('constant_values','bootstrap_methods'):ck(r['owner']+':'+k,k in r and r[k]==details.get(r['owner'],{}).get(k))
    ss=e.get('source_tracks',[]);ck('fixed-source-records',sorted((r.get('path'),r.get('sha256'),r.get('revision')) for r in ss)==sorted(SOURCES))
    return checks

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('jar','evidence','source-root','out'):ap.add_argument('--'+k,required=True)
    a=ap.parse_args();raw=Path(a.jar).read_bytes()
    if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:raise SystemExit('Wrong fixed artifact')
    e=json.loads(Path(a.evidence).read_text());actual={};decl={}
    with zipfile.ZipFile(a.jar) as z:
        for owner in OWNERS:
            b=z.read(owner+'.class');c=parse_class(b);decl[owner]={k:c[k] for k in DECL}
            actual.update({ident(m):m for m in parse_bounded(b,True) if ident(m) in SELECTED})
    details=copy.deepcopy(BOUNDDETAILS);checks=audit(e,actual,decl,details);root=Path(a.source_root)
    revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    checks.append({'check':'source-revision','pass':revision==SOURCES[0][2]})
    for path,sha,rev in SOURCES:checks.append({'check':'source:'+path,'pass':hashlib.sha256((root/path).read_bytes()).hexdigest()==sha})
    negatives=[]
    def member(x,owner,desc,name=None):return next(m for m in x['members'] if m['owner']==OWNERS[owner] and m['descriptor']==desc and (name is None or m['name']==name))
    def op(x,owner,desc,offset,name=None):return next(o for o in member(x,owner,desc,name)['instructions'] if o['offset']==offset)
    def neg(name,mutate):
        x=copy.deepcopy(e);mutate(x);fail=[c for c in audit(x,actual,decl,details) if not c['pass']];negatives.append({'control':name,'rejected':bool(fail)})
    neg('missing-method',lambda x:x['members'].pop())
    neg('missing-owner',lambda x:x['owner_declarations'].pop())
    neg('missing-source',lambda x:x['source_tracks'].pop())
    neg('missing-bootstrap',lambda x:x['bootstrap_and_constant_evidence'].pop())
    neg('wrong-artifact',lambda x:x['artifact'].update(sha256='0'*64))
    neg('missing-paperdoll-config-owner-0',lambda x:member(x,0,'()V','m_7856_')['instructions'].pop())
    neg('missing-paperdoll-config-owner-1',lambda x:member(x,1,'()V','m_5691_')['instructions'].pop())
    neg('missing-paperdoll-config-owner-2',lambda x:member(x,2,'()Z','Oo0Oo0o00O00Oo0OOoOOoooo')['instructions'].pop())
    neg('wrong-scale-combiner',lambda x:op(x,0,'(DDIDD)Z',34,'m_7979_')['reference'].update(name='max'))
    neg('changed-draft-priority',lambda x:op(x,0,'(DDIDD)Z',4,'m_7979_').update(opcode='0x9a'))
    neg('missing-release-flag-reset',lambda x:op(x,0,'(DDI)Z',7,'m_6348_').update(opcode='0x00'))
    neg('missing-checkbox-live-write',lambda x:op(x,1,'()V',14,'m_5691_')['reference'].update(name='get'))
    neg('invented-close-finally',lambda x:member(x,0,'()V','m_7379_')['exception_handlers'].append({'handler':0}))
    result={'artifact_sha256':SHA,'checks':checks,'negative_controls':negatives,'failures':[c for c in checks if not c['pass']],'negative_failures':[n for n in negatives if not n['rejected']],'independent_semantic_review':'NOT_RUN','runtime_executed':False,'central_mapping_promoted':False}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'negative_controls':len(negatives),'failures':len(result['failures'])+len(result['negative_failures'])}))
    if result['failures'] or result['negative_failures']:raise SystemExit(1)
if __name__=='__main__':main()
