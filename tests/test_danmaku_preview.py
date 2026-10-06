"""Run the dependency-free danmaku draft contracts with the real JDK."""

from pathlib import Path
import shutil
import subprocess

import pytest


def test_danmaku_draft_model_and_json(tmp_path):
    javac, java = shutil.which("javac"), shutil.which("java")
    if not javac or not java:
        pytest.skip("JDK17-compatible javac/java required")
    root = Path(__file__).resolve().parents[1] / "departments/minecraft/danmaku-preview"
    sources = [
        root / "src/kneekura/danmaku/Pattern.java",
        root / "src/kneekura/danmaku/PatternJson.java",
        root / "src/kneekura/danmaku/Score.java",
        root / "src/kneekura/danmaku/ScoreJson.java",
        root / "tests/kneekura/danmaku/PatternTest.java",
        root / "tests/kneekura/danmaku/ScoreTest.java",
    ]
    compiled = subprocess.run(
        [javac, "--release", "17", "-encoding", "UTF-8", "-d", str(tmp_path), *map(str, sources)],
        capture_output=True, text=True, errors="replace", timeout=30,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr

    pattern = subprocess.run(
        [java, "-cp", str(tmp_path), "kneekura.danmaku.PatternTest", str(root / "presets/fan.json")],
        capture_output=True, text=True, errors="replace", timeout=30,
    )
    assert pattern.returncode == 0, pattern.stdout + pattern.stderr

    score = subprocess.run(
        [java, "-cp", str(tmp_path), "kneekura.danmaku.ScoreTest", str(root / "presets/grand-danmaku-score.json")],
        capture_output=True, text=True, errors="replace", timeout=30,
    )
    assert score.returncode == 0, score.stdout + score.stderr
