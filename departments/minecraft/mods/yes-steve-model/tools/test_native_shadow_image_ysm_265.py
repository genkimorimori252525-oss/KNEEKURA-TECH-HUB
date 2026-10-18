"""Own-byte working-copy mutation ledger and transactional guard tests."""
import io,unittest
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_unicorn_guarded_ysm_265 import SP,STACK,ModelHalt
CODE=0x100000;DATA=0x200000
class ShadowTests(unittest.TestCase):
 def cpu(self,code='488903',grant=True,limit=1):
  c=ShadowGuardedCPU(io.StringIO(),limit=limit);c.add_image(CODE,bytes.fromhex(code)+b'\x90'*16);c.add_image(DATA,bytes(4096),False);c.protect_image();c.reg('RBX',DATA);c.reg('RAX',0x123456789abcdef)
  if grant:c.grant_shadow_range(DATA,16,7)
  return c
 def test_valid_write_only_changes_working_view(self):
  c=self.cpu();baseline=c.image[1][2];c.run(CODE);self.assertEqual(c.completed,1);self.assertEqual(c.shadow_events,1);self.assertEqual(c.shadow_bytes,8);self.assertEqual(c.image[1][2],baseline);self.assertFalse(c.image_unchanged());self.assertTrue(c.expected_image_matches());self.assertEqual(bytes(c.uc.mem_read(DATA,8)),(0x123456789abcdef).to_bytes(8,'little'))
 def test_ungranted_write_rolls_back(self):
  c=self.cpu(grant=False);c.run(CODE);self.assertEqual(c.completed,0);self.assertEqual(c.shadow_events,0);self.assertTrue(c.image_unchanged());self.assertTrue(c.expected_image_matches())
 def test_same_page_outside_exact_range_rolls_back(self):
  c=self.cpu();c.reg('RBX',DATA+16);c.run(CODE);self.assertEqual(c.stop['reason'],'SHADOW_WRITE_OUTSIDE_GRANTED_RANGE');self.assertEqual(c.shadow_events,0);self.assertTrue(c.image_unchanged())
 def test_cross_range_store_rolls_back_all_bytes(self):
  c=self.cpu();c.reg('RBX',DATA+12);c.run(CODE);self.assertEqual(c.completed,0);self.assertTrue(c.image_unchanged());self.assertEqual(c.reg('RIP'),CODE)
 def test_quota_rejects_before_commit(self):
  c=self.cpu();c.MAX_IMAGE_BYTES=7;c.run(CODE);self.assertEqual(c.stop['reason'],'SHADOW_WRITE_BUDGET');self.assertEqual(c.shadow_events,0);self.assertTrue(c.image_unchanged())
 def test_second_store_quota_preserves_first(self):
  c=self.cpu('488903488903',limit=2);c.MAX_IMAGE_EVENTS=1;c.run(CODE);self.assertEqual(c.completed,1);self.assertEqual(c.shadow_events,1);self.assertTrue(c.expected_image_matches());self.assertEqual(c.reg('RIP'),CODE+3)
 def test_private_writes_still_tracked(self):
  c=self.cpu('50');c.run(CODE);self.assertEqual(c.read_known(SP-8,8),(0x123456789abcdef).to_bytes(8,'little'));self.assertEqual(c.shadow_events,0)
 def test_unknown_read_does_not_commit(self):
  c=self.cpu('488b01488903',limit=2);c.reg('RCX',SP+64);c.run(CODE);self.assertEqual(c.stop['reason'],'UNINITIALIZED_READ');self.assertEqual(c.shadow_events,0);self.assertTrue(c.image_unchanged())
 def test_unaccounted_mutation_detected(self):
  c=self.cpu();c.uc.mem_write(DATA,b'x');self.assertFalse(c.expected_image_matches())
 def test_reference_mutation_detected(self):
  c=self.cpu();a,b,v=c.image[1];c.image[1]=(a,b,b'x'+v[1:]);self.assertNotEqual(c.reference_hashes(),c.reference_digests)
 def test_invalid_grants(self):
  for address,size,prot in [(DATA+1,8,7),(DATA,0,7),(DATA,8,8),(0xdead000,8,7)]:
   c=self.cpu(grant=False)
   with self.assertRaises(ModelHalt):c.grant_shadow_range(address,size,prot)
 def test_store_crossing_image_mapping_rolls_back(self):
  c=self.cpu();c.grant_shadow_range(DATA,4096,7);c.reg('RBX',DATA+4092);c.run(CODE);self.assertEqual(c.completed,0);self.assertTrue(c.image_unchanged());self.assertTrue(c.expected_image_matches())
 def test_read_back_committed_working_value(self):
  c=self.cpu('488903488b0b',limit=2);c.run(CODE);self.assertEqual(c.completed,2);self.assertEqual(c.reg('RCX'),0x123456789abcdef);self.assertTrue(c.expected_image_matches())
 def test_crc_summary_disabled_after_mutation(self):
  from native_crc32_loop_profile_ysm_265 import eligible
  c=self.cpu();c.run(CODE);c.pc=0x15f0d5e;self.assertFalse(eligible(c))
 def test_restore_readonly_revokes_previous_grant(self):
  c=self.cpu();c.grant_shadow_range(DATA,16,5);c.run(CODE);self.assertEqual(c.completed,0);self.assertTrue(c.image_unchanged());self.assertEqual(c.shadow_events,0)
 def test_latest_overlapping_permission_wins(self):
  c=self.cpu();c.grant_shadow_range(DATA,4096,7);c.grant_shadow_range(DATA,4096,5);self.assertFalse(c.shadow_writable(DATA,8));c.grant_shadow_range(DATA,8,7);self.assertTrue(c.shadow_writable(DATA,8));self.assertFalse(c.shadow_writable(DATA+8,8))
 def test_no_code_permission_expansion(self):
  c=self.cpu();self.assertFalse(c.code_allowed(DATA));self.assertFalse(c.code_allowed(SP))
if __name__=='__main__':unittest.main()
