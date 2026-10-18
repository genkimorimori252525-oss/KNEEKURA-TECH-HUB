"""Explicit platform counterfactuals, without any actual OS call."""
import io,struct,unittest
from native_unicorn_guarded_ysm_265 import GuardedCPU,SP
RET=0x100000
class PlatformTests(unittest.TestCase):
 def cpu(self,page=False):
  c=GuardedCPU(io.StringIO(),limit=1);c.add_image(RET,b'\x90');c.add_image(0x13d84a7,bytes.fromhex('ff25c3534700'));c.add_image(0x13d84c9,bytes.fromhex('ff35c9534700c3'));c.add_image(0x184d870,bytes(48),False);c.protect_image();c.configure_loader('image-only');c.virtual_platform=True;c.reg('RDI',30 if page else c.loader_name);c.reg('RSI',0);c.write_private(SP,(bytes(8) if page else b'')+struct.pack('<Q',RET));return c
 def test_open_failure(self):
  c=self.cpu();c.run(0x13d84a7);self.assertEqual(c.reg('RAX'),0xffffffff);self.assertEqual(c.reg('RSP'),SP+8);self.assertEqual(c.platform_calls,1)
 def test_page_size(self):
  c=self.cpu(True);c.run(0x13d84cf);self.assertEqual(c.reg('RAX'),4096);self.assertEqual(c.reg('RSP'),SP+16);self.assertEqual(c.platform_calls,1)
 def test_wrong_sysconf(self):
  c=self.cpu(True);c.reg('RDI',0);c.run(0x13d84cf);self.assertEqual(c.stop['reason'],'UNMODELED_SYSCONF_REQUEST');self.assertEqual(c.platform_calls,0)
 def test_wrong_open_flags(self):
  c=self.cpu();c.reg('RSI',1);c.run(0x13d84a7);self.assertEqual(c.stop['reason'],'UNMODELED_FILE_REQUEST');self.assertEqual(c.platform_calls,0)
 def test_disabled(self):
  c=self.cpu();c.virtual_platform=False;c.run(0x13d84a7);self.assertEqual(c.stop['reason'],'EXTERNAL_OR_NULL_TARGET');self.assertEqual(c.platform_calls,0)
if __name__=='__main__':unittest.main()
