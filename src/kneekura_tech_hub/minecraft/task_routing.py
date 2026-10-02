"""Read-only, context-aware capability prerequisites for the Minecraft task facade.

READY describes an offered local operation (not execution or gameplay acceptance).
In particular, GameTest readiness is for preparing the existing contract/runner
path; the runner still revalidates its scenario, authority and launch budget.
Retained sessions cannot establish current live observation or input readiness.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import zipfile

from . import asset_contract, blockbench, execution, experiment_adapter, input_route, runtime, task_context, verification
from .storage import ContractError, Limits, Store, _collect, digest, key_for, valid_hash
from .workspace import workspace_fingerprint


CAPABILITY_IDS = ('source_search', 'bytecode_inspect', 'mappings', 'failure_history',
                  'core_context', 'blockbench_asset', 'forge_build', 'gametest',
                  'server_observation', 'client_observation', 'native_input', 'experimental_runtime')
_LOCAL_ERRORS = (ContractError, OSError, ValueError, TypeError, KeyError, AttributeError, zipfile.BadZipFile)
_RUNTIME_IDS = ('gametest', 'server_observation', 'client_observation', 'native_input')


class _Unavailable(Exception):
    """Only fixed public codes and prerequisite labels cross the facade."""

    def __init__(self, readiness, code, missing, evidence=()):
        self.readiness, self.code = readiness, code
        self.missing, self.evidence = missing, evidence


def _record(identifier, readiness, code, missing=(), evidence=(), *, surface='IMPLEMENTED'):
    return {'id': identifier, 'surface': surface, 'readiness': readiness, 'reason_code': code,
            'missing': list(missing), 'evidence': list(dict.fromkeys(evidence))}


def _checked(identifier, operation, *, evidence=()):
    try:
        return operation()
    except _Unavailable as error:
        return _record(identifier, error.readiness, error.code, error.missing,
                       (*evidence, *error.evidence))
    except _LOCAL_ERRORS:
        # Never publish a validator's exception text: it may contain local paths.
        return _record(identifier, 'BLOCKED', 'EVIDENCE_SCOPE_INSUFFICIENT',
                       ('valid_local_prerequisites',), evidence)


def _registered(store, inputs, kind):
    registry = inputs.get('run_registry')
    if registry is None:
        raise _Unavailable('NOT_CONFIGURED', 'PROVIDER_NOT_REGISTERED', ('run_registry',))
    try:
        root, _ = execution._registry(registry, kind)
    except _LOCAL_ERRORS:
        raise _Unavailable('BLOCKED', 'LAUNCH_NOT_AUTHORIZED', ('registered_operation',)) from None
    lock = store.root / ('workspace-' + key_for(str(root)) + '.lock')
    if lock.exists() or lock.is_symlink():
        raise _Unavailable('UNKNOWN', 'SESSION_UNKNOWN_COMPLETION', ('workspace_reconciliation',))
    return registry, root


def _current_profile(inputs, root):
    snapshot = inputs.get('index')
    if snapshot is None:
        raise _Unavailable('NOT_CONFIGURED', 'PROFILE_MISSING', ('environment_capture', 'index_snapshot_id'))
    manifest = snapshot['profile']['manifest']
    current = workspace_fingerprint(root)
    if (manifest.get('dirty_hash') != current
            or manifest.get('workspace') and Path(manifest['workspace']).resolve() != root):
        raise _Unavailable('BLOCKED', 'INDEX_STALE', ('current_index',))
    target = task_context.summarize_target(inputs)
    if target['loader'] != 'forge' or any(target[k] is None for k in
            ('minecraft', 'loader_version', 'java_major', 'workspace_revision')):
        raise _Unavailable('UNKNOWN', 'EVIDENCE_SCOPE_INSUFFICIENT', ('exact_forge_target',))
    return manifest, current


def _compile_receipt(store, inputs, registry, *, require_known_completion=True):
    """Use bounded CAS verification; an opaque receipt cannot prove completion."""
    if not registry.get('build_receipt_hash'):
        raise _Unavailable('NOT_CONFIGURED', 'EVIDENCE_SCOPE_INSUFFICIENT',
                           ('successful_compile_receipt',))
    identifier = valid_hash(registry['build_receipt_hash'])
    pointer, = task_context._evidence_metadata(store, (identifier,))
    raw = task_context._verified_evidence_bytes(store, pointer)
    if raw is None:
        raise _Unavailable('UNKNOWN', 'EVIDENCE_SCOPE_INSUFFICIENT', ('readable_compile_receipt',), (identifier,))
    receipt = json.loads(raw, object_pairs_hook=task_context._unique_json_object,
                         parse_constant=task_context._reject_nonfinite_json)
    if not isinstance(receipt, dict):
        raise _Unavailable('BLOCKED', 'EVIDENCE_SCOPE_INSUFFICIENT', ('successful_compile_receipt',))
    task_context._check_evidence_session_identity(receipt, inputs)
    expected = task_context._expected_evidence_identity(inputs)
    public = task_context._project_evidence_record(receipt, expected)
    if require_known_completion and _uncertain(public):
        raise _Unavailable('UNKNOWN', 'SESSION_UNKNOWN_COMPLETION', ('build_reconciliation',), (identifier,))
    return identifier, receipt


def _compile_artifact(store, inputs, registry, root, current):
    """Read the compile/artifact identities required by contracts/runtime."""
    identifier, receipt = _compile_receipt(store, inputs, registry)
    if receipt.get('result', {}).get('outcome') != 'PASS':
        # An unsuccessful completed attempt is valid evidence, but cannot prove
        # the successful compile prerequisite. It is not an identity conflict.
        raise _Unavailable('BLOCKED', 'EVIDENCE_SCOPE_INSUFFICIENT', ('successful_compile_receipt',), (identifier,))
    if not registry.get('build_artifact'):
        raise _Unavailable('NOT_CONFIGURED', 'EVIDENCE_SCOPE_INSUFFICIENT', ('build_artifact',))
    output = execution._file(root, registry['build_artifact'])
    errors, exclusions = [], []
    rows, original = _collect(output, 'directory' if output.is_dir() else 'jar',
                              Limits(), errors, exclusions, store.root)
    if errors or exclusions or not any(name.endswith('.class') for name, _ in rows):
        raise _Unavailable('BLOCKED', 'EVIDENCE_SCOPE_INSUFFICIENT', ('complete_build_artifact',))
    artifact = digest(original) if original is not None else key_for(
        [{'path': name, 'hash': digest(data)} for name, data in sorted(rows)])
    if (receipt.get('request', {}).get('kind') != 'compile'
            or receipt['request'].get('workspace') != str(root)
            or receipt.get('source_generation') != current
            or receipt.get('source_generation_after') != current
            or not any(row.get('content_hash') == artifact for row in receipt.get('outputs', []))):
        raise _Unavailable('BLOCKED', 'EVIDENCE_SCOPE_INSUFFICIENT', ('successful_same_source_compile',), (identifier,))
    return identifier, artifact


def _build(store, inputs):
    registry, root = _registered(store, inputs, 'compile')
    _current_profile(inputs, root)
    if registry.get('build_receipt_hash') is not None:
        _compile_receipt(store, inputs, registry)
    return _record('forge_build', 'READY', 'PREREQUISITES_SATISFIED', evidence=(inputs['index_snapshot_id'],))


def _gametest(store, inputs):
    registry, root = _registered(store, inputs, 'gametest')
    manifest, current = _current_profile(inputs, root)
    selected_contract = (inputs.get('session') or {}).get('contract')
    role, _ = runtime.dedicated_registry(registry, selected_contract)
    if (role is not None or inputs.get('run_directory') is not None
            or any(k in manifest for k in ('runtime_scope', 'dependency_inventory_hash', 'target_selection'))):
        raise _Unavailable('BLOCKED', 'LAUNCH_NOT_AUTHORIZED', ('gametest_runtime_role',))
    if (manifest['minecraft'], manifest['java_major'], manifest.get('physical_side')) != ('1.20.1', 17, 'server'):
        raise _Unavailable('BLOCKED', 'EVIDENCE_SCOPE_INSUFFICIENT', ('gametest_server_target',))
    if inputs.get('world') is None:
        raise _Unavailable('NOT_CONFIGURED', 'LAUNCH_NOT_AUTHORIZED', ('prepared_world',))
    marker, _ = execution._owned_world(root, inputs['world'], layout='server')
    session_path = Path(marker['directory']) / 'session.json'
    if session_path.exists() or session_path.is_symlink():
        raise _Unavailable('BLOCKED', 'LAUNCH_NOT_AUTHORIZED', ('unused_run_directory',))
    budget, budget_id = registry.get('remaining_launches'), registry.get('launch_budget_id')
    if type(budget) is not int or budget < 1 or not isinstance(budget_id, str) or not budget_id:
        raise _Unavailable('BLOCKED', 'LAUNCH_NOT_AUTHORIZED', ('launch_budget',))
    launches = store.root / 'launches'
    used = launches / key_for({'workspace': str(root), 'budget': budget_id})
    if (launches.is_symlink() or used.is_symlink()
            or used.exists() and not used.is_dir() or len(list(used.glob('*.json'))) >= budget):
        raise _Unavailable('BLOCKED', 'LAUNCH_NOT_AUTHORIZED', ('remaining_launch_budget',))
    receipt, artifact = _compile_artifact(store, inputs, registry, root, current)
    config_hash = key_for(runtime.config_snapshot(registry))
    session = inputs.get('session')
    if session is not None:
        c = session['contract']
        expected = dict(c, profile_id=inputs['index']['profile']['profile_id'],
            index_snapshot_id=inputs['index_snapshot_id'], dirty_hash=current,
            source_revision=manifest['workspace_revision'], build_artifact_hash=artifact,
            world_id=marker['world_id'], world_template_hash=marker['world_template_hash'],
            config_hash=config_hash, physical_side='server', logical_side='server',
            adapter_id=runtime.ADAPTER_ID, adapter_version=runtime.ADAPTER_VERSION)
        if verification._identity_errors(expected, {'identity': c}):
            raise _Unavailable('BLOCKED', 'EVIDENCE_SCOPE_INSUFFICIENT', ('matching_run_identity',))
    return _record('gametest', 'READY', 'PREREQUISITES_SATISFIED',
                   evidence=(inputs['index_snapshot_id'], receipt, artifact))


def _retained_session(inputs):
    selected = inputs.get('session')
    if selected is None:
        raise _Unavailable('NOT_CONFIGURED', 'SESSION_NOT_CONFIGURED', ('session',))
    try:
        actual = runtime.load_session(selected.get('path'))
        c = selected['contract']
        directory = Path(actual['directory'])
        if (verification._identity_errors(c, {'identity': actual['contract']}) or actual != selected
                or c.get('adapter_id') != runtime.ADAPTER_ID or c.get('adapter_version') != runtime.ADAPTER_VERSION
                or not directory.is_absolute() or directory.is_symlink() or not directory.is_dir()
                or directory != directory.resolve() or Path(actual['path']) != directory / 'session.json'
                or Path(actual['endpoint_path']) != directory / 'endpoint.json'):
            raise ContractError('Retained session identity mismatch')
    except _LOCAL_ERRORS:
        raise _Unavailable('BLOCKED', 'SESSION_IDENTITY_INVALID', ('matching_private_session',)) from None
    return actual


def _observation(inputs, side):
    identifier = side + '_observation'
    session = _retained_session(inputs)
    c = session['contract']
    # Integrated clients can carry server observations; dedicated receiving
    # clients cannot establish server-side readiness from their local world.
    if side == 'client' and c['physical_side'] != 'client' or side == 'server' and c['logical_side'] != 'server':
        raise _Unavailable('BLOCKED', 'EVIDENCE_SCOPE_INSUFFICIENT', ('matching_session_side',))
    return _record(identifier, 'UNKNOWN', 'LIVE_STATE_NOT_PROBED', ('authenticated_live_observation',),
                   (c['profile_id'], c['index_snapshot_id'], c['build_artifact_hash']))


def _native(inputs):
    registry = inputs.get('input_registry')
    if registry is None:
        raise _Unavailable('NOT_CONFIGURED', 'PROVIDER_NOT_REGISTERED', ('input_registry',))
    selected = _retained_session(inputs)
    try:
        registered, session = input_route._registry(registry)
        if session != selected:
            raise ContractError('Registered session differs')
    except _LOCAL_ERRORS:
        raise _Unavailable('BLOCKED', 'SESSION_IDENTITY_INVALID', ('registered_client_identity',)) from None
    attempts = Path(session['directory']) / '.input-attempts'
    lock = attempts / ('active-' + key_for({'display': registered['display']}))
    if attempts.is_symlink() or lock.exists() or lock.is_symlink():
        raise _Unavailable('UNKNOWN', 'SESSION_UNKNOWN_COMPLETION', ('input_reconciliation',))
    c = session['contract']
    return _record('native_input', 'UNKNOWN', 'LIVE_STATE_NOT_PROBED',
                   ('authenticated_live_observation', 'native_target_binding'),
                   (c['profile_id'], c['index_snapshot_id'], c['build_artifact_hash']))


def _provider(inputs):
    registry = inputs.get('blockbench_registry')
    if registry is None:
        raise _Unavailable('NOT_CONFIGURED', 'PROVIDER_NOT_REGISTERED', ('blockbench_registry',))
    checked = blockbench._registry(registry)
    if not checked['allow_probe']:
        raise _Unavailable('BLOCKED', 'PROVIDER_NOT_REGISTERED', ('authorized_provider_probe',))
    return _record('blockbench_asset', 'UNKNOWN', 'LIVE_STATE_NOT_PROBED', ('guarded_provider_readiness',))


def _uncertain(item):
    return any(item.get(field) in ('UNKNOWN', 'STARTED') for field in ('status', 'outcome', 'input_status'))


def _unknown_capabilities(item):
    if item.get('classification') != 'receipt' or not _uncertain(item):
        return ()
    kind, record_type = item.get('kind'), item.get('record_type')
    if kind in ('native-input-receipt', 'input-receipt') or record_type == 'input_receipt':
        return ('native_input',)
    if kind in ('compile', 'build', 'build-receipt') or record_type == 'build_receipt':
        return ('forge_build', 'gametest')
    if kind == 'gametest':
        return ('gametest', 'server_observation')
    if kind == 'server':
        return ('server_observation',)
    if kind == 'client':
        return ('client_observation', 'native_input')
    if record_type in ('asset_editor_inspection', 'asset_session_capture', 'asset_export', 'asset_guard_package', 'asset_request'):
        return ('blockbench_asset',)
    return _RUNTIME_IDS


def evaluate_capabilities(store: Store, request: dict, inputs: dict, evidence: dict) -> list[dict]:
    """Evaluate validated Task 1 inputs and Task 2 summaries without side effects.

    Request prose is never authority. OS support describes this execution host or
    an explicitly registered backend, never a platform inferred for indexed code.
    Public evidence contains only existing SHA-256 references, never body/path data.
    """
    task_context.validate_task_request(request)
    result = {}
    index_id = inputs.get('index_snapshot_id')
    scope = evidence['index']
    for identifier, available in (('source_search', scope['source_documents'] > 0),
            ('bytecode_inspect', scope['prepared_bytecode'] > 0 and scope['coverage_complete'] is True
             and scope['unresolved_roots'] == 0 and scope['unresolved_bytecode'] == 0)):
        if inputs.get('index') is None:
            result[identifier] = _record(identifier, 'NOT_CONFIGURED', 'PROFILE_MISSING',
                                         ('environment_capture', 'index_snapshot_id'))
        elif available:
            result[identifier] = _record(identifier, 'READY', 'PREREQUISITES_SATISFIED', evidence=(index_id,))
        else:
            result[identifier] = _record(identifier, 'UNKNOWN', 'EVIDENCE_SCOPE_INSUFFICIENT',
                ('captured_source' if identifier == 'source_search' else 'prepared_bytecode_coverage',), (index_id,))
    for identifier, classification, code, missing in (
            ('mappings', 'mapping', 'MAPPING_NOT_CONFIGURED', 'mapping_record'),
            ('failure_history', 'history', 'HISTORY_NOT_CONFIGURED', 'history_record')):
        hashes = [item['content_hash'] for item in evidence['items'] if item['classification'] == classification]
        result[identifier] = _record(identifier, 'READY' if hashes else 'NOT_CONFIGURED',
            'PREREQUISITES_SATISFIED' if hashes else code, () if hashes else (missing,), hashes)
    configured = inputs.get('core_configured') is True
    result['core_context'] = _record('core_context', 'UNKNOWN' if configured else 'NOT_CONFIGURED',
        'LIVE_STATE_NOT_PROBED' if configured else 'PROVIDER_NOT_REGISTERED',
        ('core_probe',) if configured else ('core_configured',))
    for identifier, operation in (
            ('blockbench_asset', lambda: _provider(inputs)),
            ('forge_build', lambda: _build(store, inputs)),
            ('gametest', lambda: _gametest(store, inputs)),
            ('server_observation', lambda: _observation(inputs, 'server')),
            ('client_observation', lambda: _observation(inputs, 'client')),
            ('native_input', lambda: _native(inputs))):
        result[identifier] = _checked(identifier, operation)
    backend = (inputs.get('input_registry') or {}).get('backend')
    windows = sys.platform.startswith('win') or isinstance(backend, str) and backend.startswith('windows')
    if windows or not sys.platform.startswith('linux'):
        result['native_input'] = _record('native_input', 'BLOCKED',
            'WINDOWS_INPUT_UNSUPPORTED' if windows else 'NATIVE_INPUT_UNSUPPORTED',
            ('supported_native_backend',), surface='UNSUPPORTED')
    for item in evidence['items']:
        for identifier in _unknown_capabilities(item):
            prior = result[identifier]
            missing = tuple(dict.fromkeys((*prior['missing'], 'completion_reconciliation')))
            hashes = (*prior['evidence'], item['content_hash'])
            if prior['surface'] == 'UNSUPPORTED':
                result[identifier] = _record(identifier, prior['readiness'], prior['reason_code'],
                                             missing, hashes, surface=prior['surface'])
                continue
            result[identifier] = _record(identifier, 'UNKNOWN', 'SESSION_UNKNOWN_COMPLETION',
                                         missing, hashes)
    report = inputs.get('experiment_report')
    control = inputs.get('experiment_control_receipt')
    if control and control['requires_reconciliation']:
        result['experimental_runtime'] = _record('experimental_runtime', 'UNKNOWN',
            'SESSION_UNKNOWN_COMPLETION', ('completion_reconciliation',), (control['receipt_hash'],))
    elif report and report['next_operation'] == 'experiment.reconcile_unknown':
        result['experimental_runtime'] = _record('experimental_runtime', 'UNKNOWN',
            'SESSION_UNKNOWN_COMPLETION', ('completion_reconciliation',), (report['result_hash'],))
    elif report and report['currentness'] == 'REVERIFY_REQUIRED':
        result['experimental_runtime'] = _record('experimental_runtime', 'BLOCKED',
            'EXPERIMENT_TARGET_CHANGED', ('current_target_reverification', 'loaded_runtime_attestation'),
            (report['result_hash'],))
    elif report or inputs.get('experiment_adapter') or inputs.get('experiment_control_adapter') or control:
        result['experimental_runtime'] = _record('experimental_runtime', 'BLOCKED',
            'LAB_RUNTIME_ATTESTATION_REQUIRED', ('loaded_runtime_attestation', 'disposable_world_authority',
            'live_repair_acceptance'), (report['result_hash'],) if report else (control['receipt_hash'],) if control else ())
    elif experiment_adapter.inspect_builtin_source().get('status') == 'AVAILABLE':
        result['experimental_runtime'] = _record('experimental_runtime', 'BLOCKED',
            'LAB_RUNTIME_ATTESTATION_REQUIRED', ('experiment_registry', 'loaded_runtime_attestation',
            'disposable_world_authority', 'live_repair_acceptance'))
    else:
        result['experimental_runtime'] = _record('experimental_runtime', 'NOT_CONFIGURED',
            'LAB_ADAPTER_NOT_REGISTERED', ('experiment_registry_or_retained_result',))
    rows = [result[identifier] for identifier in CAPABILITY_IDS]
    task_context._check_private_aliases(rows, inputs)
    return rows


_RESEARCH_INTENTS = ('investigate', 'edit_code', 'compatibility_research')
# Operation, applicable intents, required READY capability, mode, explicit inputs.
# This is a recommendation table, not an executable workflow or permission grant.
_NEXT_ACTION_RULES = (
    ('research.search', _RESEARCH_INTENTS, 'source_search', 'READ_ONLY', ('query',)),
    ('research.inspect', _RESEARCH_INTENTS, 'bytecode_inspect', 'READ_ONLY', ('symbol_selector',)),
    ('history.query', tuple(sorted(task_context.TASK_INTENTS)), 'failure_history', 'READ_ONLY', ('query',)),
    ('build.registered', ('edit_code', 'verify_server'), 'forge_build', 'SIDE_EFFECTING', ('request_id',)),
    ('gametest.prepare', ('edit_code', 'verify_server'), 'gametest', 'SIDE_EFFECTING', ('verification_scenario',)),
)


def _action(operation, mode, required=(), *, primary=False, reason='PREREQUISITES_SATISFIED'):
    return {'operation_id': operation, 'primary': primary, 'mode': mode,
            'authorization_required': mode == 'SIDE_EFFECTING', 'reason_code': reason,
            'required_inputs': list(required)}


def _needs_reconciliation(capabilities):
    # Unsupported Windows input retains its surface/reason, but still carries
    # this prerequisite when a previous mutation has unknown completion.
    return any(c['reason_code'] == 'SESSION_UNKNOWN_COMPLETION'
               or 'completion_reconciliation' in c['missing'] for c in capabilities)


def derive_next_actions(request: dict, inputs: dict, capabilities: list[dict]) -> list[dict]:
    """Offer at most five inert operations using typed intent and local readiness.

    Goal/constraint/acceptance prose cannot select an operation or supply inputs.
    Unknown completion conservatively suppresses all new side-effecting advice;
    reconciliation is a read-only review, never a mutation replay or retry.
    """
    intent = task_context.validate_task_request(request)['intent']
    by_id = {c['id']: c for c in capabilities}
    reconcile = _needs_reconciliation(capabilities)
    actions = []
    if reconcile:
        control = inputs.get('experiment_control_receipt')
        operation = (control['next_operation'] if control and control['requires_reconciliation'] else
            'experiment.reconcile_unknown' if inputs.get('experiment_report', {}).get('next_operation') == 'experiment.reconcile_unknown'
            else 'runtime.reconcile_unknown')
        actions.append(_action(operation, 'READ_ONLY',
            ('operation_identity', 'retained_receipt'), primary=True, reason='SESSION_UNKNOWN_COMPLETION'))
    elif inputs.get('index') is None:
        actions.append(_action('profile.resolve', 'SIDE_EFFECTING', ('environment_capture',),
                               primary=True, reason='PROFILE_MISSING'))
    if inputs.get('experiment_report') and not reconcile:
        actions.append(_action('experiment.inspect_result', 'READ_ONLY', ('result_hash',)))
    elif inputs.get('experiment_control_adapter') and not reconcile:
        actions.append(_action('experiment.inspect_owner', 'READ_ONLY', ('request_hash', 'control_registry')))
    elif inputs.get('experiment_adapter') and not reconcile:
        actions.append(_action('experiment.prepare', 'SIDE_EFFECTING', ('experiment_request',)))
    for operation, intents, capability, mode, required in _NEXT_ACTION_RULES:
        c = by_id.get(capability, {})
        if (intent in intents and c.get('surface') == 'IMPLEMENTED' and c.get('readiness') == 'READY'
                and not (reconcile and mode == 'SIDE_EFFECTING')):
            actions.append(_action(operation, mode, required))
    if intent == 'create_asset' and inputs.get('index') is not None and not reconcile:
        try:
            # Reuse the existing complete exact-target contract; never prepare
            # an asset, access a provider, or persist anything here.
            asset_contract._profile(inputs['index']['profile'])
        except ContractError:
            pass
        else:
            actions.append(_action('asset.prepare', 'SIDE_EFFECTING', ('asset_spec',)))
    observation = {'verify_server': 'server_observation', 'verify_client': 'client_observation'}.get(intent)
    c = by_id.get(observation, {})
    if (c.get('surface') == 'IMPLEMENTED' and c.get('readiness') == 'UNKNOWN'
            and c.get('reason_code') == 'LIVE_STATE_NOT_PROBED'):
        actions.append(_action('runtime.observe', 'READ_ONLY', ('observation_query',),
                               reason='LIVE_STATE_NOT_PROBED'))
    return actions[:5]
