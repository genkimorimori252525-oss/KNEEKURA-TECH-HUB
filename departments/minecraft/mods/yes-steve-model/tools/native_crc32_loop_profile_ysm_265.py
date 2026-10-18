"""Pinned masked-CRC32 loop contract; optional verified state summary, no host target execution."""
import hashlib, io, struct, time
ENTRY=0x15f0d5e
EXIT=0x14728bf
TABLE=0x170ec60
XOR_MASK=0xa30cc68d
CYCLE_STEPS=28
MAX_BYTES=16*1024*1024
CODE={
    0x15f0d5e:bytes.fromhex('410fb61a689e1620b533dec16c240095682e528ca366c17c240a4f81e3ff000000c06c240424418b1c9bff442403c07c24082366814c240d0b6ac1ee0866c16c240be8c14c240a24e872490e00'),
    0x16d571d:bytes.fromhex('33f348c7442400971d949566f754240e49ffc281f68dc60ca3689b67811448c14424033548ffc9e921f90a00'),
    0x178506a:bytes.fromhex('e945d8ceff'),
    0x14728b4:bytes.fromhex('488d6424200f859fe41700'),
}
TABLE_SHA256='f72cea55089d04d0d4c0c04673f3c7d0f1445de390efb8a0673a9a09674d4465'

P1=dict(entry=ENTRY,exit=EXIT,table=TABLE,mask=XOR_MASK,steps=CYCLE_STEPS,code=CODE,table_sha=TABLE_SHA256,source_reg='R10',table_reg='R11',crc_reg='RSI',scratch=32)
P2=dict(entry=0x1503f30,exit=0x14e880b,table=0x16c0498,mask=0x3f168d01,steps=21,table_sha='312e6056bd022a9fb7552251010a6eddd97dfb65455f3101b8b77c2d16f86db2',source_reg='RAX',table_reg='RDX',crc_reg='RDI',scratch=24,code={
0x1503f30:bytes.fromhex('440fb618e8f24f2d00'),
0x17d8f2b:bytes.fromhex('e9722ed9ff'),
0x156bda2:bytes.fromhex('48c744240018f618bf4433df4181e3ff000000468b1c9ae8136e1400'),
0x16b2bd1:bytes.fromhex('e950e7efff'),
0x15b1326:bytes.fromhex('c1ef084133fbe9a674f3ff'),
0x14e87d7:bytes.fromhex('688d613d4848ffc066816c2401b43048c7442408b3d590a381f7018d163f81642405af3183ba48ffc9488d6424180f8525b70100'),
})
from native_crc32_jni_profiles_ysm_265 import JNI_PROFILES
PROFILES={p['entry']:p for p in (P1,P2)+JNI_PROFILES}

def standard_table():
    table=[]
    for byte in range(256):
        value=byte
        for _ in range(8):value=(value>>1)^(0xedb88320 if value&1 else 0)
        table.append(value)
    return table

def update_crc(value,data,table,mask=XOR_MASK):
    value&=0xffffffff
    for byte in data:value=(value>>8)^table[(value^byte)&255]^mask
    return value

def profile_matches(cpu,p=P1):
    for address,expected in p['code'].items():
        if cpu.unknown(address,len(expected)) is not None or bytes(cpu.uc.mem_read(address,len(expected)))!=expected:return False
    if cpu.unknown(p['table'],1024) is not None:return False
    raw=bytes(cpu.uc.mem_read(p['table'],1024))
    if hashlib.sha256(raw).hexdigest()!=p['table_sha']:return False
    return all(value^p['mask']==standard for value,standard in zip(struct.unpack('<256I',raw),standard_table()))

def eligible(cpu):
    from native_unicorn_guarded_ysm_265 import STACK,STACK_SIZE
    # Deterministic pre-execution loader fixups form a fixed input view. No summary after runtime image stores.
    p=PROFILES.get(cpu.pc)
    if p is None:return False
    if getattr(cpu,'shadow_events',0)>getattr(cpu,'loader_relocation_events',0)+getattr(cpu,'external_binding_events',0) and not p.get('working_image_safe'):return False
    n=cpu.reg(p.get('counter_reg','RCX'));source=cpu.reg(p['source_reg']);sp=cpu.reg('RSP')
    if cpu.reg(p['table_reg'])!=p['table'] or not 2<=n<=MAX_BYTES:return False
    if not STACK<=sp-p['scratch'] or sp>STACK+STACK_SIZE:return False
    region=next(((a,b,v) for a,b,v in cpu.image if a<=source and source+n<=b),None)
    if region is None:return False
    if p.get('working_image_safe'):
        a,b,original=region
        if cpu.unknown(source,n) is not None or bytes(cpu.uc.mem_read(source,n))!=original[source-a:source-a+n]:return False
    if cpu.crc_profile_verified is None:cpu.crc_profile_verified={}
    if cpu.pc not in cpu.crc_profile_verified:cpu.crc_profile_verified[cpu.pc]=profile_matches(cpu,p)
    return cpu.crc_profile_verified[cpu.pc]

def apply_summary(cpu):
    from native_unicorn_guarded_ysm_265 import GuardedCPU,REGS,X,ModelHalt
    if not eligible(cpu):raise ValueError('CRC summary preconditions changed')
    p=PROFILES[cpu.pc];steps=p['steps'];scratch=p['scratch']
    counter=p.get('counter_reg','RCX');n=cpu.reg(counter);source=cpu.reg(p['source_reg']);sp=cpu.reg('RSP');initial=cpu.reg(p['crc_reg'])&0xffffffff
    table_raw=bytes(cpu.uc.mem_read(p['table'],1024));table=struct.unpack('<256I',table_raw)
    # Advance n-2 recurrences locally, then execute one exact full cycle in an isolated CPU.
    # This materializes the final prior iteration's registers, flags and all profile-specific temporary stack bytes.
    data=cpu.read_known(source,n-2);crc=initial
    for offset in range(0,len(data),65536):
        cpu.demand(time.monotonic()<=cpu.deadline,'TIME_BUDGET',cpu.pc)
        crc=update_crc(crc,data[offset:offset+65536],table,p['mask'])
    ref=GuardedCPU(io.StringIO(),'strict',steps,2)
    for address,code in p['code'].items():ref.add_image(address,code,True)
    ref.add_image(p['table'],table_raw,False)
    address=source+n-2;ref.add_image(address,cpu.read_known(address,1),False)
    ref.protect_image()
    for name in REGS:ref.reg(name,cpu.reg(name))
    ref.uc.reg_write(X.UC_X86_REG_EFLAGS,cpu.uc.reg_read(X.UC_X86_REG_EFLAGS))
    ref.reg(p['crc_reg'],crc);ref.reg(p['source_reg'],address);ref.reg(counter,2)
    result=ref.run(p['entry'])
    cpu.demand(result['reason']=='INSTRUCTION_BUDGET' and ref.completed==steps and ref.reg('RIP')==p['entry'] and ref.reg('RSP')==sp and ref.reg(counter)==1,'CRC_REFERENCE_CYCLE_FAILURE',cpu.pc)
    stack=ref.read_known(sp-scratch,scratch)
    cpu.demand(time.monotonic()<=cpu.deadline,'TIME_BUDGET',cpu.pc)
    # All validation precedes the bounded main-state commit.
    cpu.write_private(sp-scratch,stack,log=False)
    for name in REGS:cpu.reg(name,ref.reg(name))
    cpu.uc.reg_write(X.UC_X86_REG_EFLAGS,ref.uc.reg_read(X.UC_X86_REG_EFLAGS))
    cpu.crc_blocks+=1;cpu.crc_iterations+=n-1;cpu.crc_logical_steps+=(n-1)*steps
    cpu.emit('MODELED_CRC32',f"profile_entry={p['entry']:x}",f'source={source:x}',f'iterations={n-1}',f'logical_instructions={(n-1)*steps}',f'initial={initial:x}',f"result={cpu.reg(p['crc_reg']):x}",f'input_sha256={hashlib.sha256(cpu.read_known(source,n-1)).hexdigest()}',f'reference_cycle_steps={steps}','remaining_iterations=1')
