"""Counterfactual return input only. Image protections must never be relaxed."""
import io,struct,unittest
from native_unicorn_guarded_ysm_265 import GuardedCPU,SP
RET=0x100000;DATA=0x200000
class ProtectionTests(unittest.TestCase):
 def cpu(self,result='success-input',code=b'\x90',limit=1):
  c=GuardedCPU(io.StringIO(),limit=limit);c.add_image(RET,code);c.add_image(DATA,bytes(16),False);c.add_image(0x13d84d0,bytes.fromhex('ff35ca534700c3'));c.add_image(0x184d8a0,bytes(8),False);c.protect_image();c.protection_result=result;c.write_private(SP,bytes(8)+struct.pack('<Q',RET));c.reg('RDI',DATA);c.reg('RSI',16);c.reg('RDX',7);return c
 def test_success_return_only(self):
  c=self.cpu();c.run(0x13d84d6);self.assertEqual(c.reg('RAX'),0);self.assertEqual(c.reg('RSP'),SP+16);self.assertEqual(c.protection_calls,1);self.assertTrue(c.image_unchanged())
 def test_failure_return_only(self):
  c=self.cpu('failure-input');c.run(0x13d84d6);self.assertEqual(c.reg('RAX'),0xffffffff);self.assertEqual(c.protection_calls,1)
 def test_write_still_blocked_after_success(self):
  c=self.cpu(code=bytes.fromhex('488903'),limit=2);c.reg('RBX',DATA);c.run(0x13d84d6);self.assertEqual(c.stop['reason'],'ORIGINAL_IMAGE_WRITE_BLOCKED');self.assertEqual(c.completed,1);self.assertTrue(c.image_unchanged());self.assertIn('ATTEMPTED_IMAGE_WRITE',c.out.getvalue())
 def test_wrong_request(self):
  c=self.cpu();c.reg('RDX',16);c.run(0x13d84d6);self.assertEqual(c.stop['reason'],'UNMODELED_PROTECTION_REQUEST');self.assertEqual(c.protection_calls,0)
 def test_disabled(self):
  c=self.cpu('disabled');c.run(0x13d84d6);self.assertEqual(c.stop['reason'],'EXTERNAL_OR_NULL_TARGET');self.assertEqual(c.protection_calls,0)
if __name__=='__main__':unittest.main()
