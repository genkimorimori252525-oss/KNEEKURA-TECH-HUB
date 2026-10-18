"""Own-byte guard/CPU fixtures. No target image is loaded by this suite."""
import io,struct,unittest
from unicorn import x86_const as X
from native_unicorn_guarded_ysm_265 import GuardedCPU,ModelHalt,STACK,STACK_SIZE,SP,HEAP,HEAP_SIZE,FILE_HANDLE
TOY=0x100000;DATA=0x200000
class GuardTests(unittest.TestCase):
    def cpu(self,code,mode='strict',limit=1):
        c=GuardedCPU(io.StringIO(),mode,limit);c.add_image(TOY,bytes.fromhex(code)+b'\x90'*32);c.add_image(DATA,b'\0'*4096,False);c.protect_image();return c
    def test_private_push_pop(self):
        c=self.cpu('505b','strict',2);c.reg('RAX',0x1122334455667788);c.run(TOY);self.assertEqual(c.reg('RBX'),0x1122334455667788);self.assertEqual(c.completed,2)
    def test_original_write_blocked(self):
        c=self.cpu('488903');c.reg('RBX',DATA);c.reg('RAX',0x11223344);c.run(TOY);self.assertEqual(c.stop['reason'],'ORIGINAL_IMAGE_WRITE_BLOCKED');self.assertEqual(bytes(c.uc.mem_read(DATA,8)),bytes(8));self.assertEqual(c.completed,0);self.assertEqual(c.reg('RIP'),TOY);self.assertTrue(c.image_unchanged())
    def test_padding_write_transaction(self):
        c=self.cpu('c6401801','heap');a=c.allocate(24);c.reg('RAX',a);c.run(TOY);self.assertEqual(c.stop['reason'],'OUTSIDE_PRIVATE_WRITABLE_REGIONS');self.assertEqual(bytes(c.uc.mem_read(a+24,1)),b'\0');self.assertIsNotNone(c.unknown(a+24,1));self.assertEqual(c.completed,0);self.assertEqual(c.reg('RIP'),TOY)
    def test_cross_mapping_write_rollback(self):
        c=self.cpu('488903');address=STACK+STACK_SIZE-4;c.write_private(address,b'ABCD');c.reg('RBX',address);c.reg('RAX',0x1122334455667788);c.run(TOY);self.assertEqual(bytes(c.uc.mem_read(address,4)),b'ABCD');self.assertEqual(c.completed,0)
    def test_unknown_read_rollback(self):
        c=self.cpu('488b03');c.reg('RBX',SP+32);c.reg('RAX',0x99);c.run(TOY);self.assertEqual(c.stop['reason'],'UNINITIALIZED_READ');self.assertEqual(c.reg('RAX'),0x99)
    def test_opaque_stale_read_blocked(self):
        c=self.cpu('8a03');c.reg('RBX',SP+32);c.write_private(SP+32,b'Q');c.known[STACK][SP+32-STACK]=0;c.opaque[SP+32]=SP+64;c.run(TOY);self.assertEqual(c.stop['reason'],'OPAQUE_VALUE_READ');self.assertEqual(c.reg('RAX'),0)
    def test_known_write_clears_opaque(self):
        c=self.cpu('c60342');c.reg('RBX',SP+32);c.opaque[SP+32]=SP+64;c.run(TOY);self.assertEqual(c.read_known(SP+32,1),b'B');self.assertNotIn(SP+32,c.opaque)
    def test_external_call_transaction(self):
        c=self.cpu('ffd0');c.reg('RAX',0xdeadbeef);c.run(TOY);self.assertEqual(c.stop['reason'],'EXTERNAL_OR_NULL_TARGET');self.assertEqual(c.reg('RSP'),SP);self.assertIsNotNone(c.unknown(SP-8,8));self.assertEqual(bytes(c.uc.mem_read(SP-8,8)),bytes(8))
    def test_syscall_blocked(self):
        c=self.cpu('0f05');c.reg('RAX',39);c.run(TOY);self.assertEqual(c.stop['reason'],'UNMODELED_ENVIRONMENT_INSTRUCTION');self.assertEqual(c.completed,0)
    def test_segment_context_blocked(self):
        c=self.cpu('64488b042528000000');c.run(TOY);self.assertEqual(c.stop['reason'],'UNMODELED_ENVIRONMENT_INSTRUCTION');self.assertEqual(c.completed,0)
    def test_xchg32_cpu_rule(self):
        c=self.cpu('44870c24');c.reg('R9',0xffffffffffffffff);c.write_private(SP,bytes(4));c.run(TOY);self.assertEqual(c.reg('R9'),0);self.assertEqual(c.read_known(SP,4),b'\xff'*4)
    def test_shr_masked_one_of(self):
        c=self.cpu('41c0eae1');c.reg('R10',0xde);c.run(TOY);self.assertEqual(c.reg('R10'),0x6f);self.assertEqual(c.reg('OF'),1)
    def test_shr_masked_zero_of(self):
        c=self.cpu('41c0eae0');c.reg('R10',0x12);c.uc.reg_write(X.UC_X86_REG_EFLAGS,0xa02);c.run(TOY);self.assertEqual(c.reg('R10'),0x12);self.assertEqual(c.reg('OF'),1)
    def test_copy_known_and_direction(self):
        for df in (0,1):
            c=self.cpu('f3a4','opaque',4);c.write_private(SP+32,b'ABC');c.reg('RSI',SP+32+(2 if df else 0));c.reg('RDI',SP-64+(2 if df else 0));c.reg('RCX',3);c.uc.reg_write(X.UC_X86_REG_EFLAGS,0x202|(df<<10));c.run(TOY);self.assertEqual(c.read_known(SP-64,3),b'ABC');self.assertEqual(c.completed,4);self.assertEqual(c.reg('RCX'),0)
    def test_opaque_copy_then_consumer(self):
        c=self.cpu('f3a48a03','opaque',10);c.reg('RSI',SP+32);c.reg('RDI',SP-64);c.reg('RBX',SP-64);c.reg('RCX',1);c.run(TOY);self.assertEqual(c.stop['reason'],'OPAQUE_VALUE_READ');self.assertEqual(c.opaque[SP-64],SP+32)
    def test_copy_overlap_identity(self):
        c=self.cpu('f3a4','opaque',4);c.reg('RSI',SP+32);c.reg('RDI',SP+33);c.reg('RCX',3);c.run(TOY);self.assertEqual(c.opaque[SP+35],SP+32)
    def test_clock_scenario(self):
        c=self.cpu('0f310f31','clock',2);c.seed=0xffffffff;c.stride=2;c.run(TOY);self.assertEqual(c.reg('RAX'),1);self.assertEqual(c.reg('RDX'),1);self.assertEqual(c.clock_reads,2)
    def test_clock_disabled(self):
        c=self.cpu('0f31');c.run(TOY);self.assertEqual(c.stop['reason'],'UNMODELED_RDTSC');self.assertEqual(c.clock_reads,0)
    def setup_frame(self,c,push=True):
        c.write_private(SP,(bytes(8) if push else b'')+struct.pack('<Q',TOY));c.reg('RSP',SP)
    def test_malloc_model_and_bounds(self):
        c=self.cpu('90','heap');self.setup_frame(c);c.reg('RDI',24);c.model('malloc');self.assertEqual(c.reg('RAX'),HEAP);self.assertIsNotNone(c.unknown(HEAP,1));self.assertFalse(c.private_allowed(HEAP+24,1));self.assertEqual(c.reg('RSP'),SP+16)
    def test_heap_exhaustion(self):
        c=self.cpu('90','heap')
        with self.assertRaises(ModelHalt):c.allocate(HEAP_SIZE+1)
        self.assertEqual(c.heap_used,0)
    def test_file_fixture_without_host_io(self):
        c=self.cpu('90','proc-fixture');self.setup_frame(c);c.write_private(SP+64,b'/proc/self/status\0');c.write_private(SP+128,b'r\0');c.reg('RDI',SP+64);c.reg('RSI',SP+128);c.model('fopen');self.assertEqual(c.reg('RAX'),FILE_HANDLE)
        self.setup_frame(c);c.reg('RDI',SP+256);c.reg('RSI',128);c.reg('RDX',FILE_HANDLE);c.model('fgets');self.assertEqual(c.read_known(SP+256,19),b'Name:\tvirtual-ysm\n\0')
        self.setup_frame(c,False);c.reg('RDI',FILE_HANDLE);c.model('fclose');self.assertFalse(c.file_open)
    def test_fgets_image_write_refused(self):
        c=self.cpu('90','proc-fixture');self.setup_frame(c);c.file_open=True;c.reg('RDI',DATA);c.reg('RSI',128);c.reg('RDX',FILE_HANDLE)
        with self.assertRaises(ModelHalt):c.model('fgets')
        self.assertEqual(c.file_position,0);self.assertTrue(c.image_unchanged())
    def test_privileged_environment_ops_blocked(self):
        for code in ('0f32','0f30','0f01d0','0fc7f8'):
            c=self.cpu(code);c.run(TOY);self.assertEqual(c.stop['reason'],'UNMODELED_ENVIRONMENT_INSTRUCTION');self.assertEqual(c.completed,0)
    def test_resource_configuration_rejected(self):
        for kwargs in ({'limit':0},{'limit':4000001},{'seconds':0},{'seconds':181}):
            with self.assertRaises(ValueError):GuardedCPU(io.StringIO(),**kwargs)
if __name__=='__main__':unittest.main()
