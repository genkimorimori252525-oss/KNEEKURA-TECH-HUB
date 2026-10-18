"""Declared allocator import fixture tests using only synthetic guest bytes."""
import io
import struct
import unittest
from native_allocator_os_fixture_ysm_265 import model, entropy, FD, IMPORTS, SYMBOLS
from native_sparse_vm_ysm_265 import SparseGuardedCPU, PAGE
from native_unicorn_guarded_ysm_265 import ModelHalt

class AllocatorFixtureTests(unittest.TestCase):
    def cpu(self): return SparseGuardedCPU(io.StringIO(), 'heap', limit=1)
    def call(self, c, symbol, *args):
        for register, value in zip(('RDI', 'RSI', 'RDX', 'RCX', 'R8', 'R9'), args): c.reg(register, value)
        return model(c, symbol)
    def string(self, c, value):
        a = c.reserve_fixture(len(value) + 1); c.write_private(a, value.encode() + b'\0'); return a
    def open_entropy(self, c): return self.call(c, 'open', self.string(c, '/dev/urandom'), 0x80000)

    def test_errno_is_stable_declared_input(self):
        c = self.cpu(); a = model(c, '__errno_location')
        self.assertEqual(c.read_known(a, 4), struct.pack('<i', 2))
        self.assertEqual(model(c, '__errno_location'), a)
        self.assertEqual(c.os_fixture['calls'], 2)

    def test_entropy_chunking_and_close(self):
        c = self.cpu(); self.assertEqual(self.open_entropy(c), FD); a = c.vm_map(PAGE)
        self.assertEqual(self.call(c, 'read', FD, a, 17), 17)
        self.assertEqual(self.call(c, 'read', FD, a + 17, 48), 48)
        self.assertEqual(c.read_known(a, 65), entropy(c.os_fixture['entropy_seed'], 0, 65))
        self.assertEqual(c.os_fixture['entropy_offset'], 65)
        self.assertTrue(c.expected_sparse_matches())
        self.assertEqual(self.call(c, 'close', FD), 0)
        with self.assertRaises(ModelHalt): self.call(c, 'read', FD, a, 1)

    def test_entropy_zero_length_does_not_touch_pointer(self):
        c = self.cpu(); self.open_entropy(c)
        self.assertEqual(self.call(c, 'read', FD, 0xdeadbeef, 0), 0)
        self.assertEqual(c.vm_pages, {})

    def test_entropy_quota_rejects_before_mutation(self):
        c = self.cpu(); self.open_entropy(c); a = c.vm_map(PAGE)
        self.call(c, 'read', FD, a, PAGE)
        before = c.read_known(a, PAGE)
        with self.assertRaises(ModelHalt): self.call(c, 'read', FD, a, 1)
        self.assertEqual(c.os_fixture['entropy_offset'], PAGE)
        self.assertEqual(c.read_known(a, PAGE), before)

    def test_unknown_paths_flags_and_descriptors_rejected(self):
        for path, flags in [('/etc/passwd', 0x80000), ('/dev/urandom', 4)]:
            c = self.cpu()
            with self.assertRaises(ModelHalt): self.call(c, 'open', self.string(c, path), flags)
            self.assertFalse(c.os_fixture['entropy_open'])
        c = self.cpu(); self.open_entropy(c)
        with self.assertRaises(ModelHalt): self.call(c, 'close', FD + 1)
        self.assertTrue(c.os_fixture['entropy_open'])

    def test_mmap_mprotect_advice_unmap(self):
        c = self.cpu(); a = self.call(c, 'mmap', 0, 1 << 30, 3, 0x4022, (1 << 64) - 1, 0)
        self.assertEqual(c.vm_pages, {})
        self.assertEqual(self.call(c, 'mprotect', a, PAGE, 1), 0)
        self.assertEqual(self.call(c, 'madvise', a, PAGE, 8), 0)
        self.assertEqual(self.call(c, 'munmap', a, PAGE), 0)
        self.assertIsNone(c.vm_cover(a, 1))

    def test_unknown_mmap_requests_rejected(self):
        for args in [(PAGE, PAGE, 3, 0x22, (1 << 64)-1, 0),
                     (0, PAGE, 3, 0x10, (1 << 64)-1, 0),
                     (0, PAGE, 3, 0x22, 7, 0),
                     (0, PAGE, 3, 0x22, (1 << 64)-1, 1),
                     (0, PAGE, 7, 0x22, (1 << 64)-1, 0)]:
            c = self.cpu()
            with self.assertRaises(ModelHalt): self.call(c, 'mmap', *args)
            self.assertEqual(c.vm_regions, [])

    def test_virtual_name_is_bounded_to_known_mapping(self):
        c = self.cpu(); a = c.vm_map(PAGE); name = self.string(c, 'snmalloc')
        self.assertEqual(self.call(c, 'prctl', 0x53564d41, 0, a, PAGE, name), 0)
        self.assertEqual(c.os_fixture['names'], [[a, PAGE, 'snmalloc']])
        with self.assertRaises(ModelHalt): self.call(c, 'prctl', 0x53564d41, 0, a, PAGE+1, name)

    def test_unknown_symbol_rejected(self):
        with self.assertRaises(ValueError): model(self.cpu(), 'socket')

    def test_clock_little_endian_timespec_and_stride(self):
        c = self.cpu(); a = c.vm_map(PAGE)
        self.assertEqual(self.call(c, 'clock_gettime', 1, a), 0)
        self.assertEqual(c.read_known(a, 16), bytes(16))
        self.assertEqual(self.call(c, 'clock_gettime', 1, a), 0)
        self.assertEqual(c.read_known(a, 16), struct.pack('<qq', 0, 1000000))
        self.assertEqual(c.os_fixture['monotonic_ns'], 2000000)
        self.assertEqual(c.os_fixture['clock_calls'], 2)
        self.assertEqual(c.os_fixture['calls'], 2)
        self.assertTrue(c.expected_sparse_matches())
        self.assertEqual(IMPORTS[64], ('clock_gettime', 0x184d218, 0x14cb9e8))

    def test_clock_timespec_second_boundary(self):
        c = self.cpu(); a = c.vm_map(PAGE)
        c.os_fixture.update(monotonic_ns=999000000, clock_calls=999, calls=999)
        self.call(c, 'clock_gettime', 1, a)
        self.assertEqual(c.read_known(a, 16), struct.pack('<qq', 0, 999000000))
        self.call(c, 'clock_gettime', 1, a)
        self.assertEqual(c.read_known(a, 16), struct.pack('<qq', 1, 0))

    def test_clock_rejects_realtime_without_increment(self):
        c = self.cpu(); a = c.vm_map(PAGE)
        with self.assertRaises(ModelHalt): self.call(c, 'clock_gettime', 0, a)
        self.assertEqual(c.stop['reason'], 'UNMODELED_CLOCK_ID')
        self.assertEqual(c.os_fixture['monotonic_ns'], 0)
        self.assertEqual(c.os_fixture['clock_calls'], 0)
        self.assertEqual(c.os_fixture['calls'], 0)
        self.assertEqual(c.vm_pages, {})

    def test_clock_permission_failure_does_not_increment(self):
        for prot in (0, 1):
            with self.subTest(prot=prot):
                c = self.cpu(); a = c.vm_map(PAGE, prot)
                with self.assertRaises(ModelHalt): self.call(c, 'clock_gettime', 1, a)
                self.assertEqual(c.os_fixture['monotonic_ns'], 0)
                self.assertEqual(c.os_fixture['clock_calls'], 0)
                self.assertEqual(c.os_fixture['calls'], 0)
                self.assertEqual(c.vm_write_events, 0)

    def test_clock_checkpoint_restore_continues_sequence(self):
        import copy
        c = self.cpu(); a = c.vm_map(PAGE); self.call(c, 'clock_gettime', 1, a)
        d = self.cpu(); d.restore_sparse(copy.deepcopy(c.capture_sparse()))
        self.assertEqual(d.os_fixture['monotonic_ns'], 1000000)
        self.assertEqual(d.os_fixture['clock_calls'], 1)
        self.call(d, 'clock_gettime', 1, a)
        self.assertEqual(d.read_known(a, 16), struct.pack('<qq', 0, 1000000))
        self.assertEqual(d.os_fixture['clock_calls'], 2)

    def test_clock_checkpoint_missing_fields_migrate_to_zero(self):
        import copy
        c = self.cpu(); state = copy.deepcopy(c.capture_sparse())
        del state['os_fixture']['monotonic_ns']; del state['os_fixture']['clock_calls']
        d = self.cpu(); d.restore_sparse(state)
        self.assertEqual(d.os_fixture['monotonic_ns'], 0)
        self.assertEqual(d.os_fixture['clock_calls'], 0)

    def test_clock_checkpoint_invalid_counter_and_stride_rejected(self):
        import copy
        c = self.cpu(); original = c.capture_sparse()
        for calls, ns in [(-1, -1000000), (1, 0), (c.MAX_VM_EVENTS + 1, (c.MAX_VM_EVENTS + 1) * 1000000)]:
            with self.subTest(calls=calls, ns=ns):
                state = copy.deepcopy(original)
                state['os_fixture'].update(clock_calls=calls, monotonic_ns=ns)
                with self.assertRaises(ValueError): self.cpu().restore_sparse(state)

    def test_readlink_fixture_has_no_nul_and_truncates(self):
        c = self.cpu(); path = self.string(c, '/proc/self/exe'); a = c.vm_map(PAGE); c.write_model_memory(a, b'X'*64)
        self.assertEqual(self.call(c, 'readlink', path, a, 4096), len('/virtual/jdk/bin/java'))
        self.assertEqual(c.read_known(a, 22), b'/virtual/jdk/bin/javaX')
        self.assertEqual(self.call(c, 'readlink', path, a, 3), 3)
        self.assertEqual(c.read_known(a, 3), b'/vi')
        self.assertEqual(c.os_fixture['readlink_calls'], 2)

    def test_readlink_rejects_unknown_path_and_zero_buffer(self):
        for path, size in [('/etc/passwd', 64), ('/proc/self/exe', 0)]:
            c = self.cpu()
            with self.assertRaises(ModelHalt): self.call(c, 'readlink', self.string(c, path), 0xdead, size)
            self.assertEqual(c.os_fixture['readlink_calls'], 0)

    def test_virtual_stat_exact_layout_for_two_declared_files(self):
        for path, mode in [('/virtual/jdk/bin/java', 0o100755), ('/virtual/jdk/lib/server/libjvm.so', 0o100644)]:
            c = self.cpu(); a = c.vm_map(PAGE)
            self.assertEqual(self.call(c, '__xstat', 1, self.string(c, path), a), 0)
            data = c.read_known(a, 144)
            self.assertEqual(struct.unpack_from('<QQQIII', data), (1,1,1,mode,1000,1000))
            self.assertEqual(struct.unpack_from('<qqq', data, 48), (0,4096,0))
            self.assertEqual(data[72:], bytes(72))

    def test_stat_unknown_path_or_abi_rejected(self):
        for version, path in [(0, '/virtual/jdk/bin/java'), (1, '/etc/passwd')]:
            c = self.cpu(); a = c.vm_map(PAGE)
            with self.assertRaises(ModelHalt): self.call(c, '__xstat', version, self.string(c, path), a)
            self.assertEqual(c.vm_pages, {})

    def test_entropy_readonly_open_without_cloexec(self):
        c = self.cpu(); self.assertEqual(self.call(c, 'open', self.string(c, '/dev/urandom'), 0), FD)

    def test_declared_imports_are_exact(self):
        self.assertEqual(len(IMPORTS), 15)
        self.assertEqual(SYMBOLS, {'__errno_location', 'open', 'read', 'close', 'prctl', 'mmap', 'madvise', 'mprotect', 'munmap', 'clock_gettime', 'readlink', '__xstat'})

if __name__ == '__main__': unittest.main()
