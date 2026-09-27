"""Bounded local input capture and immutable, content-addressed evidence.

This is an analysis cache, not a second canonical knowledge database. Inputs
are explicitly registered paths. Nothing here runs Gradle or downloaded code.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import stat
import tempfile
import time
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class ContractError(ValueError):
    """Malformed or unsupported request, distinct from unavailable artifacts."""


class ArtifactUnavailable(OSError):
    """A pinned artifact cannot currently be read."""


class IntegrityError(ContractError):
    """Bytes or metadata do not match their immutable identity."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key_for(value: Any) -> str:
    return digest(canonical(value))


def valid_hash(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value):
        raise ContractError('Expected a lowercase SHA-256 identifier')
    return value


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Store:
    """CAS with hash verification on every read; no automatic garbage collection."""

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

    def blob_path(self, key: str) -> Path:
        valid_hash(key)
        return self.root / 'blobs' / key[:2] / key

    def put(self, data: bytes) -> str:
        key = digest(data)
        path = self.blob_path(key)
        if path.is_symlink() or not path.resolve().is_relative_to(self.root):
            raise IntegrityError('CAS path escapes managed storage')
        if path.exists():
            self.read(key)  # Never heal corrupt evidence by overwriting history.
        else:
            atomic_write(path, data)
        return key

    def read(self, key: str) -> bytes:
        path = self.blob_path(key)
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(self.root):
                raise IntegrityError('CAS path escapes managed storage')
            data = path.read_bytes()
        except OSError as exc:
            raise ArtifactUnavailable(f'Unavailable artifact {key}') from exc
        if digest(data) != key:
            raise IntegrityError(f'Artifact hash mismatch: {key}')
        return data

    def put_json(self, value: Any) -> str:
        return self.put(canonical(value))

    def json(self, key: str) -> Any:
        return json.loads(self.read(key))

    def pin(self, key: str, reference: str) -> None:
        self.read(key)
        if not isinstance(reference, str) or not reference:
            raise ContractError('A nonempty evidence reference is required')
        # One immutable marker per (reference, blob), avoiding lost-update sets.
        marker = {'content_hash': key, 'reference': reference}
        atomic_write(self.root / 'pins' / key_for(marker), canonical(marker))

    def pinned_hashes(self) -> set[str]:
        return {json.loads(p.read_bytes())['content_hash']
                for p in (self.root / 'pins').glob('*') if p.is_file()}


@dataclass(frozen=True)
class Limits:
    max_files: int = 50000
    max_file_bytes: int = 16 * 1024 * 1024
    max_total_bytes: int = 512 * 1024 * 1024
    max_compression_ratio: int = 1000
    max_seconds: int = 300

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in vars(self).values()):
            raise ContractError('All capture limits must be positive integers')


TEXT_SUFFIXES = {'.java', '.txt', '.md', '.json', '.jsonl', '.toml', '.properties',
                 '.gradle', '.kts', '.xml', '.cfg', '.mcmeta', '.yml', '.yaml',
                 '.accesswidener', '.tsrg', '.tiny', '.srg', '.csv', '.fsh', '.vsh'}
SCOPES = {'compile', 'runtime', 'client', 'server', 'buildscript', 'research'}
NAMESPACES = {'mojmap', 'srg', 'obf', 'intermediary', 'yarn', 'unknown'}
TRACKS = {'ANCHOR', 'FRONTIER', 'COMPARATIVE'}
EXCLUDED = {'.git', '.gradle', '.kneekura-cache', '__pycache__', '.pytest_cache'}


def safe_entry(name: str) -> str:
    if not isinstance(name, str) or not name or '\x00' in name or '\\' in name:
        raise ContractError('Unsafe archive/path entry')
    normalized = unicodedata.normalize('NFC', name.rstrip('/'))
    parts = normalized.split('/')
    if any(p in ('', '.', '..') or ':' in p for p in parts):
        raise ContractError(f'Unsafe relative path: {name!r}')
    if PurePosixPath(normalized).is_absolute():
        raise ContractError('Absolute archive entry')
    return normalized


def _read_bounded(path: Path, limit: int) -> bytes:
    if path.is_symlink():
        raise ContractError('Symlinks are not input artifacts')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ContractError('File size limit exceeded')
    return data


def _collect(path: Path, kind: str, limits: Limits, errors: list[str],
             excluded: list[str], store_root: Path) -> tuple[list[tuple[str, bytes]], bytes | None]:
    started = time.monotonic()
    records: list[tuple[str, bytes]] = []
    total = 0

    def add(name: str, data: bytes):
        nonlocal total
        total += len(data)
        if (len(records) >= limits.max_files or len(data) > limits.max_file_bytes
                or total > limits.max_total_bytes
                or time.monotonic() - started > limits.max_seconds):
            raise ContractError('Capture resource budget exceeded')
        records.append((safe_entry(name), data))

    if path.is_symlink():
        raise ContractError('Root symlink is not allowed')
    if path.resolve().is_relative_to(store_root):
        raise ContractError('Managed cache cannot be captured as an input root')
    if not path.exists():
        raise ArtifactUnavailable('Input root does not exist')
    if kind == 'directory':
        if not path.is_dir():
            raise ContractError('Expected directory root')
        for directory, dirs, files in os.walk(path, followlinks=False,
                                               onerror=lambda exc: errors.append(f'Unreadable directory: {exc}')):
            for name in sorted(dirs[:]):
                item = Path(directory) / name
                relative = item.relative_to(path).as_posix()
                if item.is_symlink():
                    dirs.remove(name); errors.append(f'Symlink directory excluded: {relative}')
                elif name in EXCLUDED or item.resolve() == store_root:
                    dirs.remove(name); excluded.append(relative)
            dirs.sort()
            for name in sorted(files):
                item = Path(directory) / name
                relative = item.relative_to(path).as_posix()
                if item.is_symlink() or not item.resolve().is_relative_to(path.resolve()):
                    errors.append(f'Symlink/escaped input excluded: {relative}')
                    continue
                try:
                    add(relative, _read_bounded(item, limits.max_file_bytes))
                except OSError:
                    errors.append(f'Unreadable input: {relative}')
        return records, None
    if kind == 'file':
        add(path.name, _read_bounded(path, limits.max_file_bytes))
        return records, records[0][1]
    if kind != 'jar':
        raise ContractError(f'Unsupported root kind: {kind}')
    raw = _read_bounded(path, limits.max_total_bytes)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > limits.max_files:
            raise ContractError('Archive entry count limit exceeded')
        seen: set[str] = set()
        declared_total = 0
        for info in entries:
            name = safe_entry(info.filename)
            if name in seen:
                raise ContractError('Duplicate normalized archive path')
            seen.add(name)
            if stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1:
                raise ContractError('Symlink/encrypted archive entries are unsupported')
            declared_total += info.file_size
            if (info.file_size > limits.max_file_bytes or declared_total > limits.max_total_bytes
                    or info.file_size / max(1, info.compress_size) > limits.max_compression_ratio):
                raise ContractError('Archive expansion limit exceeded')
        for info in entries:
            if info.is_dir():
                continue
            with archive.open(info) as stream:
                data = stream.read(limits.max_file_bytes + 1)
            add(info.filename, data)
    return records, raw


def _validate_manifest(manifest: dict) -> dict:
    m = json.loads(canonical(manifest))  # Detach caller state; reject non-JSON/NaN.
    if not isinstance(m, dict) or type(m.get('schema_version')) is not int or m['schema_version'] != 1 or not isinstance(m.get('roots'), list):
        raise ContractError('schema_version=1 and explicit roots are required')
    if m.get('track') not in TRACKS:
        raise ContractError('Explicit ANCHOR / FRONTIER / COMPARATIVE track required')
    if m['track'] == 'ANCHOR' and (m.get('minecraft') != '1.20.1' or m.get('loader') != 'forge'):
        raise ContractError('ANCHOR requires Minecraft 1.20.1 and Forge')
    aliases = m.get('namespace_aliases', {})
    if not isinstance(aliases, dict) or any(v not in NAMESPACES for v in aliases.values()):
        raise ContractError('Namespace aliases must explicitly map to known namespaces')
    if m.get('namespace') not in NAMESPACES:
        raise ContractError('Explicit project namespace required')
    ids: set[str] = set()
    for root in m['roots']:
        if not isinstance(root, dict):
            raise ContractError('Each root must be a JSON object')
        required = ('id', 'path', 'kind', 'scope', 'role', 'namespace', 'stage', 'classloader', 'track')
        if any(not isinstance(root.get(k), str) or not root[k] or len(root[k]) > 4096 for k in required):
            raise ContractError('Each root needs explicit origin/scope/namespace/stage/track metadata')
        if root['id'] in ids or root['scope'] not in SCOPES or root['track'] not in TRACKS:
            raise ContractError('Duplicate root ID or invalid scope/track')
        ids.add(root['id'])
        namespace = aliases.get(root['namespace'], root['namespace'])
        if namespace not in NAMESPACES:
            raise ContractError('Unspecified namespace alias (Parchment is annotation, not namespace)')
    return m


def capture_profile(manifest: dict, base: Path, store: Store, *, limits: Limits | None = None) -> dict:
    """Explicitly capture registered local roots; no downloads or script evaluation."""
    m = _validate_manifest(manifest)
    limits = limits or Limits()
    warnings = []
    for field in ('minecraft', 'loader_version'):
        if not isinstance(m.get(field), str) or not re.fullmatch(r'\d+(?:\.\d+)+', m[field]):
            warnings.append(f'UNKNOWN exact {field}')
    for field in ('java_major', 'workspace_revision', 'dirty_hash', 'toolchain', 'physical_side', 'logical_side'):
        if m.get(field) is None:
            warnings.append(f'UNKNOWN {field}')
    if m['track'] == 'ANCHOR' and m.get('java_major') != 17:
        warnings.append('ANCHOR game Java toolchain is not confirmed as 17')
    documents = []; roots = []; unresolved = []; exclusions = []
    total_bytes = 0; total_files = 0
    for order, root in enumerate(m['roots']):
        errors: list[str] = []; excluded: list[str] = []
        path = Path(root['path'])
        if not path.is_absolute():
            path = Path(base) / path
        # Keep the un-resolved final component until _collect rejects symlinks.
        result = dict(root, order=order)
        try:
            records, artifact_bytes = _collect(path, root['kind'], limits, errors, excluded, store.root)
            total_bytes += sum(len(data) for _, data in records)
            total_files += len(records)
            if total_bytes > limits.max_total_bytes or total_files > limits.max_files:
                raise ContractError('Whole-profile capture budget exceeded')
            hashes = [{'path': name, 'hash': digest(data)} for name, data in records]
            # Preserve the whole archive, not just extracted entries. A directory
            # artifact is its exact captured inventory, with each file in the CAS.
            artifact_hash = store.put(artifact_bytes) if artifact_bytes is not None else store.put_json(hashes)
            result['artifact_hash'] = artifact_hash
            for name, data in records:
                suffix = PurePosixPath(name).suffix.lower()
                media = 'class' if suffix == '.class' else 'binary'
                if suffix in TEXT_SUFFIXES:
                    try:
                        data.decode('utf-8'); media = 'text'
                    except UnicodeDecodeError:
                        errors.append(f'Non-UTF8 text not indexed: {name}')
                if suffix == '.jar':
                    errors.append(f'Nested JAR requires its own explicit root: {name}')
                if name.startswith('META-INF/versions/'):
                    errors.append(f'Multi-release class selection unresolved: {name}')
                doc = {k: root[k] for k in ('scope', 'role', 'stage', 'classloader', 'track')}
                doc.update(root_id=root['id'], root_order=order, path=name,
                           namespace=m.get('namespace_aliases', {}).get(root['namespace'], root['namespace']),
                           artifact_hash=artifact_hash, content_hash=store.put(data), size=len(data),
                           media=media, source_binary_match='UNRESOLVED')
                doc['document_id'] = key_for(doc)
                documents.append(doc)
            result['status'] = 'PARTIAL' if errors else 'OK'
        except (OSError, ContractError, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
            result['artifact_hash'] = None; result['status'] = 'ARTIFACT_UNAVAILABLE'
            errors.append(f'{type(exc).__name__}: {exc}')
        if errors:
            unresolved.append({'root_id': root['id'], 'reasons': errors})
        if excluded:
            exclusions.append({'root_id': root['id'], 'paths': excluded})
        roots.append(result)
    if not roots:
        warnings.append('No input roots declared')
    if unresolved:
        warnings.append('UNKNOWN input identity: one or more roots are incomplete')
    p = {'schema_version': 1, 'manifest': m, 'roots': roots, 'documents': documents,
         'identity_status': 'UNKNOWN' if warnings else 'PINNED',
         'resolution': 'CAPTURED_NOT_RUNTIME_VERIFIED', 'warnings': warnings,
         'coverage': {'complete': bool(roots) and not unresolved, 'requested_roots': [r['id'] for r in roots],
                      'analyzed_roots': [r['id'] for r in roots if r['status'] == 'OK'],
                      'unresolved_roots': unresolved, 'exclusions': exclusions}}
    p['profile_hash'] = key_for(p); p['profile_id'] = p['profile_hash']
    return p
