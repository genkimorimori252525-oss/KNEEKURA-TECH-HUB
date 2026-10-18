"""Unresolved external object pointers cannot silently become mapped ELF-header data."""
import io,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_unicorn_guarded_ysm_265 import ModelHalt
CODE=0x100000;SLOT=0x200000
class ExternalDataTests(unittest.TestCase):
 def cpu(self):
  c=ShadowGuardedCPU(io.StringIO(),limit=1);c.add_image(CODE,bytes.fromhex('488b0390'));c.add_image(SLOT,bytes(4096),False);c.protect_image();c.external_data_slots=[[SLOT,'stdout']];c.external_data_guard_applied=True;c.reg('RBX',SLOT);return c
 def test_native_pointer_load_stops_before_zero_is_consumed(self):
  c=self.cpu();c.reg('RAX',123);c.run(CODE);self.assertEqual(c.stop['reason'],'UNMODELED_EXTERNAL_DATA_READ');self.assertEqual(c.reg('RAX'),123);self.assertEqual(c.completed,0)
 def test_model_read_is_also_unknown(self):
  c=self.cpu()
  with self.assertRaises(ModelHalt):c.read_known(SLOT,8)
 def test_partial_overlap_is_unknown(self):
  c=self.cpu();self.assertEqual(c.unknown(SLOT+7,2),SLOT+7)
 def test_other_image_bytes_remain_known(self):
  c=self.cpu();self.assertEqual(c.read_known(SLOT+8,8),bytes(8))
if __name__=='__main__':unittest.main()
