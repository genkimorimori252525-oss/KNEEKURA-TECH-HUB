"""Pinned lazy-binding frame models. No real dynamic linker or operator new is called."""
import io,struct,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_unicorn_guarded_ysm_265 import SP,HEAP,RETURN
RET=0x100000;ENTRY=0x14f9c20
class LazyTests(unittest.TestCase):
 def cpu(self,index=250):
  c=ShadowGuardedCPU(io.StringIO(),'heap',1,5);c.add_image(RET,b'\x90'*32);c.add_image(ENTRY,b'\xc3');c.add_image(0x13d743c,bytes.fromhex('ff25a6634700'));c.add_image(0x13fe69d,bytes.fromhex('68fa000000'));c.add_image(0x184d7e8,struct.pack('<Q',0x13fe69d),False);c.add_image(0x184d680,struct.pack('<Q',0x1478e57),False);c.add_image(0x1478e57,bytes.fromhex('68cd000000'));c.add_image(0x184d640,struct.pack('<Q',0x14c39b7),False);c.add_image(0x14c39b7,bytes.fromhex('68c5000000'));c.add_image(0x184d048,struct.pack('<Q',0x15044c7),False);c.add_image(0x15044c7,bytes.fromhex('6806000000'));c.protect_image();c.write_private(SP,struct.pack('<QQQQ',0,0,index,RET));c.reg('RDI',24);return c
 def test_operator_new_private_allocation_and_frame(self):
  c=self.cpu();c.run(ENTRY);self.assertEqual(c.completed,1);self.assertEqual(c.reg('RAX'),HEAP);self.assertEqual(c.reg('RSP'),SP+32);self.assertEqual(c.reg('RIP'),RET);self.assertEqual(c.lazy_new_calls,1);self.assertEqual(c.malloc_calls,0);self.assertIsNotNone(c.unknown(HEAP,24));self.assertFalse(c.private_allowed(HEAP+24,1))
 def test_array_new_uses_same_bounded_heap(self):
  c=self.cpu(205);c.reg('RDI',2080);c.run(ENTRY);self.assertEqual(c.completed,1);self.assertEqual(c.allocations,[(HEAP,2080)]);self.assertEqual(c.lazy_new_calls,1);self.assertIn('symbol=_Znam',c.out.getvalue())
 def test_memset_initializes_private_bytes(self):
  c=self.cpu(197);a=c.allocate(24);c.reg('RDI',a);c.reg('RSI',0x1ab);c.reg('RDX',24);c.run(ENTRY);self.assertEqual(c.read_known(a,24),bytes([0xab])*24);self.assertEqual(c.reg('RAX'),a);self.assertEqual(c.lazy_memset_calls,1)
 def test_memset_rejects_outside_allocation(self):
  c=self.cpu(197);a=c.allocate(24);c.reg('RDI',a);c.reg('RDX',25);c.run(ENTRY);self.assertEqual(c.lazy_memset_calls,0);self.assertIsNotNone(c.unknown(a,24));self.assertEqual(c.stop['reason'],'MODEL_WRITE_OUTSIDE_GRANTED_RANGE')
 def test_memset_rejects_image_destination(self):
  c=self.cpu(197);c.reg('RDI',RET);c.reg('RDX',1);c.run(ENTRY);self.assertEqual(c.lazy_memset_calls,0);self.assertTrue(c.image_unchanged())
 def test_zero_memset_preserves_unknown_bytes(self):
  c=self.cpu(197);a=c.allocate(8);c.reg('RDI',a);c.reg('RDX',0);c.run(ENTRY);self.assertEqual(c.reg('RAX'),a);self.assertIsNotNone(c.unknown(a,8));self.assertEqual(c.lazy_memset_calls,1)
 def test_atexit_records_without_executing_callback(self):
  c=self.cpu(6);c.reg('RDI',RET);c.reg('RSI',123);c.reg('RDX',456);c.run(ENTRY);self.assertEqual(c.atexit_registrations,[[RET,123,456]]);self.assertEqual(c.reg('RAX'),0);self.assertEqual(c.completed,1)
 def test_invalid_atexit_function_rejected(self):
  c=self.cpu(6);c.reg('RDI',0);c.run(ENTRY);self.assertEqual(c.atexit_registrations,[]);self.assertEqual(c.stop['reason'],'UNMODELED_ATEXIT_REGISTRATION')
 def test_atexit_tail_return_finishes_entry(self):
  c=self.cpu(6);c.reg('RSP',SP-24);c.write_private(SP-24,struct.pack('<QQQQ',0,0,6,RETURN));c.reg('RDI',RET);c.run(ENTRY);self.assertEqual(c.stop['reason'],'ENTRY_RETURN');self.assertEqual(c.completed,1);self.assertEqual(c.reg('RSP'),SP+8);self.assertEqual(len(c.atexit_registrations),1)
 def test_wrong_stack_tail_return_rejected(self):
  c=self.cpu(6);c.write_private(SP+24,struct.pack('<Q',RETURN));c.reg('RDI',RET);c.run(ENTRY);self.assertEqual(c.stop['reason'],'EXTERNAL_OR_NULL_TARGET');self.assertEqual(c.atexit_registrations,[])
 def test_unknown_import_stops(self):
  c=self.cpu(1);c.run(ENTRY);self.assertEqual(c.stop['reason'],'UNMODELED_LAZY_IMPORT');self.assertEqual(c.heap_used,0)
 def test_linker_state_rejected(self):
  c=self.cpu();c.write_private(SP,struct.pack('<Q',1));c.run(ENTRY);self.assertEqual(c.stop['reason'],'UNEXPECTED_LAZY_BINDER_STATE');self.assertEqual(c.heap_used,0)
 def test_invalid_return_rejected_before_allocation(self):
  c=self.cpu();c.write_private(SP+24,bytes(8));c.run(ENTRY);self.assertEqual(c.stop['reason'],'EXTERNAL_OR_NULL_TARGET');self.assertEqual(c.heap_used,0)
 def test_exhaustion_stops_without_faking_exception(self):
  c=self.cpu();c.reg('RDI',0x100001);c.run(ENTRY);self.assertEqual(c.stop['reason'],'VIRTUAL_HEAP_EXHAUSTED');self.assertEqual(c.lazy_new_calls,0)
if __name__=='__main__':unittest.main()
