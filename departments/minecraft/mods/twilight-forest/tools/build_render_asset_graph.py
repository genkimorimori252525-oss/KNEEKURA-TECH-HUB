#!/usr/bin/env python3
"""Build a complete Twilight Forest block/item render-asset dependency graph.

The tool reads a local full checkout of TeamTwilight/twilightforest. It does not
copy third-party assets into TECH HUB; it emits provenance, dependency edges,
hashes, and unresolved-reference diagnostics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


NAMESPACE = "twilightforest"
ASSET_ROOTS = (
    Path("src/main/resources/assets") / NAMESPACE,
    Path("src/generated/resources/assets") / NAMESPACE,
)


@dataclass(frozen=True)
class AssetFile:
    kind: str
    logical_path: str
    source_path: str
    sha256: str
    size: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(relative: Path) -> str | None:
    parts = relative.parts
    if not parts:
        return None
    if parts[0] == "blockstates" and relative.suffix == ".json":
        return "blockstate"
    if parts[0] == "models" and relative.suffix == ".json":
        return "model"
    if parts[0] == "items" and relative.suffix == ".json":
        return "item_definition"
    if parts[0] == "atlases" and relative.suffix == ".json":
        return "atlas"
    if parts[0] == "textures" and relative.suffix == ".png":
        return "texture"
    return None


def collect_files(source_root: Path) -> tuple[list[AssetFile], dict[str, list[str]]]:
    files: list[AssetFile] = []
    logical_sources: dict[str, list[str]] = defaultdict(list)

    for asset_root_rel in ASSET_ROOTS:
        asset_root = source_root / asset_root_rel
        if not asset_root.exists():
            continue
        for path in sorted(p for p in asset_root.rglob("*") if p.is_file()):
            relative = path.relative_to(asset_root)
            kind = classify(relative)
            if kind is None:
                continue
            logical = relative.as_posix()
            source_path = path.relative_to(source_root).as_posix()
            files.append(
                AssetFile(
                    kind=kind,
                    logical_path=logical,
                    source_path=source_path,
                    sha256=sha256_file(path),
                    size=path.stat().st_size,
                )
            )
            logical_sources[logical].append(source_path)

    return files, dict(logical_sources)


def walk_refs(value: Any, key: str = "", inside_textures: bool = False) -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        if key == "parent":
            yield "parent", value
        elif key == "model":
            yield "model", value
        elif inside_textures or key == "texture":
            yield "texture", value
        elif key in {"resource", "sprite", "source"}:
            yield "resource", value
        return

    if isinstance(value, list):
        for item in value:
            yield from walk_refs(item, key, inside_textures)
        return

    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from walk_refs(
                child,
                child_key,
                inside_textures=inside_textures or child_key == "textures",
            )


def split_resource_location(value: str) -> tuple[str, str] | None:
    if value.startswith("#"):
        return None
    if ":" in value:
        namespace, path = value.split(":", 1)
        return namespace, path
    return "minecraft", value


def expected_local_path(ref_kind: str, value: str) -> str | None:
    parsed = split_resource_location(value)
    if parsed is None:
        return None
    namespace, resource_path = parsed
    if namespace != NAMESPACE:
        return None

    if ref_kind in {"model", "parent"}:
        return f"models/{resource_path}.json"
    if ref_kind == "texture":
        return f"textures/{resource_path}.png"
    return None


def logical_id(kind: str, logical_path: str) -> str:
    return f"{kind}:{NAMESPACE}:{logical_path}"


def find_parent_cycles(model_edges: dict[str, list[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    state: dict[str, int] = {}
    stack: list[str] = []
    position: dict[str, int] = {}

    def visit(node: str) -> None:
        state[node] = 1
        position[node] = len(stack)
        stack.append(node)

        for target in model_edges.get(node, []):
            if state.get(target, 0) == 0:
                visit(target)
            elif state.get(target) == 1:
                start = position[target]
                cycle = stack[start:] + [target]
                if cycle not in cycles:
                    cycles.append(cycle)

        stack.pop()
        position.pop(node, None)
        state[node] = 2

    for node in sorted(model_edges):
        if state.get(node, 0) == 0:
            visit(node)

    return cycles


def build_graph(source_root: Path, source_commit: str | None = None) -> dict[str, Any]:
    files, logical_sources = collect_files(source_root)
    by_logical = set(logical_sources)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    model_parent_edges: dict[str, list[str]] = defaultdict(list)

    for file in files:
        nodes.append(
            {
                "id": logical_id(file.kind, file.logical_path),
                "kind": file.kind,
                "logical_path": file.logical_path,
                "source_path": file.source_path,
                "sha256": file.sha256,
                "size": file.size,
            }
        )

        if file.kind == "texture":
            continue

        source_path = source_root / file.source_path
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except Exception as exc:  # diagnostics are part of output
            parse_errors.append({"path": file.source_path, "error": str(exc)})
            continue

        seen_refs: set[tuple[str, str]] = set()
        for ref_kind, value in walk_refs(payload):
            pair = (ref_kind, value)
            if pair in seen_refs:
                continue
            seen_refs.add(pair)

            target_path = expected_local_path(ref_kind, value)
            target_exists = target_path in by_logical if target_path else None
            edge = {
                "source": logical_id(file.kind, file.logical_path),
                "source_path": file.logical_path,
                "ref_kind": ref_kind,
                "raw_ref": value,
                "target_local_path": target_path,
                "target_exists": target_exists,
            }
            edges.append(edge)

            if target_path and not target_exists:
                unresolved.append(
                    {
                        "source_path": file.logical_path,
                        "ref_kind": ref_kind,
                        "raw_ref": value,
                        "expected_path": target_path,
                    }
                )

            if file.kind == "model" and ref_kind == "parent" and target_path and target_exists:
                model_parent_edges[file.logical_path].append(target_path)

    duplicates = [
        {"logical_path": path, "sources": sources}
        for path, sources in sorted(logical_sources.items())
        if len(sources) > 1
    ]

    counts = defaultdict(int)
    for file in files:
        counts[file.kind] += 1

    return {
        "graph_version": "1.0",
        "target": "The Twilight Forest",
        "namespace": NAMESPACE,
        "source_commit": source_commit,
        "source_root": str(source_root),
        "counts": {
            **dict(sorted(counts.items())),
            "nodes": len(nodes),
            "edges": len(edges),
            "unresolved_local_refs": len(unresolved),
            "duplicate_logical_paths": len(duplicates),
            "parse_errors": len(parse_errors),
        },
        "nodes": nodes,
        "edges": edges,
        "unresolved_local_refs": unresolved,
        "duplicate_logical_paths": duplicates,
        "parse_errors": parse_errors,
        "model_parent_cycles": find_parent_cycles(dict(model_parent_edges)),
    }


def summary_markdown(graph: dict[str, Any]) -> str:
    counts = graph["counts"]
    lines = [
        "# Twilight Forest Render Asset Graph — Generated Summary",
        "",
        f"- source commit: \`{graph.get('source_commit') or 'UNSPECIFIED'}\`",
        f"- blockstates: **{counts.get('blockstate', 0)}**",
        f"- models: **{counts.get('model', 0)}**",
        f"- item definitions: **{counts.get('item_definition', 0)}**",
        f"- atlases: **{counts.get('atlas', 0)}**",
        f"- textures: **{counts.get('texture', 0)}**",
        f"- dependency edges: **{counts.get('edges', 0)}**",
        f"- unresolved local refs: **{counts.get('unresolved_local_refs', 0)}**",
        f"- duplicate logical paths: **{counts.get('duplicate_logical_paths', 0)}**",
        f"- parse errors: **{counts.get('parse_errors', 0)}**",
        f"- model parent cycles: **{len(graph.get('model_parent_cycles', []))}**",
        "",
        "The JSON graph is the canonical machine-readable output.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Full Twilight Forest checkout root")
    parser.add_argument("--source-commit", default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()

    graph = build_graph(args.source_root.resolve(), args.source_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(summary_markdown(graph), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
