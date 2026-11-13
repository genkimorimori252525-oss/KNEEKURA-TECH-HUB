"""No-network contract tests for the optional mcbuild launcher."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "departments" / "minecraft" / "building" / "mcbuild" / "runner.py"
spec = importlib.util.spec_from_file_location("kneekura_mcbuild_bridge", BRIDGE)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def test_pinned_upstream_identity_and_anchor():
    meta = bridge.metadata()
    assert meta["genre"] == "建築"
    assert meta["upstream"]["commit"] == "34ce86372d4c23f4d83d4e24fc256cb399d6c3e3"
    assert meta["tracks"]["anchor"]["minecraft"] == "1.20.1"
    assert meta["tracks"]["frontier"]["loader"] == "NeoForge"


def test_source_and_output_paths_are_ignored_local_artifacts():
    assert bridge.LOCAL.parent.name == "local-artifacts"
    assert bridge.UPSTREAM.parent == bridge.LOCAL
    assert bridge.RUNS.parent == bridge.LOCAL


def test_offline_demo_must_use_fake_llm():
    cmd = bridge.run_command("demo", "a tiny stone hut", 3, "", 0)
    assert cmd[:5] == ["uv", "run", "--frozen", "--no-sync", "mcbuild"]
    assert "--fake-llm" in cmd
    assert "--model" not in cmd
    assert cmd[cmd.index("--out") + 1] == str(bridge.RUNS)


def test_online_build_passes_explicit_cost_ceiling():
    cmd = bridge.run_command("build", "a shrine", 6, "example/model", 1.5)
    assert "--fake-llm" not in cmd
    assert cmd[cmd.index("--model") + 1] == "example/model"
    assert cmd[cmd.index("--cost-ceiling") + 1] == "1.5"


@pytest.mark.parametrize("action,iterations,model,ceiling", [
    ("demo", 0, "", 0),
    ("demo", 21, "", 0),
    ("build", 4, "example/model", 0),
    ("build", 4, "example/model", 101),
    ("build", 4, "", 2),
    ("unrecognized", 4, "", 0),
])
def test_invalid_invocations_fail_closed(action, iterations, model, ceiling):
    with pytest.raises(ValueError):
        bridge.run_command(action, "sample", iterations, model, ceiling)


def test_status_does_not_fetch_or_install(monkeypatch, capsys):
    monkeypatch.setattr(bridge, "UPSTREAM", bridge.LOCAL / "not-present")
    monkeypatch.setattr(bridge.shutil, "which", lambda exe: None)
    assert bridge.main(["status"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["source_verified"] is False
    assert status["live_world_edit"] is False


def test_build_without_explicit_online_ack_does_not_spawn(monkeypatch, capsys):
    def unexpected(*_a, **_kw):
        raise AssertionError("no subprocess permitted")
    monkeypatch.setattr(bridge.subprocess, "run", unexpected)
    assert bridge.main(["build", "--prompt", "a test house"]) == 2
    assert "--online" in capsys.readouterr().err
