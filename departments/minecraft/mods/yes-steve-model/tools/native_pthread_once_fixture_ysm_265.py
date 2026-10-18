"""Bounded pthread_once with real guarded guest callbacks, never host calls.

Control storage stays opaque and physically zero. Completion exists only in the
side table after a callback returns through the checked gateway. A stop during
a callback leaves it running; it must never be reported as completed.
"""
import copy
import struct
import time
from unicorn import UC_PROT_READ, UC_PROT_EXEC
from native_thread_support_gate_ysm_265 import ThreadLinkedCPU
from native_unicorn_guarded_ysm_265 import STACK, STACK_SIZE

GATE = 0x770000001000
PAGE = b'\xc3' + bytes(4095)
SAVED = ('RBX', 'RBP', 'R12', 'R13', 'R14', 'R15')
IMPORTS = {12: ('pthread_once', 0x184d078, 0x14ea804)}


class OnceThreadCPU(ThreadLinkedCPU):
    MAX_ONCE_OBJECTS = 1024
    MAX_ONCE_PENDING = 64
    MAX_ONCE_CALLS = 1000000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.once_objects = {}
        self.once_pending = []
        self.once_calls = 0
        self.uc.mem_map(GATE, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.uc.mem_write(GATE, PAGE)

    def once_hit(self, a, n):
        return next((int(k) for k in getattr(self, 'once_objects', {})
                     if int(k) < a+n and a < int(k)+4), None)

    def sync_hit(self, a, n):
        hit = self.once_hit(a, n)
        return hit if hit is not None else super().sync_hit(a, n)

    def sync_storage(self, a, n):
        # Also prevents semaphore/thread output models claiming once storage.
        return self.once_hit(a, n) is None and super().sync_storage(a, n)

    def code_allowed(self, a, n=1):
        return (a == GATE and n == 1 and bool(self.once_pending)) or super().code_allowed(a, n)

    def unknown(self, a, n):
        if a == GATE and n == 1:
            return None
        return super().unknown(a, n)

    def _write(self, uc, access, a, n, value, user):
        if GATE < a+n and a < GATE+4096:
            for at in range(max(a, GATE), min(a+n, GATE+4096)):
                self.journal.append((at, bytes(uc.mem_read(at, 1))))
            self.fail('ONCE_GATE_WRITE_BLOCKED', a, n)
            return
        super()._write(uc, access, a, n, value, user)

    def _code(self, uc, address, size, user):
        if address != GATE:
            return super()._code(uc, address, size, user)
        if self.stop:
            return
        if not self.code_allowed(address, size):
            self.fail('UNEXPECTED_ONCE_RETURN', address)
            return
        if time.monotonic() > self.deadline:
            self.fail('TIME_BUDGET', address)
            return
        self.pc = address
        self.current_raw = b'\xc3'
        self.attempted += 1
        self.pending = 'pthread-once-return'
        uc.emu_stop()

    def once_function(self, address):
        return (type(address) is int and address > 0 and
                any(lo <= address < hi for lo, hi in self.exec_ranges) and
                self.unknown(address, 1) is None)

    def begin_once(self, sp, target):
        self.demand(self.threads_enabled, 'THREAD_SCENARIO_DISABLED')
        self.demand(self.once_calls < self.MAX_ONCE_CALLS, 'ONCE_CALL_BUDGET')
        self.demand(type(sp) is int and STACK <= sp and sp+32 <= STACK+STACK_SIZE
                    and sp % 16 == 0 and self.reg('RSP') == sp,
                    'INVALID_ONCE_FRAME', sp)
        self.demand(not self.once_pending or sp+32 <= self.once_pending[-1]['sp']+24,
                    'OVERLAPPING_ONCE_CALLBACK_FRAME', sp)
        self.demand(type(target) is int and self.return_target_allowed(target, sp+32),
                    'INVALID_ONCE_RETURN', target)
        self.demand(int.from_bytes(self.read_known(sp+24, 8), 'little') == target,
                    'ONCE_RETURN_FRAME_MISMATCH', sp+24)
        a, callback = self.reg('RDI'), self.reg('RSI')
        self.demand(self.once_function(callback), 'UNKNOWN_ONCE_CALLBACK', callback)
        self.demand(a % 4 == 0 and super().sync_storage(a, 4), 'INVALID_ONCE_STORAGE', a, 4)
        self.demand(super().sync_hit(a, 4) is None, 'OVERLAPPING_ONCE_STORAGE', a, 4)
        self.demand(not (a < sp+32 and sp < a+4) and
                    all(not (a < f['sp']+32 and f['sp'] < a+4) for f in self.once_pending),
                    'ONCE_STORAGE_OVERLAPS_FRAME', a, 4)
        obj = self.once_objects.get(str(a))
        self.demand(obj is not None or self.once_hit(a, 4) is None,
                    'OVERLAPPING_ONCE_STORAGE', a, 4)
        if obj is not None:
            self.demand(obj['state'] == 'done', 'VIRTUAL_ONCE_WOULD_BLOCK', a)
            self.once_calls += 1
            self.reg('RAX', 0); self.reg('RSP', sp+32); self.reg('RIP', target)
            return
        self.demand(len(self.once_objects) < self.MAX_ONCE_OBJECTS, 'ONCE_OBJECT_BUDGET')
        self.demand(len(self.once_pending) < self.MAX_ONCE_PENDING, 'ONCE_PENDING_BUDGET')
        self.demand(self.read_known(a, 4) == bytes(4), 'UNSUPPORTED_ONCE_INITIAL_STATE', a, 4)
        self.demand(self.private_allowed(sp+24, 8) and self.sync_hit(sp+24, 8) is None,
                    'INVALID_ONCE_OUTPUT_FRAME', sp+24, 8)
        frame = {'control': a, 'callback': callback, 'sp': sp, 'target': target,
                 'saved': {r: self.reg(r) for r in SAVED}}
        self.write_private(sp+24, struct.pack('<Q', GATE))
        self.once_objects[str(a)] = {'state': 'running', 'callback': callback}
        self.once_pending.append(frame)
        self.once_calls += 1
        self.reg('RSP', sp+24); self.reg('RIP', callback)
        self.emit('GUEST_ONCE_CALLBACK_BEGIN', f'control={a:x}', f'callback={callback:x}',
                  'host_code_executed=false', 'completion=false')

    def model(self, kind):
        if kind != 'pthread-once-return':
            return super().model(kind)
        self.demand(bool(self.once_pending), 'UNEXPECTED_ONCE_RETURN')
        f = self.once_pending[-1]
        self.demand(self.reg('RIP') == GATE and self.reg('RSP') == f['sp']+32,
                    'ONCE_CALLBACK_STACK_MISMATCH')
        self.demand(all(self.reg(r) == f['saved'][r] for r in SAVED),
                    'ONCE_CALLBACK_CALLEE_REGISTER_MISMATCH')
        self.demand(self.reg('DF') == 0, 'ONCE_CALLBACK_DIRECTION_FLAG')
        self.demand(self.return_target_allowed(f['target'], f['sp']+32), 'INVALID_ONCE_RETURN')
        self.write_private(f['sp']+24, struct.pack('<Q', f['target']))
        self.once_objects[str(f['control'])]['state'] = 'done'
        self.once_pending.pop()
        self.reg('RAX', 0); self.reg('RIP', f['target'])
        self.emit('GUEST_ONCE_CALLBACK_COMPLETE', f'control={f["control"]:x}',
                  'guest_callback_returned=true', 'host_code_executed=false')

    def verify_once(self):
        if bytes(self.uc.mem_read(GATE, 4096)) != PAGE:
            raise ValueError('Once gateway changed')
        if any(bytes(self.uc.mem_read(int(k), 4)) != bytes(4) for k in self.once_objects):
            raise ValueError('Opaque once storage changed')

    def capture_sparse(self):
        self.verify_once()
        s = super().capture_sparse()
        s['once'] = copy.deepcopy({'objects': self.once_objects,
                                  'pending': self.once_pending, 'calls': self.once_calls})
        return s

    def restore_sparse(self, s):
        t = copy.deepcopy(s.get('once', {'objects': {}, 'pending': [], 'calls': 0}))
        def integer(v, lo=0, hi=(1 << 64)-1):
            return type(v) is int and lo <= v <= hi
        if (type(t) is not dict or set(t) != {'objects', 'pending', 'calls'} or
                type(t['objects']) is not dict or type(t['pending']) is not list or
                len(t['objects']) > self.MAX_ONCE_OBJECTS or len(t['pending']) > self.MAX_ONCE_PENDING or
                not integer(t['calls'], len(t['objects']), self.MAX_ONCE_CALLS)):
            raise ValueError('Invalid once checkpoint')
        objects, pending = t['objects'], t['pending']
        starts = []
        for key, obj in objects.items():
            if not isinstance(key, str) or not key.isascii() or not key.isdecimal() or len(key) > 20:
                raise ValueError('Invalid once control')
            a = int(key)
            if (str(a) != key or not integer(a, 4, (1 << 64)-4) or a % 4 or
                    type(obj) is not dict or set(obj) != {'state', 'callback'} or
                    obj['state'] not in ('running', 'done') or not self.once_function(obj['callback'])):
                raise ValueError('Invalid once object')
            starts.append(a)
        starts.sort()
        if any(a+4 > b for a, b in zip(starts, starts[1:])):
            raise ValueError('Overlapping once controls')
        controls = []
        for f in pending:
            if (type(f) is not dict or set(f) != {'control', 'callback', 'sp', 'target', 'saved'} or
                    not integer(f['control']) or not integer(f['callback']) or
                    not integer(f['sp'], STACK, STACK+STACK_SIZE-32) or f['sp'] % 16 or
                    not integer(f['target'], 1) or
                    type(f['saved']) is not dict or set(f['saved']) != set(SAVED) or
                    any(not integer(v) for v in f['saved'].values())):
                raise ValueError('Invalid once pending frame')
            obj = objects.get(str(f['control']))
            if obj != {'state': 'running', 'callback': f['callback']}:
                raise ValueError('Once pending object mismatch')
            # A nested callback may return to the outer callback gateway.
            if not (self.return_target_allowed(f['target'], f['sp']+32) or
                    (f['target'] == GATE and controls)):
                raise ValueError('Invalid once return target')
            if controls and f['sp']+32 > pending[len(controls)-1]['sp']+24:
                raise ValueError('Overlapping once callback frames')
            controls.append(f['control'])
        if len(set(controls)) != len(controls) or set(controls) != {
                int(k) for k, o in objects.items() if o['state'] == 'running'}:
            raise ValueError('Missing or duplicate pending once callback')
        if objects and not s.get('threads', {}).get('enabled'):
            raise ValueError('Once requires enabled thread scenario')
        super().restore_sparse(s)
        for a in starts:
            if (not super().sync_storage(a, 4) or super().sync_hit(a, 4) is not None or
                    self.unknown(a, 4) is not None or bytes(self.uc.mem_read(a, 4)) != bytes(4) or
                    any(a < f['sp']+32 and f['sp'] < a+4 for f in pending)):
                raise ValueError('Invalid once backing storage')
        for f in pending:
            if (not self.private_allowed(f['sp']+24, 8) or self.sync_hit(f['sp']+24, 8) is not None or
                    self.unknown(f['sp']+24, 8) is not None or
                    bytes(self.uc.mem_read(f['sp']+24, 8)) != struct.pack('<Q', GATE)):
                raise ValueError('Invalid once callback return storage')
        self.once_objects, self.once_pending, self.once_calls = objects, pending, t['calls']
        self.verify_once()

    def report_preservation(self):
        self.verify_once()
        super().report_preservation()
