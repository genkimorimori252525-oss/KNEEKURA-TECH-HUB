import importlib,unittest
class ContinuationTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_continuation_ysm_265')
  except ModuleNotFoundError:self.fail('Missing continuation helper')
 def test_fixed_inputs(self):
  r=self.m.fixed_inputs();self.assertEqual((r['r9_after_shift'],r['shl_r10w_carry']),(0,0))
 def test_third_candidate(self):
  r=self.m.third_candidate(0x93,0xa7,0x0ca71429);self.assertEqual((r['key'],r['delta_u32'],r['target']),(0xff30d23c,0x80223,0xf69c60))
 def test_changed_byte_changes_third_target(self):self.assertNotEqual(self.m.third_candidate(0x92,0xa7,0x0ca71429)['target'],0xf69c60)
 def test_changed_word_changes_third_target(self):self.assertNotEqual(self.m.third_candidate(0x93,0xa7,0x0ca71428)['target'],0xf69c60)
 def test_fourth_candidate(self):
  t=self.m.third_candidate(0x93,0xa7,0x0ca71429);r=self.m.fourth_candidate(0xb3,0xf452b8b0,t);self.assertEqual((r['key'],r['delta_u32'],r['target']),(0xff38d0a7,0x3c3c86,0x132d8e6))
 def test_invalid_byte_rejected(self):
  with self.assertRaises(ValueError):self.m.third_candidate(256,0,0)
 def test_all_prior_write_offsets_preserve_saved_return(self):
  self.assertTrue(all(self.m.stack_jump(i,0x7f0000000000)['target']==0x7f0000efedbf for i in range(256)))
 def test_known_jnp(self):
  r=self.m.parity_guard();self.assertEqual((r['ax_after_adc'],r['parity_flag'],r['taken']),(0x36ba,0,True))
 def test_missing_segments_rejected(self):
  with self.assertRaises(ValueError):self.m.validate_parts([])
 def test_mutated_segments_rejected(self):
  with self.assertRaises(ValueError):self.m.validate_parts([bytes(n) for _,n,_ in self.m.SEGMENTS])
if __name__=='__main__':unittest.main()
