#!/usr/bin/env python3
"""Build a bounded semantic Foundation Map for the exact YSM 2.6.5 Java shell.

Inputs:
- exact official YSM JAR (temporary/local only)
- KNEEKURA semantic obfuscation map

Output:
- machine-readable class/domain assignments and unresolved priorities

The tool never decompiles native code, decrypts model data, or emits method bodies.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import zipfile
from pathlib import Path

from scan_ysm_265 import parse_class

ROOT = "com/elfmcys/yesstevemodel/"

DOMAINS = (
    "MODEL",
    "ANIMATION",
    "MOLANG",
    "RENDERER",
    "NETWORK",
    "CAPABILITY",
    "GUI",
    "INTEGRATION",
    "MIXIN",
    "ENTITY_PRESENTATION",
    "EVENT_LIFECYCLE",
    "UTILITY",
    "CORE",
    "UNKNOWN",
)


def semantic_domain(name: str | None) -> str:
    s = (name or "").lower()
    if not s:
        return "UNKNOWN"
    if ".network" in s:
        return "NETWORK"
    if ".mixin" in s:
        return "MIXIN"
    if ".capability" in s:
        return "CAPABILITY"
    if ".compat" in s:
        return "INTEGRATION"
    if ".client.gui" in s or ".gui." in s:
        return "GUI"
    if ".animation.molang" in s or ".core.molang" in s or ".molang." in s:
        return "MOLANG"
    if ".controller" in s or "animationcontroller" in s:
        return "ANIMATION"
    if ".renderer" in s or "renderer" in s:
        return "RENDERER"
    if ".geo.animated" in s or ".geo.render.built" in s or "geomodel" in s or "ibone" in s or "animatedgeobone" in s:
        return "MODEL"
    if ".model" in s:
        return "MODEL"
    if ".client.entity" in s or "animatableentity" in s or "livinganimatable" in s:
        return "ENTITY_PRESENTATION"
    if ".event" in s:
        return "EVENT_LIFECYCLE"
    if ".animation" in s or "animation" in s:
        return "ANIMATION"
    if ".util" in s or ".api" in s:
        return "UTILITY"
    return "CORE"


EXTERNAL_ANCHORS = {
    "NETWORK": (
        "net/minecraftforge/network/",
        "net/minecraft/network/FriendlyByteBuf",
        "net/minecraft/network/Connection",
        "io/netty/",
    ),
    "RENDERER": (
        "com/mojang/blaze3d/",
        "net/minecraft/client/renderer/",
        "net/minecraft/client/model/",
    ),
    "GUI": (
        "net/minecraft/client/gui/",
        "org/lwjgl/glfw/",
    ),
    "CAPABILITY": (
        "net/minecraftforge/common/capabilities/",
        "net/minecraftforge/common/util/LazyOptional",
        "net/minecraftforge/event/AttachCapabilitiesEvent",
    ),
    "MIXIN": (
        "org/spongepowered/asm/mixin/",
    ),
    "INTEGRATION": (
        "com/github/tartaricacid/",
        "com/tacz/",
        "com/tacz/guns/",
        "snownee/jade/",
        "tschipp/carryon/",
        "yesman/epicfight/",
        "com/hollingsworth/arsnouveau/",
        "top/theillusivec4/curios/",
        "com/hammy275/immersivemc/",
    ),
    "ENTITY_PRESENTATION": (
        "net/minecraft/world/entity/",
    ),
}

STRING_ANCHORS = {
    "MOLANG": (
        "ground_speed2", "bone_rot", "bone_pos", "bone_scale", "bone_pivot_abs",
        "play_sound", "stop_sound", "defer", "query.", "math.",
    ),
    "NETWORK": ("2.6.0",),
    "INTEGRATION": (
        "tac_hold_gun", "tac_gun_type", "tac_is_fire", "carryon_type", "carryon_is_princess",
    ),
}


def normalize(v: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, x) for x in v.values())
    if total <= 0:
        return {}
    return {k: max(0.0, x) / total for k, x in v.items() if x > 0}


def top_pairs(v: dict[str, float], n=3):
    return sorted(v.items(), key=lambda x: (-x[1], x[0]))[:n]


def load_classes(jar_path: Path):
    classes = {}
    parse_errors = []
    with zipfile.ZipFile(jar_path) as z:
        for entry in z.namelist():
            if not entry.endswith(".class") or entry.startswith("META-INF/versions/"):
                continue
            try:
                c = parse_class(z.read(entry))
            except Exception as e:
                parse_errors.append({"entry": entry, "error": str(e)})
                continue
            if c["name"].startswith(ROOT):
                classes[c["name"]] = c
    return classes, parse_errors


def build_seed_map(mapping: dict):
    owner_candidates: dict[str, list[tuple[int, str, str]]] = collections.defaultdict(list)
    for x in mapping.get("mappings", []):
        owner = (x.get("obfuscated_owner") or "").replace(".", "/")
        if not owner.startswith(ROOT):
            continue
        sem = x.get("semantic_owner")
        dom = semantic_domain(sem)
        # Prefer class mappings, then CONFIRMED over HIGH, then everything else.
        weight = 0
        if x.get("kind") == "class":
            weight += 100
        if x.get("confidence") == "CONFIRMED":
            weight += 20
        elif x.get("confidence") == "HIGH":
            weight += 10
        if x.get("exact_jar_verified"):
            weight += 5
        owner_candidates[owner].append((weight, dom, sem or ""))
    seeds = {}
    provenance = {}
    for owner, rows in owner_candidates.items():
        rows.sort(key=lambda x: (-x[0], x[1], x[2]))
        best = rows[0]
        seeds[owner] = best[1]
        provenance[owner] = {
            "domain": best[1],
            "semantic_owner": best[2],
            "alternatives": [
                {"weight": w, "domain": d, "semantic_owner": s}
                for w, d, s in rows[:8]
            ],
        }
    return seeds, provenance


def anchor_vector(c: dict) -> dict[str, float]:
    out = collections.Counter()
    refs = c["class_refs"]
    text = "\n".join(c["utf8"])
    for dom, prefixes in EXTERNAL_ANCHORS.items():
        for p in prefixes:
            hits = sum(1 for ref in refs if ref.startswith(p))
            if hits:
                out[dom] += min(2.5, 0.35 * hits)
    for dom, tokens in STRING_ANCHORS.items():
        for t in tokens:
            if t in text:
                out[dom] += 0.8
    # Strong hierarchy anchors.
    sup = c.get("super") or ""
    if sup.startswith("net/minecraft/client/gui/screens/"):
        out["GUI"] += 2.0
    if sup.startswith("net/minecraft/client/renderer/entity/"):
        out["RENDERER"] += 2.0
    if any(i.startswith("snownee/jade/") for i in c.get("interfaces", [])):
        out["INTEGRATION"] += 2.5
    if any(i.startswith("net/minecraftforge/client/gui/overlay/") for i in c.get("interfaces", [])):
        out["GUI"] += 2.0
    return normalize(dict(out))


def connected_components(graph):
    seen = set()
    comps = []
    for n in graph:
        if n in seen:
            continue
        q = [n]
        seen.add(n)
        comp = []
        while q:
            x = q.pop()
            comp.append(x)
            for y in graph[x]:
                if y not in seen:
                    seen.add(y)
                    q.append(y)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    return comps


def nearest_seeds(graph, seeds, start, limit=3):
    if start in seeds:
        return [{"owner": start, "domain": seeds[start], "distance": 0}]
    q = collections.deque([(start, 0)])
    seen = {start}
    found = []
    found_dist = None
    while q:
        node, d = q.popleft()
        if found_dist is not None and d > found_dist + 1:
            break
        if node != start and node in seeds:
            found.append({"owner": node, "domain": seeds[node], "distance": d})
            found_dist = d if found_dist is None else found_dist
            if len(found) >= limit:
                break
            continue
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, d + 1))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    jar_path = Path(args.jar)
    raw = jar_path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    mapping = json.loads(Path(args.map).read_text(encoding="utf-8"))
    classes, parse_errors = load_classes(jar_path)

    graph = {name: set() for name in classes}
    directed_edges = 0
    for name, c in classes.items():
        for ref in c["class_refs"]:
            if ref in classes and ref != name:
                directed_edges += 1
                graph[name].add(ref)
                graph[ref].add(name)
        sup = c.get("super")
        if sup in classes and sup != name:
            graph[name].add(sup); graph[sup].add(name)
        for iface in c.get("interfaces", []):
            if iface in classes and iface != name:
                graph[name].add(iface); graph[iface].add(name)

    seeds, seed_provenance = build_seed_map(mapping)
    seeds = {k:v for k,v in seeds.items() if k in classes}
    anchors = {name: anchor_vector(c) for name,c in classes.items()}

    # Semantic label propagation. Exact semantic seeds stay clamped.
    probs = {}
    for name in classes:
        if name in seeds:
            probs[name] = {seeds[name]: 1.0}
        elif anchors[name]:
            probs[name] = anchors[name]
        else:
            probs[name] = {}

    for _ in range(18):
        nxt = {}
        for name in classes:
            if name in seeds:
                nxt[name] = {seeds[name]: 1.0}
                continue
            acc = collections.Counter()
            degree = len(graph[name])
            if degree:
                for nb in graph[name]:
                    for dom, score in probs[nb].items():
                        acc[dom] += 0.78 * score / degree
            for dom, score in anchors[name].items():
                acc[dom] += 0.22 * score
            nxt[name] = normalize(dict(acc))
        probs = nxt

    comps = connected_components(graph)
    comp_id = {}
    for i, comp in enumerate(comps):
        for n in comp:
            comp_id[n] = i

    records = []
    domain_stats = collections.defaultdict(lambda: {
        "classes": 0, "mapped_seed_classes": 0, "confirmed_assignments": 0,
        "unresolved": 0, "degree_sum": 0, "score_sum": 0.0,
    })
    for name, c in classes.items():
        p = probs[name]
        top = top_pairs(p, 3)
        dom = top[0][0] if top else "UNKNOWN"
        score = top[0][1] if top else 0.0
        second = top[1][1] if len(top) > 1 else 0.0
        margin = score - second
        mapped = name in seeds
        degree = len(graph[name])
        mapped_neighbors = sum(1 for x in graph[name] if x in seeds)
        unresolved_priority = 0.0 if mapped else (
            degree * (0.55 + score) * (1.0 + 0.15 * mapped_neighbors) * (0.8 + max(0.0, margin))
        )
        refs = sorted(graph[name])
        external_refs = sorted(x for x in c["class_refs"] if not x.startswith(ROOT))
        rec = {
            "class": name,
            "domain": dom,
            "domain_score": round(score, 6),
            "margin": round(margin, 6),
            "top_domains": [{"domain": d, "score": round(v, 6)} for d,v in top],
            "mapped_seed": mapped,
            "seed_semantic": seed_provenance.get(name),
            "degree": degree,
            "mapped_neighbors": mapped_neighbors,
            "unresolved_priority": round(unresolved_priority, 6),
            "component": comp_id[name],
            "super": c.get("super"),
            "interfaces": c.get("interfaces", []),
            "method_count": len(c.get("methods", [])),
            "field_count": len(c.get("fields", [])),
            "anchor_domains": anchors[name],
            "nearest_seeds": nearest_seeds(graph, seeds, name, 3),
            "ysm_refs": refs[:48],
            "external_refs": external_refs[:32],
        }
        records.append(rec)
        st = domain_stats[dom]
        st["classes"] += 1
        st["mapped_seed_classes"] += 1 if mapped else 0
        st["confirmed_assignments"] += 1 if (mapped or (score >= 0.55 and margin >= 0.10)) else 0
        st["unresolved"] += 0 if mapped else 1
        st["degree_sum"] += degree
        st["score_sum"] += score

    records.sort(key=lambda x: x["class"])
    by_name = {x["class"]:x for x in records}
    domain_summaries = {}
    for dom in DOMAINS:
        rows = [x for x in records if x["domain"] == dom]
        if not rows:
            continue
        unresolved = [x for x in rows if not x["mapped_seed"]]
        unresolved.sort(key=lambda x:(-x["unresolved_priority"], -x["degree"], x["class"]))
        mapped_rows = [x for x in rows if x["mapped_seed"]]
        mapped_rows.sort(key=lambda x:(-x["degree"], x["class"]))
        bridge_rows = sorted(rows, key=lambda x:(-x["degree"], x["class"]))
        st = domain_stats[dom]
        domain_summaries[dom] = {
            "classes": st["classes"],
            "mapped_seed_classes": st["mapped_seed_classes"],
            "unresolved_classes": st["unresolved"],
            "high_confidence_assignment_count": st["confirmed_assignments"],
            "average_degree": round(st["degree_sum"]/max(1,st["classes"]), 3),
            "average_domain_score": round(st["score_sum"]/max(1,st["classes"]), 6),
            "mapped_hubs": [
                {"class":x["class"],"degree":x["degree"],"semantic":(x["seed_semantic"] or {}).get("semantic_owner")}
                for x in mapped_rows[:12]
            ],
            "top_unresolved": [
                {
                    "class":x["class"],"priority":x["unresolved_priority"],"degree":x["degree"],
                    "score":x["domain_score"],"margin":x["margin"],
                    "nearest_seeds":x["nearest_seeds"],"super":x["super"],"interfaces":x["interfaces"],
                    "method_count":x["method_count"],"field_count":x["field_count"],
                }
                for x in unresolved[:20]
            ],
            "central_classes": [
                {"class":x["class"],"degree":x["degree"],"mapped":x["mapped_seed"],"score":x["domain_score"]}
                for x in bridge_rows[:15]
            ],
        }

    cross_domain_edges = collections.Counter()
    seen_edges = set()
    for a, nbs in graph.items():
        for b in nbs:
            edge = tuple(sorted((a,b)))
            if edge in seen_edges:
                continue
            seen_edges.add(edge)
            da, db = by_name[a]["domain"], by_name[b]["domain"]
            if da != db:
                cross_domain_edges[tuple(sorted((da,db)))] += 1

    result = {
        "format": "kneekura.ysm-foundation-map.v1",
        "artifact": {
            "sha256": sha256,
            "size": len(raw),
            "classes": len(classes),
            "parse_errors": len(parse_errors),
        },
        "graph": {
            "nodes": len(graph),
            "undirected_edges": len(seen_edges),
            "directed_class_refs_observed": directed_edges,
            "components": len(comps),
            "largest_components": [len(x) for x in comps[:20]],
            "seed_classes": len(seeds),
        },
        "domains": domain_summaries,
        "cross_domain_edges": [
            {"domains": list(k), "edges": v}
            for k,v in sorted(cross_domain_edges.items(), key=lambda x:(-x[1],x[0]))
        ],
        "classes": records,
        "parse_errors": parse_errors,
        "methodology": {
            "seed_source": "OBFUSCATION-MAP-2026-10-05.json owner semantic roles",
            "seed_rule": "class mappings preferred, then CONFIRMED/HIGH/exact-JAR evidence",
            "propagation_iterations": 18,
            "neighbor_weight": 0.78,
            "stable_external_anchor_weight": 0.22,
            "warning": "Domain assignments for unmapped classes are clustering hints, not semantic symbol confirmation.",
        },
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("KNEEKURA_FOUNDATION_SHA256=" + sha256)
    print("KNEEKURA_FOUNDATION_CLASSES=" + str(len(classes)))
    print("KNEEKURA_FOUNDATION_EDGES=" + str(len(seen_edges)))
    print("KNEEKURA_FOUNDATION_COMPONENTS=" + str(len(comps)))
    print("KNEEKURA_FOUNDATION_SEEDS=" + str(len(seeds)))
    for dom, d in sorted(domain_summaries.items()):
        print("KNEEKURA_DOMAIN_" + dom + "=" + json.dumps({
            "classes":d["classes"],
            "mapped_seed_classes":d["mapped_seed_classes"],
            "unresolved_classes":d["unresolved_classes"],
            "average_domain_score":d["average_domain_score"],
            "top_unresolved":d["top_unresolved"][:8],
        }, ensure_ascii=False))
    print("KNEEKURA_CROSS_DOMAIN=" + json.dumps(result["cross_domain_edges"][:20], ensure_ascii=False))


if __name__ == "__main__":
    main()
