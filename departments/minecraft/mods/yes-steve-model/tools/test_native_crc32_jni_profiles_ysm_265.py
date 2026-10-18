"""Three pinned JNI CRC profiles: full observable state/known-mask differentials."""
import io,struct,unittest,zlib
from native_crc32_jni_profiles_ysm_265 import JNI_PROFILES
from native_crc32_loop_profile_ysm_265 import eligible,standard_table
from native_unicorn_guarded_ysm_265 import GuardedCPU,REGS,SP,STACK,X
from native_shadow_image_ysm_265 import ShadowGuardedCPU
DATA=0x300000;OTHER=0x400000
class JniCRCProfilesTests(unittest.TestCase):
 def make(self,p,data,seed,fast,shadow=False):
  cls=ShadowGuardedCPU if shadow else GuardedCPU;n=len(data);c=cls(io.StringIO(),'strict',p['steps']+1 if fast and n>1 else n*p['steps'],10)
  for a,b in p['code'].items():c.add_image(a,b)
  c.add_image(p['exit'],b'\x90');c.add_image(p['table'],struct.pack('<256I',*(v^p['mask'] for v in standard_table())),False);c.add_image(DATA,data,False);c.add_image(OTHER,bytes(4096),False);c.protect_image()
  for i,r in enumerate(REGS):c.reg(r,0x1122334400000000+i*0x1020304)
  c.reg('RSP',SP);c.reg(p['source_reg'],DATA);c.reg(p['table_reg'],p['table']);c.reg(p['counter_reg'],n);c.reg(p['crc_reg'],0x9988776600000000|seed);c.uc.reg_write(X.UC_X86_REG_EFLAGS,0xa47);c.write_private(SP-64,bytes(range(64)));c.accelerate_crc=fast
  for i in range(32):c.uc.reg_write(getattr(X,'UC_X86_REG_ZMM'+str(i)),int.from_bytes(bytes([i+1])*64,'little'))
  return c
 def assert_state(self,p,a,b,data,seed):
  self.assertEqual(a.stop['reason'],'INSTRUCTION_BUDGET');self.assertEqual(b.stop['reason'],'INSTRUCTION_BUDGET');self.assertEqual({k:a.reg(k) for k in REGS},{k:b.reg(k) for k in REGS});self.assertEqual(a.uc.reg_read(X.UC_X86_REG_EFLAGS),b.uc.reg_read(X.UC_X86_REG_EFLAGS));self.assertEqual(a.read_known(SP-64,64),b.read_known(SP-64,64));self.assertEqual(a.known[STACK],b.known[STACK]);self.assertEqual(a.reg(p['crc_reg']),zlib.crc32(data,seed^0xffffffff)^0xffffffff)
  for i in range(32):self.assertEqual(a.uc.reg_read(getattr(X,'UC_X86_REG_ZMM'+str(i))),b.uc.reg_read(getattr(X,'UC_X86_REG_ZMM'+str(i))))
 def test_ninety_full_architectural_differentials(self):
  for p in JNI_PROFILES:
   for n in (1,2,3,4,7,16,31,64,255,1024):
    for seed in (0,0xffffffff,0x12345678):
     with self.subTest(entry=hex(p['entry']),n=n,seed=seed):
      data=bytes((i*37+19)&255 for i in range(n));a=self.make(p,data,seed,False);b=self.make(p,data,seed,True);a.run(p['entry']);b.run(p['entry']);self.assert_state(p,a,b,data,seed)
 def test_unrelated_working_image_store_does_not_disable_verified_loop(self):
  for p in JNI_PROFILES:
   data=bytes(range(32));a=self.make(p,data,7,False,True);b=self.make(p,data,7,True,True)
   for c in (a,b):c.grant_shadow_range(OTHER,4096,3);c.write_model_memory(OTHER,b'x');c.pc=p['entry'];self.assertTrue(eligible(c))
   a.run(p['entry']);b.run(p['entry']);self.assert_state(p,a,b,data,7);self.assertTrue(a.expected_image_matches() and b.expected_image_matches());self.assertEqual(b.crc_blocks,1)
 def test_changed_source_is_not_summarized(self):
  for p in JNI_PROFILES:
   c=self.make(p,b'abc',0,True,True);c.grant_shadow_range(DATA,3,3);c.write_model_memory(DATA,b'x');c.pc=p['entry'];self.assertFalse(eligible(c))
 def test_changed_code_table_and_wrong_table_are_rejected(self):
  for p in JNI_PROFILES:
   for kind in ('code','table','pointer'):
    c=self.make(p,b'abc',0,True);c.pc=p['entry']
    if kind=='pointer':c.reg(p['table_reg'],p['table']+4)
    else:c.uc.mem_write(p['entry'] if kind=='code' else p['table'],b'\x90')
    self.assertFalse(eligible(c))
 def test_counter_and_source_bounds(self):
  for p in JNI_PROFILES:
   for count in (0,1,4,0xffffffffffffffff):
    c=self.make(p,b'abc',0,True);c.pc=p['entry'];c.reg(p['counter_reg'],count);self.assertFalse(eligible(c))
   c=self.make(p,b'abc',0,True);c.pc=p['entry'];c.reg(p['source_reg'],SP-64);self.assertFalse(eligible(c))
if __name__=='__main__':unittest.main()
