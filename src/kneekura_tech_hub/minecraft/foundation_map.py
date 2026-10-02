"""Content-addressed Minecraft 1.20.1 Vanilla Foundation Map.

The map is derived from an already captured Source Intelligence IndexSnapshot. It
never resolves Gradle, downloads artifacts, or starts Minecraft. "Vanilla" here
means ``net/minecraft/**`` classes present in the exact Forge ANCHOR profile; the
origin/stage of every variant is preserved because Forge-patched Minecraft bytes
are not silently relabelled as pristine Mojang source.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from typing import Any

from . import index
from .classfile import read_class
from .storage import ArtifactUnavailable, ContractError, IntegrityError, Store, canonical, key_for, valid_hash


SCHEMA_VERSION = 1
KIND = "minecraft-1.20.1-vanilla-foundation-map"
MAX_CLASSES = 50_000
MAX_REFERENCES_PER_VARIANT = 1_024

# Ordered: the first match is the primary subsystem. More specific namespaces
# must precede their broad parents.
SUBSYSTEM_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ai.goal", ("net/minecraft/world/entity/ai/goal/",)),
    ("ai.behavior", ("net/minecraft/world/entity/ai/behavior/",)),
    ("ai.memory", ("net/minecraft/world/entity/ai/memory/",)),
    ("ai.sensing", ("net/minecraft/world/entity/ai/sensing/",)),
    ("ai.navigation", ("net/minecraft/world/entity/ai/navigation/",)),
    ("ai.control", ("net/minecraft/world/entity/ai/control/",)),
    ("ai.core", ("net/minecraft/world/entity/ai/",)),
    ("pathfinding", ("net/minecraft/world/level/pathfinder/",)),
    ("client.debug", ("net/minecraft/client/renderer/debug/",)),
    ("entity", ("net/minecraft/world/entity/",)),
    ("world.level", ("net/minecraft/world/level/",)),
    ("server", ("net/minecraft/server/",)),
    ("client", ("net/minecraft/client/",)),
    ("network", ("net/minecraft/network/",)),
    ("commands", ("net/minecraft/commands/",)),
    ("data", ("net/minecraft/data/",)),
    ("resources", ("net/minecraft/resources/",)),
    ("core", ("net/minecraft/core/",)),
)

# Discovery anchors are not an exhaustive definition of Minecraft. They provide
# a small, stable readiness surface for the Foundation Map and its AI use cases.
ANCHOR_OWNERS = (
    "net/minecraft/world/entity/Mob",
    "net/minecraft/world/entity/ai/goal/GoalSelector",
    "net/minecraft/world/entity/ai/Brain",
    "net/minecraft/world/entity/ai/navigation/PathNavigation",
    "net/minecraft/world/entity/ai/control/MoveControl",
    "net/minecraft/world/level/pathfinder/PathFinder",
    "net/minecraft/world/level/pathfinder/NodeEvaluator",
    "net/minecraft/world/level/pathfinder/Path",
    "net/minecraft/world/level/pathfinder/Node",
    "net/minecraft/client/renderer/debug/PathfindingRenderer",
    "net/minecraft/client/renderer/debug/GoalSelectorDebugRenderer",
    "net/minecraft/client/renderer/debug/BrainDebugRenderer",
    "net/minecraft/network/protocol/game/DebugPackets",
)


def _subsystem(owner: str) -> str:
    for name, prefixes in SUBSYSTEM_RULES:
        if owner.startswith(prefixes):
            return name
    return "minecraft.other"


def _package(owner: str) -> str:
    return owner.rsplit("/", 1)[0] if "/" in owner else ""


def _simple(owner: str) -> str:
    return owner.rsplit("/", 1)[-1]


def _foundation_profile(snapshot: dict) -> dict:
    profile = snapshot.get("profile")
    if not isinstance(profile, dict):
        raise IntegrityError("IndexSnapshot has no profile")
    manifest = profile.get("manifest")
    if not isinstance(manifest, dict):
        raise IntegrityError("IndexSnapshot profile has no manifest")
    if manifest.get("track") != "ANCHOR":
        raise ContractError("Foundation Map requires an ANCHOR IndexSnapshot")
    if manifest.get("minecraft") != "1.20.1":
        raise ContractError("Foundation Map requires Minecraft 1.20.1")
    if manifest.get("loader") != "forge":
        raise ContractError("Foundation Map requires a Forge ANCHOR profile")
    if manifest.get("namespace") != "mojmap":
        raise ContractError("Foundation Map requires a Mojmap project namespace")
    return profile


def _origin(identifier: str, doc: dict) -> dict:
    loc = index.locator(identifier, doc)
    return {
        "document_id": doc["document_id"],
        "artifact_hash": doc["artifact_hash"],
        "content_hash": doc["content_hash"],
        "root_id": doc["root_id"],
        "root_order": doc["root_order"],
        "path": doc["path"],
        "scope": doc["scope"],
        "role": doc["role"],
        "namespace": doc["namespace"],
        "stage": doc["stage"],
        "classloader": doc["classloader"],
        "evidence": loc,
    }


def _variant(content_hash: str, parsed: dict, origins: list[dict]) -> dict:
    refs = sorted({
        ref for ref in parsed.get("class_references", [])
        if isinstance(ref, str) and ref.startswith("net/minecraft/")
        and ref != parsed["owner"]
    })
    truncated = len(refs) > MAX_REFERENCES_PER_VARIANT
    return {
        "content_hash": content_hash,
        "classfile_major": parsed["major"],
        "access": parsed["access"],
        "superclass": parsed["superclass"],
        "interfaces": sorted(parsed["interfaces"]),
        "references": refs[:MAX_REFERENCES_PER_VARIANT],
        "references_truncated": truncated,
        "origins": sorted(origins, key=lambda o: (
            o["root_order"], o["scope"], o["stage"], o["path"]
        )),
    }


def build(store: Store, index_snapshot_id: str, *, max_classes: int = 20_000) -> dict:
    """Build and pin a compact structural map from an immutable IndexSnapshot.

    This is a pure read of captured inputs plus one derived CAS write. It does
    not prepare bytecode, resolve dependencies, or execute build/game code.
    """
    index._positive(max_classes, MAX_CLASSES)
    snapshot = index._load(store, valid_hash(index_snapshot_id))
    profile = _foundation_profile(snapshot)

    all_class_docs = [
        d for d in profile["documents"]
        if d.get("media") == "class"
        and d.get("track") == "ANCHOR"
        and d.get("namespace") == "mojmap"
        and d.get("scope") != "buildscript"
    ]
    # A JVM class is normally loaded from <internal-owner>.class. Restricting the
    # expensive classfile pass to the net/minecraft path keeps the Foundation
    # Map independent of the potentially huge MOD/library classpath.
    selected_docs = [
        d for d in all_class_docs
        if d.get("path", "").startswith("net/minecraft/")
    ]

    # Group exact same class bytes first. Multiple origins of identical bytes
    # are provenance, while different bytes for one owner are ambiguity.
    by_owner_hash: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    unreadable: list[dict[str, Any]] = []
    path_owner_mismatches: list[dict[str, Any]] = []
    parsed_count = 0
    budget_truncated = False

    for doc in selected_docs:
        if parsed_count >= max_classes:
            budget_truncated = True
            break
        try:
            raw = store.read(doc["content_hash"])
            parsed = read_class(raw)
        except (OSError, ValueError, TypeError, KeyError, ContractError,
                IntegrityError, ArtifactUnavailable) as exc:
            unreadable.append({
                "document_id": doc.get("document_id"),
                "root_id": doc.get("root_id"),
                "path": doc.get("path"),
                "reason": f"{type(exc).__name__}: {exc}",
            })
            continue

        owner = parsed["owner"]
        if not owner.startswith("net/minecraft/"):
            path_owner_mismatches.append({
                "document_id": doc["document_id"],
                "path": doc["path"],
                "owner": owner,
            })
            continue
        parsed_count += 1
        digest = doc["content_hash"]
        bucket = by_owner_hash[owner]
        if digest not in bucket:
            bucket[digest] = {"parsed": parsed, "origins": []}
        bucket[digest]["origins"].append(_origin(index_snapshot_id, doc))

    classes: list[dict[str, Any]] = []
    edges_by_id: dict[str, dict[str, Any]] = {}
    package_counts: Counter[str] = Counter()
    subsystem_counts: Counter[str] = Counter()
    reference_truncations = 0
    ambiguous_owners: list[str] = []

    def edge(relation: str, source: str, target: str, variant_hash: str) -> None:
        if not target or not target.startswith("net/minecraft/") or source == target:
            return
        value = {
            "relation": relation,
            "source": source,
            "target": target,
            "variant_hash": variant_hash,
        }
        edges_by_id[key_for(value)] = value

    for owner in sorted(by_owner_hash):
        variants = []
        for content_hash, item in sorted(by_owner_hash[owner].items()):
            v = _variant(content_hash, item["parsed"], item["origins"])
            variants.append(v)
            reference_truncations += int(v["references_truncated"])
            if v["superclass"]:
                edge("extends", owner, v["superclass"], content_hash)
            for interface in v["interfaces"]:
                edge("implements", owner, interface, content_hash)
            for target in v["references"]:
                edge("references_class", owner, target, content_hash)

        ambiguous = len(variants) > 1
        if ambiguous:
            ambiguous_owners.append(owner)
        subsystem = _subsystem(owner)
        package = _package(owner)
        package_counts[package] += 1
        subsystem_counts[subsystem] += 1
        classes.append({
            "owner": owner,
            "simple_name": _simple(owner),
            "package": package,
            "subsystem": subsystem,
            "ambiguous_variants": ambiguous,
            "variant_count": len(variants),
            "variants": variants,
        })

    owners = {c["owner"]: c for c in classes}
    anchors = []
    missing_anchors = []
    ambiguous_anchors = []
    for owner in ANCHOR_OWNERS:
        entry = owners.get(owner)
        if entry is None:
            state = "MISSING"
            missing_anchors.append(owner)
        elif entry["ambiguous_variants"]:
            state = "AMBIGUOUS"
            ambiguous_anchors.append(owner)
        else:
            state = "PRESENT"
        anchors.append({"owner": owner, "state": state})

    profile_complete = bool(profile.get("coverage", {}).get("complete"))
    profile_identity_pinned = profile.get("identity_status") == "PINNED"
    complete = (
        profile_complete
        and profile_identity_pinned
        and not unreadable
        and not path_owner_mismatches
        and not budget_truncated
        and not missing_anchors
        and not ambiguous_anchors
        and reference_truncations == 0
    )
    coverage = {
        "complete": complete,
        "profile_complete": profile_complete,
        "profile_identity_status": profile.get("identity_status"),
        "all_anchor_class_documents": len(all_class_docs),
        "selected_minecraft_class_documents": len(selected_docs),
        "excluded_non_minecraft_class_documents": len(all_class_docs) - len(selected_docs),
        "parsed_minecraft_class_documents": parsed_count,
        "unique_minecraft_owners": len(classes),
        "path_owner_mismatches": path_owner_mismatches,
        "unreadable": unreadable,
        "budget_truncated": budget_truncated,
        "max_classes": max_classes,
        "ambiguous_owner_count": len(ambiguous_owners),
        "ambiguous_owners": ambiguous_owners[:256],
        "ambiguous_owners_truncated": len(ambiguous_owners) > 256,
        "reference_truncation_count": reference_truncations,
        "missing_anchors": missing_anchors,
        "ambiguous_anchors": ambiguous_anchors,
        "source_semantics": "FORGE_ANCHOR_NET_MINECRAFT_CLASSES_WITH_ORIGIN_PRESERVED",
    }

    manifest = profile["manifest"]
    map_doc = {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "source_index_snapshot_id": index_snapshot_id,
        "index_snapshot_id": index_snapshot_id,
        "profile_id": profile["profile_id"],
        "profile_hash": profile["profile_hash"],
        "environment": {
            "minecraft": manifest["minecraft"],
            "loader": manifest["loader"],
            "loader_version": manifest.get("loader_version"),
            "java_major": manifest.get("java_major"),
            "namespace": manifest.get("namespace"),
            "track": manifest.get("track"),
            "physical_side": manifest.get("physical_side"),
            "logical_side": manifest.get("logical_side"),
            "workspace_revision": manifest.get("workspace_revision"),
            "resolution": profile.get("resolution"),
            "identity_status": profile.get("identity_status"),
        },
        "semantics": {
            "name": "Minecraft 1.20.1 Vanilla Foundation Map",
            "minecraft_scope": "net/minecraft/** from exact captured Forge ANCHOR profile",
            "not_a_claim_of": [
                "pristine Mojang source bytes",
                "runtime-loaded byte identity",
                "dynamic call graph",
                "complete reflection/mixin behavior",
            ],
            "class_reference_semantics": "JVM CONSTANT_Class structural/reference candidates",
        },
        "anchors": anchors,
        "subsystems": [
            {"name": name, "class_count": subsystem_counts[name]}
            for name in sorted(subsystem_counts)
        ],
        "packages": [
            {"package": package, "class_count": package_counts[package]}
            for package in sorted(package_counts)
        ],
        "classes": classes,
        "edges": sorted(edges_by_id.values(), key=lambda e: (
            e["source"], e["relation"], e["target"], e["variant_hash"]
        )),
        "coverage": coverage,
    }
    foundation_map_id = store.put_json(map_doc)
    store.pin(foundation_map_id, f"vanilla-foundation-map:{index_snapshot_id}")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "OK" if complete else "PARTIAL",
        "foundation_map_id": foundation_map_id,
        "source_index_snapshot_id": index_snapshot_id,
        "profile_id": profile["profile_id"],
        "class_count": len(classes),
        "edge_count": len(map_doc["edges"]),
        "coverage": coverage,
        "anchors": anchors,
    }


def _load(store: Store, foundation_map_id: str) -> dict:
    value = store.json(valid_hash(foundation_map_id))
    if value.get("schema_version") != SCHEMA_VERSION or value.get("kind") != KIND:
        raise IntegrityError("Artifact is not a Vanilla Foundation Map")
    if not isinstance(value.get("classes"), list) or not isinstance(value.get("edges"), list):
        raise IntegrityError("Malformed Vanilla Foundation Map")
    return value


def _reply(value: dict, foundation_map_id: str, status: str, results: list,
           *, coverage: dict | None = None, cursor: str | None = None) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "foundation_map_id": foundation_map_id,
        "source_index_snapshot_id": value["source_index_snapshot_id"],
        "index_snapshot_id": value["source_index_snapshot_id"],
        "profile_id": value["profile_id"],
        "results": results,
        "coverage": json.loads(canonical(coverage if coverage is not None else value["coverage"])),
        "warnings": [],
        "next_cursor": cursor,
    }


def search(store: Store, foundation_map_id: str, query: str, *, subsystem: str | None = None,
           limit: int = 20, cursor: str | None = None) -> dict:
    """Search owners/packages/subsystems without touching external sources."""
    index._positive(limit, 1000)
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise ContractError("A nonempty Foundation Map query is required")
    value = _load(store, foundation_map_id)
    if subsystem is not None and subsystem not in {x["name"] for x in value["subsystems"]}:
        raise ContractError("Unknown Foundation Map subsystem")
    request = {"operation": "foundation-search", "query": query, "subsystem": subsystem}
    offset = index._offset(cursor, foundation_map_id, request)
    if offset is None:
        return _reply(value, foundation_map_id, "STALE", [])

    needle = query.casefold()
    matches = []
    for item in value["classes"]:
        if subsystem is not None and item["subsystem"] != subsystem:
            continue
        haystack = "\n".join((
            item["owner"], item["simple_name"], item["package"], item["subsystem"]
        )).casefold()
        if needle in haystack:
            matches.append({
                "owner": item["owner"],
                "simple_name": item["simple_name"],
                "package": item["package"],
                "subsystem": item["subsystem"],
                "ambiguous_variants": item["ambiguous_variants"],
                "variant_count": item["variant_count"],
            })
    matches.sort(key=lambda x: (x["owner"].casefold().find(needle), x["owner"]))
    page = matches[offset:offset + limit]
    end = offset + len(page)
    more = end < len(matches)
    coverage = {
        **value["coverage"],
        "matching_classes": len(matches),
        "query_scope": "foundation_class_owner_package_subsystem",
        "truncated": more,
    }
    status = "PARTIAL" if more or not value["coverage"]["complete"] else ("OK" if page else "NOT_FOUND")
    return _reply(
        value, foundation_map_id, status, page, coverage=coverage,
        cursor=index._cursor(foundation_map_id, request, end) if more else None,
    )


def inspect(store: Store, foundation_map_id: str, owner: str) -> dict:
    if not isinstance(owner, str) or not owner.startswith("net/minecraft/"):
        raise ContractError("Exact net/minecraft internal owner is required")
    value = _load(store, foundation_map_id)
    item = next((x for x in value["classes"] if x["owner"] == owner), None)
    if item is None:
        status = "PARTIAL" if not value["coverage"]["complete"] else "NOT_FOUND"
        return _reply(value, foundation_map_id, status, [])

    outgoing = [e for e in value["edges"] if e["source"] == owner]
    incoming = [e for e in value["edges"] if e["target"] == owner]
    result = dict(item)
    result["relations"] = {
        "outgoing": outgoing[:1000],
        "incoming": incoming[:1000],
        "outgoing_total": len(outgoing),
        "incoming_total": len(incoming),
        "truncated": len(outgoing) > 1000 or len(incoming) > 1000,
    }
    status = "AMBIGUOUS" if item["ambiguous_variants"] else (
        "PARTIAL" if not value["coverage"]["complete"] else "OK"
    )
    return _reply(value, foundation_map_id, status, [result])


def subsystems(store: Store, foundation_map_id: str) -> dict:
    value = _load(store, foundation_map_id)
    status = "OK" if value["coverage"]["complete"] else "PARTIAL"
    return _reply(value, foundation_map_id, status, value["subsystems"])
