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

def standard_table():
    table=[]
    for byte in range(256):
        value=byte
        for _ in range(8):value=(value>>1)^(0xedb88320 if value&1 else 0)
        table.append(value)
    return table

def update_crc(value,data,table):
    value&=0xffffffff
    for byte in data:value=(value>>8)^table[(value^byte)&255]^XOR_MASK
    return value

def profile_matches(cpu):
    for address,expected in CODE.items():
        if cpu.unknown(address,len(expected)) is not None or bytes(cpu.uc.mem_read(address,len(expected)))!=expected:return False
    if cpu.unknown(TABLE,1024) is not None:return False
    raw=bytes(cpu.uc.mem_read(TABLE,1024))
    if hashlib.sha256(raw).hexdigest()!=TABLE_SHA256:return False
    return all(value^XOR_MASK==standard for value,standard in zip(struct.unpack('<256I',raw),standard_table()))

def eligible(cpu):
    from native_unicorn_guarded_ysm_265 import STACK,STACK_SIZE
    n=cpu.reg('RCX');source=cpu.reg('R10');sp=cpu.reg('RSP')
    if cpu.pc!=ENTRY or cpu.reg('R11')!=TABLE or not 2<=n<=MAX_BYTES:return False
    if not STACK<=sp-32 or sp>STACK+STACK_SIZE:return False
    # Immutable original-image input excludes stack overlap, unknown bytes and heap mutations.
    if not any(a<=source and source+n<=b for a,b,_ in cpu.image):return False
    if cpu.crc_profile_verified is None:cpu.crc_profile_verified=profile_matches(cpu)
    return cpu.crc_profile_verified

def apply_summary(cpu):
    from native_unicorn_guarded_ysm_265 import GuardedCPU,REGS,X,ModelHalt
    if not eligible(cpu):raise ValueError('CRC summary preconditions changed')
    n=cpu.reg('RCX');source=cpu.reg('R10');sp=cpu.reg('RSP');initial=cpu.reg('RSI')&0xffffffff
    table_raw=bytes(cpu.uc.mem_read(TABLE,1024));table=struct.unpack('<256I',table_raw)
    # Advance n-2 recurrences locally, then execute one exact full cycle in an isolated CPU.
    # This materializes the final prior iteration's registers, flags and all 32 temporary stack bytes.
    data=cpu.read_known(source,n-2);crc=initial
    for offset in range(0,len(data),65536):
        cpu.demand(time.monotonic()<=cpu.deadline,'TIME_BUDGET',cpu.pc)
        crc=update_crc(crc,data[offset:offset+65536],table)
    ref=GuardedCPU(io.StringIO(),'strict',CYCLE_STEPS,2)
    for address,code in CODE.items():ref.add_image(address,code,True)
    ref.add_image(TABLE,table_raw,False)
    address=source+n-2;ref.add_image(address,cpu.read_known(address,1),False)
    ref.protect_image()
    for name in REGS:ref.reg(name,cpu.reg(name))
    ref.uc.reg_write(X.UC_X86_REG_EFLAGS,cpu.uc.reg_read(X.UC_X86_REG_EFLAGS))
    ref.reg('RSI',crc);ref.reg('R10',address);ref.reg('RCX',2)
    result=ref.run(ENTRY)
    cpu.demand(result['reason']=='INSTRUCTION_BUDGET' and ref.completed==CYCLE_STEPS and ref.reg('RIP')==ENTRY and ref.reg('RSP')==sp and ref.reg('RCX')==1,'CRC_REFERENCE_CYCLE_FAILURE',cpu.pc)
    stack=ref.read_known(sp-32,32)
    cpu.demand(time.monotonic()<=cpu.deadline,'TIME_BUDGET',cpu.pc)
    # All validation precedes the bounded main-state commit.
    cpu.write_private(sp-32,stack,log=False)
    for name in REGS:cpu.reg(name,ref.reg(name))
    cpu.uc.reg_write(X.UC_X86_REG_EFLAGS,ref.uc.reg_read(X.UC_X86_REG_EFLAGS))
    cpu.crc_blocks+=1;cpu.crc_iterations+=n-1;cpu.crc_logical_steps+=(n-1)*CYCLE_STEPS
    cpu.emit('MODELED_CRC32',f'source={source:x}',f'iterations={n-1}',f'logical_instructions={(n-1)*CYCLE_STEPS}',f'initial={initial:x}',f'result={cpu.reg("RSI"):x}',f'input_sha256={hashlib.sha256(cpu.read_known(source,n-1)).hexdigest()}','reference_cycle_steps=28','remaining_iterations=1')
