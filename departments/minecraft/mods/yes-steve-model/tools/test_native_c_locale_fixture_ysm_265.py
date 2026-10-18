"""Authored C-locale API/ASCII fixtures, no host locale calls."""
import io,struct,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_c_locale_fixture_ysm_265 import ensure_c_locale,classification,convert,model,DESC
from native_unicorn_guarded_ysm_265 import SP,HEAP,HEAP_SIZE,ModelHalt
class CLocaleTests(unittest.TestCase):
 def cpu(self):return ShadowGuardedCPU(io.StringIO(),'heap',1,5)
 def test_classification_golden_ascii(self):
  for c,expected in [(65,0xd508),(97,0xd608),(48,0xd808),(32,0x6001),(9,0x2003),(10,0x2002),(33,0xc004),(0,2),(127,2),(128,0),(-1,0),(-128,0)]:self.assertEqual(classification(c),expected)
 def test_case_conversion_domain(self):
  for c in range(-128,256):
   self.assertEqual(convert(c,True),-1 if c==-1 else c+256 if c<0 else c-32 if 97<=c<=122 else c)
   self.assertEqual(convert(c,False),-1 if c==-1 else c+256 if c<0 else c+32 if 65<=c<=90 else c)
 def test_fixture_layout_and_unknown_fields(self):
  c=self.cpu();p=ensure_c_locale(c);b,l,u=struct.unpack('<QQQ',c.read_known(p+104,24));self.assertEqual(int.from_bytes(c.read_known(b+65*2,2),'little'),0xd508);self.assertEqual(int.from_bytes(c.read_known(l+65*4,4),'little'),97);self.assertEqual(int.from_bytes(c.read_known(u+97*4,4),'little'),65);self.assertIsNotNone(c.unknown(p,104));self.assertIsNotNone(c.unknown(p+128+6*8,8))
 def test_fixture_does_not_move_normal_heap_cursor(self):
  c=self.cpu();p=ensure_c_locale(c);self.assertEqual(c.heap_used,0);self.assertEqual(c.fixture_reserved,8192);self.assertEqual(c.allocate(16),HEAP);self.assertEqual(ensure_c_locale(c),p);self.assertEqual(c.fixture_reserved,8192)
 def test_fixture_cannot_be_overwritten(self):
  c=self.cpu();p=ensure_c_locale(c)
  with self.assertRaises(ModelHalt):c.write_private(p+104,bytes(8))
 def test_fixture_readonly_source_copy_is_allowed(self):
  c=self.cpu();p=ensure_c_locale(c);c.reg('RSI',p+0x1000);c.reg('RDI',SP+32);c.reg('RCX',1);c.model('copy');self.assertEqual(c.read_known(SP+32,1),b'C')
 def test_newlocale_c_and_reuse(self):
  c=self.cpu();c.write_private(SP+32,b'C\0');c.reg('RDI',64);c.reg('RSI',SP+32);c.reg('RDX',0);p=model(c,'__newlocale');self.assertEqual(p,model(c,'__newlocale'));self.assertEqual(c.locale_model_calls,2)
 def test_unknown_locale_stops_without_allocation(self):
  c=self.cpu();c.write_private(SP+32,b'ja_JP.UTF-8\0');c.reg('RDI',64);c.reg('RSI',SP+32)
  with self.assertRaises(ModelHalt):model(c,'__newlocale')
  self.assertEqual(c.fixture_reserved,0)
 def test_c_dup_and_free_use_shared_readonly_handle(self):
  c=self.cpu();p=ensure_c_locale(c);c.reg('RDI',p);self.assertEqual(model(c,'__duplocale'),p);model(c,'__freelocale');self.assertEqual(c.c_locale_handle,p)
 def test_thread_locale_is_logical_only(self):
  c=self.cpu();p=ensure_c_locale(c);c.reg('RDI',p);self.assertEqual(model(c,'__uselocale'),(1<<64)-1);c.reg('RDI',0);self.assertEqual(model(c,'__uselocale'),p);c.reg('RDI',(1<<64)-1);self.assertEqual(model(c,'__uselocale'),p)
 def test_wide_classification_descriptor(self):
  c=self.cpu();p=ensure_c_locale(c);c.write_private(SP+32,b'alpha\0');c.reg('RDI',SP+32);c.reg('RSI',p);d=model(c,'__wctype_l');c.reg('RDI',65);c.reg('RSI',d);c.reg('RDX',p);self.assertEqual(model(c,'__iswctype_l'),1);c.reg('RDI',0x3042);self.assertEqual(model(c,'__iswctype_l'),0)
 def test_c_multibyte_boundaries(self):
  c=self.cpu();self.assertEqual(model(c,'__ctype_get_mb_cur_max'),1)
  for x,expected in ((65,65),(127,127),(128,0xffffffff),(255,0xffffffff),(0xffffffff,0xffffffff)):
   c.reg('RDI',x);self.assertEqual(model(c,'wctob'),expected);self.assertEqual(model(c,'btowc'),expected)
 def test_normal_heap_respects_fixture_reservation(self):
  c=self.cpu();ensure_c_locale(c)
  with self.assertRaises(ModelHalt):c.allocate(HEAP_SIZE)
if __name__=='__main__':unittest.main()
