import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "departments" / "minecraft" / "mods" / "twilight-forest" / "tools" / "build_render_asset_graph.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("tf_render_graph", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Dataclasses resolve postponed annotations through the importing module.
    # Register it during execution, then restore sys.modules for test isolation.
    with patch.dict(sys.modules, {spec.name: module}):
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


def test_summary_uses_markdown_code_delimiters(tmp_path: Path):
    mod = load_tool()
    summary = mod.summary_markdown(mod.build_graph(tmp_path, "fixture"))
    assert "- source commit: `fixture`" in summary.splitlines()


def test_loader_restores_previous_module_registration():
    sentinel = object()
    with patch.dict(sys.modules, {"tf_render_graph": sentinel}):
        module = load_tool()
        assert sys.modules["tf_render_graph"] is sentinel
        assert module.NAMESPACE == "twilightforest"


def test_nested_item_definitions_resolve_and_deduplicate_models(tmp_path: Path):
    mod = load_tool()
    assets = tmp_path / "src/generated/resources/assets/twilightforest"
    write_json(assets / "items/test.json", {
        "model": {
            "type": "minecraft:condition",
            "on_true": {"type": "minecraft:model", "model": "twilightforest:item/test"},
            "on_false": {"type": "minecraft:model", "model": "twilightforest:item/test"},
        }
    })
    write_json(assets / "models/item/test.json", {"parent": "minecraft:item/generated"})
    graph = mod.build_graph(tmp_path, "fixture")
    references = [edge for edge in graph["edges"] if edge["source_path"] == "items/test.json"]
    assert graph["counts"]["item_definition"] == 1
    assert len(references) == 1
    assert references[0]["ref_kind"] == "model"
    assert references[0]["target_local_path"] == "models/item/test.json"
    assert references[0]["target_exists"] is True


def test_atlas_resource_references_are_preserved(tmp_path: Path):
    mod = load_tool()
    assets = tmp_path / "src/main/resources/assets/twilightforest"
    write_json(assets / "atlases/test.json", {"sources": [
        {"type": "minecraft:single", "resource": "twilightforest:block/test"},
        {"type": "minecraft:directory", "source": "block", "prefix": "block/"},
    ]})
    graph = mod.build_graph(tmp_path, "fixture")
    assert graph["counts"]["atlas"] == 1
    assert {(edge["ref_kind"], edge["raw_ref"]) for edge in graph["edges"]} == {
        ("resource", "twilightforest:block/test"), ("resource", "block"),
    }


def test_duplicate_logical_paths_retain_both_source_files(tmp_path: Path):
    mod = load_tool()
    for root in ("main", "generated"):
        write_json(tmp_path / f"src/{root}/resources/assets/twilightforest/models/item/test.json",
                   {"parent": "minecraft:item/generated"})
    graph = mod.build_graph(tmp_path, "fixture")
    assert graph["counts"]["model"] == 2
    assert graph["counts"]["duplicate_logical_paths"] == 1
    duplicate = graph["duplicate_logical_paths"][0]
    assert duplicate["logical_path"] == "models/item/test.json"
    assert set(duplicate["sources"]) == {
        f"src/{root}/resources/assets/twilightforest/models/item/test.json"
        for root in ("main", "generated")
    }
    assert len({node["source_path"] for node in graph["nodes"]}) == 2


def test_invalid_json_is_reported_without_dropping_inventory_node(tmp_path: Path):
    mod = load_tool()
    assets = tmp_path / "src/main/resources/assets/twilightforest"
    malformed = assets / "models/item/broken.json"
    malformed.parent.mkdir(parents=True)
    malformed.write_text("{broken", encoding="utf-8")
    graph = mod.build_graph(tmp_path, "fixture")
    assert graph["counts"]["nodes"] == 1
    assert graph["counts"]["parse_errors"] == 1
    assert graph["parse_errors"][0]["path"] == malformed.relative_to(tmp_path).as_posix()
    assert graph["parse_errors"][0]["error"]


def test_model_parent_cycle_is_reported(tmp_path: Path):
    mod = load_tool()
    assets = tmp_path / "src/generated/resources/assets/twilightforest"
    write_json(assets / "models/block/a.json", {"parent": "twilightforest:block/b"})
    write_json(assets / "models/block/b.json", {"parent": "twilightforest:block/a"})
    graph = mod.build_graph(tmp_path, "fixture")
    assert graph["model_parent_cycles"] == [[
        "models/block/a.json", "models/block/b.json", "models/block/a.json",
    ]]
    assert graph["counts"]["unresolved_local_refs"] == 0


def test_external_and_texture_slot_references_are_not_false_local_misses(tmp_path: Path):
    mod = load_tool()
    assets = tmp_path / "src/main/resources/assets/twilightforest"
    write_json(assets / "models/block/test.json", {
        "parent": "minecraft:block/cube_all",
        "textures": {"all": "othermod:block/shared", "particle": "#all"},
    })
    graph = mod.build_graph(tmp_path, "fixture")
    assert len(graph["edges"]) == 3
    assert graph["counts"]["unresolved_local_refs"] == 0
    assert all(edge["target_exists"] is None for edge in graph["edges"])


def test_node_hashes_sizes_and_repeated_extraction_are_stable(tmp_path: Path):
    import hashlib

    mod = load_tool()
    assets = tmp_path / "src/main/resources/assets/twilightforest"
    source = assets / "models/item/test.json"
    write_json(source, {"parent": "minecraft:item/generated"})
    first = mod.build_graph(tmp_path, "fixture")
    second = mod.build_graph(tmp_path, "fixture")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["nodes"][0]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert first["nodes"][0]["size"] == len(source.read_bytes())


def test_cli_writes_graph_and_summary_for_all_five_fixture_kinds(tmp_path: Path):
    import subprocess

    source = tmp_path / "fixture-source"
    assets = source / "src/main/resources/assets/twilightforest"
    write_json(assets / "blockstates/test.json", {
        "variants": {"": {"model": "twilightforest:block/test"}},
    })
    write_json(assets / "models/block/test.json", {
        "parent": "minecraft:block/cube_all", "textures": {"all": "twilightforest:block/test"},
    })
    write_json(assets / "items/test.json", {
        "model": {"type": "minecraft:model", "model": "twilightforest:block/test"},
    })
    write_json(assets / "atlases/test.json", {
        "sources": [{"type": "minecraft:single", "resource": "twilightforest:block/test"}],
    })
    texture = assets / "textures/block/test.png"
    texture.parent.mkdir(parents=True)
    texture.write_bytes(b"png-fixture-not-a-real-texture")
    output = tmp_path / "out/graph.json"
    summary = tmp_path / "out/graph.md"
    result = subprocess.run([
        sys.executable, str(TOOL), str(source), "--source-commit", "fixture-not-upstream",
        "--output", str(output), "--summary-output", str(summary),
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    graph = json.loads(output.read_text(encoding="utf-8"))
    assert graph["source_commit"] == "fixture-not-upstream"
    assert graph["source_root"] == str(source.resolve())
    for kind in ("blockstate", "model", "item_definition", "atlas", "texture"):
        assert graph["counts"][kind] == 1
    assert graph["counts"]["nodes"] == 5
    assert graph["counts"]["unresolved_local_refs"] == 0
    assert graph["counts"]["parse_errors"] == 0
    assert graph["model_parent_cycles"] == []
    assert "- source commit: `fixture-not-upstream`" in summary.read_text(encoding="utf-8")