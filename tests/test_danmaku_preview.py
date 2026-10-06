"""Run the dependency-free draft model contracts with the real JDK."""

from pathlib import Path
import shutil
import subprocess

import pytest


def test_danmaku_draft_model_and_json(tmp_path):
    javac, java = shutil.which("javac"), shutil.which("java")
    if not javac or not java:
        pytest.skip("JDK17-compatible javac/java required")
    root = Path(__file__).resolve().parents[1] / "departments/minecraft/danmaku-preview"
    sources = [root / "src/kneekura/danmaku/Pattern.java",
               root / "src/kneekura/danmaku/PatternJson.java",
               root / "tests/kneekura/danmaku/PatternTest.java"]
    compiled = subprocess.run(
        [javac, "--release", "17", "-encoding", "UTF-8", "-d", str(tmp_path), *map(str, sources)],
        capture_output=True, text=True, errors="replace", timeout=30,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    tested = subprocess.run(
        [java, "-cp", str(tmp_path), "kneekura.danmaku.PatternTest", str(root / "presets/fan.json")],
        capture_output=True, text=True, errors="replace", timeout=30,
    )
    assert tested.returncode == 0, tested.stdout + tested.stderr
