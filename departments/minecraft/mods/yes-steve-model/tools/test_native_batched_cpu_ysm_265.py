"""Own-byte differential tests. No target image, host JVM or native imports."""
import io
import re
import struct
import unittest
from unicorn import x86_const as X
from native_sparse_vm_ysm_265 import SparseGuardedCPU
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_sync_fixture_ysm_265 import SyncGuardedCPU
from native_jni_fixture_ysm_265 import JniGuardedCPU, TRAPS, ENV_NAMES, VERSION, CALLBACK_RETURN
from native_unicorn_guarded_ysm_265 import GuardedCPU, REGS, STACK, STACK_SIZE, HEAP, HEAP_SIZE, SP, RETURN
try:
    from native_batched_cpu_ysm_265 import BatchedMixin, BatchedGuarded, BatchedJni
except ImportError:
    BatchedMixin = BatchedGuarded = BatchedJni = None

TOY = 0x100000

class BatchedTests(unittest.TestCase):
    def pair(self, code, setup=lambda c: None, limit=20, base=GuardedCPU, mode='heap', batch=256, entry=TOY):
        self.assertIsNotNone(BatchedMixin, 'Optional batched executor is not implemented')
        batched = type('OwnByteBatched', (BatchedMixin, base), {})
        cpus = []
        for cls in (base, batched):
            c = cls(io.StringIO(), mode, limit)
            c.add_image(TOY, bytes.fromhex(code) + b'\x90' * 64)
            c.protect_image()
            if isinstance(c, BatchedMixin): c.batch_size = batch
            setup(c)
            c.run(entry)
            cpus.append(c)
        self.equal(*cpus)
        return cpus

    def equal(self, a, b):
        self.assertEqual(a.stop, b.stop)
        self.assertEqual(re.sub(r"rollbacks=\d+", "rollbacks=IGNORED",a.out.getvalue()),re.sub(r"rollbacks=\d+", "rollbacks=IGNORED",b.out.getvalue()))
        self.assertEqual({r:a.reg(r) for r in REGS}, {r:b.reg(r) for r in REGS})
        self.assertEqual(a.uc.reg_read(X.UC_X86_REG_EFLAGS), b.uc.reg_read(X.UC_X86_REG_EFLAGS))
        for i in range(32):
            reg=getattr(X,'UC_X86_REG_ZMM'+str(i))
            self.assertEqual(a.uc.reg_read(reg),b.uc.reg_read(reg))
        for base, size in ((STACK, STACK_SIZE), (HEAP, HEAP_SIZE)):
            self.assertEqual(bytes(a.uc.mem_read(base,size)), bytes(b.uc.mem_read(base,size)))
        for name in ('known','opaque','attempted','completed','heap_writes','clock_reads','malloc_calls','modeled_copies','allocations','oracle_seen','oracle_checks'):
            self.assertEqual(getattr(a,name),getattr(b,name),name)
        for page in getattr(a,'vm_pages',{}):
            self.assertEqual(bytes(a.uc.mem_read(page,4096)),bytes(b.uc.mem_read(page,4096)))
        for lo,hi,_ in a.image:
            self.assertEqual(bytes(a.uc.mem_read(lo,hi-lo)),bytes(b.uc.mem_read(lo,hi-lo)))
        for name in ('vm_pages','vm_write_events','vm_write_bytes','shadow_expected','shadow_events','shadow_bytes','jni_state','sync_objects','sync_calls','crc_blocks','crc_iterations','crc_logical_steps'):
            if hasattr(a,name): self.assertEqual(getattr(a,name),getattr(b,name),name)

    def test_stores_read_after_write(self):
        self.pair('c603114883c301c60322488b43ff', lambda c:c.reg('RBX',SP+32), limit=5)

    def test_first_second_quota(self):
        for limit in (1,2,3):
            for batch in (1,2,256):
                self.pair('505b90c3',lambda c:c.reg('RAX',123),limit=limit,batch=batch)

    def test_partial_invalid_store(self):
        def setup(c):
            c.reg('RBX',STACK+STACK_SIZE-4);c.reg('RAX',0x1122334455667788)
            c.write_private(STACK+STACK_SIZE-4,b'ABCD')
        self.pair('90488903',setup)

    def test_unknown_read(self):
        self.pair('90488b03',lambda c:c.reg('RBX',SP+32))

    def test_external_call_and_return(self):
        for target in (0xdeadbeef,TOY+128,RETURN):
            self.pair('90ffd0',lambda c:c.reg('RAX',target))
        self.pair('c3')
        self.pair('90c3',lambda c:(c.reg('RSP',SP+8),c.write_private(SP+8,struct.pack('<Q',RETURN))))

    def test_clock_pending(self):
        self.pair('900f31900f31c3',mode='clock')

    def test_model_error(self):
        self.pair('900fa2',lambda c:setattr(c,'cpuid_leaf1',(0,0,0,0)))

    def test_private_readonly(self):
        def setup(c):
            c.reg('RBX',SP+32);c.private_readonly.append((SP+32,SP+40))
        self.pair('90c60355',setup)

    def test_forbidden_instruction(self):
        self.pair('900f05')

    def test_resume(self):
        a,b=self.pair('505b9090c3',lambda c:c.reg('RAX',123),limit=2)
        for c in (a,b):
            c.stop=None;c.limit=10;c.run(c.reg('RIP'))
        self.equal(a,b)

    def test_shadow_store_quotas(self):
        for cap in (0,1,2):
            def setup(c):
                c.add_image(0x200000,bytes(4096),False);c.protect_image()
                c.grant_shadow_range(0x200000,4096,3)
                c.reg('RBX',0x200000);c.MAX_IMAGE_EVENTS=cap
            self.pair('c60311c6430122c3',setup,base=ShadowGuardedCPU)

    def test_sparse_stores_readonly_and_quota(self):
        for prot in (1,3):
            for cap in (0,1,2):
                def setup(c):
                    c.reg('RBX',c.vm_map(4096,prot));c.MAX_VM_EVENTS=cap
                self.pair('c60311c6430122c3',setup,base=SparseGuardedCPU)

    def test_sparse_partial_store(self):
        def setup(c):
            a=c.vm_map(4096);c.write_model_memory(a+4092,b'ABCD')
            c.reg('RBX',a+4092);c.reg('RAX',0x1122334455667788)
        self.pair('90488903',setup,base=SparseGuardedCPU)

    def test_sync_write_journal(self):
        def setup(c):
            c.reg('RBX',SP+32);c.write_private(SP+32,bytes(32))
            c.sync_objects[str(SP+32)]={'kind':'semaphore','size':32,'value':0,'active':True}
        self.pair('90c60311',setup,base=SyncGuardedCPU)

    def test_import_malloc_pending_and_tail_return(self):
        def setup(c):
            c.add_image(0x13d8472,b'\xc3');c.protect_image()
            c.reg('RAX',0x13d8472);c.reg('RDI',24)
        # Push the import slot; JMP into the model, whose frame consumes slot + sentinel.
        self.pair('6a00ffe0',setup)

    def test_jni_outer_mro_gateway(self):
        def setup(c):
            c.configure_jni();c.reg('RDI',c.jni_state['env'])
            c.reg('RAX',TRAPS+16*(8+ENV_NAMES.index('GetVersion')))
        a,b=self.pair('ffd0c3',setup,base=JniGuardedCPU)
        self.assertEqual(b.jni_state['getversion_calls'],1)
        self.assertEqual(b.reg('RAX'),VERSION)
        self.assertEqual(b.stop['reason'],'ENTRY_RETURN')

    def test_jni_model_tail_return(self):
        def setup(c):
            c.configure_jni();c.reg('RDI',c.jni_state['env'])
            c.reg('RAX',TRAPS+16*(8+ENV_NAMES.index('GetVersion')))
        self.pair('ffe0',setup,base=JniGuardedCPU)

    def test_jni_callback_gateway(self):
        def setup(c):
            c.configure_jni();c.write_private(SP-8,struct.pack('<Q',CALLBACK_RETURN))
            c.reg('RSP',SP-8)
            c.jni_state['pending_callbacks']=[{'sp':SP-32,'target':TOY+16,'function':TOY,'data':0,'infos':[0],'module_index':0,'saved':{r:c.reg(r) for r in ('RBX','RBP','R12','R13','R14','R15')}}]
        self.pair('c3',setup,base=JniGuardedCPU)

    def test_copy_model_preserves_partial_error_semantics(self):
        def setup(c):
            c.reg('RCX',2);c.reg('RSI',SP+32);c.reg('RDI',SP-64)
        self.pair('f3a48a03',setup,mode='opaque')

    def test_code_range_end_rolls_back_prior(self):
        for cls in (GuardedCPU,BatchedGuarded):
            c=cls(io.StringIO(),limit=10);c.add_image(TOY,b'\x50');c.protect_image()
            c.run(TOY)
            self.assertEqual(c.completed,0);self.assertEqual(c.reg('RSP'),SP)
            self.assertEqual(bytes(c.uc.mem_read(SP-8,8)),bytes(8))

    def test_instruction_trace_is_optional(self):
        c=BatchedGuarded(io.StringIO(),limit=1);c.trace_instructions=False
        c.add_image(TOY,b'\x90\x90');c.protect_image();c.run(TOY)
        self.assertNotIn('INS\t',c.out.getvalue());self.assertIn('COUNTS\t',c.out.getvalue())

    def test_time_interrupt_rolls_back_current(self):
        import time
        class DelayedGuard(GuardedCPU):
            def _code(self,uc,address,size,user):
                super()._code(uc,address,size,user)
                time.sleep(0.04)
        cpus=[]
        for cls in (DelayedGuard,type('DelayedBatch',(BatchedMixin,DelayedGuard),{})):
            c=cls(io.StringIO(),limit=10,seconds=0.01)
            c.add_image(TOY,b'\x50\x90');c.protect_image();c.reg('RAX',123)
            c.run(TOY);cpus.append(c)
        self.equal(*cpus)
        self.assertEqual(cpus[1].stop['reason'],'ENGINE_TIMEOUT')
        self.assertEqual(cpus[1].completed,0)

    def test_decoded_instruction_extends_beyond_allowed_range(self):
        cpus=[]
        for cls in (GuardedCPU,BatchedGuarded):
            c=cls(io.StringIO(),limit=10)
            c.add_image(TOY,bytes.fromhex('504889c0'))
            c.exec_ranges=[(TOY,TOY+2)]
            c.protect_image();c.run(TOY);cpus.append(c)
        self.equal(*cpus)
        self.assertEqual(cpus[1].completed,1)

    def test_oracle_fault_commits_prior_only(self):
        cpus=[]
        for cls in (GuardedCPU,BatchedGuarded):
            c=cls(io.StringIO(),limit=10);c.oracle_enabled=True
            c.add_image(0x174d06e,b'\x50\x90\x90');c.protect_image()
            c.run(0x174d06e);cpus.append(c)
        self.equal(*cpus)
        self.assertEqual(cpus[1].stop['reason'],'ORACLE_DISAGREEMENT')
        self.assertEqual(cpus[1].completed,1)

    def test_native_rep_iterations(self):
        def setup(c):
            c.write_private(SP+32,b'ABC');c.reg('RSI',SP+32)
            c.reg('RDI',SP-64);c.reg('RCX',3);c.reg('RAX',0x44)
        for code in ('f3a4c3','f3aac3'):
            for limit in (1,2,3,4,5,20):
                self.pair(code,setup,mode='strict',limit=limit)

    def test_self_modifying_shadow(self):
        def setup(c):
            c.grant_shadow_range(TOY,4096,7);c.reg('RBX',TOY+3)
        self.pair('c60390c390c3',setup,base=ShadowGuardedCPU)

    def test_deterministic_arithmetic_sequences(self):
        import random
        rng=random.Random(265)
        ops=['48ffc0','48ffcb','4831d0','4801c1','48d1e0','48d1eb','505a','4887d8','90']
        for i in range(30):
            code=''.join(rng.choice(ops) for _ in range(15))+'c3'
            self.pair(code,lambda c:(c.reg('RAX',0x88776655),c.reg('RBX',0x11223344)),limit=40,batch=3 if i%2 else 256)

    def test_self_modifying_batch_edges(self):
        for offset in (0,1,3,5,16,32):
            for batch in (2,3,256):
                def setup(c):
                    c.grant_shadow_range(TOY,4096,7);c.reg('RBX',TOY+offset)
                self.pair('c603909090c3',setup,base=ShadowGuardedCPU,batch=batch,limit=8)

    def test_crc_pending_models(self):
        from native_crc32_loop_profile_ysm_265 import PROFILES, standard_table
        for p in PROFILES.values():
            for fast in (False,True):
                def setup(c):
                    for a,raw in p['code'].items():c.add_image(a,raw)
                    c.add_image(p['exit'],b'\x90')
                    c.add_image(p['table'],struct.pack('<256I',*(v^p['mask'] for v in standard_table())),False)
                    c.add_image(0x300000,b'abcde',False);c.protect_image()
                    c.reg(p['source_reg'],0x300000);c.reg(p['table_reg'],p['table'])
                    c.reg(p.get('counter_reg','RCX'),5);c.reg(p['crc_reg'],0x12345678)
                    c.accelerate_crc=fast
                a,b=self.pair('',setup,limit=p['steps']+1 if fast else 5*p['steps'],entry=p['entry'])
                self.assertEqual(b.crc_blocks,1 if fast else 0)

if __name__=='__main__': unittest.main()
