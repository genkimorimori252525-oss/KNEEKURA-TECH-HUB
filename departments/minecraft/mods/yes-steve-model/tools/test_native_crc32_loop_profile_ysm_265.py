"""Differential checks of the pinned loop's small bounded fragments in an emulator, never on host CPU."""
import io,struct,unittest,zlib
from native_crc32_loop_profile_ysm_265 import CODE,ENTRY,EXIT,TABLE,XOR_MASK,CYCLE_STEPS,standard_table,update_crc,eligible
from native_unicorn_guarded_ysm_265 import GuardedCPU,REGS,SP,STACK,X
DATA=0x300000
class CRCProfileTests(unittest.TestCase):
    def make(self,data,seed,accelerate):
        n=len(data);c=GuardedCPU(io.StringIO(),'strict',29 if accelerate and n>1 else n*CYCLE_STEPS,5)
        for address,code in CODE.items():c.add_image(address,code,True)
        c.add_image(EXIT,b'\x90',True);c.add_image(TABLE,struct.pack('<256I',*(x^XOR_MASK for x in standard_table())),False);c.add_image(DATA,data,False);c.protect_image()
        for i,name in enumerate(REGS):c.reg(name,0x1122334400000000+i*0x1020304)
        c.reg('RSP',SP);c.reg('R10',DATA);c.reg('R11',TABLE);c.reg('RCX',n);c.reg('RSI',0x9988776600000000|seed);c.uc.reg_write(X.UC_X86_REG_EFLAGS,0xa47)
        c.write_private(SP-32,bytes(range(32)));c.accelerate_crc=accelerate;return c
    def test_complete_state_differential(self):
        cases=0
        for n in (1,2,3,4,7,16,31,64,255,1024):
            for seed in (0,0xffffffff,0x12345678):
                data=bytes((i*37+19)&255 for i in range(n));full=self.make(data,seed,False);fast=self.make(data,seed,True);full.run(ENTRY);fast.run(ENTRY)
                self.assertEqual(full.stop['reason'],'INSTRUCTION_BUDGET');self.assertEqual(fast.stop['reason'],'INSTRUCTION_BUDGET')
                self.assertEqual({k:full.reg(k) for k in REGS},{k:fast.reg(k) for k in REGS});self.assertEqual(full.uc.reg_read(X.UC_X86_REG_EFLAGS),fast.uc.reg_read(X.UC_X86_REG_EFLAGS));self.assertEqual(full.read_known(SP-32,32),fast.read_known(SP-32,32));self.assertEqual(full.reg('RSI'),zlib.crc32(data,seed^0xffffffff)^0xffffffff)
                self.assertEqual(fast.crc_iterations,n-1 if n>1 else 0);self.assertTrue(full.image_unchanged() and fast.image_unchanged());cases+=1
        self.assertEqual(cases,30)
    def test_standard_recurrence_reference(self):
        table=[x^XOR_MASK for x in standard_table()]
        for seed in (0,1,0xffffffff,0x12345678):
            for data in (b'',b'123456789',bytes(range(256))):self.assertEqual(update_crc(seed,data,table),zlib.crc32(data,seed^0xffffffff)^0xffffffff)
    def test_no_mutable_source_summary(self):
        c=self.make(b'abc',1,True);c.pc=ENTRY;c.reg('R10',SP-32);self.assertFalse(eligible(c))
    def test_wrong_table_address_rejected(self):
        c=self.make(b'abc',1,True);c.pc=ENTRY;c.reg('R11',TABLE+4);self.assertFalse(eligible(c))
    def test_single_iteration_not_summarized(self):
        c=self.make(b'a',1,True);c.pc=ENTRY;self.assertFalse(eligible(c))
    def test_code_signature_rejected(self):
        c=self.make(b'abc',1,True);c.pc=ENTRY;c.uc.mem_write(ENTRY,b'\x90');self.assertFalse(eligible(c))
    def test_table_signature_rejected(self):
        c=self.make(b'abc',1,True);c.pc=ENTRY;c.uc.mem_write(TABLE,b'\0');self.assertFalse(eligible(c))
    def test_excessive_count_not_summarized(self):
        c=self.make(b'abc',1,True);c.pc=ENTRY;c.reg('RCX',16*1024*1024+1);self.assertFalse(eligible(c))
if __name__=='__main__':unittest.main()
