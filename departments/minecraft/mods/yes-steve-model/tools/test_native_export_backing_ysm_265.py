#!/usr/bin/env python3
"""Synthetic one-instruction/range tests; not target behavior tests."""
import struct,unittest
from native_export_backing_ysm_265 import backing,data_at,direct_branch
class BoundaryTests(unittest.TestCase):
 def test_x86_forward(self):self.assertEqual(direct_branch(62,b'\xe9\x10\0\0\0',0x100)['target_address'],0x115)
 def test_x86_negative(self):self.assertEqual(direct_branch(62,b'\xe9\xfb\xff\xff\xff',0x100)['target_address'],0x100)
 def test_a64_forward(self):self.assertEqual(direct_branch(183,struct.pack('<I',0x14000004),0x100)['target_address'],0x110)
 def test_a64_negative(self):self.assertEqual(direct_branch(183,struct.pack('<I',0x17ffffff),0x100)['target_address'],0xfc)
 def test_no_bl(self):self.assertIsNone(direct_branch(183,struct.pack('<I',0x94000004),0x100))
 def test_no_unknown_x86(self):self.assertIsNone(direct_branch(62,b'\x90'*5,0x100))
 def rs(self):return [dict(address=0x100,memory_size=32,file_size=16,file_offset=4)]
 def test_file_offset(self):self.assertEqual(backing(self.rs(),0x105,2)['file_offset'],9)
 def test_virtual_tail(self):self.assertFalse(backing(self.rs(),0x110,1)['file_backed'])
 def test_no_read_virtual_tail(self):
  with self.assertRaises(ValueError):data_at(b'x'*64,self.rs(),0x110,1)
 def test_no_cross_boundary(self):
  with self.assertRaises(ValueError):backing(self.rs(),0x11f,2)
 def test_no_ambiguous_regions(self):
  with self.assertRaises(ValueError):backing(self.rs()*2,0x100,1)
 def test_no_truncated_file(self):
  with self.assertRaises(ValueError):data_at(b'x',self.rs(),0x100,1)
if __name__=='__main__':unittest.main()
