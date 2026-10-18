"""Explicit fresh-loader thread capability; a gateway, never a host pthread call."""
import struct,time
from unicorn import UC_PROT_READ,UC_PROT_EXEC
from native_pthread_fixture_ysm_265 import ThreadGuardedCPU,model as pthread_model
GATE=0x770000000000
SLOT=0xd2cf70
NAME='__pthread_key_create'
PAGE=b'\xc3'+bytes(4095)
class ThreadLinkedCPU(ThreadGuardedCPU):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.uc.mem_map(GATE,4096,UC_PROT_READ|UC_PROT_EXEC);self.uc.mem_write(GATE,PAGE)
    def gate_enabled(self):return self.threads_enabled and self.external_data_bindings.get(NAME)==GATE
    def code_allowed(self,a,n=1):return (a==GATE and n==1 and self.gate_enabled()) or super().code_allowed(a,n)
    def unknown(self,a,n):
        if GATE<=a and a+n<=GATE+1:return None
        return super().unknown(a,n)
    def _write(self,uc,access,a,n,value,user):
        if GATE<a+n and a<GATE+4096:
            for at in range(max(a,GATE),min(a+n,GATE+4096)):self.journal.append((at,bytes(uc.mem_read(at,1))))
            self.fail('THREAD_GATE_WRITE_BLOCKED',a,n);return
        super()._write(uc,access,a,n,value,user)
    def _code(self,uc,address,size,user):
        if address==GATE:
            if self.stop:return
            if not self.code_allowed(address,size):self.fail('THREAD_GATE_DISABLED',address);return
            if time.monotonic()>self.deadline:self.fail('TIME_BUDGET',address);return
            self.pc=address;self.current_raw=b'\xc3';self.attempted+=1;self.pending='pthread-weak-key';self.emit('WEAK_PTHREAD_GATE_INTERCEPT','host_code_executed=false');uc.emu_stop();return
        super()._code(uc,address,size,user)
    def model(self,kind):
        if kind!='pthread-weak-key':return super().model(kind)
        sp,target=self.frame(False);result=pthread_model(self,NAME);self.reg('RAX',result);self.reg('RSP',sp+8);self.reg('RIP',target)
    def verify_thread_gate(self):
        if bytes(self.uc.mem_read(GATE,4096))!=PAGE:raise ValueError('Thread gateway changed')
        if self.threads_enabled:
            if not self.gate_enabled() or self.shadow_region(SLOT,8) is None or bytes(self.uc.mem_read(SLOT,8))!=struct.pack('<Q',GATE):raise ValueError('Thread support binding mismatch')
        elif NAME in self.external_data_bindings:raise ValueError('Disabled thread capability has binding')
    def capture_sparse(self):
        self.verify_thread_gate();return super().capture_sparse()
    def restore_sparse(self,s):
        super().restore_sparse(s);self.verify_thread_gate()
    def report_preservation(self):
        self.verify_thread_gate();self.emit('THREAD_GATE_PRESERVATION','unchanged=true',f'enabled={self.threads_enabled}','host_threads=false');super().report_preservation()

def configure_thread_support(cpu,data,entries):
    from native_elf_loader_view_ysm_265 import manifest
    m=manifest(data)
    if [SLOT,NAME] not in m['weak_function_slots']:raise ValueError('Pinned weak pthread identity mismatch')
    if cpu.attempted or getattr(cpu,'origin_completed',0) or not cpu.loader_view_applied or cpu.threads_enabled:raise ValueError('Thread support requires fresh relocated pre-initializer scenario')
    if cpu.shadow_region(SLOT,8) is None or not cpu.shadow_writable(SLOT,8) or bytes(cpu.uc.mem_read(SLOT,8))!=bytes(8) or NAME in cpu.external_data_bindings:raise ValueError('Unexpected weak pthread binding state')
    cpu.configure_threads(entries);cpu.uc.mem_write(SLOT,struct.pack('<Q',GATE));cpu.commit_write(SLOT,8);cpu.external_data_bindings[NAME]=GATE;cpu.external_binding_events+=1
    cpu.emit('EXPLICIT_WEAK_THREAD_BINDING',NAME,f'slot={SLOT:x}',f'gateway={GATE:x}','before_initializers=true','other_weak_imports_unchanged=true','workers_deferred=true','host_linker_called=false')
    cpu.verify_thread_gate()
