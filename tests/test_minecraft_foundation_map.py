import importlib
import shutil
import subprocess
from pathlib import Path

import pytest

from test_minecraft_storage import manifest


def mod(name):
    return importlib.import_module("kneekura_tech_hub.minecraft." + name)


ANCHORS = [
    ("net/minecraft/world/entity", "Mob"),
    ("net/minecraft/world/entity/ai/goal", "GoalSelector"),
    ("net/minecraft/world/entity/ai", "Brain"),
    ("net/minecraft/world/entity/ai/navigation", "PathNavigation"),
    ("net/minecraft/world/entity/ai/control", "MoveControl"),
    ("net/minecraft/world/level/pathfinder", "PathFinder"),
    ("net/minecraft/world/level/pathfinder", "NodeEvaluator"),
    ("net/minecraft/world/level/pathfinder", "Path"),
    ("net/minecraft/world/level/pathfinder", "Node"),
    ("net/minecraft/client/renderer/debug", "PathfindingRenderer"),
    ("net/minecraft/client/renderer/debug", "GoalSelectorDebugRenderer"),
    ("net/minecraft/client/renderer/debug", "BrainDebugRenderer"),
    ("net/minecraft/network/protocol/game", "DebugPackets"),
]


def _write_java(root: Path, package_path: str, name: str, body: str = "") -> Path:
    package = package_path.replace("/", ".")
    folder = root / package_path
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.java"
    path.write_text(f"package {package}; public class {name} {{ {body} }}\n")
    return path


@pytest.fixture
def foundation(tmp_path):
    if not shutil.which("javac"):
        pytest.skip("JDK required for Foundation Map classfile fixture")
    src = tmp_path / "java"
    sources = [_write_java(src, package, name) for package, name in ANCHORS]
    sources.append(_write_java(
        src,
        "net/minecraft/client/renderer/debug",
        "DebugRenderer",
        "public final PathfindingRenderer pathfindingRenderer = new PathfindingRenderer();",
    ))
    sources.append(_write_java(src, "example/mod", "NotMinecraft"))
    classes = tmp_path / "classes"
    subprocess.run(
        ["javac", "--release", "17", "-g", "-d", str(classes), *map(str, sources)],
        check=True,
        capture_output=True,
    )
    storage = mod("storage")
    store = storage.Store(tmp_path / "cache")
    profile = storage.capture_profile(manifest("classes"), tmp_path, store)
    prepared = mod("index").prepare_index(profile, store)
    return store, prepared, tmp_path


def test_foundation_map_builds_from_exact_anchor_without_javap(foundation):
    store, prepared, _ = foundation
    fm = mod("foundation_map")
    result = fm.build(store, prepared["index_snapshot_id"])
    assert result["status"] == "OK"
    assert result["class_count"] == len(ANCHORS) + 1
    assert not result["coverage"]["missing_anchors"]
    assert result["coverage"]["skipped_non_minecraft_classes"] == 1
    assert result["foundation_map_id"] in store.pinned_hashes()


def test_foundation_search_finds_pathfinding_debug_surface(foundation):
    store, prepared, _ = foundation
    fm = mod("foundation_map")
    built = fm.build(store, prepared["index_snapshot_id"])
    result = fm.search(store, built["foundation_map_id"], "Pathfinding")
    owners = {row["owner"] for row in result["results"]}
    assert "net/minecraft/client/renderer/debug/PathfindingRenderer" in owners
    assert "net/minecraft/world/level/pathfinder/PathFinder" not in owners
    subsystem = fm.search(
        store, built["foundation_map_id"], "Renderer", subsystem="client.debug"
    )
    assert all(row["subsystem"] == "client.debug" for row in subsystem["results"])


def test_foundation_inspect_exposes_structural_reference_candidates(foundation):
    store, prepared, _ = foundation
    fm = mod("foundation_map")
    built = fm.build(store, prepared["index_snapshot_id"])
    owner = "net/minecraft/client/renderer/debug/DebugRenderer"
    result = fm.inspect(store, built["foundation_map_id"], owner)
    assert result["status"] == "OK"
    outgoing = result["results"][0]["relations"]["outgoing"]
    assert any(
        edge["relation"] == "references_class"
        and edge["target"] == "net/minecraft/client/renderer/debug/PathfindingRenderer"
        for edge in outgoing
    )


def test_classfile_reference_candidates_are_available_without_javap(foundation):
    store, prepared, _ = foundation
    snap = mod("index")._load(store, prepared["index_snapshot_id"])
    doc = next(
        d for d in snap["profile"]["documents"]
        if d["path"].endswith("net/minecraft/client/renderer/debug/DebugRenderer.class")
    )
    parsed = mod("classfile").read_class(store.read(doc["content_hash"]))
    assert "net/minecraft/client/renderer/debug/PathfindingRenderer" in parsed["class_references"]


def test_foundation_map_refuses_non_anchor_profile(tmp_path):
    if not shutil.which("javac"):
        pytest.skip("JDK required for Foundation Map classfile fixture")
    src = _write_java(tmp_path / "java", "net/minecraft/world/entity", "Mob")
    classes = tmp_path / "classes"
    subprocess.run(
        ["javac", "--release", "17", "-d", str(classes), str(src)],
        check=True,
        capture_output=True,
    )
    storage = mod("storage")
    m = manifest("classes")
    m["track"] = "FRONTIER"
    m["roots"][0]["track"] = "FRONTIER"
    store = storage.Store(tmp_path / "cache")
    profile = storage.capture_profile(m, tmp_path, store)
    prepared = mod("index").prepare_index(profile, store)
    with pytest.raises(storage.ContractError, match="ANCHOR"):
        mod("foundation_map").build(store, prepared["index_snapshot_id"])


def test_foundation_map_preserves_conflicting_class_origins(tmp_path):
    if not shutil.which("javac"):
        pytest.skip("JDK required for Foundation Map classfile fixture")
    roots = []
    for i, value in enumerate((1, 2)):
        src_root = tmp_path / f"src{i}"
        src = _write_java(
            src_root, "net/minecraft/world/entity", "Mob",
            f"public int marker() {{ return {value}; }}",
        )
        classes = tmp_path / f"classes{i}"
        subprocess.run(
            ["javac", "--release", "17", "-d", str(classes), str(src)],
            check=True,
            capture_output=True,
        )
        roots.append(classes)

    storage = mod("storage")
    m = manifest(str(roots[0]), "directory")
    m["roots"][0]["path"] = str(roots[0])
    m["roots"].append(dict(m["roots"][0], id="second", path=str(roots[1])))
    store = storage.Store(tmp_path / "cache")
    profile = storage.capture_profile(m, tmp_path, store)
    prepared = mod("index").prepare_index(profile, store)
    built = mod("foundation_map").build(store, prepared["index_snapshot_id"])
    assert built["status"] == "PARTIAL"
    inspected = mod("foundation_map").inspect(
        store, built["foundation_map_id"], "net/minecraft/world/entity/Mob"
    )
    assert inspected["status"] == "AMBIGUOUS"
    item = inspected["results"][0]
    assert item["variant_count"] == 2
    assert len({v["content_hash"] for v in item["variants"]}) == 2
