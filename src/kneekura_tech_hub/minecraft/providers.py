"""Pinned Vineflower / tiny-remapper adapters with immutable derived evidence.

Only prepare_transform executes tools. No downloads, shell expressions, or
implicit execution in search. The caller must register a trusted tool hash.
"""
from __future__ import annotations
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path
from . import bytecode, index
from .mappings import MappingTable
from .process import run_process
from .storage import (Store, ContractError, IntegrityError, Limits, _collect,
                      atomic_write, canonical, digest, key_for, valid_hash, NAMESPACES)


def _output_records(path: Path, operation: str, store: Store) -> tuple[list, list]:
    limits=Limits(); errors=[]; ignored=[]; raw_hashes=[]
    if operation=='remap':
        records,raw=_collect(path,'jar',limits,errors,ignored,store.root)
        raw_hashes.append(store.put(raw))
        if not any(name.endswith('.class') for name,_ in records):
            raise ContractError('Remapper output contains no classes')
    else:
        records,_=_collect(path,'directory',limits,errors,ignored,store.root)
        flattened=[]
        for name,data in records:
            if name.endswith(('.jar','.zip')):
                # Validate archive paths and expansion budgets without extracting
                # anything to the host filesystem.
                with tempfile.TemporaryDirectory(prefix='kneekura-source-archive-') as tmp:
                    archive=Path(tmp)/'sources.jar'; archive.write_bytes(data)
                    children,raw=_collect(archive,'jar',limits,errors,ignored,store.root)
                raw_hashes.append(store.put(raw)); flattened.extend(children)
            else: flattened.append((name,data))
        records=flattened
        if not any(name.endswith('.java') for name,_ in records):
            raise ContractError('Decompiler produced no Java source; not a successful provider result')
    if errors: raise ContractError('Incomplete provider output: '+str(errors))
    if len({n for n,_ in records})!=len(records): raise ContractError('Duplicate provider output paths')
    if len(records)>limits.max_files or sum(len(b) for _,b in records)>limits.max_total_bytes:
        raise ContractError('Provider output capture budget exceeded')
    return records,raw_hashes


def _attach(store: Store, parent_id: str, receipt: dict) -> dict:
    parent=index._load(store,parent_id)
    p=json.loads(canonical(parent['profile']))
    p.pop('profile_id'); p.pop('profile_hash')
    origin=next(r for r in p['roots'] if r['id']==receipt['root_id'])
    rid='derived:'+receipt['cache_key']
    if any(r['id']==rid for r in p['roots']):
        return {'status':'OK','index_snapshot_id':parent_id,'profile_id':parent['profile']['profile_id'],
                'parent_index_snapshot_id':parent_id,'receipt_hash':store.put_json(receipt)}
    root={**origin,'id':rid,'path':'cas:'+receipt['output_artifact_hash'],
          'order':len(p['roots']),'artifact_hash':receipt['output_artifact_hash'],
          'namespace':receipt['output_namespace'],'stage':receipt['operation']+':'+origin['stage'],
          'role':'decompiled_source' if receipt['operation']=='decompile' else 'remapped_binary',
          'status':'OK','kind':'jar'}
    p['roots'].append(root)
    p['manifest'].setdefault('derivations',[]).append(store.put_json(receipt))
    new_classes=[]
    for entry in receipt['entries']:
        data=store.read(entry['content_hash']); name=entry['path']
        media='class' if name.endswith('.class') else 'text' if name.endswith(('.java','.json','.txt','.properties','.toml','.xml')) else 'binary'
        if media=='text':
            try: data.decode('utf-8')
            except UnicodeError: media='binary'
        d={k:root[k] for k in ('scope','role','stage','classloader','track','namespace')}
        d.update(root_id=rid,root_order=root['order'],path=name,artifact_hash=root['artifact_hash'],
                 content_hash=entry['content_hash'],size=len(data),media=media,
                 source_binary_match='CANDIDATE',derivation={'input_artifact_hash':receipt['input_artifact_hash'],
                     'provider_receipt_hash':store.put_json(receipt),'relationship':'DERIVED_FROM_PINNED_INPUT_NOT_ORIGINAL_SOURCE'})
        d['document_id']=key_for(d); p['documents'].append(d)
        if media=='class': new_classes.append({'document_id':d['document_id'],'reason':'Remapped class disassembly not prepared'})
    p['coverage']['requested_roots'].append(rid); p['coverage']['analyzed_roots'].append(rid)
    p['profile_hash']=key_for(p); p['profile_id']=p['profile_hash']
    result={**parent,'profile':p,'bytecode_unresolved':parent['bytecode_unresolved']+new_classes}
    snapshot=store.put_json(result)
    return {'status':'OK','profile_id':p['profile_id'],'index_snapshot_id':snapshot,
            'parent_index_snapshot_id':parent_id, 'receipt_hash':store.put_json(receipt),
            'warnings':['Provider derivation is not source/binary equivalence or runtime compatibility proof']}


def prepare_transform(store: Store, parent_id: str, root_id: str, operation: str, config: dict,
                      *, mapping_hash: str | None = None, from_namespace: str | None = None,
                      to_namespace: str | None = None, runner=run_process) -> dict:
    if operation not in {'decompile','remap'}: raise ContractError('Unsupported provider operation')
    if config.get('allow_execute') is not True: raise ContractError('Trusted provider allow_execute=true required')
    snapshot=index._load(store,parent_id)
    roots=[r for r in snapshot['profile']['roots'] if r['id']==root_id]
    if len(roots)!=1 or roots[0]['kind']!='jar' or not roots[0].get('artifact_hash'):
        raise ContractError('Select one captured JAR root')
    root=roots[0]; original=store.read(root['artifact_hash'])
    tool=Path(config.get('jar',''))
    if tool.is_symlink() or not tool.is_file(): raise ContractError('Trusted provider tool JAR unavailable')
    tool_bytes=tool.read_bytes()
    if digest(tool_bytes)!=valid_hash(config.get('jar_sha256')):
        raise IntegrityError('Trusted provider tool hash changed')
    memory=config.get('memory_mib',1024); threads=config.get('threads',2)
    if type(memory) is not int or not 128<=memory<=8192 or type(threads) is not int or not 1<=threads<=16:
        raise ContractError('Invalid provider memory/thread limit')
    jdk=bytecode.provider_identity(config.get('java','java'))
    jdk.update(provider='jdk-java-cli',options=[])
    namespace=root['namespace']; mapping=None
    if operation=='remap':
        if namespace!=from_namespace or to_namespace not in NAMESPACES-{'unknown'}:
            raise ContractError('Input/root namespace does not match explicit remapping namespace')
        mapping=store.read(valid_hash(mapping_hash))
        table=MappingTable.parse(mapping.decode('utf-8'),'tiny')
        if from_namespace not in table.namespaces or to_namespace not in table.namespaces:
            raise ContractError('Namespaces missing from Tiny mapping')
        namespace=to_namespace
    dependency_ids=config.get('classpath_root_ids',[])
    if not isinstance(dependency_ids,list) or len(set(dependency_ids))!=len(dependency_ids):
        raise ContractError('Explicit ordered provider classpath root IDs required')
    dependencies=[]
    for selected in dependency_ids:
        found=[r for r in snapshot['profile']['roots'] if r['id']==selected and r['kind']=='jar']
        if len(found)!=1 or found[0]['scope']=='buildscript': raise ContractError('Invalid provider library root')
        store.read(found[0]['artifact_hash']); dependencies.append(found[0]['artifact_hash'])
    identity={'provider':'vineflower' if operation=='decompile' else 'tiny-remapper',
              'version':config.get('version','UNKNOWN'),'jar_hash':digest(tool_bytes),'jdk':jdk,
              'memory_mib':memory,'threads':threads}
    key=key_for({'input':root['artifact_hash'],'root_id':root_id,'operation':operation,'provider':identity,
                 'mapping_hash':mapping_hash,'from_namespace':from_namespace,'to_namespace':to_namespace,
                 'classpath':dependencies})
    cache=store.root/'providers'/(key+'.json')
    if cache.is_symlink() or not cache.resolve().is_relative_to(store.root): raise IntegrityError('Escaped provider cache')
    if cache.exists():
        cached=json.loads(cache.read_bytes()); receipt=store.json(cached['receipt_hash'])
        if receipt.get('cache_key')!=key or receipt.get('input_artifact_hash')!=root['artifact_hash']:
            raise IntegrityError('Provider cache input mismatch')
        expected_fields = {'provider': identity, 'root_id': root_id, 'operation': operation,
                           'input_namespace': root['namespace'], 'output_namespace': namespace,
                           'mapping_hash': mapping_hash, 'classpath_artifact_hashes': dependencies}
        if any(receipt.get(k) != v for k, v in expected_fields.items()):
            raise IntegrityError('Provider cache derivation mismatch')
        # The normalized archive is the source of truth for an entry inventory;
        # a cache receipt cannot silently splice in bytes from another analysis.
        archive = store.read(receipt['output_artifact_hash'])
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            actual = {n: digest(z.read(n)) for n in z.namelist()}
        entries = receipt.get('entries', [])
        if (len(actual) != len(entries) or
                {e['path']: e['content_hash'] for e in entries} != actual):
            raise IntegrityError('Provider cache output inventory mismatch')
        return dict(_attach(store,parent_id,receipt),cache_hit=True)
    store.root.mkdir(parents=True,exist_ok=True)
    lease=store.root/'provider-active.lock'
    try: fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError as exc: raise ContractError('A heavy provider job is active; no automatic retry') from exc
    try:
        with os.fdopen(fd,'w') as f: f.write(str(os.getpid()))
        with tempfile.TemporaryDirectory(prefix='kneekura-provider-') as folder:
            work=Path(folder); source=work/'input.jar'; source.write_bytes(original)
            tool_copy=work/'tool.jar'; tool_copy.write_bytes(tool_bytes)
            output=work/('output' if operation=='decompile' else 'output.jar')
            argv=[jdk['executable'],f'-Xmx{memory}m','-jar',str(tool_copy)]
            libs=[]
            for i,h in enumerate(dependencies):
                path=work/f'library-{i}.jar'; path.write_bytes(store.read(h)); libs.append(str(path))
            if operation=='decompile':
                argv+=['--folder',f'--thread-count={threads}','--remove-synthetic=0','--remove-bridge=0',
                       *['--add-external='+p for p in libs],str(source),str(output)]
            else:
                mp=work/'mappings.tiny'; mp.write_bytes(mapping)
                argv += [str(source),str(output),str(mp),from_namespace,to_namespace,*libs,f'--threads={threads}']
            result=runner(argv,work,timeout=config.get('timeout_seconds',300),max_output_bytes=8*1024*1024)
            log_hash=store.put(result.get('stdout',b''))
            if result.get('completed') is not True or result.get('exit_code')!=0:
                return {'status':'ERROR','outcome':'FAIL','provider':identity,'log_hash':log_hash,
                        'reason':'Provider did not finish successfully; output not indexed','cache_hit':False}
            try: records,raw_hashes=_output_records(output,operation,store)
            except (OSError,ContractError,zipfile.BadZipFile) as exc:
                return {'status':'ERROR','outcome':'FAIL','log_hash':log_hash,'reason':str(exc),'cache_hit':False}
            package=io.BytesIO()
            with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
                for name,data in sorted(records):
                    info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
                    z.writestr(info,data)
            artifact=store.put(package.getvalue())
            receipt={'schema_version':1,'cache_key':key,'provider':identity,'root_id':root_id,
                     'operation':operation,'input_artifact_hash':root['artifact_hash'],
                     'input_namespace':root['namespace'],'output_namespace':namespace,
                     'mapping_hash':mapping_hash,'classpath_artifact_hashes':dependencies,
                     'output_artifact_hash':artifact,'raw_output_hashes':raw_hashes,'log_hash':log_hash,
                     'entries':[{'path':n,'content_hash':store.put(b)} for n,b in records]}
            tool_hash = store.put(tool_bytes)
            rh=store.put_json(receipt)
            for h in [rh, tool_hash, *([mapping_hash] if mapping_hash else []), root['artifact_hash'],artifact,log_hash,*raw_hashes,*dependencies,
                      *[e['content_hash'] for e in receipt['entries']]]: store.pin(h,'provider:'+rh)
            atomic_write(cache,canonical({'receipt_hash':rh}))
            return dict(_attach(store,parent_id,receipt),cache_hit=False)
    finally:
        lease.unlink(missing_ok=True)
