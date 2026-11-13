"""Strict block-state strings and Sponge VarInt block data."""

from __future__ import annotations

import re
from array import array
from dataclasses import dataclass

_ID = re.compile(r"^[a-z0-9_.-]{1,64}:[a-z0-9_./-]{1,128}$")
_KEY = re.compile(r"^[a-z0-9_]{1,64}$")
_VALUE = re.compile(r"^[a-z0-9_]{1,64}$")
AIR_IDS = frozenset({"minecraft:air", "minecraft:cave_air", "minecraft:void_air"})


class BlockStateError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class BlockState:
    """Fully-qualified block id plus properties sorted by key (canonical form)."""

    block_id: str
    properties: tuple[tuple[str, str], ...] = ()

    @property
    def namespace(self) -> str:
        return self.block_id.split(":", 1)[0]

    @property
    def is_air(self) -> bool:
        return self.block_id in AIR_IDS

    def __str__(self) -> str:
        if not self.properties:
            return self.block_id
        return self.block_id + "[" + ",".join(f"{k}={v}" for k, v in self.properties) + "]"


def parse_state(text: str) -> BlockState:
    """Parse ``ns:id[k=v,...]``. No implicit namespace, no duplicate keys, no whitespace tricks."""
    if not isinstance(text, str) or len(text) > 1024:
        raise BlockStateError("INVALID_BLOCK_STATE")
    base, bracket, rest = text.partition("[")
    if not _ID.match(base) or ".." in base:
        raise BlockStateError(f"INVALID_BLOCK_ID: {text!r}")
    props: dict[str, str] = {}
    if bracket:
        if not rest.endswith("]") or "[" in rest or "]" in rest[:-1]:
            raise BlockStateError(f"INVALID_BLOCK_STATE_SYNTAX: {text!r}")
        body = rest[:-1]
        if body:
            for part in body.split(","):
                key, eq, value = part.partition("=")
                if not eq or not _KEY.match(key) or not _VALUE.match(value):
                    raise BlockStateError(f"INVALID_BLOCK_PROPERTY: {text!r}")
                if key in props:
                    raise BlockStateError(f"DUPLICATE_BLOCK_PROPERTY: {text!r}")
                props[key] = value
    return BlockState(base, tuple(sorted(props.items())))


def encode_varints(values) -> bytes:
    out = bytearray()
    for v in values:
        if v < 0 or v > 0x7FFFFFFF:
            raise BlockStateError("VARINT_OUT_OF_RANGE")
        while True:
            b = v & 0x7F
            v >>= 7
            if v:
                out.append(b | 0x80)
            else:
                out.append(b)
                break
    return bytes(out)


def decode_varints(data: bytes, count: int, max_value: int) -> array:
    """Decode exactly ``count`` VarInts. Rejects overlong (>5 byte or non-minimal),
    truncated, out-of-palette and trailing data instead of guessing."""
    if count < 0 or count > len(data):
        # Every VarInt needs at least one byte; reject before allocating the result list.
        raise BlockStateError("VARINT_COUNT_EXCEEDS_DATA")
    out = array("I")  # 4 bytes per cell, not a Python int object per cell
    i = 0
    n = len(data)
    for _ in range(count):
        value = 0
        shift = 0
        start = i
        while True:
            if i >= n:
                raise BlockStateError("TRUNCATED_VARINT")
            b = data[i]
            i += 1
            value |= (b & 0x7F) << shift
            shift += 7
            if not b & 0x80:
                break
            if i - start >= 5:
                raise BlockStateError("OVERLONG_VARINT")
        if i - start > 1 and data[i - 1] == 0:
            raise BlockStateError("NON_MINIMAL_VARINT")
        if value > max_value:
            raise BlockStateError("VARINT_OUTSIDE_PALETTE")
        out.append(value)
    if i != n:
        raise BlockStateError("TRAILING_BLOCK_DATA")
    return out
