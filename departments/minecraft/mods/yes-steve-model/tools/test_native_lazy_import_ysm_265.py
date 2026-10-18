"""Pinned lazy-binding frame models. No real dynamic linker or operator new is called."""
import io,struct,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_unicorn_guarded_ysm_265 import SP,HEAP
RET=0x100000;ENTRY=0x14f9c20
class LazyTests(unittest.TestCase):
 def cpu(self,index=250):
  c=ShadowGuardedCPU(io.StringIO(),'heap',1,5);c.add_image(RET,b'\x90'*32);c.add_image(ENTRY,b'\xc3');c.add_image(0x13d743c,bytes.fromhex('ff25a6634700'));c.add_image(0x13fe69d,bytes.fromhex('68fa000000'));c.add_image(0x184d7e8,struct.pack('<Q',0x13fe69d),False);c.add_image(0x184d680,struct.pack('<Q',0x1478e57),False);c.add_image(0x1478e57,bytes.fromhex('68cd000000'));c.protect_image();c.write_private(SP,struct.pack('<QQQQ',0,0,index,RET));c.reg('RDI',24);return c
 def test_operator_new_private_allocation_and_frame(self):
  c=self.cpu();c.run(ENTRY);self.assertEqual(c.completed,1);self.assertEqual(c.reg('RAX'),HEAP);self.assertEqual(c.reg('RSP'),SP+32);self.assertEqual(c.reg('RIP'),RET);self.assertEqual(c.lazy_new_calls,1);self.assertEqual(c.malloc_calls,0);self.assertIsNotNone(c.unknown(HEAP,24));self.assertFalse(c.private_allowed(HEAP+24,1))
 def test_array_new_uses_same_bounded_heap(self):
  c=self.cpu(205);c.reg('RDI',2080);c.run(ENTRY);self.assertEqual(c.completed,1);self.assertEqual(c.allocations,[(HEAP,2080)]);self.assertEqual(c.lazy_new_calls,1);self.assertIn('symbol=_Znam',c.out.getvalue())
 def test_unknown_import_stops(self):
  c=self.cpu(1);c.run(ENTRY);self.assertEqual(c.stop['reason'],'UNMODELED_LAZY_IMPORT');self.assertEqual(c.heap_used,0)
 def test_linker_state_rejected(self):
  c=self.cpu();c.write_private(SP,struct.pack('<Q',1));c.run(ENTRY);self.assertEqual(c.stop['reason'],'UNEXPECTED_LAZY_BINDER_STATE');self.assertEqual(c.heap_used,0)
 def test_invalid_return_rejected_before_allocation(self):
  c=self.cpu();c.write_private(SP+24,bytes(8));c.run(ENTRY);self.assertEqual(c.stop['reason'],'EXTERNAL_OR_NULL_TARGET');self.assertEqual(c.heap_used,0)
 def test_exhaustion_stops_without_faking_exception(self):
  c=self.cpu();c.reg('RDI',0x100001);c.run(ENTRY);self.assertEqual(c.stop['reason'],'VIRTUAL_HEAP_EXHAUSTED');self.assertEqual(c.lazy_new_calls,0)
if __name__=='__main__':unittest.main()
