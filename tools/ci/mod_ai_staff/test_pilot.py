"""Build-only pilot boundaries. These tests never launch Minecraft."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / 'tests'))
from test_minecraft_asset_export import capture as capture_fixture
from kneekura_tech_hub.minecraft.asset_contract import prepare_request
from kneekura_tech_hub.minecraft.asset_export import materialize_asset
from kneekura_tech_hub.minecraft.storage import Store, ContractError, capture_profile, canonical


def api():
    path = ROOT / 'pilot.py'
    assert path.exists(), 'The safe build-only staff pilot is not implemented'
    spec = importlib.util.spec_from_file_location('staff_pilot', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def exported(tmp_path):
    source = tmp_path / 'source'; source.mkdir(); (source / 'Source.java').write_text('class Source {}')
    store = Store(tmp_path / 'cas')
    manifest = dict(schema_version=1, minecraft='1.20.1', loader='forge', loader_version='47.4.6',
                    java_major=17, namespace='mojmap', physical_side='client', logical_side='client',
                    track='ANCHOR', workspace_revision='a'*40, dirty_hash='b'*64, toolchain={},
                    roots=[dict(id='own', path=str(source), kind='directory', scope='client',
                                role='source', namespace='mojmap', stage='workspace', classloader='unknown', track='ANCHOR')])
    profile = capture_profile(manifest, tmp_path, store)
    spec = dict(schema_version=1, asset_id='kneekura:celestial_staff', asset_kind='java_item',
                visual_brief='Golden staff.', style=dict(texture_size=[32,32], palette={'metal':'#d4af37'},
                pixel_art=True, shading='minecraft'), reference_hashes=[], required_views=['front','left','back'])
    request = prepare_request(store, profile=profile, spec=spec)['request_hash']
    plan = dict(schema_version=1, request_hash=request, fill='#d4af37', cubes=[
        dict(name='staff', **{'from':[7,0,7], 'to':[9,16,9]}, uv=[0,0,4,4])])
    store, capture, _ = capture_fixture.__wrapped__((store, request, None, plan))
    parent = tmp_path / 'exports'; parent.mkdir()
    result = materialize_asset(store, capture, parent=parent)
    return store, result


def mdklike(tmp_path):
    root=tmp_path/'mdk'; root.mkdir()
    (root/'gradlew').write_text('#!/bin/sh\nexit 0\n')
    (root/'gradle.properties').write_text('minecraft_version=1.20.1\nforge_version=47.4.6\nmod_id=examplemod\nmod_version=1.0.0\n')
    return root


def snapshot(path):
    return {str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()}


def test_imports_only_validated_model_and_texture(exported,tmp_path):
    store,export=exported; root=mdklike(tmp_path); api().configure(root)
    out=api().import_asset(store,export['manifest_hash'],Path(export['directory']),root)
    assert out['outcome']=='NOT_RUN'
    assert {x['path'] for x in out['files']}=={
        'src/main/resources/assets/kneekura/models/item/celestial_staff.json',
        'src/main/resources/assets/kneekura/textures/item/celestial_staff.png'}
    assert not list(root.rglob('*.bbmodel'))
    assert not list(root.rglob('eula.txt'))
    assert out['source_generation_before'] != out['source_generation_after']
    before=snapshot(root)
    with pytest.raises(ContractError,match='exist|overwrite'):
        api().import_asset(store,export['manifest_hash'],Path(export['directory']),root)
    assert snapshot(root)==before


@pytest.mark.parametrize('fault',['traversal','missing','duplicate','wrong_hash','edited_export','wrong_asset','wrong_target','wrong_receipt','symlink_export','symlink_destination'])
def test_import_refuses_invalid_package_before_writing(exported,tmp_path,fault):
    store,export=exported; root=mdklike(tmp_path); api().configure(root)
    directory=Path(export['directory']); manifest=deepcopy(store.json(export['manifest_hash']))
    if fault=='traversal': manifest['files'][0]['path']='../../evil.json'
    elif fault=='missing': manifest['files'].pop()
    elif fault=='duplicate': manifest['files'].append(manifest['files'][0])
    elif fault=='wrong_hash': manifest['files'][0]['content_hash']='a'*64
    elif fault=='edited_export': (directory/manifest['files'][0]['path']).write_text('{}')
    elif fault=='wrong_asset': manifest['asset_id']='evil:staff'
    elif fault=='wrong_target': manifest['target']['loader_version']='47.4.0'
    elif fault=='wrong_receipt': manifest['capture_receipt_hash']='b'*64
    elif fault=='symlink_export':
        link=tmp_path/'export-link'; link.symlink_to(directory,target_is_directory=True); directory=link
    elif fault=='symlink_destination':
        other=tmp_path/'other';other.mkdir();(root/'src/main/resources/assets/kneekura/models').symlink_to(other,target_is_directory=True)
    h=store.put_json(manifest)
    if fault not in ('edited_export','symlink_export'):
        (directory/'manifest.json').write_bytes(canonical(manifest))
    before=snapshot(root)
    with pytest.raises((ContractError,OSError)):
        api().import_asset(store,h,directory,root)
    assert snapshot(root)==before


def test_configure_refuses_existing_source_and_wrong_target(tmp_path):
    root=mdklike(tmp_path); (root/'src').mkdir(); before=snapshot(root)
    with pytest.raises(ContractError): api().configure(root)
    assert snapshot(root)==before
    (root/'src').rmdir(); (root/'gradle.properties').write_text('minecraft_version=1.20.1\nforge_version=47.4.0\n')
    before=snapshot(root)
    with pytest.raises(ContractError): api().configure(root)
    assert snapshot(root)==before


def test_policy_on_jdk17_without_starting_minecraft(tmp_path):
    source=ROOT/'java/org/kneekura/staff/StaffUsePolicy.java'
    assert source.exists(), 'The predeclared staff policy is not implemented'
    jdk=Path(__import__('os').environ.get('JAVA_HOME', str(REPO.parent/'provider-acceptance/jdk-17.0.20.1+1')))
    if not (jdk/'bin/javac').exists(): pytest.skip('Explicit JDK17 required for standalone policy check')
    out=tmp_path/'classes'; out.mkdir()
    result=subprocess.run([str(jdk/'bin/javac'),'--release','17','-d',str(out),str(source),
                           str(ROOT/'testjava/org/kneekura/staff/PolicyAssertions.java')],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    result=subprocess.run([str(jdk/'bin/java'),'-cp',str(out),'org.kneekura.staff.PolicyAssertions'],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert result.stdout.strip()=='STAFF_POLICY_ASSERTIONS_PASS_NOT_GAMEPLAY'


def test_configure_rejects_symlink_properties_before_source_creation(tmp_path):
    root=mdklike(tmp_path); outside=tmp_path/'outside.properties'
    (root/'gradle.properties').rename(outside); (root/'gradle.properties').symlink_to(outside)
    before=outside.read_bytes()
    with pytest.raises(ContractError): api().configure(root)
    assert not (root/'src').exists()
    assert outside.read_bytes()==before


def test_capture_bytes_are_revalidated_not_only_manifest(exported,tmp_path):
    store,export=exported;root=mdklike(tmp_path);api().configure(root)
    manifest=store.json(export['manifest_hash'])
    receipt=store.json(manifest['capture_receipt_hash'])
    # A self-consistent edited receipt/manifest must not bypass the capture validator.
    model=store.json(receipt['artifacts'][0]['content_hash'])
    model['elements'][0]['faces']['north']['texture']='#undeclared'
    raw=canonical(model)
    receipt['artifacts'][0].update(content_hash=store.put(raw),size_bytes=len(raw))
    manifest['capture_receipt_hash']=store.put_json(receipt)
    manifest['source_model_hash']=receipt['artifacts'][0]['content_hash']
    h=store.put_json(manifest);directory=Path(export['directory'])
    (directory/'manifest.json').write_bytes(canonical(manifest))
    before=snapshot(root)
    with pytest.raises(ContractError): api().import_asset(store,h,directory,root)
    assert snapshot(root)==before


def evidence_bundle(store,export):
    import base64
    h=export['manifest_hash'];m=store.json(h);r=store.json(m['capture_receipt_hash']);q=store.json(r['request_hash'])
    keys={h,m['capture_receipt_hash'],r['request_hash'],r['plan_hash'],r['inspection_hash'],
          q['profile_record_hash'],q['spec_hash'],q['style_hash'],
          *(x['content_hash'] for x in r['artifacts']),*(x['content_hash'] for x in m['files']),*q['reference_hashes']}
    if q.get('index_snapshot_id'):keys.add(q['index_snapshot_id'])
    return {'schema_version':1,'receipt_hash':m['capture_receipt_hash'],'export_manifest_hash':h,'encoding':'base64',
            'objects':{k:base64.b64encode(store.read(k)).decode() for k in keys}}


def test_imports_original_bounded_evidence_without_reconstruction(exported,tmp_path):
    store,export=exported;bundle=evidence_bundle(store,export);path=tmp_path/'evidence.json';path.write_bytes(canonical(bundle))
    destination=Store(tmp_path/'local-cas');module=api()
    assert hasattr(module,'import_evidence_bundle'), 'Original-byte evidence import is not implemented'
    result=module.import_evidence_bundle(path,destination)
    assert result['export_manifest_hash']==export['manifest_hash']
    assert result['receipt_hash']==bundle['receipt_hash']
    for key in bundle['objects']:assert destination.read(key)==store.read(key)
    root=mdklike(tmp_path);module.configure(root)
    assert module.import_asset(destination,export['manifest_hash'],Path(export['directory']),root)['outcome']=='NOT_RUN'


@pytest.mark.parametrize('fault',['edited_bytes','unknown_field','missing_record','extra_record','invalid_base64','wrong_receipt'])
def test_bad_evidence_bundle_does_not_write_to_cas(exported,tmp_path,fault):
    import base64
    store,export=exported;bundle=evidence_bundle(store,export)
    if fault=='edited_bytes':bundle['objects'][bundle['receipt_hash']]=base64.b64encode(b'{}').decode()
    elif fault=='unknown_field':bundle['secret']='unexpected'
    elif fault=='missing_record':bundle['objects'].pop(bundle['receipt_hash'])
    elif fault=='extra_record':
        key=store.put(b'unrelated');bundle['objects'][key]=base64.b64encode(b'unrelated').decode()
    elif fault=='invalid_base64':bundle['objects'][bundle['receipt_hash']]='@@'
    else:bundle['receipt_hash']=bundle['export_manifest_hash']
    path=tmp_path/'bad-evidence.json';path.write_bytes(canonical(bundle));destination=Store(tmp_path/'local-cas')
    before=snapshot(destination.root);module=api()
    assert hasattr(module,'import_evidence_bundle'), 'Original-byte evidence import is not implemented'
    with pytest.raises(ContractError):module.import_evidence_bundle(path,destination)
    assert snapshot(destination.root)==before


def test_prebuild_resource_validation_uses_immutable_capture(exported,tmp_path):
    store,export=exported;root=mdklike(tmp_path);module=api();module.configure(root)
    module.import_asset(store,export['manifest_hash'],Path(export['directory']),root)
    assert hasattr(module,'validate_imported_resources'), 'Build is not bound to immutable capture evidence'
    origin=module.validate_imported_resources(root,store,export['manifest_hash'])
    assert origin['manifest_hash']==export['manifest_hash']
    assert origin['capture_receipt_hash']==store.json(export['manifest_hash'])['capture_receipt_hash']
    target=root/'src/main/resources/assets/kneekura/models/item/celestial_staff.json'
    target.write_bytes(b'{}')
    with pytest.raises(ContractError,match='captured'):
        module.validate_imported_resources(root,store,export['manifest_hash'])


def test_edited_after_import_rejected_even_when_jar_matches_mutable_files(exported,tmp_path):
    import inspect
    import zipfile
    store,export=exported;root=mdklike(tmp_path);module=api();module.configure(root)
    module.import_asset(store,export['manifest_hash'],Path(export['directory']),root)
    target=root/'src/main/resources/assets/kneekura/models/item/celestial_staff.json';target.write_bytes(b'{}')
    jar=root/module.JAR;jar.parent.mkdir(parents=True)
    with zipfile.ZipFile(jar,'w') as z:
        for path in (root/'src/main/resources').rglob('*'):
            if path.is_file():z.writestr(path.relative_to(root/'src/main/resources').as_posix(),path.read_bytes())
    wrapper=root/'gradlew';wrapper.write_text('#!/bin/sh\nprintf called > should-not-execute\nexit 1\n');wrapper.chmod(0o700)
    jdk=tmp_path/'jdk';(jdk/'bin').mkdir(parents=True);(jdk/'bin/java').write_bytes(b'')
    evidence=tmp_path/'build-evidence'
    assert 'asset_store' in inspect.signature(module.build_only).parameters, 'Build does not require original asset evidence'
    with pytest.raises(ContractError,match='captured'):
        module.build_only(root,evidence,jdk,tmp_path/'gradle-home',request_prefix='must-not-execute',
                          asset_store=store,asset_manifest_hash=export['manifest_hash'])
    assert not (root/'should-not-execute').exists()
    assert not evidence.exists()


def test_registry_separates_userdev_classes_from_reobfuscated_package(tmp_path):
    root=mdklike(tmp_path);jdk=tmp_path/'jdk';(jdk/'bin').mkdir(parents=True);(jdk/'bin/java').write_bytes(b'')
    registered=api().registry(root,jdk,tmp_path/'gradle-home')
    assert registered['build_outputs']==[api().JAR,'build/classes/java/main']
    assert registered['build_artifact']=='build/classes/java/main'
    assert registered['allowed_kinds']==['compile','export'] and registered['remaining_launches']==0
