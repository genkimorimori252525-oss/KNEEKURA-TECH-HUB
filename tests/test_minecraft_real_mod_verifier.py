"""Negative controls for the checked-in real-MOD acceptance verifier."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'departments/minecraft/mod-ai/verification/real-mod-2026-09-30'


def helpers():
    path = DIRECTORY / 'verification_helpers.py'
    assert path.is_file(), 'Verifier comparison/smoke checks must be reusable and fail closed'
    spec = importlib.util.spec_from_file_location('real_mod_verification_helpers', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('comparisons', [[], [{'same_normalized_javap': False}],
    [{'same_normalized_javap': True}, {'same_normalized_javap': False}]])
def test_any_remap_mismatch_fails_the_verifier(comparisons):
    module=helpers()
    with pytest.raises(AssertionError): module.require_all_class_comparisons(comparisons)


def test_all_matching_classes_pass_the_verifier():
    helpers().require_all_class_comparisons([{'same_normalized_javap': True}]*7)


@pytest.mark.skipif(not shutil.which('javac'), reason='JDK17 tools required for actual Java smoke control')
def test_reused_smoke_reads_constants_from_each_actual_output(tmp_path):
    original = ROOT / 'tools/ci/mod_ai_staff/java/org/kneekura/staff/StaffUsePolicy.java'
    source = tmp_path/'StaffUsePolicy.java'; source.write_bytes(original.read_bytes())
    named = tmp_path/'original'; named.mkdir()
    mutant = tmp_path/'changed'; mutant.mkdir()
    compiled = tmp_path/'smoke'; compiled.mkdir()
    subprocess.run(['javac','--release','17','-d',str(named),str(source)], check=True,capture_output=True)
    smoke = tmp_path/'SmokePolicy.java'; smoke.write_text(helpers().POLICY_SMOKE_SOURCE)
    subprocess.run(['javac','--release','17','-cp',str(named),'-d',str(compiled),str(smoke)],check=True,capture_output=True)
    normal = subprocess.run(['java','-cp',str(compiled)+os.pathsep+str(named),'SmokePolicy'],capture_output=True)
    assert normal.returncode == 0
    text=source.read_text(); assert 'GLOW_TICKS = 60' in text
    source.write_text(text.replace('GLOW_TICKS = 60','GLOW_TICKS = 61'))
    subprocess.run(['javac','--release','17','-d',str(mutant),str(source)],check=True,capture_output=True)
    changed = subprocess.run(['java','-cp',str(compiled)+os.pathsep+str(mutant),'SmokePolicy'],capture_output=True)
    assert changed.returncode != 0, 'A smoke compiled against original constants must reject changed output constants'


def test_research_profile_binds_mod_revision_not_adapter_revision():
    module=helpers()
    captured={'manifest':{'workspace_revision':'2'*40,'dirty_hash':'a'*64}}
    assert module.bound_mod_revision(captured,'a'*64)=='2'*40
    with pytest.raises(AssertionError): module.bound_mod_revision(captured,'b'*64)
    with pytest.raises(AssertionError): module.bound_mod_revision({'manifest':{}},'a'*64)


@pytest.mark.parametrize('actual', [['A.class'], ['A.class','B.class','extra.png'], ['A.class','B.class','B.class']])
def test_missing_added_or_duplicate_output_entry_fails(actual):
    module=helpers()
    with pytest.raises(AssertionError): module.require_same_archive_inventory(['A.class','B.class'],actual)


def test_exact_output_inventory_passes():
    helpers().require_same_archive_inventory(['A.class','asset.png'],['asset.png','A.class'])


@pytest.mark.parametrize('name', ['../other','/absolute','x/y','', '.', '..'])
def test_verification_output_name_cannot_escape_work_directory(name):
    module=helpers()
    with pytest.raises(ValueError): module.verification_name(name)
