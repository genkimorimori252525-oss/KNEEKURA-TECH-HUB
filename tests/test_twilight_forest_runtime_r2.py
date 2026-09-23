import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "departments" / "minecraft" / "mods" / "twilight-forest" / "tools" / "run_runtime_r2.py"
WORKFLOW = ROOT / ".github" / "workflows" / "twilight-runtime-r2.yml"


def load_tool():
    spec = importlib.util.spec_from_file_location("tf_runtime_r2", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_portal_fixture_is_fixed_and_uses_real_twilight_portal():
    mod = load_tool()
    commands = mod.build_portal_fixture_commands()
    assert commands[-1] == "say KNEEKURA_R2_FIXTURE_READY"
    assert "fill 0 160 0 1 160 1 twilightforest:twilight_portal" in commands
    assert "fill -1 161 -1 2 161 2 minecraft:fern" in commands
    assert mod.TWILIGHT_DIMENSION == "twilightforest:twilight_forest"
    assert "kneekura_r2_probe" in mod.summon_probe_command()


def test_region_chunk_coordinates_reads_anvil_location_table(tmp_path: Path):
    mod = load_tool()
    region = tmp_path / "r.1.-1.mca"
    header = bytearray(4096)
    header[0:4] = bytes([0, 0, 2, 1])
    offset = 33 * 4
    header[offset:offset + 4] = bytes([0, 0, 3, 1])
    region.write_bytes(header)
    assert mod.region_chunk_coordinates(region) == [[32, -32], [33, -31]]


def test_keepup_warning_parser_is_bounded():
    mod = load_tool()
    parsed = mod.parse_keepup_warning(
        "Can't keep up! Is the server overloaded? Running 2345ms or 47 ticks behind"
    )
    assert parsed == {"delay_ms": 2345.0, "ticks_behind": 47}
    assert mod.parse_keepup_warning("normal line") is None


def test_r2_workflow_preserves_track_specific_java_and_tasks():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Twilight Forest Runtime Evidence R2" in workflow
    assert "Minecraft_Server_1.20.1" in workflow
    assert 'java-version: \'21\'' in workflow
    assert 'java-version: \'25\'' in workflow
    assert "org.gradle.java.installations.auto-download=false" in workflow
    assert "run_runtime_r2.py" in workflow
    assert "RUNTIME-R2-LATEST.json" in workflow