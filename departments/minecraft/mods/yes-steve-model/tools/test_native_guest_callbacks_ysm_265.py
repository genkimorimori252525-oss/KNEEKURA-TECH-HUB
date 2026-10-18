"""Own ELF bytes and guest callbacks only; never run a target library or host loader."""
import copy
import io
import json
import struct
import unittest

from native_guarded_checkpoint_ysm_265 import capture, restore
from native_jni_fixture_ysm_265 import CALLEE, CALLBACK_RETURN, JniGuardedCPU
from native_unicorn_guarded_ysm_265 import ModelHalt, SP

CODE = 0x100000
TARGET = CODE + 0x100
DATA = SP + 128
STUB = 0x15eda1c
SLOT = 0x184d1a8


class GuestCallbackTests(unittest.TestCase):
    def cpu(self, result=0, code=None, configured=True):
        c = JniGuardedCPU(io.StringIO(), 'heap', limit=5)
        header = bytearray(64 + 56)
        header[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<Q', header, 32, 64)
        struct.pack_into('<HH', header, 54, 56, 1)
        c.add_image(0, bytes(header), False)
        # Save callback's info and size into supplied user data, then return int.
        if code is None: code = bytes.fromhex('48893a48897208b8') + struct.pack('<I', result) + b'\xc3'
        c.add_image(CODE, code.ljust(0x110, b'\x90'))
        c.add_image(STUB, b'\x68' + struct.pack('<I', 50))
        c.add_image(SLOT, struct.pack('<Q', STUB), False)
        c.configure_loader('image-only')
        c.protect_image()
        if configured: c.configure_jni()
        return c

    def begin(self, c, function=CODE):
        c.write_private(SP, struct.pack('<QQQQ', 0, 0, 50, TARGET))
        c.write_private(DATA, bytes(16))
        c.reg('RSP', SP)
        c.reg('RDI', function)
        c.reg('RSI', DATA)
        for index, name in enumerate(CALLEE): c.reg(name, 0x1110 + index)
        c.model('lazy-import')

    def assert_returned(self, c, result):
        self.assertEqual(c.reg('RIP'), TARGET)
        self.assertEqual(c.reg('RSP'), SP + 32)
        self.assertEqual(c.reg('RAX'), result)
        self.assertEqual(c.jni_state['pending_callbacks'], [])
        self.assertEqual(c.jni_state['phdr_callbacks'], 1)
        self.assertEqual(c.read_known(SP + 24, 8), struct.pack('<Q', TARGET))
        for index, name in enumerate(CALLEE): self.assertEqual(c.reg(name), 0x1110 + index)

    def test_guest_callback_executes_and_returns_zero_or_nonzero(self):
        for result in (0, 17, 0xffffffff):
            with self.subTest(result=result):
                c = self.cpu(result)
                self.begin(c)
                info = c.jni_state['phdr_info']
                self.assertEqual(c.reg('RDI'), info)
                self.assertEqual(c.reg('RSI'), 64)
                self.assertEqual(c.reg('RDX'), DATA)
                self.assertEqual(c.read_known(info, 64), struct.pack('<QQQH6xQQQQ', 0, c.loader_name, 64, 1, 1, 0, 1, 0))
                self.assertEqual(c.read_known(SP + 24, 8), struct.pack('<Q', CALLBACK_RETURN))
                c.run(c.reg('RIP'))
                self.assertEqual(c.stop['reason'], 'INSTRUCTION_BUDGET')
                self.assertEqual(c.read_known(DATA, 16), struct.pack('<QQ', info, 64))
                self.assert_returned(c, result)

    def test_callback_callee_saved_register_violation_stops(self):
        c = self.cpu(code=bytes.fromhex('48ffc3c3'))  # inc rbx; ret
        self.begin(c)
        c.run(c.reg('RIP'))
        self.assertEqual(c.stop['reason'], 'CALLBACK_ABI_MISMATCH')
        self.assertEqual(len(c.jni_state['pending_callbacks']), 1)

    def test_callback_stack_violation_stops(self):
        c = self.cpu()
        self.begin(c)
        c.reg('RSP', SP + 40)
        with self.assertRaisesRegex(ModelHalt, 'CALLBACK_ABI_MISMATCH'):
            c.finish_phdr_callback()
        self.assertEqual(len(c.jni_state['pending_callbacks']), 1)

    def test_unmapped_and_gateway_callbacks_are_rejected(self):
        for function in (0, 0xdeadbeef, CALLBACK_RETURN):
            with self.subTest(function=function):
                c = self.cpu()
                with self.assertRaisesRegex(ModelHalt, 'INVALID_PROGRAM_HEADER_CALLBACK'):
                    self.begin(c, function)
                self.assertEqual(c.jni_state['pending_callbacks'], [])
                self.assertEqual(c.jni_state['phdr_callbacks'], 0)

    def pending_checkpoint(self):
        c = self.cpu(result=17)
        self.begin(c)
        c.limit = 1
        c.run(c.reg('RIP'))
        return c, json.loads(json.dumps(capture(c)))

    def test_pending_checkpoint_resumes_actual_guest_callback(self):
        c, state = self.pending_checkpoint()
        d = self.cpu(result=17, configured=False)
        restore(d, state)
        self.assertEqual(d.jni_state, c.jni_state)
        self.assertEqual(d.read_known(SP + 24, 8), struct.pack('<Q', CALLBACK_RETURN))
        d.limit = 4
        d.run(d.reg('RIP'))
        self.assert_returned(d, 17)
        self.assertEqual(d.read_known(DATA, 16), struct.pack('<QQ', d.jni_state['phdr_info'], 64))

    def test_invalid_pending_checkpoint_fields_are_rejected(self):
        _, original = self.pending_checkpoint()
        changes = [
            lambda s: s['pending_callbacks'][0]['saved'].update(RBX=-1),
            lambda s: s.update(phdr_info=0),
            lambda s: s.update(phdr_callbacks=0),
            lambda s: s['pending_callbacks'][0].update(data='bad'),
            lambda s: s.update(phdr_callbacks=-1),
            lambda s: s.update(phdr_callbacks=True),
            lambda s: s.update(phdr_info=1),
            lambda s: s['pending_callbacks'][0].update(sp=0),
            lambda s: s['pending_callbacks'][0].update(function=0xdeadbeef),
            lambda s: s['pending_callbacks'][0].update(target=0),
            lambda s: s['pending_callbacks'][0].update(saved={}),
            lambda s: s['pending_callbacks'][0].update(unexpected=True),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                state = copy.deepcopy(original)
                change(state['sparse']['jni'])
                with self.assertRaises(ValueError): restore(self.cpu(result=17, configured=False), state)


if __name__ == '__main__':
    unittest.main()
