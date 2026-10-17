import importlib,struct,unittest
class InitializerTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_initializer_inventory_ysm_265')
  except ModuleNotFoundError:self.fail('Missing initializer inventory helper')
 def test_dynamic_null_termination(self):self.assertEqual(self.m.dynamic_records(struct.pack('<qQqQ',12,123,0,0)),[(12,123)])
 def test_dynamic_unterminated_rejected(self):
  with self.assertRaises(ValueError):self.m.dynamic_records(struct.pack('<qQ',12,123))
 def test_rela_signed_addend(self):self.assertEqual(self.m.rela_records(struct.pack('<QQq',16,8,-4)),[(16,8,-4)])
 def test_rela_truncation(self):
  with self.assertRaises(ValueError):self.m.rela_records(bytes(23))
 def test_relative_array_uses_addend_not_zero(self):self.assertEqual(self.m.array_targets(0x100,bytes(8),[(0x100,8,0x200)]),[dict(slot=0x100,raw_value=0,relative_target=0x200)])
 def test_duplicate_array_relocation_rejected(self):
  with self.assertRaises(ValueError):self.m.array_targets(0x100,bytes(8),[(0x100,8,0x200)]*2)
 def test_nonrelative_array_relocation_rejected(self):
  with self.assertRaises(ValueError):self.m.array_targets(0x100,bytes(8),[(0x100,6,0x200)])
 def test_overlap_includes_preceding_write(self):self.assertEqual(self.m.overlaps([(0x100,8,0)],0x107,4),[(0x100,8,0)])
 def test_adjacent_write_not_overlap(self):self.assertEqual(self.m.overlaps([(0x100,8,0)],0x108,4),[])
 def test_unknown_relocation_not_silently_ignored(self):
  with self.assertRaises(ValueError):self.m.overlaps([(0x100,999,0)],0x200,4)
 def test_prefix_summary_excludes_raw_body(self):
  r=self.m.prefix_summary('  100: c3  \tret',0x100,bytes.fromhex('c3'))
  self.assertEqual((r['instruction_count'],r['prefix_byte_count'],r['first_transfer']['assembly']),(1,1,'ret'));self.assertNotIn('instructions',r)
 def test_prefix_byte_mismatch(self):
  with self.assertRaises(ValueError):self.m.prefix_summary('  100: c3  \tret',0x100,bytes.fromhex('90'))
if __name__=='__main__':unittest.main()
