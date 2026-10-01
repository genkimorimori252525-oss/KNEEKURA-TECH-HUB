"""Real Blockbench desktop acceptance driver for the guarded M2 asset path.

This helper is intentionally CI/local-fixture scoped. It prepares an isolated profile,
loads no plugin itself, and never embeds the private guard token in retained evidence.
The desktop/plugin load is performed by the fixed CDP helper; asset calls still travel
through the authenticated guarded loopback protocol implemented in the product code.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import sys

from kneekura_tech_hub.minecraft.asset_contract import (
    PROVIDER_ID, PROVIDER_REVISION, prepare_request, provider_pin,
)
from kneekura_tech_hub.minecraft.asset_guard import load_request, prepare_guarded_package
from kneekura_tech_hub.minecraft.asset_session import run_session, run_mutation
from kneekura_tech_hub.minecraft.asset_mutation import bounded_read, json_equal, load_snapshot
from kneekura_tech_hub.minecraft.asset_comparison import compare_captures
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


def capture_evidence(store: Store, receipt_hash: str, export_hash: str) -> dict:
    """Retain only this fixed fixture's exact non-secret CAS closure for import."""
    receipt = store.json(receipt_hash)
    request, _ = load_request(store, receipt["request_hash"])
    exported = store.json(export_hash)
    if exported.get("capture_receipt_hash") != receipt_hash:
        raise ValueError("Export and capture evidence differ")
    keys = {receipt_hash, export_hash, receipt["request_hash"], receipt["plan_hash"],
            receipt["inspection_hash"], request["profile_record_hash"], request["spec_hash"],
            request["style_hash"], *request["reference_hashes"],
            *(a["content_hash"] for a in receipt["artifacts"]),
            *(a["content_hash"] for a in exported["files"])}
    if request.get("index_snapshot_id"):
        keys.add(request["index_snapshot_id"])
    # Schema-2 repair evidence retains only its bounded exact parent closure.
    current = receipt
    seen = {receipt_hash}
    for _ in range(33):
        if current.get('schema_version') != 2:
            break
        keys.add(current['snapshot_hash'])
        if current['generation'] == 0:
            break
        keys.add(current['mutation_hash'])
        parent = current['parent_receipt_hash']
        if parent in seen:
            raise ValueError('Cyclic repair closure')
        seen.add(parent); keys.add(parent)
        current = json.loads(bounded_read(store, parent, 1024 * 1024))
        keys.update([current['plan_hash'], current['inspection_hash'],
                     *(a['content_hash'] for a in current['artifacts'])])
    else:
        raise ValueError('Repair evidence closure exceeds generation limit')
    objects = {}
    size = 0
    for key in sorted(keys):
        raw = bounded_read(store, key, 1024 * 1024)
        size += len(raw)
        if size > 8 * 1024 * 1024:
            raise ValueError("Captured evidence closure exceeds budget")
        objects[key] = base64.b64encode(raw).decode("ascii")
    return {"schema_version": 1, "receipt_hash": receipt_hash,
            "export_manifest_hash": export_hash, "encoding": "base64", "objects": objects}


def run(root: Path, evidence: Path, *, repairs: bool = False) -> dict:
    root = _runner_root(root)
    evidence.mkdir(parents=True, exist_ok=True)
    context = json.loads((root / "context-private.json").read_text(encoding="utf-8"))
    store = Store(context["store_root"])
    package = Path(context["package_directory"])
    private_config = json.loads((package / "client-private.json").read_text(encoding="utf-8"))
    registry = {
        "schema_version": 1, "provider": PROVIDER_ID, "revision": PROVIDER_REVISION,
        "port": context["bridge_port"], "allow_session": True,
        "timeout_seconds": 20, "max_response_bytes": 2 * 1024 * 1024,
    }
    result = run_session(store, registry, private_config, context["plan"], retain_generation=repairs)
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
    with (evidence / "capture-evidence.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(capture_evidence(store, result["receipt_hash"], exported["manifest_hash"]), indent=2))
    output = {**safe, "export": exported}
    if repairs:
        repair_evidence = evidence / 'repairs'
        repair_evidence.mkdir(mode=0o700)
        output['repairs'] = run_repairs(store, registry, private_config, result, repair_evidence)
    return output



def staff_repair_cases() -> list[dict]:
    """Declared regression faults, not defects asserted in the accepted staff."""
    return [
        {'id':'part','operation':'part_edit','target':{'part_id':'star_up','property':'to','axis':1},
         'fault':30,'repair':28.5},
        {'id':'uv','operation':'uv_edit','target':{'part_id':'star_core','face':'north','texture_id':'atlas'},
         'fault':[0,0,4,4],'repair':[24,24,28,28]},
        {'id':'texture','operation':'texture_edit','target':{'texture_id':'atlas','rect':[24,24,32,32]},
         'fault':'#d4af37','repair':'#864fc7'},
        {'id':'display','operation':'display_edit','target':{'slot':'thirdperson_righthand','property':'translation','axis':1},
         'fault':6,'repair':4},
    ]


def _repair_intent(store, receipt_hash, case, value):
    receipt,snapshot=load_snapshot(store,receipt_hash);t=case['target'];op=case['operation']
    if op in ('part_edit','uv_edit'):
        index=[p['part_id'] for p in snapshot['parts']].index(t['part_id'])
        element=snapshot['native']['elements'][index]
        expected=element[t['property']][t['axis']] if op=='part_edit' else element['faces'][t['face']]['uv']
    elif op=='display_edit':
        expected=snapshot['native']['display'][t['slot']].get(t['property'],[1,1,1] if t['property']=='scale' else [0,0,0])[t['axis']]
    else:
        x0,y0,x1,y1=t['rect'];width=snapshot['texture']['width'];pixels=base64.b64decode(snapshot['texture']['rgba'],validate=True)
        expected=digest(b''.join(pixels[(y*width+x0)*4:(y*width+x1)*4] for y in range(y0,y1)))
    return {'schema_version':1,'request_hash':receipt['request_hash'],'project_uuid':receipt['project_uuid'],
        'expected_generation':receipt['generation'],'expected_snapshot_hash':receipt['snapshot_hash'],
        'operation':op,'target':t,'expected':expected,'value':value}


def _retain_repair_capture(store, result, directory):
    directory.mkdir(mode=0o700)
    copied=[_copy_artifact(store,item,directory) for item in result['artifacts']]
    exported=materialize_asset(store,result['receipt_hash'],parent=directory)
    safe_export={k:v for k,v in exported.items() if k!='directory'}
    (directory/'capture.json').write_bytes(canonical({**result,'retained_files':copied}))
    (directory/'export.json').write_bytes(canonical(safe_export))
    return safe_export


def run_repairs(store, registry, config, baseline, evidence):
    """Run each exact fault/repair once; any uncertain operation stops the trial."""
    initial_receipt,initial_snapshot=load_snapshot(store,baseline['receipt_hash'])
    if initial_receipt['generation']!=0:
        raise ValueError('Repair trial requires its just-created sealed initial generation')
    current=baseline;cases=[];last_export=None
    bounds_case={'id':'camera-control','operation':'part_edit',
        'target':{'part_id':'halo_top','property':'to','axis':1},'fault':31,'repair':32}
    for case in [*staff_repair_cases(),bounds_case]:
        before=run_mutation(store,registry,config,current['receipt_hash'],
                            _repair_intent(store,current['receipt_hash'],case,case['fault']))
        before_export=_retain_repair_capture(store,before,evidence/(case['id']+'-before'))
        after=run_mutation(store,registry,config,before['receipt_hash'],
                           _repair_intent(store,before['receipt_hash'],case,case['repair']))
        last_export=_retain_repair_capture(store,after,evidence/(case['id']+'-after'))
        comparison=compare_captures(store,before['receipt_hash'],after['receipt_hash'])
        if comparison['comparability']!='COMPARABLE':
            raise ValueError('Actual repair capture conditions are not comparable')
        _,restored=load_snapshot(store,after['receipt_hash'])
        restored['generation']=initial_snapshot['generation']
        if not json_equal(restored,initial_snapshot):
            raise ValueError('Repair did not restore the complete initial effective asset')
        entry={'case':case['id'],'operation':case['operation'],'target':case['target'],
            'before_receipt_hash':before['receipt_hash'],'after_receipt_hash':after['receipt_hash'],
            'before_generation':before['generation'],'after_generation':after['generation'],
            'before_export_manifest_hash':before_export['manifest_hash'],
            'after_export_manifest_hash':last_export['manifest_hash'],'comparison':comparison,
            'verification':{'structural':'PASS','visual':'NOT_RUN','runtime':'NOT_RUN'}}
        if case['id']=='camera-control':
            _,bad=load_snapshot(store,before['receipt_hash'])
            maxima=lambda snap:[max(e['to'][axis] for e in snap['native']['elements']) for axis in range(3)]
            entry['scene_bounds_changed']=maxima(bad)!=maxima(restored)
            if not entry['scene_bounds_changed']:
                raise ValueError('Camera control did not change scene bounds')
            camera_control=entry
        else:
            cases.append(entry)
        current=after
    report={'schema_version':1,'assertion_domain':'live_blockbench_bounded_asset_repair',
        'fixture_faults_injected':True,'request_hash':baseline['request_hash'],'project_uuid':baseline['project_uuid'],
        'initial_receipt_hash':baseline['receipt_hash'],'final_receipt_hash':current['receipt_hash'],
        'final_generation':current['generation'],'cases':cases,'camera_control':camera_control,
        'loaded_revision':'UNATTESTED','outcome':'NOT_RUN',
        'verification':{'structural':'PASS','visual':'NOT_RUN','runtime':'NOT_RUN'}}
    (evidence/'repairs.json').write_bytes(canonical(report))
    (evidence/'capture-evidence.json').write_bytes(canonical(capture_evidence(store,current['receipt_hash'],last_export['manifest_hash'])))
    return report

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
    r.add_argument("--repairs", action="store_true", help="Run the bounded retained staff repair trial")
    args = parser.parse_args(argv)
    try:
        result = prepare(args.root, args.plugin_source, args.evidence) if args.command == "prepare" else run(args.root, args.evidence, repairs=args.repairs)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"schema_version": 1, "status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
