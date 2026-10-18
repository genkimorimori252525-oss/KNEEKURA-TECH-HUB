import io,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_memory_imports_ysm_265 import model
from native_unicorn_guarded_ysm_265 import SP,ModelHalt
DATA=0x200000
class MemoryTests(unittest.TestCase):
 def cpu(self):
  c=ShadowGuardedCPU(io.StringIO(),'heap');c.add_image(DATA,b'abc\0'+bytes(4092),False);c.protect_image();c.write_private(SP+32,b'abc\0def\0');return c
 def test_memcmp_unsigned_byte_difference(self):
  c=self.cpu();c.reg('RDI',SP+32);c.reg('RSI',DATA);c.reg('RDX',4);self.assertEqual(model(c,'memcmp'),0);c.write_private(SP+32,b'\xff');self.assertEqual(model(c,'memcmp'),255-97)
 def test_strlen_and_strcmp(self):
  c=self.cpu();c.reg('RDI',SP+32);c.reg('RSI',DATA);self.assertEqual(model(c,'strlen'),3);self.assertEqual(model(c,'strcmp'),0)
 def test_strncmp_does_not_read_after_n(self):
  c=self.cpu();c.reg('RDI',SP+32);c.reg('RSI',SP+36);c.reg('RDX',0);self.assertEqual(model(c,'strncmp'),0);c.reg('RDX',2);self.assertEqual(model(c,'strncmp'),(-3)&0xffffffff)
 def test_memcpy_to_private(self):
  c=self.cpu();c.reg('RDI',SP+128);c.reg('RSI',DATA);c.reg('RDX',4);self.assertEqual(model(c,'memcpy'),SP+128);self.assertEqual(c.read_known(SP+128,4),b'abc\0')
 def test_memcpy_to_granted_working_image(self):
  c=self.cpu();c.grant_shadow_range(DATA,4096,3);c.reg('RDI',DATA+32);c.reg('RSI',SP+32);c.reg('RDX',4);model(c,'memcpy');self.assertEqual(c.read_known(DATA+32,4),b'abc\0');self.assertEqual(c.shadow_events,1);self.assertTrue(c.expected_image_matches())
 def test_unknown_source_does_not_initialize_destination(self):
  c=self.cpu();c.reg('RDI',SP+128);c.reg('RSI',SP+256);c.reg('RDX',4)
  with self.assertRaises(ModelHalt):model(c,'memcpy')
  self.assertIsNotNone(c.unknown(SP+128,4))
 def test_overlap_rejected(self):
  c=self.cpu();c.reg('RDI',SP+33);c.reg('RSI',SP+32);c.reg('RDX',3)
  with self.assertRaises(ModelHalt):model(c,'memcpy')
 def test_readonly_image_rejected(self):
  c=self.cpu();c.reg('RDI',DATA);c.reg('RSI',SP+32);c.reg('RDX',4)
  with self.assertRaises(ModelHalt):model(c,'memcpy')
  self.assertTrue(c.image_unchanged())
 def test_page_revocation_blocks_modeled_write_outside_partial_range(self):
  c=self.cpu();c.grant_shadow_range(DATA,4096,3);c.grant_shadow_range(DATA,8,1)
  with self.assertRaises(ModelHalt):c.write_model_memory(DATA+16,b'x')
  self.assertTrue(c.image_unchanged())
if __name__=='__main__':unittest.main()
