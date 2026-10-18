"""Byte/parser/provenance tests; never executes target code or a JVM."""
from pathlib import Path
import struct
import tempfile
import unittest

import recover_native_bindings_ysm_265 as recovery
from test_native_java_metadata_ysm_265 import class_bytes, fixture


class BindingRecoveryTests(unittest.TestCase):
    def metadata(self, access=0x109, name='run', descriptor='(J)V'):
        return fixture({'example/Owner.class': class_bytes(
            'example/Owner', methods=[(access, name, descriptor)])})

    def test_exact_payload(self):
        payload = b'Lexample/Owner;run(J)V\0'
        self.assertEqual(recovery.parse_payload(payload, len(payload)),
                         ('example/Owner', 'run', '(J)V'))

    def test_malformed_payloads_rejected(self):
        values = [b'example/Owner;run()V\0', b'Lx;r()V', b'Lx;r()V\0\0',
                  b'Lx;()V\0', b'Lx;r(I)invalid\0', b'Lx;r()Vjunk\0',
                  b'Lx;<init>()V\0', b'Lx;bad/name()V\0', b'Lx;r(\xff)V\0']
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                recovery.parse_payload(value, len(value))
        with self.assertRaises(ValueError):
            recovery.parse_payload(b'Lx;r()V\0', 100)

    def test_exact_native_static_abi(self):
        payload = b'Lexample/Owner;run(J)V\0'
        proof = recovery.declaration_proof(self.metadata(), payload,
                                          dict(length=len(payload), static=True))
        self.assertTrue(proof['acc_native'])
        self.assertEqual(proof['jni_second_argument'], 'jclass')
        self.assertEqual(proof['access'], 0x109)

    def test_observed_payload_hash_mismatch_rejected(self):
        payload = b'Lexample/Owner;run(J)V\0'
        with self.assertRaises(ValueError):
            recovery.declaration_proof(self.metadata(), payload,
                dict(length=len(payload), static=True, payload_sha256='0'*64))

    def test_same_length_other_valid_native_cannot_replace_payload(self):
        original = b'Lexample/Owner;run(J)V\0'
        swapped = b'Lexample/Owner;sun(J)V\0'
        metadata = fixture({'example/Owner.class': class_bytes('example/Owner',
                            methods=[(0x109, 'run', '(J)V'), (0x109, 'sun', '(J)V')])})
        self.assertEqual(len(original), len(swapped))
        with self.assertRaisesRegex(ValueError, 'pinned observed evidence'):
            recovery.declaration_proof(metadata, swapped,
                dict(length=len(original), static=True, payload_sha256=recovery.digest(original)))

    def test_exact_native_instance_abi(self):
        payload = b'Lexample/Owner;run(J)V\0'
        proof = recovery.declaration_proof(self.metadata(0x102), payload,
                                          dict(length=len(payload), static=False))
        self.assertEqual(proof['jni_second_argument'], 'jobject')

    def test_non_native_wrong_abi_and_descriptor_rejected(self):
        payload = b'Lexample/Owner;run(J)V\0'
        for metadata, static in [(self.metadata(9), True),
                                 (self.metadata(), False),
                                 (self.metadata(descriptor='(I)V'), True)]:
            with self.subTest(static=static), self.assertRaises(ValueError):
                recovery.declaration_proof(metadata, payload,
                                          dict(length=len(payload), static=static))

    def test_embedded_instruction_pairs_resolve_exact_targets(self):
        self.assertEqual(len(recovery.PAIRS), 17)
        self.assertEqual(sum(not row['static'] for row in recovery.PAIRS), 1)
        for index, row in enumerate(recovery.PAIRS):
            self.assertEqual(row['callback'], 0x418540 + index * 32)
            for slot, target in [(0, row['callback']), (2, row['native'])]:
                address, hexbytes = row['stores'][slot]
                code = bytes.fromhex(hexbytes)
                self.assertEqual(len(code), 7)
                self.assertEqual(code[1], 0x8d)
                self.assertEqual(address + 7 + struct.unpack_from('<i', code, 3)[0], target)
            self.assertEqual(bytes.fromhex(row['stores'][1][1])[-1], 0x18)
            self.assertEqual(bytes.fromhex(row['stores'][3][1])[-1], 0x20)

    def test_source_and_file_hashes_fail_closed(self):
        with self.assertRaises(ValueError):
            recovery.source_proof(b'not the original ELF')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_bytes(b'authored fixture')
            self.assertEqual(recovery.pinned(path, recovery.digest(path.read_bytes())), path.read_bytes())
            with self.assertRaises(ValueError):
                recovery.pinned(path, recovery.IMAGE_SHA)

    def test_exact_set_rejects_duplicates_and_omissions(self):
        records = [dict(owner='example/C', name='m'+str(i), descriptor='()V') for i in range(17)]
        expected = {(r['owner'], r['name'], r['descriptor']) for r in records}
        recovery.exact_set(records, expected)
        for bad in (records[:-1], records[:-1]+records[:1]):
            with self.assertRaises(ValueError):
                recovery.exact_set(bad, expected)

    def test_saved_proof_rejects_wrong_inputs_or_incomplete_records(self):
        with self.assertRaises(ValueError):
            recovery.verify_saved({}, None, [], set())
        saved = dict(image_sha256=recovery.IMAGE_SHA, jar_sha256=recovery.JAR_SHA,
                     checkpoint_sha256=recovery.CHECKPOINT_SHA, bindings=[])
        with self.assertRaises(ValueError):
            recovery.verify_saved(saved, None, [], set())

    def test_saved_source_metadata_corruption_rejected_before_decoding(self):
        proofs = [dict(callback=hex(row['callback']), native=hex(row['native']),
                       source=hex(row['source']), source_length=row['length'],
                       source_sha256=row['source_sha256'], callback_sha256=row['callback_sha256'],
                       registration_flags=0 if i < 6 else 2)
                  for i, row in enumerate(recovery.PAIRS)]
        for key in ('source', 'source_length', 'source_sha256', 'callback_sha256', 'registration_flags'):
            records = [dict(p, stop=dict(reason='ENTRY_RETURN')) for p in proofs]
            records[0][key] = 'tampered'
            saved = dict(image_sha256=recovery.IMAGE_SHA, jar_sha256=recovery.JAR_SHA,
                         checkpoint_sha256=recovery.CHECKPOINT_SHA, bindings=records)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Saved source proof mismatch'):
                recovery.verify_saved(saved, None, proofs, set())

    def test_resource_segments_continue_only_same_active_frame(self):
        class CPU:
            def __init__(self, reasons):
                self.reasons = iter(reasons)
                self.stop = None
                self.attempted = self.completed = 0
                self.pc = 100
                self.starts = []
            def reg(self, name):
                return self.pc
            def run(self, pc):
                self.starts.append(pc)
                self.pc += 7
                self.attempted = self.completed = 10
                self.stop = dict(reason=next(self.reasons))
                return self.stop
        cpu = CPU(['INSTRUCTION_BUDGET', 'ENTRY_RETURN'])
        stop, segments = recovery.run_segments(cpu, 2)
        self.assertEqual(cpu.starts, [100, 107])
        self.assertEqual(stop['reason'], 'ENTRY_RETURN')
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['attempted'], 10)
        for reason in ['UNKNOWN_IMPORT', 'UNINITIALIZED_READ', 'ENTRY_RETURN']:
            cpu = CPU([reason])
            stop, segments = recovery.run_segments(cpu, 2)
            self.assertEqual(len(segments), 1)
            self.assertEqual(stop['reason'], reason)
        cpu = CPU(['INSTRUCTION_BUDGET', 'INSTRUCTION_BUDGET'])
        self.assertEqual(len(recovery.run_segments(cpu, 2)[1]), 2)

    def test_cli_requires_paths_and_bounded_budgets(self):
        with self.assertRaises(SystemExit):
            recovery.main([])
        with self.assertRaises(ValueError):
            recovery.main(['--image', 'unused', '--jar', 'unused', '--checkpoint', 'unused',
                           '--out', 'unused', '--steps', '4000001'])


if __name__ == '__main__':
    unittest.main()
