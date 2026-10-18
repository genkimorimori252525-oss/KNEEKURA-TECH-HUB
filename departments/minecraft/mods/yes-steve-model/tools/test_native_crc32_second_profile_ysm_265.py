"""Second independently pinned masked CRC loop; full architectural differential."""
import io,struct,unittest,zlib
from native_crc32_loop_profile_ysm_265 import P2 as P,standard_table,eligible
from native_unicorn_guarded_ysm_265 import GuardedCPU,REGS,SP,X
DATA=0x300000
class SecondCRCProfileTests(unittest.TestCase):
 def make(self,data,seed,accelerate):
  n=len(data);c=GuardedCPU(io.StringIO(),'strict',P['steps']+1 if accelerate and n>1 else n*P['steps'],5)
  for address,code in P['code'].items():c.add_image(address,code,True)
  c.add_image(P['exit'],b'\x90',True);c.add_image(P['table'],struct.pack('<256I',*(x^P['mask'] for x in standard_table())),False);c.add_image(DATA,data,False);c.protect_image()
  for i,name in enumerate(REGS):c.reg(name,0x1122334400000000+i*0x1020304)
  c.reg('RSP',SP);c.reg(P['source_reg'],DATA);c.reg(P['table_reg'],P['table']);c.reg('RCX',n);c.reg(P['crc_reg'],0x9988776600000000|seed);c.uc.reg_write(X.UC_X86_REG_EFLAGS,0xa47);c.write_private(SP-32,bytes(range(32)));c.accelerate_crc=accelerate;return c
 def test_complete_state_differential(self):
  for n in (1,2,3,4,7,16,31,64,255,1024):
   for seed in (0,0xffffffff,0x12345678):
    data=bytes((i*37+19)&255 for i in range(n));full=self.make(data,seed,False);fast=self.make(data,seed,True);full.run(P['entry']);fast.run(P['entry'])
    self.assertEqual(full.stop['reason'],'INSTRUCTION_BUDGET');self.assertEqual(fast.stop['reason'],'INSTRUCTION_BUDGET');self.assertEqual({k:full.reg(k) for k in REGS},{k:fast.reg(k) for k in REGS});self.assertEqual(full.uc.reg_read(X.UC_X86_REG_EFLAGS),fast.uc.reg_read(X.UC_X86_REG_EFLAGS));self.assertEqual(full.read_known(SP-32,32),fast.read_known(SP-32,32));self.assertEqual(full.reg(P['crc_reg']),zlib.crc32(data,seed^0xffffffff)^0xffffffff);self.assertTrue(full.image_unchanged() and fast.image_unchanged())
 def test_mutable_source_rejected(self):
  c=self.make(b'abc',1,True);c.pc=P['entry'];c.reg(P['source_reg'],SP-32);self.assertFalse(eligible(c))
 def test_wrong_table_rejected(self):
  c=self.make(b'abc',1,True);c.pc=P['entry'];c.reg(P['table_reg'],P['table']+4);self.assertFalse(eligible(c))
 def test_changed_code_rejected(self):
  c=self.make(b'abc',1,True);c.pc=P['entry'];c.uc.mem_write(P['entry'],b'\x90');self.assertFalse(eligible(c))
 def test_changed_table_rejected(self):
  c=self.make(b'abc',1,True);c.pc=P['entry'];c.uc.mem_write(P['table'],b'\0');self.assertFalse(eligible(c))
 def test_one_iteration_not_summarized(self):
  c=self.make(b'a',1,True);c.pc=P['entry'];self.assertFalse(eligible(c))
if __name__=='__main__':unittest.main()
