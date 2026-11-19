"""Building IR (PLAN P1): exact integer XYZ -> block state, with air intent made explicit.

Coordinates are the building's *design* coordinates (mcbuild VoxelGrid frame, +Y up). The paste
origin is the design point that lands on the player's position; by default (0, 0, 0), which
matches how WorldEdit places an mcbuild v3 file (block = paste point + Offset + local).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from . import nbt
from .blockstate import BlockState, BlockStateError, decode_varints, parse_state

ABSENT, EXPLICIT_AIR, SOLID_OR_OTHER = "ABSENT", "EXPLICIT_AIR", "SOLID_OR_OTHER"
AIR_KNOWN, AIR_UNKNOWN = "KNOWN", "AIR_INTENT_UNKNOWN"
MAX_CELLS = 4_000_000   # same guard as mcbuild VoxelGrid
MAX_EXTENT = 512        # same guard as mcbuild VoxelGrid
MAX_VOLUME = 32_000_000  # dense volume a reader/writer may be asked to allocate
SPARSE_FORMAT = "kneekura_mcbuild_sparse_v1"

Coord = tuple[int, int, int]


class IRError(ValueError):
    pass


def _int(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or abs(value) > 30_000_000:
        raise IRError(f"INVALID_{label}")
    return value


@dataclass
class BuildingIR:
    cells: dict[Coord, BlockState]
    air_intent: str
    source: dict
    paste_origin: Coord = (0, 0, 0)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.air_intent not in (AIR_KNOWN, AIR_UNKNOWN):
            raise IRError("INVALID_AIR_INTENT")
        if len(self.cells) > MAX_CELLS:
            raise IRError("CELL_LIMIT")
        if self.air_intent == AIR_UNKNOWN and any(s.is_air for s in self.cells.values()):
            raise IRError("AIR_CELLS_WITH_UNKNOWN_INTENT")
        for pos in self.cells:
            if len(pos) != 3:
                raise IRError("INVALID_COORD")
            for v in pos:
                _int(v, "COORD")
        for v in self.paste_origin:
            _int(v, "ORIGIN")
        b = self.bounds(include_air=True)
        if b and any(hi - lo + 1 > MAX_EXTENT for lo, hi in zip(*b)):
            raise IRError("EXTENT_LIMIT")

    def cell_kind(self, pos: Coord) -> str:
        state = self.cells.get(pos)
        if state is None:
            return ABSENT
        return EXPLICIT_AIR if state.is_air else SOLID_OR_OTHER

    @property
    def solid(self) -> dict[Coord, BlockState]:
        return {p: s for p, s in self.cells.items() if not s.is_air}

    @property
    def explicit_air(self) -> list[Coord]:
        return sorted(p for p, s in self.cells.items() if s.is_air)

    def bounds(self, include_air: bool = False) -> tuple[Coord, Coord] | None:
        """Recomputed from cells that actually remain, so cleared regions never inflate it."""
        points = list(self.cells if include_air else self.solid)
        if not points:
            return None
        return (tuple(min(p[i] for p in points) for i in range(3)),
                tuple(max(p[i] for p in points) for i in range(3)))

    def content_sha256(self) -> str:
        """Hash of the placement only (positions + states + air intent), independent of file format."""
        h = hashlib.sha256(self.air_intent.encode())
        for pos in sorted(self.cells):
            h.update(f"\n{pos[0]},{pos[1]},{pos[2]}={self.cells[pos]}".encode())
        return h.hexdigest()


def from_sparse_json(data: bytes, *, max_bytes: int = 64 * 1024 * 1024) -> BuildingIR:
    """Sparse placement exported from a VoxelGrid (``export_sparse.py``): air intent is KNOWN."""
    if len(data) > max_bytes:
        raise IRError("SPARSE_INPUT_TOO_LARGE")
    try:
        doc = json.loads(data)
    except (ValueError, RecursionError) as exc:
        raise IRError(f"INVALID_SPARSE_JSON: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("format") != SPARSE_FORMAT:
        raise IRError("NOT_SPARSE_EXPORT")
    rows = doc.get("cells")
    if not isinstance(rows, list) or len(rows) > MAX_CELLS:
        raise IRError("INVALID_SPARSE_CELLS")
    cells: dict[Coord, BlockState] = {}
    cache: dict[str, BlockState] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 4 or not isinstance(row[3], str):
            raise IRError("INVALID_SPARSE_ROW")
        pos = (_int(row[0], "COORD"), _int(row[1], "COORD"), _int(row[2], "COORD"))
        if pos in cells:
            raise IRError("DUPLICATE_SPARSE_CELL")
        state = cache.get(row[3]) or cache.setdefault(row[3], parse_state(row[3]))
        cells[pos] = state
    source = {"kind": "mcbuild_sparse", "sha256": hashlib.sha256(data).hexdigest(),
              "mcbuild_commit": doc.get("mcbuild_commit"), "blueprint_sha256": doc.get("blueprint_sha256"),
              "seed": doc.get("seed"), "data_version": doc.get("data_version")}
    return BuildingIR(cells=cells, air_intent=AIR_KNOWN, source=source)


def _req(compound: dict, key: str, tag: int):
    entry = compound.get(key)
    if entry is None or entry[0] != tag:
        raise IRError(f"SCHEM_FIELD_MISSING_OR_WRONG_TYPE: {key}")
    return entry[1]


def read_dims(schematic: dict) -> tuple[int, int, int]:
    dims = tuple(_req(schematic, k, nbt.SHORT) for k in ("Width", "Height", "Length"))
    if any(d <= 0 for d in dims):
        raise IRError("INVALID_SCHEM_DIMENSIONS")
    if any(d > MAX_EXTENT for d in dims) or dims[0] * dims[1] * dims[2] > MAX_VOLUME:
        raise IRError("SCHEM_VOLUME_LIMIT")
    return dims


def read_palette(palette: dict) -> list[BlockState]:
    if not palette or len(palette) > 65536:
        raise IRError("INVALID_PALETTE_SIZE")
    by_index: dict[int, BlockState] = {}
    for key, (tag, index) in palette.items():
        if tag != nbt.INT or index < 0 or index >= len(palette) or index in by_index:
            raise IRError("INVALID_PALETTE_INDEX")
        try:
            by_index[index] = parse_state(key)
        except BlockStateError as exc:
            raise IRError(f"INVALID_PALETTE_ENTRY: {exc}") from exc
    if len(set(by_index.values())) != len(by_index):
        raise IRError("DUPLICATE_PALETTE_STATE")
    return [by_index[i] for i in range(len(palette))]


def from_sponge_v3(data: bytes, *, allow_dropping_extras: bool = False) -> BuildingIR:
    """Read an mcbuild-style Sponge v3 file. Air cells cannot be told apart from unplaced
    cells (mcbuild fills the bounding box with air), so air intent is AIR_INTENT_UNKNOWN."""
    name, (_, root) = nbt.loads(data)
    schematic = _req(root, "Schematic", nbt.COMPOUND)
    if _req(schematic, "Version", nbt.INT) != 3:
        raise IRError("NOT_SPONGE_V3")
    data_version = _req(schematic, "DataVersion", nbt.INT)
    w, h, l = read_dims(schematic)
    offset = [0, 0, 0]
    if "Offset" in schematic:
        offset = _req(schematic, "Offset", nbt.INT_ARRAY)
        if len(offset) != 3:
            raise IRError("INVALID_SCHEM_OFFSET")
    blocks = _req(schematic, "Blocks", nbt.COMPOUND)
    palette = read_palette(_req(blocks, "Palette", nbt.COMPOUND))
    indices = decode_varints(_req(blocks, "Data", nbt.BYTE_ARRAY), w * h * l, len(palette) - 1)
    air_ids = {i for i, p in enumerate(palette) if p.is_air}
    # Count before building any per-cell structure: a tiny gzip can declare 32M solid cells (review H1).
    solid = sum(1 for v in indices if v not in air_ids)
    if solid > MAX_CELLS:
        raise IRError("CELL_LIMIT")
    warnings: list[str] = []
    extras = 0
    for container, key in ((blocks, "BlockEntities"), (schematic, "Entities")):
        if key in container:
            element, items = _req(container, key, nbt.LIST)
            extras += len(items)
    if extras:
        if not allow_dropping_extras:
            raise IRError("BLOCK_ENTITIES_OR_ENTITIES_NOT_SUPPORTED")
        warnings.append(f"DROPPED_BLOCK_ENTITIES_OR_ENTITIES:{extras}")
    cells: dict[Coord, BlockState] = {}
    air_cells = 0
    for index, value in enumerate(indices):
        if value in air_ids:
            air_cells += 1
            continue
        state = palette[value]
        y, rem = divmod(index, w * l)
        z, x = divmod(rem, w)
        cells[(offset[0] + x, offset[1] + y, offset[2] + z)] = state
    if air_cells:
        warnings.append(f"AIR_INTENT_UNKNOWN:{air_cells}_air_cells_not_carried")
    source = {"kind": "sponge_v3", "sha256": hashlib.sha256(data).hexdigest(), "data_version": data_version,
              "schematic_version": 3, "dimensions": [w, h, l], "offset": list(offset), "root_name": name}
    return BuildingIR(cells=cells, air_intent=AIR_UNKNOWN, source=source, warnings=warnings)
