"""Checkpoint state equivalence and rejection tests using authored instructions only."""
import io,json,unittest,copy
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_guarded_checkpoint_ysm_265 import capture,restore,pack,unpack,ContextHeader,sanitize_context
from native_unicorn_guarded_ysm_265 import SP,STACK,X,REGS
CODE=0x100000;DATA=0x200000
class CheckpointTests(unittest.TestCase):
 def cpu(self,limit=1):
  c=ShadowGuardedCPU(io.StringIO(),'heap',limit,5);c.add_image(CODE,bytes.fromhex('488903488b0b4883c101')+b'\x90');c.add_image(DATA,bytes(4096),False);c.protect_image();c.reg('RAX',0x123456789abc);c.reg('RBX',DATA);return c
 def stopped(self):
  c=self.cpu();c.grant_shadow_range(DATA,16,7);c.allocate(24);c.write_private(SP+32,b'abc');c.opaque[SP+64]=SP+128;c.uc.reg_write(X.UC_X86_REG_XMM15,0x123456789abcdef0123456789abcdef0);c.run(CODE);return c
 def test_full_cpu_private_and_image_state_roundtrip(self):
  c=self.stopped();state=json.loads(json.dumps(capture(c)));r=self.cpu();restore(r,state)
  self.assertEqual({x:c.reg(x) for x in REGS},{x:r.reg(x) for x in REGS});self.assertEqual(c.uc.reg_read(X.UC_X86_REG_EFLAGS),r.uc.reg_read(X.UC_X86_REG_EFLAGS));self.assertEqual(c.uc.reg_read(X.UC_X86_REG_XMM15),r.uc.reg_read(X.UC_X86_REG_XMM15));self.assertEqual(c.known,r.known);self.assertEqual(c.opaque,r.opaque);self.assertEqual(c.read_known(SP+32,3),r.read_known(SP+32,3));self.assertTrue(r.expected_image_matches());self.assertEqual(r.shadow_events,1);self.assertEqual(r.origin_completed,1);self.assertEqual(r.attempted,0)
 def test_resumed_execution_equals_uninterrupted(self):
  c=self.stopped();r=self.cpu(limit=2);restore(r,capture(c));r.run(r.reg('RIP'));full=self.cpu(limit=3);full.grant_shadow_range(DATA,16,7);full.run(CODE)
  self.assertEqual({x:full.reg(x) for x in REGS},{x:r.reg(x) for x in REGS});self.assertEqual(full.uc.reg_read(X.UC_X86_REG_EFLAGS),r.uc.reg_read(X.UC_X86_REG_EFLAGS));self.assertEqual(full.read_known(DATA,8),r.read_known(DATA,8));self.assertEqual(r.completed,2)
 def test_image_mismatch_rejected(self):
  state=capture(self.stopped());state['images'][0]=(CODE,CODE+10,'bad');r=self.cpu()
  with self.assertRaises(ValueError):restore(r,state)
 def test_engine_mismatch_rejected(self):
  state=capture(self.stopped());state['engine']='other'
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_context_size_mismatch_rejected(self):
  state=capture(self.stopped());state['context']['size']+=1
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_bad_known_mask_rejected(self):
  state=capture(self.stopped());state['private'][str(STACK)]['known']=pack(bytes([2])*0x10000)
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_patch_outside_image_rejected(self):
  state=capture(self.stopped());state['patches']=[[SP,'01']]
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_patch_without_writable_history_rejected(self):
  state=capture(self.stopped());state['shadow_ranges']=[]
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_bounded_decompression(self):
  with self.assertRaises(ValueError):unpack(pack(bytes(4096)),8)
 def test_serialized_context_has_no_memory_snapshot_pointers(self):
  state=capture(self.stopped());m=state['context'];raw=unpack(m['bytes'],m['size']);h=ContextHeader.from_buffer_copy(raw);self.assertIsNone(h.last_block);self.assertIsNone(h.fv);self.assertEqual(h.snapshot_level,0)
 def test_bad_cpu_header_rejected(self):
  state=capture(self.stopped());m=state['context'];raw=bytearray(unpack(m['bytes'],m['size']));raw[0]^=1;m['bytes']=pack(raw)
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_crc_diagnostic_counters_roundtrip(self):
  c=self.stopped();c.crc_blocks=15;c.crc_iterations=23591981;c.crc_logical_steps=528156776;r=self.cpu();restore(r,capture(c));self.assertEqual((r.crc_blocks,r.crc_iterations,r.crc_logical_steps),(15,23591981,528156776));self.assertTrue(r.crc_counters_complete)
 def test_legacy_missing_crc_diagnostics_are_marked_incomplete(self):
  state=capture(self.stopped())
  for key in ('crc_blocks','crc_iterations','crc_logical_steps','crc_counters_complete'):state['fields'].pop(key)
  r=self.cpu();restore(r,state);self.assertFalse(r.crc_counters_complete);self.assertEqual(r.crc_blocks,0)
 def test_capture_requires_stopped_state(self):
  with self.assertRaises(ValueError):capture(self.cpu())
if __name__=='__main__':unittest.main()
