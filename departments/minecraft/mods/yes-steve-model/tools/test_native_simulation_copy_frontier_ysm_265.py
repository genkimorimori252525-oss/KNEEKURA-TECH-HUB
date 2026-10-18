"""Scoped tests; YSM_SIM_INPUTS points to external original image and retained traces."""
import os,tempfile,unittest
from pathlib import Path
from native_simulation_copy_frontier_ysm_265 import analyze,copy_contract
class CopyFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(os.environ['YSM_SIM_INPUTS']);cls.image=root/'native-static-20261017/libysm-core.so';out=root/'ghidra-static-20261018/output';cls.old=out/'bounded-init-atomic-trial.tsv';cls.new=out/'bounded-init-register-trial.tsv'
    def test_fixed_count(self):self.assertEqual(copy_contract()['count'],328)
    def test_retained_trial(self):
        r=analyze(self.image,self.old,self.new);self.assertEqual(r['completed_byte_copies'],96);self.assertEqual(r['overlap_bytes'],24);self.assertFalse(r['unknown_bytes_filled'])
    def bad_trace(self,transform):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trace.tsv';p.write_text(transform(self.new.read_text()))
            with self.assertRaises(ValueError):analyze(self.image,self.old,p)
    def test_changed_path_rejected(self):self.bad_trace(lambda x:x.replace('INS\t152eb19','INS\t152eb18',1))
    def test_missing_register_rejected(self):self.bad_trace(lambda x:'\n'.join(y for y in x.splitlines() if not y.startswith('STOP_REGISTER\tDF\t'))+'\n')
    def test_changed_count_rejected(self):self.bad_trace(lambda x:x.replace('STOP_REGISTER\tRCX\te7','STOP_REGISTER\tRCX\te8'))
    def test_wrong_image_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'image';p.write_bytes(b'not the pinned image')
            with self.assertRaises(ValueError):analyze(p,self.old,self.new)
if __name__=='__main__':unittest.main()
