import importlib,unittest
class InitializerWriteTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_initializer_write_audit_ysm_265')
  except ModuleNotFoundError:self.fail('Missing initializer write audit')
 def test_rip_indirect_slot(self):self.assertEqual(self.m.rip_slot(bytes.fromhex('ff25faffffff'),0x100),0x100)
 def test_other_branch_not_misread(self):self.assertIsNone(self.m.rip_slot(bytes.fromhex('e90000000090'),0x100))
 def test_direct_ram_output(self):self.assertEqual(self.m.classify_write('(ram, 0xd30e20, 16) COPY (register, 0x1200, 16)'),dict(kind='direct',address=0xd30e20,size=16))
 def test_constant_store(self):self.assertEqual(self.m.classify_write(' ---  STORE (const, 0x1b1, 8) , (const, 0x100, 8) , (register, 0x0, 4)'),dict(kind='direct',address=0x100,size=4))
 def test_register_store_remains_unresolved(self):self.assertEqual(self.m.classify_write(' ---  STORE (const, 0x1b1, 8) , (register, 0x20, 8) , (const, 0x0, 8)'),dict(kind='unresolved',size=8))
 def test_read_not_write(self):self.assertIsNone(self.m.classify_write('(register, 0x0, 8) COPY (ram, 0x100, 8)'))
 def test_preceding_overlap(self):self.assertTrue(self.m.overlap(0x100,8,0x107,4))
 def test_adjacent_nonoverlap(self):self.assertFalse(self.m.overlap(0x100,8,0x108,4))
if __name__=='__main__':unittest.main()
