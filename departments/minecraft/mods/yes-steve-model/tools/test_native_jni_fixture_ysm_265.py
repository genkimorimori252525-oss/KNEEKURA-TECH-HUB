"""Own-byte JNI tables and checkpoints; no JVM or target library execution."""
import copy
import io
import json
import struct
import unittest

from unicorn import UC_PROT_READ, UC_PROT_EXEC

from native_guarded_checkpoint_ysm_265 import capture, restore
from native_initializer_sequence_ysm_265 import prepare_call
from native_jni_fixture_ysm_265 import (
    ENV_NAMES, ENV_TABLE, JniGuardedCPU, TRAPS, VERSION, VM_NAMES, VM_TABLE, table,
)
from native_unicorn_guarded_ysm_265 import ModelHalt, SP, X

CODE = 0x100000


class JniFixtureTests(unittest.TestCase):
    def cpu(self, code=b'\xc3', configured=True):
        c = JniGuardedCPU(io.StringIO(), 'heap', limit=8)
        c.add_image(CODE, code + b'\x90' * 16)
        c.protect_image()
        if configured:
            c.configure_jni()
        return c

    def arguments(self, c, category='vm', name='GetEnv', pointer=None,
                  output=SP + 64, version=VERSION):
        names = VM_NAMES if category == 'vm' else ENV_NAMES
        gateway = TRAPS + 16 * (names.index(name) + (0 if category == 'vm' else 8))
        c.write_private(SP, struct.pack('<Q', CODE))
        c.reg('RSP', SP)
        c.reg('RDI', c.jni_state[category] if pointer is None else pointer)
        c.reg('RSI', output)
        c.reg('RDX', version)
        c.reg('RAX', 0x11223344)
        c.pc = gateway
        c.reg('RIP', gateway)
        return gateway

    def test_getenv_returns_attached_env_and_pops_import_frame(self):
        c = self.cpu()
        self.arguments(c)
        c.model('jni-import')
        self.assertEqual(c.read_known(SP + 64, 8), struct.pack('<Q', c.jni_state['env']))
        self.assertEqual(c.reg('RAX'), 0)
        self.assertEqual(c.reg('RSP'), SP + 8)
        self.assertEqual(c.reg('RIP'), CODE)
        self.assertEqual(c.jni_state['getenv_calls'], 1)
        self.assertEqual(c.jni_state['calls'], [['vm', 6, 'GetEnv']])

    def test_getversion_and_real_gateway_dispatch(self):
        c = self.cpu()
        gateway = self.arguments(c, 'env', 'GetVersion')
        # The own-byte RET at CODE then consumes this second return address.
        c.write_private(SP + 8, struct.pack('<Q', CODE))
        c.limit = 1
        c.run(gateway)
        self.assertEqual(c.stop['reason'], 'INSTRUCTION_BUDGET')
        self.assertEqual(c.reg('RAX'), VERSION)
        self.assertEqual(c.reg('RSP'), SP + 8)
        self.assertEqual(c.reg('RIP'), CODE)
        self.assertEqual(c.jni_state['getversion_calls'], 1)

    def test_cloned_invoke_interface_is_accepted_by_contents(self):
        c = self.cpu()
        copied_table, copied_handle = SP + 128, SP + 256
        c.write_private(copied_table, table(VM_NAMES, 0))
        c.write_private(copied_handle, struct.pack('<Q', copied_table))
        self.arguments(c, pointer=copied_handle)
        c.model('jni-import')
        self.assertEqual(c.reg('RAX'), 0)
        self.assertEqual(c.jni_state['getenv_calls'], 1)

    def test_tables_and_handles_are_readonly(self):
        c = self.cpu()
        self.assertEqual(len(ENV_NAMES), 234)
        self.assertEqual(c.read_known(VM_TABLE, 64), table(VM_NAMES, 0))
        self.assertEqual(c.read_known(ENV_TABLE, len(ENV_NAMES) * 8), table(ENV_NAMES, 8))
        for key in ('vm', 'env'):
            address = c.jni_state[key]
            before = c.read_known(address, 8)
            with self.assertRaises(ModelHalt):
                c.write_model_memory(address, b'x')
            self.assertEqual(c.read_known(address, 8), before)
        with self.assertRaises(ValueError):
            c.configure_jni()

    def test_invalid_getenv_inputs_do_not_return_success(self):
        for case in ('version', 'null-output', 'readonly-output', 'null-vm',
                     'wrong-interface', 'bad-frame', 'bad-return'):
            with self.subTest(case=case):
                c = self.cpu()
                kwargs = {'version': 0x10008} if case == 'version' else {}
                if case == 'null-output': kwargs['output'] = 0
                if case == 'readonly-output': kwargs['output'] = c.jni_state['env']
                if case == 'null-vm': kwargs['pointer'] = 0
                if case == 'wrong-interface': kwargs['pointer'] = c.jni_state['env']
                self.arguments(c, **kwargs)
                if case == 'bad-frame': c.reg('RSP', 0)
                if case == 'bad-return': c.write_private(SP, bytes(8))
                before = copy.deepcopy(c.jni_state)
                with self.assertRaises(ModelHalt): c.model('jni-import')
                self.assertEqual(c.jni_state, before)
                self.assertEqual(c.reg('RAX'), 0x11223344)

    def test_findclass_declared_runtime_exception_returns_opaque_handle(self):
        c = self.cpu()
        for _ in range(2):
            c.write_private(SP + 128, b'java/lang/RuntimeException\0')
            self.arguments(c, 'env', 'FindClass', output=SP + 128)
            c.model('jni-import')
            self.assertEqual(c.reg('RAX'), 0x790000000000)
            self.assertEqual(c.reg('RSP'), SP + 8)
            self.assertEqual(c.reg('RIP'), CODE)
        self.assertEqual(c.jni_state['classes'], {str(0x790000000000): 'java/lang/RuntimeException'})
        self.assertEqual(c.jni_state['calls'], [['env', 6, 'FindClass']] * 2)
        self.assertIsNotNone(c.unknown(0x790000000000, 1))
        prepare_call(c, CODE)
        c.run(CODE)
        d = self.cpu(configured=False)
        restore(d, json.loads(json.dumps(capture(c))))
        self.assertEqual(d.jni_state['classes'], c.jni_state['classes'])

    def test_findclass_unknown_name_stops_without_creating_handle(self):
        c = self.cpu()
        c.write_private(SP + 128, b'example/UnmodeledClass\0')
        self.arguments(c, 'env', 'FindClass', output=SP + 128)
        before = copy.deepcopy(c.jni_state)
        with self.assertRaisesRegex(ModelHalt, 'UNMODELED_JAVA_CLASS'):
            c.model('jni-import')
        self.assertEqual(c.jni_state, before)
        self.assertEqual(c.reg('RAX'), 0x11223344)

    def artifact_address_fixture(self, body):
        c = self.cpu()
        base = 0x7b0000000000
        c.uc.mem_map(base, 4096, UC_PROT_READ | UC_PROT_EXEC)
        c.jni_state['jvm_interfaces'] = {
            kind: [0 if name.startswith('reserved') else base + 16 * (offset + i)
                   for i, name in enumerate(names)]
            for kind, names, offset in [('vm', VM_NAMES, 0), ('env', ENV_NAMES, 8)]
        }
        c.rebuild_jni_interfaces()
        gateway = c.jni_state['jvm_interfaces']['env'][4]
        c.uc.mem_write(gateway, body)
        c.jvm_interfaces_ready = True
        self.arguments(c, 'env', 'GetVersion')
        c.reg('RIP', gateway)
        return c, gateway

    def test_artifact_address_gateway_intercepts_before_own_first_instruction(self):
        # These are authored bytes, not JVM code. Neither first instruction may execute.
        for body in (bytes.fromhex('49c7c701000000c3'), bytes.fromhex('488903c3')):
            with self.subTest(body=body.hex()):
                c, gateway = self.artifact_address_fixture(body)
                c.reg('R15', 0xabcdef)
                c.reg('RBX', SP + 256)
                c.write_private(SP + 256, b'unchange')
                c.limit = 1
                c.run(gateway)
                self.assertEqual(c.reg('RAX'), VERSION)
                self.assertEqual(c.reg('R15'), 0xabcdef)
                self.assertEqual(c.read_known(SP + 256, 8), b'unchange')
                self.assertEqual(c.reg('RIP'), CODE)
                self.assertEqual(c.jni_state['getversion_calls'], 1)
                self.assertEqual(c.completed, 1)
                self.assertIn('intercepted_before_first_instruction=true', c.out.getvalue())

    def test_artifact_gateway_neighbor_and_unready_gateway_are_blocked(self):
        for ready, offset in ((True, 1), (False, 0)):
            with self.subTest(ready=ready, offset=offset):
                c, gateway = self.artifact_address_fixture(bytes.fromhex('49ffc7c3'))
                c.jvm_interfaces_ready = ready
                c.reg('R15', 0xabcdef)
                self.assertFalse(c.code_allowed(gateway + offset))
                c.run(gateway + offset)
                self.assertEqual(c.stop['reason'], 'EXTERNAL_OR_NULL_TARGET')
                self.assertEqual(c.reg('R15'), 0xabcdef)
                self.assertEqual(c.attempted, 0)
                self.assertEqual(c.jni_state['getversion_calls'], 0)

    def declare_exception_class(self, c):
        c.write_private(SP + 128, b'java/lang/RuntimeException\0')
        self.arguments(c, 'env', 'FindClass', output=SP + 128)
        c.model('jni-import')
        return c.reg('RAX')

    def test_thrownew_records_exception_and_delete_preserves_it_on_restore(self):
        c = self.cpu()
        handle = self.declare_exception_class(c)
        c.write_private(SP + 192, b'own-byte exception message\0')
        self.arguments(c, 'env', 'ThrowNew', output=handle, version=SP + 192)
        c.model('jni-import')
        expected = {'class': 'java/lang/RuntimeException', 'message': 'own-byte exception message'}
        self.assertEqual(c.reg('RAX'), 0)
        self.assertEqual(c.jni_state['pending_exception'], expected)
        self.arguments(c, 'env', 'DeleteLocalRef', output=handle)
        c.model('jni-import')
        self.assertEqual(c.reg('RAX'), 0x11223344)  # void call does not invent a result
        self.assertEqual(c.jni_state['deleted_local_refs'], [handle])
        self.assertEqual(c.jni_state['pending_exception'], expected)
        prepare_call(c, CODE)
        c.run(CODE)
        d = self.cpu(configured=False)
        restore(d, json.loads(json.dumps(capture(c))))
        self.assertEqual(d.jni_state['pending_exception'], expected)
        self.assertEqual(d.jni_state['deleted_local_refs'], [handle])
        self.assertEqual(d.jni_state['calls'], c.jni_state['calls'])

    def test_thrownew_rejects_unknown_deleted_or_already_pending_class(self):
        for case in ('unknown', 'deleted', 'pending'):
            with self.subTest(case=case):
                c = self.cpu()
                handle = self.declare_exception_class(c)
                c.write_private(SP + 192, b'test\0')
                if case == 'deleted':
                    self.arguments(c, 'env', 'DeleteLocalRef', output=handle)
                    c.model('jni-import')
                if case == 'pending':
                    self.arguments(c, 'env', 'ThrowNew', output=handle, version=SP + 192)
                    c.model('jni-import')
                self.arguments(c, 'env', 'ThrowNew', output=0 if case == 'unknown' else handle, version=SP + 192)
                before = copy.deepcopy(c.jni_state)
                with self.assertRaisesRegex(ModelHalt, 'INVALID_JNI_THROW_CLASS_OR_STATE'):
                    c.model('jni-import')
                self.assertEqual(c.jni_state, before)

    def test_delete_local_ref_null_unknown_double_delete_and_reacquisition(self):
        c = self.cpu()
        self.arguments(c, 'env', 'DeleteLocalRef', output=0)
        c.model('jni-import')
        self.assertEqual(c.jni_state['deleted_local_refs'], [])
        handle = self.declare_exception_class(c)
        self.arguments(c, 'env', 'DeleteLocalRef', output=handle)
        c.model('jni-import')
        self.assertEqual(c.jni_state['deleted_local_refs'], [handle])
        self.assertEqual(self.declare_exception_class(c), handle)
        self.assertEqual(c.jni_state['deleted_local_refs'], [])
        for duplicate in (False, True):
            d = self.cpu()
            ref = self.declare_exception_class(d)
            if duplicate:
                self.arguments(d, 'env', 'DeleteLocalRef', output=ref)
                d.model('jni-import')
            self.arguments(d, 'env', 'DeleteLocalRef', output=ref if duplicate else 123)
            before = copy.deepcopy(d.jni_state)
            with self.assertRaisesRegex(ModelHalt, 'UNKNOWN_JNI_LOCAL_REFERENCE'):
                d.model('jni-import')
            self.assertEqual(d.jni_state, before)

    def test_unknown_jni_slot_stops_at_named_frontier(self):
        c = self.cpu()
        self.arguments(c, 'env', 'DefineClass')
        with self.assertRaisesRegex(ModelHalt, 'UNMODELED_JNI_CALL'):
            c.model('jni-import')
        self.assertEqual(c.jni_state['calls'], [])
        self.assertIn('DefineClass', c.out.getvalue() if hasattr(c, 'out') else '')

    def test_native_writes_to_gateway_and_tables_roll_back(self):
        for address in (TRAPS, ENV_TABLE, VM_TABLE, ENV_TABLE + 4092):
            with self.subTest(address=hex(address)):
                c = self.cpu(b'\x48\x89\x03')  # mov [rbx], rax
                c.reg('RBX', address)
                c.reg('RAX', 0xabcdef0123456789)
                before = {a: bytes(c.uc.mem_read(a, len(v))) for a, v in c.jni_expected.items()}
                c.run(CODE)
                self.assertEqual(c.stop['reason'], 'JNI_FIXTURE_WRITE_BLOCKED')
                self.assertEqual(c.completed, 0)
                for a, data in before.items(): self.assertEqual(bytes(c.uc.mem_read(a, len(data))), data)

    def checkpoint(self):
        c = self.cpu()
        self.arguments(c)
        c.model('jni-import')
        prepare_call(c, CODE)
        c.run(CODE)
        return c, json.loads(json.dumps(capture(c)))

    def test_full_checkpoint_restores_state_maps_and_readonly_handles(self):
        c, state = self.checkpoint()
        d = self.cpu(configured=False)
        restore(d, state)
        self.assertEqual(d.jni_state, c.jni_state)
        self.assertEqual(d.jni_expected, c.jni_expected)
        self.assertEqual(d.jni_gateways, c.jni_gateways)
        self.assertEqual(d.capture_sparse(), c.capture_sparse())
        for a, data in c.jni_expected.items(): self.assertEqual(d.read_known(a, len(data)), data)
        for key in ('vm', 'env'):
            address = d.jni_state[key]
            self.assertTrue(any(lo <= address and address + 8 <= hi for lo, hi in d.private_readonly))
        self.arguments(d, 'env', 'GetVersion')
        d.model('jni-import')
        self.assertEqual(d.reg('RAX'), VERSION)
        self.assertEqual(d.jni_state['getversion_calls'], 1)
        self.assertEqual(c.jni_state['getversion_calls'], 0)

    def test_malformed_restore_rejected(self):
        _, original = self.checkpoint()
        changes = [
            lambda s: s.update(version=0x10008),
            lambda s: s.update(table_slots=233),
            lambda s: s.update(getenv_calls=-1),
            lambda s: s.update(getversion_calls=True),
            lambda s: s.update(getenv_calls=4097),
            lambda s: s.update(calls=[['env', 4, 'GetVersion']] * 4097),
            lambda s: s.update(vm=0),
            lambda s: s.update(env=s['vm']),
            lambda s: s.update(unexpected=True),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                state = copy.deepcopy(original)
                change(state['sparse']['jni'])
                with self.assertRaises(ValueError): restore(self.cpu(configured=False), state)

    def test_restore_rejects_bad_ledger_and_lost_readonly_handles(self):
        _, original = self.checkpoint()
        changes = [
            lambda s: s['sparse']['jni'].update(calls=['fake']),
            lambda s: s['sparse']['jni'].update(calls=[['vm', 5, 'GetEnv']]),
            lambda s: s['sparse']['jni'].update(getenv_calls=99),
            lambda s: s['fields'].update(private_readonly=[]),
            lambda s: s['fields'].update(private_readonly=[
                [s['sparse']['jni']['vm'], s['sparse']['jni']['vm'] + 7],
                [s['sparse']['jni']['env'], s['sparse']['jni']['env'] + 8]]),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                state = copy.deepcopy(original)
                change(state)
                with self.assertRaises(ValueError): restore(self.cpu(configured=False), state)

    def test_declared_basic_cpuid_preserves_flags_and_unrelated_registers(self):
        c = self.cpu(bytes.fromhex('0fa290'))
        c.limit = 1
        c.cpuid_leaf1 = (0, 0, 0, 0)
        c.reg('RAX', 0)
        c.reg('RCX', 0xffffffff)
        c.reg('R15', 0x123456789abcdef)
        c.uc.reg_write(X.UC_X86_REG_EFLAGS, 0xa47)
        flags = c.uc.reg_read(X.UC_X86_REG_EFLAGS)
        c.run(CODE)
        self.assertEqual(c.reg('RAX'), 1)
        vendor = b''.join(c.reg(r).to_bytes(4, 'little') for r in ('RBX', 'RDX', 'RCX'))
        self.assertEqual(vendor, b'GenuineIntel')
        self.assertEqual(c.reg('R15'), 0x123456789abcdef)
        self.assertEqual(c.uc.reg_read(X.UC_X86_REG_EFLAGS), flags)
        self.assertEqual(c.jni_state['cpuid_basic_calls'], 1)
        self.assertEqual(c.reg('RIP'), CODE + 2)
        self.assertEqual(c.completed, 1)
        state = json.loads(json.dumps(capture(c)))
        d = self.cpu(bytes.fromhex('0fa290'), configured=False)
        restore(d, state)
        self.assertEqual(d.jni_state['cpuid_basic_calls'], 1)

    def test_declared_leaf7_subleaf0_returns_zero_fixture(self):
        c = self.cpu(bytes.fromhex('0fa290'))
        c.limit = 1
        c.cpuid_leaf1 = (0, 0, 0, 0)
        for r in ('RAX', 'RBX', 'RCX', 'RDX'): c.reg(r, 0xffffffffffffffff)
        c.reg('RAX', 7)
        c.reg('RCX', 0)
        c.run(CODE)
        self.assertEqual(tuple(c.reg(r) for r in ('RAX', 'RBX', 'RCX', 'RDX')), (0, 0, 0, 0))
        self.assertEqual(c.jni_state['cpuid_basic_calls'], 1)
        self.assertEqual(c.reg('RIP'), CODE + 2)
        self.assertEqual(c.completed, 1)

    def test_legacy_checkpoint_migrates_basic_cpuid_counter(self):
        _, state = self.checkpoint()
        del state['sparse']['jni']['cpuid_basic_calls']
        d = self.cpu(configured=False)
        restore(d, state)
        self.assertEqual(d.jni_state['cpuid_basic_calls'], 0)

    def test_invalid_basic_cpuid_counter_rejected(self):
        _, original = self.checkpoint()
        for value in (-1, True, 4097):
            with self.subTest(value=value):
                state = copy.deepcopy(original)
                state['sparse']['jni']['cpuid_basic_calls'] = value
                with self.assertRaises(ValueError): restore(self.cpu(configured=False), state)

    def test_preparation_rejects_overwriting_unfinished_frame(self):
        c = self.cpu()
        prepare_call(c, CODE)
        before = (c.reg('RSP'), c.reg('RIP'), c.read_known(SP, 8))
        with self.assertRaises(ValueError): prepare_call(c, CODE)
        self.assertEqual((c.reg('RSP'), c.reg('RIP'), c.read_known(SP, 8)), before)


if __name__ == '__main__':
    unittest.main()
