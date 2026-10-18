"""Own-byte virtual semaphore fixtures; never load or execute a target library."""
import copy
import io
import json
import struct
import unittest

from native_allocator_os_fixture_ysm_265 import model as os_model
from native_guarded_checkpoint_ysm_265 import capture, restore
from native_sparse_vm_ysm_265 import PAGE
from native_sync_fixture_ysm_265 import MAX_VALUE, SIZE, SyncGuardedCPU, model
from native_unicorn_guarded_ysm_265 import ModelHalt, SP

CODE = 0x100000
DATA = 0x200000
RAW = bytes(range(SIZE))


class SemaphoreTests(unittest.TestCase):
    def cpu(self, code=b'\x90'):
        c = SyncGuardedCPU(io.StringIO(), 'heap', limit=1)
        c.add_image(CODE, code + b'\x90' * 16)
        c.add_image(DATA, bytes(PAGE), False)
        c.protect_image()
        return c

    def storage(self, c, kind):
        if kind == 'private':
            a = SP + 64
        elif kind == 'image':
            c.grant_shadow_range(DATA, PAGE, 3)
            a = DATA + 64
        else:
            a = c.vm_map(PAGE) + 64
        c.write_model_memory(a, RAW)
        return a

    def call(self, c, name, a, value=0, shared=0):
        c.reg('RDI', a)
        c.reg('RSI', shared)
        c.reg('RDX', value)
        return model(c, name)

    def initialized(self, kind='private', value=0, code=b'\x90'):
        c = self.cpu(code)
        a = self.storage(c, kind)
        self.assertEqual(self.call(c, 'sem_init', a, value), 0)
        return c, a

    def errno(self, c):
        p = os_model(c, '__errno_location')
        return struct.unpack('<i', c.read_known(p, 4))[0]

    def test_lifecycle_counts_and_raw_storage_unchanged(self):
        for kind in ('private', 'image', 'sparse'):
            with self.subTest(kind=kind):
                c, a = self.initialized(kind, 2)
                for name, count in [('sem_post', 3), ('sem_wait', 2),
                                    ('sem_trywait', 1), ('sem_destroy', 1)]:
                    self.assertEqual(self.call(c, name, a), 0)
                    self.assertEqual(c.sync_objects[str(a)]['value'], count)
                    self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)
                self.assertFalse(c.sync_objects[str(a)]['active'])
                self.assertEqual(c.sync_calls, 5)
                self.assertEqual(self.call(c, 'sem_init', a, 7), 0)
                self.assertEqual(c.sync_objects[str(a)]['value'], 7)
                self.assertEqual(c.sync_calls, 6)
                self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)

    def test_errno_einval_eagain_eoverflow(self):
        for value, name, expected, exists in [
            (MAX_VALUE + 1, 'sem_init', 22, False),
            (0, 'sem_trywait', 11, True),
            (MAX_VALUE, 'sem_post', 75, True),
        ]:
            with self.subTest(name=name):
                c = self.cpu()
                a = self.storage(c, 'private')
                if exists:
                    self.call(c, 'sem_init', a, value)
                self.assertEqual(self.call(c, name, a, value), 0xffffffff)
                self.assertEqual(self.errno(c), expected)
                self.assertEqual(str(a) in c.sync_objects, exists)
                if exists:
                    self.assertEqual(c.sync_objects[str(a)]['value'], value)
                self.assertEqual(c.sync_calls, 2 if exists else 1)
                self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)

    def test_zero_wait_stops_without_consumption_or_success(self):
        c, a = self.initialized()
        with self.assertRaisesRegex(ModelHalt, 'VIRTUAL_SEMAPHORE_WOULD_BLOCK'):
            self.call(c, 'sem_wait', a)
        self.assertEqual(c.sync_calls, 1)
        self.assertEqual(c.sync_objects[str(a)]['value'], 0)
        self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)

    def test_double_init_destroy_and_unknown_rejected(self):
        for name, destroyed, offset in [('sem_init', False, 0),
                                         ('sem_destroy', True, 0),
                                         ('sem_wait', True, 0),
                                         ('sem_post', False, 64)]:
            with self.subTest(name=name, destroyed=destroyed, offset=offset):
                c, a = self.initialized()
                if destroyed:
                    self.call(c, 'sem_destroy', a)
                before = copy.deepcopy(c.sync_objects)
                count = c.sync_calls
                with self.assertRaises(ModelHalt):
                    self.call(c, name, a + offset)
                self.assertEqual(c.sync_objects, before)
                self.assertEqual(c.sync_calls, count)

    def test_overlap_rejected_including_destroyed_storage(self):
        for destroyed in (False, True):
            c, a = self.initialized()
            if destroyed:
                self.call(c, 'sem_destroy', a)
            with self.assertRaisesRegex(ModelHalt, 'OVERLAPPING_SEMAPHORE'):
                self.call(c, 'sem_init', a + 8)

    def test_invalid_shared_alignment_and_storage(self):
        for address, shared in [(SP + 64, 1), (SP + 65, 0),
                                (0, 0), (DATA, 0), (0xfffffffffffffff8, 0)]:
            with self.subTest(address=address, shared=shared):
                c = self.cpu()
                with self.assertRaises(ModelHalt):
                    self.call(c, 'sem_init', address, shared=shared)
                self.assertEqual(c.sync_objects, {})
                self.assertEqual(c.sync_calls, 0)
        for prot in (0, 1):
            c = self.cpu()
            a = c.vm_map(PAGE, prot)
            with self.assertRaises(ModelHalt):
                self.call(c, 'sem_init', a)

    def test_model_read_write_guards_all_storage(self):
        for kind in ('private', 'image', 'sparse'):
            for operation in ('read', 'write'):
                with self.subTest(kind=kind, operation=operation):
                    c, a = self.initialized(kind)
                    self.assertEqual(c.unknown(a + 8, 1), a + 8)
                    with self.assertRaisesRegex(ModelHalt, 'OPAQUE_SYNC_OBJECT'):
                        if operation == 'read':
                            c.read_known(a + 8, 1)
                        else:
                            c.write_model_memory(a + 8, b'x')
                    self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)

    def test_private_write_guard(self):
        c, a = self.initialized()
        with self.assertRaisesRegex(ModelHalt, 'OPAQUE_SYNC_OBJECT_WRITE'):
            c.write_private(a, b'x')
        self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)

    def test_model_copy_source_and_destination_are_guarded(self):
        for kind in ('private', 'image', 'sparse'):
            for source in (False, True):
                with self.subTest(kind=kind, source=source):
                    c, a = self.initialized(kind)
                    other = SP + 256
                    c.write_private(other, b'q')
                    c.reg('RSI', a if source else other)
                    c.reg('RDI', other if source else a)
                    c.reg('RCX', 1)
                    with self.assertRaises(ModelHalt):
                        c.model('copy')
                    self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)
                    self.assertEqual(c.read_known(other, 1), b'q')

    def test_authored_native_read_and_pending_store_rollback(self):
        for kind in ('private', 'image', 'sparse'):
            for code, reason in [(b'\x48\x8b\x03', 'OPAQUE_SYNC_OBJECT_READ'),
                                  (b'\x48\x89\x03', 'OPAQUE_SYNC_OBJECT_WRITE')]:
                with self.subTest(kind=kind, code=code.hex()):
                    c, a = self.initialized(kind, code=code)
                    c.reg('RBX', a)
                    c.reg('RAX', 0xabcdef1234567890)
                    counts = (c.vm_write_events, c.shadow_events, c.heap_writes)
                    c.run(CODE)
                    self.assertEqual(c.stop['reason'], reason)
                    self.assertEqual(c.completed, 0)
                    self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)
                    self.assertEqual((c.vm_write_events, c.shadow_events, c.heap_writes), counts)
                    self.assertTrue(c.expected_sparse_matches())
                    self.assertTrue(c.expected_image_matches())

    def test_cross_boundary_native_store_rolls_back_all_bytes(self):
        for kind in ('private', 'image', 'sparse'):
            for offset in (-4, SIZE - 4):
                with self.subTest(kind=kind, offset=offset):
                    c, a = self.initialized(kind, code=b'\x48\x89\x03')
                    before = bytes(c.uc.mem_read(a - 8, SIZE + 16))
                    c.reg('RBX', a + offset)
                    c.reg('RAX', 0xabcdef1234567890)
                    c.run(CODE)
                    self.assertEqual(c.stop['reason'], 'OPAQUE_SYNC_OBJECT_WRITE')
                    self.assertEqual(c.completed, 0)
                    self.assertEqual(bytes(c.uc.mem_read(a - 8, SIZE + 16)), before)
                    self.assertTrue(c.expected_sparse_matches())
                    self.assertTrue(c.expected_image_matches())

    def test_sparse_discard_cannot_invalidate_semaphore_storage(self):
        for advice in (4, 8):
            c, a = self.initialized('sparse')
            with self.assertRaisesRegex(ModelHalt, 'SYNC_STORAGE_ADVICE'):
                c.vm_advice(a & ~(PAGE - 1), PAGE, advice)
            self.assertEqual(bytes(c.uc.mem_read(a, SIZE)), RAW)
            self.assertEqual(c.sync_objects[str(a)]['value'], 0)

    def test_storage_mapping_change_rejected(self):
        for remove in (False, True):
            c, a = self.initialized('sparse')
            with self.assertRaisesRegex(ModelHalt, 'SYNC_STORAGE_MAPPING_CHANGE'):
                c.vm_change(a & ~(PAGE - 1), PAGE, prot=1, remove=remove)

    def test_full_checkpoint_roundtrip_retains_opaque_guards(self):
        c = self.cpu()
        addresses = [self.storage(c, kind) for kind in ('private', 'image', 'sparse')]
        for a in addresses:
            self.call(c, 'sem_init', a, 3)
        self.call(c, 'sem_destroy', addresses[1])
        c.run(CODE)
        state = json.loads(json.dumps(capture(c)))
        d = self.cpu()
        restore(d, state)
        self.assertEqual(d.capture_sparse(), c.capture_sparse())
        self.assertEqual(d.sync_calls, 4)
        for a in addresses:
            self.assertEqual(bytes(d.uc.mem_read(a, SIZE)), RAW)
            self.assertIsNotNone(d.unknown(a, SIZE))
            with self.assertRaisesRegex(ModelHalt, 'OPAQUE_SYNC_OBJECT_READ'):
                d.read_known(a, SIZE)
        self.assertEqual(self.call(d, 'sem_wait', addresses[0]), 0)
        self.assertEqual(d.sync_objects[str(addresses[0])]['value'], 2)

    def test_invalid_restored_semaphore_states_rejected(self):
        c, a = self.initialized('sparse')
        original = c.capture_sparse()
        def obj(state):
            return state['sync']['objects'][str(a)]
        changes = [
            lambda s: obj(s).update(value=-1),
            lambda s: obj(s).update(value=MAX_VALUE + 1),
            lambda s: obj(s).update(value=True),
            lambda s: obj(s).update(active=1),
            lambda s: obj(s).update(kind='mutex'),
            lambda s: obj(s).update(size=16),
            lambda s: obj(s).update(extra=0),
            lambda s: s['sync'].update(calls=-1),
            lambda s: s['sync'].update(calls=True),
            lambda s: s['sync'].update(calls=1000001),
            lambda s: s['sync']['objects'].update({str(a + 8): copy.deepcopy(obj(s))}),
            lambda s: s['sync'].update(objects={str(a + 1): copy.deepcopy(obj(s))}),
            lambda s: s['sync'].update(objects={'0' + str(a): copy.deepcopy(obj(s))}),
            lambda s: s['sync'].update(objects={'0': copy.deepcopy(obj(s))}),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                state = copy.deepcopy(original)
                change(state)
                with self.assertRaises(ValueError):
                    self.cpu().restore_sparse(state)


if __name__ == '__main__':
    unittest.main()
