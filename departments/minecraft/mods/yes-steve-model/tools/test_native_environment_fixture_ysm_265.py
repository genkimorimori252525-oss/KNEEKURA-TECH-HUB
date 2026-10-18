"""Authored environment model calls only; no original or guest instructions run."""
import copy
import io
import json
import struct
import unittest
from dataclasses import FrozenInstanceError
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_guarded_checkpoint_ysm_265 import capture, restore
from native_unicorn_guarded_ysm_265 import SP, ModelHalt

KEYS = ['TMPDIR', 'TMP', 'TEMP', 'TEMPDIR']

class EnvironmentTests(unittest.TestCase):
    def cpu(self): return ShadowGuardedCPU(io.StringIO(), 'heap', 1, 5)
    def call(self, c, key):
        from native_environment_fixture_ysm_265 import model
        c.write_private(SP + 256, key + b'\0'); c.reg('RDI', SP + 256)
        return model(c, 'secure_getenv')
    def snapshot(self, c):
        c.stop = {'reason': 'AUTHORED_TEST'}
        return json.loads(json.dumps(capture(c)))

    def test_declared_absence_preserves_default_and_exact_sequence(self):
        c = self.cpu(); c.configure_environment_absent(KEYS)
        for key in ['GLIBCXX_TUNABLES'] + KEYS: self.assertEqual(self.call(c, key.encode()), 0)
        self.assertEqual(c.environment['lookups'], ['GLIBCXX_TUNABLES'] + KEYS)
        self.assertEqual(c.environment_model_calls, 5)
        self.assertEqual(c.attempted, 0)

    def test_tmpdir_only_stops_at_next_key(self):
        c = self.cpu(); c.configure_environment_absent(['TMPDIR'])
        self.assertEqual(self.call(c, b'TMPDIR'), 0)
        with self.assertRaises(ModelHalt): self.call(c, b'TMP')
        self.assertEqual(c.environment['lookups'], ['TMPDIR'])

    def test_prior_default_unchanged(self):
        c = self.cpu(); self.assertEqual(self.call(c, b'GLIBCXX_TUNABLES'), 0)
        with self.assertRaises(ModelHalt): self.call(c, b'TMPDIR')
        self.assertEqual(c.environment_model_calls, 1)

    def test_generic_named_key_supported(self):
        c = self.cpu(); c.configure_environment_absent(['AUTHORED_KEY'])
        self.assertEqual(self.call(c, b'AUTHORED_KEY'), 0)
        with self.assertRaises(ModelHalt): self.call(c, b'OTHER_KEY')

    def test_duplicate_malformed_present_configuration_rejected(self):
        for keys in [['TMP', 'TMP'], [''], ['A=B'], ['a b'], ['é'], ['1A'], ['A'*65], [1], 'TMP', {'TMP': '/tmp'}, ['K'+str(n) for n in range(33)]]:
            with self.subTest(keys=keys), self.assertRaises(ValueError): self.cpu().configure_environment_absent(keys)

    def test_invalid_guest_keys_and_unknown_memory_leave_ledger_unchanged(self):
        for key in [b'', b'A=B', b'\xff', b'A'*256]:
            c = self.cpu()
            with self.assertRaises(ModelHalt): self.call(c, key)
            self.assertEqual(c.environment_model_calls, 0)
        from native_environment_fixture_ysm_265 import model
        c = self.cpu(); c.reg('RDI', 0xdeadbeef)
        with self.assertRaises(ModelHalt): model(c, 'secure_getenv')

    def test_live_configuration_and_ledger_tampering_rejected(self):
        for mutate in [lambda s: s['absent_keys'].append('TMP'), lambda s: s['lookups'].append('TMP'), lambda s: s.update(legacy_calls=True), lambda s: s.update(extra=1)]:
            c = self.cpu(); mutate(c.environment)
            with self.assertRaises(ValueError): self.call(c, b'GLIBCXX_TUNABLES')
            with self.assertRaises(ValueError): self.snapshot(c)

    def test_declaration_frozen_and_reconfiguration_rejected(self):
        c = self.cpu(); c.configure_environment_absent(['TMP'])
        with self.assertRaises(FrozenInstanceError): c.environment_declaration.absent_keys = ('TEMP',)
        with self.assertRaises(ValueError): c.configure_environment_absent(['TEMP'])
        c.configure_environment_absent(['TMP'])

    def test_checkpoint_roundtrip_and_stale_requested_configuration(self):
        c = self.cpu(); c.configure_environment_absent(KEYS); self.call(c, b'TMPDIR')
        s = self.snapshot(c); original = copy.deepcopy(s); d = self.cpu(); restore(d, s)
        self.assertEqual(d.environment, c.environment); self.assertEqual(d.attempted, 0)
        self.assertEqual(self.call(d, b'TMP'), 0); self.assertEqual(s, original)
        with self.assertRaises(ValueError): d.configure_environment_absent(['TMPDIR'], allow_legacy_extension=True)
        e = self.cpu(); e.configure_environment_absent(['TEMP'])
        with self.assertRaises(ValueError): restore(e, s)

    def test_checkpoint_bad_types_provenance_ledger_and_count_rejected(self):
        c = self.cpu(); c.configure_environment_absent(KEYS); self.call(c, b'TMP')
        s = self.snapshot(c)
        for mutate in [lambda t: t.update(legacy_extension=1), lambda t: t.update(legacy_calls=-1), lambda t: t.update(lookups=['OTHER']), lambda t: t['import'].update(index=120), lambda t: t['absent_keys'].append('TMP'), lambda t: t.update(extra=0)]:
            bad = copy.deepcopy(s); mutate(bad['environment'])
            with self.assertRaises(ValueError): restore(self.cpu(), bad)
        bad = copy.deepcopy(s); bad['fields']['environment_model_calls'] += 1
        with self.assertRaises(ValueError): restore(self.cpu(), bad)

    def test_legacy_extension_explicit_and_preserves_count(self):
        c = self.cpu(); self.call(c, b'GLIBCXX_TUNABLES'); s = self.snapshot(c); s.pop('environment')
        before = copy.deepcopy(s); d = self.cpu(); restore(d, s)
        with self.assertRaises(ValueError): d.configure_environment_absent(KEYS)
        d.configure_environment_absent(KEYS, allow_legacy_extension=True)
        self.assertEqual(d.environment['legacy_calls'], 1)
        self.assertTrue(d.environment['legacy_extension'])
        self.call(d, b'TMPDIR'); self.assertEqual(d.environment_model_calls, 2)
        e = self.cpu(); restore(e, self.snapshot(d)); self.assertEqual(e.environment, d.environment)
        self.assertEqual(s, before)

    def test_new_default_snapshot_also_requires_explicit_extension(self):
        c = self.cpu(); s = self.snapshot(c); d = self.cpu(); restore(d, s)
        with self.assertRaises(ValueError): d.configure_environment_absent(KEYS)
        d.configure_environment_absent(KEYS, allow_legacy_extension=True)

    def test_lazy_import_identity_checked_before_model(self):
        for corrupt in ['slot', 'stub', None]:
            c = self.cpu(); c.configure_environment_absent(['TMP'])
            slot, stub, index, target = 0x184d3e0, 0x14bdbd9, 121, 0x100000
            c.add_image(slot, struct.pack('<Q', stub + (corrupt == 'slot')), False)
            c.add_image(stub, b'\x68' + struct.pack('<I', index + (corrupt == 'stub')))
            c.add_image(target, b'\xc3'); c.protect_image()
            c.write_private(SP + 32, struct.pack('<QQQQ', 0, 0, index, target)); c.reg('RSP', SP + 32)
            c.write_private(SP + 256, b'TMP\0'); c.reg('RDI', SP + 256)
            if corrupt:
                with self.assertRaises(ModelHalt): c.model('lazy-import')
                self.assertEqual(c.environment_model_calls, 0)
            else:
                c.model('lazy-import'); self.assertEqual(c.reg('RAX'), 0); self.assertEqual(c.environment_model_calls, 1)
            self.assertEqual(c.attempted, 0)

    def test_absence_does_not_authorize_tmp_stat(self):
        from native_allocator_os_fixture_ysm_265 import model
        from native_sparse_vm_ysm_265 import SparseGuardedCPU
        c = SparseGuardedCPU(io.StringIO(), 'heap', 1, 5); c.configure_environment_absent(KEYS)
        # Authored algebra for static plan: all four null results select literal /tmp.
        self.assertTrue(all(self.call(c, k.encode()) == 0 for k in KEYS))
        c.write_private(SP + 256, b'/tmp\0'); c.reg('RDI', 1); c.reg('RSI', SP + 256); c.reg('RDX', SP + 512)
        with self.assertRaises(ModelHalt): model(c, '__xstat')
        self.assertEqual(c.stop['reason'], 'UNMODELED_STAT_PATH_OR_ABI')
        self.assertEqual(c.attempted, 0)

    def test_comparison_rejects_different_declaration_same_counts(self):
        from compare_native_guarded_checkpoints_ysm_265 import compare
        c = self.cpu(); c.configure_environment_absent(['TMP'])
        d = self.cpu(); d.configure_environment_absent(['TEMP'])
        a, b = self.snapshot(c), self.snapshot(d)
        self.assertFalse(compare(a, b)['all_checks_pass'])
        self.assertTrue(compare(a, copy.deepcopy(a))['all_checks_pass'])

    def test_cli_rejects_bad_inputs_before_any_image_read(self):
        import subprocess
        import sys
        from pathlib import Path
        command = [sys.executable, str(Path(__file__).with_name('native_jni_onload_ysm_265.py')),
                   '--image', '/does-not-exist', '--resume-jni-checkpoint', '/does-not-exist',
                   '--out', '/does-not-exist/out', '--checkpoint-out', '/does-not-exist/checkpoint']
        for args, message in [(['--allow-environment-extension'], 'requires --environment-absent-key'),
                              (['--environment-absent-key', 'TMP', '--environment-absent-key', 'TMP'], 'Duplicate'),
                              (['--environment-absent-key', 'TMP=/tmp'], 'Malformed')]:
            result = subprocess.run(command + args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2); self.assertIn(message, result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_wrong_symbol_and_lookup_budget_rejected(self):
        from native_environment_fixture_ysm_265 import model, MAX_LOOKUPS
        c = self.cpu()
        with self.assertRaises(ValueError): model(c, 'getenv')
        c.environment['lookups'] = ['GLIBCXX_TUNABLES'] * MAX_LOOKUPS
        c.environment_model_calls = MAX_LOOKUPS
        with self.assertRaises(ModelHalt): self.call(c, b'GLIBCXX_TUNABLES')
        self.assertEqual(c.environment_model_calls, MAX_LOOKUPS)

if __name__ == '__main__': unittest.main()
