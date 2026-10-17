#!/usr/bin/env python3
import unittest
from native_load_parity_proof_ysm_265 import EXPECTED,prove,parity_after_dec
class ParityProofTests(unittest.TestCase):
 def test_fixed_result(self):
  p=prove(EXPECTED);self.assertEqual((p['word_before'],p['word_after'],p['low_byte_set_bits'],p['target_address']),(0xffad,0xffac,4,0x13b4244))
 def test_counterfactual_odd_parity(self):self.assertFalse(parity_after_dec(0xac14cb90)['parity_flag'])
 def test_sign_extension(self):self.assertEqual(parity_after_dec(0xad14cb90)['pushed_u64_hex'],'ffffffffad14cb90')
 def test_zero_extension_positive(self):self.assertEqual(parity_after_dec(0x2d14cb90)['pushed_u64_hex'],'000000002d14cb90')
 def test_reject_mutations(self):
  for i in [1,5,6,9,11,15,16,17]:
   b=bytearray(EXPECTED);b[i]^=1
   with self.subTest(offset=i),self.assertRaises(ValueError):prove(bytes(b))
 def test_reject_truncation(self):
  with self.assertRaises(ValueError):prove(EXPECTED[:-1])
if __name__=='__main__':unittest.main()
