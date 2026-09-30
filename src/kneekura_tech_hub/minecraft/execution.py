"""Synchronous adapter to an explicitly registered local Gradle workspace.

No scheduler, background dispatch, CI, shell command inference or automatic retry.
Request receipts survive process interruption; an unknown completion stays unknown.
"""
from __future__ import annotations

import json
import os
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from .process import run_process
from .storage import Store, ContractError, atomic_write, canonical, digest, key_for, valid_hash, _collect, Limits
from .workspace import _workspace, file_hash, workspace_fingerprint, configuration_fingerprint, _inputs
from .verification import evaluate_tests

TASKS={'compile':'build','unit':'test','gametest':'runGameTestServer','client':'runClient','export':'kneekuraExportInputs'}


def _file(root, value):
    if not isinstance(value,str) or not value: raise ContractError('Explicit file path required')
    path=Path(value); path=path if path.is_absolute() else root/path
    if path.is_symlink() or not path.resolve().is_relative_to(root): raise ContractError('Path escapes registered workspace')
    return path


def _request(value):
    if not isinstance(value,str) or not 1<=len(value)<=200: raise ContractError('A bounded request ID is required')
    return value


def _registry(registry,kind):
    root=_workspace(registry.get('workspace'))
    if registry.get('allow_gradle') is not True or kind not in registry.get('allowed_kinds',[]):
        raise ContractError('This Gradle operation is not registered')
    wrapper=root/('gradlew.bat' if os.name=='nt' else 'gradlew')
    if wrapper.is_symlink() or not wrapper.is_file() or file_hash(wrapper)!=valid_hash(registry.get('wrapper_sha256')):
        raise ContractError('Registered Gradle wrapper changed or unavailable')
    return root,wrapper


def _tree(template):
    rows=[]; total=0
    for base,dirs,files in os.walk(template,followlinks=False):
        dirs.sort(); files.sort()
        for name in dirs+files:
            if (Path(base)/name).is_symlink(): raise ContractError('Symlinks are not supported in test world templates')
        for name in files:
            path=Path(base)/name
            if not path.is_file(): raise ContractError('Special file in test world template')
            total+=path.stat().st_size
            if total>2*1024**3 or len(rows)>=50000: raise ContractError('Test template exceeds copy budget')
            rows.append({'path':path.relative_to(template).as_posix(),'sha256':file_hash(path)})
    return rows


def _world_destination(directory,world_name,layout):
    if layout not in ('server','client'):
        raise ContractError('Explicit server or client world layout required')
    if not isinstance(world_name,str) or not world_name.replace('_','').replace('-','').isalnum():
        raise ContractError('Simple world directory name required')
    directory=Path(directory)
    parent=directory/'saves' if layout=='client' else directory
    destination=parent/world_name
    if any(p.is_symlink() for p in (directory,parent,destination)):
        raise ContractError('Unsafe managed world path')
    return destination


def prepare_world(store: Store,registry: dict,*,template: str,request_id: str,
                  world_name='gametestserver',layout='server'):
    root=_workspace(registry.get('workspace')); _request(request_id)
    src=Path(template)
    if src.is_symlink() or not src.is_dir() or str(src.resolve()) not in {str(Path(x).resolve()) for x in registry.get('world_templates',[])}:
        raise ContractError('World template is not registered')
    parent=root/'.kneekura-runs'
    if parent.is_symlink(): raise ContractError('Unsafe run root')
    directory=parent/key_for({'workspace':str(root),'request_id':request_id})[:24]
    if directory.exists() or directory.is_symlink(): raise ContractError('Test world already exists; never overwrite/reuse it')
    # Validate only the intended managed path, before creating even the run root.
    destination=_world_destination(directory,world_name,layout)
    before=_tree(src); template_hash=key_for(before)
    parent.mkdir(exist_ok=True); directory.mkdir(mode=0o700)
    destination.parent.mkdir(exist_ok=True)
    shutil.copytree(src,destination,symlinks=False)
    if _tree(src)!=before or _tree(destination)!=before:
        raise ContractError('World template changed during copy; incomplete copy retained for inspection')
    marker={'schema_version':1,'workspace':str(root),'directory':str(directory),'world':str(destination),
            'world_id':directory.name,'world_template_hash':template_hash,'template':str(src.resolve()),
            'request_id':request_id,'fresh':True,'world_layout':layout}
    atomic_write(directory/'.kneekura-run.json',canonical(marker))
    h=store.put_json(marker); store.pin(h,'test-world:'+request_id)
    return dict(status='OK',**marker,marker_hash=h)


def _owned_world(root,world,*,layout=None):
    if not isinstance(world,str): raise ContractError('An explicitly prepared test world is required')
    path=Path(world); runs=root/'.kneekura-runs'
    try: parts=path.relative_to(runs).parts
    except ValueError: raise ContractError('Not a fresh managed test world') from None
    if not (len(parts)==2 or len(parts)==3 and parts[1]=='saves') or '..' in parts:
        raise ContractError('Not a fresh managed test world')
    directory=runs/parts[0]
    if (runs.is_symlink() or directory.is_symlink() or path.parent.is_symlink() or
        path.is_symlink() or not path.is_dir() or not path.resolve().is_relative_to(runs)):
        raise ContractError('Not a fresh managed test world')
    marker_path=directory/'.kneekura-run.json'
    if marker_path.is_symlink(): raise ContractError('Unsafe world marker')
    try: marker=json.loads(marker_path.read_bytes())
    except (OSError,ValueError): raise ContractError('Unowned test world') from None
    if not isinstance(marker,dict): raise ContractError('Unowned test world')
    # Older markers describe only the existing server layout. Never infer client
    # ownership from a nested directory or silently migrate a prepared world.
    actual_layout=marker.get('world_layout','server')
    expected=_world_destination(directory,path.name,actual_layout)
    if path!=expected or layout is not None and actual_layout!=layout:
        raise ContractError('Prepared world layout does not match this launch')
    if (marker.get('workspace')!=str(root) or marker.get('world')!=str(path.resolve()) or
        marker.get('directory')!=str(directory.resolve()) or marker.get('fresh') is not True):
        raise ContractError('Wrong or already used test world marker')
    valid_hash(marker.get('world_template_hash'))
    if key_for(_tree(path))!=marker['world_template_hash']:
        raise ContractError('Prepared test world changed before launch')
    return marker,marker_path


def _unit_report(root,started_ns,store):
    tests=[]; errors=[]; artifacts=[]
    results=root/'build/test-results/test'
    for path in sorted(results.glob('*.xml')):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            errors.append('Unsafe JUnit report'); continue
        if path.stat().st_mtime_ns<started_ns: continue
        if path.stat().st_size>16*1024*1024: errors.append('Oversized JUnit report'); continue
        raw=path.read_bytes(); h=store.put(raw); artifacts.append(h)
        if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw: errors.append('Entity definitions forbidden in reports'); continue
        try:
            xml=ET.fromstring(raw)
            for case in xml.iter('testcase'):
                status='FAIL' if case.find('failure') is not None or case.find('error') is not None else 'SKIPPED' if case.find('skipped') is not None else 'PASS'
                tests.append({'id':case.get('classname','')+'.'+case.get('name',''), 'status':status})
        except ET.ParseError: errors.append('Malformed JUnit XML')
    return tests,errors,artifacts


def execute(store: Store,registry: dict,*,kind: str,request_id: str,world=None,contract=None,
            runner=run_process,timeout=None):
    """Execute once. Registry is trusted user configuration, not ingested source data."""
    _request(request_id)
    if kind not in TASKS: raise ContractError('Unknown validation kind')
    root,wrapper=_registry(registry,kind)
    source=workspace_fingerprint(root); config=configuration_fingerprint(root)
    request={'workspace':str(root),'kind':kind,'request_id':request_id,'registry_hash':key_for(registry),
             'source_generation':source,'configuration_fingerprint':config,'world':world,
             'contract_hash':key_for(contract) if contract else None}
    path=store.root/'operations'/key_for({'workspace':str(root),'request_id':request_id})
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        saved=json.loads(path.read_bytes())
        if saved.get('request')!=request: raise ContractError('Request ID already used with different inputs')
        if saved.get('receipt_hash'):
            result=store.json(saved['receipt_hash'])['result']
            return dict(result,receipt_hash=saved['receipt_hash'],replayed_execution=False)
        return {'status':'PARTIAL','outcome':'UNKNOWN','retry_allowed':False,'replayed_execution':False,
                'reasons':['Accepted request has no completed receipt; do not resend blindly']}
    lock=store.root/('workspace-'+key_for(str(root))+'.lock')
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError: raise ContractError('This workspace has an active/uncertain operation; inspect before retrying') from None
    os.close(fd)
    try:
        # Recheck after taking the single-workspace lease. A concurrent editor must
        # not turn the captured plan into a different build.
        if workspace_fingerprint(root)!=source: raise ContractError('Workspace changed before execution')
        _registry(registry, kind)  # Recheck executable identity under the lease.
        argv=[str(wrapper),'--no-daemon','--console=plain']
        marker=None; session=None; marker_path=None
        if kind in ('gametest','client'):
            marker,marker_path=_owned_world(root,world,layout='client' if kind=='client' else 'server')
            budget=registry.get('remaining_launches'); budget_id=registry.get('launch_budget_id')
            if type(budget) is not int or budget<1 or not isinstance(budget_id,str) or not budget_id:
                raise ContractError('No explicit game launch budget')
            budgets=store.root/'launches'/key_for({'workspace':str(root),'budget':budget_id}); budgets.mkdir(parents=True,exist_ok=True)
            if len(list(budgets.glob('*.json')))>=budget: raise ContractError('Game launch budget exhausted')
            if not isinstance(contract,dict): raise ContractError('Run-bound assertion contract required')
            if contract.get('dirty_hash')!=source or contract.get('world_id')!=marker['world_id'] or contract.get('world_template_hash')!=marker['world_template_hash']:
                raise ContractError('Contract does not match current sources and prepared test world')
            from .runtime import create_session
            session=create_session(store,dict(registry,world_directory_name=Path(marker['world']).name,
                                              world_layout=marker.get('world_layout','server')),
                                   contract,directory=Path(marker['directory']))
            script=Path(__file__).with_name('resources')/'kneekura-run.init.gradle'
            observer=Path(__file__).with_name('resources')/'forge-observer'
            if not observer.is_dir(): observer=Path(__file__).resolve().parents[3]/'departments/minecraft/mod-ai/forge-observer'
            if not observer.is_dir(): raise ContractError('Packaged observer source root is unavailable')
            argv+=['-I',str(script),'-PkneekuraRunDirectory='+marker['directory'],
                   '-PkneekuraSessionFile='+str(session['path']),'-PkneekuraObserverRoot='+str(observer)]
        if kind=='unit': argv+=['--rerun-tasks']
        if kind=='export':
            script=Path(__file__).with_name('resources')/'kneekura-inputs.init.gradle'
            destination=root/'build/kneekura/resolved-inputs.json'
            argv+=['-I',str(script),'-PkneekuraNamespace=mojmap','-PkneekuraExport='+str(destination)]
            if registry.get('resolve_sources') is True: argv+=['-PkneekuraSources=true']
        argv.append(TASKS[kind])
        atomic_write(path,canonical({'request':request,'state':'ACCEPTED','receipt_hash':None}))
        if marker:
            atomic_write(budgets/(key_for(request_id)+'.json'),canonical(request))
            marker['fresh']=False; atomic_write(marker_path,canonical(marker))
        started_ns=time.time_ns()
        result=runner(argv,root,timeout=timeout or registry.get('timeout_seconds',300),
                      max_output_bytes=registry.get('max_log_bytes',8*1024*1024),env=registry.get('environment'))
        after=workspace_fingerprint(root); outputs=[]; errors=[]; tests=[]; report_hashes=[]
        log_hash=store.put(result['stdout']); outcome='PASS' if result['completed'] and result['exit_code']==0 else 'FAIL'
        if not result['completed']: outcome='BLOCKED'; errors.append('Process did not complete within its budget')
        if after!=source: outcome='BLOCKED'; errors.append('Workspace inputs changed during execution')
        if kind=='compile':
            declared=registry.get('build_outputs',[])
            if not declared: errors.append('No explicit packaged build outputs'); outcome='BLOCKED'
            for name in declared:
                output=_file(root,name)
                if not output.exists(): errors.append('Missing build output: '+name); outcome='BLOCKED'; continue
                kind_output='directory' if output.is_dir() else 'file'
                problems=[]; ignored=[]
                rows,original=_collect(output,kind_output,Limits(),problems,ignored,store.root)
                if problems or ignored: errors.append('Incomplete build artifact: '+name); outcome='BLOCKED'; continue
                inventory=[{'path':n,'hash':store.put(data)} for n,data in sorted(rows)]
                h=store.put(original) if original is not None else store.put_json(inventory)
                outputs.append({'path':name,'kind':kind_output,'content_hash':h})
        if kind=='export':
            destination=root/'build/kneekura/resolved-inputs.json'
            if not destination.is_file() or destination.stat().st_mtime_ns<started_ns:
                outcome='BLOCKED'; errors.append('No fresh resolved-input export')
            else:
                from .workspace import import_resolved
                raw=destination.read_bytes(); imported=import_resolved(json.loads(raw),root)
                outputs.append({'path':str(destination),'content_hash':store.put(raw),'manifest_hash':store.put_json(imported)})
        if kind=='unit':
            tests,test_errors,report_hashes=_unit_report(root,started_ns,store); errors.extend(test_errors)
            if test_errors: outcome='BLOCKED'
            elif any(t['status']=='FAIL' for t in tests): outcome='FAIL'
            elif not any(t['status']=='PASS' for t in tests): outcome='NOT_RUN'
        gametest=None
        if kind in ('gametest','client'):
            if kind=='gametest' and session:
                from .runtime import read_signed_report
                try:
                    report=read_signed_report(session,Path(marker['directory'])/'gametest-report.json')
                    report.update(completed=report.get('completed') is True and result['completed'],exit_code=result['exit_code'])
                    gametest=evaluate_tests(contract,report); report_hashes.append(store.put_json(report))
                    if after==source: outcome=gametest['outcome']; errors.extend(gametest['reasons'])
                except (OSError,ValueError):
                    if after == source and result['completed']: outcome='NOT_RUN'
                    errors.append('No authenticated same-run GameTest completion report')
            else:
                outcome='NOT_RUN'; errors.append('Client launch alone proves no rendering/behaviour assertion; inspect captured observations')
        public={'schema_version':1,'status':'OK' if not errors else 'PARTIAL','outcome':outcome,'reasons':errors,
                'request_id':request_id,'assertion_domain':{'compile':'compile_only','unit':'unit_tests','export':'input_resolution'}.get(kind,'server_behavior' if kind=='gametest' else 'client_observation'),
                'tests_executed':(gametest or {}).get('tests_executed', 0) if kind=='gametest' else sum(t['status']!='SKIPPED' for t in tests),
                'retry_allowed':False,
                'replayed_execution':False,'log_hash':log_hash,'outputs':outputs,'gametest':gametest,
                'evidence_level':'REGISTERED_LOCAL_EXECUTION_NOT_GENERAL_RUNTIME_PROOF'}
        receipt={'schema_version':1,'request':request,'source_generation':source,'source_generation_after':after,
                 'process':{k:v for k,v in result.items() if k!='stdout'},'argv':argv,'outputs':outputs,
                 'tests':tests,'report_hashes':report_hashes,'result':public}
        h=store.put_json(receipt)
        for ref in [h,log_hash,*report_hashes,*[o['content_hash'] for o in outputs]]: store.pin(ref,'operation:'+h)
        atomic_write(path,canonical({'request':request,'state':'COMPLETED','receipt_hash':h}))
        return dict(public,receipt_hash=h)
    finally:
        lock.unlink(missing_ok=True)
