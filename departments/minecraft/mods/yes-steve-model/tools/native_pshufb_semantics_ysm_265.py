"""Legacy register PSHUFB correction for pinned Unicorn2.1.4.

The upstream helper fills16 bytes of an uninitialized64-byte ZMMReg then copies
all64 bytes. Model the specified128-bit permutation and preserve upper384 bits.
Memory and nonlegacy encodings are deliberately outside this model.
"""
from unicorn import x86_const as X
MASK128=(1<<128)-1

def decode(raw):
    if not raw.startswith(b'\x66'):return None
    pos=1;rex=0
    if pos<len(raw) and 0x40<=raw[pos]<=0x4f:rex=raw[pos];pos+=1
    if raw[pos:pos+3]!=b'\x0f\x38\x00':return None
    if len(raw)!=pos+4 or raw[-1]>>6!=3:return 'unsupported-memory'
    modrm=raw[-1];return ((modrm>>3)&7)+((rex&4)<<1),(modrm&7)+((rex&1)<<3)

def apply(cpu):
    registers=decode(cpu.current_raw)
    cpu.demand(isinstance(registers,tuple),'UNMODELED_LEGACY_PSHUFB_ENCODING')
    dst,src=registers;dr=getattr(X,'UC_X86_REG_ZMM'+str(dst));sr=getattr(X,'UC_X86_REG_ZMM'+str(src))
    old=cpu.uc.reg_read(dr);control=(cpu.uc.reg_read(sr)&MASK128).to_bytes(16,'little');source=(old&MASK128).to_bytes(16,'little')
    result=bytes(0 if x&0x80 else source[x&15] for x in control)
    cpu.uc.reg_write(dr,(old&~MASK128)|int.from_bytes(result,'little'));cpu.reg('RIP',cpu.pc+len(cpu.current_raw));cpu.pshufb_model_calls+=1
    cpu.emit('MODELED_LEGACY_PSHUFB',f'destination=zmm{dst}',f'control=xmm{src}','upper384_preserved=true','flags_preserved=true','host_target_execution=false')
