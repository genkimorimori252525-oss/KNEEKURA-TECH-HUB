import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "departments" / "minecraft" / "mods" / "twilight-forest" / "tools" / "build_render_asset_graph.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("tf_render_graph", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_render_graph_resolves_model_parent_and_texture(tmp_path: Path):
    mod = load_tool()
    assets = tmp_path / "src" / "generated" / "resources" / "assets" / "twilightforest"

    write_json(
        assets / "blockstates" / "test_block.json",
        {"variants": {"": {"model": "twilightforest:block/test_block"}}},
    )
    write_json(
        assets / "models" / "block" / "test_block.json",
        {
            "parent": "twilightforest:block/base",
            "textures": {"all": "twilightforest:block/test"},
        },
    )
    write_json(
        assets / "models" / "block" / "base.json",
        {"parent": "minecraft:block/cube_all"},
    )
    texture = assets / "textures" / "block" / "test.png"
    texture.parent.mkdir(parents=True, exist_ok=True)
    texture.write_bytes(b"png-fixture")

    graph = mod.build_graph(tmp_path, "fixture")
    assert graph["counts"]["blockstate"] == 1
    assert graph["counts"]["model"] == 2
    assert graph["counts"]["texture"] == 1
    assert graph["counts"]["unresolved_local_refs"] == 0
    assert graph["model_parent_cycles"] == []


def test_render_graph_reports_missing_local_texture(tmp_path: Path):
    mod = load_tool()
    assets = tmp_path / "src" / "main" / "resources" / "assets" / "twilightforest"

    write_json(
        assets / "models" / "item" / "broken.json",
        {
            "parent": "minecraft:item/generated",
            "textures": {"layer0": "twilightforest:item/missing"},
        },
    )

    graph = mod.build_graph(tmp_path)
    assert graph["counts"]["unresolved_local_refs"] == 1
    assert graph["unresolved_local_refs"][0]["expected_path"] == "textures/item/missing.png"
