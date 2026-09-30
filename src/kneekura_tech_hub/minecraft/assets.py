"""Asset preparation CLI: python -m kneekura_tech_hub.minecraft.assets.

Uses the existing Minecraft CAS. Does not install plugins, launch a process,
submit editing commands. Probe and no-overwrite local export are explicit opt-in IO.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .asset_contract import decode_json, prepare_request, validate_spec
from .blockbench import probe
from .storage import ContractError, Store, canonical


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ContractError(message)


def _read(path: str, limit: int = 65536):
    source = Path(path)
    if not source.is_file():
        raise ContractError('Input must be an existing regular file')
    with source.open('rb') as stream:
        return decode_json(stream.read(limit + 1), max_bytes=limit)


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description='Prepare static Java-item asset requests and explicitly probe the editor.')
    parser.add_argument('--store', help='Existing Minecraft CAS directory; required for prepare/probe')
    subs = parser.add_subparsers(dest='operation', required=True)
    check = subs.add_parser('check', help='Validate the asset spec only; no editor, game or CAS writes')
    check.add_argument('--spec', required=True)
    prepare = subs.add_parser('prepare', help='Bind a request to an existing captured profile/index')
    prepare.add_argument('--spec', required=True)
    source = prepare.add_mutually_exclusive_group(required=True)
    source.add_argument('--index', help='Existing index_snapshot_id from the Minecraft CLI')
    source.add_argument('--profile', help='JSON object returned by capture_profile')
    inspect = subs.add_parser('probe', help='Three read-only loopback requests with explicit registry permission')
    inspect.add_argument('--registry', required=True)
    export = subs.add_parser('export', help='Materialize a verified capture into a fresh resource package')
    export.add_argument('--receipt', required=True)
    export.add_argument('--parent', required=True)
    try:
        args = parser.parse_args(argv)
        if args.operation == 'check':
            s = validate_spec(_read(args.spec))
            result = {'schema_version': 1, 'status': 'OK', 'outcome': 'NOT_RUN',
                      'assertion_domain': 'asset_spec_validation', 'asset_id': s['asset_id']}
        else:
            if not args.store:
                raise ContractError('--store is required for prepare, probe and export')
            store = Store(args.store)
            if args.operation == 'probe':
                result = probe(store, _read(args.registry))
            elif args.operation == 'export':
                from .asset_export import materialize_asset
                result = materialize_asset(store, args.receipt, parent=Path(args.parent))
            else:
                if args.index:
                    snapshot = store.json(args.index)
                    if not isinstance(snapshot, dict) or 'profile' not in snapshot:
                        raise ContractError('Artifact is not an index snapshot')
                    profile = snapshot['profile']
                else:
                    profile = _read(args.profile, 16 * 1024 * 1024)
                result = prepare_request(store, profile=profile, spec=_read(args.spec), index_id=args.index)
        print(canonical(result).decode('utf-8'))
        return 0 if result['status'] == 'OK' else 3
    except (ContractError, OSError, ValueError) as exc:
        print(canonical({'schema_version': 1, 'status': 'ERROR', 'outcome': 'NOT_RUN',
                         'error': str(exc)}).decode('utf-8'))
        return 2


if __name__ == '__main__':
    sys.exit(main())
