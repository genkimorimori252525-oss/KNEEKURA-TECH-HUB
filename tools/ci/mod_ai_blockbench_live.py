"""Real Blockbench desktop acceptance driver for the guarded M2 asset path.

This helper is intentionally CI/local-fixture scoped. It prepares an isolated profile,
loads no plugin itself, and never embeds the private guard token in retained evidence.
The desktop/plugin load is performed by the fixed CDP helper; asset calls still travel
through the authenticated guarded loopback protocol implemented in the product code.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from kneekura_tech_hub.minecraft.asset_contract import (
    PROVIDER_ID, PROVIDER_REVISION, prepare_request, provider_pin,
)
from kneekura_tech_hub.minecraft.asset_guard import prepare_guarded_package
from kneekura_tech_hub.minecraft.asset_session import run_session
from kneekura_tech_hub.minecraft.asset_export import materialize_asset
from kneekura_tech_hub.minecraft.storage import Store, canonical, capture_profile, digest


def blockbench_release() -> dict:
    return {
        "version": "5.2.1",
        "source_revision": "e2ede0809ee6bc91f374ac7e00d34cffbdf86a14",
        "deb_url": "https://github.com/JannisX11/blockbench/releases/download/v5.2.1/Blockbench_5.2.1.deb",
        "deb_sha256": "d6329fd8db35a6e1ffb86c3f61b77ff193c6526418e6454e1cac863a0e384003",
    }


def plugin_permissions() -> dict:
    # The guarded derivative still needs the upstream bridge's loopback listener.
    # No filesystem/process/shell/clipboard/child-process permission is pre-granted.
    return {"blockbench_mcp": {"allowed": {"net": True}}}


def celestial_staff_plan(request_hash: str) -> dict:
    # An open stepped gold halo, with air separating every purple star tip.
    # UVs reserve the lower-right atlas quadrant for the accent color.
    cubes = [
        ("shaft_bottom", [7, 0, 7], [9, 8, 9], [0, 0, 2, 8]),
        ("shaft_mid", [7, 8, 7], [9, 18, 9], [2, 0, 4, 10]),
        ("collar", [6, 15, 6], [10, 17, 10], [4, 0, 8, 4]),
        ("halo_left", [0, 22, 7], [2, 28, 9], [8, 0, 10, 6]),
        ("halo_right", [14, 22, 7], [16, 28, 9], [10, 0, 12, 6]),
        ("halo_top", [4, 30, 7], [12, 32, 9], [12, 0, 20, 2]),
        ("halo_bottom", [4, 18, 7], [12, 20, 9], [12, 2, 20, 4]),
        ("halo_top_left", [2, 28, 7], [4, 30, 9], [20, 0, 22, 2]),
        ("halo_top_right", [12, 28, 7], [14, 30, 9], [20, 0, 22, 2]),
        ("halo_bottom_left", [2, 20, 7], [4, 22, 9], [20, 0, 22, 2]),
        ("halo_bottom_right", [12, 20, 7], [14, 22, 9], [20, 0, 22, 2]),
        ("star_core", [7, 24, 7], [9, 26, 9], [24, 24, 28, 28]),
        ("star_up", [7.5, 26, 7], [8.5, 28.5, 9], [24, 24, 28, 28]),
        ("star_down", [7.5, 21.5, 7], [8.5, 24, 9], [24, 24, 28, 28]),
        ("star_left", [4.5, 24.5, 7], [7, 25.5, 9], [24, 24, 28, 28]),
        ("star_right", [9, 24.5, 7], [11.5, 25.5, 9], [24, 24, 28, 28]),
    ]
    return {
        "schema_version": 1,
        "request_hash": request_hash,
        "fill": "#d4af37",
        "texture_regions": [{"rect": [24, 24, 32, 32], "color": "#864fc7"}],
        "cubes": [
            {"name": name, "from": start, "to": end, "uv": uv}
            for name, start, end, uv in cubes
        ],
    }


def _runner_root(path: Path) -> Path:
    root = path.absolute()
    runner = os.environ.get("RUNNER_TEMP")
    if runner:
        base = Path(runner).absolute()
        if root == base or not root.is_relative_to(base):
            raise ValueError("Live Blockbench root must be a child of RUNNER_TEMP")
    return root


def _write_permissions(xdg: Path) -> list[str]:
    raw = canonical(plugin_permissions())
    written = []
    # Electron userData is appData/app.getName(). The duplicate lowercase path
    # keeps this deterministic across package-name casing without granting more APIs.
    for name in ("Blockbench", "blockbench"):
        directory = xdg / name
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "plugin_permissions.json"
        target.write_bytes(raw)
        try:
            target.chmod(0o600)
        except OSError:
            pass
        written.append(str(target))
    return written


def prepare(root: Path, plugin_source: Path, evidence: Path) -> dict:
    root = _runner_root(root)
    if root.exists():
        raise ValueError("Live Blockbench root must be fresh")
    root.mkdir(parents=True)
    evidence.mkdir(parents=True, exist_ok=True)
    private = root / "private"
    private.mkdir(mode=0o700)
    workspace = root / "workspace"
    workspace.mkdir()
    (workspace / "fixture.txt").write_text("KNEEKURA Blockbench desktop acceptance fixture\n", encoding="utf-8")

    store = Store(root / "cas")
    manifest = {
        "schema_version": 1,
        "minecraft": "1.20.1",
        "loader": "forge",
        "loader_version": "47.4.6",
        "java_major": 17,
        "namespace": "mojmap",
        "physical_side": "client",
        "logical_side": "client",
        "track": "ANCHOR",
        "workspace_revision": os.environ.get("GITHUB_SHA", "0" * 40)[:40].ljust(40, "0"),
        "dirty_hash": digest((workspace / "fixture.txt").read_bytes()),
        "toolchain": {"blockbench": blockbench_release()["version"]},
        "roots": [{
            "id": "asset-fixture",
            "path": str(workspace),
            "kind": "directory",
            "scope": "client",
            "role": "source",
            "namespace": "mojmap",
            "stage": "workspace",
            "classloader": "unknown",
            "track": "ANCHOR",
        }],
    }
    profile = capture_profile(manifest, root, store)
    spec = {
        "schema_version": 1,
        "asset_id": "kneekura:celestial_staff",
        "asset_kind": "java_item",
        "visual_brief": "Golden celestial staff with a purple accent and a star inside a halo.",
        "style": {
            "texture_size": [32, 32],
            "palette": {"metal": "#d4af37", "accent": "#864fc7"},
            "pixel_art": True,
            "shading": "minecraft",
        },
        "reference_hashes": [],
        "required_views": ["front", "left", "back"],
    }
    request = prepare_request(store, profile=profile, spec=spec)
    source = plugin_source.absolute()
    if source.is_symlink() or not source.is_file():
        raise ValueError("Pinned sosadly source must be a regular local file")
    package = prepare_guarded_package(
        store,
        request["request_hash"],
        upstream=source.read_bytes(),
        parent=private,
        allow_write=True,
    )
    package_dir = Path(package["package_directory"]).absolute()
    plugin_path = package_dir / "blockbench_mcp.js"
    if not plugin_path.is_file():
        raise RuntimeError("Guard package did not preserve Blockbench plugin identity")

    xdg = root / "xdg"
    permission_files = _write_permissions(xdg)
    context = {
        "schema_version": 1,
        "request_hash": request["request_hash"],
        "store_root": str(store.root.absolute()),
        "package_directory": str(package_dir),
        "plugin_path": str(plugin_path),
        "xdg_config_home": str(xdg.absolute()),
        "bridge_port": 8787,
        "plan": celestial_staff_plan(request["request_hash"]),
    }
    (root / "context-private.json").write_bytes(canonical(context))
    (root / "plugin-path.txt").write_text(str(plugin_path), encoding="utf-8")
    (root / "xdg-path.txt").write_text(str(xdg.absolute()), encoding="utf-8")

    safe = {
        "schema_version": 1,
        "status": "PREPARED",
        "blockbench": blockbench_release(),
        "provider": provider_pin(),
        "request_hash": request["request_hash"],
        "profile_id": profile["profile_id"],
        "guard_manifest_hash": package["manifest_hash"],
        "plugin_sha256": digest(plugin_path.read_bytes()),
        "permission_api_names": ["net"],
        "permission_file_count": len(permission_files),
        "verification": {"structural": "NOT_RUN", "visual": "NOT_RUN", "runtime": "NOT_RUN"},
    }
    (evidence / "preparation.json").write_text(json.dumps(safe, indent=2), encoding="utf-8")
    return safe


def _copy_artifact(store: Store, item: dict, evidence: Path) -> str:
    kind = item["kind"]
    view = item.get("view")
    if kind == "model":
        name = "celestial_staff.model.json"
    elif kind == "native":
        name = "celestial_staff.bbmodel"
    elif kind == "texture":
        name = "celestial_staff.png"
    elif kind == "view" and view:
        name = f"view-{view}.png"
    else:
        raise ValueError("Unexpected captured artifact kind")
    target = evidence / name
    with target.open("xb") as stream:
        stream.write(store.read(item["content_hash"]))
    return name


def run(root: Path, evidence: Path) -> dict:
    root = _runner_root(root)
    evidence.mkdir(parents=True, exist_ok=True)
    context = json.loads((root / "context-private.json").read_text(encoding="utf-8"))
    store = Store(context["store_root"])
    package = Path(context["package_directory"])
    private_config = json.loads((package / "client-private.json").read_text(encoding="utf-8"))
    result = run_session(
        store,
        {
            "schema_version": 1,
            "provider": PROVIDER_ID,
            "revision": PROVIDER_REVISION,
            "port": context["bridge_port"],
            "allow_session": True,
            "timeout_seconds": 20,
            "max_response_bytes": 2 * 1024 * 1024,
        },
        private_config,
        context["plan"],
    )
    copied = [_copy_artifact(store, item, evidence) for item in result["artifacts"]]
    safe = {
        "schema_version": 1,
        "status": result["status"],
        "outcome": result["outcome"],
        "assertion_domain": "live_blockbench_desktop_asset_session",
        "request_hash": result["request_hash"],
        "loaded_revision": result["loaded_revision"],
        "project_uuid": result["project_uuid"],
        "inspection_hash": result["inspection_hash"],
        "receipt_hash": result["receipt_hash"],
        "artifacts": result["artifacts"],
        "retained_files": copied,
        "verification": result["verification"],
        "desktop_environment": "GitHub-hosted Ubuntu/Xvfb",
    }
    with (evidence / "session.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(safe, indent=2))
    # Resource compatibility is a separate check from capture transport. Keep
    # the original receipt and its NOT_RUN visual/runtime gates unchanged.
    exported = materialize_asset(store, result["receipt_hash"], parent=evidence)
    with (evidence / "export.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(exported, indent=2))
    return {**safe, "export": exported}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("prepare")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--plugin-source", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    r = subs.add_parser("run")
    r.add_argument("--root", type=Path, required=True)
    r.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = prepare(args.root, args.plugin_source, args.evidence) if args.command == "prepare" else run(args.root, args.evidence)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"schema_version": 1, "status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
