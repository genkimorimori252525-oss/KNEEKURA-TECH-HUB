"""Read-only, bounded class/member evidence. Never loads a JVM or executes bytecode.

The path constructor pins YSM and explicitly hashed dependency JARs. JDK identity is
reported, not inferred from its filename. Missing classes/members return None;
invalid or over-budget inputs raise MetadataError. Interfaces are not traversed.
"""
from __future__ import annotations

from collections.abc import Mapping
import copy
import hashlib
import io
from pathlib import Path
import re
import struct
import zipfile

from scan_ysm_265 import parse_class

YSM_SHA256 = "25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f"
DEFAULT_JAR_PATH = Path(__file__).resolve().parents[6] / "ysm-local-inputs/ysm.jar"
DEFAULT_JAVA_BASE_PATH = Path(__file__).resolve().parents[6] / "ysm-local-inputs/tool-cache/jdk21/jdk-21.0.12.1+1/jmods/java.base.jmod"
MAX_CLASS_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 100_000
MAX_SUPER_DEPTH = 64
MAX_DEPENDENCIES = 8
MAX_DEPENDENCY_BYTES = 128 * 1024 * 1024


class MetadataError(ValueError):
    """Untrusted archive/class input is invalid or exceeds a fixed bound."""


def _name(name):
    if (not isinstance(name, str) or not name or len(name) > 65535
            or any(c in name for c in ".;[\\\x00:")
            or any(ord(c) < 32 for c in name)
            or any(not part for part in name.split("/"))):
        raise MetadataError("invalid internal class name")
    return name


def _descriptor(value):
    """Validate an exact JVM method descriptor without recursive parsing."""
    if not isinstance(value, str) or not value.startswith("(") or len(value) > 65535:
        raise MetadataError("invalid method descriptor")

    def field(pos):
        start = pos
        while pos < len(value) and value[pos] == "[":
            pos += 1
        if pos - start > 255 or pos >= len(value):
            raise MetadataError("invalid method descriptor")
        if value[pos] in "BCDFIJSZ":
            return pos + 1
        if value[pos] == "L":
            end = value.find(";", pos + 1)
            if end != -1:
                _name(value[pos + 1:end])
                return end + 1
        raise MetadataError("invalid method descriptor")

    pos = 1
    while pos < len(value) and value[pos] != ")":
        pos = field(pos)
    if pos >= len(value):
        raise MetadataError("invalid method descriptor")
    pos += 1
    end = pos + 1 if value[pos:pos + 1] == "V" else field(pos)
    if end != len(value):
        raise MetadataError("invalid method descriptor")



def _field_descriptor(value):
    """Validate exactly one non-void JVM field type, with bounded array rank."""
    if not isinstance(value, str) or not value or len(value) > 65535:
        raise MetadataError("invalid field descriptor")
    rank = len(value) - len(value.lstrip("["))
    if rank > 255:
        raise MetadataError("invalid field descriptor")
    atom = value[rank:]
    if len(atom) == 1 and atom in "BCDFIJSZ":
        return
    if atom.startswith("L") and atom.endswith(";"):
        _name(atom[1:-1])
        return
    raise MetadataError("invalid field descriptor")


def _validate_class_bounds(raw):
    """Check every attribute extent before the legacy scanner seeks past it."""
    pos = 0
    def take(n):
        nonlocal pos
        if n < 0 or pos + n > len(raw):
            raise MetadataError("truncated class structure")
        out = raw[pos:pos + n]
        pos += n
        return out
    def u2():
        return int.from_bytes(take(2), "big")
    take(8)
    count = u2()
    index = 1
    while index < count:
        tag = take(1)[0]
        if tag == 1:
            take(u2())
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            take(4)
        elif tag in (5, 6):
            take(8)
            index += 1
        elif tag in (7, 8, 16, 19, 20):
            take(2)
        elif tag == 15:
            take(3)
        else:
            raise MetadataError("invalid constant pool tag")
        index += 1
    take(6)
    take(2 * u2())
    def attributes():
        for _ in range(u2()):
            take(2)
            take(int.from_bytes(take(4), "big"))
    for _ in range(2):
        for _ in range(u2()):
            take(6)
            attributes()
    attributes()
    if pos != len(raw):
        raise MetadataError("trailing class data")


class JavaMetadata:
    """Explicit local sources, with no extraction and no filesystem writes.

    sources maps stable source IDs to sha256, archive_kind and entry_count.
    dependency_paths maps IDs to (path, mandatory lowercase SHA-256).
    Dependency archives are indexed only; manifest classpaths are never followed.
    class_info returns detached dictionaries. lookup_method includes access flags,
    declaring_class and source provenance. Static/instance mismatches fail closed.
    JNI method lookup does not enforce Java caller visibility; access flags are
    retained as evidence, and inherited private methods are excluded.
    """

    def __init__(self, jar_path=None, java_base_path=None, *, dependency_paths=None):
        self._archives = {}
        self._cache = {}
        self.sources = {}
        dependencies = self._dependencies(dependency_paths)
        for key, path, kind, expected in (
            ("ysm", jar_path, "jar", YSM_SHA256),
            ("java.base", java_base_path, "jmod", None),
        ):
            if path is not None:
                with Path(path).open("rb") as stream:
                    data = stream.read(MAX_ARCHIVE_BYTES + 1)
                self._add(key, data, kind, expected)
        self._add_dependencies(dependencies, paths=True)

    @classmethod
    def from_buffers(cls, *, jar=None, java_base=None, expected_jar_sha256=YSM_SHA256,
                     dependency_buffers=None):
        """In-memory fixture seam; real path inputs always use pinned YSM hash."""
        dependencies = cls._dependencies(dependency_buffers)
        result = cls()
        if jar is not None:
            result._add("ysm", jar, "jar", expected_jar_sha256)
        if java_base is not None:
            result._add("java.base", java_base, "jmod", None)
        result._add_dependencies(dependencies, paths=False)
        return result

    @staticmethod
    def _dependencies(values):
        if values is None:
            return []
        if not isinstance(values, Mapping):
            raise MetadataError("dependency inputs must be a mapping")
        if len(values) > MAX_DEPENDENCIES:
            raise MetadataError("dependency count budget exceeded")
        result = []
        for key, pair in values.items():
            if (not isinstance(key, str) or key in ("ysm", "java.base")
                    or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", key)):
                raise MetadataError("invalid or reserved dependency source ID")
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise MetadataError("dependency input requires data/path and SHA-256")
            value, expected = pair
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise MetadataError("dependency requires lowercase SHA-256")
            result.append((key, value, expected))
        return sorted(result)

    def _add_dependencies(self, dependencies, *, paths):
        total = 0
        for key, value, expected in dependencies:
            if paths:
                with Path(value).open("rb") as stream:
                    data = stream.read(min(MAX_ARCHIVE_BYTES, MAX_DEPENDENCY_BYTES - total) + 1)
            else:
                if not isinstance(value, bytes):
                    raise MetadataError("dependency buffer must be bytes")
                data = value
            total += len(data)
            if total > MAX_DEPENDENCY_BYTES:
                raise MetadataError("dependency byte budget exceeded")
            self._add(key, data, "jar", expected)
        if dependencies:
            owners = {}
            platform = self._archives.get("java.base", (None, {}))[1]
            for key, (_, index) in self._archives.items():
                if key == "java.base":
                    continue
                for entry in index:
                    if not entry.endswith(".class") or entry == "module-info.class":
                        continue
                    if key != "ysm" and (entry.startswith("java/") or "classes/" + entry in platform):
                        raise MetadataError("dependency platform class shadowing")
                    if entry in owners:
                        raise MetadataError("ambiguous class across archive sources: " + entry)
                    owners[entry] = key

    def _add(self, key, data, kind, expected):
        if len(data) > MAX_ARCHIVE_BYTES:
            raise MetadataError("archive byte budget exceeded")
        digest = hashlib.sha256(data).hexdigest()
        if expected is not None and digest != expected:
            raise MetadataError(key + " archive SHA-256 mismatch")
        if kind == "jmod" and not data.startswith(b"JM\x01\x00"):
            raise MetadataError("missing JMOD header")
        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                raise MetadataError("archive entry budget exceeded")
            index = {}
            for entry in entries:
                name = entry.filename
                parts = name.rstrip("/").split("/")
                if (name.startswith("/") or "\\" in name or "\x00" in name
                        or ":" in name or any(p in ("", ".", "..") for p in parts)):
                    raise MetadataError("unsafe archive entry name")
                if name in index:
                    raise MetadataError("duplicate archive entry")
                index[name] = entry
            self._archives[key] = (archive, index)
            self.sources[key] = {"sha256": digest, "archive_kind": kind,
                                 "entry_count": len(entries)}
        except (zipfile.BadZipFile, OSError) as exc:
            raise MetadataError("invalid archive") from exc

    def class_info(self, internal_name):
        name = _name(internal_name)
        if name == "module-info":raise MetadataError("module descriptor is not ordinary class metadata")
        if name in self._cache:
            return copy.deepcopy(self._cache[name])
        # Platform classes must not be shadowed by an application JAR.
        order = (("java.base",) if name.startswith("java/") else
                 ("java.base", "ysm", *sorted(k for k in self._archives
                                               if k not in ("java.base", "ysm"))))
        for key in order:
            if key not in self._archives:
                continue
            archive, index = self._archives[key]
            entry = index.get(("classes/" if key == "java.base" else "") + name + ".class")
            if entry is None:
                continue
            if entry.file_size > MAX_CLASS_BYTES or entry.flag_bits & 1:
                raise MetadataError("class byte budget exceeded or encrypted entry")
            try:
                with archive.open(entry) as stream:
                    raw = stream.read(MAX_CLASS_BYTES + 1)
                if len(raw) > MAX_CLASS_BYTES or len(raw) != entry.file_size:
                    raise MetadataError("class byte budget or size mismatch")
                _validate_class_bounds(raw)
                parsed = parse_class(raw)
                if parsed["name"] != name:
                    raise MetadataError("class identity does not match archive path")
                if parsed["super"] is not None:
                    _name(parsed["super"])
                result = {k: parsed[k] for k in ("name", "super", "methods", "fields", "access", "interfaces")}
                result.update(class_sha256=hashlib.sha256(raw).hexdigest(),
                              source={"id": key, **self.sources[key]})
            except (ValueError, IndexError, TypeError, struct.error, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
                raise MetadataError("invalid class metadata: " + name) from exc
            if len(self._cache) >= 256:
                self._cache.pop(next(iter(self._cache)))
            self._cache[name] = result
            return copy.deepcopy(result)
        return None

    def lookup_method(self, class_name, method, descriptor, static=False):
        _name(class_name)
        _descriptor(descriptor)
        if (not isinstance(method, str) or not method or
                any(c in method for c in ".;/[\\\x00") or
                (any(c in method for c in "<>") and method != "<init>")):
            raise MetadataError("invalid method name")
        if type(static) is not bool:
            raise MetadataError("static must be a boolean")
        if method == "<init>" and (static or not descriptor.endswith(")V")):
            return None
        seen = set()
        current = class_name
        for depth in range(MAX_SUPER_DEPTH):
            if current in seen:
                raise MetadataError("cyclic superclass hierarchy")
            seen.add(current)
            info = self.class_info(current)
            if info is None:
                return None
            for member in info["methods"]:
                if member["name"] == method and member["descriptor"] == descriptor:
                    if bool(member["access"] & 0x0008) != static:
                        return None
                    if depth and member["access"] & 0x0002:
                        return None
                    return {**member, "declaring_class": current,
                            "class_sha256": info["class_sha256"], "source": info["source"]}
            if method == "<init>" or not info["super"]:
                return None
            current = info["super"]
        raise MetadataError("superclass depth budget exceeded")

    def lookup_field(self, class_name, field, descriptor, static=False):
        """Return exact class-file evidence only; never initialize/read a Java field.

        Declared private fields are eligible, including superclass declarations.
        Interface resolution is unsupported: stop before crossing such a boundary.
        """
        _name(class_name)
        _field_descriptor(descriptor)
        if (not isinstance(field, str) or not field or len(field) > 65535
                or any(c in field for c in ".;/[\\\x00<>")
                or any(ord(c) < 32 for c in field)):
            raise MetadataError("invalid field name")
        if type(static) is not bool:
            raise MetadataError("static must be a boolean")
        seen = set()
        current = class_name
        for _ in range(MAX_SUPER_DEPTH):
            if current in seen:
                raise MetadataError("cyclic superclass hierarchy")
            seen.add(current)
            info = self.class_info(current)
            if info is None:
                return None
            for member in info["fields"]:
                if member["name"] == field and member["descriptor"] == descriptor:
                    if bool(member["access"] & 0x0008) != static:
                        return None
                    return {**member, "declaring_class": current,
                            "class_sha256": info["class_sha256"], "source": info["source"]}
            if info["interfaces"] or not info["super"]:
                return None
            current = info["super"]
        raise MetadataError("superclass depth budget exceeded")
