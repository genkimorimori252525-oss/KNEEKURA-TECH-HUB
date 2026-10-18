"""Authored callback/order fixtures and deterministic loader state; no original target input."""
import io,struct,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_elf_loader_view_ysm_265 import apply_fixups
from native_initializer_sequence_ysm_265 import prepare_call,run_sequence
from native_unicorn_guarded_ysm_265 import SP,RETURN
CODE=0x100000;DATA=0x200000
class InitSequenceTests(unittest.TestCase):
 def cpu(self):
  c=ShadowGuardedCPU(io.StringIO(),limit=100);c.add_image(CODE,b'\xc3'*64);c.add_image(DATA,bytes(4096),False);c.protect_image();return c
 def test_loader_updates_working_view_only(self):
  c=self.cpu();apply_fixups(c,[(DATA,32,3)],[(DATA,CODE),(DATA+8,CODE+1)]);self.assertEqual(c.read_known(DATA,16),struct.pack('<QQ',CODE,CODE+1));self.assertTrue(c.loader_view_applied);self.assertEqual(c.loader_relocation_events,2);self.assertEqual(c.shadow_events,2);self.assertEqual(c.image[1][2],bytes(4096));self.assertTrue(c.expected_image_matches())
 def test_duplicate_fixup_rejected(self):
  c=self.cpu()
  with self.assertRaises(ValueError):apply_fixups(c,[(DATA,32,3)],[(DATA,CODE),(DATA,CODE)])
  self.assertTrue(c.image_unchanged())
 def test_fixup_outside_writable_range_rejected(self):
  c=self.cpu()
  with self.assertRaises(ValueError):apply_fixups(c,[(DATA,8,3)],[(DATA+8,CODE)])
 def test_loader_cannot_apply_twice(self):
  c=self.cpu();apply_fixups(c,[(DATA,8,3)],[(DATA,CODE)])
  with self.assertRaises(ValueError):apply_fixups(c,[(DATA,8,3)],[(DATA,CODE)])
 def test_ordered_callbacks_share_state_and_return(self):
  c=self.cpu();m={'dt_init':CODE,'initializers':[CODE+1,CODE+2]};r=run_sequence(c,m,100,5);self.assertEqual(r['phase'],'done');self.assertEqual(c.init_array_completed,[0,1]);self.assertFalse(c.call_in_progress);self.assertEqual(c.reg('RIP'),RETURN);self.assertEqual(c.origin_completed+c.completed,3)
 def test_unfinished_call_frame_is_not_reset(self):
  c=self.cpu();prepare_call(c,CODE)
  with self.assertRaises(ValueError):prepare_call(c,CODE+1)
 def test_external_entry_rejected(self):
  c=self.cpu()
  with self.assertRaises(ValueError):prepare_call(c,0)
 def test_resource_boundary_retains_next_callback(self):
  c=self.cpu();r=run_sequence(c,{'dt_init':CODE,'initializers':[CODE+1]},1,5);self.assertEqual(c.init_phase,'init-array');self.assertFalse(c.call_in_progress);self.assertEqual(c.init_array_completed,[]);r=run_sequence(c,{'dt_init':CODE,'initializers':[CODE+1]},1,5);self.assertEqual(c.init_array_completed,[0]);self.assertEqual(r['phase'],'done')
if __name__=='__main__':unittest.main()
