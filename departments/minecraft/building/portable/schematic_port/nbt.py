"""Bounded NBT codec (Java edition, big-endian). Standard library only.

Values are represented as ``(tag_id, value)`` pairs so tag types survive a round trip:

* compound -> ``dict[str, (tag_id, value)]`` (insertion ordered)
* list     -> ``(element_tag_id, [value, ...])``
* arrays   -> ``bytes`` (byte array, signed bytes kept raw) or ``list[int]`` (int/long arrays)

Every length is checked against the bytes that remain *before* anything is allocated, so a
hostile header cannot make the reader reserve gigabytes (PLAN P3 / T07).
"""

from __future__ import annotations

import gzip
import io
import struct
import sys
from array import array
import zlib

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTE_ARRAY, STRING, LIST, COMPOUND, INT_ARRAY, LONG_ARRAY = range(13)

DEFAULT_MAX_DECOMPRESSED = 64 * 1024 * 1024
MAX_DEPTH = 32
MAX_NODES = 2_000_000


class NBTError(ValueError):
    """Malformed, truncated or over-limit NBT. Raised before any large allocation."""


def gunzip_bounded(data: bytes, max_bytes: int = DEFAULT_MAX_DECOMPRESSED) -> bytes:
    """Decompress gzip without trusting the stream to be small (zip-bomb guard)."""
    if data[:2] != b"\x1f\x8b":
        raise NBTError("NOT_GZIP")
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        out = d.decompress(data, max_bytes + 1)
    except zlib.error as exc:
        raise NBTError(f"CORRUPT_GZIP: {exc}") from exc
    if len(out) > max_bytes or d.unconsumed_tail:
        raise NBTError("DECOMPRESSED_SIZE_LIMIT")
    if not d.eof:
        raise NBTError("TRUNCATED_GZIP")
    if d.unused_data.strip(b"\x00"):
        raise NBTError("TRAILING_GZIP_MEMBER")
    return out


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0
        self.nodes = 0

    def take(self, n: int) -> bytes:
        if n < 0 or self.pos + n > len(self.data):
            raise NBTError("TRUNCATED_NBT")
        chunk = self.data[self.pos:self.pos + n]
        self.pos += n
        return chunk

    def unpack(self, fmt: str):
        return struct.unpack(">" + fmt, self.take(struct.calcsize(">" + fmt)))[0]

    def string(self) -> str:
        n = self.unpack("H")
        try:
            return self.take(n).decode("utf-8")
        except UnicodeDecodeError as exc:  # NBT uses modified UTF-8; anything else is rejected
            raise NBTError("INVALID_NBT_STRING") from exc

    def length(self, item_size: int) -> int:
        n = self.unpack("i")
        if n < 0 or n * item_size > len(self.data) - self.pos:
            raise NBTError("NBT_LENGTH_EXCEEDS_INPUT")
        return n

    def payload(self, tag: int, depth: int):
        self.nodes += 1
        if self.nodes > MAX_NODES or depth > MAX_DEPTH:
            raise NBTError("NBT_COMPLEXITY_LIMIT")
        if tag == BYTE:
            return self.unpack("b")
        if tag == SHORT:
            return self.unpack("h")
        if tag == INT:
            return self.unpack("i")
        if tag == LONG:
            return self.unpack("q")
        if tag == FLOAT:
            return self.unpack("f")
        if tag == DOUBLE:
            return self.unpack("d")
        if tag == BYTE_ARRAY:
            return self.take(self.length(1))
        if tag == STRING:
            return self.string()
        if tag == LIST:
            element = self.unpack("B")
            if element > LONG_ARRAY:
                raise NBTError("INVALID_LIST_TAG")
            n = self.length(1 if element != END else 0)
            if element == END and n:
                raise NBTError("NON_EMPTY_END_LIST")
            return (element, [self.payload(element, depth + 1) for _ in range(n)])
        if tag == COMPOUND:
            out: dict = {}
            while True:
                child = self.unpack("B")
                if child == END:
                    return out
                if child > LONG_ARRAY:
                    raise NBTError("INVALID_TAG")
                name = self.string()
                if name in out:
                    raise NBTError("DUPLICATE_COMPOUND_KEY")
                out[name] = (child, self.payload(child, depth + 1))
        if tag in (INT_ARRAY, LONG_ARRAY):
            # Compact typed arrays: no Python int object per element (review L1).
            size, code = (4, "i") if tag == INT_ARRAY else (8, "q")
            n = self.length(size)
            out = array(code, self.take(size * n))
            if sys.byteorder == "little":
                out.byteswap()
            return out
        raise NBTError("INVALID_TAG")


def loads(data: bytes, *, gzipped: bool = True, max_bytes: int = DEFAULT_MAX_DECOMPRESSED) -> tuple[str, tuple[int, dict]]:
    """Parse a whole NBT document. Returns ``(root_name, (COMPOUND, value))``."""
    raw = gunzip_bounded(data, max_bytes) if gzipped else data
    if len(raw) > max_bytes:
        raise NBTError("DECOMPRESSED_SIZE_LIMIT")
    r = _Reader(raw)
    tag = r.unpack("B")
    if tag != COMPOUND:
        raise NBTError("ROOT_NOT_COMPOUND")
    name = r.string()
    value = r.payload(COMPOUND, 0)
    if r.pos != len(raw):
        raise NBTError("TRAILING_NBT_BYTES")
    return name, (COMPOUND, value)


def _write(buf: io.BytesIO, tag: int, value) -> None:
    pack = lambda fmt, v: buf.write(struct.pack(">" + fmt, v))  # noqa: E731
    if tag == BYTE:
        pack("b", value)
    elif tag == SHORT:
        pack("h", value)
    elif tag == INT:
        pack("i", value)
    elif tag == LONG:
        pack("q", value)
    elif tag == FLOAT:
        pack("f", value)
    elif tag == DOUBLE:
        pack("d", value)
    elif tag == BYTE_ARRAY:
        pack("i", len(value))
        buf.write(bytes(value))
    elif tag == STRING:
        raw = value.encode("utf-8")
        if len(raw) > 0xFFFF:
            raise NBTError("NBT_STRING_TOO_LONG")
        pack("H", len(raw))
        buf.write(raw)
    elif tag == LIST:
        element, items = value
        buf.write(bytes([element]))
        pack("i", len(items))
        for item in items:
            _write(buf, element, item)
    elif tag == COMPOUND:
        for name, (child, child_value) in value.items():
            buf.write(bytes([child]))
            _write(buf, STRING, name)
            _write(buf, child, child_value)
        buf.write(bytes([END]))
    elif tag in (INT_ARRAY, LONG_ARRAY):
        out = array("i" if tag == INT_ARRAY else "q", value)
        if sys.byteorder == "little":
            out.byteswap()
        pack("i", len(value))
        buf.write(out.tobytes())
    else:
        raise NBTError("INVALID_TAG")


def dumps(root: dict, *, root_name: str = "", gzipped: bool = True) -> bytes:
    """Serialize a root compound. gzip mtime is fixed to 0 so output bytes are reproducible."""
    buf = io.BytesIO()
    buf.write(bytes([COMPOUND]))
    _write(buf, STRING, root_name)
    _write(buf, COMPOUND, root)
    raw = buf.getvalue()
    return gzip.compress(raw, mtime=0) if gzipped else raw
