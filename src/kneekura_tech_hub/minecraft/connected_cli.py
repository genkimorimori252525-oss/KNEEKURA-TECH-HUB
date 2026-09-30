"""Public routes for the explicit workspace/provider/runtime adapters.

This module only dispatches user-selected operations. Retrieved text cannot
supply an executable or grant execution permission.
"""
from __future__ import annotations

import base64
from pathlib import Path

from . import core_bridge, execution, index, interventions, providers, runtime, task_context, workspace
from .mappings import MappingTable
from .storage import ContractError, Store, capture_profile, valid_hash


def add_commands(commands, profile):
    p = profile.add_parser('discover')
    p.add_argument('--workspace', required=True)
    p.add_argument('--physical-side', choices=('client', 'server'), default='server')
    p = profile.add_parser('import')
    p.add_argument('--resolved', required=True); p.add_argument('--workspace', required=True)
    p.add_argument('--physical-side', choices=('client', 'server'), default='server')
    p.add_argument('--javap'); p.add_argument('--max-classes', type=int, default=500)
    p = profile.add_parser('resolve')
    p.add_argument('--registry', required=True); p.add_argument('--request-id', required=True)
    p.add_argument('--physical-side', choices=('client', 'server'), default='server')
    p.add_argument('--javap'); p.add_argument('--max-classes', type=int, default=500)
    p = profile.add_parser('transform')
    p.add_argument('--index', required=True); p.add_argument('--root', required=True)
    p.add_argument('--operation', choices=('decompile', 'remap'), required=True)
    p.add_argument('--provider', required=True); p.add_argument('--mapping-hash')
    p.add_argument('--from-namespace'); p.add_argument('--to-namespace')

    m = commands.add_parser('mapping').add_subparsers(dest='action', required=True)
    p = m.add_parser('import'); p.add_argument('--path', required=True)
    p.add_argument('--format', choices=('tiny', 'tsrg', 'proguard'), required=True)
    p.add_argument('--source-namespace'); p.add_argument('--target-namespace')
    p = m.add_parser('lookup'); p.add_argument('--mapping', required=True)
    p.add_argument('--from-namespace', required=True); p.add_argument('--to-namespace', required=True)
    p.add_argument('--owner', required=True); p.add_argument('--member'); p.add_argument('--descriptor')
    p.add_argument('--aliases-json', default='{}')

    a = commands.add_parser('artifact').add_subparsers(dest='action', required=True)
    p = a.add_parser('read'); p.add_argument('--hash', required=True)
    p.add_argument('--view', choices=('text', 'bytes'), default='text')
    p.add_argument('--size', type=int, default=32768); p.add_argument('--cursor')

    for name in ('interventions', 'relations'):
        p = commands.add_parser(name); p.add_argument('--index', required=True)
        p.add_argument('--owner', required=name == 'relations')
        if name == 'interventions':
            p.add_argument('--member'); p.add_argument('--descriptor')
        else:
            p.add_argument('--depth', type=int, default=1)
        p.add_argument('--scope'); p.add_argument('--namespace'); p.add_argument('--track')
        p.add_argument('--limit', type=int, default=20); p.add_argument('--cursor')

    k = commands.add_parser('knowledge').add_subparsers(dest='action', required=True)
    p = k.add_parser('stage'); p.add_argument('--index', required=True)
    p.add_argument('--document', required=True, action='append')
    p.add_argument('--summary', required=True); p.add_argument('--actor-id', required=True)
    p.add_argument('--actor-type', choices=('ai', 'tool'), default='ai')
    p.add_argument('--source-licenses', help='JSON file mapping captured root IDs to reviewed Core license metadata')

    w = commands.add_parser('world').add_subparsers(dest='action', required=True)
    p = w.add_parser('prepare'); p.add_argument('--registry', required=True)
    p.add_argument('--template', required=True); p.add_argument('--request-id', required=True)
    p.add_argument('--world-name', default='gametestserver')
    p.add_argument('--layout', choices=('server', 'client'), default='server')
    directory = commands.add_parser('client-directory').add_subparsers(dest='action', required=True)
    p = directory.add_parser('prepare'); p.add_argument('--registry', required=True)
    p.add_argument('--template', required=True); p.add_argument('--request-id', required=True)
    s = commands.add_parser('session').add_subparsers(dest='action', required=True)
    p = s.add_parser('create'); p.add_argument('--registry', required=True)
    p.add_argument('--contract', required=True); p.add_argument('--directory', required=True)
    c = commands.add_parser('contract').add_subparsers(dest='action', required=True)
    p = c.add_parser('prepare'); p.add_argument('--registry', required=True)
    p.add_argument('--index', required=True)
    owned = p.add_mutually_exclusive_group(required=True)
    owned.add_argument('--world'); owned.add_argument('--run-directory')
    p.add_argument('--scenario', required=True); p.add_argument('--output')
    i = commands.add_parser('input').add_subparsers(dest='action', required=True)
    p = i.add_parser('bind'); p.add_argument('--registry', required=True)
    p = i.add_parser('dispatch'); p.add_argument('--registry', required=True)
    p.add_argument('--binding', required=True); p.add_argument('--request', required=True)
    p = commands.add_parser('observe-pair')
    p.add_argument('--server-session', required=True); p.add_argument('--client-session', required=True)
    p.add_argument('--player-uuid', required=True); p.add_argument('--dimension', default='minecraft:overworld')
    p.add_argument('--timeout', type=float, default=10); p.add_argument('--screenshot', action='store_true')
    commands.add_parser('capabilities')
    task = commands.add_parser('task', help='Read-only task readiness and next operations').add_subparsers(
        dest='action', required=True)
    for action in ('prepare', 'capabilities'):
        p = task.add_parser(action, description='Read-only task readiness; does not execute or connect')
        p.add_argument('--request', required=True, metavar='TASK_REQUEST_JSON')
        p.add_argument('--index', metavar='INDEX_SNAPSHOT_ID')
        p.add_argument('--run-registry', metavar='RUN_REGISTRY_JSON')
        p.add_argument('--input-registry', metavar='INPUT_REGISTRY_JSON')
        p.add_argument('--blockbench-registry', metavar='REGISTRY_JSON')
        p.add_argument('--session', metavar='PRIVATE_SESSION_JSON')
        p.add_argument('--evidence', action='append', default=[], metavar='SHA256',
                       help='Captured evidence hash (repeatable, maximum 32)')
        p.add_argument('--world', metavar='OWNED_WORLD_PATH', help='Readiness input only')
        p.add_argument('--run-directory', metavar='OWNED_RUN_DIR', help='Readiness input only')
        p.add_argument('--core-configured', action='store_true',
                       help='Explicit configuration-presence hint; no connection')


def prepare(store, manifest, root, args):
    profile = capture_profile(manifest, Path(root), store)
    result = index.prepare_index(profile, store, javap=args.javap, max_classes=args.max_classes)
    return {'schema_version': 1, 'status': result['status'], 'profile_id': profile['profile_id'],
            'profile_hash': profile['profile_hash'], 'index_snapshot_id': result['index_snapshot_id'],
            'results': [result], 'coverage': profile['coverage'], 'warnings': profile['warnings']}


def _read_task_file(reader, path, label):
    # CLI errors are public JSON. File errors and duplicate-key messages may
    # contain caller-private paths or text; keep existing loaders and hide those details.
    try:
        return reader(path)
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise ContractError(f'Unable to load task {label} input') from None


def dispatch(args, store: Store, read_json, parse_json):
    if args.command == 'task' and args.action in ('prepare', 'capabilities'):
        result = task_context.prepare_task_context(store, _read_task_file(read_json, args.request, 'request'),
            index_id=args.index,
            run_registry=_read_task_file(read_json, args.run_registry, 'run-registry')
                if args.run_registry is not None else None,
            input_registry=_read_task_file(read_json, args.input_registry, 'input-registry')
                if args.input_registry is not None else None,
            blockbench_registry=_read_task_file(read_json, args.blockbench_registry, 'blockbench-registry')
                if args.blockbench_registry is not None else None,
            session=_read_task_file(runtime.load_session, args.session, 'session')
                if args.session is not None else None,
            evidence_hashes=tuple(args.evidence), world=args.world,
            run_directory=args.run_directory, core_configured=args.core_configured)
        if args.action == 'capabilities':
            return {field: result[field] for field in ('schema_version', 'status', 'target', 'capabilities')}
        return result
    if args.command == 'profile':
        if args.action == 'discover':
            manifest = workspace.discover_workspace(args.workspace, physical_side=args.physical_side)
            return {'status': 'PARTIAL', 'manifest': manifest,
                    'note': 'Declared inputs only; no dependency resolution or build was executed'}
        if args.action == 'import':
            manifest = workspace.import_resolved(read_json(args.resolved), args.workspace,
                                                  physical_side=args.physical_side)
            return prepare(store, manifest, args.workspace, args)
        if args.action == 'resolve':
            registry = read_json(args.registry)
            receipt = execution.execute(store, registry, kind='export', request_id=args.request_id)
            if receipt['outcome'] != 'PASS':
                return receipt
            manifest = store.json(receipt['outputs'][0]['manifest_hash'])
            manifest['physical_side'] = args.physical_side
            result = prepare(store, manifest, registry['workspace'], args)
            result['resolution_receipt_hash'] = receipt['receipt_hash']
            return result
        if args.action == 'transform':
            return providers.prepare_transform(store, args.index, args.root, args.operation,
                read_json(args.provider), mapping_hash=args.mapping_hash,
                from_namespace=args.from_namespace, to_namespace=args.to_namespace)
    if args.command == 'mapping':
        if args.action == 'import':
            path = Path(args.path)
            with path.open('rb') as stream:
                raw = stream.read(64 * 1024 * 1024 + 1)
            if len(raw) > 64 * 1024 * 1024: raise ContractError('Mapping exceeds 64 MiB')
            table = MappingTable.parse(raw.decode('utf-8'), args.format,
                source_namespace=args.source_namespace, target_namespace=args.target_namespace)
            text_hash = store.put(raw)
            record = {'schema_version': 1, 'kind': 'mapping-table', 'text_hash': text_hash,
                      'format': args.format, 'source_namespace': args.source_namespace,
                      'target_namespace': args.target_namespace, 'namespaces': table.namespaces}
            h = store.put_json(record)
            for item in (h, text_hash): store.pin(item, 'mapping:' + h)
            return {'status': 'OK', 'mapping_hash': h, 'text_hash': text_hash,
                    'namespaces': table.namespaces, 'classes': len(table.classes)}
        record = store.json(valid_hash(args.mapping))
        if record.get('kind') != 'mapping-table': raise ContractError('Not a captured mapping table')
        table = MappingTable.parse(store.read(record['text_hash']).decode('utf-8'), record['format'],
            source_namespace=record['source_namespace'], target_namespace=record['target_namespace'])
        return table.resolve(args.from_namespace, args.to_namespace, args.owner, args.member,
                             args.descriptor, aliases=parse_json(args.aliases_json))
    if args.command == 'artifact':
        valid_hash(args.hash); index._positive(args.size, 1024 * 1024)
        request = {'operation': 'artifact-read', 'view': args.view}
        offset = index._offset(args.cursor, args.hash, request)
        if offset is None: return {'status': 'STALE', 'results': [], 'warnings': ['Cursor belongs to a different artifact/view']}
        raw = store.read(args.hash)
        value = raw if args.view == 'bytes' else raw.decode('utf-8')
        chunk = value[offset:offset + args.size]
        item = {'offset': offset, 'total': len(value),
                'offset_unit': 'bytes' if args.view == 'bytes' else 'unicode_codepoints',
                'content_hash': args.hash}
        item['base64' if args.view == 'bytes' else 'text'] = base64.b64encode(chunk).decode() if args.view == 'bytes' else chunk
        next_offset = offset + len(chunk)
        return {'status': 'OK', 'results': [item], 'next_cursor': index._cursor(args.hash, request, next_offset) if next_offset < len(value) else None}
    if args.command in ('interventions', 'relations'):
        kw = dict(owner=args.owner, scope=args.scope, namespace=args.namespace,
                  track=args.track, limit=args.limit, cursor=args.cursor)
        if args.command == 'interventions':
            return interventions.inspect_interventions(store, args.index, member=args.member,
                                                        descriptor=args.descriptor, **kw)
        return interventions.relations(store, args.index, depth=args.depth, **kw)
    if args.command == 'knowledge':
        return core_bridge.stage_bundle(store, args.index, args.document, summary=args.summary,
            actor={'actor_type': args.actor_type, 'actor_id': args.actor_id},
            source_licenses=read_json(args.source_licenses) if args.source_licenses else None)
    if args.command == 'world':
        return execution.prepare_world(store, read_json(args.registry), template=args.template,
                                        request_id=args.request_id, world_name=args.world_name, layout=args.layout)
    if args.command == 'client-directory':
        return execution.prepare_client_directory(store, read_json(args.registry), template=args.template,
                                                  request_id=args.request_id)
    if args.command == 'observe-pair':
        from .runtime_pair import observe_pair
        return observe_pair(store, server_session=args.server_session, client_session=args.client_session,
                            player_uuid=args.player_uuid, dimension=args.dimension,
                            timeout=args.timeout, screenshot=args.screenshot)
    if args.command == 'session':
        session = runtime.create_session(store, read_json(args.registry), read_json(args.contract),
                                          directory=Path(args.directory))
        # Authentication material must never reach the public CLI / content store.
        return {'status': 'OK', 'session_file': session['path'],
                'session_epoch': session['contract']['session_epoch'],
                'run_id': session['contract']['run_id'], 'outcome': 'NOT_RUN'}
    if args.command == 'contract':
        from .contracts import prepare_contract
        from .storage import atomic_write, canonical
        result = prepare_contract(store, read_json(args.registry), index_id=args.index,
                                  world=args.world, run_directory=args.run_directory, scenario=read_json(args.scenario))
        if args.output: atomic_write(Path(args.output), canonical(result['contract']))
        return result
    if args.command == 'input':
        from . import input_route
        registry = read_json(args.registry)
        if args.action == 'bind': return input_route.bind(store, registry)
        return input_route.dispatch_registered(store, registry, args.binding, read_json(args.request))
    if args.command == 'capabilities':
        return {'status': 'OK', 'adapter_version': runtime.ADAPTER_VERSION,
                'capability_scope': 'STATIC_SURFACE',
                'operations': ['profile', 'search', 'inspect', 'mapping', 'interventions', 'relations',
                               'context', 'knowledge', 'artifact', 'validate', 'world', 'client-directory', 'contract', 'session', 'observe', 'observe-pair', 'input'],
                'execution_policy': 'EXPLICIT_REGISTERED_PROVIDERS_ONLY', 'ci_used': False,
                'runtime_status': 'NOT_PROBED', 'core_status': 'OPTIONAL_EXISTING_CORE',
                'note': 'Command availability is not evidence of installed tools or successful Forge integration'}
    raise ContractError('Unknown connected operation')
