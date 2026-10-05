#!/usr/bin/env python3
"""Rerun ten concrete evidence-regression controls against the hash-fixed JAR.

The fixtures deliberately corrupt retained expected evidence, never the artifact.
They test audit rejection, not execution of Minecraft or native code.
"""
import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--jar',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    audit=root/'tools/audit_seed_recovery_ysm_265.py'
    dossiers={key:json.loads((root/name).read_text()) for key,name in {
        'loop':'MOLANG-LOOP-EVIDENCE-2026-10-05.json',
        'math':'MOLANG-MATH-EVIDENCE-2026-10-05.json',
        'pooled':'MOLANG-POOLED-PARSER-EVIDENCE-2026-10-05.json',
        'ast':'MOLANG-TYPED-AST-EVIDENCE-2026-10-05.json'}.items()}
    fixtures=[]
    def fixture(key,label):
        value=copy.deepcopy(dossiers[key]);fixtures.append((label,value));return value
    def member(value,suffix,name):
        return next(row for row in value['members'] if row['semantic_owner'].endswith(suffix) and row['semantic_member']==name)
    value=fixture('loop','loop-local-iinc-zero')
    row=member(value,'ExpressionEvaluatorImpl','visitLoop')
    next(op for op in row['supplemental_full_operand_records'] if op['opcode']=='0x84')['increment']=0
    value=fixture('loop','loop-foreach-bootstrap-body-swapped')
    detail=value['bootstrap_and_constant_evidence']
    if isinstance(detail,list):detail=next(row for row in detail if row['owner'].endswith('/OOooO0oOOOoO000oOo0O00Oo'))
    a,b=detail['bootstrap_methods'][:2]
    a['arguments'][1],b['arguments'][1]=b['arguments'][1],a['arguments'][1]
    value=fixture('math','acos-registration-reassigned-to-asin')
    next(row for row in value['classes'] if row['semantic_owner'].endswith('.ACos'))['registration_anchor']['literal']='asin'
    value=fixture('math','acos-arity-one-to-two')
    next(op for op in member(value,'.ACos','validateArgumentSize')['instructions'] if op['offset']==1)['opcode']='0x5'
    value=fixture('math','acos-operation-changed-to-asin')
    next(op for op in member(value,'.ACos','evaluate')['instructions'] if op.get('reference',{}).get('owner')=='java/lang/Math')['reference']['name']='asin'
    value=fixture('pooled','struct-copy-sharing-condition-inverted')
    row=member(value,'HashMapStruct','copy')
    branch=next(op for op in row['instructions'] if op['opcode'] in ['0x99','0x9a'])
    branch['opcode']='0x9a' if branch['opcode']=='0x99' else '0x99'
    value=fixture('ast','variable-node-target-interface-swapped')
    variable=next(row for row in value['classes'] if row['semantic_owner'].endswith('.VariableExpression'))
    assignable=next(row for row in value['classes'] if row['semantic_owner'].endswith('.AssignableVariableExpression'))
    variable['literal_anchors']=assignable['literal_anchors']
    value=fixture('ast','binary-node-constructor-label-wrong')
    next(row for row in value['classes'] if row['semantic_owner'].endswith('.BinaryExpression'))['literal_anchors'][0]='conditional'
    value=fixture('ast','array-visitor-dispatch-subtype-wrong')
    owner=next(row['owner'] for row in value['classes'] if row['semantic_owner'].endswith('.ArrayAccessExpression'))
    target=next(row['owner'] for row in value['classes'] if row['semantic_owner'].endswith('.StructAccessExpression'))
    dispatch=next(row for row in value['bounded_dependency_support'] if row['owner']==owner and any(op.get('reference',{}).get('descriptor')=='(L'+owner+';)Ljava/lang/Object;' for op in row.get('instructions',[])))
    next(op for op in dispatch['instructions'] if op.get('reference',{}).get('descriptor')=='(L'+owner+';)Ljava/lang/Object;')['reference']['descriptor']='(L'+target+';)Ljava/lang/Object;'
    value=fixture('pooled','context-function-gate-condition-inverted')
    row=member(value,'ContextFunction','evaluate')
    branch=next(op for op in row['instructions'] if op['opcode'] in ['0x99','0x9a'])
    branch['opcode']='0x9a' if branch['opcode']=='0x99' else '0x99'
    results=[]
    with tempfile.TemporaryDirectory(prefix='ysm265-evidence-negatives-') as temporary:
        temporary=Path(temporary)
        for index,(label,value) in enumerate(fixtures):
            evidence=temporary/f'{index}.json';output=temporary/f'{index}-audit.json'
            evidence.write_text(json.dumps(value))
            process=subprocess.run([sys.executable,str(audit),'--jar',str(Path(args.jar).resolve()),'--evidence',str(evidence),'--out',str(output)],capture_output=True,text=True)
            actual=json.loads(output.read_text()) if output.exists() else {}
            failures=actual.get('failures',[])
            results.append({'mutation':label,'exit_code':process.returncode,'rejected':process.returncode==1 and bool(failures),'failed_checks':[row['check'] for row in failures]})
    report={'purpose':'Evidence corruption regression checks; no artifact modification or runtime execution','checks':len(results),'failures':[row for row in results if not row['rejected']],'results':results}
    Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'checks':report['checks'],'failures':report['failures']}))
    if report['failures']:raise SystemExit(1)

if __name__=='__main__':main()
