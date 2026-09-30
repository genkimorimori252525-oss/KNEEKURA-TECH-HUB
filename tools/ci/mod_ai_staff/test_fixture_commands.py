"""Offline fixture-only command regression; never downloads, launches or executes a command."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest

from kneekura_tech_hub.minecraft.process import clean_environment
from kneekura_tech_hub.minecraft.storage import ContractError

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
IDENTITIES = {
    'client': {'account_sign_in': False, 'kind': 'local_synthetic_offline_test_identity',
               'name': 'KneekuraTest', 'uuid': '57e9ec72-85ae-3dd2-8fb4-2672e58b0ffe'},
    'control': {'account_sign_in': False, 'kind': 'local_synthetic_offline_test_identity',
                'name': 'KneekuraControl', 'uuid': '59503c28-8713-3baf-bfd8-8c411b004b66'},
}


def api():
    path = HERE/'fixture_commands.py'
    assert path.is_file(), 'UUID-bound disposable player command definition is missing'
    spec = importlib.util.spec_from_file_location('staff_fixture_commands', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_fixed_commands_preserve_both_exact_approved_identity_bindings():
    value=json.loads(json.dumps(IDENTITIES));before=json.dumps(value,sort_keys=True)
    commands=api().build_creative_commands(value)
    assert commands == {
        'creative_invoker': 'execute as 57e9ec72-85ae-3dd2-8fb4-2672e58b0ffe run gamemode creative @s',
        'creative_control': 'execute as 59503c28-8713-3baf-bfd8-8c411b004b66 run gamemode creative @s',
    }
    assert json.dumps(value,sort_keys=True)==before
    commands['creative_invoker']='changed'
    assert api().build_creative_commands(value)['creative_invoker'].endswith('run gamemode creative @s')


@pytest.mark.parametrize('fault',['swap','swap_uuids','wrong_uuid','uppercase_uuid','wrong_name','selector_name','signed_in',
                                  'zero_instead_of_false','unknown_field','extra_role','missing_role','non_dict'])
def test_no_new_identity_arbitrary_selector_or_command_text_is_accepted(fault):
    value=json.loads(json.dumps(IDENTITIES))
    if fault=='swap':value['client'],value['control']=value['control'],value['client']
    elif fault=='swap_uuids':value['client']['uuid'],value['control']['uuid']=value['control']['uuid'],value['client']['uuid']
    elif fault=='wrong_uuid':value['client']['uuid']='00000000-0000-0000-0000-000000000000'
    elif fault=='uppercase_uuid':value['client']['uuid']=value['client']['uuid'].upper()
    elif fault=='wrong_name':value['client']['name']='SomeoneElse'
    elif fault=='selector_name':value['client']['name']='@a run stop'
    elif fault=='signed_in':value['client']['account_sign_in']=True
    elif fault=='zero_instead_of_false':value['client']['account_sign_in']=0
    elif fault=='unknown_field':value['client']['command']='gamemode creative @a'
    elif fault=='extra_role':value['other']=value['control']
    elif fault=='missing_role':del value['control']
    else:value=[]
    with pytest.raises(ContractError):api().build_creative_commands(value)


def parser_inputs():
    configured=os.environ.get('KNEEKURA_STAFF_PARSER_EXPORT')
    path=Path(configured) if configured else REPO.parent/'staff-dedicated-acceptance/server/mdk/build/kneekura/resolved-inputs.json'
    if not path.is_file():
        if configured:pytest.fail('Explicit cached parser export is unavailable')
        pytest.skip('Cached Forge 1.20.1-47.4.6 resolved export required; no download or launch fallback')
    manifest=json.loads(path.read_bytes())
    assert (manifest['format'],manifest['minecraft'],manifest['loader_version'],manifest['java_major'],manifest['namespace'])==(
        'kneekura.forge-inputs.v1','1.20.1','47.4.6',17,'mojmap')
    paths=[];hashes={}
    for row in manifest['artifacts']:
        item=Path(row['path']);assert item.is_file() and not item.is_symlink()
        actual=hashlib.sha256(item.read_bytes()).hexdigest();assert actual==row['sha256'],str(item)
        if item not in paths:paths.append(item);hashes[str(item)]=actual
    minecraft=[p for p in paths if p.name=='forge-1.20.1-47.4.6_mapped_official_1.20.1.jar']
    brigadier=[p for p in paths if p.name=='brigadier-1.1.8.jar']
    assert len(minecraft)==len(brigadier)==1
    jdk=Path(os.environ.get('JAVA_HOME',str(REPO.parent/'provider-acceptance/jdk-17.0.20.1+1')))
    assert (jdk/'bin/java').is_file() and (jdk/'bin/javac').is_file(), 'Explicit JDK17 required'
    return jdk,paths,minecraft[0],hashes


def test_actual_cached_minecraft_and_brigadier_parsers_accept_fix_and_reject_original(tmp_path):
    jdk,paths,minecraft,hashes=parser_inputs()
    commands=api().build_creative_commands(json.loads(json.dumps(IDENTITIES)))
    source=HERE/'testjava/org/kneekura/staff/FixtureCommandParserAssertions.java'
    assert source.is_file(), 'Real Minecraft parser harness missing'
    classes=tmp_path/'classes';classes.mkdir()
    cp=os.pathsep.join(str(p) for p in paths)
    compiled=subprocess.run([str(jdk/'bin/javac'),'-proc:none','--release','17','-cp',cp,'-d',str(classes),str(source)],
                            cwd=tmp_path,capture_output=True,text=True,env=clean_environment(),timeout=60)
    assert compiled.returncode==0,compiled.stdout+compiled.stderr
    argv=[str(jdk/'bin/java'),'-cp',str(classes)+os.pathsep+cp,'org.kneekura.staff.FixtureCommandParserAssertions',str(minecraft)]
    for role,key in [('client','creative_invoker'),('control','creative_control')]:
        argv.extend([IDENTITIES[role]['uuid'],commands[key]])
    result=subprocess.run(argv,cwd=tmp_path,capture_output=True,text=True,env=clean_environment(),timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'REAL_MINECRAFT_BRIGADIER_PARSE_PASS_NO_COMMAND_EXECUTION' in result.stdout
    assert result.stdout.count('ORIGINAL_UUID_REJECTED')==2
    assert result.stdout.count('FIXED_UUID_SELF_COMMAND_PARSED')==2
    (tmp_path/'parser-input-hashes.json').write_text(json.dumps(hashes,indent=2))
