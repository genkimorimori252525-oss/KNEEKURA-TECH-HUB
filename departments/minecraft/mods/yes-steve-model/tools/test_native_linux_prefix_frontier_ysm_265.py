#!/usr/bin/env python3
import unittest
from native_linux_prefix_frontier_ysm_265 import parse_prefix,direct_target
class PrefixTests(unittest.TestCase):
 def test_stops_at_call(self):
  out=' 100: 90 \tnop\n 101: e8 00 00 00 00 \tcall   0x106\n 106: 90 \tnop\n';ops=parse_prefix(out,0x100,b'\x90\xe8\0\0\0\0\x90');self.assertEqual(len(ops),2)
 def test_noncontiguous(self):
  with self.assertRaises(ValueError):parse_prefix(' 101: c3 \tret\n',0x100,b'\xc3')
 def test_wrong_bytes(self):
  with self.assertRaises(ValueError):parse_prefix(' 100: c3 \tret\n',0x100,b'\x90')
 def test_no_control(self):
  with self.assertRaises(ValueError):parse_prefix(' 100: 90 \tnop\n',0x100,b'\x90')
 def test_direct_target(self):self.assertEqual(direct_target(dict(address=0x100,bytes='e800000000',assembly='call 0x105')),0x105)
 def test_negative_jump(self):self.assertEqual(direct_target(dict(address=0x100,bytes='e9fbffffff',assembly='jmp 0x100')),0x100)
 def test_wrong_target(self):
  with self.assertRaises(ValueError):direct_target(dict(address=0x100,bytes='e800000000',assembly='call 0x106'))
 def test_wrong_mnemonic(self):
  with self.assertRaises(ValueError):direct_target(dict(address=0x100,bytes='e800000000',assembly='jmp 0x105'))
 def test_indirect_boundary(self):self.assertIsNone(direct_target(dict(address=0x100,bytes='ffe0',assembly='jmp rax')))
 def test_conditional_boundary(self):self.assertIsNone(direct_target(dict(address=0x100,bytes='7400',assembly='je 0x102')))
if __name__=='__main__':unittest.main()
