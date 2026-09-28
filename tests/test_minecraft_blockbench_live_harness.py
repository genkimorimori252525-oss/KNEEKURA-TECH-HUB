"""RED contract for the real Blockbench hosted acceptance harness."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tools/ci/mod_ai_blockbench_live.py"
WORKFLOW = ROOT / ".github/workflows/mod-ai-blockbench.yml"
CDP = ROOT / "tools/ci/blockbench_cdp.mjs"


def load_harness():
    assert HARNESS.is_file(), "real Blockbench acceptance harness is not implemented"
    spec = importlib.util.spec_from_file_location("mod_ai_blockbench_live", HARNESS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_blockbench_release_is_exact_and_hash_pinned():
    m = load_harness()
    pin = m.blockbench_release()
    assert pin == {
        "version": "5.2.1",
        "source_revision": "e2ede0809ee6bc91f374ac7e00d34cffbdf86a14",
        "deb_url": "https://github.com/JannisX11/blockbench/releases/download/v5.2.1/Blockbench_5.2.1.deb",
        "deb_sha256": "d6329fd8db35a6e1ffb86c3f61b77ff193c6526418e6454e1cac863a0e384003",
    }


def test_plugin_permission_document_grants_only_loopback_network_module():
    m = load_harness()
    assert m.plugin_permissions() == {"blockbench_mcp": {"allowed": {"net": True}}}


def test_celestial_staff_plan_is_bounded_and_nontrivial():
    m = load_harness()
    request_hash = "a" * 64
    plan = m.celestial_staff_plan(request_hash)
    assert set(plan) == {"schema_version", "request_hash", "fill", "cubes"}
    assert plan["schema_version"] == 1 and plan["request_hash"] == request_hash
    assert plan["fill"] == "#d4af37"
    assert 8 <= len(plan["cubes"]) <= 32
    assert len({c["name"] for c in plan["cubes"]}) == len(plan["cubes"])
    assert any(c["name"].startswith("star_") for c in plan["cubes"])
    for cube in plan["cubes"]:
        assert set(cube) == {"name", "from", "to", "uv"}
        assert all(-16 <= n <= 32 for key in ("from", "to") for n in cube[key])
        assert 0 <= cube["uv"][0] < cube["uv"][2] <= 32
        assert 0 <= cube["uv"][1] < cube["uv"][3] <= 32


def test_workflow_is_standard_hosted_pinned_and_retains_evidence():
    text = WORKFLOW.read_text()
    assert 'runs-on: ubuntu-latest' in text
    assert 'self-hosted' not in text
    assert 'Blockbench_5.2.1.deb' in text
    assert 'd6329fd8db35a6e1ffb86c3f61b77ff193c6526418e6454e1cac863a0e384003' in text
    assert 'xvfb-run' in text
    assert 'mod_ai_blockbench_live.py' in text
    assert 'blockbench_cdp.mjs' in text
    assert 'retention-days: 7' in text


def test_cdp_loader_never_evaluates_asset_prompt_or_enables_raw_script_route():
    text = CDP.read_text()
    assert "loadFromFile" in text
    assert "blockbench_mcp_toggle" in text
    assert "execute_script" not in text
    assert "visual_brief" not in text
    assert "prompt" not in text.lower()
