"""Fixed U04 selected dependency provenance; no remapping or class loading here."""
from __future__ import annotations
import io
import re
import stat
import tomllib
import zipfile

from .mappings import MappingTable
from .storage import ArtifactUnavailable, ContractError, canonical, digest, key_for, valid_hash, safe_entry, Limits


REQUIRED_CLASSES = {
    'twilightforest/entity/boss/Hydra.class', 'twilightforest/entity/boss/HydraPart.class',
    'twilightforest/entity/boss/HydraHeadContainer.class', 'twilightforest/client/TFClientSetup.class',
    'twilightforest/client/JappaPackReloadListener.class',
    'twilightforest/client/renderer/entity/HydraRenderer.class',
    'twilightforest/client/model/entity/HydraModel.class',
}


def validate_shape(value):
    fields={'schema_version','kind','coordinate','sha256','provider_receipt_hash','class_resources'}
    if (not isinstance(value,dict) or set(value)!=fields or type(value.get('schema_version')) is not int
            or value['schema_version']!=1 or value.get('kind')!='u04_hydra_derived_dependency'
            or not isinstance(value.get('coordinate'),str) or not 1<=len(value['coordinate'])<=2048
            or not value['coordinate'].startswith('twilightforest-')
            or any(ord(c)<32 or ord(c)==127 for c in value['coordinate'])):
        raise ContractError('Explicit fixed U04 target selection required')
    valid_hash(value['sha256']); valid_hash(value['provider_receipt_hash'])
    names=value['class_resources']
    if (not isinstance(names,list) or not 1<=len(names)<=32
            or any(not isinstance(n,str) or len(n)>2048
                   or not re.fullmatch(r'twilightforest/(?:[A-Za-z0-9_$]+/)*[A-Za-z0-9_$]+\.class',n) for n in names)
            or len(set(names))!=len(names) or not REQUIRED_CLASSES<=set(names)):
        raise ContractError('One to32 distinct safe Twilight class resources required')
    return value


def _read(store,h):
    h=valid_hash(h)
    try: size=store.blob_path(h).stat().st_size
    except OSError as exc: raise ArtifactUnavailable('Provider chain artifact unavailable') from exc
    if size>512*1024*1024:
        raise ContractError('Provider chain byte budget exceeded')
    return store.read(h)


def _entries(raw):
    limits=Limits(); result={}; total=0
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos=z.infolist()
            if len(infos)>limits.max_files: raise ContractError('Provider archive entry budget exceeded')
            seen=set()
            for info in infos:
                name=safe_entry(info.filename)
                if name in seen or stat.S_ISLNK(info.external_attr>>16) or info.flag_bits&1:
                    raise ContractError('Unsafe/duplicate provider archive entry')
                seen.add(name); total+=info.file_size
                if (info.file_size>limits.max_file_bytes or total>limits.max_total_bytes
                        or info.file_size/max(1,info.compress_size)>limits.max_compression_ratio):
                    raise ContractError('Provider archive expansion budget exceeded')
                if not info.is_dir():
                    with z.open(info) as stream: data=stream.read(limits.max_file_bytes+1)
                    if len(data)!=info.file_size: raise ContractError('Truncated provider archive')
                    result[name]=data
    except (zipfile.BadZipFile,RuntimeError,EOFError) as exc:
        raise ContractError('Invalid retained provider archive') from exc
    return result


def validate_selection(store,registry,inventory):
    selection=validate_shape(registry.get('target_selection'))
    matches=[e for e in inventory['entries'] if e['coordinate']==selection['coordinate'] and e['sha256']==selection['sha256']]
    if not matches or not any(e['scope']=='runtime' for e in matches):
        raise ContractError('Selected target is absent from exact resolved runtime inventory')
    receipt=store.json(selection['provider_receipt_hash'])
    if not isinstance(receipt,dict): raise ContractError('Retained remapping receipt required')
    provider=receipt.get('provider',{}); classpath=receipt.get('classpath_artifact_hashes')
    if (type(receipt.get('schema_version')) is not int or receipt['schema_version']!=1
            or receipt.get('operation')!='remap' or receipt.get('input_namespace')!='srg'
            or receipt.get('output_namespace')!='mojmap' or receipt.get('output_artifact_hash')!=selection['sha256']
            or not isinstance(provider,dict) or provider.get('provider')!='tiny-remapper'
            or not isinstance(provider.get('version'),str) or not re.fullmatch(r'\d+(?:\.\d+)+',provider['version'])
            or not isinstance(receipt.get('root_id'),str) or not receipt['root_id']
            or not isinstance(classpath,list) or not 1<=len(classpath)<=4096):
        raise ContractError('U04 target requires exact retained SRG-to-Mojmap provider derivation')
    expected_key=key_for({'input':receipt['input_artifact_hash'],'root_id':receipt['root_id'],'operation':'remap',
        'provider':provider,'mapping_hash':receipt.get('mapping_hash'),'from_namespace':'srg','to_namespace':'mojmap',
        'classpath':classpath})
    if receipt.get('cache_key')!=expected_key: raise ContractError('Provider derivation cache identity mismatch')
    raw_outputs=receipt.get('raw_output_hashes')
    if not isinstance(raw_outputs,list) or not 1<=len(raw_outputs)<=8:
        raise ContractError('Provider original output archive evidence required')
    refs={receipt['input_artifact_hash'],selection['sha256'],provider.get('jar_hash'),receipt.get('mapping_hash'),
          receipt.get('log_hash'),*classpath,*raw_outputs}
    captured={}; total=0
    for h in refs:
        data=_read(store,h); total+=len(data)
        if total>2*1024*1024*1024: raise ContractError('Provider chain byte budget exceeded')
        captured[h]=data
    table=MappingTable.parse(captured[receipt['mapping_hash']].decode('utf-8'),'tiny')
    if not {'srg','mojmap'}<=set(table.namespaces): raise ContractError('Provider mapping namespaces differ')
    output=_entries(captured[selection['sha256']]); original=_entries(captured[receipt['input_artifact_hash']])
    try:
        mods=tomllib.loads(original.get('META-INF/mods.toml',b'').decode('utf-8')).get('mods',[])
    except (ValueError,UnicodeError) as exc: raise ContractError('Invalid original TF mod metadata') from exc
    if not isinstance(mods,list) or not any(isinstance(m,dict) and m.get('modId')=='twilightforest' for m in mods):
        raise ContractError('U04 selected provider input is not identified as Twilight Forest')
    expected={n:digest(data) for n,data in output.items()}
    entries=receipt.get('entries')
    if (not isinstance(entries,list) or len(entries)!=len(expected)
            or any(not isinstance(e,dict) or set(e)!={'path','content_hash'} for e in entries)
            or {e['path']:e['content_hash'] for e in entries}!=expected):
        raise ContractError('Provider output entries differ from exact derived archive')
    for row in entries:
        if _read(store,row['content_hash'])!=output[row['path']]: raise ContractError('Provider entry bytes differ')
    for h in raw_outputs:
        if {n:digest(data) for n,data in _entries(captured[h]).items()}!=expected:
            raise ContractError('Raw provider output differs from normalized archive')
    if {n:data for n,data in original.items() if not n.endswith('.class')} != {n:data for n,data in output.items() if not n.endswith('.class')}:
        raise ContractError('U04 remapping must retain every original non-class resource')
    if any(n not in output for n in selection['class_resources']): raise ContractError('Selected class resource missing from derived archive')
    return {'target_selection':selection,'target_selection_hash':key_for(selection),
            'target_dependency_probes':[{'resource':n,'sha256':expected[n]} for n in selection['class_resources']],
            'selected_target_root_ids':['dependency:'+str(e['order']) for e in matches]}
