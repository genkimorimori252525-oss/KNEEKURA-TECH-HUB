import unittest
from native_simulation_trace_crosscheck_ysm_265 import instructions,groups
class TraceTests(unittest.TestCase):
    def trace(self,body,count):return body+f'COUNTS\tattempted={count}\tcompleted={count}\nBOUNDED_RESULT\tINSTRUCTION_BUDGET\n'
    def test_duplicate_and_ranges(self):
        ops,s=instructions(self.trace('INS\t1000\t90\tNOP\nINS\t1001\t90\tNOP\nINS\t1000\t90\tNOP\n',3));self.assertEqual(len(ops),3);self.assertEqual(len(groups(s)),1)
    def test_conflicting_bytes(self):
        with self.assertRaises(ValueError):instructions(self.trace('INS\t1000\t90\tNOP\nINS\t1000\tcc\tINT3\n',2))
    def test_invalid_length(self):
        with self.assertRaises(ValueError):instructions(self.trace('INS\t1000\t'+'90'*16+'\tbad\n',1))
    def test_missing_completion(self):
        with self.assertRaises(ValueError):instructions('INS\t1000\t90\tNOP\nCOUNTS\tattempted=1\n')
    def test_wrong_count(self):
        with self.assertRaises(ValueError):instructions(self.trace('INS\t1000\t90\tNOP\n',2))
    def test_overlap_separates_groups(self):self.assertEqual(len(groups({0x1000:b'\x48\x90',0x1001:b'\x90',0x1002:b'\x90'})),2)
if __name__=='__main__':unittest.main()
