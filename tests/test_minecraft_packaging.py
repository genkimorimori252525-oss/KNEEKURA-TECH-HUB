"""Package declarations and isolated installed-layout Core integration checks."""
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def test_minecraft_entrypoint_and_observer_are_declared_in_wheel():
    config=tomllib.loads(Path('pyproject.toml').read_text())
    assert config['project']['scripts'].get('kneekura-minecraft')=='kneekura_tech_hub.minecraft.__main__:main'
    include=config['tool']['hatch']['build']['targets']['wheel']['force-include']
    assert include['departments/minecraft/mod-ai/forge-observer']=='kneekura_tech_hub/minecraft/resources/forge-observer'
    root=Path('departments/minecraft/mod-ai/forge-observer')
    assert (root/'src/main/resources/META-INF/mods.toml').is_file()
    assert {path.name for path in root.rglob('*.java')} == {
        'BridgeTransport.java', 'ClientProbe.java', 'ForgeObserver.java', 'RunLedger.java',
        'LinuxClientIdentity.java', 'StaffStateQuery.java',
        'DedicatedClientObserver.java', 'DedicatedSession.java', 'StaffStateCapture.java',
        'StaffPacketTrace.java', 'StaffTrace.java',
        'DependencyInventory.java', 'TargetDependency.java', 'U04HydraProbe.java',
    }


def test_gradle_scripts_are_present_and_ci_is_not_a_dependency():
    resources=Path('src/kneekura_tech_hub/minecraft/resources')
    assert (resources/'kneekura-inputs.init.gradle').is_file()
    assert (resources/'kneekura-run.init.gradle').is_file()
    config=tomllib.loads(Path('pyproject.toml').read_text())
    assert config['project']['dependencies']==['jsonschema>=4.23,<5']


def test_observer_resource_pack_metadata_matches_minecraft_1_20_1():
    """The separate dev observer pack needs the same format as the staff pilot."""
    path=Path('departments/minecraft/mod-ai/forge-observer/src/main/resources/pack.mcmeta')
    assert path.is_file(), 'Observer resource pack is missing pack.mcmeta'
    pack=json.loads(path.read_text())['pack']
    assert type(pack['pack_format']) is int and pack['pack_format']==15
    assert isinstance(pack['description'],str) and pack['description'].strip()


def test_installed_package_stages_against_packaged_core_schema_and_policy(tmp_path):
    """Materialize declared wheel content without a backend or network prerequisite."""
    repository=Path.cwd()
    installed=tmp_path/'site-packages'; installed.mkdir()
    shutil.copytree(repository/'src/kneekura_tech_hub',installed/'kneekura_tech_hub',
                    ignore=shutil.ignore_patterns('__pycache__'))
    config=tomllib.loads((repository/'pyproject.toml').read_text())
    includes=config['tool']['hatch']['build']['targets']['wheel']['force-include']
    for source,destination in includes.items():
        shutil.copytree(repository/source,installed/destination,dirs_exist_ok=True)
    outside=tmp_path/'unrelated-working-directory'; outside.mkdir()
    script=r'''
import contextlib
import io
import json
import sys
from pathlib import Path
import kneekura_tech_hub
from kneekura_tech_hub import validator
from kneekura_tech_hub.bundle import load_bundle_schema, preflight_bundle
from kneekura_tech_hub.minecraft import task_context, task_routing
from kneekura_tech_hub.minecraft.__main__ import main
from kneekura_tech_hub.minecraft.core_bridge import stage_bundle
from kneekura_tech_hub.minecraft.index import prepare_index
from kneekura_tech_hub.minecraft.storage import Store, capture_profile

installed=Path(sys.argv[1]).resolve()
assert Path(kneekura_tech_hub.__file__).is_relative_to(installed)
for module in (task_context, task_routing):
    assert Path(module.__file__).is_relative_to(installed)
    assert Path(module.__file__).is_file()
observer_resources=Path(kneekura_tech_hub.__file__).parent/'minecraft/resources/forge-observer/src/main/resources'
pack_path=observer_resources/'pack.mcmeta'
assert pack_path.is_file(), 'Installed observer resource pack is missing pack.mcmeta'
assert json.loads(pack_path.read_text())['pack']['pack_format']==15
for loader in (validator.load_schema, validator.load_review_decision_schema,
               validator.load_source_selection_decision_schema,
               validator.load_source_acquisition_authorization_schema,
               validator.load_source_acquisition_execution_schema,
               validator.load_source_acquisition_commit_schema, load_bundle_schema):
    assert loader()['$schema'].endswith('/draft/2020-12/schema')
assert validator.load_policy()['license_unknown_max_acquisition']=='metadata-only'
root=Path.cwd(); (root/'src').mkdir()
(root/'src/Example.java').write_text('class Example { int attack=1; }')
manifest={'schema_version':1,'minecraft':'1.20.1','loader':'forge','loader_version':'47.4.0',
          'java_major':17,'namespace':'mojmap','physical_side':'server','logical_side':'server',
          'track':'ANCHOR','workspace_revision':'a'*40,'dirty_hash':'b'*64,
          'toolchain':{'gradle':'8.8','forgegradle':'6.0.24'},
          'roots':[{'id':'own','path':'src','kind':'directory','scope':'runtime',
                    'role':'source','namespace':'mojmap','stage':'workspace',
                    'classloader':'unknown','track':'ANCHOR'}]}
store=Store(root/'cas'); profile=capture_profile(manifest,root,store)
index=prepare_index(profile,store)['index_snapshot_id']
request={'schema_version':1,'intent':'edit_code','goal':'Inspect the captured attack field',
         'constraints':[],'acceptance':['Keep the exact captured target']}
context=task_context.prepare_task_context(store,request,index_id=index)
assert context['status']=='OK'
assert context['target']['index_snapshot_id']==index
assert tuple(row['id'] for row in context['capabilities'])==task_routing.CAPABILITY_IDS
assert context['next_actions'][0]['operation_id']=='research.search'
request_file=root/'task.json'; request_file.write_text(json.dumps(request))
for action in ('prepare','capabilities'):
    output=io.StringIO()
    with contextlib.redirect_stdout(output):
        code=main(['--store',str(store.root),'task',action,'--request',str(request_file),
                   '--index',index])
    response=json.loads(output.getvalue())
    assert code==0 and response['status']=='OK'
    assert response['target']==context['target']
    assert response['capabilities']==context['capabilities']
    assert response['results']==[] and response['next_cursor'] is None
    assert response['request_id']
    if action=='prepare':
        assert response['next_actions']==context['next_actions']
        assert response['kind']=='minecraft_task_context'
    else:
        assert 'next_actions' not in response and 'task' not in response
result=stage_bundle(store,index,[profile['documents'][0]['document_id']],
                    summary='Observed installed-package fixture',actor={'actor_type':'ai'},
                    source_licenses={'own':{'state':'KNOWN','declared_expression':'MIT'}})
assert len(preflight_bundle(store.json(result['bundle_hash'])))==4
assert result['canonical_writes']==0
print(json.dumps({'status':result['status'],'canonical_writes':result['canonical_writes']}))
'''
    result=subprocess.run([sys.executable,'-c',script,str(installed)],cwd=outside,
                          env=dict(os.environ,PYTHONPATH=str(installed),PYTHONNOUSERSITE='1'),
                          text=True,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)=={'status':'OK','canonical_writes':0}
    observer_pack=Path('src/main/resources/pack.mcmeta')
    assert (installed/'kneekura_tech_hub/minecraft/resources/forge-observer'/observer_pack).read_bytes()==(
        repository/'departments/minecraft/mod-ai/forge-observer'/observer_pack).read_bytes()
    for directory in ('schemas','governance'):
        for source in (repository/directory).rglob('*.json'):
            packaged=installed/'kneekura_tech_hub/resources'/source.relative_to(repository)
            assert packaged.read_bytes()==source.read_bytes()


def test_explicit_schema_and_policy_paths_keep_precedence(tmp_path):
    from kneekura_tech_hub import validator
    from kneekura_tech_hub.bundle import load_bundle_schema
    custom=tmp_path/'override.json'; custom.write_text('{"explicit_override":true}')
    for loader in (validator.load_schema, validator.load_review_decision_schema,
                   validator.load_source_selection_decision_schema,
                   validator.load_source_acquisition_authorization_schema,
                   validator.load_source_acquisition_execution_schema,
                   validator.load_source_acquisition_commit_schema,
                   validator.load_policy, load_bundle_schema):
        assert loader(custom)=={'explicit_override':True}