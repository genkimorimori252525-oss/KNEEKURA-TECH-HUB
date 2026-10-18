import importlib,unittest
class InitGuardChainTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_init_guard_chain_ysm_265')
  except ModuleNotFoundError:self.fail('Missing init guard chain helper')
 def test_borrow_and_sign(self):
  r=self.m.fixed_flags();self.assertEqual((r['r10d_after_sbb'],r['borrow'],r['sign'],r['jb_taken'],r['jns_taken']),(0x2e61fffe,1,0,True,True))
 def test_cqo_is_zero(self):self.assertEqual(self.m.fixed_flags()['rdx_at_push'],0)
 def test_final_ja_with_both_bts_carries(self):
  for c in (0,1):self.assertTrue(self.m.final_ja(c)['taken'])
 def test_final_nonzero_without_64bit_borrow(self):
  r=self.m.final_ja(0);self.assertEqual((r['rdx'],r['carry'],r['zero']),(0xb9d02ad9,0,0))
 def test_invalid_carry(self):
  with self.assertRaises(ValueError):self.m.final_ja(2)
 def test_missing_prefixes(self):
  with self.assertRaises(ValueError):self.m.validate_parts([])
 def test_changed_prefixes(self):
  with self.assertRaises(ValueError):self.m.validate_parts([bytes(n) for _,n,_ in self.m.SEGMENTS])
if __name__=='__main__':unittest.main()
