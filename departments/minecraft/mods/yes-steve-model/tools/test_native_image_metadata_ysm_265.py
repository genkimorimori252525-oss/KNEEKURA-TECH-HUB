#!/usr/bin/env python3
"""Synthetic header tests; no native target execution."""
import struct,unittest
from native_image_metadata_ysm_265 import header
class HeaderTests(unittest.TestCase):
 def elf(self,machine):
  b=bytearray(64);b[:6]=b'\x7fELF\x02\x01';struct.pack_into('<HHIQQQIHHHHHH',b,16,3,machine,1,123,64,0,0,64,56,12,64,0,0);return b
 def pe(self):
  b=bytearray(256);b[:2]=b'MZ';struct.pack_into('<I',b,60,64);b[64:68]=b'PE\0\0';struct.pack_into('<HHIIIHH',b,68,0x8664,5,1234,0,0,240,0x2022);struct.pack_into('<H',b,88,0x20b);struct.pack_into('<I',b,104,0x1234);struct.pack_into('<Q',b,112,0x180000000);return b
 def test_sectionless_elf(self):
  h=header(self.elf(62));self.assertEqual((h['machine'],h['section_header_count'],h['program_header_count']),(62,0,12))
 def test_aarch64(self):self.assertEqual(header(self.elf(183))['machine'],183)
 def test_pe32_plus(self):
  h=header(self.pe());self.assertEqual((h['machine'],h['entry_rva'],h['image_base']),(0x8664,0x1234,0x180000000))
 def test_bad_pe_signature(self):
  b=self.pe();b[64]=0
  with self.assertRaises(ValueError):header(b)
 def test_reject_pe32(self):
  b=self.pe();struct.pack_into('<H',b,88,0x10b)
  with self.assertRaises(ValueError):header(b)
 def test_reject_elf_endianness(self):
  b=self.elf(62);b[5]=2
  with self.assertRaises(ValueError):header(b)
if __name__=='__main__':unittest.main()
