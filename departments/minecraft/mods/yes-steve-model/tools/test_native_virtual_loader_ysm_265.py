"""Synthetic loader boundary tests; no target library or host loader execution."""
import io,struct,unittest
from native_unicorn_guarded_ysm_265 import GuardedCPU,ModelHalt,SP,STACK,STACK_SIZE
THUNK=0x13d8466;SLOT=0x184d820;QUERY=0x200000;RET=0x100000
class LoaderTests(unittest.TestCase):
    def cpu(self,scenario='image-only'):
        c=GuardedCPU(io.StringIO(),limit=1);c.add_image(THUNK,bytes.fromhex('ff25b4534700'));c.add_image(SLOT,bytes(8),False);c.add_image(QUERY,b'query',False);c.add_image(RET,b'\x90');c.protect_image();c.configure_loader(scenario);c.write_private(SP,struct.pack('<Q',RET));c.reg('RDI',QUERY);c.reg('RSI',SP+64);return c
    def test_success_layout_and_return(self):
        c=self.cpu();c.run(THUNK);self.assertEqual(c.completed,1);self.assertEqual(c.reg('RAX'),1);self.assertEqual(c.reg('RSP'),SP+8);self.assertEqual(c.reg('RIP'),RET);self.assertEqual(struct.unpack('<QQQQ',c.read_known(SP+64,32)),(c.loader_name,0,0,0));self.assertEqual(c.ascii(c.loader_name),'/virtual/libysm-core.so');self.assertTrue(c.image_unchanged())
    def test_unavailable_does_not_fill_output(self):
        c=self.cpu('unavailable');c.run(THUNK);self.assertEqual(c.reg('RAX'),0);self.assertIsNotNone(c.unknown(SP+64,32));self.assertEqual(c.dladdr_calls,1)
    def test_disabled_stops(self):
        c=self.cpu('disabled');c.run(THUNK);self.assertEqual(c.dladdr_calls,0);self.assertEqual(c.stop['reason'],'EXTERNAL_OR_NULL_TARGET')
    def test_image_destination_rejected(self):
        c=self.cpu();c.reg('RSI',QUERY);c.run(THUNK);self.assertEqual(c.completed,0);self.assertEqual(c.dladdr_calls,0);self.assertTrue(c.image_unchanged());self.assertEqual(c.reg('RSP'),SP)
    def test_cross_stack_destination_rejected(self):
        c=self.cpu();c.reg('RSI',STACK+STACK_SIZE-16);c.run(THUNK);self.assertEqual(c.completed,0);self.assertEqual(c.dladdr_calls,0)
    def test_unknown_query_rejected(self):
        c=self.cpu();c.reg('RDI',SP);c.run(THUNK);self.assertEqual(c.stop['reason'],'QUERY_OUTSIDE_MODELED_IMAGE');self.assertEqual(c.dladdr_calls,0)
    def test_invalid_return_rejected_before_output(self):
        c=self.cpu();c.write_private(SP,bytes(8));c.run(THUNK);self.assertEqual(c.dladdr_calls,0);self.assertIsNotNone(c.unknown(SP+64,32))
    def test_name_is_not_code(self):
        c=self.cpu();self.assertFalse(c.code_allowed(c.loader_name));self.assertFalse(c.private_allowed(c.loader_name,1))
    def test_thunk_mismatch_rejected(self):
        c=self.cpu();c.uc.mem_write(THUNK,b'\x90');c.image=[(a,b,(b'\x90'+v[1:]) if a==THUNK else v) for a,b,v in c.image];c.run(THUNK);self.assertEqual(c.stop['reason'],'LOADER_THUNK_MISMATCH');self.assertEqual(c.dladdr_calls,0)
    def test_nonzero_slot_rejected(self):
        c=self.cpu();raw=struct.pack('<Q',RET);c.uc.mem_write(SLOT,raw);c.image=[(a,b,raw if a==SLOT else v) for a,b,v in c.image];c.run(THUNK);self.assertEqual(c.stop['reason'],'UNEXPECTED_IMPORT_SLOT_VALUE');self.assertEqual(c.dladdr_calls,0);self.assertIsNotNone(c.unknown(SP+64,32))
    def test_unknown_return_rejected(self):
        c=self.cpu();c.reg('RSP',SP+256);c.run(THUNK);self.assertEqual(c.stop['reason'],'UNINITIALIZED_READ');self.assertEqual(c.dladdr_calls,0)
    def test_scenario_validation(self):
        with self.assertRaises(ValueError):self.cpu('actual-host')
if __name__=='__main__':unittest.main()
