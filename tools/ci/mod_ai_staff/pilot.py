"""Build-only, disposable staff pilot using the existing MOD-AI execution receipts.

No launch, EULA, authentication, driver installation, or CI mutation is available.
The capture remains in its original CAS. Only its validated model and texture are
installed, after complete inventory validation and exclusive-create checks.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import zipfile

from kneekura_tech_hub.minecraft import execution, index
from kneekura_tech_hub.minecraft.asset_contract import decode_json
from kneekura_tech_hub.minecraft.asset_export import _check_parent, _validate_capture
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical, capture_profile, digest, valid_hash
from kneekura_tech_hub.minecraft.workspace import _inputs, _properties, file_hash, workspace_fingerprint

HERE = Path(__file__).resolve().parent
TARGET = {'minecraft': '1.20.1', 'loader': 'forge', 'loader_version': '47.4.6', 'java_major': 17}
ASSET_TARGET = dict(TARGET, track='ANCHOR')
ASSET = 'kneekura:celestial_staff'
JAR = 'build/libs/kneekura-1.0.0.jar'


def require(value, message):
    if not value: raise ContractError(message)


def create_file(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    _check_parent(path.parent)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def configure(root: Path):
    root = _check_parent(root)
    require((root/'gradle.properties').is_file() and not (root/'gradle.properties').is_symlink(),
            'Real MDK properties required; symlink inputs forbidden')
    props = _properties(root / 'gradle.properties')
    require(props.get('minecraft_version') == '1.20.1' and props.get('forge_version') == '47.4.6',
            'Pilot requires the exact fresh Forge 1.20.1-47.4.6 MDK')
    require(not (root/'src').exists() and not (root/'src').is_symlink(), 'Existing source: overwrite prohibited')
    require((root/'gradlew').is_file() and not (root/'gradlew').is_symlink(), 'Real MDK wrapper required')
    # The MDK must be extracted with its example src omitted, never deleted from an existing project.
    for source in sorted((HERE/'java').rglob('*.java')):
        create_file(root/'src/main/java'/source.relative_to(HERE/'java'), source.read_bytes())
    resources = root/'src/main/resources'
    create_file(resources/'META-INF/mods.toml', b'''modLoader="javafml"
loaderVersion="[47,48)"
license="All Rights Reserved"
[[mods]]
modId="kneekura"
version="1.0.0"
displayName="Disposable Celestial Staff pilot"
[[dependencies.kneekura]]
modId="forge"
mandatory=true
versionRange="[47.4.6]"
ordering="NONE"
side="BOTH"
[[dependencies.kneekura]]
modId="minecraft"
mandatory=true
versionRange="[1.20.1]"
ordering="NONE"
side="BOTH"
''')
    create_file(resources/'pack.mcmeta', canonical({'pack':{'pack_format':15,'description':'Disposable staff pilot'}}))
    create_file(resources/'assets/kneekura/lang/en_us.json', canonical({'item.kneekura.celestial_staff':'Celestial Staff'}))
    # Existing helper only serializes a three-block empty NBT template; it does not launch.
    import importlib.util
    module_spec = importlib.util.spec_from_file_location('mod_ai_live_template', HERE.parent/'mod_ai_live.py')
    module = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
    create_file(resources/'data/kneekura/structures/empty.nbt', module.empty_structure())
    # Only the fresh MDK's documented mod identity properties change.
    original = (root/'gradle.properties').read_text()
    lines = original.splitlines()
    changes = {'mod_id':'kneekura','mod_version':'1.0.0','mod_name':'Celestial Staff pilot',
               'mod_group_id':'org.kneekura.staff','org.gradle.jvmargs':'-Xmx3G',
               'org.gradle.workers.max':'2','org.gradle.daemon':'false'}
    seen=set(); revised=[]
    for line in lines:
        key=line.split('=',1)[0]
        if key in changes: revised.append(key+'='+changes[key]); seen.add(key)
        else: revised.append(line)
    revised += [key+'='+value for key,value in changes.items() if key not in seen]
    (root/'gradle.properties').write_text('\n'.join(revised)+'\n')
    return {'status':'OK','outcome':'NOT_RUN','source_generation':workspace_fingerprint(root)}


def _validated_export(store: Store, manifest_hash: str):
    manifest = decode_json(store.read(valid_hash(manifest_hash)))
    require(isinstance(manifest,dict) and manifest.get('record_type')=='asset_export', 'Expected asset export manifest')
    require(manifest.get('asset_id')==ASSET and manifest.get('target')==ASSET_TARGET, 'Exact staff resource and target required')
    receipt, request, content = _validate_capture(store, valid_hash(manifest.get('capture_receipt_hash')))
    entries=[{'kind':kind,'path':request['exports'][kind],'content_hash':digest(raw),'size_bytes':len(raw)}
             for kind,raw in content.items()]
    expected={'schema_version':1,'record_type':'asset_export','capture_receipt_hash':manifest['capture_receipt_hash'],
              'request_hash':receipt['request_hash'],'profile_id':request['profile_id'],'asset_id':request['asset_id'],
              'target':request['target'],'loaded_revision':'UNATTESTED','files':entries,
              'source_model_hash':receipt['artifacts'][0]['content_hash'],
              'derivation':'texture_resource_id_qualified_for_exact_request',
              'verification':{'structural':'PASS','visual':'NOT_RUN','runtime':'NOT_RUN'},'outcome':'NOT_RUN'}
    require(manifest==expected, 'Export inventory or capture identity mismatch')
    require(request['asset_id']==ASSET and request['target']==ASSET_TARGET, 'Captured asset target differs from pilot')
    return manifest, content


def validate_imported_resources(root: Path, store: Store, manifest_hash: str) -> dict:
    """Bind current resources to their original captured bytes, never a mutable receipt."""
    root=_check_parent(root);manifest,content=_validated_export(store,manifest_hash)
    resources=[entry for entry in manifest["files"] if entry["kind"] in ("model","texture")]
    for entry in resources:
        path=root/"src/main/resources"/entry["path"];_check_parent(path.parent)
        require(path.is_file() and not path.is_symlink() and path.read_bytes()==content[entry["kind"]],
                "Workspace resources differ from original captured asset bytes")
    return {"manifest_hash":manifest_hash,"capture_receipt_hash":manifest["capture_receipt_hash"],
            "request_hash":manifest["request_hash"],"asset_profile_id":manifest["profile_id"],
            "source_model_hash":manifest["source_model_hash"],"files":resources}


def import_asset(store: Store, manifest_hash: str, directory: Path, root: Path):
    directory=_check_parent(directory);root=_check_parent(root)
    manifest,content=_validated_export(store,manifest_hash)
    require((directory/"manifest.json").is_file() and not (directory/"manifest.json").is_symlink(), "Real export manifest required")
    require((directory/"manifest.json").read_bytes()==canonical(manifest), "Export manifest differs from CAS")
    entries=manifest["files"]
    prepared=[]
    for entry in entries:
        source=directory/entry['path']; _check_parent(source.parent)
        require(source.is_file() and not source.is_symlink(), 'Real captured resource required')
        raw=source.read_bytes()
        require(raw==content[entry['kind']], 'Export bytes differ from validated capture')
        if entry['kind']=='native': continue  # Keep editable source in its existing evidence store.
        destination=root/'src/main/resources'/entry['path']
        # Validate every existing ancestor before any destination is created.
        parent=destination.parent
        while not parent.exists() and not parent.is_symlink(): parent=parent.parent
        _check_parent(parent)
        require(not destination.exists() and not destination.is_symlink(), 'Resource exists; overwrite prohibited')
        prepared.append((destination,raw,entry))
    before=workspace_fingerprint(root)
    for destination,raw,_ in prepared: create_file(destination,raw)
    return {'schema_version':1,'outcome':'NOT_RUN','asset_export_manifest_hash':manifest_hash,
            'files':[dict(entry,path=destination.relative_to(root).as_posix()) for destination,_,entry in prepared],
            'source_generation_before':before,'source_generation_after':workspace_fingerprint(root),
            'note':'Resources copied; recapture resolved inputs before any new run contract'}



def import_evidence_bundle(path: Path, store: Store) -> dict:
    """Hydrate only exact hashed capture bytes; validate all before any CAS write."""
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 32*1024*1024,
            'A bounded original-byte evidence bundle is required')
    value=decode_json(path.read_bytes(),max_bytes=32*1024*1024)
    require(isinstance(value,dict) and set(value)=={'schema_version','receipt_hash','export_manifest_hash','encoding','objects'}
            and type(value['schema_version']) is int and value['schema_version']==1
            and value['encoding']=='base64', 'Invalid evidence bundle fields')
    encoded=value['objects']
    require(isinstance(encoded,dict) and 1 <= len(encoded) <= 64, 'Bounded evidence object inventory required')
    decoded={}
    for key,body in encoded.items():
        valid_hash(key)
        require(isinstance(body,str) and len(body)<=24*1024*1024, 'Bounded base64 evidence bytes required')
        try: raw=base64.b64decode(body,validate=True)
        except (binascii.Error,ValueError) as exc: raise ContractError('Invalid base64 evidence') from exc
        require(digest(raw)==key, 'Evidence hash mismatch; original bytes required')
        decoded[key]=raw
    def read(key):
        valid_hash(key)
        require(key in decoded, 'Missing capture evidence record')
        return decoded[key]
    def record(key): return decode_json(read(key),max_bytes=16*1024*1024)
    manifest=record(value['export_manifest_hash']);receipt=record(value['receipt_hash'])
    try:
        require(manifest['capture_receipt_hash']==value['receipt_hash'], 'Wrong capture receipt identity')
        request=record(receipt['request_hash'])
        required={value['export_manifest_hash'],value['receipt_hash'],receipt['request_hash'],receipt['plan_hash'],
                  receipt['inspection_hash'],request['profile_record_hash'],request['spec_hash'],request['style_hash'],
                  *(item['content_hash'] for item in receipt['artifacts']),
                  *(item['content_hash'] for item in manifest['files']),*request['reference_hashes']}
        if 'index_snapshot_id' in request: required.add(request['index_snapshot_id'])
    except (KeyError,TypeError) as exc: raise ContractError('Incomplete capture evidence closure') from exc
    require(set(decoded)==required, 'Missing or unrelated evidence records')
    class ReadOnlyBundle:
        def read(self,key): return read(key)
    _validate_capture(ReadOnlyBundle(),value['receipt_hash'])
    for key,raw in decoded.items(): require(store.put(raw)==key, 'CAS identity mismatch')
    return {'status':'OK','outcome':'NOT_RUN','receipt_hash':value['receipt_hash'],
            'export_manifest_hash':value['export_manifest_hash'],'objects':len(decoded)}


def registry(root: Path, jdk: Path, gradle_home: Path):
    require((jdk/'bin/java').is_file(), 'Explicit local JDK required')
    return {'workspace':str(root.resolve()),'allow_gradle':True,'wrapper_sha256':file_hash(root/'gradlew'),
            'allowed_kinds':['compile','export'],'build_outputs':[JAR,'build/classes/java/main'], 'build_artifact':'build/classes/java/main',
            'remaining_launches':0,'runtime_config_files':[], 'timeout_seconds':1800,'max_log_bytes':16*1024*1024,
            'environment':{'JAVA_HOME':str(jdk.resolve()),'PATH':str(jdk.resolve()/'bin')+os.pathsep+os.environ['PATH'],
                           'GRADLE_USER_HOME':str(gradle_home.resolve())}}


def build_only(root: Path, evidence: Path, jdk: Path, gradle_home: Path, *, request_prefix: str,
               asset_store: Store, asset_manifest_hash: str, registered: dict | None = None):
    root=root.resolve(); _check_parent(root)
    origin=validate_imported_resources(root,asset_store,asset_manifest_hash)
    evidence.mkdir(parents=True,exist_ok=True)
    store=Store(evidence/'cas')
    if registered is None: registered=registry(root,jdk,gradle_home)
    require(Path(registered['workspace']).resolve()==root and registered.get('allowed_kinds')==['compile','export']
            and registered.get('remaining_launches')==0, 'Only the registered build-only workspace is accepted')
    (evidence/'registry.json').write_bytes(canonical(registered))
    source=workspace_fingerprint(root)
    (evidence/'inputs.json').write_bytes(canonical([{'path':p.relative_to(root).as_posix(),'sha256':file_hash(p)} for p in _inputs(root)]))
    results={}
    for phase in ('compile','export'):
        result=execution.execute(store,registered,kind=phase,request_id=request_prefix+'-'+phase)
        results[phase]=result
        (evidence/(phase+'.json')).write_bytes(canonical(result))
        if result.get('log_hash'): (evidence/(phase+'.log')).write_bytes(store.read(result['log_hash']))
        print(phase,result.get('outcome'),flush=True)
        require(result.get('outcome')=='PASS', phase+' failed; inspect the retained receipt/log before retrying')
    require(validate_imported_resources(root,asset_store,asset_manifest_hash)==origin, 'Captured asset identity changed during build')
    manifest=store.json(results['export']['outputs'][0]['manifest_hash'])
    require(all(manifest.get(k)==v for k,v in TARGET.items()), 'Resolved target differs from pinned pilot')
    require(manifest['dirty_hash']==source and workspace_fingerprint(root)==source, 'Inputs changed; recapture required')
    profile=capture_profile(manifest,root,store)
    snapshot=index.prepare_index(profile,store)
    (evidence/'profile.json').write_bytes(canonical(profile)); (evidence/'index.json').write_bytes(canonical(snapshot))
    artifact=root/JAR
    with zipfile.ZipFile(artifact) as jar:
        names=jar.namelist()
        require(len(names)==len(set(names)), 'Duplicate packaged entries')
        inventory=[{'path':name,'sha256':digest(jar.read(name)),'size_bytes':len(jar.read(name))} for name in sorted(names) if not name.endswith('/')]
        required={'org/kneekura/staff/StaffMod.class','org/kneekura/staff/CelestialStaffItem.class',
                  'assets/kneekura/models/item/celestial_staff.json','assets/kneekura/textures/item/celestial_staff.png'}
        require(required<=set(names), 'Staff class or resource missing from packaged JAR')
        for entry in origin['files']:
            require(digest(jar.read(entry['path']))==entry['content_hash'],
                    'Packaged resource differs from original captured asset bytes')
    (evidence/'jar-inventory.json').write_bytes(canonical(inventory))
    registered['build_receipt_hash']=results['compile']['receipt_hash']
    (evidence/'registry.json').write_bytes(canonical(registered))
    summary={'schema_version':1,'outcome':'PASS','assertion_domain':'compile_and_packaging_only',
             **TARGET,'source_generation':source,'jar_sha256':file_hash(artifact),'captured_asset':origin,
             'compile_receipt_hash':results['compile']['receipt_hash'],'export_receipt_hash':results['export']['receipt_hash'],
             'profile_id':profile['profile_id'],'index_snapshot_id':snapshot['index_snapshot_id'],
             'runtime_artifact_path':registered['build_artifact'],
             'runtime_artifact_hash':next(item['content_hash'] for item in results['compile']['outputs']
                                          if item['path']==registered['build_artifact']),
             'asset_resource_hashes':[i for i in inventory if i['path'].startswith('assets/kneekura/')],
             'handler_gametest':'NOT_RUN','runtime_client_handler_mutation':'NOT_RUN','physical_right_click':'NOT_RUN','rendering':'NOT_RUN','synchronization':'NOT_RUN',
             'launches_during_build':0,'eula_written_by_build':False}
    (evidence/'summary.json').write_bytes(canonical(summary)); return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True); parser.add_argument('--configure',action='store_true')
    parser.add_argument('--capture-bundle',type=Path)
    parser.add_argument('--asset-store',type=Path); parser.add_argument('--asset-manifest'); parser.add_argument('--asset-directory',type=Path)
    parser.add_argument('--evidence',type=Path); parser.add_argument('--jdk',type=Path); parser.add_argument('--gradle-home',type=Path)
    parser.add_argument('--request-prefix',default='staff-build-v1')
    args=parser.parse_args()
    if args.capture_bundle:
        require(args.asset_store is not None, 'Explicit asset CAS destination required')
        hydrated=import_evidence_bundle(args.capture_bundle,Store(args.asset_store))
        if args.asset_manifest: require(args.asset_manifest==hydrated['export_manifest_hash'],'Explicit manifest differs from bundle')
        args.asset_manifest=hydrated['export_manifest_hash']
    if args.configure: print(json.dumps(configure(args.workspace)))
    if args.asset_manifest and args.asset_directory:
        result=import_asset(Store(args.asset_store),args.asset_manifest,args.asset_directory,args.workspace)
        print(json.dumps(result))
        if args.evidence:
            args.evidence.mkdir(parents=True,exist_ok=True);create_file(args.evidence/'asset-import.json',canonical(result))
    if args.jdk:
        require(args.evidence and args.gradle_home and args.asset_store and args.asset_manifest,
                'Evidence, private Gradle home, and original asset CAS/manifest are required')
        print(json.dumps(build_only(args.workspace,args.evidence,args.jdk,args.gradle_home,request_prefix=args.request_prefix,
                                    asset_store=Store(args.asset_store),asset_manifest_hash=args.asset_manifest)))

if __name__=='__main__': main()
