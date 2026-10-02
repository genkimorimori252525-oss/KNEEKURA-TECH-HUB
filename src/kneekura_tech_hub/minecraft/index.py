"""Snapshot-bound search, source/bytecode readers and exact JVM member lookup."""
from __future__ import annotations

import base64
import json
import uuid
from typing import Any

from . import bytecode
from .storage import ArtifactUnavailable, ContractError, IntegrityError, Store, canonical, key_for, SCOPES, NAMESPACES, TRACKS


def _positive(value: int, maximum: int = 10000) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ContractError(f'Expected integer in 1..{maximum}')
    return value


def prepare_index(profile: dict, store: Store, *, javap: str | None = None,
                  max_classes: int = 500) -> dict:
    """Explicit preparation. Passive queries below never invoke this provider."""
    _positive(max_classes, 50000)
    p = json.loads(canonical(profile))
    claimed = p.pop('profile_hash', None); pid = p.pop('profile_id', None)
    if not claimed or claimed != pid or key_for(p) != claimed:
        raise IntegrityError('Profile identity mismatch')
    p['profile_hash'] = claimed; p['profile_id'] = pid
    identity = bytecode.provider_identity(javap) if javap else None
    prepared = {}; errors = []; hits = 0; misses = 0; done = 0
    for d in p['documents']:
        if d['media'] != 'class': continue
        if identity is None or done >= max_classes:
            errors.append({'document_id': d['document_id'], 'reason': 'Bytecode not prepared / class budget'})
            continue
        done += 1
        try:
            details, cached = bytecode.prepare_class(store, d['content_hash'], identity)
            hits += int(cached); misses += int(not cached)
            prepared[d['document_id']] = details
        except (OSError, ContractError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append({'document_id': d['document_id'], 'reason': f'{type(exc).__name__}: {exc}'})
    snapshot = {'schema_version': 1, 'profile': p, 'bytecode': prepared,
                'bytecode_unresolved': errors, 'provider': identity}
    identifier = store.put_json(snapshot)
    return {'index_snapshot_id': identifier, 'profile_id': pid,
            'status': 'PARTIAL' if errors or not p['coverage']['complete'] else 'OK',
            'cache': {'hits': hits, 'misses': misses}, 'bytecode_unresolved': errors}


def _load(store: Store, identifier: str) -> dict:
    result = store.json(identifier)
    if result.get('schema_version') != 1 or 'profile' not in result or 'bytecode' not in result:
        raise IntegrityError('Artifact is not an index snapshot')
    return result


def _coverage(index: dict) -> dict:
    return json.loads(canonical(index['profile']['coverage']))


def _envelope(index: dict, identifier: str, status: str, results: list, *,
              coverage: dict | None = None, warnings: list | None = None,
              cursor: str | None = None, evidence: list | None = None) -> dict:
    p = index['profile']
    return {'schema_version': 1, 'request_id': str(uuid.uuid4()), 'profile_id': p['profile_id'],
            'profile_hash': p['profile_hash'], 'index_snapshot_id': identifier,
            'status': status, 'results': results, 'evidence': evidence or [],
            'coverage': coverage if coverage is not None else _coverage(index),
            'warnings': p['warnings'] + (warnings or []), 'next_cursor': cursor,
            'run_id': None, 'null_reasons': {'run_id': 'Static analysis, not a game run'}}


def _cursor(identifier: str, request: dict, offset: int) -> str:
    return base64.urlsafe_b64encode(canonical({'snapshot': identifier, 'query': key_for(request),
                                               'offset': offset})).decode('ascii')


def _offset(value: str | None, identifier: str, request: dict) -> int | None:
    if value is None: return 0
    try:
        if not isinstance(value, str) or len(value) > 4096: return None
        decoded = json.loads(base64.b64decode(value, altchars=b'-_', validate=True))
        if decoded['snapshot'] != identifier or decoded['query'] != key_for(request): return None
        offset = decoded['offset']
        return offset if type(offset) is int and offset >= 0 else None
    except (ValueError, KeyError, TypeError):
        return None


def _validate_filters(scope, namespace, track):
    if scope is not None and scope not in SCOPES:
        raise ContractError('Unknown classpath scope')
    if namespace is not None and namespace not in NAMESPACES:
        raise ContractError('Unknown namespace; use an explicitly resolved namespace')
    if track is not None and track not in TRACKS | {'all'}:
        raise ContractError('Unknown research track')


def _selected(doc: dict, profile: dict, scope: str | None, namespace: str | None,
              track: str | None) -> bool:
    if scope is None and doc['scope'] == 'buildscript': return False
    if scope is not None and doc['scope'] != scope: return False
    if namespace is not None and doc['namespace'] != namespace: return False
    effective_track = track or profile['manifest']['track']
    return effective_track == 'all' or doc['track'] == effective_track


def locator(identifier: str, doc: dict, content_hash: str | None = None) -> dict:
    return {'index_snapshot_id': identifier, 'artifact_hash': doc['artifact_hash'],
            'content_hash': content_hash or doc['content_hash'], 'document_id': doc['document_id'],
            'path': doc['path'], 'root_id': doc['root_id'], 'namespace': doc['namespace'],
            'stage': doc['stage'], 'availability': 'AVAILABLE', 'maturity': 'RESEARCH_ONLY'}


def search(store: Store, identifier: str, query: str, *, limit: int = 20,
           cursor: str | None = None, scope: str | None = None,
           namespace: str | None = None, track: str | None = None) -> dict:
    """Literal text/path search. Its absence result never claims full semantic absence."""
    _positive(limit)
    _validate_filters(scope, namespace, track)
    if not isinstance(query, str) or not query or len(query) > 4096:
        raise ContractError('A nonempty literal query of at most 4096 characters is required')
    index = _load(store, identifier)
    request = {'operation': 'search', 'query': query, 'scope': scope, 'namespace': namespace, 'track': track}
    offset = _offset(cursor, identifier, request)
    if offset is None: return _envelope(index, identifier, 'STALE', [])
    matches = []; unavailable = []; needle = query.casefold()
    for doc in index['profile']['documents']:
        if not _selected(doc, index['profile'], scope, namespace, track): continue
        text = ''
        if doc['media'] == 'text':
            try: text = store.read(doc['content_hash']).decode('utf-8')
            except (OSError, IntegrityError, UnicodeError):
                unavailable.append(doc['document_id']); continue
        where = text.casefold().find(needle)
        if where >= 0 or needle in doc['path'].casefold():
            # Use a presentation snippet only; the locator always resolves the original bytes.
            hit = dict(doc, snippet=text[max(0, where - 80): max(0, where) + 160],
                       applicability='RESEARCH_NOT_RUNTIME_EVIDENCE')
            matches.append(hit)
    coverage = _coverage(index)
    coverage.update(search_scope='captured_text_and_paths', matching_documents=len(matches),
                    unavailable_documents=unavailable, excluded_buildscript=scope is None,
                    track_filter=track or index['profile']['manifest']['track'])
    if offset > len(matches): return _envelope(index, identifier, 'STALE', [], coverage=coverage)
    page = matches[offset:offset + limit]
    # Enforce a bounded page; excess results remain addressable by cursor.
    while len(page) > 1 and len(canonical(page)) > 48 * 1024: page.pop()
    end = offset + len(page); more = end < len(matches)
    next_cursor = _cursor(identifier, request, end) if more else None
    partial = more or not coverage['complete'] or bool(unavailable)
    status = 'PARTIAL' if partial else ('OK' if page else 'NOT_FOUND')
    coverage['truncated'] = more
    return _envelope(index, identifier, status, page, coverage=coverage, cursor=next_cursor,
                     evidence=[locator(identifier, doc) for doc in page])


def inspect_document(store: Store, identifier: str, document_id: str, *, view: str = 'source',
                     size: int = 32768, cursor: str | None = None) -> dict:
    _positive(size, 65536)
    if size < 4: raise ContractError('Text page size must be at least four bytes')
    index = _load(store, identifier)
    docs = [d for d in index['profile']['documents'] if d['document_id'] == document_id]
    if not docs: return _envelope(index, identifier, 'NOT_FOUND', [])
    doc = docs[0]
    request = {'operation': 'inspect', 'document': document_id, 'view': view}
    offset = _offset(cursor, identifier, request)
    if offset is None: return _envelope(index, identifier, 'STALE', [])
    content_hash = doc['content_hash']
    if view == 'bytecode':
        details = index['bytecode'].get(document_id)
        if not details:
            return _envelope(index, identifier, 'UNSUPPORTED', [], warnings=['Bytecode was not prepared'])
        content_hash = details['text_hash']
    elif view == 'source' and doc['media'] != 'text':
        return _envelope(index, identifier, 'UNSUPPORTED', [], warnings=['No source representation; use bytes or prepared bytecode'])
    elif view not in ('source', 'bytes'):
        raise ContractError('view must be source, bytecode or bytes')
    evidence = locator(identifier, doc, content_hash)
    input_missing = False
    if view == 'bytecode':
        try:
            store.read(doc['content_hash'])
            evidence['input_availability'] = 'AVAILABLE'
        except (OSError, IntegrityError) as exc:
            input_missing = True
            evidence['input_availability'] = 'HASH_MISMATCH' if isinstance(exc, IntegrityError) else 'ARTIFACT_UNAVAILABLE'
    try: data = store.read(content_hash)
    except ArtifactUnavailable:
        evidence['availability'] = 'ARTIFACT_UNAVAILABLE'
        return _envelope(index, identifier, 'ARTIFACT_UNAVAILABLE', [], evidence=[evidence])
    except IntegrityError:
        evidence['availability'] = 'HASH_MISMATCH'
        return _envelope(index, identifier, 'ERROR', [], evidence=[evidence])
    if offset > len(data): return _envelope(index, identifier, 'STALE', [])
    end = min(len(data), offset + size)
    if view != 'bytes':
        while end < len(data) and data[end] & 0xC0 == 0x80: end -= 1
        try: value = data[offset:end].decode('utf-8')
        except UnicodeError: return _envelope(index, identifier, 'STALE', [])
        payload = {'text': value}
    else: payload = {'base64': base64.b64encode(data[offset:end]).decode('ascii')}
    more = end < len(data)
    evidence.update(byte_start=offset, byte_end=end)
    result = dict(payload, document_id=document_id, total_bytes=len(data), byte_start=offset, byte_end=end)
    return _envelope(index, identifier, 'PARTIAL' if more or input_missing else 'OK', [result],
                     warnings=['Original class bytes unavailable; the pinned disassembly remains readable'] if input_missing else [],
                     cursor=_cursor(identifier, request, end) if more else None, evidence=[evidence])


def find_symbols(store: Store, identifier: str, owner: str, *, member: str | None = None,
                 descriptor: str | None = None, namespace: str | None = None,
                 scope: str | None = None, track: str | None = None,
                 limit: int = 20, cursor: str | None = None) -> dict:
    """Exact internal class/member/descriptor lookup; no display-name remapping guesses."""
    _positive(limit)
    _validate_filters(scope, namespace, track)
    if not isinstance(owner, str) or not owner or len(owner) > 4096:
        raise ContractError('A nonempty internal class name is required')
    index = _load(store, identifier); found = []; unavailable = []
    request = dict(operation='symbols', owner=owner, member=member, descriptor=descriptor,
                   namespace=namespace, scope=scope, track=track)
    offset = _offset(cursor, identifier, request)
    if offset is None: return _envelope(index, identifier, 'STALE', [])
    for doc in index['profile']['documents']:
        if not _selected(doc, index['profile'], scope, namespace, track): continue
        details = index['bytecode'].get(doc['document_id'])
        if not details or details['owner'] != owner: continue
        try:
            store.read(doc['content_hash'])
            store.read(details['text_hash'])
        except (OSError, IntegrityError) as exc:
            unavailable.append({'document_id': doc['document_id'], 'reason': type(exc).__name__})
            continue
        members = details['members'] if member else [dict(owner=owner, name=owner, descriptor=None,
                                                         kind='class', superclass=details['superclass'])]
        for symbol in members:
            if member is not None and symbol['name'] != member: continue
            if descriptor is not None and symbol['descriptor'] != descriptor: continue
            result = {**doc, **symbol, 'bytecode_hash': details['text_hash']}
            result['symbol_id'] = key_for({'profile': index['profile']['profile_id'],
                                           'document': doc['document_id'], 'symbol': symbol})
            # This is a preview, not a lossy replacement for the full disassembly.
            references = symbol.get('references', [])
            result.update(references=references[:100], reference_count=len(references),
                          references_truncated=len(references) > 100,
                          full_reference_view={'document_id': doc['document_id'], 'view': 'bytecode'})
            found.append(result)
    coverage = _coverage(index)
    coverage.update(search_scope='prepared_bytecode_symbols', unresolved_bytecode=index['bytecode_unresolved'],
                    matching_symbols=len(found), unavailable_documents=unavailable)
    coverage['complete'] = coverage['complete'] and not index['bytecode_unresolved'] and not unavailable
    if offset > len(found): return _envelope(index, identifier, 'STALE', [], coverage=coverage)
    page = found[offset:offset + limit]
    while len(page) > 1 and len(canonical(page)) > 48 * 1024: page.pop()
    end = offset + len(page); more = end < len(found)
    coverage['truncated'] = more
    partial = not coverage['complete'] or more
    status = 'AMBIGUOUS' if len(found) > 1 else ('PARTIAL' if partial else ('OK' if found else 'NOT_FOUND'))
    return _envelope(index, identifier, status, page, coverage=coverage,
                     warnings=bytecode.LIMITATIONS, cursor=_cursor(identifier, request, end) if more else None,
                     evidence=[dict(locator(identifier, r, r['bytecode_hash']), owner=r['owner'],
                                    member=r['name'], descriptor=r['descriptor']) for r in page])
