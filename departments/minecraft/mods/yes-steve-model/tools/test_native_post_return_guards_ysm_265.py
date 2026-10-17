#!/usr/bin/env python3
import importlib,unittest
class PostReturnGuardsTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_post_return_guards_ysm_265')
  except ModuleNotFoundError:self.fail('Missing post-return guard helper')
 def test_neg_jbe_complete_word_domain(self):
  self.assertTrue(all(self.m.neg_jbe(x,16)['taken'] for x in range(65536)))
 def test_neg_zero_flags(self):
  self.assertEqual(self.m.neg_jbe(0,16),dict(result=0,cf=0,zf=1,taken=True))
 def test_neg_nonzero_flags(self):
  self.assertEqual(self.m.neg_jbe(0x8000,16),dict(result=0x8000,cf=1,zf=0,taken=True))
 def test_known_or_guard(self):
  r=self.m.fixed_registers();self.assertEqual((r['rdx'],r['r11_before_or'],r['or_stack_offset'],r['return_store_offset']),(65535,255,0,0));self.assertTrue(self.m.or_jg(r['rdx'],r['r11_before_or'])['taken'])
 def test_or_zero_counterexample(self):self.assertFalse(self.m.or_jg(0,0)['taken'])
 def test_or_negative_counterexample(self):self.assertFalse(self.m.or_jg(1<<63,255)['taken'])
 def test_missing_ranges(self):
  with self.assertRaises(ValueError):self.m.validate_parts([])
 def test_changed_ranges(self):
  with self.assertRaises(ValueError):self.m.validate_parts([bytes(n) for _,n,_ in self.m.SEGMENTS])
if __name__=='__main__':unittest.main()
