"""Owned ELF metadata and gateway bodies only; never a real JVM or YSM execution."""
import copy,hashlib,io,json,struct,unittest
from native_jni_fixture_ysm_265 import JniGuardedCPU,VM_NAMES,ENV_NAMES,VERSION,JVM_IMPORT_SLOTS
from native_jvm_artifact_view_ysm_265 import BASE
from native_jvm_loader_fixture_ysm_265 import model,HANDLE
from native_unicorn_guarded_ysm_265 import ModelHalt,SP
from native_guarded_checkpoint_ysm_265 import capture,restore
RET=0x100000

def owned_jvm():
    b=bytearray(0x10000);b[:16]=b'\x7fELF\x02\x01\x01'+bytes(9)
    struct.pack_into('<HHIQQQIHHHHHH',b,16,3,62,1,0,64,0x8000,0,64,56,2,64,6,0)
    struct.pack_into('<IIQQQQQQ',b,64,1,5,0,0,0,0xd000,0xd000,4096)
    struct.pack_into('<IIQQQQQQ',b,120,1,6,0xe000,0xe000,0,4096,4096,4096)
    names=bytearray(b'\0');locals_=['jni_'+n for n in VM_NAMES+ENV_NAMES if not n.startswith('reserved')]
    for table_index,off,kind,rows,start in [(3,0x1000,11,list(JVM_IMPORT_SLOTS),0x7100),(4,0x2000,2,locals_,0x4000)]:
        for i,name in enumerate(rows):
            n=len(names);names.extend(name.encode()+b'\0');a=start+i*32
            struct.pack_into('<IBBHQQ',b,off+i*24,n,0x12 if kind==11 else 2,0,1,a,6);b[a:a+6]=bytes.fromhex('b8efbeaddec3')
        struct.pack_into('<IIQQQQIIQQ',b,0x8000+table_index*64,0,kind,0,0,off,len(rows)*24,5,0,8,24)
    struct.pack_into('<IIQQQQIIQQ',b,0x8040,0,1,6,0x4000,0x4000,0x4000,0,0,16,0)
    struct.pack_into('<IIQQQQIIQQ',b,0x8080,0,1,3,0xe000,0xe000,4096,0,0,8,0)
    struct.pack_into('<IIQQQQIIQQ',b,0x8140,0,3,2,0x9000,0x9000,len(names),0,0,1,0);b[0x9000:0x9000+len(names)]=names
    return bytes(b)

class JvmLoaderTests(unittest.TestCase):
    def cpu(self,configure=True):
        c=JniGuardedCPU(io.StringIO(),'heap',limit=1);c.add_image(RET,b'\x90'*16);c.add_image(0xd2d000,bytes(4096),False);c.protect_image();c.grant_shadow_range(0xd2d000,4096,3);c.configure_jni()
        if configure:c.configure_jvm_artifact(owned_jvm(),initial=True)
        return c
    def string(self,c,s):
        a=c.reserve_fixture(len(s)+1);c.write_private(a,s.encode()+b'\0');return a
    def open(self,c):
        c.reg('RDI',self.string(c,'/virtual/jdk/lib/server/libjvm.so'));c.reg('RSI',5);return model(c,'dlopen')
    def test_source_backed_interfaces_and_required_imports(self):
        c=self.cpu();self.assertTrue(c.jvm_interfaces_ready);self.assertEqual(c.external_binding_events,3)
        for name,slot in JVM_IMPORT_SLOTS.items():
            address=c.jvm_view.symbol(name)['address'];self.assertEqual(c.read_known(slot,8),struct.pack('<Q',address));self.assertEqual(c.external_data_bindings[name],address)
        self.assertTrue(c.expected_image_matches());self.assertEqual(c.interface_bytes('vm')[48:56],struct.pack('<Q',c.jvm_view.local_function('jni_GetEnv')['address']))
    def test_getversion_intercept_never_executes_owned_body(self):
        c=self.cpu();target=c.jvm_view.local_function('jni_GetVersion')['address'];c.write_private(SP,struct.pack('<Q',RET));c.reg('RDI',c.jni_state['env']);c.run(target)
        self.assertEqual(c.reg('RAX'),VERSION);self.assertNotEqual(c.reg('RAX'),0xdeadbeef);self.assertEqual(c.completed,1);self.assertTrue(c.jvm_view.unchanged(c));self.assertFalse(c.code_allowed(target+5))
    def test_open_lookup_and_dladdr_exports(self):
        c=self.cpu();self.assertEqual(self.open(c),HANDLE);c.reg('RDI',HANDLE);c.reg('RSI',self.string(c,'JNI_CreateJavaVM'));address=model(c,'dlsym');self.assertEqual(address,c.jvm_view.symbol('JNI_CreateJavaVM')['address'])
        c.reg('RDI',address);c.reg('RSI',SP+64);self.assertEqual(model(c,'dladdr'),1);fname,base,sname,saddr=struct.unpack('<QQQQ',c.read_known(SP+64,32));self.assertEqual(base,BASE);self.assertEqual(saddr,address);self.assertEqual(c.ascii(fname),'/virtual/jdk/lib/server/libjvm.so');self.assertEqual(c.ascii(sname),'JNI_CreateJavaVM')
    def test_dladdr_local_is_not_exported(self):
        c=self.cpu();c.reg('RDI',c.jvm_view.local_function('jni_GetEnv')['address']);c.reg('RSI',SP+64);self.assertEqual(model(c,'dladdr'),1);self.assertEqual(c.read_known(SP+80,16),bytes(16))
    def test_unknown_symbols_and_flags_stop(self):
        c=self.cpu();self.open(c);c.reg('RDI',HANDLE);c.reg('RSI',self.string(c,'jni_GetEnv'))
        with self.assertRaises(ModelHalt):model(c,'dlsym')
        c=self.cpu();c.reg('RDI',self.string(c,'/virtual/jdk/lib/server/libjvm.so'));c.reg('RSI',1)
        with self.assertRaises(ModelHalt):model(c,'dlopen')
    def test_writable_jvm_runtime_data_is_unknown(self):
        c=self.cpu()
        with self.assertRaises(ModelHalt):c.read_known(BASE+0xe000,8)
        self.assertEqual(c.stop['reason'],'UNINITIALIZED_READ');self.assertTrue(c.jvm_view.unchanged(c))
    def test_checkpoint_requires_identical_artifact_and_rebind(self):
        c=self.cpu();c.stop={'reason':'TEST'};state=json.loads(json.dumps(capture(c)))
        d=JniGuardedCPU(io.StringIO(),'heap',limit=1);d.add_image(RET,b'\x90'*16);d.add_image(0xd2d000,bytes(4096),False);d.protect_image();restore(d,state);self.assertFalse(d.jvm_interfaces_ready);d.configure_jvm_artifact(owned_jvm());self.assertTrue(d.jvm_interfaces_ready);self.assertEqual(d.jni_state,c.jni_state)
        changed=bytearray(owned_jvm());changed[-1]=1
        with self.assertRaises(ValueError):d.configure_jvm_artifact(bytes(changed))
    def test_mutated_artifact_cannot_be_checkpointed(self):
        c=self.cpu();c.uc.mem_write(BASE+0x4000,b'x');c.stop={'reason':'TEST'}
        with self.assertRaises(ValueError):capture(c)
if __name__=='__main__':unittest.main()
