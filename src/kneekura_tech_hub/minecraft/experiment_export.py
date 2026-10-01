"""Bounded, hash-verified private export import into the existing TECH Store.

Manifest entries never contain source paths. Only fixed hash-derived filenames
under the separately pinned owner's transport root are read. The entire export
and its linked report are checked before any new bytes are retained in CAS.
"""
from __future__ import annotations

import time

from .asset_contract import decode_json
from .experiment_adapter import _directory, _file
from .experiment_bridge import _read_bounded, _record, _validate_snapshot, import_experiment_result, load_experiment
from .experiment_contract import validate_experiment_result
from .experiment_control import _registry, _timeout
from .storage import ContractError, IntegrityError, Store, canonical, key_for, valid_hash

_FIELDS = {'schema_version', 'kind', 'request_hash', 'result_hash', 'run_snapshot_content_hash',
    'contains_private_evidence', 'provenance', 'runtime_attestation', 'blobs'}
_CLASSES = {'PRIVATE_RETAINED_EVIDENCE', 'PRIVATE_RUN_SNAPSHOT', 'PRIVATE_EXPERIMENT_RESULT', 'DERIVED_EVIDENCE_PROJECTION'}
_TOTAL_BYTES = 64*1024*1024


def _manifest(value, request_hash):
    if (not isinstance(value, dict) or set(value) != _FIELDS or type(value['schema_version']) is not int
            or value['schema_version'] != 1 or value['kind'] != 'lab_experiment_export'
            or value['request_hash'] != request_hash or value['contains_private_evidence'] is not True
            or value['provenance'] != 'FINALIZED_LAB_EVIDENCE_REPORT'
            or value['runtime_attestation'] != 'NOT_ESTABLISHED'):
        raise ContractError('Exact private finalized LAB export required')
    result_hash = valid_hash(value['result_hash']); snapshot_hash = valid_hash(value['run_snapshot_content_hash'])
    if result_hash == snapshot_hash: raise IntegrityError('Export artifact roles collide')
    rows = value['blobs']
    if not isinstance(rows, list) or not 2 <= len(rows) <= 130:
        raise ContractError('Bounded whole export inventory required')
    result = {}; total = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'content_hash', 'size_bytes', 'classification'}:
            raise ContractError('Hash-only export inventory required')
        h = valid_hash(row['content_hash']); size = row['size_bytes']; classification = row['classification']
        if not isinstance(classification, str) or classification not in _CLASSES or h in result:
            raise ContractError('Invalid export classification or duplicate identity')
        limit = 1024*1024 if h == result_hash else 2*1024*1024 if h == snapshot_hash else 16*1024*1024
        expected = 'PRIVATE_EXPERIMENT_RESULT' if h == result_hash else 'PRIVATE_RUN_SNAPSHOT' if h == snapshot_hash else None
        if (type(size) is not int or not 1 <= size <= limit
                or expected is not None and classification != expected
                or expected is None and classification not in ('PRIVATE_RETAINED_EVIDENCE', 'DERIVED_EVIDENCE_PROJECTION')):
            raise ContractError('Invalid export artifact size or role')
        total += size; result[h] = row
    if total > _TOTAL_BYTES or not {result_hash, snapshot_hash} <= set(result):
        raise ContractError('Export is incomplete or exceeds total byte limit')
    return result


def import_export(store: Store, registry: dict, request_hash: str, manifest_hash: str):
    """Import the exact finalized export; never execute, follow paths, or promote claims."""
    request_hash = valid_hash(request_hash); manifest_hash = valid_hash(manifest_hash)
    deadline = time.monotonic() + _timeout(registry)
    request = load_experiment(store, request_hash)
    _, owner = _registry(registry, deadline=deadline)
    if (owner['run']['identity']['requestHash'] != request_hash
            or owner['run']['identity']['experimentId'] != request['experiment_id']):
        raise IntegrityError('Export owner belongs to another experiment')
    root = _directory(str(_directory(owner['inputRoot'])/'exports'/request_hash))
    raw_manifest = _file(root/'manifests'/(manifest_hash+'.json'), 128*1024, expected=manifest_hash, deadline=deadline)
    manifest = decode_json(raw_manifest, max_bytes=128*1024)
    inventory = _manifest(manifest, request_hash)
    # Bound aggregate retained memory before any blob read. No path from the
    # manifest is followed, even when a file or ancestor becomes a symlink.
    blobs = {}
    for h, row in inventory.items():
        raw = _file(root/'blobs'/h, row['size_bytes'], expected=h, deadline=deadline)
        if len(raw) != row['size_bytes']: raise IntegrityError('Export blob size mismatch')
        blobs[h] = raw
    report = validate_experiment_result(decode_json(blobs[manifest['result_hash']], max_bytes=1024*1024), request)
    if report['run_snapshot_content_hash'] != manifest['run_snapshot_content_hash']:
        raise IntegrityError('Export snapshot linkage mismatch')
    expected = {manifest['result_hash'], manifest['run_snapshot_content_hash']}
    for row in report['evidence']:
        h = row['content_hash']
        if h in expected or h not in inventory or inventory[h]['size_bytes'] != row['size_bytes']:
            raise IntegrityError('Export evidence inventory mismatch')
        expected.add(h)
    if set(inventory) != expected: raise IntegrityError('Export contains unreferenced artifacts')
    snapshot = _validate_snapshot(request, report, blobs[manifest['run_snapshot_content_hash']])
    identity = owner['run']['identity']
    for field, identity_field in (('debugSessionId', 'debugSessionId'), ('runId', 'runId'),
                                 ('snapshotId', 'runSnapshotId'), ('processEpoch', 'processEpoch')):
        if snapshot[field] != identity[identity_field]:
            raise IntegrityError('Export snapshot belongs to another registered run')
    # Validate existing CAS collisions before retaining any new bytes. Store.put
    # still rechecks during writes and never repairs corrupt retained history.
    derived_record = _record(request_hash, report, snapshot)
    for h, raw in {manifest_hash:raw_manifest, **blobs, key_for(derived_record):canonical(derived_record)}.items():
        path = store.blob_path(h)
        if path.exists() or path.is_symlink(): _read_bounded(store, h, len(raw))
    _registry(registry, deadline=deadline)
    for h, raw in blobs.items():
        if store.put(raw) != h: raise IntegrityError('Export CAS identity mismatch')
    if store.put(raw_manifest) != manifest_hash: raise IntegrityError('Export manifest CAS identity mismatch')
    imported = import_experiment_result(store, request_hash, report)
    for h in (manifest_hash, *blobs): store.pin(h, 'experiment-export:' + manifest_hash)
    return dict(imported, export_manifest_hash=manifest_hash, source_result_hash=manifest['result_hash'],
                export_provenance='FINALIZED_LAB_EVIDENCE_REPORT')
