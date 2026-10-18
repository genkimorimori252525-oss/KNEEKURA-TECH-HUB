#!/usr/bin/env python3
"""Bounded Unicorn CPU model. Never loads YSM as a host library or invokes its imports.

Image pages are read/execute only. Each native instruction is a transaction:
private writes and CPU state roll back on a guard failure. This is necessary
because Unicorn's normal write-hook emu_stop does not cancel the pending store.
"""
import argparse, bisect, hashlib, json, struct, time, threading
from pathlib import Path
from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_64, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC, UC_PROT_ALL, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_INVALID, UC_QUERY_TIMEOUT, UC_MEM_FETCH_UNMAPPED, UC_MEM_FETCH_PROT
from unicorn import x86_const as X
from native_export_backing_ysm_265 import regions

IMAGE_SHA='15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22'
STACK=0x700000000000; STACK_SIZE=0x10000; SP=STACK+0x8008
HEAP=0x710000000000; HEAP_SIZE=0x100000; FILE_HANDLE=0x720000000000
RETURN=0x7fff00000000; MASK=(1<<64)-1
REGS={n:getattr(X,'UC_X86_REG_'+n) for n in ['RAX','RBX','RCX','RDX','RSI','RDI','RBP','RSP','R8','R9','R10','R11','R12','R13','R14','R15','RIP']}
FLAG_BITS={'CF':0,'PF':2,'AF':4,'ZF':6,'SF':7,'IF':9,'OF':11,'DF':10}
MODES={'strict':0,'opaque':1,'clock':2,'heap':3,'proc-failure':4,'proc-fixture':5}
class ModelHalt(Exception): pass

class GuardedCPU:
    def __init__(self,out,mode='strict',limit=10000,seconds=60,seed=0x1122334455667788,stride=1000,pid=0):
        if mode not in MODES or not 0<limit<=2000000 or not 0<seconds<=120:raise ValueError('Invalid bounded configuration')
        self.uc=Uc(UC_ARCH_X86,UC_MODE_64);self.out=out;self.level=MODES[mode];self.limit=limit;self.seconds=seconds
        self.seed=seed&MASK;self.stride=stride&MASK;self.clock_reads=0;self.allocations=[];self.heap_used=0;self.malloc_calls=0
        self.fopen_calls=self.fgets_calls=self.fclose_calls=0;self.file_open=False;self.file_position=0
        self.fixture=f'Name:\tvirtual-ysm\nTracerPid:\t{pid}\n'.encode('ascii')
        self.protection_result='disabled';self.protection_calls=0;self.virtual_platform=False;self.platform_calls=0;self.virtual_loader='disabled';self.dladdr_calls=0;self.loader_name=0x730000000000;self.loader_ready=False
        self.accelerate_crc=False;self.crc_profile_verified=None;self.crc_blocks=self.crc_iterations=self.crc_logical_steps=0
        self.attempted=self.completed=0;self.modeled_copies=self.opaque_copies=0;self.heap_writes=0;self.rollback_count=0
        self.known={STACK:bytearray(STACK_SIZE),HEAP:bytearray(HEAP_SIZE)};self.opaque={};self.image=[];self.exec_ranges=[];self.pages={}
        self.stop=None;self.pending=None;self.journal=[];self.writes=[];self.pc=0;self.oracle_seen=set();self.oracle_checks=0;self.oracle_enabled=False
        self.uc.mem_map(STACK,STACK_SIZE,UC_PROT_READ|UC_PROT_WRITE);self.uc.mem_map(HEAP,HEAP_SIZE,UC_PROT_READ|UC_PROT_WRITE)
        for reg in REGS.values():self.uc.reg_write(reg,0)
        self.reg('RSP',SP);self.uc.reg_write(X.UC_X86_REG_EFLAGS,0x202)
        self.write_private(SP,struct.pack('<Q',RETURN),log=False)
        self.uc.hook_add(UC_HOOK_CODE,self._code)
        self.uc.hook_add(UC_HOOK_MEM_READ,self._read)
        self.uc.hook_add(UC_HOOK_MEM_WRITE,self._write)
        self.uc.hook_add(UC_HOOK_MEM_INVALID,self._invalid)
    def emit(self,*parts):self.out.write('\t'.join(str(p) for p in parts)+'\n')
    def reg(self,name,value=None):
        if value is not None:self.uc.reg_write(REGS[name],value&MASK);return
        if name in FLAG_BITS:return (self.uc.reg_read(X.UC_X86_REG_EFLAGS)>>FLAG_BITS[name])&1
        if name=='R11D':return self.reg('R11')&0xffffffff
        return self.uc.reg_read(REGS[name])
    def add_image(self,address,data,execute=True):
        end=address+len(data)
        for page in range(address&~4095,(end+4095)&~4095,4096):
            if page not in self.pages:self.uc.mem_map(page,4096,UC_PROT_ALL);self.pages[page]=UC_PROT_READ
            else:self.uc.mem_protect(page,4096,UC_PROT_ALL)
            if execute:self.pages[page]|=UC_PROT_EXEC
        self.uc.mem_write(address,data);self.image.append((address,end,bytes(data)))
        if execute:self.exec_ranges.append((address,end))
    def protect_image(self):
        for page,perm in self.pages.items():self.uc.mem_protect(page,4096,perm)
    def load_image(self,data):
        if hashlib.sha256(data).hexdigest()!=IMAGE_SHA:raise ValueError('Wrong original image')
        for r in regions(data):
            start=r['address'];end=start+r['memory_size'];execute=bool(r['flags']&1)
            v=data[r['file_offset']:r['file_offset']+r['file_size']]+bytes(r['memory_size']-r['file_size']);self.image.append((start,end,v))
            if execute:self.exec_ranges.append((start,end))
            for page in range(start&~4095,(end+4095)&~4095,4096):self.pages[page]=self.pages.get(page,UC_PROT_READ)|(UC_PROT_EXEC if execute else 0)
        pages=sorted(self.pages);runs=[]
        for page in pages:
            if runs and runs[-1][1]==page:runs[-1][1]+=4096
            else:runs.append([page,page+4096])
        for a,b in runs:self.uc.mem_map(a,b-a,UC_PROT_ALL)
        for a,b,v in self.image:self.uc.mem_write(a,v)
        runs=[]
        for page in pages:
            perm=self.pages[page]
            if runs and runs[-1][1]==page and runs[-1][2]==perm:runs[-1][1]+=4096
            else:runs.append([page,page+4096,perm])
        for a,b,perm in runs:self.uc.mem_protect(a,b-a,perm)
        self.oracle_enabled=True
    def image_unchanged(self):return all(bytes(self.uc.mem_read(a,b-a))==v for a,b,v in self.image)
    def code_allowed(self,a,n=1):return a>=0x1000 and any(lo<=a and a+n<=hi for lo,hi in self.exec_ranges)
    def physical(self,a,n=1):
        for base,size in [(STACK,STACK_SIZE),(HEAP,HEAP_SIZE)]:
            if base<=a and a+n<=base+size:return base
        return None
    def private_allowed(self,a,n):
        if n<=0:return False
        if STACK<=a and a+n<=STACK+STACK_SIZE:return True
        return self.level>=3 and any(start<=a and a+n<=start+size for start,size in self.allocations)
    def unknown(self,a,n):
        base=self.physical(a,n)
        if base is not None:
            k=self.known[base].find(0,a-base,a-base+n)
            return None if k<0 else base+k
        if any(lo<=a and a+n<=hi for lo,hi,_ in self.image):return None
        for k in range(n):
            at=a+k;base=self.physical(at)
            if base is not None:
                if not self.known[base][at-base]:return at
            elif not any(lo<=at<hi for lo,hi,_ in self.image):return at
        return None
    def fail(self,reason,a=0,n=0):
        if self.stop is None:self.stop={'reason':reason,'pc':self.pc,'address':a,'size':n};self.emit('STOP',reason,f'pc={self.pc:x}',f'address={a:x}',f'size={n}')
        self.uc.emu_stop()
    def demand(self,condition,reason,a=0,n=0):
        if not condition:self.fail(reason,a,n);raise ModelHalt(reason)
    def read_known(self,a,n):
        bad=self.unknown(a,n)
        self.demand(bad is None,'OPAQUE_VALUE_READ' if bad in self.opaque else 'UNINITIALIZED_READ',bad or a,n)
        return bytes(self.uc.mem_read(a,n))
    def mark_known(self,a,n):
        base=self.physical(a,n)
        if base is None:raise ValueError('Private write crosses physical arenas')
        self.known[base][a-base:a-base+n]=b'\1'*n
        for k in range(n):self.opaque.pop(a+k,None)
    def write_private(self,a,data,log=True):
        self.demand(self.private_allowed(a,len(data)),'OUTSIDE_PRIVATE_WRITABLE_REGIONS',a,len(data))
        self.uc.mem_write(a,data);self.mark_known(a,len(data))
        if log:self.log_heap_write(a,len(data))
    def log_heap_write(self,a,n):
        if HEAP<=a<HEAP+HEAP_SIZE:self.heap_writes+=1;self.emit('PRIVATE_HEAP_WRITE',f'pc={self.pc:x}',f'address={a:x}',f'size={n}')
    def _code(self,uc,address,size,user):
        if self.stop:return
        if time.monotonic()>self.deadline:self.fail('TIME_BUDGET',address);return
        if not self.code_allowed(address,size):self.fail('EXTERNAL_OR_NULL_TARGET',address,size);return
        self.pc=address;raw=bytes(uc.mem_read(address,size));self.attempted+=1;self.emit('INS',f'{address:x}',raw.hex(),'Unicorn')
        self.check_oracle()
        if self.stop:return
        if self.accelerate_crc and address in (0x15f0d5e,0x1503f30):
            from native_crc32_loop_profile_ysm_265 import eligible
            if eligible(self):self.pending='crc';uc.emu_stop();return
        if raw==b'\xf3\xa4' and self.level>=1:self.pending='copy'
        elif raw==b'\x0f\x31':
            if self.level>=2:self.pending='clock'
            else:self.fail('UNMODELED_RDTSC',address);return
        elif address==0x13d8472 and self.level>=3:self.pending='malloc'
        elif address==0x13d8499 and self.level>=4:self.pending='fopen'
        elif address==0x13d84a0 and self.level>=5:self.pending='fgets'
        elif address==0x13d84a1 and self.level>=5:self.pending='fclose'
        elif address==0x13d8466 and self.virtual_loader!='disabled':
            if raw!=bytes.fromhex('ff25b4534700'):self.fail('LOADER_THUNK_MISMATCH',address);return
            self.pending='dladdr'
        elif address==0x13d84d6 and self.protection_result!='disabled':self.pending='protection-result'
        elif self.virtual_platform and address in (0x13d84a7,0x13d84cf):
            self.pending='open-unavailable' if address==0x13d84a7 else 'page-size'
        else:
            op=raw;segmented=False
            while op and (op[0] in (0x66,0x67,0xf0,0xf2,0xf3,0x2e,0x36,0x3e,0x26,0x64,0x65) or 0x40<=op[0]<=0x4f):
                segmented=segmented or op[0] in (0x64,0x65);op=op[1:]
            forbidden=(segmented or not op or op[0] in (0xcc,0xcd,0xce,0xcf,0xf4,0xe4,0xe5,0xe6,0xe7,0xec,0xed,0xee,0xef,0x6c,0x6d,0x6e,0x6f) or op[:2] in (b'\x0f\x05',b'\x0f\x07',b'\x0f\x31',b'\x0f\x33',b'\x0f\x34',b'\x0f\x35',b'\x0f\xa2',b'\x0f\xc7',b'\x0f\x00',b'\x0f\x01',b'\x0f\x06',b'\x0f\x08',b'\x0f\x09',b'\x0f\x20',b'\x0f\x21',b'\x0f\x22',b'\x0f\x23',b'\x0f\x30',b'\x0f\x32',b'\x0f\x78',b'\x0f\x79',b'\x0f\xae') or op[:3]==b'\x0f\x01\xf9')
            if forbidden:self.fail('UNMODELED_ENVIRONMENT_INSTRUCTION',address,size);return
        if self.pending:uc.emu_stop()
    def _read(self,uc,access,a,n,value,user):
        bad=self.unknown(a,n)
        if bad is not None:self.fail('OPAQUE_VALUE_READ' if bad in self.opaque else 'UNINITIALIZED_READ',bad,n)
    def _write(self,uc,access,a,n,value,user):
        # Always preserve mapped private bytes, including allocation padding, for rollback.
        if self.physical(a,n) is not None:self.journal.append((a,bytes(uc.mem_read(a,n))))
        else:
            for k in range(n):
                if self.physical(a+k) is not None:self.journal.append((a+k,bytes(uc.mem_read(a+k,1))))
        if not self.private_allowed(a,n):
            image=any(lo<a+n and a<hi for lo,hi,_ in self.image)
            if image:self.emit('ATTEMPTED_IMAGE_WRITE',f'pc={self.pc:x}',f'address={a:x}',f'size={n}',f'hook_value={value & ((1<<(min(n,8)*8))-1):x}','applied=false')
            self.fail('ORIGINAL_IMAGE_WRITE_BLOCKED' if image else 'OUTSIDE_PRIVATE_WRITABLE_REGIONS',a,n);return
        self.writes.append((a,n))
    def _invalid(self,uc,access,a,n,value,user):
        if not self.stop:self.fail('EXTERNAL_OR_NULL_TARGET' if access in (UC_MEM_FETCH_UNMAPPED,UC_MEM_FETCH_PROT) else 'UNMAPPED_OR_PROTECTED_ACCESS',a,n)
        return False
    def check_oracle(self):
        cases={0x174d06f:{'ZF':0,'RSP':SP-128},0x16668ff:{'CF':0,'RCX':1,'R11D':0xd99b4c01},0x16b05fe:{'CF':0},0x171695b:{'RSI':0x1499584},0x14995c7:{'CF':1,'SF':0},0x1603de3:{'SF':0},0x1444517:{'CF':0,'ZF':0}}
        if not self.oracle_enabled or self.pc not in cases or self.pc in self.oracle_seen:return
        self.oracle_seen.add(self.pc)
        for name,expected in cases[self.pc].items():
            value=self.reg(name);self.oracle_checks+=1;self.emit('ORACLE',f'{self.pc:x}',name,f'actual={value:x}',f'expected={expected:x}')
            if value!=expected:self.fail('ORACLE_DISAGREEMENT',self.pc);return
    def allocate(self,n):
        reserve=(max(n,1)+15)&~15
        self.demand(0<=n<=HEAP_SIZE and reserve<=HEAP_SIZE-self.heap_used,'VIRTUAL_HEAP_EXHAUSTED',n)
        a=HEAP+self.heap_used;self.heap_used+=reserve;self.allocations.append((a,n));self.malloc_calls+=1;self.emit('VIRTUAL_MALLOC',f'{a:x}',f'size={n}',f'reserved={reserve}');return a
    def frame(self,push=True):
        sp=self.reg('RSP');self.demand(STACK<=sp and sp+(16 if push else 8)<=STACK+STACK_SIZE,'INVALID_IMPORT_FRAME',sp)
        if push:self.demand(int.from_bytes(self.read_known(sp,8),'little')==0,'UNEXPECTED_IMPORT_SLOT_VALUE',sp)
        target=int.from_bytes(self.read_known(sp+(8 if push else 0),8),'little');self.demand(self.code_allowed(target),'EXTERNAL_OR_NULL_TARGET',target)
        return sp,target
    def ascii(self,a):
        out=bytearray()
        for k in range(256):
            c=self.read_known(a+k,1)[0]
            if c==0:return out.decode('ascii')
            self.demand(c<128,'NON_ASCII_ARGUMENT',a+k);out.append(c)
        self.demand(False,'STRING_ARGUMENT_LIMIT',a)
    def configure_loader(self,scenario):
        if scenario not in ('disabled','unavailable','image-only'):raise ValueError('Unknown loader scenario')
        if self.attempted or self.loader_ready:raise ValueError('Configure loader only once before running')
        self.virtual_loader=scenario
        if scenario=='image-only':
            self.add_image(self.loader_name,b'/virtual/libysm-core.so\0',False);self.uc.mem_protect(self.loader_name,4096,UC_PROT_READ);self.loader_ready=True
    def model(self,kind):
        if kind=='protection-result':
            self.demand(self.protection_result in ('success-input','failure-input'),'UNMODELED_PROTECTION_RESULT')
            sp,target=self.frame(True);address=self.reg('RDI');size=self.reg('RSI');prot=self.reg('RDX')
            self.demand(self.read_known(0x13d84d0,7)==bytes.fromhex('ff35ca534700c3') and self.read_known(0x184d8a0,8)==bytes(8),'PROTECTION_THUNK_MISMATCH')
            self.demand(address%4096==0 and 0<size<=16*1024*1024 and 0<=prot<=7 and all(page in self.pages and page!=self.loader_name for page in range(address,(address+size+4095)&~4095,4096)),'UNMODELED_PROTECTION_REQUEST',address,size)
            result=0 if self.protection_result=='success-input' else 0xffffffff
            self.protection_calls+=1;self.emit('VIRTUAL_PROTECTION_RESULT',self.protection_result,f'address={address:x}',f'size={size:x}',f'prot={prot}',f'result={result:x}','permissions_applied=false','stop_before_original_image_write=true')
            self.reg('RAX',result);self.reg('RSP',sp+16);self.reg('RIP',target);return
        if kind in ('open-unavailable','page-size'):
            pushed=kind=='page-size';sp,target=self.frame(pushed)
            if pushed:
                self.demand(self.read_known(0x13d84c9,7)==bytes.fromhex('ff35c9534700c3') and self.read_known(0x184d898,8)==bytes(8),'PLATFORM_THUNK_MISMATCH')
                self.demand(self.reg('RDI')==30,'UNMODELED_SYSCONF_REQUEST',self.reg('RDI'));result=4096
            else:
                self.demand(self.read_known(0x13d84a7,6)==bytes.fromhex('ff25c3534700') and self.read_known(0x184d870,8)==bytes(8),'PLATFORM_THUNK_MISMATCH')
                self.demand(self.ascii(self.reg('RDI'))=='/virtual/libysm-core.so' and self.reg('RSI')==0,'UNMODELED_FILE_REQUEST');result=0xffffffff
            self.platform_calls+=1;self.emit('VIRTUAL_PLATFORM',kind,f'result={result:x}','host_os_access=false','errno=unmodeled')
            self.reg('RAX',result);self.reg('RSP',sp+(16 if pushed else 8));self.reg('RIP',target);return
        if kind=='dladdr':
            self.demand(self.virtual_loader in ('unavailable','image-only'),'UNMODELED_LOADER_REQUEST')
            sp,target=self.frame(False);query=self.reg('RDI');buf=self.reg('RSI')
            self.demand(self.read_known(0x13d8466,6)==bytes.fromhex('ff25b4534700'),'LOADER_THUNK_MISMATCH')
            self.demand(self.read_known(0x184d820,8)==bytes(8),'UNEXPECTED_IMPORT_SLOT_VALUE')
            result=0
            if self.virtual_loader=='image-only':
                self.demand(self.loader_ready and any(a<=query<b and a!=self.loader_name for a,b,_ in self.image),'QUERY_OUTSIDE_MODELED_IMAGE',query)
                # Explicit counterfactual image-only loader, no symbol claims or host lookup.
                self.demand(self.private_allowed(buf,32),'OUTSIDE_PRIVATE_WRITABLE_REGIONS',buf,32)
                self.write_private(buf,struct.pack('<QQQQ',self.loader_name,0,0,0));result=1
            self.dladdr_calls+=1;self.emit('VIRTUAL_DLADDR',f'scenario={self.virtual_loader}',f'query={query:x}',f'buffer={buf:x}',f'result={result}','host_loader_access=false')
            self.reg('RAX',result);self.reg('RSP',sp+8);self.reg('RIP',target);return

        if kind=='crc':
            from native_crc32_loop_profile_ysm_265 import apply_summary
            apply_summary(self);return
        if kind=='copy':
            self.modeled_copies+=1;n=self.reg('RCX')
            if n==0:self.reg('RIP',self.pc+2);return
            src,dst,df=self.reg('RSI'),self.reg('RDI'),self.reg('DF');self.demand(self.private_allowed(src,1),'COPY_SOURCE_OUTSIDE_PRIVATE',src);self.demand(self.private_allowed(dst,1),'OUTSIDE_PRIVATE_WRITABLE_REGIONS',dst)
            if self.unknown(src,1) is None:self.write_private(dst,self.read_known(src,1))
            else:
                base=self.physical(dst);self.known[base][dst-base]=0;origin=self.opaque.get(src,src);self.opaque[dst]=origin;self.opaque_copies+=1;self.emit('OPAQUE_COPY',f'{src:x}',f'{dst:x}',f'origin={origin:x}');self.log_heap_write(dst,1)
            step=-1 if df else 1;self.reg('RSI',src+step);self.reg('RDI',dst+step);self.reg('RCX',n-1);self.reg('RIP',self.pc);return
        if kind=='clock':
            value=(self.seed+self.clock_reads*self.stride)&MASK;self.emit('VIRTUAL_TSC',self.clock_reads,f'{value:x}');self.clock_reads+=1;self.reg('RAX',value&0xffffffff);self.reg('RDX',value>>32);self.reg('RIP',self.pc+2);return
        sp,target=self.frame(kind!='fclose');result=0
        if kind=='malloc':result=self.allocate(self.reg('RDI'))
        elif kind=='fopen':
            path,mode=self.ascii(self.reg('RDI')),self.ascii(self.reg('RSI'));self.demand(path=='/proc/self/status' and mode=='r','UNMODELED_FILE_REQUEST',self.pc)
            if self.level>=5:self.demand(not self.file_open,'FILE_ALREADY_OPEN');self.file_open=True;self.file_position=0;result=FILE_HANDLE
            self.fopen_calls+=1;self.emit('VIRTUAL_FOPEN',f'result={result:x}','host_file_access=false')
        elif kind=='fgets':
            self.demand(self.file_open and self.reg('RDX')==FILE_HANDLE,'UNKNOWN_FILE_HANDLE');n=self.reg('RSI')&0xffffffff;self.demand(2<=n<=4096,'UNMODELED_FGETS_SIZE',n);buf=self.reg('RDI');pos=self.file_position
            if pos<len(self.fixture):
                end=min(len(self.fixture),pos+n-1);newline=self.fixture.find(b'\n',pos,end)
                if newline>=0:end=newline+1
                data=self.fixture[pos:end]+b'\0';self.write_private(buf,data);self.file_position=end;result=buf
            self.fgets_calls+=1;self.emit('VIRTUAL_FGETS',f'position={self.file_position}',f'eof={result==0}','host_file_access=false')
        elif kind=='fclose':self.demand(self.file_open and self.reg('RDI')==FILE_HANDLE,'UNKNOWN_FILE_HANDLE');self.file_open=False;self.fclose_calls+=1;self.emit('VIRTUAL_FCLOSE','host_file_access=false')
        else:raise ValueError('Unknown model')
        self.reg('RAX',result);self.reg('RSP',sp+(8 if kind=='fclose' else 16));self.reg('RIP',target)
    def rollback(self,context):
        for a,data in reversed(self.journal):self.uc.mem_write(a,data)
        self.uc.context_restore(context);self.rollback_count+=1
    def run(self,entry):
        self.reg('RIP',entry);self.deadline=time.monotonic()+self.seconds;self.timed_out=False
        def timed_out():
            self.timed_out=True;self.uc.emu_stop()
        timer=threading.Timer(self.seconds,timed_out);timer.daemon=True;timer.start()
        try:
            while not self.stop:
                self.pc=self.reg('RIP')
                if self.attempted>=self.limit:self.fail('INSTRUCTION_BUDGET',self.pc);break
                if time.monotonic()>self.deadline:self.fail('TIME_BUDGET',self.pc);break
                if not self.code_allowed(self.pc):self.fail('EXTERNAL_OR_NULL_TARGET',self.pc);break
                context=self.uc.context_save();self.journal=[];self.writes=[];self.pending=None
                try:self.uc.emu_start(self.pc,0,count=1)
                except UcError as e:
                    if not self.stop:self.fail('ENGINE_EXCEPTION:'+str(e),self.pc)
                if not self.stop and self.timed_out:self.fail("ENGINE_TIMEOUT",self.pc)
                if self.stop:self.rollback(context);break
                if self.pending:
                    try:self.model(self.pending)
                    except ModelHalt:break
                else:
                    nxt=self.reg('RIP')
                    if nxt==RETURN and self.reg('RSP')==SP+8:
                        for a,n in self.writes:self.mark_known(a,n);self.log_heap_write(a,n)
                        self.completed+=1;self.fail('ENTRY_RETURN',nxt);break
                    if not self.code_allowed(nxt):self.fail('EXTERNAL_OR_NULL_TARGET',nxt);self.rollback(context);break
                    for a,n in self.writes:self.mark_known(a,n);self.log_heap_write(a,n)
                if not self.stop:self.completed+=1
        finally:
            timer.cancel();timer.join(timeout=1)
        self.emit('COUNTS',f'attempted={self.attempted}',f'completed={self.completed}',f'rollbacks={self.rollback_count}',f'modeled_copy_steps={self.modeled_copies}',f'opaque_byte_copies={self.opaque_copies}',f'virtual_clock_reads={self.clock_reads}',f'virtual_malloc_calls={self.malloc_calls}',f'heap_write_events={self.heap_writes}',f'virtual_fopen_calls={self.fopen_calls}',f'virtual_fgets_calls={self.fgets_calls}',f'virtual_fclose_calls={self.fclose_calls}',f'virtual_protection_result_calls={self.protection_calls}',f'virtual_platform_calls={self.platform_calls}',f'virtual_dladdr_calls={self.dladdr_calls}',f'crc_blocks={self.crc_blocks}',f'crc_iterations={self.crc_iterations}',f'crc_logical_instructions={self.crc_logical_steps}')
        for name in REGS:self.emit('STOP_REGISTER',name,f'{self.reg(name):x}')
        for name in FLAG_BITS:self.emit('STOP_REGISTER',name,f'{self.reg(name):x}')
        preserved=self.image_unchanged();self.emit('PRESERVATION',f'image_unchanged={preserved}')
        if not preserved:raise AssertionError('Original image memory changed')
        self.emit('BOUNDED_RESULT',self.stop['reason'],'target_host_library_execution=false','host_file_access=false','original_image_write_applied=false','transactional_fault_state=true')
        return self.stop

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--mode',choices=MODES,default='strict');p.add_argument('--steps',type=int,default=10000);p.add_argument('--seconds',type=int,default=60);p.add_argument('--seed',default='1122334455667788');p.add_argument('--stride',default='3e8');p.add_argument('--pid',type=int,default=0);p.add_argument('--accelerate-crc',action='store_true');p.add_argument('--protection-result',choices=['disabled','success-input','failure-input'],default='disabled',help='Counterfactual return value only; never changes permissions, stops before image write');p.add_argument('--virtual-platform',action='store_true',help='Explicit page-size 4096 and module-open failure scenario; no errno model');p.add_argument('--virtual-loader',choices=['disabled','unavailable','image-only'],default='disabled');a=p.parse_args()
    if a.pid<0:raise ValueError('Negative fixture PID')
    data=a.image.read_bytes();before=hashlib.sha256(data).hexdigest()
    with a.out.open('w') as out:
        cpu=GuardedCPU(out,a.mode,a.steps,a.seconds,int(a.seed,16),int(a.stride,16),a.pid);cpu.load_image(data);cpu.configure_loader(a.virtual_loader);cpu.virtual_platform=a.virtual_platform;cpu.protection_result=a.protection_result;cpu.accelerate_crc=a.accelerate_crc;cpu.emit('CONFIG','engine=Unicorn2.1.4',f'mode={a.mode}',f'max_steps={a.steps}','imagebase=0','relocations=false','synthetic_registers=true','bss_zero=true');result=cpu.run(0x152eb19)
    if hashlib.sha256(a.image.read_bytes()).hexdigest()!=before:raise AssertionError('Original file changed')
    print(json.dumps({'status':result,'attempted':cpu.attempted,'completed':cpu.completed,'oracles':cpu.oracle_checks,'image_unchanged':True}))
if __name__=='__main__':main()
