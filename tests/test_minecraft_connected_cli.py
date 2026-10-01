"""Subprocess tests: real public CLI routes, not calls to private helpers."""
import json
from pathlib import Path
import socket
import subprocess

import pytest

from kneekura_tech_hub.minecraft import connected_cli, runtime, task_context
from kneekura_tech_hub.minecraft.__main__ import parse_json, parser, read_json
from kneekura_tech_hub.minecraft.storage import ContractError, Store, canonical
from test_minecraft_blockbench import registry as blockbench_registry
from test_minecraft_cli import run_cli
from test_minecraft_task_context import compile_receipt_record, deep_index_payload, task_request
from test_minecraft_task_routing import client_session, prepared
from test_minecraft_workspace import project, export_data
from test_minecraft_execution import local


def test_cli_passive_discovery_and_resolved_import(project, tmp_path):
    cache=tmp_path/'cas'
    p,out=run_cli(cache,'profile','discover','--workspace',str(project))
    assert p.returncode==0,p.stderr
    assert out['manifest']['dependency_resolution']=='UNKNOWN'
    data=export_data(project); data['output_roots']=[]
    export=tmp_path/'export.json'; export.write_text(json.dumps(data))
    p,out=run_cli(cache,'profile','import','--workspace',str(project),'--resolved',str(export))
    assert p.returncode==0,p.stderr
    index=out['index_snapshot_id']; assert index
    p,out=run_cli(cache,'search','--index',index,'--query','class Mob')
    assert out['results']


def test_cli_mapping_import_lookup_and_original_bytes(tmp_path):
    cache=tmp_path/'cas'; path=tmp_path/'names.tiny'
    text='tiny\t2\t0\tintermediary\tmojmap\nc\ta/A\tb/B\n\tm\t()V\ta\tattack\n'
    path.write_text(text)
    p,out=run_cli(cache,'mapping','import','--path',str(path),'--format','tiny')
    assert p.returncode==0,p.stderr
    table=out['mapping_hash']; raw=out['text_hash']
    p,out=run_cli(cache,'mapping','lookup','--mapping',table,'--from-namespace','intermediary','--to-namespace','mojmap','--owner','a/A','--member','a','--descriptor','()V')
    assert p.returncode==0,p.stderr
    assert out['results'][0]['name']=='attack'
    p,out=run_cli(cache,'artifact','read','--hash',raw,'--size','20')
    assert out['results'][0]['text']==text[:20] and out['next_cursor']
    p,more=run_cli(cache,'artifact','read','--hash',raw,'--size','20','--cursor',out['next_cursor'])
    assert more['results'][0]['text']==text[20:40]


def test_cli_interventions_and_core_staging_keep_provenance(project,tmp_path):
    cache=tmp_path/'cas'; data=export_data(project); data['output_roots']=[]
    (project/'src/main/resources/demo.accesswidener').write_text('accessWidener v2 named\naccessible class example/Mob\n')
    export=tmp_path/'export.json'; export.write_text(json.dumps(data))
    p,out=run_cli(cache,'profile','import','--workspace',str(project),'--resolved',str(export))
    assert p.returncode==0,p.stderr
    idx=out['index_snapshot_id']
    p,out=run_cli(cache,'interventions','--index',idx,'--owner','example/Mob')
    assert p.returncode==0,p.stderr
    assert out['results']
    p,search=run_cli(cache,'search','--index',idx,'--query','class Mob')
    doc=search['results'][0]['document_id']
    stage_args=('knowledge','stage','--index',idx,'--document',doc,'--summary','Observed declaration','--actor-id','jolly')
    p,out=run_cli(cache,*stage_args)
    assert p.returncode != 0 and 'license' in str(out).lower()
    # This file is a test-owned fixture; no real upstream license is inferred.
    from kneekura_tech_hub.minecraft.storage import Store
    from kneekura_tech_hub.minecraft.index import _load
    store=Store(cache)
    snapshot=_load(store,idx)
    licenses=tmp_path/'reviewed-licenses.json'
    licenses.write_text(json.dumps({root['id']:{'state':'KNOWN','declared_expression':'MIT'}
                                    for root in snapshot['profile']['roots']}))
    p,out=run_cli(cache,*stage_args,'--source-licenses',str(licenses))
    assert p.returncode==0,p.stderr
    assert out['canonical_writes']==0 and out['bundle_hash']
    from kneekura_tech_hub.bundle import preflight_bundle
    preflight_bundle(store.json(out['bundle_hash']))
    p,out=run_cli(cache,'context','--index',idx,'--query','Mob','--entity','ke:mob')
    assert p.returncode==0,p.stderr
    assert out['research']['results'] and out['governed']['status']=='UNAVAILABLE'


def test_cli_registered_validation_executes_once(local,tmp_path):
    store,registry,root=local
    path=tmp_path/'registry.json'; path.write_text(json.dumps(registry))
    p,out=run_cli(store.root,'validate','run','--registry',str(path),'--kind','compile','--request-id','cli-1')
    assert p.returncode==0,p.stderr
    assert out['outcome']=='PASS' and out['receipt_hash']
    p,again=run_cli(store.root,'validate','run','--registry',str(path),'--kind','compile','--request-id','cli-1')
    assert again['receipt_hash']==out['receipt_hash']
    assert (root/'build/calls').read_text().count('called')==1


def test_cli_world_and_capabilities_do_not_claim_installed_forge(local,tmp_path):
    store,reg,root=local; template=root/'templates/empty'; template.mkdir(parents=True)
    reg['world_templates']=[str(template)]
    path=tmp_path/'reg.json'; path.write_text(json.dumps(reg))
    p,out=run_cli(store.root,'world','prepare','--registry',str(path),'--template',str(template),'--request-id','world-cli')
    assert p.returncode==0,p.stderr
    assert Path(out['world']).is_dir()
    p,out=run_cli(store.root,'capabilities')
    assert p.returncode==0,p.stderr
    assert out['runtime_status']=='NOT_PROBED' and out['ci_used'] is False
    assert out['capability_scope'] == 'STATIC_SURFACE'


def test_duplicate_keys_cannot_override_explicit_execution_authorization(local,tmp_path):
    store,reg,root=local; pth=tmp_path/'reg.json'
    pth.write_text('{"allow_gradle":false,"allow_gradle":true}')
    p,out=run_cli(store.root,'validate','run','--registry',str(pth),'--kind','compile','--request-id','unsafe')
    assert p.returncode!=0 and out is not None and 'duplicate' in str(out).lower()
    assert not (root/'build/calls').exists()

def test_all_operation_envelopes_have_the_declared_common_fields(tmp_path):
    p,out=run_cli(tmp_path/'cas','capabilities')
    assert p.returncode==0
    assert {'schema_version','request_id','profile_id','profile_hash','index_snapshot_id',
            'status','results','evidence','coverage','warnings','next_cursor'} <= set(out)


def test_cli_explicit_client_world_layout_uses_run_saves(local,tmp_path):
    store,reg,root=local
    template=root/'templates/client'; template.mkdir(parents=True)
    (template/'level.dat').write_bytes(b'fixture-world')
    reg['world_templates']=[str(template)]
    path=tmp_path/'reg.json'; path.write_text(json.dumps(reg))
    p,out=run_cli(store.root,'world','prepare','--registry',str(path),'--template',str(template),
                  '--request-id','client-world-cli','--world-name','proof-world','--layout','client')
    assert p.returncode==0,p.stderr
    assert out['world_layout']=='client'
    assert Path(out['world'])==Path(out['directory'])/'saves/proof-world'
    assert (Path(out['world'])/'level.dat').read_bytes()==b'fixture-world'
    assert (Path(out['directory'])/'.kneekura-run.json').is_file()


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_commands_parse_all_explicit_readiness_inputs(action):
    args = parser().parse_args([
        'task', action, '--request', 'request.json', '--index', 'a' * 64,
        '--run-registry', 'run.json', '--input-registry', 'input.json',
        '--blockbench-registry', 'blockbench.json', '--session', 'private.json',
        '--evidence', 'b' * 64, '--evidence', 'c' * 64,
        '--world', 'owned/world', '--run-directory', 'owned/client', '--core-configured',
    ])
    assert (args.command, args.action, args.request) == ('task', action, 'request.json')
    assert args.index == 'a' * 64
    assert (args.run_registry, args.input_registry, args.blockbench_registry) == (
        'run.json', 'input.json', 'blockbench.json')
    assert args.session == 'private.json'
    assert args.evidence == ['b' * 64, 'c' * 64]
    assert (args.world, args.run_directory, args.core_configured) == ('owned/world', 'owned/client', True)


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_parser_defaults_and_required_request(action):
    args = parser().parse_args(['task', action, '--request', 'request.json'])
    assert args.core_configured is False
    assert not args.evidence
    assert all(getattr(args, field) is None for field in (
        'index', 'run_registry', 'input_registry', 'blockbench_registry',
        'session', 'world', 'run_directory'))
    with pytest.raises(SystemExit) as exc:
        parser().parse_args(['task', action])
    assert exc.value.code == 2


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_help_documents_read_only_inputs(action, capsys):
    with pytest.raises(SystemExit) as exc:
        parser().parse_args(['task', action, '--help'])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    for flag in ('--request', '--index', '--run-registry', '--input-registry',
                 '--blockbench-registry', '--session', '--evidence', '--world',
                 '--run-directory', '--core-configured'):
        assert flag in output
    assert 'readiness' in output.lower()
    assert '32' in output


def test_task_surface_has_no_executor(capsys):
    with pytest.raises(SystemExit) as exc:
        parser().parse_args(['task', '--help'])
    assert exc.value.code == 0
    assert '{prepare,capabilities}' in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        parser().parse_args(['task', 'run', '--request', 'request.json'])
    assert exc.value.code == 2


@pytest.mark.parametrize('argv', [
    ['profile', 'prepare', '--manifest', 'profile.json'],
    ['profile', 'discover', '--workspace', '.'],
    ['search', '--index', 'index', '--query', 'Mob'],
    ['inspect', '--index', 'index', '--owner', 'Mob'],
    ['mapping', 'import', '--path', 'names.tiny', '--format', 'tiny'],
    ['interventions', '--index', 'index'],
    ['relations', '--index', 'index', '--owner', 'Mob'],
    ['context', '--index', 'index', '--query', 'Mob', '--entity', 'ke:mob'],
    ['knowledge', 'stage', '--index', 'index', '--document', 'doc', '--summary', 'x', '--actor-id', 'ai'],
    ['artifact', 'read', '--hash', 'a' * 64],
    ['validate', 'run', '--plan', 'plan.json'],
    ['world', 'prepare', '--registry', 'reg.json', '--template', 'world', '--request-id', 'r'],
    ['client-directory', 'prepare', '--registry', 'reg.json', '--template', 'client', '--request-id', 'r'],
    ['contract', 'prepare', '--registry', 'reg.json', '--index', 'index', '--world', 'world', '--scenario', 'scenario.json'],
    ['session', 'create', '--registry', 'reg.json', '--contract', 'contract.json', '--directory', 'private'],
    ['observe', '--session', 'private.json'],
    ['observe-pair', '--server-session', 'server.json', '--client-session', 'client.json', '--player-uuid', 'player'],
    ['input', 'bind', '--registry', 'reg.json'],
    ['capabilities'],
])
def test_task_registration_preserves_existing_commands(argv):
    assert parser().parse_args(argv).command == argv[0]


def test_static_capabilities_preserves_prior_payload_and_labels_scope(tmp_path):
    result = connected_cli.dispatch(parser().parse_args(['capabilities']),
                                    Store(tmp_path / 'absent'), read_json, parse_json)
    assert result == {
        'status': 'OK', 'adapter_version': runtime.ADAPTER_VERSION,
        'operations': ['profile', 'search', 'inspect', 'mapping', 'interventions', 'relations',
                       'context', 'knowledge', 'artifact', 'validate', 'world', 'client-directory',
                       'contract', 'session', 'observe', 'observe-pair', 'input', 'experiment'],
        'execution_policy': 'EXPLICIT_REGISTERED_PROVIDERS_ONLY', 'ci_used': False,
        'runtime_status': 'NOT_PROBED', 'core_status': 'OPTIONAL_EXISTING_CORE',
        'note': 'Command availability is not evidence of installed tools or successful Forge integration',
        'capability_scope': 'STATIC_SURFACE',
    }
    assert not (tmp_path / 'absent').exists()


@pytest.fixture
def task_cli_inputs(prepared, tmp_path):
    store, identifier, registry, world, _ = prepared
    session, input_registry = client_session(prepared)
    # The retained client session does not authorize a new server run.
    registry['allowed_kinds'] = ['compile']
    provider = blockbench_registry()
    request = task_request(goal='private-task-goal', constraints=['private-constraint'],
                           acceptance=['private-acceptance'])
    evidence = store.put_json({'kind': 'receipt', 'status': 'OK',
                              'body': 'private-evidence-body', 'token': 'private-evidence-token',
                              'path': '/private/evidence'})
    argv = []
    for option, value in (('request', request), ('run-registry', registry),
                          ('input-registry', input_registry), ('blockbench-registry', provider)):
        path = tmp_path / (option + '.json')
        path.write_bytes(canonical(value))
        argv.extend(['--' + option, str(path)])
    argv.extend(['--index', identifier, '--session', session['path'], '--evidence', evidence,
                 '--world', world['world'], '--run-directory', world['directory'], '--core-configured'])
    kwargs = dict(index_id=identifier, run_registry=registry, input_registry=input_registry,
                  blockbench_registry=provider, session=session, evidence_hashes=(evidence,),
                  world=world['world'], run_directory=world['directory'], core_configured=True)
    return store, request, argv, kwargs


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_dispatch_matches_real_prepared_context(action, task_cli_inputs):
    store, request, argv, kwargs = task_cli_inputs
    expected = task_context.prepare_task_context(store, request, **kwargs)
    result = connected_cli.dispatch(parser().parse_args(['task', action, *argv]),
                                    store, read_json, parse_json)
    if action == 'capabilities':
        expected = {field: expected[field] for field in ('schema_version', 'status', 'target', 'capabilities')}
        assert set(result) == {'schema_version', 'status', 'target', 'capabilities'}
    assert canonical(result) == canonical(expected)


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
@pytest.mark.parametrize('configured', [False, True])
def test_task_core_presence_is_only_an_explicit_hint(action, configured, tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://private-user:private-password@host/core')
    monkeypatch.setenv('KNEEKURA_CORE_CONFIGURED', 'true')
    request_path = tmp_path / 'request.json'
    request_path.write_bytes(canonical(task_request()))
    argv = ['task', action, '--request', str(request_path)]
    if configured:
        argv.append('--core-configured')
    store = Store(tmp_path / 'absent')
    result = connected_cli.dispatch(parser().parse_args(argv), store, read_json, parse_json)
    core = next(row for row in result['capabilities'] if row['id'] == 'core_context')
    assert core['readiness'] == ('UNKNOWN' if configured else 'NOT_CONFIGURED')
    assert core['reason_code'] == ('LIVE_STATE_NOT_PROBED' if configured else 'PROVIDER_NOT_REGISTERED')
    assert result['status'] == 'PARTIAL'
    assert not store.root.exists()


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_dispatch_never_executes_or_mutates_files(action, task_cli_inputs, tmp_path, monkeypatch):
    from kneekura_tech_hub.minecraft import blockbench, core_bridge, execution, index, input_route, native_input, storage
    store, _, argv, _ = task_cli_inputs
    def files():
        return {str(path.relative_to(tmp_path)): path.read_bytes() if path.is_file() else None
                for path in tmp_path.rglob('*')}
    before = files()
    def forbidden(*args, **kwargs):
        pytest.fail('Task dispatch attempted a write, Gradle/process, network, or native input')
    for owner, name in (
        (Store, 'put'), (Store, 'put_json'), (Store, 'pin'), (storage, 'atomic_write'),
        (storage, 'capture_profile'), (index, 'prepare_index'), (subprocess, 'Popen'), (subprocess, 'run'),
        (socket, 'create_connection'), (socket.socket, 'connect'), (execution, 'execute'),
        (execution, 'prepare_world'), (execution, 'prepare_client_directory'),
        (runtime, 'observe_live'), (runtime, 'create_session'), (runtime.BridgeClient, 'request'),
        (runtime, 'execute_registered_command'), (input_route, 'bind'),
        (input_route, 'dispatch_registered'), (native_input, 'native_exchange'),
        (core_bridge, 'context'), (core_bridge, 'stage_bundle'), (blockbench, 'probe')):
        monkeypatch.setattr(owner, name, forbidden)
    result = connected_cli.dispatch(parser().parse_args(['task', action, *argv]),
                                    store, read_json, parse_json)
    assert result['status'] == 'PARTIAL'
    assert files() == before


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_evidence_enforces_32_item_limit_and_existing_hash_rules(action, tmp_path):
    store = Store(tmp_path / 'cas')
    request_path = tmp_path / 'request.json'
    request_path.write_bytes(canonical(task_request()))
    hashes = [store.put(f'evidence {number}'.encode()) for number in range(33)]
    def dispatch_evidence(identifiers):
        flags = [arg for identifier in identifiers for arg in ('--evidence', identifier)]
        return connected_cli.dispatch(parser().parse_args([
            'task', action, '--request', str(request_path), *flags]), store, read_json, parse_json)
    assert dispatch_evidence(hashes[:32])['status'] == 'PARTIAL'
    for identifiers in (hashes, [hashes[0], hashes[0]], ['not-a-sha256']):
        with pytest.raises(ContractError):
            dispatch_evidence(identifiers)


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_file_read_errors_do_not_expose_exception_content(action, tmp_path):
    args = parser().parse_args(['task', action, '--request', '/private/request-token.json'])
    def failed_reader(path):
        raise PermissionError(f'private-exception-token at {path}')
    with pytest.raises(ContractError) as exc:
        connected_cli.dispatch(args, Store(tmp_path / 'absent'), failed_reader, parse_json)
    assert '/private/' not in str(exc.value)
    assert 'private-exception-token' not in str(exc.value)
    assert 'request' in str(exc.value).lower()


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
@pytest.mark.parametrize('option', ['run-registry', 'input-registry', 'blockbench-registry', 'session'])
def test_task_explicit_empty_file_path_is_not_ignored(action, option, tmp_path):
    request = tmp_path / 'request.json'
    request.write_bytes(canonical(task_request()))
    args = parser().parse_args(['task', action, '--request', str(request), '--' + option, ''])
    with pytest.raises(ContractError, match=f'Unable to load task {option} input'):
        connected_cli.dispatch(args, Store(tmp_path / 'absent'), read_json, parse_json)
    assert not (tmp_path / 'absent').exists()


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_subprocess_preserves_facade_and_adds_only_existing_envelope(action, task_cli_inputs):
    store, request, argv, kwargs = task_cli_inputs
    expected = task_context.prepare_task_context(store, request, **kwargs)
    if action == 'capabilities':
        expected = {field: expected[field] for field in ('schema_version', 'status', 'target', 'capabilities')}
    proc, result = run_cli(store.root, 'task', action, *argv)
    assert proc.returncode == 0, proc.stderr
    assert {field: result[field] for field in expected} == expected
    envelope_fields = {'schema_version', 'status', 'results', 'warnings', 'request_id', 'evidence',
                       'coverage', 'next_cursor', 'profile_id', 'profile_hash', 'index_snapshot_id', 'null_reasons'}
    assert set(result) == set(expected) | envelope_fields
    assert result['results'] == result['warnings'] == []
    assert result['coverage'] == {} and result['next_cursor'] is None
    assert result['request_id']
    assert result['null_reasons'] == {field: 'Not available/applicable to this operation'
                                     for field in ('profile_id', 'profile_hash', 'index_snapshot_id')}
    assert all(result[field] is None for field in result['null_reasons'])
    if action == 'capabilities':
        assert result['evidence'] == []
    public = proc.stdout + proc.stderr
    for secret in (str(store.root), str(Path(kwargs['session']['path']).parent),
                   kwargs['session']['path'], kwargs['session']['token'], kwargs['world'],
                   kwargs['run_directory'], kwargs['run_registry']['workspace'],
                   'private-task-goal', 'private-constraint', 'private-acceptance',
                   'private-evidence-body', 'private-evidence-token', '/private/evidence'):
        assert secret not in public


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
def test_task_subprocess_deep_index_returns_structured_error(action, tmp_path):
    store = Store(tmp_path / 'cas')
    identifier = store.put(deep_index_payload())
    request = tmp_path / 'request.json'
    request.write_bytes(canonical(task_request()))
    proc, result = run_cli(store.root, 'task', action, '--request', str(request), '--index', identifier)
    assert proc.returncode == 2
    assert proc.stderr == ''
    assert set(result) == {'schema_version', 'status', 'results', 'warnings', 'request_id', 'evidence',
        'coverage', 'next_cursor', 'profile_id', 'profile_hash', 'index_snapshot_id', 'null_reasons'}
    assert result['status'] == 'ERROR'
    assert result['warnings'] == ['IntegrityError: Artifact is not a valid index snapshot']
    assert result['results'] == result['evidence'] == []
    assert result['coverage'] == {} and result['next_cursor'] is None
    assert all(result[field] is None for field in ('profile_id', 'profile_hash', 'index_snapshot_id'))
    assert str(tmp_path) not in proc.stdout and 'RecursionError' not in proc.stdout


@pytest.mark.parametrize('action', ['prepare', 'capabilities'])
@pytest.mark.parametrize('fault', ['stale', 'malformed', 'request', 'contradictory'])
def test_task_subprocess_compile_evidence_error_matches_registry_entry(action, fault, prepared, tmp_path):
    store, idx, registry, _, _ = prepared
    receipt = compile_receipt_record(store, registry)
    if fault == 'request':
        receipt['request']['source_generation'] = 'c' * 64
    else:
        receipt['source_generation_after'] = None if fault == 'malformed' else 'c' * 64
    identifier = registry['build_receipt_hash'] = store.put_json(receipt)
    request = tmp_path / 'request.json'; request.write_bytes(canonical(task_request()))
    registry_path = tmp_path / 'registry.json'; registry_path.write_bytes(canonical(registry))
    base = ['task', action, '--request', str(request)]
    if fault != 'contradictory':
        base += ['--index', idx]
    results = []
    for flags in (['--evidence', identifier], ['--run-registry', str(registry_path)]):
        proc, result = run_cli(store.root, *base, *flags)
        assert proc.returncode == 2
        assert proc.stderr == ''
        assert result['status'] == 'ERROR'
        assert result['results'] == result['evidence'] == []
        assert len(result['warnings']) == 1
        assert str(tmp_path) not in proc.stdout
        result.pop('request_id')
        results.append(result)
    assert results[0] == results[1]
