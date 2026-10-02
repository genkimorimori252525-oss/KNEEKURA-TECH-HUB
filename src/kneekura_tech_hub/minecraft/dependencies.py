"""Bounded target-code profiles plus complete, receipt-bound dependency bytes.

Retaining every resolved archive does not imply expanded dependency analysis or
loaded-class attestation. The broad imported profile is never rewritten here.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from .storage import ContractError, Store, canonical, digest, key_for, valid_hash, capture_profile
from .workspace import (_workspace, workspace_fingerprint, configuration_fingerprint,
                        import_resolved, EXPORT_FORMAT)

RUNTIME_SCOPE = 'TARGET_CODE_AND_DEPENDENCY_BYTES'
MAX_ENTRIES = 4096
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_EXPORT_BYTES = 4 * 1024 * 1024


def _json(raw: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ContractError('Duplicate key in resolved export')
            result[key] = value
        return result
    try: return json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError) as exc: raise ContractError('Malformed resolved export') from exc


def _read_file(path: Path, maximum: int) -> bytes:
    if (not path.is_absolute() or path.is_symlink() or path.resolve() != path
            or not path.is_file()):
        raise ContractError('Dependency/export must be a canonical nonsymlink regular file')
    try:
        before = path.stat()
        if not 0 < before.st_size <= maximum: raise ContractError('Dependency/export byte budget exceeded')
        with path.open('rb') as stream: raw = stream.read(maximum + 1)
        after = path.stat()
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ContractError('Dependency/export changed while reading')
        if len(raw) != before.st_size: raise ContractError('Incomplete dependency/export read')
        return raw
    except OSError as exc: raise ContractError('Dependency/export unavailable') from exc


def _export_authority(store: Store, registry: dict):
    root = _workspace(registry.get('workspace'))
    receipt_hash = valid_hash(registry.get('export_receipt_hash'))
    receipt = store.json(receipt_hash)
    if not isinstance(receipt, dict): raise ContractError('Registered export receipt required')
    request = receipt.get('request', {}); process = receipt.get('process', {})
    source = workspace_fingerprint(root); config = configuration_fingerprint(root)
    if (request.get('kind') != 'export' or request.get('workspace') != str(root)
            or request.get('source_generation') != source or request.get('configuration_fingerprint') != config
            or receipt.get('source_generation') != source or receipt.get('source_generation_after') != source
            or receipt.get('result', {}).get('outcome') != 'PASS'
            or process.get('completed') is not True or type(process.get('exit_code')) is not int
            or process['exit_code'] != 0):
        raise ContractError('Successful same-source/config registered export receipt required')
    destination = root/'build/kneekura/resolved-inputs.json'
    outputs = receipt.get('outputs')
    if (not isinstance(outputs, list) or len(outputs) != 1 or not isinstance(outputs[0], dict)
            or outputs[0].get('path') != str(destination)):
        raise ContractError('Receipt must bind the exact resolved-input export')
    raw_hash = valid_hash(outputs[0].get('content_hash'))
    raw = store.read(raw_hash)
    if len(raw) > MAX_EXPORT_BYTES or _read_file(destination, MAX_EXPORT_BYTES) != raw:
        raise ContractError('Current resolved export differs from its registered immutable output')
    export = _json(raw)
    if (not isinstance(export, dict) or type(export.get('schema_version')) is not int
            or export['schema_version'] != 1 or export.get('format') != EXPORT_FORMAT
            or export.get('workspace') != str(root) or export.get('source_fingerprint') != source
            or export.get('configuration_fingerprint') != config
            or export.get('unresolved') != []):
        raise ContractError('Complete current resolved export with no unresolved dependencies required')
    artifacts = export.get('artifacts')
    if not isinstance(artifacts, list) or not 1 <= len(artifacts) <= MAX_ENTRIES:
        raise ContractError('Bounded nonempty complete dependency export required')
    if {a.get('scope') for a in artifacts if isinstance(a, dict)} != {'compile', 'runtime'}:
        raise ContractError('Complete compile and runtime dependency entries required')
    return root, receipt_hash, raw_hash, export


def _inventory(store: Store, registry: dict, *, retain: bool):
    root, receipt_hash, raw_hash, export = _export_authority(store, registry)
    entries = []; files = []; captured = {}; retained = set(); total = 0
    for order, artifact in enumerate(export['artifacts']):
        if (not isinstance(artifact, dict) or artifact.get('scope') not in ('compile', 'runtime')
                or any(not isinstance(artifact.get(k), str) or not 1 <= len(artifact[k]) <= 2048
                       or any(ord(c) < 32 or ord(c) == 127 for c in artifact[k])
                       for k in ('coordinate', 'namespace', 'stage', 'path'))):
            raise ContractError('Malformed mandatory resolved dependency entry')
        expected = valid_hash(artifact.get('sha256')); path = Path(artifact['path'])
        if path.suffix.lower() not in ('.jar', '.zip'): raise ContractError('Resolved dependency must retain an original JAR/ZIP archive')
        if str(path) not in captured:
            raw = _read_file(path, MAX_ARCHIVE_BYTES)
            actual = digest(raw)
            if actual != expected: raise ContractError('Resolved dependency bytes changed')
            total += len(raw)
            if total > MAX_TOTAL_BYTES: raise ContractError('Dependency inventory byte budget exceeded')
            if actual not in retained:
                if retain: store.put(raw)
                elif store.read(actual) != raw: raise ContractError('Retained dependency bytes differ')
                retained.add(actual)
            captured[str(path)] = (actual, len(raw))
        actual, size = captured[str(path)]
        if actual != expected: raise ContractError('Conflicting duplicate dependency path')
        entries.append(dict(order=order, coordinate=artifact['coordinate'], scope=artifact['scope'],
                            namespace=artifact['namespace'], stage=artifact['stage'], sha256=expected,
                            size_bytes=size, retention='original_archive_bytes'))
        files.append(dict(order=order, path=str(path), sha256=expected, size_bytes=size))
    if (workspace_fingerprint(root) != export['source_fingerprint']
            or configuration_fingerprint(root) != export['configuration_fingerprint']):
        raise ContractError('Workspace changed while verifying dependency inventory')
    inventory = dict(schema_version=1, kind='resolved_dependency_bytes', runtime_scope=RUNTIME_SCOPE,
                     export_receipt_hash=receipt_hash, resolved_inputs_hash=raw_hash, workspace=str(root),
                     source_generation=export['source_fingerprint'],
                     configuration_fingerprint=export['configuration_fingerprint'], entries=entries)
    return inventory, files, export


def prepare_dependency_inventory(store: Store, registry: dict) -> dict:
    """Retain exact export and JAR bytes without resolving, building, or launching."""
    inventory, files, _ = _inventory(store, registry, retain=True)
    h = store.put_json(inventory)
    for ref in {h, inventory['export_receipt_hash'], inventory['resolved_inputs_hash'],
                *(entry['sha256'] for entry in inventory['entries'])}:
        store.pin(ref, 'dependency-inventory:' + h)
    return dict(dependency_inventory_hash=h, dependency_inventory=inventory, dependency_files=files)


def validate_dependency_inventory(store: Store, registry: dict) -> dict:
    """Re-derive every ordered row from registered export authority, never caller rows."""
    if registry.get('runtime_scope') != RUNTIME_SCOPE:
        raise ContractError('Explicit target-code/dependency-byte runtime scope required')
    h = valid_hash(registry.get('dependency_inventory_hash')); recorded = store.json(h)
    inventory, files, _ = _inventory(store, registry, retain=False)
    if canonical(recorded) != canonical(inventory):
        raise ContractError('Inventory differs from the complete ordered registered export')
    return dict(dependency_inventory_hash=h, dependency_inventory=inventory, dependency_files=files)


class _RetainedCapture:
    """Read-only capture sink: every expected target byte must already be retained."""
    def __init__(self, store: Store):
        self.store = store
        self.root = store.root

    def put(self, data: bytes) -> str:
        h = digest(data)
        if self.store.read(h) != data: raise ContractError('Retained target bytes differ')
        return h

    def put_json(self, value) -> str:
        return self.put(canonical(value))



def _empty_optional_resource_directory(path: Path) -> bool:
    """Only a proven directly empty real directory is byte-equivalent to absence."""
    try:
        before = path.lstat()
        if stat.S_ISLNK(before.st_mode): raise ContractError('Optional resource root is a symlink')
        if not stat.S_ISDIR(before.st_mode): return False
        with os.scandir(path) as entries:
            empty = next(entries, None) is None
        after = path.lstat()
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        if any(getattr(before, k) != getattr(after, k) for k in fields):
            raise ContractError('Optional resource directory changed while checking emptiness')
        return empty
    except FileNotFoundError:
        # A missing optional root is handled by the existing explicit absence path.
        return False
    except OSError as exc:
        raise ContractError('Cannot prove optional resource directory is empty') from exc


def _target_profile(store: Store, registry: dict, bundle: dict, *, physical_side: str,
                    retain: bool) -> dict:
    root, _, _, export = _export_authority(store, registry)
    manifest = import_resolved(export, root, physical_side=physical_side)
    from .target_selection import validate_selection
    target = validate_selection(store, registry, bundle['dependency_inventory']) if 'target_selection' in registry else None
    target_roots = target['selected_target_root_ids'] if target else []
    selected = []; absent = []
    for item in manifest['roots']:
        if item['id'].startswith('dependency:') and item['id'] not in target_roots: continue
        path = Path(item['path'])
        if item['role'] == 'resources' and _empty_optional_resource_directory(path):
            absent.append(item)
        elif not path.exists():
            if item['role'] != 'resources':
                raise ContractError('Mandatory target source/output/config input is absent')
            absent.append(item)
        else: selected.append(item)
    if not any(r['role'] == 'source' for r in selected) or not any(r['role'] == 'binary' for r in selected):
        raise ContractError('Complete target source and compiled output roots required')
    compile_hash = valid_hash(registry.get('build_receipt_hash')); receipt = store.json(compile_hash)
    source = manifest['dirty_hash']
    if (receipt.get('request', {}).get('kind') != 'compile'
            or receipt['request'].get('workspace') != str(root)
            or receipt.get('source_generation') != source or receipt.get('source_generation_after') != source
            or receipt.get('result', {}).get('outcome') != 'PASS'):
        raise ContractError('Target profile requires its successful same-source compile receipt')
    manifest.update(roots=selected, runtime_scope=RUNTIME_SCOPE,
                    dependency_inventory_hash=bundle['dependency_inventory_hash'],
                    compile_receipt_hash=compile_hash,
                    binary_generation={'status':'SAME_SOURCE_COMPILE_RECEIPT', 'receipt_hash':compile_hash})
    if target: manifest['target_selection'] = target['target_selection']
    profile = capture_profile(manifest, root, store if retain else _RetainedCapture(store))
    if profile['identity_status'] != 'PINNED' or profile['coverage']['complete'] is not True:
        raise ContractError('Target code roots must be completely captured and exactly pinned')
    for item in profile['roots']:
        if item['role'] != 'binary': continue
        if not any((root/str(row.get('path',''))).resolve() == Path(item['path']).resolve()
                   and row.get('content_hash') == item['artifact_hash'] for row in receipt.get('outputs', [])):
            raise ContractError('Target compiled root differs from registered same-source build output')
    # Completeness of this selected scope cannot be mistaken for whole-tree analysis.
    profile.pop('profile_id'); profile.pop('profile_hash')
    profile['identity_status'] = 'PINNED_TARGET_CODE'
    profile['coverage'].update(complete=False, target_complete=True, scope='TARGET_CODE',
                               absent_target_roots=absent, dependency_bytes_complete=True,
                               dependency_analysis='NOT_CLAIMED', loaded_class_attestation='NOT_OBSERVED')
    if target:
        profile['coverage'].update(selected_target_root_ids=target_roots, dependency_analysis='SELECTED_TARGET_ONLY')
    profile['warnings'].append('Only target code is analyzed; dependency bytes are retained without whole-tree analysis or loaded-class attestation')
    profile['profile_id'] = profile['profile_hash'] = key_for(profile)
    if (workspace_fingerprint(root) != export['source_fingerprint']
            or configuration_fingerprint(root) != export['configuration_fingerprint']):
        raise ContractError('Workspace changed while verifying complete target closure')
    if retain: store.put_json(profile)
    return profile


def prepare_target_profile(store: Store, registry: dict, *, physical_side='server') -> dict:
    """Capture a new explicitly limited profile. Never relabel a broad UNKNOWN profile."""
    bundle = prepare_dependency_inventory(store, registry)
    return _target_profile(store, registry, bundle, physical_side=physical_side, retain=True)


def validate_target_profile(store: Store, registry: dict, profile: dict) -> dict:
    """Re-derive the entire receipt-bound target closure without writing evidence."""
    bundle = validate_dependency_inventory(store, registry)
    expected = _target_profile(store, registry, bundle,
        physical_side=profile.get('manifest', {}).get('physical_side'), retain=False)
    if canonical(profile) != canonical(expected):
        raise ContractError('Target profile differs from complete export/compile-derived closure')
    return bundle
