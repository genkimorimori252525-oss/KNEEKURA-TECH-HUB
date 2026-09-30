"""Bounded read-only pairing of independently authenticated dedicated observers.

This joins evidence in the existing Store. It never launches or connects a game,
sends input, changes configuration, invents a shared epoch, or asserts gameplay.
"""
from __future__ import annotations

import math
from pathlib import Path
import re
import time
import uuid

from . import runtime, verification
from .storage import ContractError, Store, key_for, valid_hash


def _session(path: str, role: str) -> dict:
    session = runtime.load_session(path)
    directory = Path(session.get('directory', ''))
    if (not directory.is_absolute() or directory.is_symlink() or not directory.is_dir()
            or directory != directory.resolve() or Path(session['path']) != directory/'session.json'
            or Path(session.get('endpoint_path', '')) != directory/'endpoint.json'):
        raise ContractError('Pairing requires each canonical private run session')
    contract = session.get('contract', {})
    if (contract.get('schema_version') != 2 or contract.get('session_role') != role
            or verification._identity_errors(contract, {'identity': contract})):
        raise ContractError('Pairing requires exact dedicated server and receiver contracts')
    policy = verification.validate_connection_policy(contract.get('connection_policy'))
    if (key_for(policy) != contract.get('connection_policy_hash')
            or session.get('connection_policy') != policy):
        raise ContractError('Session connection policy differs from its captured contract')
    versions = session.get('expected_runtime')
    if (not isinstance(versions, dict) or set(versions) != {'minecraft','forge','java_major'}
            or versions['minecraft'] != '1.20.1' or type(versions['java_major']) is not int
            or versions['java_major'] != 17 or not isinstance(versions['forge'], str)
            or not re.fullmatch(r'47\.\d+\.\d+', versions['forge'])):
        raise ContractError('Pairing requires exact Forge 1.20.1 / Java17 versions')
    return session


def _row(contract: dict, raw: dict, player: str, dimension: str) -> dict:
    checked = verification.evaluate_observation(contract, raw)
    if checked['status'] != 'OK' or raw.get('atomic') is not False:
        raise ContractError('Pair capture is incomplete or claims an atomic snapshot')
    rows = raw.get('entities', [])
    if (len(rows) != 1 or rows[0].get('uuid') != player or rows[0].get('dimension') != dimension
            or raw.get('entities_truncated', False) is not False):
        raise ContractError('Pair capture requires one untruncated selected player')
    row = rows[0]
    state = row.get('staff_state')
    side = 'logical_client' if contract['session_role'] == 'dedicated_client' else 'logical_server'
    if (not isinstance(state, dict) or state.get('applicable') is not True
            or state.get('observation_side') != side):
        raise ContractError('Independent side-specific staff state is unavailable')
    verification.validate_connection(contract, row.get('connection'))
    return row


def observe_pair(store: Store, *, server_session: str, client_session: str,
                 player_uuid: str, dimension: str = 'minecraft:overworld',
                 timeout: float = 10, screenshot: bool = False) -> dict:
    """Capture server-before/client/server-after once within one total deadline.

    Both sessions remain independent authorities. Socket tuple equality proves
    the observed local TCP pairing, not receipt of a particular gameplay packet
    or causal synchronization. Raw captures remain retained even if pairing fails.
    """
    if (type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 30
            or type(screenshot) is not bool):
        raise ContractError('Pair capture requires a finite deadline of at most 30 seconds')
    try:
        if not isinstance(player_uuid, str) or str(uuid.UUID(player_uuid)) != player_uuid:
            raise ValueError()
    except ValueError:
        raise ContractError('Canonical selected player UUID required') from None
    if (not isinstance(dimension, str) or len(dimension) > 256
            or not re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+', dimension)):
        raise ContractError('Explicit resource-location dimension required')
    started = time.monotonic(); deadline = started + timeout
    server = _session(server_session, 'dedicated_server')
    client = _session(client_session, 'dedicated_client')
    sc, cc = server['contract'], client['contract']
    if (server['path'] == client['path'] or server['directory'] == client['directory']
            or sc['run_id'] == cc['run_id'] or sc['session_epoch'] == cc['session_epoch']):
        raise ContractError('Server and receiver require distinct owned runs and epochs')
    server_hash = key_for(sc)
    if cc['server_contract_hash'] != server_hash or store.json(server_hash) != sc:
        raise ContractError('Receiver does not reference the exact retained server contract')
    if (server['expected_runtime'] != client['expected_runtime']
            or sc['build_artifact_hash'] != cc['build_artifact_hash']
            or sc['source_revision'] != cc['source_revision']
            or sc['connection_policy_hash'] != cc['connection_policy_hash']
            or sc['connection_policy'] != cc['connection_policy']
            or cc['player_uuid'] != player_uuid
            or player_uuid not in sc['connection_policy']['player_uuids']):
        raise ContractError('Pair target, selected player, runtime artifact or registered policy differs')
    # Different profile/config/path/dirty hashes are preserved, never collapsed.
    query = {'entity_uuids':[player_uuid], 'dimension':dimension, 'limit':1, 'staff_state':True}
    captures = []
    for label, session, operation in [('server_before',server,'observe'),
                                      ('client',client,'client'), ('server_after',server,'observe')]:
        remaining = deadline-time.monotonic()
        if remaining <= 0: raise ContractError('Pair capture deadline expired; no automatic retry')
        request = dict(query)
        if operation == 'client': request['screenshot'] = screenshot
        begin = time.monotonic()-started
        result = runtime.observe_live(store, session['path'], operation=operation,
                                      query=request, timeout=min(remaining,30))
        end = time.monotonic()-started
        if time.monotonic() >= deadline:
            raise ContractError('Pair capture deadline expired; no automatic retry')
        if (result.get('status') != 'OK'
                or result.get('evidence_level') != 'AUTHENTICATED_LIVE_OBSERVER'):
            raise ContractError('Pairing requires fresh authenticated complete observations')
        raw_hash = valid_hash(result.get('artifact_hash'))
        hello_hash = valid_hash(result.get('handshake_hash'))
        raw, hello = store.json(raw_hash), store.json(hello_hash)
        contract = session['contract']
        if (hello.get('ready') is not True or verification._identity_errors(contract, hello)
                or any(hello.get(k) != v for k,v in session['expected_runtime'].items()
                       if k != 'java_major') or type(hello.get('java_major')) is not int or hello['java_major'] != 17):
            # Runtime uses the short 'forge' key, matching expected_runtime.
            raise ContractError('Pair handshake identity/version/readiness differs')
        row = _row(contract, raw, player_uuid, dimension)
        captures.append({'role':label,'artifact_hash':raw_hash,'handshake_hash':hello_hash,
                         'controller_elapsed_start':begin,'controller_elapsed_end':end,
                         'row':row,'raw':raw})
    before, receiving, after = captures
    server_connection = before['row']['connection']
    client_connection = receiving['row']['connection']
    if (server_connection != after['row']['connection']
            or client_connection != receiving['raw'].get('connection')
            or server_connection['local'] != client_connection['remote']
            or server_connection['remote'] != client_connection['local']):
        raise ContractError('Game socket tuple or connection changed during paired observation')
    if before['raw']['server_tick_end'] > after['raw']['server_tick_start']:
        raise ContractError('Server capture intervals moved backwards')
    references = [{k:v for k,v in item.items() if k not in ('row','raw')} for item in captures]
    record = {'schema_version':1,'kind':'dedicated-observer-pair','atomic':False,
              'server_contract_hash':server_hash,'client_contract_hash':key_for(cc),
              'connection_policy_hash':sc['connection_policy_hash'], 'player_uuid':player_uuid,
              'dimension':dimension, 'client_directory_id':cc['run_directory_id'],
              'target_build_binding':'MATCHING_RUNTIME_ARTIFACT_AND_REVISION',
              'world_binding':{'source':'authenticated_server_contract','world_id':sc['world_id'],
                               'world_seed':sc['world_seed'],'world_template_hash':sc['world_template_hash']},
              'samples':references,'synchronization_verdict':'NOT_RUN',
              'evidence_level':'AUTHENTICATED_PAIRED_OBSERVATIONS',
              'note':'Independent same-connection state evidence; no gameplay, packet-causality or latency assertion'}
    # Pin both contracts and every raw source; never retain private session bytes.
    client_hash = store.put_json(cc)
    artifact = store.put_json(record)
    for h in [artifact,server_hash,client_hash,*[x[k] for x in references for k in ('artifact_hash','handshake_hash')]]:
        store.pin(h, 'dedicated-pair:'+artifact)
    return {'schema_version':1,'status':'OK','outcome':'NOT_RUN','artifact_hash':artifact,
            'evidence_level':record['evidence_level'],'atomic':False,'retry_allowed':False,
            'note':record['note']}
