#!/usr/bin/env python3
import unittest
from native_load_flag_chain_ysm_265 import SEGMENTS,prove,inherited_sign,bit_carry
class FlagTests(unittest.TestCase):
 def parts(self):return [bytes.fromhex(h) for _,h in SEGMENTS]
 def test_fixed_chain(self):
  p=prove(self.parts(),0xffac);self.assertTrue(all(x['taken'] for x in p.values()));self.assertEqual([p[k]['target_address'] for k in ['sign','btr','btc']],[0x1311bc0,0x129b910,0x12de5ac])
 def test_sign_set(self):self.assertTrue(inherited_sign(0xffac))
 def test_sign_clear(self):self.assertFalse(inherited_sign(0x7fac))
 def test_btr_modulo(self):self.assertEqual(bit_carry(0xc57f,0x2f,16),bit_carry(0xc57f,15,16))
 def test_btr_counterfactual(self):self.assertEqual(bit_carry(0x457f,0x2f,16),0)
 def test_btc_modulo(self):self.assertEqual(bit_carry(0xd6bd2601,0x22,32),0)
 def test_btc_counterfactual(self):self.assertEqual(bit_carry(0xd6bd2605,0x22,32),1)
 def test_changed_sequence(self):
  for i in range(len(SEGMENTS)):
   p=self.parts();p[i]=bytes([p[i][0]^1])+p[i][1:]
   with self.subTest(segment=i),self.assertRaises(ValueError):prove(p,0xffac)
 def test_wrong_segment_count(self):
  with self.assertRaises(ValueError):prove(self.parts()[:-1],0xffac)
 def test_no_assumed_inherited_sign(self):self.assertFalse(prove(self.parts(),0x7fac)['sign']['taken'])
if __name__=='__main__':unittest.main()
