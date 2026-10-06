#!/usr/bin/env python3
"""Build a machine-readable top-level Java/class index for supplied QB/Garnet source trees.

This tool does not download or publish the original MOD source. Point it at already
authorized/extracted archive roots. It records package/class inheritance metadata
and source/class SHA-256 for reproducible local analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_declaration(text: str):
    package_match = re.search(r"^\s*package\s+([\w.]+)\s*;", text, re.M)
    clean = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    clean = re.sub(r"//.*", " ", clean)
    match = re.search(
        r"\bpublic\s+(?:(abstract|final)\s+)?(class|interface|enum)\s+(\w+)([^\{]*)\{",
        clean,
        re.S,
    )
    if not match:
        match = re.search(
            r"\b(?:(abstract|final)\s+)?(class|interface|enum)\s+(\w+)([^\{]*)\{",
            clean,
            re.S,
        )
    if not match:
        raise ValueError("top-level declaration not found")

    kind = match.group(2)
    name = match.group(3)
    tail = " ".join(match.group(4).split())
    extends = None
    implements = []

    if kind == "interface":
        ext = re.search(r"\bextends\s+(.+)$", tail)
        if ext:
            extends = [x.strip() for x in ext.group(1).split(",") if x.strip()]
    else:
        ext = re.search(r"\bextends\s+([^\s,]+(?:\s*<[^>]+>)?)", tail)
        if ext:
            extends = ext.group(1).strip()
        impl = re.search(r"\bimplements\s+(.+)$", tail)
        if impl:
            implements = [x.strip() for x in impl.group(1).split(",") if x.strip()]

    return package_match.group(1) if package_match else None, kind, name, extends, implements


def collect(label: str, root: Path, source_prefix: str):
    rows = []
    misses = []
    source_root = root / source_prefix
    for source in sorted(source_root.rglob("*.java")):
        rel = source.relative_to(root).as_posix()
        try:
            text = source.read_text("cp932", errors="replace")
            package, kind, name, extends, implements = parse_declaration(text)
        except Exception as exc:
            misses.append({"source_path": rel, "error": str(exc)})
            continue

        class_path = rel[len("MCP/") : -5] + ".class"
        compiled = root / class_path
        rows.append(
            {
                "archive": label,
                "source_path": rel,
                "source_sha256": sha256(source),
                "package": package,
                "kind": kind,
                "name": name,
                "extends": extends,
                "implements": implements,
                "class_path": class_path,
                "class_sha256": sha256(compiled) if compiled.exists() else None,
            }
        )
    return rows, misses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qb-root", type=Path, required=True)
    parser.add_argument("--garnet-root", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--tsv-out", type=Path)
    args = parser.parse_args()

    entries = []
    misses = []
    for label, root, prefix in [
        ("QB-MOD", args.qb_root, "MCP/puellamagi/mods"),
        ("Garnet-MOD", args.garnet_root, "MCP/garnet/mods"),
    ]:
        rows, errors = collect(label, root, prefix)
        entries.extend(rows)
        misses.extend({"archive": label, **e} for e in errors)

    result = {
        "format": "kneekura.madomagi.java-class-map.v1",
        "generated_at": "2026-10-07",
        "entry_count": len(entries),
        "entries": entries,
        "parse_misses": misses,
    }
    args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf-8")

    if args.tsv_out:
        header = [
            "archive", "source_path", "package", "kind", "name",
            "extends", "implements", "source_sha256", "class_path", "class_sha256",
        ]
        lines = ["\t".join(header)]
        for row in entries:
            ext = row["extends"]
            if isinstance(ext, list):
                ext = ",".join(ext)
            values = [
                row["archive"], row["source_path"], row["package"] or "", row["kind"],
                row["name"], ext or "", ",".join(row["implements"]),
                row["source_sha256"], row["class_path"], row["class_sha256"] or "",
            ]
            lines.append("\t".join(values))
        args.tsv_out.write_text("\n".join(lines) + "\n", "utf-8")

    print(json.dumps({
        "entries": len(entries),
        "parse_misses": len(misses),
        "json_sha256": sha256(args.json_out),
        "tsv_sha256": sha256(args.tsv_out) if args.tsv_out else None,
    }, indent=2))


if __name__ == "__main__":
    main()
