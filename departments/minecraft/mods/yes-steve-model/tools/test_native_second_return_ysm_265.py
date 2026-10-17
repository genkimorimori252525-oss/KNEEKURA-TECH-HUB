#!/usr/bin/env python3
import importlib,unittest
class SecondReturnTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_second_return_ysm_265')
  except ModuleNotFoundError:self.fail('The second-return proof helper is not implemented')
 def test_constant_store_offset(self):
  r=self.m.return_registers(0x89);self.assertEqual((r['rsi_final'],r['store_offset']),(0x2280ffff,0))
 def test_second_data_word_delta(self):
  r=self.m.second_delta(0x3b7414a3,0xf28db0);self.assertEqual((r['delta_u32'],r['adc_carry']),(0xffc25fec,0))
 def test_changed_si_does_not_prove_top_store(self):
  self.assertNotEqual(self.m.return_registers(0x88)['store_offset'],0)
 def test_changed_word_changes_candidate(self):
  self.assertNotEqual(self.m.second_delta(0x3b7414a2,0xf28db0)['delta_u32'],0xffc25fec)
 def test_missing_segments_rejected(self):
  with self.assertRaises(ValueError):self.m.validate_parts([])
 def test_mutated_segments_rejected(self):
  with self.assertRaises(ValueError):self.m.validate_parts([bytes(n) for _,n,_ in self.m.SEGMENTS])
if __name__=='__main__':unittest.main()
