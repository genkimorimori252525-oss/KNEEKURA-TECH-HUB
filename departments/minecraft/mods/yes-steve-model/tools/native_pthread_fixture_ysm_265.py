"""Opt-in x86-64 guest pthread reservation model, without a worker scheduler.

A successful create reserves a real bounded pending record; it does not execute
its entry point. The declared schedule defers every worker through the main JNI
boundary. Join always stops for a scheduler. Detach does not complete a worker.
TLS values belong only to virtual main thread 1; destructors never execute.
Unsupported attributes, unknown IDs/entries and unsupported calls fail closed.
No host pthread API or target native library is loaded or called.

Integration must bind ONLY the verified __pthread_key_create weak relocation to
an intercepted gateway BEFORE initializers in a fresh opt-in scenario. This
module does not patch weak slots or infer their identity. The gateway may call
model(cpu, '__pthread_key_create'); every other weak symbol remains unsupported.
This is an explicit schedule fixture, not evidence of complete runtime behavior.
"""
import copy
import struct
from native_sync_fixture_ysm_265 import SyncGuardedCPU

IMPORTS = {26: ('pthread_create', 0x184d0e8, 0x1565534),27:('pthread_join',0x184d0f0,0x15c3d75),43:('pthread_self',0x184d170,0x15da3f7),149:('pthread_key_delete',0x184d4c0,0x1514c64),150:('pthread_key_create',0x184d4c8,0x15fa060),151:('pthread_setspecific',0x184d4d0,0x15d64a4),152:('pthread_getspecific',0x184d4d8,0x144650e),184:('pthread_detach',0x184d5d8,0x145bb1c)}
SYMBOLS = {'pthread_create', 'pthread_join', 'pthread_detach', 'pthread_self',
           'pthread_equal', 'pthread_key_create', '__pthread_key_create',
           'pthread_key_delete', 'pthread_getspecific', 'pthread_setspecific'}
SCHEDULE = 'defer-all-workers-through-main-jni-boundary'


class ThreadGuardedCPU(SyncGuardedCPU):
    MAX_THREADS = 64
    MAX_KEYS = 128
    MAX_THREAD_CALLS = 1000000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.threads_enabled = False
        self.thread_entries = []
        self.thread_records = {}
        self.thread_keys = {}
        self.thread_calls = 0
        self.thread_boundary_reached = False

    def configure_threads(self, entries):
        self.demand(not self.threads_enabled and not self.thread_records and
                    not self.thread_calls and not self.attempted,
                    'THREAD_CONFIGURATION_REQUIRES_FRESH_CPU')
        entries = list(entries)
        self.demand(0 < len(entries) <= self.MAX_THREADS and
                    len(set(entries)) == len(entries), 'INVALID_THREAD_ENTRIES')
        for entry in entries:
            self.demand(type(entry) is int and self.code_allowed(entry) and
                        self.unknown(entry, 1) is None, 'UNKNOWN_THREAD_ENTRY', entry)
        self.thread_entries = sorted(entries)
        self.threads_enabled = True
        self.emit('VIRTUAL_THREAD_SCENARIO', f'schedule={SCHEDULE}',
                  'worker_execution=false', 'host_threads=false')

    def thread_boundary(self):
        self.demand(self.threads_enabled, 'THREAD_SCENARIO_DISABLED')
        self.thread_boundary_reached = True
        result = {'schedule': SCHEDULE, 'pending': sorted(map(int, self.thread_records)),
                  'workers_executed': 0, 'runtime_complete': False,
                  'destructors_executed': False}
        self.emit('VIRTUAL_THREAD_BOUNDARY', f'pending={len(self.thread_records)}',
                  'workers_executed=0', 'runtime_complete=false')
        return result

    def capture_sparse(self):
        s = super().capture_sparse()
        s['threads'] = copy.deepcopy({'enabled': self.threads_enabled,
            'entries': self.thread_entries, 'records': self.thread_records,
            'keys': self.thread_keys, 'calls': self.thread_calls,
            'boundary': self.thread_boundary_reached, 'schedule': SCHEDULE})
        return s

    def restore_sparse(self, s):
        t = copy.deepcopy(s.get('threads', {'enabled': False, 'entries': [],
            'records': {}, 'keys': {}, 'calls': 0, 'boundary': False, 'schedule': SCHEDULE}))
        def valid_int(v, lo, hi):
            return type(v) is int and lo <= v <= hi
        if (set(t) != {'enabled', 'entries', 'records', 'keys', 'calls', 'boundary', 'schedule'}
                or type(t['enabled']) is not bool or type(t['boundary']) is not bool
                or t['schedule'] != SCHEDULE or not valid_int(t['calls'], 0, self.MAX_THREAD_CALLS)
                or type(t['entries']) is not list or type(t['records']) is not dict
                or type(t['keys']) is not dict or len(t['records']) > self.MAX_THREADS
                or len(t['keys']) > self.MAX_KEYS):
            raise ValueError('Invalid thread checkpoint')
        entries = t['entries']
        if (any(not valid_int(e, 1, (1 << 64)-1) for e in entries)
                or entries != sorted(set(entries)) or len(entries) > self.MAX_THREADS
                or any(not self.code_allowed(e) or self.unknown(e, 1) is not None for e in entries)):
            raise ValueError('Invalid thread entries')
        if (t['enabled'] and not entries) or (not t['enabled'] and
                (entries or t['records'] or t['keys'] or t['calls'] or t['boundary'])):
            raise ValueError('Invalid disabled thread state')
        if set(t['records']) != {str(i+2) for i in range(len(t['records']))}:
            raise ValueError('Invalid thread IDs')
        for r in t['records'].values():
            if (type(r) is not dict or set(r) != {'start', 'arg', 'state', 'detached', 'executed'}
                    or type(r['start']) is not int or r['start'] not in entries
                    or not valid_int(r['arg'], 0, (1 << 64)-1) or r['state'] != 'pending'
                    or type(r['detached']) is not bool or r['executed'] is not False):
                raise ValueError('Invalid deferred thread record')
        if set(t['keys']) != {str(i) for i in range(len(t['keys']))}:
            raise ValueError('Invalid TLS key IDs')
        for k in t['keys'].values():
            if (type(k) is not dict or set(k) != {'active', 'value', 'destructor'}
                    or type(k['active']) is not bool or not valid_int(k['value'], 0, (1 << 64)-1)
                    or not valid_int(k['destructor'], 0, (1 << 64)-1)
                    or (k['destructor'] and not self.code_allowed(k['destructor']))
                    or (not k['active'] and k['value'])):
                raise ValueError('Invalid TLS key')
        if t['calls'] < len(t['records']) + len(t['keys']):
            raise ValueError('Invalid thread call accounting')
        super().restore_sparse(s)
        self.threads_enabled = t['enabled']; self.thread_entries = entries
        self.thread_records = t['records']; self.thread_keys = t['keys']
        self.thread_calls = t['calls']; self.thread_boundary_reached = t['boundary']


def model(cpu, symbol):
    cpu.demand(isinstance(cpu, ThreadGuardedCPU), 'THREAD_BACKEND_REQUIRED')
    cpu.demand(cpu.threads_enabled, 'THREAD_SCENARIO_DISABLED')
    cpu.demand(symbol in SYMBOLS, 'UNSUPPORTED_PTHREAD_SYMBOL')
    cpu.demand(cpu.thread_calls < cpu.MAX_THREAD_CALLS, 'THREAD_CALL_BUDGET')
    a, b = cpu.reg('RDI'), cpu.reg('RSI')
    result = 0
    if symbol == 'pthread_create':
        entry, arg = cpu.reg('RDX'), cpu.reg('RCX')
        cpu.demand(b == 0, 'UNMODELED_THREAD_ATTRIBUTES', b)
        cpu.demand(entry in cpu.thread_entries and cpu.code_allowed(entry) and
                   cpu.unknown(entry, 1) is None, 'UNKNOWN_THREAD_ENTRY', entry)
        cpu.demand(cpu.sync_storage(a, 8), 'INVALID_THREAD_OUTPUT', a, 8)
        cpu.demand(len(cpu.thread_records) < cpu.MAX_THREADS, 'THREAD_RECORD_BUDGET')
        tid = len(cpu.thread_records) + 2
        cpu.write_model_memory(a, struct.pack('<Q', tid))
        cpu.thread_records[str(tid)] = {'start': entry, 'arg': arg,
            'state': 'pending', 'detached': False, 'executed': False}
    elif symbol == 'pthread_self':
        result = 1
    elif symbol in ('pthread_equal', 'pthread_join', 'pthread_detach'):
        cpu.demand(a == 1 or str(a) in cpu.thread_records, 'UNKNOWN_THREAD', a)
        if symbol == 'pthread_equal':
            cpu.demand(b == 1 or str(b) in cpu.thread_records, 'UNKNOWN_THREAD', b)
            result = int(a == b)
        else:
            cpu.demand(a != 1, 'MAIN_THREAD_LIFECYCLE_UNSUPPORTED')
            r = cpu.thread_records[str(a)]
            cpu.demand(not r['detached'], 'THREAD_NOT_JOINABLE', a)
            if symbol == 'pthread_join':
                cpu.demand(False, 'THREAD_SCHEDULER_REQUIRED', a)
            r['detached'] = True
    elif symbol in ('pthread_key_create', '__pthread_key_create'):
        cpu.demand(cpu.sync_storage(a, 4), 'INVALID_TLS_KEY_OUTPUT', a, 4)
        cpu.demand(b == 0 or (cpu.code_allowed(b) and cpu.unknown(b, 1) is None),
                   'UNKNOWN_TLS_DESTRUCTOR', b)
        cpu.demand(len(cpu.thread_keys) < cpu.MAX_KEYS, 'TLS_KEY_BUDGET')
        key = len(cpu.thread_keys)
        cpu.write_model_memory(a, struct.pack('<I', key))
        cpu.thread_keys[str(key)] = {'active': True, 'value': 0, 'destructor': b}
    else:
        # SysV x86-64 pthread_key_t is unsigned int; high register bits
        # are not part of this argument. TLS values remain full pointers.
        a &= 0xffffffff
        key = cpu.thread_keys.get(str(a))
        cpu.demand(key is not None and key['active'], 'UNKNOWN_TLS_KEY', a)
        if symbol == 'pthread_getspecific':
            result = key['value']
        elif symbol == 'pthread_setspecific':
            key['value'] = b
        elif symbol == 'pthread_key_delete':
            key['active'] = False; key['value'] = 0
    cpu.thread_calls += 1
    cpu.emit('VIRTUAL_PTHREAD', symbol, f'result={result:x}',
             f'pending_workers={len(cpu.thread_records)}', 'workers_executed=0',
             'host_thread_called=false', 'runtime_complete=false')
    return result
