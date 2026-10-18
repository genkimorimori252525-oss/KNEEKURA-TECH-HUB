#!/usr/bin/env python3
"""Opt-in bounded simulated working image; immutable reference bytes and file stay separate.

No target native loading, imported function execution, host mprotect or OS file API.
Default guarded backend remains read-only. Every working-image store is journaled,
transactional, range-limited, budgeted and checked against an expected-image ledger.
"""
import argparse,hashlib,json
from pathlib import Path
from unicorn import UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC
from native_unicorn_guarded_ysm_265 import GuardedCPU,IMAGE_SHA
class ShadowGuardedCPU(GuardedCPU):
    MAX_IMAGE_BYTES=8*1024*1024
    MAX_IMAGE_EVENTS=1000000
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.shadow_ranges=[];self.shadow_expected={};self.shadow_events=0;self.shadow_bytes=0;self.reference_digests=None;self.lazy_new_calls=0;self.lazy_memset_calls=0;self.crc_counters_complete=True;self.loader_view_applied=False;self.loader_relocation_events=0;self.init_phase='dt-init';self.init_array_index=0;self.init_array_completed=[];self.call_in_progress=False;self.call_saved={};self.c_locale_handle=0;self.strerror_eperm=0;self.locale_model_calls=0;self.thread_locale=(1<<64)-1;self.memory_model_calls=0;self.atexit_registrations=[];self.external_data_slots=[];self.external_data_guard_applied=False;self.environment_model_calls=0;self.stdio_fixture_base=0;self.external_data_bindings={};self.external_binding_events=0;self.heap_free_calls=0;self.tls_spec=None;self.tls_block=0;self.tls_calls=0;self.thread_atexit_registrations=[]
    def external_data_hit(self,a,n):
        return next(((max(a,slot),name) for slot,name in getattr(self,'external_data_slots',[]) if slot<a+n and a<slot+8),None)
    def unknown(self,a,n):
        hit=self.external_data_hit(a,n)
        return hit[0] if hit else super().unknown(a,n)
    def read_known(self,a,n):
        hit=self.external_data_hit(a,n)
        if hit:self.emit('UNRESOLVED_DATA_SYMBOL',hit[1],f'address={hit[0]:x}');self.demand(False,'UNMODELED_EXTERNAL_DATA_READ',hit[0],n)
        return super().read_known(a,n)
    def _read(self,uc,access,a,n,value,user):
        hit=self.external_data_hit(a,n)
        if hit:self.emit('UNRESOLVED_DATA_SYMBOL',hit[1],f'address={hit[0]:x}');self.fail('UNMODELED_EXTERNAL_DATA_READ',hit[0],n);return
        super()._read(uc,access,a,n,value,user)
    def reference_hashes(self):return [hashlib.sha256(v).hexdigest() for a,b,v in self.image]
    def shadow_region(self,a,n):
        return next((i for i,(lo,hi,_) in enumerate(self.image) if lo<=a and a+n<=hi and lo!=self.loader_name),None)
    def grant_shadow_range(self,address,size,prot):
        # Exact byte guards below remain stricter than the page-sized emulator mapping.
        self.demand(0<=prot<=7 and address%4096==0 and 0<size<=16*1024*1024 and len(self.shadow_ranges)<128,'SHADOW_RANGE_REJECTED',address,size)
        self.demand(all(p in self.pages and p!=self.loader_name for p in range(address,(address+size+4095)&~4095,4096)),'SHADOW_RANGE_REJECTED',address,size)
        if self.reference_digests is None:self.reference_digests=self.reference_hashes()
        self.uc.mem_protect(address,((size+4095)//4096)*4096,prot)
        self.shadow_ranges.append((address,address+size,prot));self.emit('SHADOW_IMAGE_RANGE',f'address={address:x}',f'size={size:x}',f'prot={prot}','working_copy_only=true','host_permissions_changed=false')
    def write_model_memory(self,a,data):
        n=len(data)
        if not n:return
        if self.private_region(a,n):self.write_private(a,data);return
        self.demand(self.shadow_region(a,n) is not None and self.shadow_writable(a,n),'MODEL_WRITE_OUTSIDE_GRANTED_RANGE',a,n)
        self.demand(self.shadow_events+1<=self.MAX_IMAGE_EVENTS and self.shadow_bytes+n<=self.MAX_IMAGE_BYTES,'SHADOW_WRITE_BUDGET',a,n)
        self.uc.mem_write(a,data);self.commit_write(a,n)
    def _code(self,uc,address,size,user):
        super()._code(uc,address,size,user)
        if not self.stop and address==0x14f9c20 and bytes(uc.mem_read(address,size))==b'\xc3':self.pending='lazy-import';uc.emu_stop()
    def model(self,kind):
        if kind=='lazy-import':
            import struct
            sp=self.reg('RSP');self.demand(self.private_allowed(sp,32),'INVALID_LAZY_IMPORT_FRAME',sp,32)
            resolver,link_map,index,target=struct.unpack('<QQQQ',self.read_known(sp,32))
            self.demand(resolver==0 and link_map==0,'UNEXPECTED_LAZY_BINDER_STATE',sp)
            self.emit('LAZY_IMPORT_FRONTIER',f'relocation_index={index}',f'caller_return={target:x}')
            from native_c_locale_fixture_ysm_265 import IMPORTS as LOCALE_IMPORTS,SYMBOLS as LOCALE_SYMBOLS,model as locale_model
            from native_memory_imports_ysm_265 import IMPORTS as MEMORY_IMPORTS,SYMBOLS as MEMORY_SYMBOLS,model as memory_model
            from native_heap_imports_ysm_265 import IMPORTS as HEAP_IMPORTS,SYMBOLS as HEAP_SYMBOLS,model as heap_model
            from native_tls_fixture_ysm_265 import IMPORTS as TLS_IMPORTS,model as tls_model
            from native_jvm_loader_fixture_ysm_265 import IMPORTS as JVM_IMPORTS,SYMBOLS as JVM_SYMBOLS,model as jvm_model
            from native_pthread_once_fixture_ysm_265 import IMPORTS as ONCE_IMPORTS
            from native_pthread_fixture_ysm_265 import IMPORTS as THREAD_IMPORTS,SYMBOLS as THREAD_SYMBOLS,model as thread_model
            from native_sync_fixture_ysm_265 import IMPORTS as SYNC_IMPORTS,SYMBOLS as SYNC_SYMBOLS,model as sync_model
            from native_allocator_os_fixture_ysm_265 import IMPORTS as OS_IMPORTS,SYMBOLS as OS_SYMBOLS,model as os_model
            allocators={**ONCE_IMPORTS,**THREAD_IMPORTS,**JVM_IMPORTS,50:('dl_iterate_phdr',0x184d1a8,0x15eda1c),**SYNC_IMPORTS,**OS_IMPORTS,**TLS_IMPORTS,**LOCALE_IMPORTS,**MEMORY_IMPORTS,**HEAP_IMPORTS,118:('__cxa_thread_atexit_impl',0x184d3c8,0x153b3eb),6:('__cxa_atexit',0x184d048,0x15044c7),121:('secure_getenv',0x184d3e0,0x14bdbd9),250:('_Znwm',0x184d7e8,0x13fe69d),205:('_Znam',0x184d680,0x1478e57),197:('memset',0x184d640,0x14c39b7)}
            self.demand(index in allocators,'UNMODELED_LAZY_IMPORT',index)
            symbol,slot,stub=allocators[index]
            self.demand(self.read_known(slot,8)==struct.pack('<Q',stub) and self.read_known(stub,5)==b'\x68'+struct.pack('<I',index),'LAZY_IMPORT_IDENTITY_MISMATCH')
            self.demand(self.return_target_allowed(target,sp+32),'EXTERNAL_OR_NULL_TARGET',target)
            if symbol=='pthread_once':
                self.demand(hasattr(self,'begin_once'),'ONCE_BACKEND_REQUIRED');self.begin_once(sp,target);return
            elif symbol=='dl_iterate_phdr':
                self.demand(hasattr(self,'begin_phdr_callback'),'GUEST_CALLBACK_BACKEND_REQUIRED');self.begin_phdr_callback(sp,target);return
            elif symbol=='__cxa_thread_atexit_impl':
                function,arg,dso=self.reg('RDI'),self.reg('RSI'),self.reg('RDX')
                self.demand(self.code_allowed(function) and self.tls_block and self.tls_block<=arg<self.tls_block+self.tls_spec['memory_size'] and self.shadow_region(dso,8) is not None and len(self.thread_atexit_registrations)<1024,'UNMODELED_THREAD_ATEXIT_REGISTRATION',function)
                self.thread_atexit_registrations.append([function,arg,dso]);result=0;self.emit('VIRTUAL_THREAD_ATEXIT_REGISTRATION',f'function={function:x}',f'argument={arg:x}',f'dso={dso:x}','single_virtual_thread=true','callback_executed=false','host_registration=false')
            elif symbol=='__cxa_atexit':
                function,arg,dso=self.reg('RDI'),self.reg('RSI'),self.reg('RDX')
                self.demand(self.code_allowed(function) and len(self.atexit_registrations)<1024,'UNMODELED_ATEXIT_REGISTRATION',function)
                self.atexit_registrations.append([function,arg,dso]);result=0;self.emit('VIRTUAL_ATEXIT_REGISTRATION',f'function={function:x}',f'argument={arg:x}',f'dso={dso:x}','callback_executed=false','host_registration=false')
            elif symbol=='secure_getenv':
                key=self.ascii(self.reg('RDI'));self.demand(key=='GLIBCXX_TUNABLES','UNMODELED_ENVIRONMENT_KEY');result=0;self.environment_model_calls+=1;self.emit('VIRTUAL_ENVIRONMENT_ABSENT',key,'host_environment_read=false')
            elif symbol=='__tls_get_addr':result=tls_model(self)
            elif symbol in LOCALE_SYMBOLS:result=locale_model(self,symbol)
            elif symbol in JVM_SYMBOLS:result=jvm_model(self,symbol)
            elif symbol in THREAD_SYMBOLS:result=thread_model(self,symbol)
            elif symbol in SYNC_SYMBOLS:result=sync_model(self,symbol)
            elif symbol in OS_SYMBOLS:result=os_model(self,symbol)
            elif symbol in HEAP_SYMBOLS:result=heap_model(self,symbol)
            elif symbol in MEMORY_SYMBOLS:result=memory_model(self,symbol)
            elif symbol=='memset':
                result=self.reg('RDI');n=self.reg('RDX');value=self.reg('RSI')&255
                self.demand(0<=n<=0x100000,'UNMODELED_MEMSET_SIZE',n)
                if n:self.write_model_memory(result,bytes([value])*n)
                self.lazy_memset_calls+=1
            else:result=self.allocate(self.reg('RDI'),kind='operator-new');self.lazy_new_calls+=1
            self.reg('RAX',result);self.reg('RSP',sp+32);self.reg('RIP',target);self.emit('VIRTUAL_LAZY_IMPORT',f'symbol={symbol}',f'relocation_index={index}',f'result={result:x}','host_import_called=false');return

        if kind=='protection-result' and self.protection_result=='success-input':
            address,size,prot=self.reg('RDI'),self.reg('RSI'),self.reg('RDX')
            self.demand(0<=prot<=7 and len(self.shadow_ranges)<128,'SHADOW_RANGE_REJECTED',address,size)
            super().model(kind)
            self.grant_shadow_range(address,size,prot)
        else:super().model(kind)
    def shadow_writable(self,a,n):
        for at in range(a,a+n):
            prot=next((prot for lo,hi,prot in reversed(self.shadow_ranges) if lo<=at<hi),0)
            page_prot=next((prot for lo,hi,prot in reversed(self.shadow_ranges) if lo<=at<((hi+4095)&~4095)),0)
            if not prot&2 or not page_prot&2:return False
        return True
    def _write(self,uc,access,a,n,value,user):
        if not any(lo<a+n and a<hi for lo,hi,_ in self.image):return super()._write(uc,access,a,n,value,user)
        # The engine may perform a pending store after emu_stop; preserve every mapped byte.
        for k in range(n):
            at=a+k
            if (at&~4095) in self.pages:self.journal.append((at,bytes(uc.mem_read(at,1))))
        index=self.shadow_region(a,n)
        if index is None or not self.shadow_writable(a,n):self.fail('SHADOW_WRITE_OUTSIDE_GRANTED_RANGE',a,n);return
        pending=[(x,z) for x,z in self.writes if self.shadow_region(x,z) is not None]
        if self.shadow_events+len(pending)+1>self.MAX_IMAGE_EVENTS or self.shadow_bytes+sum(z for x,z in pending)+n>self.MAX_IMAGE_BYTES:self.fail('SHADOW_WRITE_BUDGET',a,n);return
        self.writes.append((a,n))
    def commit_write(self,a,n):
        index=self.shadow_region(a,n)
        if index is None:return super().commit_write(a,n)
        lo,hi,original=self.image[index]
        if index not in self.shadow_expected:self.shadow_expected[index]=bytearray(original)
        actual=bytes(self.uc.mem_read(a,n));before=bytes(self.shadow_expected[index][a-lo:a-lo+n]);self.shadow_expected[index][a-lo:a-lo+n]=actual
        self.shadow_events+=1;self.shadow_bytes+=n;self.crc_profile_verified=None
        self.emit('SHADOW_IMAGE_COMMITTED_WRITE',f'pc={self.pc:x}',f'address={a:x}',f'size={n}',f'before={before.hex()}',f'after={actual.hex()}','reference_bytes_unchanged=true')
    def expected_image_matches(self):
        return all(bytes(self.uc.mem_read(lo,hi-lo))==self.shadow_expected.get(i,original) for i,(lo,hi,original) in enumerate(self.image))
    def report_preservation(self):
        reference_ok=self.reference_digests is None or self.reference_hashes()==self.reference_digests
        expected_ok=self.expected_image_matches();unchanged=self.image_unchanged()
        self.emit('SHADOW_PRESERVATION',f'immutable_reference_unchanged={reference_ok}',f'working_image_matches_committed_ledger={expected_ok}',f'working_image_equals_reference={unchanged}',f'committed_events={self.shadow_events}',f'committed_bytes={self.shadow_bytes}',f'virtual_operator_new_calls={self.lazy_new_calls}',f'virtual_memset_calls={self.lazy_memset_calls}',f'crc_counter_history_complete={self.crc_counters_complete}',f'loader_relocation_events={self.loader_relocation_events}',f'runtime_image_events={self.shadow_events-self.loader_relocation_events-self.external_binding_events}',f'locale_model_calls={self.locale_model_calls}',f'memory_model_calls={self.memory_model_calls}',f'atexit_registrations={len(self.atexit_registrations)}',f'external_data_guard={self.external_data_guard_applied}',f'environment_model_calls={self.environment_model_calls}',f'external_binding_events={self.external_binding_events}',f'heap_free_calls={self.heap_free_calls}',f'tls_calls={self.tls_calls}')
        if not reference_ok or not expected_ok:raise AssertionError('Unaccounted image mutation')
        self.emit('BOUNDED_RESULT',self.stop['reason'],'target_host_library_execution=false','host_file_access=false','host_permissions_changed=false',f'working_copy_image_writes={self.shadow_events}','transactional_fault_state=true')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--resume-checkpoint',type=Path);p.add_argument('--checkpoint-out',type=Path);p.add_argument('--image',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--steps',type=int,default=4000000);p.add_argument('--seconds',type=int,default=180);a=p.parse_args()
    original=a.image.read_bytes()
    if hashlib.sha256(original).hexdigest()!=IMAGE_SHA:raise ValueError('Wrong immutable artifact')
    with a.out.open('w') as out:
        c=ShadowGuardedCPU(out,'proc-fixture',a.steps,a.seconds);c.load_image(original);c.configure_loader('image-only');c.virtual_platform=True;c.protection_result='success-input';c.cpuid_leaf1=(0,0,0,0);c.accelerate_crc=True
        c.emit('SHADOW_CONFIG','scenario=synthetic-clock-proc0-image-loader-open-failure-page4096-protection-success-cpuid-zero','max_working_image_write_bytes=8388608','max_working_image_write_events=1000000','reference_file_never_written=true');
        if a.resume_checkpoint:
            from native_guarded_checkpoint_ysm_265 import read_checkpoint
            c.emit('CHECKPOINT_SOURCE_SHA256',read_checkpoint(c,a.resume_checkpoint))
        r=c.run(c.reg('RIP') if a.resume_checkpoint else 0x152eb19)
        if a.checkpoint_out:
            from native_guarded_checkpoint_ysm_265 import write_checkpoint
            c.emit('CHECKPOINT_SAVED_SHA256',write_checkpoint(c,a.checkpoint_out))
    if a.image.read_bytes()!=original:raise AssertionError('Original artifact changed')
    print(json.dumps({'status':r,'attempted':c.attempted,'completed':c.completed,'shadow_events':c.shadow_events,'shadow_bytes':c.shadow_bytes,'reference_file_unchanged':True,'working_image_matches_ledger':c.expected_image_matches()}))
if __name__=='__main__':main()
