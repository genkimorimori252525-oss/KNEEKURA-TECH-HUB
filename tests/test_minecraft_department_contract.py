import json
import re
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


def test_connector_acquired_source_pins_do_not_claim_runtime_compatibility():
    workspace = ROOT / "departments" / "minecraft" / "mods" / "sinytra-connector"
    readme = (workspace / "README.md").read_text(encoding="utf-8")
    inventory = json.loads((workspace / "SOURCE-INVENTORY-2026-10-01.json").read_text(encoding="utf-8"))
    verification = json.loads((workspace / "STATIC-VERIFICATION-2026-10-01.json").read_text(encoding="utf-8"))

    # Queue position is historical; acquiring source must not leave a perpetual
    # NOT_PINNED requirement or be mistaken for a runtime compatibility result.
    assert "IN_PROGRESS" in readme
    assert "Runtime compatibility remains UNKNOWN" in readme
    assert set(inventory["tracks"]) == {"anchor", "frontier"}
    assert len({track["revision"] for track in inventory["tracks"].values()}) == 2
    for name, track in inventory["tracks"].items():
        assert track["track"] == name.upper()
        assert re.fullmatch(r"[0-9a-f]{40}", track["revision"])
        assert track["revision"] in readme
        assert track["files_acquired"] == len(track["files"]) > 0
        assert track["bytes_acquired"] == sum(item["size"] for item in track["files"])
        assert track["upstream_execution"] is False
        assert track["raw_source_publication"] is False
        assert verification["tracks"][name]["revision"] == track["revision"]
        assert verification["tracks"][name]["status"] == "PARTIAL"
        assert all(re.fullmatch(r"[0-9a-f]{40}", item["sha"]) for item in track["files"])
        assert all(re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) for item in track["files"])
    assert verification["game_launches"] == 0
    assert verification["canonical_writes"] == 0
