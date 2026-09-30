"""JSON CLI for the headless Minecraft adapter.

Use ``python -m kneekura_tech_hub.minecraft --help``. Reads never prepare inputs,
resolve Gradle dependencies, start Minecraft, or follow instructions in data.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from . import index, verification
from .storage import ArtifactUnavailable, ContractError, Store, capture_profile


def parse_json(raw: str | bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ContractError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ContractError('Non-finite JSON number: ' + value)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    if not isinstance(value, dict): raise ContractError('JSON object required')
    return value


def read_json(path: str) -> dict:
    with Path(path).open('rb') as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024: raise ContractError('JSON input exceeds 16 MiB')
    return parse_json(raw)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--store', default='.kneekura-cache/minecraft')
    commands = p.add_subparsers(dest='command', required=True)
    profile = commands.add_parser('profile').add_subparsers(dest='action', required=True)
    prepare = profile.add_parser('prepare')
    prepare.add_argument('--manifest', required=True)
    prepare.add_argument('--javap', help='Explicitly prepare disassembly with this installed JDK tool')
    prepare.add_argument('--max-classes', type=int, default=500)
    profile.add_parser('inspect').add_argument('--index', required=True)
    from .connected_cli import add_commands
    add_commands(commands, profile)
    for name in ('search', 'context'):
        q = commands.add_parser(name)
        q.add_argument('--index', required=True); q.add_argument('--query', required=True)
        q.add_argument('--limit', type=int, default=20); q.add_argument('--cursor')
        q.add_argument('--scope'); q.add_argument('--namespace'); q.add_argument('--track')
        if name == 'context':
            q.add_argument('--entity'); q.add_argument('--context-json', default='{}')
    inspect = commands.add_parser('inspect')
    inspect.add_argument('--index', required=True)
    target = inspect.add_mutually_exclusive_group(required=True)
    target.add_argument('--document'); target.add_argument('--owner')
    inspect.add_argument('--member'); inspect.add_argument('--descriptor'); inspect.add_argument('--namespace')
    inspect.add_argument('--view', choices=('source', 'bytecode', 'bytes'), default='source')
    inspect.add_argument('--size', type=int, default=32768); inspect.add_argument('--cursor')
    inspect.add_argument('--limit', type=int, default=20)
    inspect.add_argument('--scope'); inspect.add_argument('--track')
    validate = commands.add_parser('validate').add_subparsers(dest='action', required=True)
    plan = validate.add_parser('plan'); plan.add_argument('--registry', required=True)
    plan.add_argument('--kind', choices=('compile', 'unit', 'gametest', 'client', 'server'), required=True)
    owned = plan.add_mutually_exclusive_group()
    owned.add_argument('--world'); owned.add_argument('--run-directory')
    run = validate.add_parser('run')
    target = run.add_mutually_exclusive_group(required=True)
    target.add_argument('--plan'); target.add_argument('--registry')
    run.add_argument('--kind', choices=('compile', 'unit', 'gametest', 'client', 'server', 'export'))
    run.add_argument('--request-id'); run.add_argument('--contract')
    owned = run.add_mutually_exclusive_group()
    owned.add_argument('--world'); owned.add_argument('--run-directory')
    operation = validate.add_parser('operation')
    operation.add_argument('--session', required=True)
    operation.add_argument('--command-id', required=True)
    operation.add_argument('--request-id', required=True)
    report = validate.add_parser('report')
    report.add_argument('--contract', required=True); report.add_argument('--report', required=True)
    observe = commands.add_parser('observe')
    observe.add_argument('--contract'); observe.add_argument('--report')
    observe.add_argument('--session')
    observe.add_argument('--operation', choices=('observe', 'logs', 'client', 'operation'), default='observe')
    observe.add_argument('--query-json', default='{}')
    return p


def dispatch(args: argparse.Namespace) -> dict:
    store = Store(args.store)
    if args.command == 'profile':
        if args.action == 'prepare':
            profile = capture_profile(read_json(args.manifest), Path(args.manifest).resolve().parent, store)
            result = index.prepare_index(profile, store, javap=args.javap, max_classes=args.max_classes)
            return {'schema_version': 1, 'status': result['status'], 'profile_id': profile['profile_id'],
                    'profile_hash': profile['profile_hash'], 'index_snapshot_id': result['index_snapshot_id'],
                    'results': [result], 'coverage': profile['coverage'], 'warnings': profile['warnings']}
        if args.action not in ('inspect', 'prepare'):
            from .connected_cli import dispatch as connected
            return connected(args, store, read_json, parse_json)
        snapshot = index._load(store, args.index)
        return index._envelope(snapshot, args.index, 'OK', [snapshot['profile']])
    if args.command in ('search', 'context'):
        if args.command == 'context' and args.entity:
            from .core_bridge import context
            return context(store, args.index, args.query, entity_id=args.entity, extra_context=parse_json(args.context_json),
                           limit=args.limit, cursor=args.cursor, scope=args.scope, namespace=args.namespace, track=args.track)
        result = index.search(store, args.index, args.query, limit=args.limit, cursor=args.cursor,
                              scope=args.scope, namespace=args.namespace, track=args.track)
        if args.command == 'context':
            result.update(context_kind='RESEARCH_ONLY', canonical_writes=0,
                          note='Literal source/research retrieval; no inferred compatibility or canonical promotion')
        return result
    if args.command == 'inspect':
        if args.owner:
            return index.find_symbols(store, args.index, args.owner, member=args.member,
                                      descriptor=args.descriptor, namespace=args.namespace, scope=args.scope,
                                      track=args.track, limit=args.limit, cursor=args.cursor)
        return index.inspect_document(store, args.index, args.document, view=args.view,
                                      size=args.size, cursor=args.cursor)
    if args.command == 'validate':
        if args.action == 'operation':
            from .runtime import execute_registered_command
            return execute_registered_command(store, args.session, command_id=args.command_id, request_id=args.request_id)
        if args.action == 'plan':
            return verification.validation_plan(args.kind, read_json(args.registry), world=args.world, run_directory=args.run_directory)
        if args.action == 'run':
            if args.plan: return verification.delegate_run(read_json(args.plan))
            if not args.kind or not args.request_id: raise ContractError('Registered run requires --kind and --request-id')
            from .execution import execute
            return execute(store, read_json(args.registry), kind=args.kind, request_id=args.request_id,
                           world=args.world, run_directory=args.run_directory, contract=read_json(args.contract) if args.contract else None)
        return verification.evaluate_scenario_tests(read_json(args.contract), read_json(args.report))
    if args.command == 'observe':
        if args.session:
            if args.contract or args.report: raise ContractError('Use a session or imported report, not both')
            from .runtime import observe_live
            return observe_live(store, args.session, operation=args.operation, query=parse_json(args.query_json))
        if not args.contract or not args.report: raise ContractError('Imported observation requires --contract and --report')
        return verification.evaluate_observation(read_json(args.contract), read_json(args.report))
    from .connected_cli import dispatch as connected
    return connected(args, store, read_json, parse_json)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = dispatch(args)
    except ArtifactUnavailable as exc:
        result = {'schema_version': 1, 'status': 'ARTIFACT_UNAVAILABLE', 'results': [], 'warnings': [str(exc)]}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {'schema_version': 1, 'status': 'ERROR', 'results': [],
                  'warnings': [f'{type(exc).__name__}: {exc}']}
    result.setdefault('schema_version', 1); result.setdefault('status', 'OK')
    result.setdefault('results', []); result.setdefault('warnings', [])
    result.setdefault('request_id', str(uuid.uuid4()))
    result.setdefault('evidence', []); result.setdefault('coverage', {}); result.setdefault('next_cursor', None)
    for field in ('profile_id', 'profile_hash', 'index_snapshot_id'):
        if field not in result:
            result[field] = None
            result.setdefault('null_reasons', {})[field] = 'Not available/applicable to this operation'
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 2 if (result.get('status') in {'ERROR', 'STALE', 'ARTIFACT_UNAVAILABLE', 'UNSUPPORTED'}
                 or result.get('outcome') in {'BLOCKED', 'FAIL', 'UNKNOWN'}) else 0


if __name__ == '__main__':
    sys.exit(main())
