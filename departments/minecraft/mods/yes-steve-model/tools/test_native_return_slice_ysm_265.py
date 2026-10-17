#!/usr/bin/env python3
import unittest
from native_return_slice_ysm_265 import register_slice,symbolic_return,validate_parts
class ReturnSliceTests(unittest.TestCase):
 def test_constant_register(self):
  r=register_slice(0x14df0f,0xd6bd2601,0x22);self.assertEqual(r['r11_after_not_dword'],0x2942d9eb)
 def test_shr_carry(self):self.assertEqual(register_slice(0x14df0f,0xd6bd2601,0x22)['shr14_carry'],0)
 def test_counterfactual_carry(self):self.assertEqual(register_slice(0x14ff0f,0xd6bd2601,0x22)['shr14_carry'],1)
 def test_modulo_bit(self):self.assertEqual(register_slice(0x14df0f,0xd6bd2601,0x22),register_slice(0x14df0f,0xd6bd2601,2))
 def test_stack_cancellation(self):self.assertEqual(register_slice(0x14df0f,0xd6bd2601,0x22)['r11_after_not_dword']-0x2942d9eb,0)
 def test_positive_offset(self):self.assertEqual(symbolic_return(0x700000000000,1),0x7000010bf95a)
 def test_negative_offset(self):self.assertEqual(symbolic_return(0x700000000000,0xffffffff),0x7000010bf958)
 def test_signed_min(self):self.assertEqual(symbolic_return(0x700000000000,0x80000000),0x700000000000+0x10bf959-0x80000000)
 def test_wrap(self):self.assertEqual(symbolic_return(0,0xffffffff,0),(1<<64)-1)
 def test_missing_parts(self):
  with self.assertRaises(ValueError):validate_parts([])
 def test_wrong_hashes(self):
  with self.assertRaises(ValueError):validate_parts([bytes(n) for n in [30,64,74,22]])
if __name__=='__main__':unittest.main()
