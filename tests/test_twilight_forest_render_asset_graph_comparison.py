import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = (
    ROOT
    / "departments"
    / "minecraft"
    / "mods"
    / "twilight-forest"
    / "tools"
    / "compare_render_asset_graphs.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location("tf_render_compare", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_graph(commit: str, nodes: list[dict], edges=None, unresolved=None):
    edges = edges or []
    unresolved = unresolved or []
    counts = {
        "blockstate": 0,
        "model": 0,
        "item_definition": 0,
        "atlas": 0,
        "texture": 0,
    }
    for node in nodes:
        counts[node["kind"]] += 1
    counts.update(
        {
            "nodes": len(nodes),
            "edges": len(edges),
            "unresolved_local_refs": len(unresolved),
            "duplicate_logical_paths": 0,
            "parse_errors": 0,
        }
    )
    return {
        "graph_version": "1.0",
        "target": "The Twilight Forest",
        "namespace": "twilightforest",
        "source_commit": commit,
        "source_root": "fixture",
        "counts": counts,
        "nodes": nodes,
        "edges": edges,
        "unresolved_local_refs": unresolved,
        "duplicate_logical_paths": [],
        "parse_errors": [],
        "model_parent_cycles": [],
    }


def node(kind: str, path: str, content: bytes):
    return {
        "id": f"{kind}:twilightforest:{path}",
        "kind": kind,
        "logical_path": path,
        "source_path": f"src/main/resources/assets/twilightforest/{path}",
        "sha256": hashlib.sha256(content).hexdigest(),
        "size": len(content),
    }


def test_compare_reports_added_removed_and_changed_paths():
    mod = load_tool()
    anchor = make_graph(
        "anchor",
        [
            node("model", "models/item/shared.json", b"same"),
            node("model", "models/item/changed.json", b"old"),
            node("texture", "textures/item/anchor.png", b"anchor"),
        ],
    )
    frontier = make_graph(
        "frontier",
        [
            node("model", "models/item/shared.json", b"same"),
            node("model", "models/item/changed.json", b"new"),
            node("item_definition", "items/frontier.json", b"frontier"),
        ],
    )

    comparison = mod.compare_graphs(anchor, frontier)
    models = comparison["inventory_by_kind"]["model"]
    assert models["shared_logical_paths"] == 2
    assert models["shared_content_identical"] == 1
    assert models["shared_content_changed"] == 1
    assert models["changed_paths"] == ["models/item/changed.json"]
    assert comparison["inventory_by_kind"]["texture"]["anchor_only_paths"] == [
        "textures/item/anchor.png"
    ]
    assert comparison["inventory_by_kind"]["item_definition"]["frontier_only_paths"] == [
        "items/frontier.json"
    ]


def test_compare_reports_reference_and_unresolved_differences():
    mod = load_tool()
    shared_edge = {
        "source_path": "models/item/test.json",
        "ref_kind": "parent",
        "raw_ref": "minecraft:item/generated",
        "target_local_path": None,
        "target_exists": None,
    }
    anchor_edge = {
        "source_path": "models/item/test.json",
        "ref_kind": "texture",
        "raw_ref": "twilightforest:item/missing_old",
        "target_local_path": "textures/item/missing_old.png",
        "target_exists": False,
    }
    frontier_edge = {
        "source_path": "models/item/test.json",
        "ref_kind": "texture",
        "raw_ref": "twilightforest:item/missing_new",
        "target_local_path": "textures/item/missing_new.png",
        "target_exists": False,
    }
    anchor_missing = {
        "source_path": "models/item/test.json",
        "ref_kind": "texture",
        "raw_ref": "twilightforest:item/missing_old",
        "expected_path": "textures/item/missing_old.png",
    }
    frontier_missing = {
        "source_path": "models/item/test.json",
        "ref_kind": "texture",
        "raw_ref": "twilightforest:item/missing_new",
        "expected_path": "textures/item/missing_new.png",
    }

    anchor = make_graph("anchor", [], [shared_edge, anchor_edge], [anchor_missing])
    frontier = make_graph("frontier", [], [shared_edge, frontier_edge], [frontier_missing])
    comparison = mod.compare_graphs(anchor, frontier)

    assert comparison["reference_edges"]["shared_count"] == 1
    assert comparison["reference_edges"]["anchor_only_count"] == 1
    assert comparison["reference_edges"]["frontier_only_count"] == 1
    assert comparison["unresolved_local_refs"]["shared_count"] == 0
    assert comparison["unresolved_local_refs"]["anchor_only"] == [anchor_missing]
    assert comparison["unresolved_local_refs"]["frontier_only"] == [frontier_missing]


def test_validate_rejects_bad_hash_and_wrong_commit():
    mod = load_tool()
    graph = make_graph("anchor", [node("model", "models/item/test.json", b"ok")])
    graph["nodes"][0]["sha256"] = "not-a-hash"

    try:
        mod.validate_graph(graph, "different")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("validate_graph should reject invalid graph")
    assert "source_commit" in message
    assert "sha256" in message


def test_cli_writes_comparison_hashes_and_summary(tmp_path: Path):
    anchor_path = tmp_path / "anchor.json"
    frontier_path = tmp_path / "frontier.json"
    anchor_path.write_text(
        json.dumps(make_graph("anchor", [node("model", "models/item/test.json", b"old")])),
        encoding="utf-8",
    )
    frontier_path.write_text(
        json.dumps(make_graph("frontier", [node("model", "models/item/test.json", b"new")])),
        encoding="utf-8",
    )
    output = tmp_path / "comparison.json"
    summary = tmp_path / "comparison.md"

    result = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--anchor",
            str(anchor_path),
            "--frontier",
            str(frontier_path),
            "--expected-anchor-commit",
            "anchor",
            "--expected-frontier-commit",
            "frontier",
            "--output",
            str(output),
            "--summary-output",
            str(summary),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    comparison = json.loads(output.read_text(encoding="utf-8"))
    assert comparison["input_graphs"]["anchor"]["sha256"] == hashlib.sha256(
        anchor_path.read_bytes()
    ).hexdigest()
    assert comparison["input_graphs"]["frontier"]["sha256"] == hashlib.sha256(
        frontier_path.read_bytes()
    ).hexdigest()
    assert comparison["inventory_by_kind"]["model"]["shared_content_changed"] == 1
    text = summary.read_text(encoding="utf-8")
    assert "- ANCHOR source commit: `anchor`" in text
    assert "- FRONTIER source commit: `frontier`" in text
