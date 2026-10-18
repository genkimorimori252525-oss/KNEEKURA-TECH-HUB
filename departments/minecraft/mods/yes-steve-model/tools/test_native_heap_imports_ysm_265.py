import io,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_heap_imports_ysm_265 import model
from native_unicorn_guarded_ysm_265 import HEAP,ModelHalt
class HeapImportTests(unittest.TestCase):
 def cpu(self):return ShadowGuardedCPU(io.StringIO(),'heap')
 def test_malloc_alias_uses_existing_budget(self):
  c=self.cpu();c.reg('RDI',24);self.assertEqual(model(c,'malloc'),HEAP);self.assertEqual(c.malloc_calls,1);self.assertIsNotNone(c.unknown(HEAP,24))
 def test_free_removes_access_and_knownness(self):
  c=self.cpu();a=c.allocate(24);c.write_private(a,b'x'*24);c.reg('RDI',a);model(c,'free');self.assertIsNotNone(c.unknown(a,24));self.assertFalse(c.private_allowed(a,1));self.assertEqual(c.heap_free_calls,1)
 def test_free_null_is_noop(self):
  c=self.cpu();c.reg('RDI',0);model(c,'free');self.assertEqual(c.heap_free_calls,1);self.assertEqual(c.allocations,[])
 def test_interior_pointer_rejected(self):
  c=self.cpu();a=c.allocate(24);c.reg('RDI',a+1)
  with self.assertRaises(ModelHalt):model(c,'free')
  self.assertEqual(len(c.allocations),1)
 def test_fixture_cannot_be_freed(self):
  c=self.cpu();a=c.reserve_fixture(16);c.private_readonly.append((a,a+16));c.reg('RDI',a)
  with self.assertRaises(ModelHalt):model(c,'free')
 def test_delete_alias_lifetime(self):
  for symbol in ('_ZdlPv','_ZdaPv'):
   c=self.cpu();a=c.allocate(8);c.reg('RDI',a);model(c,symbol);self.assertFalse(c.private_region(a,1))
 def test_double_free_rejected(self):
  c=self.cpu();a=c.allocate(8);c.reg('RDI',a);model(c,'free')
  with self.assertRaises(ModelHalt):model(c,'free')
if __name__=='__main__':unittest.main()
