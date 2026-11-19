"""Explicit paired source gate; no download, game, JVM or browser fallback."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


def test_real_lab_scoped_control_cli_and_private_export_roundtrip():
    selected = os.environ.get('KNEEKURA_LAB_SOURCE')
    if not selected:
        pytest.skip('Explicit paired LAB source checkout required')
    lab = Path(selected)
    assert lab.is_absolute() and lab.is_dir(), 'KNEEKURA_LAB_SOURCE must be an absolute local source checkout'
    script = lab / 'debug-workspace/bridge/tests/scoped-control-roundtrip.mjs'
    assert script.is_file(), 'Selected LAB source does not contain the paired scoped-control source gate'
    node = shutil.which('node')
    assert node is not None, 'The explicit paired source gate requires installed Node'
    tech = Path(__file__).resolve().parents[1]
    completed = subprocess.run([node, str(script)], cwd=lab, capture_output=True, timeout=60,
        env={**os.environ, 'KNEEKURA_TECH_HUB_SOURCE':str(tech), 'KNEEKURA_PYTHON':sys.executable})
    assert completed.returncode == 0, completed.stderr.decode('utf-8', 'replace')
    assert completed.stderr == b''
    result = json.loads(completed.stdout)
    assert result == {
        'scope':'SOURCE_PROTOCOL_FIXTURE_ONLY',
        'controls':{'staleOwner':'OUTCOME_UNKNOWN', 'owner':'OWNER_RECORDED', 'action':'REQUESTED',
            'inspection':'REQUESTED', 'capture':'REQUESTED', 'freshStoreReplay':'ALREADY_RECORDED',
            'repeatedCapture':'ALREADY_RECORDED', 'cleanup':'REQUESTED',
            'cleanupInspection':'OUTCOME_UNKNOWN', 'repeatedCleanup':'ALREADY_RECORDED',
            'triggerWatch':'WINDOWS_FINISHED', 'triggerWindow':'PARTIAL', 'repeatedWatch':'OUTCOME_UNKNOWN', 'moduleCount':28},
        'export':'EXPORTED', 'import':'IMPORTED_LAB_REPORT', 'execution':'UNKNOWN', 'cleanup':'UNKNOWN',
        'assertions':['INCONCLUSIVE'], 'evidenceCount':6, 'runtimeAttestation':'NOT_ESTABLISHED', 'canReplay':False,
    }
