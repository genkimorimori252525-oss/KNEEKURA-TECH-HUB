import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_minecraft_department_contract_is_1201_forge():
    schema_path = ROOT / "schemas" / "v1" / "minecraft-mod-analysis.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    props = schema["properties"]
    assert props["minecraft_version"]["const"] == "1.20.1"
    assert props["loader"]["const"] == "Forge"

    readme = (ROOT / "departments" / "minecraft" / "README.md").read_text(encoding="utf-8")
    assert "Minecraft 1.20.1" in readme
    assert "Forge" in readme

def test_twilight_forest_is_registered_without_fake_snapshot():
    text = (ROOT / "departments" / "minecraft" / "mods" / "twilight-forest" / "README.md").read_text(encoding="utf-8")
    assert "The Twilight Forest" in text
    assert "NOT_PINNED" in text
    assert "QUEUED" in text
