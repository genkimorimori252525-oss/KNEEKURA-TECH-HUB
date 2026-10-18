"""Own-byte pthread_once tests; never loads the target native library."""
import copy
import io
import json
import struct
import unittest
from native_pthread_once_fixture_ysm_265 import OnceThreadCPU, GATE, SAVED
from native_unicorn_guarded_ysm_265 import ModelHalt, SP, RETURN
from native_guarded_checkpoint_ysm_265 import capture, restore
from native_batched_cpu_ysm_265 import BatchedMixin

class BatchedOnce(BatchedMixin, OnceThreadCPU):
    pass

CODE = 0x100000
FRAME = SP-24
CONTROL = SP+128
OUTPUT = SP+192


class OnceTests(unittest.TestCase):
    def cpu(self, callback=b'\xc3', limit=30, cls=OnceThreadCPU):
        c = cls(io.StringIO(), 'heap', limit=limit)
        c.add_image(CODE, callback)
        c.protect_image()
        # The weak gateway verification belongs to fresh loader integration.
        # Own-byte tests enable only the explicit isolated thread fixture.
        c.verify_thread_gate = lambda: None
        c.configure_threads([CODE])
        c.write_private(FRAME, struct.pack('<QQQQ', 0, 0, 12, RETURN))
        c.write_private(CONTROL, bytes(4))
        c.write_private(OUTPUT, bytes(8))
        c.reg('RSP', FRAME)
        c.reg('RDI', CONTROL); c.reg('RSI', CODE)
        return c

    def begin(self, c):
        c.begin_once(FRAME, RETURN)

    def test_actual_guest_side_effect_then_done_without_repeat(self):
        # movabs rax,OUTPUT; inc qword [rax]; ret
        code = b'\x48\xb8'+struct.pack('<Q', OUTPUT)+b'\x48\xff\x00\xc3'
        c = self.cpu(code); self.begin(c)
        self.assertEqual(c.once_objects[str(CONTROL)]['state'], 'running')
        self.assertEqual(c.run(c.reg('RIP'))['reason'], 'ENTRY_RETURN')
        self.assertEqual(int.from_bytes(c.read_known(OUTPUT, 8), 'little'), 1)
        self.assertEqual(c.once_objects[str(CONTROL)]['state'], 'done')
        self.assertEqual(c.reg('RAX'), 0)
        self.assertEqual(c.reg('RSP'), SP+8)
        self.assertEqual(bytes(c.uc.mem_read(CONTROL, 4)), bytes(4))
        c.stop = None; c.reg('RSP', FRAME)
        self.begin(c)
        self.assertEqual(c.reg('RIP'), RETURN)
        self.assertEqual(c.once_pending, [])
        self.assertEqual(int.from_bytes(c.read_known(OUTPUT, 8), 'little'), 1)

    def test_invalid_requests_atomic(self):
        cases = [('RDI', CONTROL+1), ('RSI', 0), ('RSI', CONTROL), ('RDI', 0)]
        for reg, value in cases:
            c = self.cpu(); c.reg(reg, value)
            before = bytes(c.uc.mem_read(FRAME, 32))
            with self.assertRaises(ModelHalt): self.begin(c)
            self.assertEqual(c.once_objects, {})
            self.assertEqual(c.once_pending, [])
            self.assertEqual(c.once_calls, 0)
            self.assertEqual(bytes(c.uc.mem_read(FRAME, 32)), before)
        c = self.cpu(); c.write_private(CONTROL, b'\x02\0\0\0')
        with self.assertRaisesRegex(ModelHalt, 'INITIAL_STATE'): self.begin(c)
        self.assertFalse(c.once_objects)

    def test_callback_failure_never_completes(self):
        for code, reason in [(b'\xfd\xc3', 'DIRECTION_FLAG'),
                             (b'\x48\xff\xc3\xc3', 'CALLEE_REGISTER'),
                             (b'\x48\x31\xc0\xff\xe0', 'EXTERNAL_OR_NULL_TARGET'),
                             (b'\xc2\x08\x00', 'STACK_MISMATCH'),
                             (b'\xeb\xfe', 'INSTRUCTION_BUDGET')]:
            c = self.cpu(code); self.begin(c)
            stop = c.run(CODE)
            self.assertIn(reason, stop['reason'])
            self.assertEqual(c.once_objects[str(CONTROL)]['state'], 'running')
            self.assertEqual(len(c.once_pending), 1)

    def test_reentrant_would_block(self):
        c = self.cpu(); self.begin(c)
        nested = FRAME-64
        c.write_private(nested, struct.pack('<QQQQ', 0, 0, 12, CODE))
        c.reg('RSP', nested)
        with self.assertRaisesRegex(ModelHalt, 'WOULD_BLOCK'):
            c.begin_once(nested, CODE)
        self.assertEqual(c.once_calls, 1)
        self.assertEqual(len(c.once_pending), 1)

    def test_opaque_reads_writes_copies_and_mapping(self):
        c = self.cpu(); self.begin(c)
        for action in (lambda: c.read_known(CONTROL, 4),
                       lambda: c.write_private(CONTROL, bytes(4)),
                       lambda: c.write_model_memory(CONTROL, bytes(4)),
                       lambda: c.vm_change(CONTROL, 4, remove=True),
                       lambda: c.vm_advice(CONTROL, 4, 4)):
            c.stop = None
            with self.assertRaises(ModelHalt): action()
        c.stop = None; c.reg('RCX', 4); c.reg('RSI', CONTROL); c.reg('RDI', OUTPUT)
        with self.assertRaisesRegex(ModelHalt, 'OPAQUE_SYNC_OBJECT_READ'): c.model('copy')
        self.assertEqual(bytes(c.uc.mem_read(CONTROL, 4)), bytes(4))

    def test_native_opaque_access_rolls_back(self):
        for tail in (b'\x8b\x00\xc3', b'\xc7\x00\x01\0\0\0\xc3'):
            c = self.cpu(b'\x48\xb8'+struct.pack('<Q', CONTROL)+tail)
            self.begin(c)
            self.assertIn('OPAQUE_SYNC_OBJECT', c.run(CODE)['reason'])
            self.assertEqual(bytes(c.uc.mem_read(CONTROL, 4)), bytes(4))
            self.assertEqual(c.once_objects[str(CONTROL)]['state'], 'running')

    def test_pending_checkpoint_resumes_actual_callback(self):
        code = b'\x90\xc3'
        c = self.cpu(code, limit=1); self.begin(c)
        self.assertEqual(c.run(CODE)['reason'], 'INSTRUCTION_BUDGET')
        state = json.loads(json.dumps(capture(c)))
        d = self.cpu(code)
        restore(d, state)
        self.assertEqual(d.once_pending, c.once_pending)
        self.assertEqual(d.run(d.reg('RIP'))['reason'], 'ENTRY_RETURN')
        self.assertEqual(d.once_objects[str(CONTROL)]['state'], 'done')
        self.assertFalse(d.once_pending)

    def test_checkpoint_rejects_tamper(self):
        c = self.cpu(b'\x90\xc3', limit=1); self.begin(c); c.run(CODE)
        original = capture(c)
        changes = [lambda t: t.update(calls=True), lambda t: t.update(calls=0),
                   lambda t: t['objects'][str(CONTROL)].update(state='complete'),
                   lambda t: t['objects'][str(CONTROL)].update(callback=CONTROL),
                   lambda t: t['pending'][0].update(sp=0),
                   lambda t: t['pending'][0].update(target=CONTROL),
                   lambda t: t['pending'][0]['saved'].update(RBX=-1),
                   lambda t: t.update(pending=[]),
                   lambda t: t['pending'].append(copy.deepcopy(t['pending'][0]))]
        for change in changes:
            state = copy.deepcopy(original); change(state['sparse']['once'])
            with self.assertRaises(ValueError): restore(self.cpu(b'\x90\xc3'), state)

    def test_batched_differential_and_checkpoint(self):
        for code in (b'\x90\xc3', b'\xfd\xc3', b'\x48\xff\xc3\xc3', b'\xc2\x08\0'):
            results = []
            for cls in (OnceThreadCPU, BatchedOnce):
                c = self.cpu(code, cls=cls); self.begin(c)
                stop = c.run(CODE)
                results.append((stop, c.once_objects, c.once_pending,
                                c.attempted, c.completed, c.reg('RSP'), c.reg('RIP')))
            self.assertEqual(results[0], results[1])
        c = self.cpu(b'\x90\xc3', limit=1, cls=BatchedOnce)
        self.begin(c); c.run(CODE)
        state = capture(c)
        d = self.cpu(b'\x90\xc3', cls=BatchedOnce); restore(d, state)
        self.assertEqual(d.run(d.reg('RIP'))['reason'], 'ENTRY_RETURN')
        self.assertEqual(d.once_objects[str(CONTROL)]['state'], 'done')

    def test_independent_nested_callbacks_complete(self):
        # Outer callback resumes after nested once, restores its own stack, returns.
        resume = CODE+16
        code = b'\xc3'+bytes(15)+b'\x48\xbc'+struct.pack('<Q', FRAME+24)+b'\xc3'
        c = self.cpu(code); self.begin(c)
        nested = FRAME-64
        c.write_private(nested, struct.pack('<QQQQ', 0, 0, 12, resume))
        c.write_private(CONTROL+8, bytes(4))
        c.reg('RSP', nested); c.reg('RDI', CONTROL+8)
        c.begin_once(nested, resume)
        self.assertEqual(len(c.once_pending), 2)
        self.assertEqual(c.run(CODE)['reason'], 'ENTRY_RETURN')
        self.assertEqual({o['state'] for o in c.once_objects.values()}, {'done'})
        self.assertFalse(c.once_pending)

    def test_shadow_and_sparse_controls_and_semaphore_exclusion(self):
        from native_sync_fixture_ysm_265 import model as sync_model
        for kind in ('shadow', 'sparse'):
            c = self.cpu()
            if kind == 'shadow':
                a = 0x200000
                c.add_image(a, bytes(4096), False)
                c.grant_shadow_range(a, 4096, 3)
            else:
                a = c.vm_map(4096)
                c.write_model_memory(a, bytes(4))
            c.reg('RDI', a); self.begin(c)
            self.assertEqual(c.run(CODE)['reason'], 'ENTRY_RETURN')
            self.assertEqual(c.once_objects[str(a)]['state'], 'done')
            self.assertTrue(c.expected_sparse_matches())
            self.assertTrue(c.expected_image_matches())
            c.stop = None; c.reg('RDI', a); c.reg('RSI', 0); c.reg('RDX', 0)
            with self.assertRaisesRegex(ModelHalt, 'INVALID_SEMAPHORE_STORAGE'):
                sync_model(c, 'sem_init')

    def test_disabled_and_overlapping_callback_frame_rejected(self):
        c = self.cpu(); c.threads_enabled = False
        with self.assertRaisesRegex(ModelHalt, 'DISABLED'): self.begin(c)
        self.assertFalse(c.once_objects)
        c = self.cpu(); self.begin(c)
        c.write_private(CONTROL+8, bytes(4)); c.reg('RDI', CONTROL+8); c.reg('RSP', FRAME)
        with self.assertRaisesRegex(ModelHalt, 'OVERLAPPING_ONCE_CALLBACK_FRAME'):
            self.begin(c)
        self.assertEqual(len(c.once_pending), 1)

    def test_frame_overlap_and_budgets(self):
        c = self.cpu(); c.reg('RDI', FRAME+24)
        with self.assertRaisesRegex(ModelHalt, 'OVERLAPS_FRAME'): self.begin(c)
        for attr in ('MAX_ONCE_OBJECTS', 'MAX_ONCE_PENDING', 'MAX_ONCE_CALLS'):
            c = self.cpu(); setattr(c, attr, 0)
            with self.assertRaisesRegex(ModelHalt, 'BUDGET'): self.begin(c)
            self.assertEqual(c.once_objects, {})

    def test_page_rounded_operations_preserve_opaque_once(self):
        for operation in ('unmap','protect','discard'):
            c=self.cpu();page=c.vm_map(4096);control=page+64;c.write_model_memory(control,bytes(4));c.reg('RDI',control);self.begin(c);before=bytes(c.uc.mem_read(page,4096));regions=copy.deepcopy(c.vm_regions)
            with self.assertRaises(ModelHalt):
                if operation=='discard':c.vm_advice(page,1,4)
                else:c.vm_change(page,1,prot=0,remove=operation=='unmap')
            self.assertEqual(c.vm_regions,regions);self.assertEqual(bytes(c.uc.mem_read(page,4096)),before);self.assertEqual(c.once_objects[str(control)]['state'],'running')

    def test_callback_sentinel_escape_cannot_complete_initializer(self):
        from native_initializer_sequence_ysm_265 import advance_after_return
        code=b'\x48\xb8'+struct.pack('<Q',RETURN)+b'\x48\x89\x04\x24\xc3'
        for cls in (OnceThreadCPU,BatchedOnce):
            c=self.cpu(code,cls=cls);c.call_in_progress=True;self.begin(c);self.assertEqual(c.run(c.reg('RIP'))['reason'],'ENTRY_RETURN');self.assertFalse(advance_after_return(c));self.assertTrue(c.call_in_progress);self.assertEqual(c.once_objects[str(CONTROL)]['state'],'running');self.assertEqual(c.stop['reason'],'UNFINISHED_GUEST_CALLBACK_AT_ENTRY_RETURN')

if __name__ == '__main__': unittest.main()
