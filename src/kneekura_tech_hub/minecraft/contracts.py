"""Assemble run identities from captured inputs, not manually copied hash strings."""
from __future__ import annotations

from pathlib import Path
import uuid

from . import index, verification
from .execution import _owned_world, _file
from .runtime import ADAPTER_ID, ADAPTER_VERSION, config_snapshot
from .storage import ContractError, Store, Limits, _collect, digest, key_for
from .workspace import _workspace, workspace_fingerprint


def prepare_contract(store: Store, registry: dict, *, index_id: str, world: str,
                     scenario: dict) -> dict:
    root = _workspace(registry.get('workspace'))
    marker, _ = _owned_world(root, world)
    snapshot = index._load(store, index_id)
    profile = snapshot['profile']; manifest = profile['manifest']
    current = workspace_fingerprint(root)
    if manifest.get('dirty_hash') != current:
        raise ContractError('Index sources are stale; explicitly import current inputs')
    if manifest.get('workspace') and Path(manifest['workspace']).resolve() != root:
        raise ContractError('Index belongs to a different workspace')
    if (manifest['minecraft'], manifest['loader'], manifest['java_major']) != ('1.20.1', 'forge', 17):
        raise ContractError('Run requires Forge 1.20.1 / Java17 inputs')
    if not isinstance(scenario, dict): raise ContractError('Explicit scenario object required')
    domain = scenario.get('assertion_domain')
    if domain not in ('server_behavior', 'rendering', 'client_observation'):
        raise ContractError('Explicit supported assertion domain required')
    tests = scenario.get('expected_tests', [])
    flags = scenario.get('expected_required', {})
    if (not isinstance(tests, list) or any(not isinstance(t, str) or not t for t in tests)
            or len(set(tests)) != len(tests) or domain == 'server_behavior' and not tests):
        raise ContractError('Server behaviour requires a nonempty distinct expected test ID set')
    if not isinstance(flags, dict) or any(k not in tests or type(v) is not bool for k, v in flags.items()):
        raise ContractError('Expected required flags must refer to selected tests')
    output = _file(root, registry.get('build_artifact'))
    if not output.exists(): raise ContractError('Expected build artifact unavailable')
    errors = []; exclusions = []
    rows, raw = _collect(output, 'directory' if output.is_dir() else 'jar', Limits(), errors, exclusions, store.root)
    if errors or exclusions: raise ContractError('Build artifact is incomplete')
    artifact = digest(raw) if raw is not None else key_for([{'path': p, 'hash': digest(b)} for p, b in sorted(rows)])
    receipt = store.json(registry.get('build_receipt_hash'))
    if (receipt.get('request', {}).get('kind') != 'compile'
            or receipt['request'].get('workspace') != str(root)
            or receipt.get('result', {}).get('outcome') != 'PASS'
            or receipt.get('source_generation') != current
            or receipt.get('source_generation_after') != current
            or not any(o['content_hash'] == artifact for o in receipt.get('outputs', []))):
        raise ContractError('Expected successful same-source compile receipt is missing')
    assertions = {'assertion_domain': domain, 'expected_tests': tests, 'expected_required': flags}
    scenario_hash = store.put_json(scenario); assertion_hash = store.put_json(assertions)
    contract = dict(schema_version=1, run_id=str(uuid.uuid4()), session_epoch=str(uuid.uuid4()),
        profile_id=profile['profile_id'], index_snapshot_id=index_id, build_artifact_hash=artifact,
        source_revision=manifest.get('workspace_revision'), dirty_hash=current,
        scenario_hash=scenario_hash, assertion_hash=assertion_hash,
        world_id=marker['world_id'], world_template_hash=marker['world_template_hash'],
        world_seed=scenario.get('world_seed'), config_hash=key_for(config_snapshot(registry)),
        physical_side=manifest['physical_side'], logical_side='server',
        adapter_id=ADAPTER_ID, adapter_version=ADAPTER_VERSION, **assertions)
    errors = verification._identity_errors(contract, {'identity': contract})
    if errors: raise ContractError('; '.join(errors))
    h = store.put_json(contract)
    for item in (h, scenario_hash, assertion_hash): store.pin(item, 'run-contract:' + h)
    return {'schema_version': 1, 'status': 'OK', 'outcome': 'NOT_RUN', 'contract_hash': h,
            'contract': contract, 'note': 'Identity preparation; no game or tests were executed'}
