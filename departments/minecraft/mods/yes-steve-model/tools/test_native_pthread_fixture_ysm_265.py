"""Own-byte fixtures only: no target image and no host thread execution."""
import copy
import io
import json
import struct
import unittest

try:
    from native_pthread_fixture_ysm_265 import ThreadGuardedCPU, model
except ImportError:
    ThreadGuardedCPU = None
from native_unicorn_guarded_ysm_265 import ModelHalt, SP
from native_guarded_checkpoint_ysm_265 import capture, restore

CODE = 0x100000
DATA = 0x200000

class PthreadTests(unittest.TestCase):
    def cpu(self, enabled=True):
        self.assertIsNotNone(ThreadGuardedCPU, 'Deferred pthread implementation required')
        c = ThreadGuardedCPU(io.StringIO(), 'heap', limit=1)
        c.add_image(CODE, b'\x90' * 32)
        c.add_image(DATA, bytes(4096), False)
        c.protect_image()
        if enabled:
            c.configure_threads([CODE])
        return c

    def call(self, c, name, *args):
        for r, v in zip(('RDI', 'RSI', 'RDX', 'RCX'), args):
            c.reg(r, v)
        return model(c, name)

    def create(self, c, output=SP+64):
        self.assertEqual(self.call(c, 'pthread_create', output, 0, CODE, 123), 0)
        return struct.unpack('<Q', c.read_known(output, 8))[0]

    def test_create_unknown_writable_output_deferred_boundary_and_detach(self):
        c = self.cpu()
        self.assertIsNotNone(c.unknown(SP+64, 8))
        tid = self.create(c)
        self.assertEqual(c.thread_records[str(tid)], {'start': CODE, 'arg': 123, 'state': 'pending', 'detached': False, 'executed': False})
        self.assertEqual(c.thread_boundary()['pending'], [tid])
        self.assertFalse(c.thread_boundary()['runtime_complete'])
        self.assertEqual(self.call(c, 'pthread_detach', tid), 0)
        self.assertTrue(c.thread_records[str(tid)]['detached'])
        self.assertFalse(c.thread_records[str(tid)]['executed'])

    def test_validation_and_disabled_leave_output_and_queue_unchanged(self):
        for enabled, out, attr, entry in [(False, SP+64, 0, CODE), (True, DATA, 0, CODE), (True, 0, 0, CODE), (True, SP+64, 1, CODE), (True, SP+64, 0, CODE+1), (True, SP+64, 0, DATA)]:
            c = self.cpu(enabled)
            before = bytes(c.uc.mem_read(SP+64, 8))
            with self.assertRaises(ModelHalt):
                self.call(c, 'pthread_create', out, attr, entry, 123)
            self.assertEqual(c.thread_records, {})
            self.assertEqual(c.thread_calls, 0)
            self.assertEqual(bytes(c.uc.mem_read(SP+64, 8)), before)

    def test_repeated_join_never_completes_and_detached_join_rejected(self):
        c = self.cpu(); tid = self.create(c)
        for _ in range(2):
            with self.assertRaisesRegex(ModelHalt, 'THREAD_SCHEDULER_REQUIRED'):
                self.call(c, 'pthread_join', tid, SP+128)
            self.assertIsNotNone(c.unknown(SP+128, 8))
        self.call(c, 'pthread_detach', tid)
        with self.assertRaisesRegex(ModelHalt, 'THREAD_NOT_JOINABLE'):
            self.call(c, 'pthread_join', tid, 0)
        with self.assertRaisesRegex(ModelHalt, 'THREAD_NOT_JOINABLE'):
            self.call(c, 'pthread_detach', tid)

    def test_identity_and_unknown_ids(self):
        c = self.cpu(); tid = self.create(c)
        main = self.call(c, 'pthread_self')
        self.assertNotEqual(main, tid)
        self.assertEqual(self.call(c, 'pthread_equal', tid, tid), 1)
        self.assertEqual(self.call(c, 'pthread_equal', tid, main), 0)
        for symbol in ('pthread_join', 'pthread_detach', 'pthread_equal'):
            with self.assertRaisesRegex(ModelHalt, 'UNKNOWN_THREAD'):
                self.call(c, symbol, 999, main)

    def test_tls_lifecycle_and_weak_alias(self):
        c = self.cpu()
        self.assertEqual(self.call(c, '__pthread_key_create', SP+64, CODE), 0)
        key = struct.unpack('<I', c.read_known(SP+64, 4))[0]
        self.assertEqual(self.call(c, 'pthread_getspecific', key), 0)
        self.assertEqual(self.call(c, 'pthread_setspecific', key, 456), 0)
        self.assertEqual(self.call(c, 'pthread_getspecific', key), 456)
        self.assertEqual(self.call(c, 'pthread_key_delete', key), 0)
        with self.assertRaisesRegex(ModelHalt, 'UNKNOWN_TLS_KEY'):
            self.call(c, 'pthread_getspecific', key)
        self.assertFalse(c.thread_boundary()['destructors_executed'])

    def test_tls_key_arguments_ignore_upper_32_register_bits(self):
        c = self.cpu()
        self.call(c, 'pthread_key_create', SP+64, 0)
        key = struct.unpack('<I', c.read_known(SP+64, 4))[0]
        wide = 0xabcdef1200000000 | key
        self.assertEqual(self.call(c, 'pthread_setspecific', wide, 0x123456789abcdef0), 0)
        self.assertEqual(self.call(c, 'pthread_getspecific', wide), 0x123456789abcdef0)
        self.assertEqual(self.call(c, 'pthread_key_delete', wide), 0)
        with self.assertRaisesRegex(ModelHalt, 'UNKNOWN_TLS_KEY'):
            self.call(c, 'pthread_getspecific', wide)

    def test_checkpoint_roundtrip_and_tamper(self):
        c = self.cpu(); self.create(c)
        self.call(c, 'pthread_key_create', SP+80, 0)
        c.thread_boundary(); c.run(CODE)
        s = json.loads(json.dumps(capture(c)))
        d = self.cpu(False); restore(d, s)
        self.assertEqual(d.capture_sparse(), c.capture_sparse())
        for field, value in [('executed', True), ('state', 'completed'), ('start', DATA), ('arg', -1)]:
            bad = copy.deepcopy(s['sparse'])
            bad['threads']['records']['2'][field] = value
            with self.assertRaises(ValueError):
                self.cpu(False).restore_sparse(bad)

    def test_budgets_and_failed_write_are_atomic(self):
        c = self.cpu(); c.MAX_THREADS = 1
        self.create(c)
        with self.assertRaisesRegex(ModelHalt, 'THREAD_RECORD_BUDGET'):
            self.create(c, SP+80)
        self.assertIsNotNone(c.unknown(SP+80, 8))
        c = self.cpu(); c.thread_calls = c.MAX_THREAD_CALLS
        with self.assertRaisesRegex(ModelHalt, 'THREAD_CALL_BUDGET'):
            self.create(c)
        c = self.cpu(); c.MAX_KEYS = 1
        self.call(c, 'pthread_key_create', SP+64, 0)
        with self.assertRaisesRegex(ModelHalt, 'TLS_KEY_BUDGET'):
            self.call(c, 'pthread_key_create', SP+80, 0)
        c = self.cpu(); c.grant_shadow_range(DATA, 4096, 3); c.shadow_events = c.MAX_IMAGE_EVENTS
        with self.assertRaisesRegex(ModelHalt, 'SHADOW_WRITE_BUDGET'):
            self.create(c, DATA)
        self.assertEqual(c.thread_records, {})
        self.assertEqual(c.thread_calls, 0)
        self.assertEqual(bytes(c.uc.mem_read(DATA, 8)), bytes(8))

    def test_output_in_sparse_and_shadow_memory_is_ledger_accounted(self):
        for kind in ('sparse', 'shadow'):
            c = self.cpu()
            if kind == 'sparse':
                a = c.vm_map(4096) + 64
            else:
                c.grant_shadow_range(DATA, 4096, 3); a = DATA + 64
            self.assertEqual(self.create(c, a), 2)
            self.assertTrue(c.expected_sparse_matches())
            self.assertTrue(c.expected_image_matches())
            self.assertEqual(c.thread_records['2']['state'], 'pending')

    def test_opaque_sync_output_failure_and_no_snapshot_aliasing(self):
        from native_sync_fixture_ysm_265 import model as sync_model
        c = self.cpu()
        self.call(c, 'pthread_key_create', SP+80, 0)
        c.reg('RDI', SP+64); c.reg('RSI', 0); c.reg('RDX', 0)
        sync_model(c, 'sem_init')
        before = bytes(c.uc.mem_read(SP+64, 8))
        with self.assertRaisesRegex(ModelHalt, 'OPAQUE_SYNC_OBJECT_WRITE'):
            self.create(c)
        self.assertEqual(c.thread_records, {})
        self.assertEqual(bytes(c.uc.mem_read(SP+64, 8)), before)
        snapshot = c.capture_sparse()
        snapshot['threads']['keys']['0']['value'] = 99
        self.assertEqual(c.thread_keys['0']['value'], 0)

    def test_configuration_invalid_entries_and_reconfiguration_rejected(self):
        for entries in ([], [DATA], [CODE, CODE], [CODE+1000]):
            c = self.cpu(False)
            with self.assertRaises(ModelHalt):
                c.configure_threads(entries)
            self.assertFalse(c.threads_enabled)
        c = self.cpu()
        with self.assertRaisesRegex(ModelHalt, 'THREAD_CONFIGURATION_REQUIRES_FRESH_CPU'):
            c.configure_threads([CODE])
        c = self.cpu(False); c.run(CODE)
        with self.assertRaisesRegex(ModelHalt, 'THREAD_CONFIGURATION_REQUIRES_FRESH_CPU'):
            c.configure_threads([CODE])

    def test_checkpoint_schema_budget_identity_and_tls_corruption_rejected(self):
        c = self.cpu(); self.create(c)
        self.call(c, 'pthread_key_create', SP+80, 0)
        original = c.capture_sparse()
        changes = [lambda t: t.update(calls=True), lambda t: t.update(calls=0),
                   lambda t: t.update(enabled=False), lambda t: t.update(boundary=1),
                   lambda t: t.update(schedule='immediate'), lambda t: t.update(entries=[CODE, CODE]),
                   lambda t: t['records'].update({'999': t['records']['2']}),
                   lambda t: t['keys']['0'].update(value=-1),
                   lambda t: t['keys']['0'].update(destructor=DATA),
                   lambda t: t['keys']['0'].update(active=False, value=9),
                   lambda t: t['keys']['0'].update(active=1),
                   lambda t: t['records']['2'].update(detached=1)]
        for change in changes:
            s = copy.deepcopy(original); change(s['threads'])
            d = self.cpu(False)
            with self.assertRaises(ValueError):
                d.restore_sparse(s)
            self.assertEqual(d.thread_records, {})
            self.assertFalse(d.threads_enabled)

if __name__ == '__main__':
    unittest.main()
