import io,struct,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_tls_fixture_ysm_265 import configure,model
from native_heap_imports_ysm_265 import model as heap_model
from native_unicorn_guarded_ysm_265 import ModelHalt
DATA=0x200000;TEMPLATE=0x300000
class TlsTests(unittest.TestCase):
 def cpu(self):
  c=ShadowGuardedCPU(io.StringIO(),'heap');c.add_image(DATA,struct.pack('<QQQQ',0,0,0,16)+bytes(4096-32),False);c.add_image(TEMPLATE,b'ABC\0',False);c.protect_image();c.grant_shadow_range(DATA,4096,3);c.grant_shadow_range(DATA,4096,1);configure(c,{'address':TEMPLATE,'file_size':4,'memory_size':32,'alignment':16,'descriptors':[[DATA,0],[DATA+16,16]]});c.reg('RDI',DATA);return c
 def test_template_and_zero_tail(self):
  c=self.cpu();p=model(c);self.assertEqual(c.read_known(p,32),b'ABC\0'+bytes(28));self.assertEqual(p%16,0);self.assertEqual(c.external_binding_events,2);self.assertEqual(c.heap_used,0);self.assertTrue(c.expected_image_matches())
 def test_offsets_share_virtual_thread_block(self):
  c=self.cpu();p=model(c);c.reg('RDI',DATA+16);self.assertEqual(model(c),p+16);self.assertEqual(c.tls_calls,2);self.assertEqual(c.fixture_reserved,32)
 def test_tls_storage_is_mutable_but_not_freeable(self):
  c=self.cpu();p=model(c);c.write_private(p+16,b'xy');c.reg('RDI',DATA+16);self.assertEqual(c.read_known(model(c),2),b'xy');c.reg('RDI',p)
  with self.assertRaises(ModelHalt):heap_model(c,'free')
 def test_unknown_descriptor_rejected(self):
  c=self.cpu();c.reg('RDI',DATA+8)
  with self.assertRaises(ModelHalt):model(c)
  self.assertEqual(c.fixture_reserved,0)
 def test_foreign_module_rejected(self):
  c=self.cpu();c.uc.mem_write(DATA,struct.pack('<Q',7))
  with self.assertRaises(ModelHalt):model(c)
  self.assertEqual(c.fixture_reserved,0)
 def test_out_of_range_offset_rejected(self):
  c=self.cpu();c.uc.mem_write(DATA+8,struct.pack('<Q',64))
  with self.assertRaises(ModelHalt):model(c)
 def test_changed_spec_rejected(self):
  c=self.cpu();s=dict(c.tls_spec);s['memory_size']=64
  with self.assertRaises(ValueError):configure(c,s)
 def test_unknown_template_bytes_not_zero_filled(self):
  c=self.cpu();c.tls_spec['address']=0x700000000040
  with self.assertRaises(ModelHalt):model(c)
  self.assertEqual(c.fixture_reserved,0)
if __name__=='__main__':unittest.main()
