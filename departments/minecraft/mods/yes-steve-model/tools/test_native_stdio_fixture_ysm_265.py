import io,struct,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_stdio_fixture_ysm_265 import ensure_stdio_bindings,SLOTS,NAMES,HANDLE
from native_unicorn_guarded_ysm_265 import ModelHalt,HEAP
class StdioTests(unittest.TestCase):
 def cpu(self):
  c=ShadowGuardedCPU(io.StringIO(),'heap');c.add_image(0xd2d000,bytes(4096),False);c.protect_image();c.external_data_slots=[[a,n] for n,a in SLOTS.items()];c.external_data_guard_applied=True;return c
 def test_pointer_variables_and_opaque_streams(self):
  c=self.cpu();ensure_stdio_bindings(c)
  for i,name in enumerate(NAMES):
   variable=int.from_bytes(c.read_known(SLOTS[name],8),'little');handle=int.from_bytes(c.read_known(variable,8),'little');self.assertEqual(variable,c.stdio_fixture_base+i*8);self.assertEqual(handle,HANDLE+i*0x100);self.assertIsNotNone(c.unknown(handle,1))
  self.assertEqual(c.external_binding_events,3);self.assertTrue(c.expected_image_matches());self.assertEqual(c.heap_used,0);self.assertEqual(c.allocate(16),HEAP)
 def test_bindings_are_idempotent(self):
  c=self.cpu();ensure_stdio_bindings(c);n=c.shadow_events;ensure_stdio_bindings(c);self.assertEqual(c.shadow_events,n);self.assertEqual(c.fixture_reserved,64)
 def test_missing_guard_rejected(self):
  c=self.cpu();c.external_data_guard_applied=False
  with self.assertRaises(ValueError):ensure_stdio_bindings(c)
 def test_unexpected_slot_rejected(self):
  c=self.cpu();c.uc.mem_write(SLOTS['stdout'],b'x')
  with self.assertRaises(ValueError):ensure_stdio_bindings(c)
  self.assertEqual(c.fixture_reserved,0)
 def test_stdio_checkpoint_restores_binding_and_unknown_FILE(self):
  from native_guarded_checkpoint_ysm_265 import capture,restore
  c=self.cpu();c.grant_shadow_range(0xd2d000,4096,3);c.grant_shadow_range(0xd2d000,4096,1);ensure_stdio_bindings(c);c.stop={'reason':'TEST_STOP','pc':0,'address':0,'size':0};r=self.cpu();restore(r,capture(c));self.assertEqual(r.external_data_bindings,c.external_data_bindings);self.assertEqual(r.read_known(r.stdio_fixture_base,24),c.read_known(c.stdio_fixture_base,24));self.assertIsNotNone(r.unknown(HANDLE,1));self.assertTrue(r.expected_image_matches())
 def test_stream_variables_are_readonly(self):
  c=self.cpu();ensure_stdio_bindings(c)
  with self.assertRaises(ModelHalt):c.write_private(c.stdio_fixture_base,bytes(8))
if __name__=='__main__':unittest.main()
