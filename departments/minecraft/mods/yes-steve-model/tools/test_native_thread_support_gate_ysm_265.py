"""Own-byte weak-gateway contracts; never loads a host library."""
import io,struct,unittest
from native_thread_support_gate_ysm_265 import ThreadLinkedCPU,GATE,SLOT,NAME,configure_thread_support
from native_unicorn_guarded_ysm_265 import SP,RETURN
from native_guarded_checkpoint_ysm_265 import capture,restore
CODE=0x100000
class ThreadGateTests(unittest.TestCase):
 def cpu(self,enabled=True,code=b'\xc3'):
  c=ThreadLinkedCPU(io.StringIO(),'heap',limit=4);c.add_image(CODE,code);c.add_image(SLOT&~4095,bytes(4096));c.protect_image();c.grant_shadow_range(SLOT&~4095,4096,3)
  if enabled:
   c.configure_threads([CODE]);c.uc.mem_write(SLOT,struct.pack('<Q',GATE));c.commit_write(SLOT,8);c.external_data_bindings[NAME]=GATE
  return c
 def test_disabled_gate_is_not_executable(self):
  c=self.cpu(False);self.assertFalse(c.code_allowed(GATE));self.assertEqual(c.run(GATE)['reason'],'EXTERNAL_OR_NULL_TARGET')
 def test_key_create_is_intercepted_and_returns_without_host_call(self):
  c=self.cpu();c.reg('RSP',SP);c.write_private(SP,struct.pack('<Q',RETURN));c.reg('RDI',SP+32);c.reg('RSI',0);self.assertEqual(c.run(GATE)['reason'],'ENTRY_RETURN');self.assertEqual(c.read_known(SP+32,4),bytes(4));self.assertEqual(c.thread_keys['0']['value'],0);self.assertEqual(c.thread_calls,1)
 def test_neighboring_gateway_byte_not_executable_or_known(self):
  c=self.cpu();self.assertFalse(c.code_allowed(GATE+1));self.assertEqual(c.unknown(GATE+1,1),GATE+1)
 def test_checkpoint_binding_and_gate_are_validated(self):
  c=self.cpu();c.stop={'reason':'TEST'};s=capture(c);d=self.cpu(False);d.shadow_ranges=[];d.shadow_expected={};restore(d,s);self.assertTrue(d.gate_enabled());d.uc.mem_write(GATE,b'\x90')
  with self.assertRaises(ValueError):capture(d)
 def test_slot_mismatch_is_not_checkpointable(self):
  c=self.cpu();c.uc.mem_write(SLOT,bytes(8));c.commit_write(SLOT,8);c.stop={'reason':'TEST'}
  with self.assertRaises(ValueError):capture(c)
 def test_unrecognized_artifact_cannot_bind_weak_symbol(self):
  c=self.cpu(False)
  with self.assertRaises(ValueError):configure_thread_support(c,b'not the source',[CODE])
  self.assertFalse(c.threads_enabled)
 def test_native_store_to_gate_rolls_back(self):
  code=b'\x48\xb8'+struct.pack('<Q',GATE)+b'\xc6\x00\x90';c=self.cpu(code=code);r=c.run(CODE);self.assertEqual(r['reason'],'THREAD_GATE_WRITE_BLOCKED');self.assertEqual(bytes(c.uc.mem_read(GATE,1)),b'\xc3')
 def test_thread_checkpoint_rejects_backend_without_thread_lifecycle(self):
  from native_sync_fixture_ysm_265 import SyncGuardedCPU
  c=self.cpu();c.stop={'reason':'TEST'};s=capture(c);d=SyncGuardedCPU(io.StringIO(),'heap');d.add_image(CODE,b'\xc3');d.add_image(SLOT&~4095,bytes(4096));d.protect_image()
  with self.assertRaisesRegex(ValueError,'thread-capable'):restore(d,s)
if __name__=='__main__':unittest.main()
