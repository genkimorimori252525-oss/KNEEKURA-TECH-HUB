"""Declared absent secure_getenv inputs; no present values or host environment I/O.

An absent key is null regardless of secure-execution policy. Unknown keys stop.
Import identity is verified by the shared lazy-import dispatcher before this model.
Legacy checkpoints retain their historical GLIBCXX_TUNABLES count separately;
that count is not presented as a newly observed per-lookup ledger.
"""
import copy
import re
from dataclasses import dataclass

DEFAULT = ('GLIBCXX_TUNABLES',)
IMPORT = {'symbol': 'secure_getenv', 'index': 121, 'slot': 0x184d3e0, 'stub': 0x14bdbd9}
MAX_LOOKUPS = 4096


def require(condition, message):
    if not condition: raise ValueError(message)


def valid_key(key):
    return type(key) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}', key) is not None


def configuration(keys):
    require(type(keys) in (list, tuple) and len(keys) <= 32, 'Require bounded absent-key list')
    require(all(valid_key(k) for k in keys), 'Malformed absent environment key')
    require(len(set(keys)) == len(keys), 'Duplicate absent environment key')
    return tuple(sorted(set(DEFAULT).union(keys)))


@dataclass(frozen=True)
class EnvironmentDeclaration:
    absent_keys: tuple
    legacy_calls: int
    legacy_extension: bool


def initial(keys=DEFAULT, legacy_calls=0, legacy_extension=False):
    return {'absent_keys': list(keys), 'declaration': list(keys), 'import': dict(IMPORT),
            'legacy_calls': legacy_calls, 'legacy_extension': legacy_extension, 'lookups': []}


def validate(state, count, declaration=None):
    require(type(state) is dict and set(state) == {'absent_keys', 'declaration', 'import', 'legacy_calls', 'legacy_extension', 'lookups'}, 'Invalid environment state fields')
    keys = state['absent_keys']
    require(type(keys) is list and 1 <= len(keys) <= 33 and all(valid_key(k) for k in keys), 'Invalid environment keys')
    require(keys == sorted(set(keys)) and set(DEFAULT).issubset(keys), 'Invalid environment declaration')
    require(type(state['declaration']) is list and state['declaration'] == keys, 'Environment declaration mismatch')
    require(type(state['import']) is dict and state['import'] == IMPORT and all(type(state['import'][k]) is type(v) for k, v in IMPORT.items()), 'Environment import provenance mismatch')
    legacy = state['legacy_calls']; extension = state['legacy_extension']; ledger = state['lookups']
    require(type(legacy) is int and 0 <= legacy <= MAX_LOOKUPS and type(extension) is bool, 'Invalid environment legacy history')
    require(type(ledger) is list and len(ledger) <= MAX_LOOKUPS and all(type(k) is str and k in keys for k in ledger), 'Invalid environment lookup ledger')
    require(type(count) is int and count == legacy + len(ledger) and count <= MAX_LOOKUPS, 'Environment lookup count mismatch')
    anchor = EnvironmentDeclaration(tuple(keys), legacy, extension)
    require(declaration is None or declaration == anchor, 'Environment immutable declaration mismatch')
    return anchor


def initialize(cpu):
    cpu.environment = initial()
    cpu.environment_declaration = validate(cpu.environment, 0)
    cpu.environment_restored = False


def configure(cpu, keys, *, allow_legacy_extension=False):
    require(type(allow_legacy_extension) is bool, 'Invalid environment extension flag')
    desired = configuration(keys)
    validate(cpu.environment, cpu.environment_model_calls, cpu.environment_declaration)
    if desired == cpu.environment_declaration.absent_keys: return
    require(cpu.environment_declaration.absent_keys == DEFAULT, 'Environment scenario already declared')
    require(not cpu.attempted, 'Configure environment before executing instructions')
    require(not cpu.environment_restored or allow_legacy_extension, 'Checkpoint requires explicit environment extension')
    state = copy.deepcopy(cpu.environment)
    state['absent_keys'] = state['declaration'] = list(desired)
    state['legacy_extension'] = cpu.environment_restored
    anchor = validate(state, cpu.environment_model_calls)
    cpu.environment = state; cpu.environment_declaration = anchor
    if cpu.environment_restored:
        cpu.emit('CHECKPOINT_SCENARIO_EXTENSION', 'kind=absent-environment-keys-v1', 'equivalent_scenario=false', 'host_environment_read=false')


def snapshot(cpu):
    validate(cpu.environment, cpu.environment_model_calls, cpu.environment_declaration)
    return copy.deepcopy(cpu.environment)


def prepare_restore(cpu, state, count, *, missing=False):
    validate(cpu.environment, cpu.environment_model_calls, cpu.environment_declaration)
    restored = initial(legacy_calls=count) if missing else copy.deepcopy(state)
    anchor = validate(restored, count)
    require(cpu.environment_declaration.absent_keys == DEFAULT or cpu.environment_declaration == anchor,
            'Checkpoint environment configuration mismatch')
    return restored, anchor


def model(cpu, symbol):
    require(symbol == IMPORT['symbol'], 'Unsupported environment operation')
    validate(cpu.environment, cpu.environment_model_calls, cpu.environment_declaration)
    key = cpu.ascii(cpu.reg('RDI'))
    cpu.demand(valid_key(key), 'MALFORMED_ENVIRONMENT_KEY')
    cpu.demand(key in cpu.environment_declaration.absent_keys, 'UNMODELED_ENVIRONMENT_KEY')
    cpu.demand(cpu.environment_model_calls < MAX_LOOKUPS, 'ENVIRONMENT_LOOKUP_LIMIT')
    cpu.environment['lookups'].append(key); cpu.environment_model_calls += 1
    cpu.emit('VIRTUAL_ENVIRONMENT_ABSENT', key, 'host_environment_read=false')
    return 0
