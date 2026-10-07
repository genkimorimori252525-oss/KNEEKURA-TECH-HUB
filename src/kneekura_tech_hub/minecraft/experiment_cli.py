"""Explicit experiment evidence and separately pinned control; no launch route."""
from __future__ import annotations

from . import experiment_bridge, experiment_contract
from .storage import ContractError, key_for


def add_commands(commands):
    sub = commands.add_parser('experiment', help='Offline LAB experiment contracts and retained reports').add_subparsers(
        dest='action', required=True)
    for name in ('validate', 'prepare'):
        sub.add_parser(name).add_argument('--request', required=True)
    sub.add_parser('inspect-request').add_argument('--request-hash', required=True)
    p = sub.add_parser('import-result'); p.add_argument('--request-hash', required=True); p.add_argument('--result', required=True)
    p = sub.add_parser('inspect-result'); p.add_argument('--result-hash', required=True); p.add_argument('--current-target')
    p = sub.add_parser('resume'); p.add_argument('--result-hash', required=True); p.add_argument('--current-target')
    sub.add_parser('inspect-adapter').add_argument('--registry', required=True)
    for name in ('register', 'inspect-registration', 'reconcile-unknown'):
        p = sub.add_parser(name); p.add_argument('--registry', required=True); p.add_argument('--request-hash', required=True)
        if name == 'reconcile-unknown': p.add_argument('--action-id', required=True)
    sub.add_parser('inspect-control').add_argument('--registry', required=True)
    sub.add_parser('inspect-control-receipt').add_argument('--receipt-hash', required=True)
    for name in ('inspect-owner', 'submit-action', 'request-capture', 'inspect-action', 'request-cleanup', 'inspect-cleanup', 'watch-triggers', 'export-result', 'import-export','mob-pov','inspect-mob-pov'):
        p = sub.add_parser(name); p.add_argument('--registry', required=True); p.add_argument('--request-hash', required=True)
        if name in ('submit-action', 'inspect-action'): p.add_argument('--action-id', required=True)
        if name == 'request-capture': p.add_argument('--capture-index', required=True, type=int)
        if name in ('mob-pov','inspect-mob-pov'): p.add_argument('--command-index',required=True,type=int)
        if name == 'mob-pov':
            p.add_argument('--camera-operation',required=True,choices=('attach','snapshot','return'))
            p.add_argument('--subject-uuid');p.add_argument('--duration-ms',type=int)
        if name == 'import-export': p.add_argument('--manifest-hash', required=True)
        if name == 'export-result':
            p.add_argument('--observation-id', action='append', default=[])
            p.add_argument('--timeline-observation-id', action='append', default=[])
            p.add_argument('--visual-packet-hash')
    p = sub.add_parser('compare'); p.add_argument('--before', required=True); p.add_argument('--after', required=True)
    p.add_argument('--changed-target', action='append', choices=sorted(experiment_contract.TARGET_FIELDS), default=[])


def dispatch(args, store, read_json):
    try:
        from . import experiment_adapter
        read_json = experiment_adapter.read_input_json
        if args.action == 'validate':
            request = experiment_contract.validate_experiment_request(read_json(args.request))
            return {'status': 'OK', 'request_hash': key_for(request), 'execution': 'NOT_RUN',
                    'runtime_attestation': 'NOT_ESTABLISHED'}
        if args.action == 'prepare':
            return experiment_bridge.prepare_experiment(store, read_json(args.request))
        if args.action == 'inspect-request':
            return {'status': 'OK', 'request': experiment_bridge.load_experiment(store, args.request_hash),
                    'execution': 'NOT_RUN', 'runtime_attestation': 'NOT_ESTABLISHED'}
        if args.action == 'import-result':
            return experiment_bridge.import_experiment_result(store, args.request_hash, read_json(args.result))
        if args.action == 'inspect-result':
            return experiment_bridge.inspect_experiment_result(store, args.result_hash,
                current_target=read_json(args.current_target) if args.current_target else None)
        if args.action == 'resume':
            return experiment_bridge.resume_experiment(store, args.result_hash,
                current_target=read_json(args.current_target) if args.current_target else None)
        if args.action in ('inspect-adapter', 'register', 'inspect-registration', 'reconcile-unknown'):
            registry = experiment_adapter.read_registry_file(args.registry)
            if args.action == 'inspect-adapter': return experiment_adapter.inspect_registry(registry)
            if args.action == 'register': return experiment_adapter.register_request(store, registry, args.request_hash)
            if args.action == 'inspect-registration': return experiment_adapter.inspect_registration(store, registry, args.request_hash)
            return experiment_adapter.reconcile_action(store, registry, args.request_hash, args.action_id)
        if args.action == 'inspect-control-receipt':
            from .experiment_control import inspect_receipt
            return inspect_receipt(store, args.receipt_hash)
        if args.action in ('inspect-control', 'inspect-owner', 'submit-action', 'request-capture', 'inspect-action', 'request-cleanup', 'inspect-cleanup', 'watch-triggers', 'export-result', 'import-export','mob-pov','inspect-mob-pov'):
            from . import experiment_control
            registry = experiment_adapter.read_registry_file(args.registry)
            if args.action == 'inspect-control': return experiment_control.inspect_registry(registry)
            if args.action == 'inspect-owner': return experiment_control.inspect_owner(store, registry, args.request_hash)
            if args.action == 'mob-pov': return experiment_control.mob_pov(store,registry,args.request_hash,args.command_index,args.camera_operation,subject_uuid=args.subject_uuid,duration_ms=args.duration_ms)
            if args.action == 'inspect-mob-pov': return experiment_control.inspect_mob_pov(store,registry,args.request_hash,args.command_index)
            if args.action == 'submit-action': return experiment_control.submit_action(store, registry, args.request_hash, args.action_id)
            if args.action == 'request-capture': return experiment_control.request_capture(store, registry, args.request_hash, args.capture_index)
            if args.action == 'inspect-action': return experiment_control.inspect_action(store, registry, args.request_hash, args.action_id)
            if args.action == 'request-cleanup': return experiment_control.request_cleanup(store, registry, args.request_hash)
            if args.action == 'inspect-cleanup': return experiment_control.inspect_cleanup(store, registry, args.request_hash)
            if args.action == 'watch-triggers': return experiment_control.watch_triggers(store, registry, args.request_hash)
            if args.action == 'export-result':
                return experiment_control.export_result(store, registry, args.request_hash, observation_ids=args.observation_id,
                    timeline_ids=args.timeline_observation_id, visual_packet_hash=args.visual_packet_hash)
            from .experiment_export import import_export
            return import_export(store, registry, args.request_hash, args.manifest_hash)
        if args.action == 'compare':
            return experiment_contract.compare_requests(read_json(args.before), read_json(args.after), args.changed_target)
        raise ContractError('Unsupported offline experiment command')
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        # Source paths, malformed field names and raw external report content
        # must not become public diagnostics through the main CLI envelope.
        raise ContractError('Experiment input or retained evidence is invalid or unavailable') from None
