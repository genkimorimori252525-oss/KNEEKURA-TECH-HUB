"""Hosted LAB source verification cannot implicitly launch a game or change LAB runners."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def test_lab_source_pin_and_workflow_are_source_only_exact_refs():
    pin=json.loads((ROOT/'departments/minecraft/mod-ai/verification/lab-source-pin.json').read_text())
    assert set(pin)=={'schema_version','lab_repository','lab_revision','mod_repository','mod_revision'}
    assert pin['schema_version']==1 and pin['lab_repository']=='genkimorimori252525-oss/KNEEKURA-LAB'
    assert pin['mod_repository']=='genkimorimori252525-oss/reimu-mod'
    assert all(re.fullmatch('[a-f0-9]{40}',pin[k]) for k in ('lab_revision','mod_revision'))
    workflow=(ROOT/'.github/workflows/mod-ai-lab-source.yml').read_text()
    assert 'runs-on: ubuntu-latest' in workflow
    assert 'persist-credentials: false' in workflow and 'contents: read' in workflow
    assert 'kneekuraDebugClasses --no-daemon' in workflow
    assert 'npm run test:ci' in workflow and 'test:bridge-runtime' in workflow
    assert 'check_lab_adapter_source.py' in workflow
    for forbidden in ('runClient','runServer','debug:start','self-hosted','workflow_dispatch','secrets.'):
        assert forbidden not in workflow
