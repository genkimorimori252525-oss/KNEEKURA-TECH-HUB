"""Offline experiment/CAS boundary. No subprocess, endpoint or runtime launch.

LAB report import preserves what a report says without pretending caller JSON is
an authenticated observation. An exact raw RunSnapshot file hash and LAB's own
logical snapshotHash are distinct. The latter is retained, not reimplemented
with Python's different numeric serialization.
"""
from __future__ import annotations

import os
import re
import stat

from .asset_contract import decode_json, _profile
from .experiment_contract import (TARGET_FIELDS, experiment_binding, validate_experiment_request,
                                  validate_experiment_result, validate_target)
from .storage import ContractError, IntegrityError, Store, canonical, digest, key_for, valid_hash
from .task_context import _load_index

_PROVENANCE = 'IMPORTED_LAB_REPORT'
_ATTESTATION = 'NOT_ESTABLISHED'
_SNAPSHOT_FIELDS = {'schemaVersion', 'snapshotId', 'createdAt', 'debugProfile', 'workspaceId',
                    'debugSessionId', 'runId', 'processEpoch', 'worldName', 'source',
                    'observer', 'build', 'runtime', 'snapshotHash', 'techHub'}
_RECORD_FIELDS = {'schema_version', 'record_type', 'request_hash', 'result', 'snapshot_content_hash',
                  'lab_snapshot_hash', 'lab_snapshot_hash_verification', 'provenance', 'runtime_attestation'}


def _read_bounded(store: Store, identifier: str, limit: int) -> bytes:
    path = store.blob_path(valid_hash(identifier))
    if path.is_symlink() or not path.resolve().is_relative_to(store.root):
        raise IntegrityError('CAS path escapes managed storage')
    metadata = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
        raise ContractError('Experiment artifact is not a bounded regular file')
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                         | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode) or opened.st_size > limit
                or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
                or path.is_symlink() or not path.resolve().is_relative_to(store.root)):
            raise IntegrityError('Experiment artifact changed before reading')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if (len(raw) > limit or len(raw) != opened.st_size or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns or after.st_ctime_ns != opened.st_ctime_ns):
        raise IntegrityError('Experiment artifact changed during bounded reading')
    if digest(raw) != identifier:
        raise IntegrityError('Experiment artifact hash mismatch')
    return raw


class _BoundedIndexView:
    """Read-only view of the same Store for the existing index/profile validator."""
    def __init__(self, store):
        self.store = store

    def json(self, identifier):
        return decode_json(_read_bounded(self.store, identifier, 16 * 1024 * 1024),
                           max_bytes=16 * 1024 * 1024)


def _target_backing(store: Store, request: dict) -> None:
    t = request['target']
    snapshot = _load_index(_BoundedIndexView(store), t['index_snapshot_id'])
    p = _profile(snapshot['profile'])
    if (p['profile_id'] != t['profile_id'] or p['manifest'].get('workspace_revision') != t['source_revision']
            or p['manifest'].get('dirty_hash') != t['dirty_hash']):
        raise IntegrityError('Experiment target does not match captured index/profile/source')
    # These are exact retained content identities, not a claim of installed or
    # loaded-runtime equivalence. The later LAB adapter must prove that boundary.
    for field, limit in (('build_artifact_hash', 64 * 1024 * 1024),
                         ('config_hash', 1024 * 1024), ('resource_hash', 16 * 1024 * 1024)):
        _read_bounded(store, t[field], limit)


def prepare_experiment(store: Store, request: dict) -> dict:
    """Validate all backing evidence before retaining a request and its binding."""
    r = validate_experiment_request(request)
    _target_backing(store, r)
    binding = experiment_binding(r)
    request_hash = store.put_json(r)
    binding_hash = store.put_json(binding)
    assertions_hash = store.put_json(r['assertions'])
    for h in (request_hash, binding_hash, assertions_hash, r['target']['index_snapshot_id'],
              r['target']['build_artifact_hash'], r['target']['config_hash'], r['target']['resource_hash']):
        store.pin(h, 'experiment-request:' + request_hash)
    return {'schema_version': 1, 'status': 'OK', 'request_hash': request_hash,
            'binding_hash': binding_hash, 'execution': 'NOT_RUN', 'runtime_attestation': _ATTESTATION}


def load_experiment(store: Store, request_hash: str) -> dict:
    r = validate_experiment_request(decode_json(_read_bounded(store, request_hash, 128 * 1024), max_bytes=128 * 1024))
    if key_for(r) != request_hash:
        raise IntegrityError('Experiment request is not in canonical stored form')
    _target_backing(store, r)
    return r


def _snapshot(store: Store, request: dict, result: dict) -> dict:
    s = decode_json(_read_bounded(store, result['run_snapshot_content_hash'], 2 * 1024 * 1024), max_bytes=2 * 1024 * 1024)
    if not isinstance(s, dict) or set(s) not in (_SNAPSHOT_FIELDS, _SNAPSHOT_FIELDS | {'bridge'}):
        raise ContractError('Expected immutable LAB RunSnapshot with prelaunch TECH HUB binding')
    if (type(s['schemaVersion']) is not int or s['schemaVersion'] != 1
            or type(s['processEpoch']) is not int or not 0 <= s['processEpoch'] <= 2**53 - 1
            or s['snapshotId'] != result['run_snapshot_id'] or canonical(s['techHub']) != canonical(experiment_binding(request))):
        raise IntegrityError('LAB RunSnapshot request/run identity mismatch')
    for field in ('snapshotId', 'debugSessionId', 'runId', 'debugProfile', 'workspaceId'):
        if not isinstance(s[field], str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}', s[field]):
            raise ContractError('Invalid LAB snapshot identity')
    for field in ('createdAt', 'worldName'):
        if not isinstance(s[field], str) or not 1 <= len(s[field]) <= 256:
            raise ContractError('Invalid LAB snapshot metadata')
    for field in ('source', 'observer', 'build', 'runtime'):
        if not isinstance(s[field], dict):
            raise ContractError('Invalid LAB snapshot evidence metadata')
    if not isinstance(s['snapshotHash'], str) or not re.fullmatch(r'sha256:[a-f0-9]{64}', s['snapshotHash']):
        raise ContractError('Invalid LAB logical snapshot hash')
    return s


def _validated_report(store, request_hash, result):
    request = load_experiment(store, request_hash)
    r = validate_experiment_result(result, request)
    snapshot = _snapshot(store, request, r)
    for entry in r['evidence']:
        raw = _read_bounded(store, entry['content_hash'], entry['size_bytes'])
        if len(raw) != entry['size_bytes']:
            raise IntegrityError('Experiment evidence size mismatch')
    return request, r, snapshot


def _record(request_hash, result, snapshot):
    return {'schema_version': 1, 'record_type': 'experiment_result_import',
            'request_hash': request_hash, 'result': result,
            'snapshot_content_hash': result['run_snapshot_content_hash'],
            'lab_snapshot_hash': snapshot['snapshotHash'], 'lab_snapshot_hash_verification': _ATTESTATION,
            'provenance': _PROVENANCE, 'runtime_attestation': _ATTESTATION}


def _summary(result_hash, record):
    result = record['result']
    uncertain = (result['execution']['status'] in ('UNKNOWN', 'PARTIAL')
                 or result['execution']['cleanup'] in ('UNKNOWN', 'FAILED')
                 or any(row['status'] == 'UNKNOWN' for row in result['execution']['action_receipts']))
    return {'schema_version': 1, 'status': 'OK', 'result_hash': result_hash,
            'request_hash': record['request_hash'], 'experiment_id': result['experiment_id'],
            'generation': result['generation'], 'run_snapshot_id': result['run_snapshot_id'],
            'snapshot_content_hash': record['snapshot_content_hash'],
            'provenance': _PROVENANCE, 'runtime_attestation': _ATTESTATION,
            'reported_execution': result['execution']['status'],
            'reported_cleanup': result['execution']['cleanup'], 'reported_assertions': result['assertions'],
            'next_operation': 'experiment.reconcile_unknown' if uncertain else 'experiment.inspect_result'}


def import_experiment_result(store: Store, request_hash: str, result: dict) -> dict:
    """Retain a linked report only after the complete referenced inventory verifies.

    All artifact bytes must already be in the existing Store. No path, URL,
    executable or credential from a report is followed or published.
    """
    _, r, snapshot = _validated_report(store, request_hash, result)
    record = _record(request_hash, r, snapshot)
    h = store.put_json(record)
    for pin in (h, request_hash, r['run_snapshot_content_hash'], *(x['content_hash'] for x in r['evidence'])):
        store.pin(pin, 'experiment-result:' + h)
    return _summary(h, record)


def inspect_experiment_result(store: Store, result_hash: str, current_target: dict | None = None) -> dict:
    """Read-only consistency/staleness view. Historical reports remain unchanged."""
    record = decode_json(_read_bounded(store, result_hash, 2 * 1024 * 1024), max_bytes=2 * 1024 * 1024)
    if not isinstance(record, dict) or set(record) != _RECORD_FIELDS:
        raise ContractError('Not an experiment result import')
    req, r, snapshot = _validated_report(store, record['request_hash'], record['result'])
    if canonical(record) != canonical(_record(record['request_hash'], r, snapshot)):
        raise IntegrityError('Experiment import metadata mismatch')
    summary = _summary(result_hash, record)
    differences = []
    if current_target is not None:
        target = validate_target(current_target)
        differences = sorted(field for field in TARGET_FIELDS if target[field] != req['target'][field])
    return dict(summary, currentness='NOT_CHECKED' if current_target is None else
                'REVERIFY_REQUIRED' if differences else 'MATCHING_DECLARED_TARGET',
                changed_target_fields=differences)
