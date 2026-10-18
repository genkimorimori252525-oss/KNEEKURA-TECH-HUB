import importlib,unittest,hashlib
class LiftTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_ghidra_crosscheck_ysm_265')
  except ModuleNotFoundError:self.fail('Missing static crosscheck helper')
  h=hashlib.sha256(bytes.fromhex('c3')).hexdigest()
  self.fixture=f'PROGRAM\tx\tx86:LE:64:default\t00000000\nINS\t100\t1\tc3\tRET\nRANGE\t100\t1\t{h}\t1\tfixture\nCOMPLETE\t1\t1\ttarget_executed=false\tautomatic_analysis=false\n'
 def test_valid_fixture(self):self.assertEqual(len(self.m.parse_lift(self.fixture)['groups']),1)
 def test_missing_completion(self):
  with self.assertRaises(ValueError):self.m.parse_lift(self.fixture.split('COMPLETE')[0])
 def test_wrong_instruction_length(self):
  with self.assertRaises(ValueError):self.m.parse_lift(self.fixture.replace('INS\t100\t1','INS\t100\t2'))
 def test_wrong_footer_count(self):
  with self.assertRaises(ValueError):self.m.parse_lift(self.fixture.replace('COMPLETE\t1\t1','COMPLETE\t2\t1'))
 def test_wrong_image_base(self):
  with self.assertRaises(ValueError):self.m.parse_lift(self.fixture.replace('00000000','00100000'))
 def test_trailing_content(self):
  with self.assertRaises(ValueError):self.m.parse_lift(self.fixture+'DATA\t100\tc3\n')
 def test_wrong_range_hash(self):
  with self.assertRaises(ValueError):self.m.parse_lift(self.fixture.replace(hashlib.sha256(bytes.fromhex('c3')).hexdigest(),'0'*64))
 def test_unknown_record(self):
  with self.assertRaises(ValueError):self.m.parse_lift(self.fixture.replace('INS\t','UNKNOWN\t'))
if __name__=='__main__':unittest.main()
