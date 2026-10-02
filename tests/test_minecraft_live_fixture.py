"""The disposable integration scenario must configure, not assume, its world."""
import importlib.util
from pathlib import Path
import pytest


def module():
    spec=importlib.util.spec_from_file_location('live_fixture',Path('tools/ci/mod_ai_live.py'))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    assert callable(getattr(m,'prepare_probe_scenario',None)), 'Missing explicit game-world setup'
    return m


def world(tmp_path):
    run=tmp_path/'run'; run.mkdir(); target=run/'gametestserver'; target.mkdir()
    return {'directory':str(run),'world':str(target)}


def test_probe_seed_and_world_are_explicit_and_ids_match_forge_prefix_setting(tmp_path):
    m=module(); w=world(tmp_path)
    scenario=m.prepare_probe_scenario(w)
    text=(Path(w['directory'])/'server.properties').read_text()
    assert 'level-seed=0\n' in text and 'level-name=gametestserver\n' in text
    assert 'server-ip=127.0.0.1\n' in text
    # Forge 1.20.1 PrefixGameTestTemplate(false) also removes the test-name prefix.
    assert scenario['expected_tests']==['bridge']
    assert scenario['expected_required']=={'bridge':True} and scenario['world_seed']==0


def test_probe_never_overwrites_existing_server_configuration(tmp_path):
    m=module(); w=world(tmp_path); config=Path(w['directory'])/'server.properties'
    config.write_text('level-name=valuable\n')
    with pytest.raises(FileExistsError): m.prepare_probe_scenario(w)
    assert config.read_text()=='level-name=valuable\n'


def test_probe_observes_its_exact_entity_not_ambient_mobs():
    import re
    import struct
    import uuid
    m=module()
    assert callable(getattr(m, 'probe_entity_request', None)), 'Missing exact-entity probe selection'
    command, query=m.probe_entity_request()
    requested=uuid.UUID(query['entity_uuids'][0])
    values=[int(v) for v in re.search(r'UUID:\[I;([^\]]+)\]',command)[1].split(',')]
    assert uuid.UUID(bytes=struct.pack('>iiii',*values))==requested
    assert query['dimension']=='minecraft:overworld' and query['limit']==1
    assert command.startswith('summon minecraft:pig ') and 'NoGravity:1b' in command
