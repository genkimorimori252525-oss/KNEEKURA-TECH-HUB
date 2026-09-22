import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_minecraft_department_uses_anchor_plus_frontier_contract():
    schema_path = ROOT / "schemas" / "v1" / "minecraft-mod-analysis.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    props = schema["properties"]
    anchor = props["adaptation_anchor"]["properties"]
    assert anchor["minecraft_version"]["const"] == "1.20.1"
    assert anchor["loader"]["const"] == "Forge"
    track_props = props["tracks"]["items"]["properties"]
    assert track_props["minecraft_version"]["type"] == "string"
    assert "NeoForge" in track_props["loader"]["enum"]
    assert "Fabric" in track_props["loader"]["enum"]
    readme = (ROOT / "departments" / "minecraft" / "README.md").read_text(encoding="utf-8")
    assert "ANCHOR" in readme
    assert "FRONTIER" in readme
    assert "1.20.1" in readme
    assert "固定しない" in readme


def test_queue_orders_twilight_forest_before_connector():
    catalog = (ROOT / "departments" / "minecraft" / "catalog" / "MODS.md").read_text(encoding="utf-8")
    assert catalog.index("The Twilight Forest") < catalog.index("Sinytra Connector")
    twilight = (ROOT / "departments" / "minecraft" / "mods" / "twilight-forest" / "README.md").read_text(encoding="utf-8")
    connector = (ROOT / "departments" / "minecraft" / "mods" / "sinytra-connector" / "README.md").read_text(encoding="utf-8")
    assert "Priority: **1**" in twilight
    assert "Priority: **2" in connector
    assert "1.20.1" in connector
    assert "26.1.x" in connector
    assert "NOT_PINNED" in connector
