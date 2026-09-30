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
    }


def test_gradle_scripts_are_present_and_ci_is_not_a_dependency():
    resources=Path('src/kneekura_tech_hub/minecraft/resources')
    assert (resources/'kneekura-inputs.init.gradle').is_file()
    assert (resources/'kneekura-run.init.gradle').is_file()
    config=tomllib.loads(Path('pyproject.toml').read_text())
    assert config['project']['dependencies']==['jsonschema>=4.23,<5']


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
import json
import sys
from pathlib import Path
import kneekura_tech_hub
from kneekura_tech_hub import validator
from kneekura_tech_hub.bundle import load_bundle_schema, preflight_bundle
from kneekura_tech_hub.minecraft.core_bridge import stage_bundle
from kneekura_tech_hub.minecraft.index import prepare_index
from kneekura_tech_hub.minecraft.storage import Store, capture_profile

installed=Path(sys.argv[1]).resolve()
assert Path(kneekura_tech_hub.__file__).is_relative_to(installed)
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
