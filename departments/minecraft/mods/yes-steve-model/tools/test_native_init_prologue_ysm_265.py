import importlib,unittest
class InitPrologueTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_init_prologue_ysm_265')
  except ModuleNotFoundError:self.fail('Missing initializer prologue helper')
 def test_first_predicate(self):self.assertEqual(self.m.first_predicate(),dict(bp=0x89a2,zf=0,taken=True))
 def test_saved_literal_slot(self):self.assertEqual(self.m.saved_literal_slot(),dict(entry_rsp_delta=-128,read_relative_offset=120,original_rsp_offset=-8,value=0x162e9a61))
 def test_second_predicate_and_data_pointer(self):
  r=self.m.second_predicate(0,0);self.assertEqual((r['rcx'],r['carry'],r['relative_data_pointer']),(1,0,0x14c9bd5))
 def test_unknown_saved_register_and_bias_do_not_change_predicate(self):
  a=self.m.second_predicate(0,0);b=self.m.second_predicate((1<<64)-1,0x7f0000000000);self.assertEqual((a['rcx'],a['carry'],a['r11d_before_bswap']),(b['rcx'],b['carry'],b['r11d_before_bswap']))
 def test_third_predicate(self):
  r=self.m.third_predicate();self.assertEqual((r['bit_index'],r['carry'],r['taken']),(6,0,True))
 def test_key_bias_cancellation(self):
  a=self.m.initial_key(0);b=self.m.initial_key(0x7f0000000000);self.assertEqual((a["key"],b["key"],a["carry"]),(0x14c9bd9,0x14c9bd9,0))
 def test_return_candidate(self):self.assertEqual(self.m.return_candidate(0xcd4bfbff)['target'],0x1499584)
 def test_changed_word_changes_candidate(self):self.assertNotEqual(self.m.return_candidate(0xcd4bfbfe)['target'],0x1499584)
 def test_missing_parts_rejected(self):
  with self.assertRaises(ValueError):self.m.validate_parts([])
 def test_changed_parts_rejected(self):
  with self.assertRaises(ValueError):self.m.validate_parts([bytes(n) for _,n,_ in self.m.SEGMENTS])
if __name__=='__main__':unittest.main()
