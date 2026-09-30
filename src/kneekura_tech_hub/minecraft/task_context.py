"""Inert task requests and private, read-only inputs for task planning.

Task text conveys intent only. It never selects files, providers, permissions,
or executable operations. Input bundles may contain secrets and must not be
serialized as public task context; public summaries are separate projections.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat

from . import index, verification
from .storage import ArtifactUnavailable, ContractError, IntegrityError, Store, canonical, key_for, valid_hash


TASK_FIELDS = {'schema_version', 'intent', 'goal', 'constraints', 'acceptance'}
TASK_INTENTS = {'investigate', 'edit_code', 'create_asset', 'verify_server',
                'verify_client', 'compatibility_research'}


def _detach(value):
    """Copy JSON data using the same finite canonical encoding as the CAS."""
    try:
        return json.loads(canonical(value))
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ContractError('Task inputs must be finite canonical JSON') from exc


def validate_task_request(value: dict) -> dict:
    """Validate the exact bounded request schema without interpreting its text."""
    if not isinstance(value, dict) or set(value) != TASK_FIELDS:
        raise ContractError('TaskRequest requires exactly schema_version, intent, goal, constraints, acceptance')
    if type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ContractError('TaskRequest schema_version must be integer 1')
    if not isinstance(value['intent'], str) or value['intent'] not in TASK_INTENTS:
        raise ContractError('Unknown TaskRequest intent')
    if not isinstance(value['goal'], str) or not 1 <= len(value['goal']) <= 4096:
        raise ContractError('TaskRequest goal must contain 1..4096 Unicode code points')
    for field in ('constraints', 'acceptance'):
        entries = value[field]
        if (not isinstance(entries, list) or len(entries) > 32
                or any(not isinstance(item, str) or not 1 <= len(item) <= 1024 for item in entries)):
            raise ContractError(f'TaskRequest {field} must contain at most 32 strings of 1..1024 Unicode code points')
    return _detach(value)


def _optional_object(value, label: str) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ContractError(f'{label} must be a JSON object')
    return _detach(value)


def _load_index(store: Store, identifier: str) -> dict:
    """Use the existing CAS loader, then verify its embedded profile identity."""
    valid_hash(identifier)
    try:
        snapshot = _detach(index._load(store, identifier))
    except (AttributeError, TypeError, ContractError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise IntegrityError('Artifact is not a valid index snapshot') from exc
    if (type(snapshot.get('schema_version')) is not int or snapshot['schema_version'] != 1
            or not isinstance(snapshot.get('profile'), dict)
            or not isinstance(snapshot.get('bytecode'), dict)):
        raise IntegrityError('Artifact is not an index snapshot')
    profile = snapshot['profile']
    body = {k: v for k, v in profile.items() if k not in ('profile_id', 'profile_hash')}
    if (profile.get('profile_id') != profile.get('profile_hash')
            or key_for(body) != profile.get('profile_id')):
        raise IntegrityError('Profile identity mismatch')
    if (type(profile.get('schema_version')) is not int or profile['schema_version'] != 1
            or not isinstance(profile.get('manifest'), dict)):
        raise IntegrityError('Artifact does not contain a captured profile')
    return snapshot


def _evidence_metadata(store: Store, hashes: tuple[str, ...]) -> list[dict]:
    """Bounded existence/size inspection only; this does not attest blob bytes."""
    if not isinstance(hashes, (tuple, list)) or len(hashes) > 32:
        raise ContractError('At most 32 ordered evidence hashes are allowed')
    identifiers = [valid_hash(value) for value in hashes]
    if len(set(identifiers)) != len(identifiers):
        raise ContractError('Evidence hashes must be distinct')
    result = []
    for identifier in identifiers:
        path = store.blob_path(identifier)
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(store.root):
                raise IntegrityError('Evidence CAS path escapes managed storage')
            metadata = path.stat(follow_symlinks=False)
        except OSError as exc:
            raise ArtifactUnavailable(f'Unavailable evidence artifact {identifier}') from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise ArtifactUnavailable(f'Evidence artifact is not a regular file: {identifier}')
        result.append({'content_hash': identifier, 'size': metadata.st_size})
    return result


def load_task_inputs(store: Store, *, index_id: str | None = None,
                     run_registry: dict | None = None, input_registry: dict | None = None,
                     blockbench_registry: dict | None = None, session: dict | None = None,
                     evidence_hashes: tuple[str, ...] = (), world: str | None = None,
                     run_directory: str | None = None, core_configured: bool = False) -> dict:
    """Build a private input bundle without preparing, writing, or executing.

Registries are detached JSON, not validated execution authority. Session input
is already-loaded JSON; the CLI must use runtime.load_session for private-file
checks. Evidence entries are metadata pointers only. Their bytes still need
hash verification before any downstream interpretation or public summary.
"""
    if type(core_configured) is not bool:
        raise ContractError('core_configured must be an explicit boolean')
    for label, value in (('world', world), ('run_directory', run_directory)):
        if value is not None and not isinstance(value, str):
            raise ContractError(f'{label} must be a string or null')
    registries = {
        'run_registry': _optional_object(run_registry, 'run_registry'),
        'input_registry': _optional_object(input_registry, 'input_registry'),
        'blockbench_registry': _optional_object(blockbench_registry, 'blockbench_registry'),
    }
    selected_session = _optional_object(session, 'session')
    if selected_session is not None:
        contract = selected_session.get('contract')
        if not isinstance(contract, dict):
            raise ContractError('Session requires an existing contract object')
        errors = verification._identity_errors(contract, {'identity': contract})
        if errors:
            raise ContractError('; '.join(errors))
    snapshot = _load_index(store, index_id) if index_id is not None else None
    if snapshot is not None and selected_session is not None:
        profile = snapshot['profile']
        expected = {'profile_id': profile['profile_id'], 'index_snapshot_id': index_id}
        for contract_field, manifest_field in (('source_revision', 'workspace_revision'),
                                                ('dirty_hash', 'dirty_hash')):
            captured = profile['manifest'].get(manifest_field)
            if captured is not None:
                expected[contract_field] = captured
        if any(contract.get(field) != value for field, value in expected.items()):
            raise IntegrityError('Session identity differs from the supplied index/profile')
    return {
        'index_snapshot_id': index_id, 'index': snapshot, **registries,
        'session': selected_session, 'evidence': _evidence_metadata(store, evidence_hashes),
        'world': world, 'run_directory': run_directory, 'core_configured': core_configured,
    }


_TARGET_FIELDS = ('profile_id', 'profile_hash', 'index_snapshot_id', 'minecraft', 'loader',
                  'loader_version', 'java_major', 'track', 'workspace_revision')


def _matching(value, pattern: str, maximum: int = 64) -> str | None:
    return value if isinstance(value, str) and len(value) <= maximum and re.fullmatch(pattern, value) else None


def summarize_target(inputs: dict) -> dict:
    """Project exact captured target values; unknown values never become defaults."""
    result = dict.fromkeys(_TARGET_FIELDS)
    snapshot = inputs.get('index')
    if snapshot is not None:
        profile = snapshot['profile']
        manifest = profile['manifest']
        for field in ('profile_id', 'profile_hash'):
            result[field] = _matching(profile.get(field), r'[a-f0-9]{64}')
        result['index_snapshot_id'] = _matching(inputs.get('index_snapshot_id'), r'[a-f0-9]{64}')
        for field in ('minecraft', 'loader_version'):
            result[field] = _matching(manifest.get(field), r'[0-9]+(?:\.[0-9]+)+', 64)
        loader = manifest.get('loader')
        if isinstance(loader, str) and loader in ('forge', 'neoforge', 'fabric', 'quilt', 'vanilla'):
            result['loader'] = loader
        major = manifest.get('java_major')
        if type(major) is int and 1 <= major <= 255:
            result['java_major'] = major
        track = manifest.get('track')
        if isinstance(track, str) and track in ('ANCHOR', 'FRONTIER', 'COMPARATIVE'):
            result['track'] = track
        result['workspace_revision'] = _matching(manifest.get('workspace_revision'), r'[a-f0-9]{40}|[a-f0-9]{64}')
    result['unknown_fields'] = [field for field in _TARGET_FIELDS if result[field] is None]
    _check_private_aliases(result, inputs)
    return result


_EVIDENCE_JSON_LIMIT = 1024 * 1024
_EVIDENCE_CHUNK_BYTES = 64 * 1024
_HASH_FIELDS = ('profile_id', 'profile_hash', 'index_snapshot_id', 'build_artifact_hash', 'dirty_hash')
_IDENTITY_FIELDS = (*_HASH_FIELDS, 'source_revision', 'run_id', 'session_epoch')
_UUID_PATTERN = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
_ENUM_FIELDS = {
    'kind': frozenset(('receipt', 'run-receipt', 'input-receipt', 'build-receipt', 'runtime-receipt',
        'mapping-table', 'native-input-binding', 'native-input-receipt',
        'authenticated-observer-error', 'validated-observer-handshake-summary',
        'compile', 'unit', 'export', 'gametest', 'server', 'client', 'build')),
    'record_type': frozenset(('execution_receipt', 'input_receipt', 'build_receipt',
        'verification_receipt', 'asset_editor_inspection', 'asset_session_capture',
        'asset_export', 'asset_guard_package', 'asset_request')),
    'status': frozenset(('OK', 'PARTIAL', 'ERROR', 'STALE', 'BLOCKED', 'UNKNOWN',
        'UNSUPPORTED', 'NOT_RUN', 'STARTED', 'COMPLETED', 'PASS', 'FAIL')),
    'outcome': frozenset(('PASS', 'FAIL', 'BLOCKED', 'UNKNOWN', 'NOT_RUN', 'UNSUPPORTED')),
    'input_status': frozenset(('BLOCKED', 'UNKNOWN', 'COMPLETED')),
}


def _enum(value, field: str) -> str | None:
    return value if isinstance(value, str) and value in _ENUM_FIELDS[field] else None


def _verified_evidence_bytes(store: Store, pointer: dict) -> bytes | None:
    """Hash every byte using bounded memory, retaining only small record bodies."""
    identifier = valid_hash(pointer.get('content_hash'))
    size = pointer.get('size')
    if type(size) is not int or size < 0:
        raise ContractError('Evidence size must be a nonnegative integer')
    path = store.blob_path(identifier)
    try:
        if path.is_symlink() or not path.resolve().is_relative_to(store.root):
            raise IntegrityError('Evidence CAS path escapes managed storage')
        metadata = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(metadata.st_mode):
            raise ArtifactUnavailable('Evidence artifact is not a regular file')
        # NOFOLLOW blocks a substituted leaf symlink; NONBLOCK avoids hanging on
        # a substituted FIFO before the descriptor's regular-file check.
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                             | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if (not stat.S_ISREG(opened.st_mode) or opened.st_size != size
                    or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
                    or path.is_symlink() or not path.resolve().is_relative_to(store.root)):
                raise IntegrityError('Evidence metadata changed after input capture')
            checksum = hashlib.sha256()
            retained = bytearray() if size <= _EVIDENCE_JSON_LIMIT else None
            total = 0
            while chunk := stream.read(_EVIDENCE_CHUNK_BYTES):
                total += len(chunk)
                if total > size:
                    raise IntegrityError('Evidence size changed while reading')
                checksum.update(chunk)
                if retained is not None:
                    retained.extend(chunk)
            after = os.fstat(stream.fileno())
            if (total != size or after.st_size != size or after.st_mtime_ns != opened.st_mtime_ns
                    or after.st_ctime_ns != opened.st_ctime_ns):
                raise IntegrityError('Evidence metadata changed while reading')
            if checksum.hexdigest() != identifier:
                raise IntegrityError('Evidence artifact hash mismatch')
            return bytes(retained) if retained is not None else None
    except OSError as exc:
        raise ArtifactUnavailable(f'Unavailable evidence artifact {identifier}') from exc


def _index_evidence_summary(inputs: dict) -> dict:
    snapshot = inputs.get('index')
    result = {'available': snapshot is not None, 'source_documents': 0, 'prepared_bytecode': 0,
              'resources': 0, 'coverage_complete': None, 'unresolved_roots': 0, 'unresolved_bytecode': 0}
    if snapshot is None:
        return result
    profile = snapshot['profile']
    documents = profile.get('documents')
    if isinstance(documents, list):
        for document in documents:
            if not isinstance(document, dict):
                continue
            result['source_documents'] += document.get('media') == 'text'
            result['resources'] += (document.get('role') in ('resource', 'resources')
                                    and document.get('media') != 'class')
    result['prepared_bytecode'] = len(snapshot['bytecode'])
    unresolved = snapshot.get('bytecode_unresolved')
    if isinstance(unresolved, list):
        result['unresolved_bytecode'] = len(unresolved)
    coverage = profile.get('coverage')
    if isinstance(coverage, dict):
        complete = coverage.get('complete')
        result['coverage_complete'] = complete if type(complete) is bool else None
        if isinstance(coverage.get('unresolved_roots'), list):
            result['unresolved_roots'] = len(coverage['unresolved_roots'])
    return result


def _expected_evidence_identity(inputs: dict) -> dict:
    expected = {}
    snapshot = inputs.get('index')
    if snapshot is not None:
        profile = snapshot['profile']
        expected.update(profile_id=profile['profile_id'], profile_hash=profile['profile_hash'],
                        index_snapshot_id=inputs['index_snapshot_id'])
        for field, captured in (('source_revision', 'workspace_revision'), ('dirty_hash', 'dirty_hash')):
            if profile['manifest'].get(captured) is not None:
                expected[field] = profile['manifest'][captured]
    session = inputs.get('session')
    if session is not None:
        contract = session['contract']
        for field in _IDENTITY_FIELDS:
            if field in contract:
                if field in expected and expected[field] != contract[field]:
                    raise IntegrityError('Session identity differs from the supplied index/profile')
                expected[field] = contract[field]
        expected.setdefault('profile_hash', contract.get('profile_id'))
    return expected


def _receipt_containers(record: dict) -> list[dict]:
    # Only these existing protocol containers supply identity/status. Arbitrary
    # nested logs, source, images and body fields are never inspected or copied.
    containers = [record]
    if isinstance(record.get('identity'), dict):
        containers.append(record['identity'])
    result = record.get('result')
    if isinstance(result, dict):
        containers.append(result)
        if isinstance(result.get('identity'), dict):
            containers.append(result['identity'])
    request = record.get('request')
    if isinstance(request, dict) and isinstance(request.get('identity'), dict):
        containers.append(request['identity'])
    return containers


def _check_evidence_session_identity(record: dict, inputs: dict) -> None:
    """Validate private full identities independently of the public field allowlist.

Explicit identity objects must satisfy the existing complete schema/role contract.
Flattened receipt fields are only checked for conflicts; filling absent fields for
that comparison does not establish complete evidence or live runtime readiness.
Receipt envelope schema_version is not the nested session identity schema.
"""
    session = inputs.get('session')
    if session is None:
        return
    contract = session['contract']
    containers = [record]
    for field in ('result', 'request'):
        if isinstance(record.get(field), dict):
            containers.append(record[field])
    for container in containers:
        if 'identity' in container:
            if verification._identity_errors(contract, {'identity': container['identity']}):
                raise IntegrityError('Evidence session identity is incomplete or inconsistent')
        # Retain every supplied field privately so the existing validator also
        # rejects foreign-role authority, including forbidden fields set to null.
        actual = dict(contract)
        actual.update({key: value for key, value in container.items() if key != 'schema_version'})
        if verification._identity_errors(contract, {'identity': actual}):
            raise IntegrityError('Evidence fields conflict with the supplied session identity')


def _project_evidence_record(record: dict, expected: dict) -> dict:
    projected = {}
    containers = _receipt_containers(record)
    observed = {}
    for container in containers:
        for field in _IDENTITY_FIELDS:
            if field not in container or container[field] is None:
                continue
            value = container[field]
            if field in observed and observed[field] != value:
                raise IntegrityError('Evidence contains contradictory identities')
            observed[field] = value
            if field in expected and expected[field] != value:
                raise IntegrityError('Evidence identity differs from the supplied index/session')
            if field in _HASH_FIELDS:
                if _matching(value, r'[a-f0-9]{64}') is None:
                    raise IntegrityError('Evidence contains an invalid identity hash')
                projected[field] = value
            elif field == 'source_revision':
                if _matching(value, r'[a-f0-9]{40}|[a-f0-9]{64}') is None:
                    raise IntegrityError('Evidence contains an invalid source revision')
                projected[field] = value
            elif field == 'run_id' and _matching(value, _UUID_PATTERN) is not None:
                projected[field] = value
        for field in ('status', 'outcome', 'input_status'):
            value = _enum(container.get(field), field)
            if value == 'STALE':
                raise IntegrityError('Evidence is explicitly stale')
            if value is not None:
                if field in projected and projected[field] != value:
                    raise IntegrityError('Evidence contains contradictory completion status')
                projected[field] = value
    # Execution receipts name the captured dirty hash as source_generation and
    # repeat it in their request. Check these private aliases on every evidence
    # entry path, without adding source generations to the public projection.
    source_generations = [record[field] for field in ('source_generation', 'source_generation_after')
                          if field in record]
    request = record.get('request')
    if isinstance(request, dict) and 'source_generation' in request:
        source_generations.append(request['source_generation'])
    for value in source_generations:
        valid_hash(value)
        if 'dirty_hash' in observed and observed['dirty_hash'] != value:
            raise IntegrityError('Evidence contains contradictory identities')
        if 'dirty_hash' in expected and expected['dirty_hash'] != value:
            raise IntegrityError('Evidence identity differs from the supplied index/session')
        observed['dirty_hash'] = value
    if ('profile_id' in observed and 'profile_hash' in observed
            and observed['profile_id'] != observed['profile_hash']):
        raise IntegrityError('Evidence contains contradictory profile identities')
    for field in ('kind', 'record_type'):
        value = _enum(record.get(field), field)
        if value is not None:
            projected[field] = value
    if isinstance(request, dict):
        kind = request.get('kind')
        if isinstance(kind, str) and kind in ('compile', 'unit', 'export', 'gametest', 'server', 'client'):
            if 'kind' in projected and projected['kind'] != kind:
                raise IntegrityError('Evidence contains contradictory operation kinds')
            projected['kind'] = kind
    if record.get('kind') == 'mapping-table':
        classification = 'mapping'
        if 'text_hash' in record:
            if _matching(record['text_hash'], r'[a-f0-9]{64}') is None:
                raise IntegrityError('Mapping record contains an invalid text hash')
            projected['text_hash'] = record['text_hash']
        if record.get('format') in ('tiny', 'tsrg', 'proguard'):
            projected['format'] = record['format']
        namespaces = ('mojmap', 'srg', 'obf', 'intermediary', 'yarn', 'official', 'named', 'unknown')
        for field in ('source_namespace', 'target_namespace'):
            if isinstance(record.get(field), str) and record[field] in namespaces:
                projected[field] = record[field]
        values = record.get('namespaces')
        if (isinstance(values, list) and len(values) <= 8
                and all(isinstance(value, str) and value in namespaces for value in values)):
            projected['namespaces'] = list(values)
    elif record.get('format') == 'kneekura.failure-history.v1':
        classification = 'history'
        projected['format'] = 'kneekura.failure-history.v1'
    elif projected:
        classification = 'receipt'
    else:
        return {'classification': 'opaque'}
    if type(record.get('schema_version')) is int and record['schema_version'] in (1, 2, 3):
        projected['schema_version'] = record['schema_version']
    return {'classification': classification, **projected}


def summarize_evidence(store: Store, inputs: dict) -> dict:
    """Return bounded, hash-verified public pointers, never persisted evidence bodies.

Classification recognizes supplied record types; it does not attest their runtime
claims or authorize replay. UNKNOWN completion survives nested receipt projection.
"""
    pointers = inputs.get('evidence', [])
    if not isinstance(pointers, list) or len(pointers) > 32:
        raise ContractError('At most 32 ordered evidence pointers are allowed')
    expected = _expected_evidence_identity(inputs)
    items = []
    seen = set()
    for pointer in pointers:
        if not isinstance(pointer, dict):
            raise ContractError('Evidence pointers must be objects')
        identifier = valid_hash(pointer.get('content_hash'))
        if identifier in seen:
            raise ContractError('Evidence hashes must be distinct')
        seen.add(identifier)
        payload = _verified_evidence_bytes(store, pointer)
        row = {'content_hash': identifier, 'size': pointer['size'], 'classification': 'opaque'}
        if payload is not None:
            try:
                record = json.loads(payload, object_pairs_hook=_unique_json_object,
                                    parse_constant=_reject_nonfinite_json)
            except IntegrityError:
                raise
            except (ValueError, UnicodeError, RecursionError):
                record = None
            if isinstance(record, dict):
                _check_evidence_session_identity(record, inputs)
                row.update(_project_evidence_record(record, expected))
                _check_private_aliases(row, inputs, record)
        _check_private_aliases(row, inputs)
        items.append(row)
    return {'index': _index_evidence_summary(inputs), 'items': items}


def summarize_lineage(inputs: dict, evidence: dict) -> list[dict]:
    """Reuse a short ordered set of existing identities; mint and persist nothing."""
    target = summarize_target(inputs)
    lineage = []
    if target['profile_id'] is not None:
        lineage.append({'kind': 'profile', 'profile_id': target['profile_id'],
                        'profile_hash': target['profile_hash']})
    if target['index_snapshot_id'] is not None:
        lineage.append({'kind': 'index', 'index_snapshot_id': target['index_snapshot_id']})
    session = inputs.get('session')
    if session is not None:
        contract = session['contract']
        row = {'kind': 'session'}
        for field in ('profile_id', 'index_snapshot_id', 'build_artifact_hash'):
            value = _matching(contract.get(field), r'[a-f0-9]{64}')
            if value is not None:
                row[field] = value
        run_id = _matching(contract.get('run_id'), _UUID_PATTERN)
        if run_id is not None:
            row['run_id'] = run_id
        lineage.append(row)
    items = evidence.get('items', [])
    if not isinstance(items, list) or len(items) > 32:
        raise ContractError('At most 32 evidence lineage references are allowed')
    for item in items:
        identifier = valid_hash(item.get('content_hash'))
        classification = item.get('classification')
        if classification not in ('mapping', 'history', 'receipt', 'opaque'):
            raise ContractError('Unknown evidence lineage classification')
        lineage.append({'kind': 'evidence', 'content_hash': identifier, 'classification': classification})
    _check_private_aliases(lineage, inputs)
    return lineage


_PRIVATE_FIELDS = ('token', 'password', 'secret', 'endpoint_path', 'report_path', 'directory',
                   'world', 'build_artifact', 'workspace', 'display', 'run_directory')


def _check_private_aliases(public, inputs: dict, record: dict | None = None) -> None:
    """Even syntactically valid IDs must not reproduce known private selectors/secrets."""
    containers = [inputs]
    for field in ('session', 'run_registry', 'input_registry', 'blockbench_registry'):
        if isinstance(inputs.get(field), dict):
            containers.append(inputs[field])
    if record is not None:
        containers.extend(_receipt_containers(record))
        if isinstance(record.get('request'), dict):
            containers.append(record['request'])
    private = {container[field] for container in containers for field in _PRIVATE_FIELDS
               if isinstance(container.get(field), str) and container[field]}
    pending = [public]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, str) and value in private:
            raise IntegrityError('Public identity aliases a private input value')


def _unique_json_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise IntegrityError('Evidence JSON contains duplicate object keys')
        result[key] = value
    return result


def _reject_nonfinite_json(value: str):
    raise IntegrityError('Evidence JSON must be finite')


def _registry_evidence(store: Store, inputs: dict) -> list[dict]:
    """Do not let prerequisite fallback hide an explicit receipt's state/errors."""
    from . import task_routing

    registry = inputs.get('run_registry') or {}
    identifier = registry.get('build_receipt_hash')
    if identifier is not None:
        # Check present compile identities independently of world/provider/run
        # prerequisites, including when this receipt was selected explicitly.
        try:
            task_routing._compile_receipt(store, inputs, registry, require_known_completion=False)
        except (task_routing._Unavailable, json.JSONDecodeError, UnicodeError, RecursionError):
            # Opaque/non-receipt evidence proves no compile success. Existing
            # integrity/hash/identity errors are deliberately not swallowed.
            pass
    if identifier is not None and identifier not in {p['content_hash'] for p in inputs['evidence']}:
        # The capability evaluator deliberately describes unavailable local
        # prerequisites as BLOCKED. The complete facade must first propagate
        # integrity failures in caller-supplied CAS authority, using the same
        # hash, stale-state and full identity validators as explicit evidence.
        return summarize_evidence(store, dict(inputs, evidence=_evidence_metadata(store, (identifier,))))['items']
    return []


def _task_status(request: dict, inputs: dict, capabilities: list[dict], actions: list[dict]) -> str:
    from .task_routing import _needs_reconciliation

    if not actions or inputs['index'] is None or _needs_reconciliation(capabilities):
        return 'PARTIAL'
    required = set({'create_asset': ('blockbench_asset',), 'verify_server': ('gametest',),
                    'verify_client': ('client_observation',)}.get(request['intent'], ()))
    # Optional, absent capabilities do not make a usable research context
    # partial. Explicitly selected authorities do retain their unmet needs.
    for field, identifiers in (
            ('run_registry', ('forge_build', 'gametest')),
            ('input_registry', ('native_input',)),
            ('blockbench_registry', ('blockbench_asset',)),
            ('session', ('server_observation', 'client_observation')),
            ('world', ('gametest',)), ('run_directory', ('gametest',))):
        if inputs[field] is not None:
            required.update(identifiers)
    if inputs['core_configured']:
        required.add('core_context')
    if any(c['id'] in required and c['readiness'] != 'READY' for c in capabilities):
        return 'PARTIAL'
    return 'OK'


def prepare_task_context(store: Store, request: dict, *, index_id: str | None = None,
                         run_registry: dict | None = None, input_registry: dict | None = None,
                         blockbench_registry: dict | None = None, session: dict | None = None,
                         evidence_hashes: tuple[str, ...] = (), world: str | None = None,
                         run_directory: str | None = None, core_configured: bool = False) -> dict:
    """Assemble a bounded, deterministic public view without writing or executing.

    OK means useful local next operations exist with their selected prerequisites;
    it is neither task completion, execution permission nor runtime acceptance.
    Missing/unprobed prerequisites stay PARTIAL. Corrupt or mismatched supplied
    authority raises instead of being hidden by an unrelated READY capability.
    """
    from . import task_routing

    request = validate_task_request(request)
    inputs = load_task_inputs(store, index_id=index_id, run_registry=run_registry,
        input_registry=input_registry, blockbench_registry=blockbench_registry, session=session,
        evidence_hashes=evidence_hashes, world=world, run_directory=run_directory,
        core_configured=core_configured)
    target = summarize_target(inputs)
    evidence = summarize_evidence(store, inputs)
    # The caller's bounded public evidence/lineage remain unchanged. A separate
    # explicitly registered receipt can still quarantine its affected capabilities
    # even when missing authorization or an index prevents prerequisite evaluation.
    selected_evidence = dict(evidence, items=[*evidence['items'], *_registry_evidence(store, inputs)])
    capabilities = task_routing.evaluate_capabilities(store, request, inputs, selected_evidence)
    for c in capabilities:
        # UNKNOWN completion can replace the main reason, but the evaluator
        # retains these typed integrity prerequisites. Preserve their errors.
        if (c['reason_code'] == 'INDEX_STALE'
                or (c['reason_code'] == 'SESSION_IDENTITY_INVALID' or 'registered_client_identity' in c['missing'])
                and (c['id'] != 'native_input' or (inputs['input_registry'] or {}).get('enabled') is True)
                or any(label in c['missing'] for label in ('current_index', 'matching_private_session',
                                                          'matching_run_identity', 'successful_same_source_compile'))):
            raise IntegrityError('Supplied task authority is stale or mismatched')
    actions = task_routing.derive_next_actions(request, inputs, capabilities)
    result = {'schema_version': 1, 'kind': 'minecraft_task_context',
        'status': _task_status(request, inputs, capabilities, actions),
        'task': {'request_hash': key_for(request), 'intent': request['intent']},
        'target': target, 'evidence': evidence, 'capabilities': capabilities,
        'next_actions': actions, 'lineage': summarize_lineage(inputs, evidence)}
    _check_private_aliases(result, inputs)
    if len(capabilities) > 12 or len(actions) > 5 or len(canonical(result)) > 96 * 1024:
        raise ContractError('TaskContext exceeds the public output budget')
    return result