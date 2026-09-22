#!/usr/bin/env python3
"""Compare pinned Twilight Forest block/item render-asset graphs.

Inputs are derived graph JSON files produced by build_render_asset_graph.py.
This tool never copies third-party assets; it compares logical paths, hashes,
reference edges, and diagnostics and emits derived evidence only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


GRAPH_KINDS = ("blockstate", "model", "item_definition", "atlas", "texture")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_graph(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_graph(graph: dict[str, Any], expected_commit: str | None = None) -> None:
    errors: list[str] = []
    if expected_commit is not None and graph.get("source_commit") != expected_commit:
        errors.append(
            f"source_commit={graph.get('source_commit')!r}, expected {expected_commit!r}"
        )

    nodes = graph.get("nodes")
    edges = graph.get("edges")
    counts = graph.get("counts")
    if not isinstance(nodes, list):
        errors.append("nodes is not a list")
        nodes = []
    if not isinstance(edges, list):
        errors.append("edges is not a list")
        edges = []
    if not isinstance(counts, dict):
        errors.append("counts is not an object")
        counts = {}

    if counts.get("nodes") != len(nodes):
        errors.append(f"counts.nodes={counts.get('nodes')!r}, actual={len(nodes)}")
    if counts.get("edges") != len(edges):
        errors.append(f"counts.edges={counts.get('edges')!r}, actual={len(edges)}")

    kind_counts = Counter(node.get("kind") for node in nodes if isinstance(node, dict))
    for kind in GRAPH_KINDS:
        if counts.get(kind, 0) != kind_counts.get(kind, 0):
            errors.append(
                f"counts.{kind}={counts.get(kind, 0)!r}, actual={kind_counts.get(kind, 0)}"
            )

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"nodes[{index}] is not an object")
            continue
        logical_path = node.get("logical_path")
        digest = node.get("sha256")
        size = node.get("size")
        if not isinstance(logical_path, str) or not logical_path:
            errors.append(f"nodes[{index}].logical_path is invalid")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            errors.append(f"nodes[{index}].sha256 is invalid")
        if not isinstance(size, int) or size < 0:
            errors.append(f"nodes[{index}].size is invalid")

    diagnostics = (
        ("unresolved_local_refs", "unresolved_local_refs"),
        ("duplicate_logical_paths", "duplicate_logical_paths"),
        ("parse_errors", "parse_errors"),
    )
    for count_key, field in diagnostics:
        value = graph.get(field)
        if not isinstance(value, list):
            errors.append(f"{field} is not a list")
            value = []
        if counts.get(count_key) != len(value):
            errors.append(
                f"counts.{count_key}={counts.get(count_key)!r}, actual={len(value)}"
            )

    cycles = graph.get("model_parent_cycles")
    if not isinstance(cycles, list):
        errors.append("model_parent_cycles is not a list")

    if errors:
        raise ValueError("invalid render graph: " + "; ".join(errors))


def _node_index(graph: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for node in graph["nodes"]:
        key = (node["kind"], node["logical_path"])
        grouped[key].append({"sha256": node["sha256"], "size": node["size"]})
    for values in grouped.values():
        values.sort(key=lambda item: (item["sha256"], item["size"]))
    return dict(grouped)


def _canonical_key(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _set_diff(
    left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    left_by_key = {_canonical_key(item): item for item in left}
    right_by_key = {_canonical_key(item): item for item in right}
    shared_keys = sorted(left_by_key.keys() & right_by_key.keys())
    left_only_keys = sorted(left_by_key.keys() - right_by_key.keys())
    right_only_keys = sorted(right_by_key.keys() - left_by_key.keys())
    return (
        [left_by_key[key] for key in shared_keys],
        [left_by_key[key] for key in left_only_keys],
        [right_by_key[key] for key in right_only_keys],
    )


def _normalized_edges(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_path": edge.get("source_path"),
            "ref_kind": edge.get("ref_kind"),
            "raw_ref": edge.get("raw_ref"),
            "target_local_path": edge.get("target_local_path"),
            "target_exists": edge.get("target_exists"),
        }
        for edge in graph["edges"]
    ]


def _normalized_unresolved(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_path": item.get("source_path"),
            "ref_kind": item.get("ref_kind"),
            "raw_ref": item.get("raw_ref"),
            "expected_path": item.get("expected_path"),
        }
        for item in graph["unresolved_local_refs"]
    ]


def compare_graphs(anchor: dict[str, Any], frontier: dict[str, Any]) -> dict[str, Any]:
    validate_graph(anchor)
    validate_graph(frontier)

    anchor_nodes = _node_index(anchor)
    frontier_nodes = _node_index(frontier)
    all_kinds = sorted({kind for kind, _ in anchor_nodes} | {kind for kind, _ in frontier_nodes})

    inventory: dict[str, Any] = {}
    changed_content: list[dict[str, Any]] = []
    for kind in all_kinds:
        anchor_keys = {key for key in anchor_nodes if key[0] == kind}
        frontier_keys = {key for key in frontier_nodes if key[0] == kind}
        shared = anchor_keys & frontier_keys
        anchor_only = sorted(path for _, path in anchor_keys - frontier_keys)
        frontier_only = sorted(path for _, path in frontier_keys - anchor_keys)
        changed = sorted(
            path
            for _, path in shared
            if anchor_nodes[(kind, path)] != frontier_nodes[(kind, path)]
        )
        unchanged_count = len(shared) - len(changed)
        inventory[kind] = {
            "anchor_logical_paths": len(anchor_keys),
            "frontier_logical_paths": len(frontier_keys),
            "shared_logical_paths": len(shared),
            "shared_content_identical": unchanged_count,
            "shared_content_changed": len(changed),
            "anchor_only_count": len(anchor_only),
            "frontier_only_count": len(frontier_only),
            "anchor_only_paths": anchor_only,
            "frontier_only_paths": frontier_only,
            "changed_paths": changed,
        }
        for path in changed:
            changed_content.append(
                {
                    "kind": kind,
                    "logical_path": path,
                    "anchor_variants": anchor_nodes[(kind, path)],
                    "frontier_variants": frontier_nodes[(kind, path)],
                }
            )

    shared_edges, anchor_only_edges, frontier_only_edges = _set_diff(
        _normalized_edges(anchor), _normalized_edges(frontier)
    )
    shared_unresolved, anchor_only_unresolved, frontier_only_unresolved = _set_diff(
        _normalized_unresolved(anchor), _normalized_unresolved(frontier)
    )

    return {
        "comparison_version": "1.0",
        "target": "The Twilight Forest",
        "anchor": {
            "source_commit": anchor.get("source_commit"),
            "counts": anchor["counts"],
        },
        "frontier": {
            "source_commit": frontier.get("source_commit"),
            "counts": frontier["counts"],
        },
        "inventory_by_kind": inventory,
        "changed_content": changed_content,
        "reference_edges": {
            "shared_count": len(shared_edges),
            "anchor_only_count": len(anchor_only_edges),
            "frontier_only_count": len(frontier_only_edges),
            "anchor_only": anchor_only_edges,
            "frontier_only": frontier_only_edges,
        },
        "unresolved_local_refs": {
            "shared_count": len(shared_unresolved),
            "anchor_only_count": len(anchor_only_unresolved),
            "frontier_only_count": len(frontier_only_unresolved),
            "shared": shared_unresolved,
            "anchor_only": anchor_only_unresolved,
            "frontier_only": frontier_only_unresolved,
        },
        "diagnostics": {
            "anchor": {
                "duplicate_logical_paths": anchor["counts"]["duplicate_logical_paths"],
                "parse_errors": anchor["counts"]["parse_errors"],
                "model_parent_cycles": anchor["model_parent_cycles"],
            },
            "frontier": {
                "duplicate_logical_paths": frontier["counts"]["duplicate_logical_paths"],
                "parse_errors": frontier["counts"]["parse_errors"],
                "model_parent_cycles": frontier["model_parent_cycles"],
            },
        },
    }


def summary_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# Twilight Forest Block / Item Render Asset Portability — Generated Summary",
        "",
        f"- ANCHOR source commit: `{comparison['anchor']['source_commit']}`",
        f"- FRONTIER source commit: `{comparison['frontier']['source_commit']}`",
    ]
    inputs = comparison.get("input_graphs")
    if inputs:
        lines.extend(
            [
                f"- ANCHOR graph SHA-256: `{inputs['anchor']['sha256']}`",
                f"- FRONTIER graph SHA-256: `{inputs['frontier']['sha256']}`",
            ]
        )

    lines.extend(
        [
            "",
            "| kind | ANCHOR | FRONTIER | shared | identical | changed | ANCHOR-only | FRONTIER-only |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for kind, item in comparison["inventory_by_kind"].items():
        lines.append(
            f"| {kind} | {item['anchor_logical_paths']} | {item['frontier_logical_paths']} | "
            f"{item['shared_logical_paths']} | {item['shared_content_identical']} | "
            f"{item['shared_content_changed']} | {item['anchor_only_count']} | "
            f"{item['frontier_only_count']} |"
        )

    refs = comparison["reference_edges"]
    unresolved = comparison["unresolved_local_refs"]
    lines.extend(
        [
            "",
            "## Reference topology",
            "",
            f"- shared edges: **{refs['shared_count']}**",
            f"- ANCHOR-only edges: **{refs['anchor_only_count']}**",
            f"- FRONTIER-only edges: **{refs['frontier_only_count']}**",
            f"- shared unresolved local refs: **{unresolved['shared_count']}**",
            f"- ANCHOR-only unresolved local refs: **{unresolved['anchor_only_count']}**",
            f"- FRONTIER-only unresolved local refs: **{unresolved['frontier_only_count']}**",
            "",
            "## Diagnostics",
            "",
        ]
    )
    for role in ("anchor", "frontier"):
        item = comparison["diagnostics"][role]
        lines.append(
            f"- {role.upper()}: duplicate logical paths **{item['duplicate_logical_paths']}**, "
            f"parse errors **{item['parse_errors']}**, "
            f"model parent cycles **{len(item['model_parent_cycles'])}**"
        )
    lines.extend(
        [
            "",
            "The JSON comparison is the canonical machine-readable output. "
            "Only derived paths, hashes, reference metadata, and diagnostics are stored.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--frontier", type=Path, required=True)
    parser.add_argument("--expected-anchor-commit")
    parser.add_argument("--expected-frontier-commit")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()

    anchor = load_graph(args.anchor)
    frontier = load_graph(args.frontier)
    validate_graph(anchor, args.expected_anchor_commit)
    validate_graph(frontier, args.expected_frontier_commit)
    comparison = compare_graphs(anchor, frontier)
    comparison["input_graphs"] = {
        "anchor": {"file": args.anchor.name, "sha256": sha256_file(args.anchor)},
        "frontier": {"file": args.frontier.name, "sha256": sha256_file(args.frontier)},
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(summary_markdown(comparison), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
