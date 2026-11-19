"""Sponge Schematic v2 writer and an independent reader + read-back diff (PLAN P3).

Layout follows WorldEdit 7.2.15 (commit 5ca4dffd): root tag named ``Schematic`` holding the
fields directly (no v3 ``Schematic.Blocks`` nesting), ``Offset`` = world min corner,
``Metadata.WEOffset{X,Y,Z}`` = min - paste origin, block index ``x + z*W + y*W*L``.

Dense data is held in compact ``array`` buffers and only non-air cells ever become dict entries,
so memory stays proportional to the guarded volume, not to Python object counts (review H2).
"""

from __future__ import annotations

import hashlib
from array import array

from . import nbt
from .blockstate import BlockState, decode_varints, encode_varints, parse_state
from .ir import MAX_CELLS, MAX_VOLUME, BuildingIR, IRError, read_dims, read_palette
from .profile import Registry, TargetProfile

AIR = BlockState("minecraft:air")
SKIP_AIR, FULL_REPLACE = "skip_air", "full_region_replace"
MAX_OUTPUT_BYTES = 64 * 1024 * 1024


class ExportError(ValueError):
    pass


def _varint_len(v: int) -> int:
    n = 1
    while v >= 0x80:
        v >>= 7
        n += 1
    return n


def plan_region(ir: BuildingIR, air_policy: str, profile: TargetProfile | None = None) -> tuple[tuple, tuple, list[str]]:
    if air_policy not in (SKIP_AIR, FULL_REPLACE):
        raise ExportError("INVALID_AIR_POLICY")
    warnings: list[str] = []
    bounds = ir.bounds(include_air=air_policy == FULL_REPLACE)
    if bounds is None:
        raise ExportError("NOTHING_TO_EXPORT")
    lo, hi = list(bounds[0]), list(bounds[1])
    if air_policy == SKIP_AIR and ir.explicit_air:
        # WorldEdit `//paste -a` skips every air cell; v2 alone cannot mark only some air as intended.
        warnings.append(f"EXPLICIT_AIR_NOT_APPLIED_WITH_SKIP_AIR:{len(ir.explicit_air)}")
    if air_policy == FULL_REPLACE:
        warnings.append("FULL_REGION_REPLACE_OVERWRITES_EVERY_CELL_IN_BOUNDS")
        if ir.air_intent != "KNOWN":
            warnings.append("AIR_INTENT_UNKNOWN_ABSENT_CELLS_WILL_BECOME_AIR")
        src = ir.source
        if src.get("kind") == "sponge_v3" and src.get("dimensions") and src.get("offset"):
            # Full replace of a v3 build must clear the same box the original file would have (review M3).
            box_lo = list(src["offset"])
            box_hi = [box_lo[i] + src["dimensions"][i] - 1 for i in range(3)]
            lo = [min(lo[i], box_lo[i]) for i in range(3)]
            hi = [max(hi[i], box_hi[i]) for i in range(3)]
            warnings.append("FULL_REPLACE_REGION_IS_SOURCE_V3_BOX")
    if profile is not None and hi[1] - lo[1] + 1 > profile.build_height:
        warnings.append(f"TALLER_THAN_TARGET_BUILD_HEIGHT:{hi[1] - lo[1] + 1}>{profile.build_height}")
    return tuple(lo), tuple(hi), warnings


def write_v2(ir: BuildingIR, profile: TargetProfile, air_policy: str = SKIP_AIR) -> tuple[bytes, dict]:
    lo, hi, warnings = plan_region(ir, air_policy, profile)
    w, h, l = (hi[i] - lo[i] + 1 for i in range(3))
    volume = w * h * l
    # Guard on the dense volume, not the block count, before allocating anything (A08 / T07).
    if max(w, h, l) > 32767 or volume > MAX_VOLUME:
        raise ExportError("EXPORT_VOLUME_LIMIT")
    # Explicit air variants (cave_air, void_air) are kept as themselves under full replace (review L4).
    written = {s for s in ir.cells.values() if not s.is_air or (air_policy == FULL_REPLACE and s != AIR)}
    palette = [AIR] + sorted(written, key=str)
    index = {s: i for i, s in enumerate(palette)}
    if volume * _varint_len(len(palette) - 1) > MAX_OUTPUT_BYTES:
        raise ExportError("EXPORT_SIZE_LIMIT")
    dense = array("I", bytes(4 * volume))
    for (x, y, z), state in ir.cells.items():
        i = index.get(state)
        if i:
            dense[(x - lo[0]) + (z - lo[2]) * w + (y - lo[1]) * w * l] = i
    we_offset = [lo[i] - ir.paste_origin[i] for i in range(3)]
    root = {
        "Version": (nbt.INT, 2),
        "DataVersion": (nbt.INT, profile.data_version),
        "Metadata": (nbt.COMPOUND, {"WEOffsetX": (nbt.INT, we_offset[0]), "WEOffsetY": (nbt.INT, we_offset[1]),
                                    "WEOffsetZ": (nbt.INT, we_offset[2])}),
        "Width": (nbt.SHORT, w), "Height": (nbt.SHORT, h), "Length": (nbt.SHORT, l),
        "Offset": (nbt.INT_ARRAY, list(lo)),
        "PaletteMax": (nbt.INT, len(palette)),
        "Palette": (nbt.COMPOUND, {str(s): (nbt.INT, i) for i, s in enumerate(palette)}),
        "BlockData": (nbt.BYTE_ARRAY, encode_varints(dense)),
        "BlockEntities": (nbt.LIST, (nbt.COMPOUND, [])),
    }
    data = nbt.dumps(root, root_name="Schematic")
    info = {"dimensions": [w, h, l], "offset": list(lo), "we_offset": we_offset, "paste_origin": list(ir.paste_origin),
            "palette_size": len(palette), "air_policy": air_policy, "warnings": warnings,
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return data, info


class Readback(dict):
    """Read-back result. ``cells`` holds non-air cells only; ``state_at`` answers for any position."""

    def state_at(self, pos) -> BlockState | None:
        w, h, l = self["dimensions"]
        x, y, z = (pos[i] - self["offset"][i] for i in range(3))
        if not (0 <= x < w and 0 <= y < h and 0 <= z < l):
            return None
        return self["_palette"][self["_indices"][x + z * w + y * w * l]]


def read_v2(data: bytes) -> Readback:
    """Independent reader: shares no code with ``write_v2`` beyond the generic NBT/VarInt primitives."""
    name, (_, s) = nbt.loads(data)
    if name != "Schematic":
        raise IRError("V2_ROOT_NAME")
    def req(key, tag):
        entry = s.get(key)
        if entry is None or entry[0] != tag:
            raise IRError(f"V2_FIELD_MISSING_OR_WRONG_TYPE: {key}")
        return entry[1]
    if req("Version", nbt.INT) != 2:
        raise IRError("NOT_SPONGE_V2")
    w, h, l = read_dims(s)
    offset = list(req("Offset", nbt.INT_ARRAY))
    if len(offset) != 3:
        raise IRError("INVALID_V2_OFFSET")
    palette = read_palette(req("Palette", nbt.COMPOUND))
    if req("PaletteMax", nbt.INT) != len(palette):
        raise IRError("PALETTE_MAX_MISMATCH")
    indices = decode_varints(req("BlockData", nbt.BYTE_ARRAY), w * h * l, len(palette) - 1)
    origin = list(offset)
    if "Metadata" in s:
        meta = req("Metadata", nbt.COMPOUND)
        if "WEOffsetX" in meta:
            weo = [meta[k][1] for k in ("WEOffsetX", "WEOffsetY", "WEOffsetZ") if meta.get(k, (None,))[0] == nbt.INT]
            if len(weo) != 3:
                raise IRError("INVALID_WE_OFFSET")
            origin = [offset[i] - weo[i] for i in range(3)]  # WorldEdit: origin = min - WEOffset
    solid_ids = {i for i, p in enumerate(palette) if not p.is_air}
    solid = sum(1 for v in indices if v in solid_ids)
    if solid > MAX_CELLS:
        raise IRError("CELL_LIMIT")
    cells = {}
    for i, v in enumerate(indices):
        if v in solid_ids:
            y, rem = divmod(i, w * l)
            z, x = divmod(rem, w)
            cells[(offset[0] + x, offset[1] + y, offset[2] + z)] = palette[v]
    return Readback(data_version=req("DataVersion", nbt.INT), dimensions=[w, h, l], offset=offset, origin=origin,
                    palette=[str(p) for p in palette], cells=cells, air_cells=len(indices) - solid,
                    block_entities=len(req("BlockEntities", nbt.LIST)[1]) if "BlockEntities" in s else 0,
                    _palette=palette, _indices=indices)


def verify_readback(ir: BuildingIR, readback: Readback, profile: TargetProfile, registry: Registry, air_policy: str) -> dict:
    """Cell-by-cell comparison. ZERO_DIFF is required before an output is accepted."""
    diffs: list[dict] = []
    counts: dict[str, int] = {}
    def diff(kind, pos, expected, actual):
        if len(diffs) < 64:
            diffs.append({"kind": kind, "pos": list(pos), "expected": expected, "actual": actual})
        counts[kind] = counts.get(kind, 0) + 1
    if readback["data_version"] != profile.data_version:
        diff("DATA_VERSION", (0, 0, 0), profile.data_version, readback["data_version"])
    if readback["origin"] != list(ir.paste_origin):
        diff("PASTE_ORIGIN", (0, 0, 0), list(ir.paste_origin), readback["origin"])
    for entry in readback["palette"]:
        st = parse_state(entry)
        # Anything the target cannot parse would be turned into air by WorldEdit 7.2.15 (A04).
        if registry.check(st):
            diff("PALETTE_NOT_LEGAL_IN_TARGET", (0, 0, 0), "legal", entry)
    cells = readback["cells"]
    for pos, state in ir.cells.items():
        if state.is_air:
            if air_policy == FULL_REPLACE and readback.state_at(pos) != state:
                diff("EXPLICIT_AIR_LOST", pos, str(state), str(readback.state_at(pos)))
            continue
        got = cells.get(pos)
        if got != state:
            diff("BLOCK_MISMATCH" if readback.state_at(pos) is not None else "BLOCK_OUTSIDE_REGION", pos, str(state), str(got))
    solid_expected = {p for p, s in ir.cells.items() if not s.is_air}
    for pos, state in cells.items():
        if pos not in solid_expected:
            diff("UNEXPECTED_BLOCK", pos, "absent_or_air", str(state))
    return {"status": "ZERO_DIFF" if not counts else "DIFF", "counts": counts, "diffs": diffs,
            "checked_cells": len(cells) + readback["air_cells"], "solid_cells": len(solid_expected)}
