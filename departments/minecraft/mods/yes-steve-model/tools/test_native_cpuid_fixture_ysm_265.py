"""Declared CPUID inputs only; no host CPU identity or feature queries."""
import io,unittest
from native_unicorn_guarded_ysm_265 import GuardedCPU,X
ENTRY=0x100000
class CpuidTests(unittest.TestCase):
 def cpu(self,fixture=(0,0,0,0)):
  c=GuardedCPU(io.StringIO(),limit=1);c.add_image(ENTRY,bytes.fromhex('0fa290'));c.protect_image();c.cpuid_leaf1=fixture;c.reg('RAX',1);c.reg('RCX',0);return c
 def test_exact_values_flags_and_other_registers(self):
  c=self.cpu((0x12345678,0xffffffff,0x2000000,0));c.reg('RBX',0xffff000000000000);c.reg('RDX',0xffff000000000000);c.reg('R15',0x123456789abcdef);c.uc.reg_write(X.UC_X86_REG_EFLAGS,0xa47);flags=c.uc.reg_read(X.UC_X86_REG_EFLAGS);c.run(ENTRY);self.assertEqual(tuple(c.reg(r) for r in ('RAX','RBX','RCX','RDX')),(0x12345678,0xffffffff,0x2000000,0));self.assertEqual(c.reg('R15'),0x123456789abcdef);self.assertEqual(c.uc.reg_read(X.UC_X86_REG_EFLAGS),flags);self.assertEqual(c.cpuid_calls,1)
 def test_zero_fixture(self):
  c=self.cpu();c.run(ENTRY);self.assertEqual(tuple(c.reg(r) for r in ('RAX','RBX','RCX','RDX')),(0,0,0,0))
 def test_disabled(self):
  c=self.cpu(None);c.run(ENTRY);self.assertEqual(c.stop['reason'],'UNMODELED_ENVIRONMENT_INSTRUCTION');self.assertEqual(c.cpuid_calls,0)
 def test_other_leaf(self):
  c=self.cpu();c.reg('RAX',7);c.run(ENTRY);self.assertEqual(c.stop['reason'],'UNMODELED_CPUID_LEAF');self.assertEqual(c.reg('RAX'),7)
 def test_leaf1_ignores_input_ecx(self):
  for value in (1,0xec8150,0xffffffff):
   c=self.cpu();c.reg('RCX',value);c.run(ENTRY);self.assertEqual(c.cpuid_calls,1);self.assertEqual(c.reg('RCX'),0);self.assertEqual(c.completed,1)
 def test_invalid_values(self):
  for values in ((0,0,0),(-1,0,0,0),(0,0,0,1<<32)):
   c=self.cpu(values);c.run(ENTRY);self.assertEqual(c.stop['reason'],'INVALID_CPUID_FIXTURE');self.assertEqual(c.cpuid_calls,0)
if __name__=='__main__':unittest.main()
