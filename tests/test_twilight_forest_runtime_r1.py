import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "departments" / "minecraft" / "mods" / "twilight-forest" / "tools" / "run_runtime_r1.py"
WORKFLOW = ROOT / ".github" / "workflows" / "twilight-runtime-r1.yml"


def load_tool():
    spec = importlib.util.spec_from_file_location("tf_runtime_r1", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_gradle_command_accepts_track_specific_task(tmp_path: Path):
    mod = load_tool()
    command = mod.build_gradle_command(tmp_path, "Minecraft_Server_1.20.1")
    assert command == [
        "cmd.exe",
        "/d",
        "/s",
        "/c",
        str(tmp_path / "gradlew.bat"),
        "Minecraft_Server_1.20.1",
        "--no-daemon",
        "--console=plain",
    ]


def test_r1_workflow_has_retry_and_sufficient_job_budget():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "timeout-minutes: 180" in workflow
    assert "Warm ANCHOR Gradle wrapper" in workflow
    assert "Warm FRONTIER Gradle wrapper" in workflow
    assert '--gradle-task "Minecraft_Server_1.20.1"' in workflow
    assert '--gradle-task "runServer"' in workflow