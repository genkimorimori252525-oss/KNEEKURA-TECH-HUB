"""Own-byte legacy PSHUFB semantics, all controls and all register pairs."""
import io,random,unittest
from native_unicorn_guarded_ysm_265 import GuardedCPU,X
from native_pshufb_semantics_ysm_265 import decode
CODE=0x100000
class PshufbTests(unittest.TestCase):
 def run_case(self,dst,src,source,control):
  rex=0x40|((dst>>3)<<2)|(src>>3);raw=b'\x66'+(bytes([rex]) if rex!=0x40 else b'')+b'\x0f\x38\x00'+bytes([0xc0|((dst&7)<<3)|(src&7)])
  c=GuardedCPU(io.StringIO(),limit=1);c.add_image(CODE,raw+b'\x90');c.protect_image();dr=getattr(X,'UC_X86_REG_ZMM'+str(dst));sr=getattr(X,'UC_X86_REG_ZMM'+str(src));c.uc.reg_write(dr,int.from_bytes(source,'little'))
  if src!=dst:c.uc.reg_write(sr,int.from_bytes(control+bytes([0xa6])*48,'little'))
  else:control=source[:16]
  prior=[c.uc.reg_read(getattr(X,'UC_X86_REG_ZMM'+str(i))) for i in range(16)];flags=c.uc.reg_read(X.UC_X86_REG_EFLAGS);c.run(CODE);expected=bytes(0 if x&128 else source[x&15] for x in control)+source[16:]
  self.assertEqual(c.uc.reg_read(dr).to_bytes(64,'little'),expected);self.assertEqual(c.uc.reg_read(X.UC_X86_REG_EFLAGS),flags);self.assertEqual(c.pshufb_model_calls,1);self.assertEqual(c.completed,1);self.assertEqual(c.reg('RIP'),CODE+len(raw))
  for i in range(16):
   if i!=dst:self.assertEqual(c.uc.reg_read(getattr(X,'UC_X86_REG_ZMM'+str(i))),prior[i])
 def test_all_register_pairs(self):
  for dst in range(16):
   for src in range(16):
    with self.subTest(dst=dst,src=src):self.run_case(dst,src,bytes(range(64)),bytes(reversed(range(16))))
 def test_all_control_bytes(self):
  for block in range(16):self.run_case(0,1,bytes((i*13+7)&255 for i in range(64)),bytes(range(block*16,(block+1)*16)))
 def test_random_patterns_and_upper_state(self):
  r=random.Random(265)
  for _ in range(64):self.run_case(3,9,r.randbytes(64),r.randbytes(16))
 def test_memory_form_stops_without_native_helper(self):
  c=GuardedCPU(io.StringIO(),limit=1);c.add_image(CODE,bytes.fromhex('660f38000090'));c.protect_image();c.run(CODE);self.assertEqual(c.stop['reason'],'UNMODELED_LEGACY_PSHUFB_ENCODING');self.assertEqual(c.completed,0)
 def test_other_encoding_not_claimed(self):
  for raw in ['0f3800c1','c4e27100c1','660f3810c1','90']:self.assertIsNone(decode(bytes.fromhex(raw)))
if __name__=='__main__':unittest.main()
