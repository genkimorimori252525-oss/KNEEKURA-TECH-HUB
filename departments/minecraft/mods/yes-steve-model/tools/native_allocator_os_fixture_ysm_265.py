"""Declared allocator OS inputs; no actual file/entropy/process/memory-management calls."""
import hashlib,struct
IMPORTS={65:('__xstat',0x184d220,0x1558b41),49:('readlink',0x184d1a0,0x13fc23e),64:('clock_gettime',0x184d218,0x14cb9e8),23:('__errno_location',0x184d0d0,0x142bc04),108:('open',0x184d378,0x151a7bf),109:('read',0x184d380,0x151d279),110:('close',0x184d388,0x1572ee3),111:('prctl',0x184d390,0x141567e),112:('mmap',0x184d398,0x184340d),113:('madvise',0x184d3a0,0x15ad6f2),195:('mprotect',0x184d630,0x1400fc3),199:('close',0x184d650,0x1841d95),243:('munmap',0x184d7b0,0x1607b55),253:('open',0x184d800,0x1550b76),254:('mmap',0x184d808,0x16159c9)}
SYMBOLS={x[0] for x in IMPORTS.values()};FD=7

def entropy(seed,start,n):
    out=b'';block=start//32
    while len(out)<(start%32)+n:out+=hashlib.sha256(seed.encode()+block.to_bytes(8,'little')).digest();block+=1
    return out[start%32:start%32+n]
def model(cpu,symbol):
    cpu.demand(hasattr(cpu,'vm_map'),'SPARSE_BACKEND_REQUIRED');s=cpu.os_fixture;cpu.demand(s['calls']<cpu.MAX_VM_EVENTS,'ALLOCATOR_OS_CALL_BUDGET')
    if symbol=='__xstat':
        path=cpu.ascii(cpu.reg('RSI'));cpu.demand(cpu.reg('RDI')==1 and path in (s['exe_path'],'/virtual/jdk/lib/server/libjvm.so'),'UNMODELED_STAT_PATH_OR_ABI');data=bytearray(144)
        struct.pack_into('<QQQIII',data,0,1,1,1,0o100755 if path==s['exe_path'] else 0o100644,1000,1000);struct.pack_into('<q',data,56,4096)
        artifact=getattr(cpu,'jni_state',None) or {}
        if path=='/virtual/jdk/lib/server/libjvm.so' and artifact.get('jvm_artifact'):
            cpu.demand(getattr(cpu,'jvm_artifact_bytes',None) is not None,'JVM_ARTIFACT_BYTES_REQUIRED');file_size=artifact['jvm_artifact']['size'];struct.pack_into('<q',data,48,file_size);struct.pack_into('<q',data,64,(file_size+511)//512)
        cpu.write_model_memory(cpu.reg('RDX'),bytes(data));result=0;cpu.emit('VIRTUAL_EXECUTABLE_STAT','linux_x86_64_stat_v1',f'path={path}','regular_file=true',f'file_size={struct.unpack_from("<q",data,48)[0]}','timestamps=0','explicit_scenario_input=true','host_stat=false')
    elif symbol=='readlink':
        cpu.demand(cpu.ascii(cpu.reg('RDI'))=='/proc/self/exe' and 0<cpu.reg('RDX')<=4096,'UNMODELED_READLINK');data=s['exe_path'].encode('ascii')[:cpu.reg('RDX')];cpu.write_model_memory(cpu.reg('RSI'),data);result=len(data);s['readlink_calls']+=1;cpu.emit('VIRTUAL_EXECUTABLE_PATH',s['exe_path'],'explicit_scenario_input=true','host_proc_read=false')
    elif symbol=='clock_gettime':
        cpu.demand(cpu.reg('RDI')==1,'UNMODELED_CLOCK_ID');value=s['monotonic_ns'];cpu.write_model_memory(cpu.reg('RSI'),struct.pack('<qq',value//1000000000,value%1000000000));s['monotonic_ns']+=1000000;s['clock_calls']+=1;result=0;cpu.emit('VIRTUAL_MONOTONIC_CLOCK',f'nanoseconds={value}','origin=0','stride_ns=1000000','host_clock_read=false')
    elif symbol=='__errno_location':
        if not s['errno_block']:
            a=cpu.reserve_fixture(16);cpu.write_private(a,struct.pack('<i',s['errno_input']));s['errno_block']=a;cpu.emit('VIRTUAL_ERRNO_INPUT',f'value={s["errno_input"]}','explicit_scenario_input=true','host_errno_access=false')
        result=s['errno_block']
    elif symbol=='open':
        path=cpu.ascii(cpu.reg('RDI'));cpu.demand(path=='/dev/urandom' and cpu.reg('RSI') in (0,0x80000) and not s['entropy_open'],'UNMODELED_ALLOCATOR_FILE_REQUEST');s['entropy_open']=True;result=FD
    elif symbol=='read':
        n=cpu.reg('RDX');cpu.demand(s['entropy_open'] and cpu.reg('RDI')==FD and n<=4096 and s['entropy_offset']+n<=4096,'UNMODELED_ENTROPY_READ');data=entropy(s['entropy_seed'],s['entropy_offset'],n)
        if n:cpu.write_model_memory(cpu.reg('RSI'),data)
        s['entropy_offset']+=n;result=n
    elif symbol=='close':cpu.demand(s['entropy_open'] and cpu.reg('RDI')==FD,'UNKNOWN_VIRTUAL_FD');s['entropy_open']=False;result=0
    elif symbol=='mmap':
        cpu.demand(cpu.reg('RDI')==0 and cpu.reg('RCX') in (0x22,0x4022) and cpu.reg('R8')&0xffffffff==0xffffffff and cpu.reg('R9')==0,'UNMODELED_MMAP_REQUEST');result=cpu.vm_map(cpu.reg('RSI'),cpu.reg('RDX'))
    elif symbol=='prctl':
        a,n=cpu.reg('RDX'),cpu.reg('RCX');cpu.demand(cpu.reg('RDI')==0x53564d41 and cpu.reg('RSI')==0 and cpu.vm_cover(a,n) is not None and cpu.ascii(cpu.reg('R8'))=='snmalloc','UNMODELED_PRCTL_REQUEST');cpu.demand(len(s['names'])<4096,'VMA_NAME_BUDGET');s['names'].append([a,n,'snmalloc']);result=0
    elif symbol=='madvise':cpu.vm_advice(cpu.reg('RDI'),cpu.reg('RSI'),cpu.reg('RDX'));result=0
    elif symbol=='munmap':cpu.vm_change(cpu.reg('RDI'),cpu.reg('RSI'),remove=True);result=0
    elif symbol=='mprotect':
        if cpu.vm_overlap(cpu.reg('RDI'),cpu.reg('RSI')):cpu.vm_change(cpu.reg('RDI'),cpu.reg('RSI'),cpu.reg('RDX'))
        else:cpu.grant_shadow_range(cpu.reg('RDI'),cpu.reg('RSI'),cpu.reg('RDX'))
        result=0
    else:raise ValueError('Unknown allocator OS model')
    s['calls']+=1;cpu.emit('VIRTUAL_ALLOCATOR_OS',symbol,f'result={result:x}','host_os_called=false','host_entropy_read=false');return result
