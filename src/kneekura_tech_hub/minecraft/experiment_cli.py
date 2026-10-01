"""Explicit offline experiment commands; there is intentionally no execute route."""
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
    p = sub.add_parser('compare'); p.add_argument('--before', required=True); p.add_argument('--after', required=True)
    p.add_argument('--changed-target', action='append', choices=sorted(experiment_contract.TARGET_FIELDS), default=[])


def dispatch(args, store, read_json):
    try:
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
        if args.action == 'compare':
            return experiment_contract.compare_requests(read_json(args.before), read_json(args.after), args.changed_target)
        raise ContractError('Unsupported offline experiment command')
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        # Source paths, malformed field names and raw external report content
        # must not become public diagnostics through the main CLI envelope.
        raise ContractError('Experiment input or retained evidence is invalid or unavailable') from None
