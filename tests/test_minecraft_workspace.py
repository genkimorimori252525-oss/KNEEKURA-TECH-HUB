"""The exporter/importer must never infer a resolved runtime from build text."""
from pathlib import Path
import importlib
import json
import subprocess
import pytest
from kneekura_tech_hub.minecraft.storage import Store, ContractError, digest


def api():
    spec = importlib.util.find_spec('kneekura_tech_hub.minecraft.workspace')
    assert spec is not None, 'resolved workspace adapter is not implemented'
    return importlib.import_module(spec.name)


@pytest.fixture
def project(tmp_path):
    p = tmp_path / 'mod with spaces'; p.mkdir()
    (p / 'gradle.properties').write_text('minecraft_version=1.20.1\nforge_version=47.4.0\n')
    (p / 'build.gradle').write_text("plugins { id 'net.minecraftforge.gradle' version '[6.0,6.2)' }\njava.toolchain.languageVersion = JavaLanguageVersion.of(17)\n")
    (p / 'gradle/wrapper').mkdir(parents=True)
    (p / 'gradle/wrapper/gradle-wrapper.properties').write_text('distributionUrl=https\\://services.gradle.org/distributions/gradle-8.8-bin.zip\n')
    (p / 'src/main/java/example').mkdir(parents=True)
    (p / 'src/main/java/example/Mob.java').write_text('package example; class Mob {}')
    (p / 'src/main/resources').mkdir(parents=True)
    (p / 'src/main/resources/config.json').write_text('{"ai":true}')
    return p


def export_data(p):
    w = api()
    return {'schema_version':1, 'format':'kneekura.forge-inputs.v1', 'workspace':str(p.resolve()),
            'source_fingerprint':w.workspace_fingerprint(p),
            'configuration_fingerprint':w.configuration_fingerprint(p),
            'minecraft':'1.20.1', 'loader':'forge', 'loader_version':'47.4.0',
            'namespace':'mojmap', 'java_major':17,
            'gradle_version':'8.8', 'forgegradle_version':'6.0.24',
            'mappings':{'channel':'official','version':'1.20.1'},
            'artifacts':[], 'unresolved':[],
            'source_roots':['src/main/java'], 'resource_roots':['src/main/resources'],
            'output_roots':['build/classes/java/main'], 'toolchain':{'language_version':17}}


def test_passive_inventory_does_not_run_gradle(project):
    (project / 'gradlew').write_text('#!/bin/sh\ntouch MUST_NOT_RUN\n')
    p = api().discover_workspace(project)
    assert not (project / 'MUST_NOT_RUN').exists()
    assert p['minecraft'] == '1.20.1' and p['loader_version'] == '47.4.0'
    assert p['dependency_resolution'] == 'UNKNOWN'
    assert p['java_major'] == 17
    assert any(r['role'] == 'resources' for r in p['roots'])


def test_export_uses_resolved_versions_not_declared_range(project, tmp_path):
    (project / 'gradle.properties').write_text('minecraft_version=1.20.1\nforge_version=[47,)\n')
    data = export_data(project)
    manifest = api().import_resolved(data, project)
    assert manifest['loader_version'] == '47.4.0'
    assert manifest['dependency_resolution'] == 'GRADLE_RESOLVED_NOT_LAUNCHED'
    assert manifest['mappings']['channel'] == 'official'


def test_resolved_classpath_order_scope_and_unknown_namespace(project):
    data = export_data(project)
    for name in ('a.jar','b.jar'):
        (project / name).write_bytes(b'test')
    data['artifacts'] = [{'path':str(project / n), 'scope':s, 'namespace':ns,
                           'coordinate':n,'sha256':digest(b'test')} for n,s,ns in
                          [('b.jar','runtime','mojmap'), ('a.jar','runtime','srg'), ('b.jar','compile','mojmap')]]
    manifest = api().import_resolved(data, project)
    roots = [r for r in manifest['roots'] if r['role'] == 'dependency']
    assert [Path(r['path']).name for r in roots] == ['b.jar','a.jar','b.jar']
    assert [r['scope'] for r in roots] == ['runtime','runtime','compile']
    assert roots[1]['namespace'] == 'srg'
    assert len({r['id'] for r in roots}) == 3


def test_stale_source_is_visible_and_export_stale_config_rejected(project):
    w = api(); data = export_data(project)
    (project / 'src/main/java/example/Mob.java').write_text('package example; class Mob { int changed; }')
    m = w.import_resolved(data, project)
    assert m['source_generation'] != data['source_fingerprint']
    assert m['binary_generation']['status'] == 'UNVERIFIED'
    (project / 'build.gradle').write_text('changed dependency configuration')
    with pytest.raises(ContractError, match='configuration'):
        w.import_resolved(data, project)


def test_artifact_drift_is_not_silently_rehashed(project):
    data = export_data(project)
    (project / 'a.jar').write_bytes(b'new')
    data['artifacts'] = [{'path':str(project/'a.jar'),'scope':'runtime','namespace':'mojmap',
                           'coordinate':'x:y:1','sha256':digest(b'old')}]
    with pytest.raises(ContractError, match='artifact'):
        api().import_resolved(data, project)


@pytest.mark.parametrize('field,value', [('minecraft','1.21.1'),('loader','neoforge'),
                                        ('loader_version','47.4.x'),('namespace','parchment')])
def test_anchor_export_rejects_wrong_or_unpinned_environment(project, field, value):
    data = export_data(project); data[field] = value
    with pytest.raises(ContractError): api().import_resolved(data, project)


def test_unresolved_dependencies_make_profile_partial(project, tmp_path):
    w = api(); data = export_data(project)
    data['output_roots'] = []
    data['unresolved'] = [{'scope':'runtime','coordinate':'missing:mod:1','reason':'not found'}]
    m = w.import_resolved(data, project)
    from kneekura_tech_hub.minecraft.storage import capture_profile
    p = capture_profile(m, project, Store(tmp_path/'cas'))
    assert not p['coverage']['complete']
    assert any('missing:mod:1' in str(x) for x in p['coverage']['unresolved_roots'])


def test_source_and_resource_generation_changes_but_build_cache_does_not(project):
    w = api(); first = w.workspace_fingerprint(project)
    (project/'build').mkdir(); (project/'build/log.txt').write_text('incidental')
    assert w.workspace_fingerprint(project) == first
    (project/'src/main/resources/config.json').write_text('{"ai":false}')
    assert w.workspace_fingerprint(project) != first


def test_profile_root_cannot_escape_through_source_export(project, tmp_path):
    data = export_data(project); data['source_roots'] = ['../other-secret-directory']
    with pytest.raises(ContractError, match='workspace'):
        api().import_resolved(data, project)


def test_gradle_plan_requires_explicit_registered_workspace(project):
    w = api()
    with pytest.raises(ContractError):
        w.export_plan(project, {'workspace':str(project.parent), 'allow_gradle':True}, project/'out.json')
    plan = w.export_plan(project, {'workspace':str(project), 'allow_gradle':True}, project/'out.json')
    assert 'kneekuraExportInputs' in plan['argv']
    assert '-I' in plan['argv']
    assert plan['outcome'] == 'NOT_RUN'
    assert all(isinstance(a,str) for a in plan['argv'])
