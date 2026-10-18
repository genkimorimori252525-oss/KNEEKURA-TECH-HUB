"""Own-byte sparse guest-memory tests; never load or execute a target binary."""
import copy
import io
import unittest
from native_sparse_vm_ysm_265 import SparseGuardedCPU, PAGE, BASE
from native_unicorn_guarded_ysm_265 import ModelHalt

CODE = 0x100000
VALUE = 0x123456789abcdef

class SparseTests(unittest.TestCase):
    def cpu(self, code='488903', limit=1):
        c = SparseGuardedCPU(io.StringIO(), limit=limit)
        c.add_image(CODE, bytes.fromhex(code) + b'\x90' * 16)
        c.protect_image()
        c.reg('RAX', VALUE)
        return c

    def test_huge_reservation_has_no_backing(self):
        c = self.cpu(); a = c.vm_map(1 << 38)
        self.assertEqual(c.vm_reserved(), 1 << 38)
        self.assertEqual(c.vm_pages, {})
        self.assertEqual(c.read_known(a + (1 << 37), 8), bytes(8))
        self.assertEqual(len(c.vm_pages), 1)

    def test_backing_cap_rejects_without_partial_materialization(self):
        c = self.cpu(); c.MAX_PAGES = 1; a = c.vm_map(PAGE * 2)
        self.assertFalse(c.vm_materialize(a, PAGE * 2, 1))
        self.assertEqual(c.stop['reason'], 'SPARSE_BACKING_BUDGET')
        self.assertEqual(c.vm_pages, {})

    def test_native_write_commits_ledger(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.reg('RBX', a); c.run(CODE)
        self.assertEqual(c.completed, 1)
        self.assertEqual(c.read_known(a, 8), VALUE.to_bytes(8, 'little'))
        self.assertEqual((c.vm_write_events, c.vm_write_bytes), (1, 8))
        self.assertTrue(c.expected_sparse_matches())

    def test_cross_page_native_store(self):
        c = self.cpu(); a = c.vm_map(2 * PAGE); c.reg('RBX', a + PAGE - 4); c.run(CODE)
        self.assertEqual(c.completed, 1)
        self.assertEqual(c.read_known(a + PAGE - 4, 8), VALUE.to_bytes(8, 'little'))
        self.assertEqual(len(c.vm_pages), 2)
        self.assertTrue(c.expected_sparse_matches())

    def test_cross_permission_store_rolls_back(self):
        c = self.cpu(); a = c.vm_map(2 * PAGE); c.read_known(a, 2 * PAGE)
        c.vm_change(a + PAGE, PAGE, 1); c.reg('RBX', a + PAGE - 4); c.run(CODE)
        self.assertEqual(c.completed, 0)
        self.assertEqual(c.vm_write_events, 0)
        self.assertEqual(bytes(c.uc.mem_read(a, 2 * PAGE)), bytes(2 * PAGE))
        self.assertTrue(c.expected_sparse_matches())

    def test_cross_reservation_store_rolls_back(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.read_known(a, PAGE)
        c.reg('RBX', a + PAGE - 4); c.run(CODE)
        self.assertEqual(c.completed, 0)
        self.assertEqual(bytes(c.uc.mem_read(a, PAGE)), bytes(PAGE))
        self.assertTrue(c.expected_sparse_matches())

    def test_write_cap_preserves_first_instruction(self):
        c = self.cpu('488903488903', 2); a = c.vm_map(PAGE); c.reg('RBX', a)
        c.MAX_VM_EVENTS = 1; c.run(CODE)
        self.assertEqual(c.completed, 1)
        self.assertEqual(c.stop['reason'], 'SPARSE_WRITE_BUDGET')
        self.assertEqual(c.vm_write_events, 1)
        self.assertTrue(c.expected_sparse_matches())

    def test_byte_cap_rejects_native_store(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.reg('RBX', a); c.MAX_VM_WRITE_BYTES = 7; c.run(CODE)
        self.assertEqual(c.completed, 0)
        self.assertEqual(c.vm_write_events, 0)
        self.assertTrue(c.expected_sparse_matches())

    def test_readonly_and_inaccessible_pages(self):
        for prot in (0, 1):
            with self.subTest(prot=prot):
                c = self.cpu(); a = c.vm_map(PAGE, prot); c.reg('RBX', a); c.run(CODE)
                self.assertEqual(c.completed, 0)
                self.assertEqual(c.vm_write_events, 0)
                self.assertTrue(c.expected_sparse_matches())

    def test_virtual_permissions_and_unmap(self):
        c = self.cpu(); a = c.vm_map(3 * PAGE); c.write_model_memory(a + PAGE, b'abc')
        c.vm_change(a + PAGE, PAGE, 1)
        self.assertIsNone(c.vm_cover(a, 3 * PAGE, 2))
        self.assertEqual(c.read_known(a + PAGE, 3), b'abc')
        c.vm_change(a + PAGE, PAGE, remove=True)
        self.assertIsNone(c.vm_cover(a + PAGE, 1))
        self.assertNotIn(a + PAGE, c.vm_pages)
        self.assertEqual(c.vm_reserved(), 2 * PAGE)

    def test_discard_zeroes_data_and_ledger(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.write_model_memory(a, b'abc'); c.vm_advice(a, PAGE, 4)
        self.assertEqual(c.read_known(a, 3), bytes(3))
        self.assertTrue(c.expected_sparse_matches())
        self.assertEqual(c.os_fixture['advice'], [[a, PAGE, 4]])

    def test_nondiscard_advice_preserves_bytes(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.write_model_memory(a, b'abc')
        for advice in (8, 16, 17): c.vm_advice(a, PAGE, advice)
        self.assertEqual(c.read_known(a, 3), b'abc')

    def test_unknown_advice_and_executable_mapping_rejected(self):
        c = self.cpu(); a = c.vm_map(PAGE)
        with self.assertRaises(ModelHalt): c.vm_advice(a, PAGE, 999)
        c = self.cpu()
        with self.assertRaises(ModelHalt): c.vm_map(PAGE, 7)

    def test_unaccounted_mutation_rejects_checkpoint(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.read_known(a, 1); c.uc.mem_write(a, b'x')
        self.assertFalse(c.expected_sparse_matches())
        with self.assertRaises(ValueError): c.capture_sparse()

    def test_checkpoint_roundtrip(self):
        c = self.cpu(); a = c.vm_map(1 << 30); c.write_model_memory(a + PAGE - 2, b'abcdef')
        c.vm_change(a + 2 * PAGE, PAGE, 0)
        state = copy.deepcopy(c.capture_sparse()); d = self.cpu(); d.restore_sparse(state)
        self.assertEqual(d.capture_sparse(), state)
        self.assertEqual(d.read_known(a + PAGE - 2, 6), b'abcdef')
        self.assertTrue(d.expected_sparse_matches())

    def test_checkpoint_rejects_invalid_regions_and_pages(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.write_model_memory(a, b'x'); original = c.capture_sparse()
        changes = [lambda s: s['regions'][0].update(prot=7),
                   lambda s: s['regions'][0].update(start=a+1),
                   lambda s: s['regions'].append(dict(s['regions'][0])),
                   lambda s: s.update(next=BASE-1),
                   lambda s: s['pages'].update({str(a+PAGE): next(iter(s['pages'].values()))})]
        for change in changes:
            with self.subTest(change=change):
                state = copy.deepcopy(original); change(state)
                with self.assertRaises(ValueError): self.cpu().restore_sparse(state)

    def test_model_write_cap_rejects_without_mutation(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.MAX_VM_WRITE_BYTES = 2
        with self.assertRaises(ModelHalt): c.write_model_memory(a, b'abc')
        self.assertEqual(c.vm_pages, {})
        self.assertEqual(c.vm_write_events, 0)

    def test_checkpoint_rejects_negative_and_overbudget_counters(self):
        c = self.cpu(); c.vm_map(PAGE); original = c.capture_sparse()
        for key, value in [('write_events', -1), ('write_bytes', -1),
                           ('map_calls', -1), ('unmap_calls', -1), ('protect_calls', -1),
                           ('write_events', c.MAX_VM_EVENTS + 1),
                           ('write_bytes', c.MAX_VM_WRITE_BYTES + 1)]:
            with self.subTest(key=key, value=value):
                state = copy.deepcopy(original); state[key] = value
                with self.assertRaises(ValueError): self.cpu().restore_sparse(state)

    def test_checkpoint_rejects_backtracking_allocation_cursor(self):
        c = self.cpu(); a = c.vm_map(PAGE); state = copy.deepcopy(c.capture_sparse())
        state['next'] = a
        with self.assertRaises(ValueError): self.cpu().restore_sparse(state)

    def test_checkpoint_rejects_corrupt_page_payload(self):
        c = self.cpu(); a = c.vm_map(PAGE); c.read_known(a, 1)
        state = copy.deepcopy(c.capture_sparse()); state['pages'][str(a)] = 'not-valid-base64'
        with self.assertRaises((ValueError, TypeError)): self.cpu().restore_sparse(state)

    def test_cross_page_quota_failure_with_one_backed_page(self):
        for backed in (0, 1):
            with self.subTest(backed=backed):
                c = self.cpu(); a = c.vm_map(2 * PAGE); c.read_known(a + backed * PAGE, 1)
                c.reg('RBX', a + PAGE - 4); c.MAX_VM_WRITE_BYTES = 7; c.run(CODE)
                self.assertEqual(c.completed, 0)
                self.assertEqual(c.stop['reason'], 'SPARSE_WRITE_BUDGET')
                self.assertEqual(c.vm_write_events, 0)
                self.assertTrue(c.expected_sparse_matches())
                self.assertEqual(bytes(c.uc.mem_read(a + backed * PAGE, PAGE)), bytes(PAGE))

    def test_native_read_of_prot_none_rejected(self):
        c = self.cpu('488b03'); a = c.vm_map(PAGE, 0); c.reg('RBX', a); c.run(CODE)
        self.assertEqual(c.completed, 0)
        self.assertEqual(c.stop['reason'], 'SPARSE_PERMISSION_OR_RANGE')
        self.assertEqual(c.vm_pages, {})

    def test_huge_materialization_rejected_before_backing(self):
        c = self.cpu(); a = c.vm_map(1 << 38)
        self.assertFalse(c.vm_materialize(a, 1 << 38, 1))
        self.assertEqual(c.stop['reason'], 'SPARSE_BACKING_BUDGET')
        self.assertEqual(c.vm_pages, {})

    def test_full_checkpoint_roundtrip_with_errno_and_sparse_pages(self):
        import json
        from native_allocator_os_fixture_ysm_265 import model
        from native_guarded_checkpoint_ysm_265 import capture, restore
        def prepared():
            c = SparseGuardedCPU(io.StringIO(), 'heap', limit=1)
            c.add_image(CODE, b'\x90' * 16); c.protect_image(); return c
        c = prepared(); errno = model(c, '__errno_location')
        a = c.vm_map(1 << 30); c.write_model_memory(a + PAGE - 2, b'abcdef'); c.run(CODE)
        state = json.loads(json.dumps(capture(c))); d = prepared(); restore(d, state)
        self.assertEqual(model(d, '__errno_location'), errno)
        self.assertEqual(d.read_known(errno, 4), (2).to_bytes(4, 'little'))
        self.assertEqual(d.read_known(a + PAGE - 2, 6), b'abcdef')
        self.assertTrue(d.expected_sparse_matches())
        self.assertEqual(d.vm_reserved(), 1 << 30)
        self.assertEqual(d.vm_write_bytes, 6)
        self.assertEqual(d.origin_completed, 1)

    def test_restore_requires_fresh_vm(self):
        c = self.cpu(); c.vm_map(PAGE)
        with self.assertRaises(ValueError): c.restore_sparse(c.capture_sparse())

if __name__ == '__main__': unittest.main()
