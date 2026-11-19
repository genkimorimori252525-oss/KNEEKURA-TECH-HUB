"""Hosted LAB source verification uses the vendored monorepo source and cannot implicitly launch a game."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def test_lab_source_pin_and_workflow_are_monorepo_source_only_exact_refs():
    pin=json.loads((ROOT/'departments/minecraft/mod-ai/verification/lab-source-pin.json').read_text())
    assert set(pin)=={'schema_version','lab_path','lab_import_repository','lab_import_revision','mod_repository','mod_revision'}
    assert pin['schema_version']==2
    assert pin['lab_path']=='departments/minecraft/lab'
    assert pin['lab_import_repository']=='genkimorimori252525-oss/KNEEKURA-LAB'
    assert pin['mod_repository']=='genkimorimori252525-oss/reimu-mod'
    assert all(re.fullmatch('[a-f0-9]{40}',pin[k]) for k in ('lab_import_revision','mod_revision'))
    lab=ROOT/pin['lab_path']
    assert (lab/'package.json').is_file()
    assert (lab/'debug-workspace/bridge/adapter-cli.mjs').is_file()

    workflow=(ROOT/'.github/workflows/mod-ai-lab-source.yml').read_text()
    assert 'runs-on: ubuntu-latest' in workflow
    assert 'persist-credentials: false' in workflow and 'contents: read' in workflow
    assert 'working-directory: tech-hub/departments/minecraft/lab' in workflow
    assert 'KNEEKURA_LAB_SOURCE: ${{ github.workspace }}/tech-hub/departments/minecraft/lab' in workflow
    assert 'kneekuraDebugClasses --no-daemon' in workflow
    assert 'npm run test:ci' in workflow and 'test:bridge-runtime' in workflow
    assert 'check_lab_adapter_source.py' in workflow

    # LAB is now same-repository source. Only the still-separate MOD checkout
    # needs a repository-scoped read-only credential.
    assert 'MOD_AI_LAB_SOURCE_SSH_KEY' not in workflow
    assert re.findall(r'\$\{\{\s*secrets\.([A-Z0-9_]+)\s*\}\}',workflow)==['MOD_AI_MOD_SOURCE_SSH_KEY']
    assert 'repository: genkimorimori252525-oss/KNEEKURA-LAB' not in workflow
    for forbidden in ('runClient','runServer','debug:start','self-hosted','workflow_dispatch'):
        assert forbidden not in workflow
