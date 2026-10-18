"""Virtual TLS destructor registration, never executing or registering host callbacks."""
import struct,unittest
import test_native_lazy_import_ysm_265 as lazy
RET,ENTRY=lazy.RET,lazy.ENTRY
from native_guarded_checkpoint_ysm_265 import capture,restore
class ThreadExitTests(unittest.TestCase):
 def cpu(self):
  c=lazy.LazyTests().cpu(118);c.add_image(0x184d3c8,struct.pack('<Q',0x153b3eb),False);c.add_image(0x153b3eb,b'\x68'+struct.pack('<I',118));c.protect_image();c.tls_block=c.reserve_fixture(64);c.tls_spec={'memory_size':64};c.reg('RDI',RET);c.reg('RSI',c.tls_block+32);c.reg('RDX',0x184d3c8);return c
 def test_register_only(self):
  c=self.cpu();c.run(ENTRY);self.assertEqual(c.thread_atexit_registrations,[[RET,c.tls_block+32,0x184d3c8]]);self.assertEqual(c.reg('RIP'),RET);self.assertEqual(c.completed,1);self.assertEqual(c.reg('RAX'),0);self.assertEqual(c.atexit_registrations,[])
 def test_foreign_callback_rejected(self):
  c=self.cpu();c.reg('RDI',c.tls_block);c.run(ENTRY);self.assertEqual(c.thread_atexit_registrations,[]);self.assertEqual(c.stop['reason'],'UNMODELED_THREAD_ATEXIT_REGISTRATION')
 def test_foreign_object_rejected(self):
  c=self.cpu();c.reg('RSI',RET);c.run(ENTRY);self.assertEqual(c.thread_atexit_registrations,[])
 def test_unknown_dso_rejected(self):
  c=self.cpu();c.reg('RDX',0xdead);c.run(ENTRY);self.assertEqual(c.thread_atexit_registrations,[])
 def test_budget_rejected(self):
  c=self.cpu();c.thread_atexit_registrations=[[RET,c.tls_block,0x184d3c8]]*1024;c.run(ENTRY);self.assertEqual(len(c.thread_atexit_registrations),1024);self.assertEqual(c.completed,0)
 def test_checkpoint_preserves_registration(self):
  c=self.cpu();c.run(ENTRY);s=capture(c);d=self.cpu();restore(d,s);self.assertEqual(d.thread_atexit_registrations,c.thread_atexit_registrations)
if __name__=='__main__':unittest.main()
