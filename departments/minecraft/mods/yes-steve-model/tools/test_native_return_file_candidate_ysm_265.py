#!/usr/bin/env python3
import unittest
from native_return_file_candidate_ysm_265 import STACK_EVENTS,ror32,bswap32,rsi_before_exchange,relative_word_address,decode_offset
class FileCandidateTests(unittest.TestCase):
 def test_stack_delta(self):self.assertEqual(sum(n for _,n in STACK_EVENTS),-136)
 def test_seed_slot(self):self.assertEqual(sum(n for _,n in STACK_EVENTS)+0xc000*2-0x17f80,-8)
 def test_shifted_rsi(self):self.assertEqual(rsi_before_exchange(),0)
 def test_relative_word(self):self.assertEqual(relative_word_address(),0xd2cd48)
 def test_fixed_decode(self):self.assertEqual(decode_offset(0xdc51ec52,0xd2cd48),0x2040f8)
 def test_candidate_address(self):self.assertEqual(0x10bf959+decode_offset(0xdc51ec52,0xd2cd48),0x12c3a51)
 def test_changed_word_changes_candidate(self):self.assertNotEqual(decode_offset(0xdc51ec53,0xd2cd48),0x2040f8)
 def test_rotate_zero(self):self.assertEqual(ror32(0x80000001,0),0x80000001)
 def test_rotate_wrap(self):self.assertEqual(ror32(1,1),0x80000000)
 def test_bswap_involution(self):self.assertEqual(bswap32(bswap32(0x12345678)),0x12345678)
if __name__=='__main__':unittest.main()
