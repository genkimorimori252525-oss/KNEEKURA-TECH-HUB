"""Snapshot-backed Failure/Repair History, a facet of MOD analysis.

An analyst reads upstream history before making records. This module neither
scrapes repositories nor infers causes from closed Issues or merged PRs. Imported
experiment records remain research evidence, never live execution attestations.
"""
from __future__ import annotations

import json
import re

from . import index
from .storage import ContractError, Store, canonical

FORMAT = 'kneekura.failure-history.v1'
FIELDS = ('symptom', 'trigger_conditions', 'root_cause', 'repair', 'lesson')
BASES = {'DIRECT_OBSERVATION', 'AUTHOR_CLAIM', 'INFERENCE', 'UNKNOWN'}
ROLES = {'issue', 'pull_request', 'commit', 'diff', 'before_code', 'after_code',
         'log', 'experiment', 'release_note', 'discussion', 'search_inventory'}
STATES = {'NOT_RUN', 'REPORTED', 'RECORDED_EXPERIMENT'}


def require(condition, message):
    if not condition:
        raise ContractError(message)


def _revision(value, *, optional=False):
    require(optional and value is None or isinstance(value, str) and
            re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', value), 'Exact commit revision required')


def _strings(value):
    return isinstance(value, list) and all(isinstance(x, str) and x for x in value)


def _assertion(value, evidence_ids):
    require(isinstance(value, dict) and value.get('basis') in BASES, 'Explicit assertion basis required')
    refs = value.get('evidence_ids')
    require(_strings(refs) and set(refs) <= evidence_ids, 'Assertion refers to unknown evidence')
    if value['basis'] == 'UNKNOWN':
        require(value.get('text') is None and isinstance(value.get('reason'), str) and
                bool(value['reason'].strip()), 'Unknown assertion needs a reason and null text')
    else:
        require(isinstance(value.get('text'), str) and bool(value['text'].strip()) and refs,
                'Positive/history-inference assertions need text and evidence')


def _verification(value, evidence):
    require(isinstance(value, dict) and value.get('state') in STATES,
            'Imported history cannot assert a locally verified runtime outcome')
    refs = value.get('evidence_ids')
    require(_strings(refs) and set(refs) <= set(evidence), 'Verification references unknown evidence')
    if value['state'] != 'NOT_RUN':
        require(bool(refs), 'Reported verification needs its original evidence')
    if value['state'] == 'RECORDED_EXPERIMENT':
        require(any(evidence[r]['role'] == 'experiment' for r in refs),
                'Recorded experiment requires experiment evidence, not an Issue closure')


def _anchors(store, entries, snapshots):
    require(isinstance(entries, list) and len(entries) <= 256, 'Bounded evidence array required')
    out = {}; missing = []; pins = []
    for supplied in entries:
        require(isinstance(supplied, dict) and isinstance(supplied.get('id'), str) and
                bool(supplied['id']) and supplied['id'] not in out, 'Distinct evidence IDs required')
        require(supplied.get('role') in ROLES, 'Explicit history evidence role required')
        identifier = supplied.get('index_snapshot_id')
        if identifier not in snapshots:
            snapshots[identifier] = index._load(store, identifier)
        docs = snapshots[identifier]['profile']['documents']
        matches = [d for d in docs if d['document_id'] == supplied.get('document_id')]
        require(len(matches) == 1, 'History evidence document does not belong to its snapshot')
        loc = index.locator(identifier, matches[0])
        out[supplied['id']] = dict(supplied, locator=loc)
        try:
            store.read(loc['content_hash']); pins.extend((identifier, loc['content_hash']))
        except (OSError, ContractError):
            missing.append(supplied['id'])
    return out, missing, pins


def capture_history(store: Store, record: dict) -> dict:
    """Freeze an explicit analysis record and exact captured evidence. No Core writes."""
    raw = canonical(record)
    require(len(raw) <= 16 * 1024 * 1024, 'History record exceeds 16 MiB')
    record = json.loads(raw)
    require(isinstance(record, dict) and record.get('format') == FORMAT, 'Unsupported history format')
    require(isinstance(record.get('repository'), str) and bool(record['repository']), 'Repository origin required')
    scope = record.get('scope'); coverage = record.get('coverage')
    require(isinstance(scope, dict) and scope.get('track') in ('ANCHOR','FRONTIER','COMPARATIVE'), 'Explicit history track required')
    _revision(scope.get('head_revision'))
    require(isinstance(scope.get('history_window'), str) and bool(scope['history_window']) and
            _strings(scope.get('queries')), 'Explicit bounded history window and queries required')
    require(isinstance(coverage, dict) and coverage.get('status') in
            ('NOT_ANALYZED','PARTIAL','REVIEWED_SCOPE'), 'History coverage status required')
    for field in ('inspected_evidence_ids','deferred','unavailable'):
        require(_strings(coverage.get(field)), 'Coverage arrays must preserve inspected/deferred/unavailable work')
    if coverage['status'] == 'REVIEWED_SCOPE':
        require(bool(coverage['inspected_evidence_ids']) and not coverage['deferred'] and not coverage['unavailable'],
                'Unreviewed/deferred scope cannot be labelled reviewed')
    cases = record.get('cases')
    require(isinstance(cases, list) and len(cases) <= 1000, 'Bounded cases array required')
    snapshots = {}; ids = set(); pins = []
    scope_refs, missing_scope, scope_pins = _anchors(store, record.get('scope_evidence', []), snapshots)
    pins.extend(scope_pins); inspected = set(scope_refs); rows = []
    for case in cases:
        require(isinstance(case, dict) and isinstance(case.get('case_id'), str) and
                bool(case['case_id']) and case['case_id'] not in ids, 'Distinct case IDs required')
        ids.add(case['case_id'])
        require(case.get('origin') in ('UPSTREAM','OWN_DEVELOPMENT'), 'History origin required')
        require(case.get('track') == scope['track'], 'Do not merge ANCHOR/FRONTIER histories')
        require(isinstance(case.get('environment'), dict) and bool(case['environment']), 'Explicit environment required')
        require(_strings(case.get('affected_symbols')), 'Affected symbols array required')
        for field in ('before_revision','after_revision'):
            require(field in case, 'Explicit before/after revision or null required')
            _revision(case[field], optional=True)
        evidence, missing, case_pins = _anchors(store, case.get('evidence'), snapshots)
        pins.extend(case_pins); inspected.update(evidence)
        for field in FIELDS:
            _assertion(case.get(field), set(evidence))
        chain = case.get('causal_chain')
        require(isinstance(chain, list) and len(chain) <= 128, 'Bounded causal chain required')
        for edge in chain:
            _assertion(edge, set(evidence))
        for field in ('reproduction','fix_verification'):
            _verification(case.get(field), evidence)
        rows.append(dict(case, evidence=list(evidence.values()), unavailable_evidence_ids=missing))
    require(set(coverage['inspected_evidence_ids']) <= inspected,
            'Inspected coverage refers to uncaptured evidence; use scope_evidence for search inventories')
    saved = {'format':FORMAT, 'record':record, 'cases':rows,
             'scope_evidence':list(scope_refs.values()), 'unavailable_scope_evidence_ids':missing_scope,
             'canonical_writes':0, 'runtime_attestation':False}
    h = store.put_json(saved)
    for pin in set(pins + [h]):
        store.pin(pin, 'failure-history:' + h)
    partial = coverage['status'] != 'REVIEWED_SCOPE' or missing_scope or any(r['unavailable_evidence_ids'] for r in rows)
    return {'status':'PARTIAL' if partial else 'OK', 'history_hash':h, 'cases':len(rows),
            'canonical_writes':0, 'runtime_attestation':False,
            'analysis_scope':scope, 'coverage':coverage}


def query_history(store: Store, history_hash: str, query: str, *, track=None, environment=None,
                  limit=20, cursor=None) -> dict:
    require(isinstance(query, str) and 0 < len(query) <= 4096, 'Bounded nonempty query required')
    require(track is None or track in ('ANCHOR','FRONTIER','COMPARATIVE'), 'Unknown history track')
    require(environment is None or isinstance(environment, dict), 'Exact environment filter must be an object')
    index._positive(limit, 100)
    saved = store.json(history_hash)
    require(isinstance(saved, dict) and saved.get('format') == FORMAT, 'Not a captured history record')
    request = dict(query=query, track=track, environment=environment)
    offset = index._offset(cursor, history_hash, request)
    if offset is None:
        return {'status':'STALE', 'results':[], 'next_cursor':None}
    selected = []
    for case in saved['cases']:
        if track is not None and case['track'] != track:
            continue
        if any(k not in case['environment'] or type(case['environment'][k]) is not type(v)
               or case['environment'][k] != v for k,v in (environment or {}).items()):
            continue
        searchable = {k:v for k,v in case.items() if k != 'evidence'}
        if query.casefold() in canonical(searchable).decode().casefold():
            selected.append(case)
    rows = selected[offset:offset+limit]
    for case in rows:
        case['unavailable_evidence_ids'] = []
        for evidence in case['evidence']:
            try:
                store.read(evidence['locator']['content_hash'])
            except (OSError, ContractError):
                case['unavailable_evidence_ids'].append(evidence['id'])
    missing_scope = []
    for evidence in saved['scope_evidence']:
        try:
            store.read(evidence['locator']['content_hash'])
        except (OSError, ContractError):
            missing_scope.append(evidence['id'])
    end = offset + len(rows)
    return {'status':'PARTIAL' if missing_scope or any(r['unavailable_evidence_ids'] for r in rows) or
            saved['record']['coverage']['status'] != 'REVIEWED_SCOPE' else 'OK',
            'results':rows, 'history_hash':history_hash, 'coverage':saved['record']['coverage'],
            'next_cursor':index._cursor(history_hash, request, end) if end < len(selected) else None,
            'canonical_writes':0, 'runtime_attestation':False,
            'unavailable_scope_evidence_ids':missing_scope,
            'no_match_meaning':'NO_MATCH_IN_RECORDED_SCOPE'}


def main(argv=None):
    import argparse
    from .__main__ import read_json, parse_json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', default='.kneekura-cache/minecraft')
    commands = parser.add_subparsers(dest='command', required=True)
    capture = commands.add_parser('import')
    capture.add_argument('--record', required=True)
    query = commands.add_parser('query')
    query.add_argument('--history', required=True)
    query.add_argument('--query', required=True)
    query.add_argument('--track', choices=('ANCHOR','FRONTIER','COMPARATIVE'))
    query.add_argument('--environment-json', default='{}')
    query.add_argument('--limit', type=int, default=20)
    query.add_argument('--cursor')
    args = parser.parse_args(argv)
    store = Store(args.store)
    try:
        if args.command == 'import':
            result = capture_history(store, read_json(args.record))
        else:
            result = query_history(store, args.history, args.query, track=args.track,
                                   environment=parse_json(args.environment_json),
                                   limit=args.limit, cursor=args.cursor)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {'status':'ERROR', 'results':[], 'reason':str(exc)}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 2 if result['status'] in ('ERROR','STALE') else 0


if __name__ == '__main__':
    raise SystemExit(main())
