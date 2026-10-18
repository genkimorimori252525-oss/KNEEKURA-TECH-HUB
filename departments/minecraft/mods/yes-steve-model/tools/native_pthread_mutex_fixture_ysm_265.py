"""Bounded GNU/Linux x86-64 default mutexes, virtual main thread only.

All workers remain deferred. No host synchronization or guest worker runs.
The 40-byte backing remains zero and opaque, even after destruction; lock state
lives only in a bounded side table. Only null attributes and normal/default
mutexes are supported. Deadlock/undefined operations stop rather than succeed.

ABI references (GNU glibc primary sources):
https://github.com/bminor/glibc/blob/master/sysdeps/x86/nptl/bits/pthreadtypes-arch.h
https://github.com/bminor/glibc/blob/master/sysdeps/x86/nptl/bits/struct_mutex.h
https://github.com/bminor/glibc/blob/master/nptl/pthread_mutex_trylock.c
"""
import copy
from native_pthread_once_fixture_ysm_265 import OnceThreadCPU

IMPORTS = {11: ('pthread_mutex_lock', 0x184d070, 0x162887e),
           13: ('pthread_mutex_unlock', 0x184d080, 0x1598bf2),
           18: ('pthread_mutex_trylock', 0x184d0a8, 0x14a1b94),
           98: ('pthread_mutex_init', 0x184d328, 0x143ce81),
           99: ('pthread_mutex_destroy', 0x184d330, 0x144844c)}
SYMBOLS = {v[0] for v in IMPORTS.values()}
SIZE = 40
EBUSY = 16


class MutexThreadCPU(OnceThreadCPU):
    MAX_MUTEX_OBJECTS = 1024
    MAX_MUTEX_CALLS = 1000000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mutex_objects = {}
        self.mutex_calls = 0

    def mutex_hit(self, a, n):
        return next((int(k) for k in getattr(self, 'mutex_objects', {})
                     if int(k) < a+n and a < int(k)+SIZE), None)

    def sync_hit(self, a, n):
        hit = self.mutex_hit(a, n)
        return hit if hit is not None else super().sync_hit(a, n)

    def sync_storage(self, a, n):
        return self.mutex_hit(a, n) is None and super().sync_storage(a, n)

    def mutex_storage(self, a):
        return (type(a) is int and 0 < a <= (1 << 64)-SIZE and a % 8 == 0 and
                super().sync_storage(a, SIZE) and super().sync_hit(a, SIZE) is None and
                all(not (a < f['sp']+32 and f['sp'] < a+SIZE)
                    for f in self.once_pending))

    @staticmethod
    def valid_mutex(obj):
        return (type(obj) is dict and set(obj) == {'kind', 'size', 'active', 'owner'} and
                obj['kind'] == 'default' and type(obj['size']) is int and obj['size'] == SIZE and
                type(obj['active']) is bool and type(obj['owner']) is int and
                obj['owner'] in (0, 1) and (obj['active'] or obj['owner'] == 0))

    def verify_mutex(self):
        for key, obj in self.mutex_objects.items():
            if not self.valid_mutex(obj) or not self.mutex_storage(int(key)):
                raise ValueError('Invalid mutex state or storage')
            if bytes(self.uc.mem_read(int(key), SIZE)) != bytes(SIZE):
                raise ValueError('Opaque mutex storage changed')

    def capture_sparse(self):
        self.verify_mutex()
        s = super().capture_sparse()
        s['mutex'] = copy.deepcopy({'objects': self.mutex_objects, 'calls': self.mutex_calls})
        return s

    def restore_sparse(self, s):
        t = copy.deepcopy(s.get('mutex', {'objects': {}, 'calls': 0}))
        if (type(t) is not dict or set(t) != {'objects', 'calls'} or
                type(t['objects']) is not dict or len(t['objects']) > self.MAX_MUTEX_OBJECTS or
                type(t['calls']) is not int or
                not len(t['objects']) <= t['calls'] <= self.MAX_MUTEX_CALLS):
            raise ValueError('Invalid mutex checkpoint')
        starts = []
        for key, obj in t['objects'].items():
            if (type(key) is not str or not key.isascii() or not key.isdecimal() or
                    len(key) > 20 or str(int(key)) != key or
                    not 0 < int(key) <= (1 << 64)-SIZE or int(key) % 8 or
                    not self.valid_mutex(obj)):
                raise ValueError('Invalid mutex object')
            starts.append(int(key))
        starts.sort()
        if any(a+SIZE > b for a, b in zip(starts, starts[1:])):
            raise ValueError('Overlapping mutex objects')
        if (t['objects'] or t['calls']) and s.get('threads', {}).get('enabled') is not True:
            raise ValueError('Mutex requires enabled thread scenario')
        # Parent validators must see the incoming semaphore/once tables, not
        # opaque controls left over from a previous state on this CPU.
        old = self.mutex_objects
        self.mutex_objects = {}
        try:
            super().restore_sparse(s)
            for a in starts:
                if (not self.mutex_storage(a) or self.unknown(a, SIZE) is not None or
                        bytes(self.uc.mem_read(a, SIZE)) != bytes(SIZE)):
                    raise ValueError('Invalid mutex backing storage')
        except Exception:
            self.mutex_objects = old
            raise
        self.mutex_objects, self.mutex_calls = t['objects'], t['calls']
        self.verify_mutex()

    def report_preservation(self):
        self.verify_mutex()
        self.emit('MUTEX_PRESERVATION', 'opaque_storage_unchanged=true',
                  'workers_executed=0', 'host_sync_called=false')
        super().report_preservation()


def model(cpu, symbol):
    cpu.demand(isinstance(cpu, MutexThreadCPU), 'MUTEX_BACKEND_REQUIRED')
    cpu.demand(cpu.threads_enabled, 'THREAD_SCENARIO_DISABLED')
    cpu.demand(symbol in SYMBOLS, 'UNSUPPORTED_MUTEX_SYMBOL')
    cpu.demand(cpu.mutex_calls < cpu.MAX_MUTEX_CALLS, 'MUTEX_CALL_BUDGET')
    a = cpu.reg('RDI')
    key = str(a)
    cpu.demand(cpu.mutex_storage(a), 'INVALID_MUTEX_STORAGE', a, SIZE)
    obj = cpu.mutex_objects.get(key)
    cpu.demand(obj is not None or cpu.mutex_hit(a, SIZE) is None,
               'OVERLAPPING_MUTEX_STORAGE', a, SIZE)
    if obj is not None:
        cpu.demand(cpu.valid_mutex(obj), 'INVALID_MUTEX_STATE', a)
        cpu.demand(bytes(cpu.uc.mem_read(a, SIZE)) == bytes(SIZE),
                   'OPAQUE_MUTEX_STORAGE_CHANGED', a, SIZE)
    result = 0
    if symbol == 'pthread_mutex_init':
        cpu.demand(cpu.reg('RSI') == 0, 'UNSUPPORTED_MUTEX_ATTRIBUTES')
        cpu.demand(obj is None or not obj['active'], 'MUTEX_ALREADY_INITIALIZED', a)
        cpu.demand(obj is not None or len(cpu.mutex_objects) < cpu.MAX_MUTEX_OBJECTS,
                   'MUTEX_OBJECT_BUDGET')
        if obj is None:
            cpu.write_model_memory(a, bytes(SIZE))
        cpu.mutex_objects[key] = {'kind': 'default', 'size': SIZE, 'active': True, 'owner': 0}
    else:
        if obj is None:
            cpu.demand(symbol in ('pthread_mutex_lock', 'pthread_mutex_trylock'),
                       'UNKNOWN_MUTEX', a)
            cpu.demand(len(cpu.mutex_objects) < cpu.MAX_MUTEX_OBJECTS, 'MUTEX_OBJECT_BUDGET')
            cpu.demand(cpu.read_known(a, SIZE) == bytes(SIZE), 'UNSUPPORTED_MUTEX_INITIAL_STATE', a, SIZE)
            obj = {'kind': 'default', 'size': SIZE, 'active': True, 'owner': 0}
            cpu.mutex_objects[key] = obj
        cpu.demand(obj['active'], 'DESTROYED_MUTEX', a)
        if symbol in ('pthread_mutex_lock', 'pthread_mutex_trylock'):
            if obj['owner']:
                cpu.demand(symbol == 'pthread_mutex_trylock', 'VIRTUAL_MUTEX_WOULD_BLOCK', a)
                result = EBUSY  # pthread return value, never errno.
            else:
                obj['owner'] = 1
        elif symbol == 'pthread_mutex_unlock':
            cpu.demand(obj['owner'] == 1, 'MUTEX_NOT_OWNED_BY_MAIN', a)
            obj['owner'] = 0
        elif symbol == 'pthread_mutex_destroy':
            cpu.demand(obj['owner'] == 0, 'MUTEX_DESTROY_LOCKED', a)
            obj['active'] = False
    cpu.mutex_calls += 1
    cpu.emit('VIRTUAL_MUTEX', symbol, f'address={a:x}', f'result={result:x}',
             'opaque_storage=true', 'virtual_main=1', 'workers_executed=0', 'host_sync_called=false')
    return result
