#!/usr/bin/env python3
"""Bounded structural scanner for the official YSM 2.6.5 Forge 1.20.1 JAR.

This tool intentionally does not decompile method bodies or touch native protection.
It records class/member identity, hierarchy, constant-pool anchors and mapping contracts.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import zipfile
from collections import Counter
from pathlib import Path


def u1(b): return struct.unpack(">B", b.read(1))[0]
def u2(b): return struct.unpack(">H", b.read(2))[0]
def u4(b): return struct.unpack(">I", b.read(4))[0]


def parse_class(data: bytes) -> dict:
    b = io.BytesIO(data)
    if u4(b) != 0xCAFEBABE:
        raise ValueError("not a class file")
    minor, major = u2(b), u2(b)
    cp_count = u2(b)
    cp = [None] * cp_count
    i = 1
    while i < cp_count:
        tag = u1(b)
        if tag == 1:
            n = u2(b)
            raw = b.read(n)
            cp[i] = (tag, raw.decode("utf-8", "replace"))
        elif tag in (3, 4):
            cp[i] = (tag, b.read(4))
        elif tag in (5, 6):
            cp[i] = (tag, b.read(8)); i += 1
        elif tag in (7, 8, 16, 19, 20):
            cp[i] = (tag, u2(b))
        elif tag in (9, 10, 11, 12, 17, 18):
            cp[i] = (tag, u2(b), u2(b))
        elif tag == 15:
            cp[i] = (tag, u1(b), u2(b))
        else:
            raise ValueError(f"unknown constant-pool tag {tag}")
        i += 1

    def utf(idx):
        if not idx: return None
        x = cp[idx]
        return x[1] if x and x[0] == 1 else None

    def cls(idx):
        if not idx: return None
        x = cp[idx]
        return utf(x[1]) if x and x[0] == 7 else None

    access = u2(b)
    this_idx, super_idx = u2(b), u2(b)
    interfaces = [cls(u2(b)) for _ in range(u2(b))]

    def members():
        out = []
        for _ in range(u2(b)):
            acc, name_idx, desc_idx = u2(b), u2(b), u2(b)
            attrs = u2(b)
            for __ in range(attrs):
                u2(b); b.seek(u4(b), io.SEEK_CUR)
            out.append({"access": acc, "name": utf(name_idx), "descriptor": utf(desc_idx)})
        return out

    fields = members()
    methods = members()

    for _ in range(u2(b)):
        u2(b); b.seek(u4(b), io.SEEK_CUR)

    utf8 = [x[1] for x in cp if x and x[0] == 1]
    class_refs = sorted({cls(i) for i, x in enumerate(cp) if i and x and x[0] == 7} - {None})
    return {
        "major": major, "minor": minor, "access": access,
        "name": cls(this_idx), "super": cls(super_idx),
        "interfaces": interfaces, "fields": fields, "methods": methods,
        "utf8": utf8, "class_refs": class_refs,
    }


def key_member(x):
    return (x.get("name"), x.get("descriptor"))


def has_method(c, name, descriptor):
    return any(m["name"] == name and m["descriptor"] == descriptor for m in c["methods"])


def has_field(c, name, descriptor):
    return any(f["name"] == name and f["descriptor"] == descriptor for f in c["fields"])


def slim(c):
    return {
        "name": c["name"], "super": c["super"], "interfaces": c["interfaces"],
        "methods": [{"name": m["name"], "descriptor": m["descriptor"]} for m in c["methods"]],
        "fields": [{"name": f["name"], "descriptor": f["descriptor"]} for f in c["fields"]],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    jar_path = Path(args.jar)
    raw = jar_path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    sha1 = hashlib.sha1(raw).hexdigest()

    classes = {}
    entries = []
    with zipfile.ZipFile(jar_path) as z:
        entries = z.namelist()
        for name in entries:
            if name.endswith(".class") and not name.startswith("META-INF/versions/"):
                try:
                    c = parse_class(z.read(name))
                    classes[c["name"]] = c
                except Exception as e:
                    classes["!parse-error:" + name] = {"error": str(e)}

    real_classes = {k:v for k,v in classes.items() if not k.startswith("!parse-error:")}
    root = "com/elfmcys/yesstevemodel/"
    ysm_classes = {k:v for k,v in real_classes.items() if k.startswith(root)}
    package_top = Counter()
    for name in ysm_classes:
        rest = name[len(root):]
        package_top[rest.split("/",1)[0] if "/" in rest else "<root>"] += 1

    mp = json.loads(Path(args.map).read_text(encoding="utf-8"))
    checks = []
    for x in mp.get("mappings", []):
        owner = (x.get("obfuscated_owner") or "").replace(".", "/")
        if not owner:
            continue
        c = real_classes.get(owner)
        status = "CLASS_MISSING" if c is None else "CLASS_PRESENT"
        if c is not None and x.get("kind") == "method" and x.get("obfuscated_member") and x.get("descriptor"):
            status = "EXACT_METHOD_PRESENT" if has_method(c, x["obfuscated_member"], x["descriptor"]) else "METHOD_DESCRIPTOR_MISSING"
        elif c is not None and x.get("kind") == "field" and x.get("obfuscated_member") and x.get("descriptor"):
            status = "EXACT_FIELD_PRESENT" if has_field(c, x["obfuscated_member"], x["descriptor"]) else "FIELD_DESCRIPTOR_MISSING"
        checks.append({"id": x["id"], "owner": owner, "status": status})

    # High-value unresolved bone alias owner search.
    bone_surface = next((x for x in mp.get("alias_surfaces", []) if x.get("id") == "ysm265.alias.animated-bone-public-surface"), None)
    bone_candidates = []
    if bone_surface:
        aliases = [a for a in bone_surface.get("aliases", []) if a.get("descriptor","").startswith("(")]
        for c in ysm_classes.values():
            matched = [a for a in aliases if has_method(c, a["obfuscated"], a["descriptor"])]
            if len(matched) >= 8:
                bone_candidates.append({
                    "class": c["name"], "super": c["super"], "interfaces": c["interfaces"],
                    "matched": len(matched), "total": len(aliases),
                    "aliases": [{"semantic":a["semantic"],"obfuscated":a["obfuscated"],"descriptor":a["descriptor"]} for a in matched],
                    "methods": [{"name":m["name"],"descriptor":m["descriptor"]} for m in c["methods"]],
                })
        bone_candidates.sort(key=lambda x:(-x["matched"], x["class"]))

    # Known compatibility seams from public actual-jar probes.
    seam_owners = [
        "com/elfmcys/yesstevemodel/o0000OoOooO0oo0o0oooo0Oo",
        "com/elfmcys/yesstevemodel/OOOO0O0O000O000000oOOO0o",
        "com/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00",
        "com/elfmcys/yesstevemodel/o0O0oOooOo0OoOo0oOo00O00",
        "com/elfmcys/yesstevemodel/oo0OooOO0oOoOoOoo00oO000",
        "com/elfmcys/yesstevemodel/oo0oOO0000o0Ooooo0OoOo0O",
    ]
    seam_details = {name: slim(real_classes[name]) for name in seam_owners if name in real_classes}

    # Stable string/interface anchors. Match literals as substrings because Utf8 entries can include
    # descriptors and concatenated compiler strings.
    clusters = {
        "native_lib": ["Failed to create preferred directory, using fallback"],
        "config_screen": ["YSM Config GUI", "disable_self_model", "use_compatibility_renderer"],
        "tacz_binding": ["tac_hold_gun", "tac_gun_type", "tac_is_fire", "tac_fire_mode"],
        "carryon_binding": ["carryon_type", "carryon_is_princess"],
        "molang_core": ["ground_speed2", "bone_rot", "bone_pos"],
        "molang_side_effects": ["play_sound", "particle", "defer"],
        "model_identity": ["model_id", "select_texture"],
        "network_version": ["2.6.0"],
    }
    cluster_hits = {}
    for label, tokens in clusters.items():
        hits = []
        for c in ysm_classes.values():
            text = "\n".join(c["utf8"])
            score = sum(1 for t in tokens if t in text)
            if score:
                hits.append({"class": c["name"], "score": score, "total": len(tokens),
                             "matched": [t for t in tokens if t in text],
                             "super": c["super"], "interfaces": c["interfaces"]})
        hits.sort(key=lambda x:(-x["score"], x["class"]))
        cluster_hits[label] = hits[:20]

    interface_hits = {}
    for iface in [
        "snownee/jade/api/IWailaPlugin",
        "net/minecraftforge/client/gui/overlay/IGuiOverlay",
    ]:
        interface_hits[iface] = [slim(c) for c in ysm_classes.values() if iface in c["interfaces"]]

    # Hierarchy beacons.
    hierarchy_hits = {}
    for super_name in [
        "net/minecraft/client/renderer/entity/EntityRenderer",
        "net/minecraft/client/renderer/entity/LivingEntityRenderer",
        "net/minecraft/client/gui/screens/Screen",
    ]:
        hierarchy_hits[super_name] = [slim(c) for c in ysm_classes.values() if c["super"] == super_name]

    statuses = Counter(x["status"] for x in checks)
    result = {
        "format": "kneekura.ysm-jar-structure.v1",
        "artifact": {
            "filename": jar_path.name,
            "size": len(raw),
            "sha256": sha256,
            "sha1": sha1,
            "zip_entries": len(entries),
            "class_files": len(real_classes),
            "ysm_class_files": len(ysm_classes),
            "classfile_major_versions": dict(Counter(str(c["major"]) for c in real_classes.values())),
        },
        "package_top": dict(package_top.most_common()),
        "map_contract": {
            "mapping_count": len(mp.get("mappings", [])),
            "status_counts": dict(statuses),
            "failures": [x for x in checks if x["status"] not in ("CLASS_PRESENT","EXACT_METHOD_PRESENT","EXACT_FIELD_PRESENT")],
            "checks": checks,
        },
        "bone_alias_candidates": bone_candidates,
        "seam_details": seam_details,
        "cluster_hits": cluster_hits,
        "interface_hits": interface_hits,
        "hierarchy_hits": hierarchy_hits,
        "parse_errors": [{"entry":k,"error":v["error"]} for k,v in classes.items() if k.startswith("!parse-error:")],
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("KNEEKURA_YSM_ARTIFACT_SHA256=" + sha256)
    print("KNEEKURA_YSM_ARTIFACT_SHA1=" + sha1)
    print("KNEEKURA_YSM_ARTIFACT_SIZE=" + str(len(raw)))
    print("KNEEKURA_YSM_CLASS_FILES=" + str(len(real_classes)))
    print("KNEEKURA_YSM_CLASSES=" + str(len(ysm_classes)))
    print("KNEEKURA_MAP_STATUS=" + json.dumps(dict(statuses), sort_keys=True))
    print("KNEEKURA_MAP_FAILURES=" + str(len(result["map_contract"]["failures"])))
    print("KNEEKURA_BONE_CANDIDATES=" + json.dumps([
        {"class":x["class"],"matched":x["matched"],"total":x["total"],"super":x["super"],"interfaces":x["interfaces"]}
        for x in bone_candidates[:10]
    ], ensure_ascii=False))
    for label in ("tacz_binding","carryon_binding","molang_core","molang_side_effects","network_version"):
        print("KNEEKURA_CLUSTER_" + label.upper() + "=" + json.dumps(cluster_hits[label][:8], ensure_ascii=False))
    print("KNEEKURA_JADE=" + json.dumps([x["name"] for x in interface_hits["snownee/jade/api/IWailaPlugin"]]))
    print("KNEEKURA_IGUIOVERLAY=" + json.dumps([x["name"] for x in interface_hits["net/minecraftforge/client/gui/overlay/IGuiOverlay"]]))
