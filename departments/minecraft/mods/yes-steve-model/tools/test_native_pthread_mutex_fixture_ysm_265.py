"""Own-byte tests: no target native library or host worker runs."""
import copy
import io
import json
import struct
import unittest
from native_pthread_mutex_fixture_ysm_265 import MutexThreadCPU, model, SIZE
from native_unicorn_guarded_ysm_265 import ModelHalt, SP
from native_guarded_checkpoint_ysm_265 import capture, restore
from native_batched_cpu_ysm_265 import BatchedMixin
CODE = 0x100000
CONTROL = SP+128
OUTPUT = SP+256
class BatchedMutex(BatchedMixin, MutexThreadCPU):
    pass
class MutexTests(unittest.TestCase):
    def cpu(self, code=b'\xc3', cls=MutexThreadCPU):
        c = cls(io.StringIO(), 'heap', limit=30)
        c.add_image(CODE, code); c.protect_image()
        c.verify_thread_gate = lambda: None
        c.configure_threads([CODE]); c.write_private(CONTROL, bytes(SIZE)); c.write_private(OUTPUT, bytes(SIZE))
        return c
    def call(self, c, name, a=CONTROL, attr=0):
        c.reg('RDI', a); c.reg('RSI', attr)
        return model(c, 'pthread_mutex_'+name)
    def test_static_lifecycle(self):
        c = self.cpu()
        self.assertEqual(self.call(c, 'lock'), 0); self.assertEqual(self.call(c, 'trylock'), 16)
        with self.assertRaisesRegex(ModelHalt, 'WOULD_BLOCK'): self.call(c, 'lock')
        self.assertEqual(c.mutex_calls, 2); c.stop = None
        with self.assertRaisesRegex(ModelHalt, 'DESTROY_LOCKED'): self.call(c, 'destroy')
        c.stop = None; self.call(c, 'unlock'); self.call(c, 'destroy')
        with self.assertRaisesRegex(ModelHalt, 'DESTROYED'): self.call(c, 'lock')
        c.stop = None; self.call(c, 'init'); self.assertEqual(self.call(c, 'trylock'), 0)
        self.assertEqual(len(c.mutex_objects), 1); self.assertEqual(bytes(c.uc.mem_read(CONTROL, SIZE)), bytes(SIZE))
    def test_dynamic_init_and_attrs(self):
        c = self.cpu(); c.write_private(CONTROL, bytes([255])*SIZE)
        with self.assertRaisesRegex(ModelHalt, 'ATTRIBUTES'): self.call(c, 'init', attr=OUTPUT)
        self.assertFalse(c.mutex_objects); self.assertEqual(bytes(c.uc.mem_read(CONTROL, SIZE)), bytes([255])*SIZE)
        c.stop = None; self.call(c, 'init')
        with self.assertRaisesRegex(ModelHalt, 'ALREADY_INITIALIZED'): self.call(c, 'init')
        c.stop = None
        with self.assertRaisesRegex(ModelHalt, 'NOT_OWNED'): self.call(c, 'unlock')
    def test_unknown_nonzero_storage_and_budgets(self):
        for a in (0, CONTROL+1, CODE):
            c = self.cpu()
            with self.assertRaises(ModelHalt): self.call(c, 'lock', a)
            self.assertFalse(c.mutex_objects)
        c = self.cpu(); c.write_private(CONTROL+16, b'\x01')
        with self.assertRaisesRegex(ModelHalt, 'INITIAL_STATE'): self.call(c, 'lock')
        self.assertFalse(c.mutex_objects)
        c = self.cpu(); a = SP+512
        with self.assertRaises(ModelHalt): self.call(c, 'lock', a)
        self.assertFalse(c.mutex_objects); c.stop = None; self.call(c, 'init', a)
        for name in ('unlock', 'destroy'):
            c = self.cpu()
            with self.assertRaisesRegex(ModelHalt, 'UNKNOWN_MUTEX'): self.call(c, name)
        for budget in ('MAX_MUTEX_OBJECTS', 'MAX_MUTEX_CALLS'):
            c = self.cpu(); setattr(c, budget, 0)
            with self.assertRaisesRegex(ModelHalt, 'BUDGET'): self.call(c, 'lock')
            self.assertFalse(c.mutex_objects)
        c = self.cpu(); c.threads_enabled = False
        with self.assertRaisesRegex(ModelHalt, 'DISABLED'): self.call(c, 'init')
    def test_native_and_model_access_even_inactive(self):
        for cls in (MutexThreadCPU, BatchedMutex):
            for tail in (b'\x8b\x00\xc3', b'\xc7\x00\x01\0\0\0\xc3'):
                c = self.cpu(b'\x48\xb8'+struct.pack('<Q', CONTROL)+tail, cls); self.call(c, 'init')
                self.assertIn('OPAQUE_SYNC_OBJECT', c.run(CODE)['reason'])
                self.assertEqual(bytes(c.uc.mem_read(CONTROL, SIZE)), bytes(SIZE))
        for inactive in (False, True):
            c = self.cpu(); self.call(c, 'init')
            if inactive: self.call(c, 'destroy')
            for action in (lambda: c.read_known(CONTROL+39, 1), lambda: c.write_private(CONTROL, bytes(SIZE)), lambda: c.write_model_memory(CONTROL+39, b'\0')):
                c.stop = None
                with self.assertRaises(ModelHalt): action()
            for src, dst in ((CONTROL, OUTPUT), (OUTPUT, CONTROL)):
                c.stop = None; c.reg('RCX', SIZE); c.reg('RSI', src); c.reg('RDI', dst)
                with self.assertRaises(ModelHalt): c.model('copy')
    def test_page_guards_and_overlap(self):
        from native_sync_fixture_ysm_265 import model as sem_model
        for operation in ('unmap', 'protect', 'discard'):
            c = self.cpu(); page = c.vm_map(4096); a = page+64; self.call(c, 'init', a)
            regions = copy.deepcopy(c.vm_regions)
            with self.assertRaises(ModelHalt):
                if operation == 'discard': c.vm_advice(page, 1, 4)
                else: c.vm_change(page, 1, prot=0, remove=operation == 'unmap')
            self.assertEqual(c.vm_regions, regions); self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), bytes(SIZE))
        c = self.cpu(); self.call(c, 'init')
        with self.assertRaisesRegex(ModelHalt, 'OVERLAPPING'): self.call(c, 'init', CONTROL+8)
        c.stop = None; c.reg('RDI', CONTROL); c.reg('RSI', 0); c.reg('RDX', 0)
        with self.assertRaises(ModelHalt): sem_model(c, 'sem_init')
        c = self.cpu(); c.reg('RDI', CONTROL); c.reg('RSI', 0); c.reg('RDX', 0); sem_model(c, 'sem_init')
        with self.assertRaises(ModelHalt): self.call(c, 'init')
        c = self.cpu(); c.once_objects[str(CONTROL+8)] = {'state': 'done', 'callback': CODE}
        with self.assertRaises(ModelHalt): self.call(c, 'init')
    def test_checkpoint_and_corruption(self):
        c = self.cpu(); self.call(c, 'lock'); self.call(c, 'init', OUTPUT); self.call(c, 'destroy', OUTPUT)
        c.run(CODE); state = json.loads(json.dumps(capture(c))); d = self.cpu(); restore(d, state)
        self.assertEqual(d.mutex_objects, c.mutex_objects); self.assertEqual(d.mutex_calls, c.mutex_calls)
        self.assertEqual(self.call(d, 'trylock'), 16); self.assertEqual(self.call(d, 'unlock'), 0)
        self.assertTrue(d.expected_sparse_matches()); self.assertTrue(d.expected_image_matches())
        changes = [lambda t: t.update(calls=True), lambda t: t.update(calls=0),
                   lambda t: t['objects'][str(CONTROL)].update(owner=2), lambda t: t['objects'][str(CONTROL)].update(owner=True),
                   lambda t: t['objects'][str(CONTROL)].update(active=1), lambda t: t['objects'][str(CONTROL)].update(active=False),
                   lambda t: t['objects'][str(CONTROL)].update(kind='recursive'), lambda t: t['objects'][str(CONTROL)].update(size=32),
                   lambda t: t['objects'].update({str(CONTROL+8): copy.deepcopy(t['objects'][str(CONTROL)])}),
                   lambda t: t['objects'].update({'0': t['objects'].pop(str(CONTROL))})]
        for change in changes:
            bad = copy.deepcopy(state); change(bad['sparse']['mutex'])
            with self.assertRaises(ValueError): restore(self.cpu(), bad)
        for table, obj in (('once', {'state': 'done', 'callback': CODE}), ('sync', {'kind': 'semaphore', 'size': 32, 'value': 0, 'active': True})):
            bad = copy.deepcopy(state); bad['sparse'][table]['objects'][str(CONTROL)] = obj; bad['sparse'][table]['calls'] = 1
            with self.assertRaises(ValueError): restore(self.cpu(), bad)
        c.uc.mem_write(CONTROL, b'\x01')
        with self.assertRaisesRegex(ValueError, 'storage changed'): capture(c)
    def test_shadow_sparse_static_and_checkpoint_backing_validation(self):
        from native_guarded_checkpoint_ysm_265 import pack, unpack
        from native_unicorn_guarded_ysm_265 import STACK, STACK_SIZE
        for kind in ('shadow', 'sparse'):
            c = self.cpu()
            if kind == 'shadow':
                a = 0x200000; c.add_image(a, bytes(4096), False); c.grant_shadow_range(a, 4096, 3)
            else:
                a = c.vm_map(4096)
            self.call(c, 'lock', a); c.run(CODE); state = capture(c)
            d = self.cpu()
            if kind == 'shadow': d.add_image(a, bytes(4096), False)
            restore(d, state); self.assertEqual(d.mutex_objects, c.mutex_objects)
            self.assertEqual(self.call(d, 'unlock', a), 0)
            self.assertTrue(d.expected_image_matches()); self.assertTrue(d.expected_sparse_matches())
        c = self.cpu(); self.call(c, 'lock'); c.run(CODE); state = capture(c)
        for field, value in (('known', 0), ('bytes', 1)):
            bad = copy.deepcopy(state); data = bytearray(unpack(bad['private'][str(STACK)][field], STACK_SIZE))
            data[CONTROL-STACK+SIZE-1] = value; bad['private'][str(STACK)][field] = pack(data)
            with self.assertRaisesRegex(ValueError, 'mutex backing storage'): restore(self.cpu(), bad)

    def test_busy_never_changes_errno_and_lost_owner_stops(self):
        from native_allocator_os_fixture_ysm_265 import model as os_model
        c = self.cpu(); errno = os_model(c, '__errno_location'); c.write_private(errno, struct.pack('<i', 123))
        self.call(c, 'lock'); self.assertEqual(self.call(c, 'trylock'), 16)
        self.assertEqual(c.read_known(errno, 4), struct.pack('<i', 123))
        c.mutex_objects[str(CONTROL)]['owner'] = 2
        with self.assertRaisesRegex(ModelHalt, 'INVALID_MUTEX_STATE'): self.call(c, 'unlock')
    def test_nonempty_mutex_checkpoint_cannot_use_older_backend(self):
        from native_pthread_once_fixture_ysm_265 import OnceThreadCPU
        c=self.cpu();self.call(c,'lock');c.stop={'reason':'TEST'};state=capture(c)
        with self.assertRaisesRegex(ValueError,'mutex-capable'):restore(self.cpu(cls=OnceThreadCPU),state)

if __name__ == '__main__': unittest.main()
