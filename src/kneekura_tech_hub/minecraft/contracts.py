"""Assemble run identities from captured inputs, not manually copied hash strings."""
from __future__ import annotations

from pathlib import Path
import uuid

from . import index, verification
from .execution import _owned_world, _owned_client_directory, _file
from .runtime import ADAPTER_ID, ADAPTER_VERSION, config_snapshot, dedicated_registry, resolve_server_contract, _profile_dependencies
from .storage import ContractError, Store, Limits, _collect, digest, key_for
from .workspace import _workspace, workspace_fingerprint


def prepare_contract(store: Store, registry: dict, *, index_id: str, world: str | None = None,
                     run_directory: str | None = None, scenario: dict) -> dict:
    root = _workspace(registry.get('workspace'))
    role, policy = dedicated_registry(registry)
    if (world is None) == (run_directory is None):
        raise ContractError('Supply exactly one prepared world or client run directory')
    if role == 'dedicated_client':
        if world is not None: raise ContractError('Receiving client cannot own a server world')
        marker, _ = _owned_client_directory(root, run_directory)
    else:
        if run_directory is not None: raise ContractError('Run directory requires dedicated client role')
        marker, _ = _owned_world(root, world, layout='client' if role == 'integrated_client' else 'server' if role else None)
    snapshot = index._load(store, index_id)
    profile = snapshot['profile']; manifest = profile['manifest']
    if role is None and any(k in manifest for k in ('runtime_scope', 'dependency_inventory_hash', 'target_selection')):
        raise ContractError('Scoped target profile requires an explicit versioned runtime role')
    if role: _profile_dependencies(store, registry, profile)
    current = workspace_fingerprint(root)
    if manifest.get('dirty_hash') != current:
        raise ContractError('Index sources are stale; explicitly import current inputs')
    if manifest.get('workspace') and Path(manifest['workspace']).resolve() != root:
        raise ContractError('Index belongs to a different workspace')
    if (manifest['minecraft'], manifest['loader'], manifest['java_major']) != ('1.20.1', 'forge', 17):
        raise ContractError('Run requires Forge 1.20.1 / Java17 inputs')
    if not isinstance(scenario, dict): raise ContractError('Explicit scenario object required')
    domain = scenario.get('assertion_domain')
    if domain not in ('server_behavior', 'rendering', 'client_observation', 'server_observation'):
        raise ContractError('Explicit supported assertion domain required')
    if role == 'integrated_client':
        if domain != 'rendering' or manifest.get('physical_side') != 'client':
            raise ContractError('Integrated U04 role requires rendering domain and client profile')
    elif role and (domain != ('client_observation' if role == 'dedicated_client' else 'server_observation')
                   or manifest.get('physical_side') != ('client' if role == 'dedicated_client' else 'server')):
        raise ContractError('Dedicated role requires its exact observation domain and physical profile side')
    if not role and domain == 'server_observation':
        raise ContractError('Server observation requires explicit dedicated server registration')
    tests = scenario.get('expected_tests', [])
    flags = scenario.get('expected_required', {})
    if (not isinstance(tests, list) or any(not isinstance(t, str) or not t for t in tests)
            or len(set(tests)) != len(tests) or domain == 'server_behavior' and not tests):
        raise ContractError('Server behaviour requires a nonempty distinct expected test ID set')
    if role and tests: raise ContractError('Dedicated observation cannot declare GameTest execution IDs')
    if role == 'dedicated_client' and any(k in scenario for k in ('world_id', 'world_template_hash', 'world_seed')):
        raise ContractError('Receiving-client scenario cannot assert a local server world')
    if not isinstance(flags, dict) or any(k not in tests or type(v) is not bool for k, v in flags.items()):
        raise ContractError('Expected required flags must refer to selected tests')
    controls = verification.validate_negative_controls(scenario.get('negative_controls', {}), tests)
    if controls and domain != 'server_behavior':
        raise ContractError('Negative GameTest controls require the server behavior domain')
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
    if 'negative_controls' in scenario:
        assertions['negative_controls'] = controls
    if role == 'dedicated_client':
        resolve_server_contract(store, registry, manifest=manifest, artifact_hash=artifact,
                                source_revision=manifest.get('workspace_revision'))
    scenario_hash = key_for(scenario); assertion_hash = key_for(assertions)
    contract = dict(schema_version=1, run_id=str(uuid.uuid4()), session_epoch=str(uuid.uuid4()),
        profile_id=profile['profile_id'], index_snapshot_id=index_id, build_artifact_hash=artifact,
        source_revision=manifest.get('workspace_revision'), dirty_hash=current,
        scenario_hash=scenario_hash, assertion_hash=assertion_hash,
        config_hash=key_for(config_snapshot(registry)),
        physical_side=manifest['physical_side'], logical_side='server',
        adapter_id=ADAPTER_ID, adapter_version=ADAPTER_VERSION, **assertions)
    if role:
        contract.update(schema_version=3 if role == 'integrated_client' else 2, session_role=role,
                        runtime_scope=registry['runtime_scope'], dependency_inventory_hash=registry['dependency_inventory_hash'])
        if role == 'integrated_client': contract['target_selection_hash'] = key_for(registry['target_selection'])
        else: contract.update(connection_policy=policy, connection_policy_hash=key_for(policy))
    if role == 'dedicated_client':
        contract.update(logical_side='client', run_directory_id=marker['run_directory_id'],
                        run_directory_template_hash=marker['run_directory_template_hash'],
                        server_contract_hash=registry['server_contract_hash'], player_uuid=registry['player_uuid'])
    else:
        contract.update(world_id=marker['world_id'], world_template_hash=marker['world_template_hash'],
                        world_seed=scenario.get('world_seed'))
    errors = verification._identity_errors(contract, {'identity': contract})
    if errors: raise ContractError('; '.join(errors))
    store.put_json(scenario); store.put_json(assertions)
    h = store.put_json(contract)
    for item in (h, scenario_hash, assertion_hash): store.pin(item, 'run-contract:' + h)
    return {'schema_version': 1, 'status': 'OK', 'outcome': 'NOT_RUN', 'contract_hash': h,
            'contract': contract, 'note': 'Identity preparation; no game or tests were executed'}
