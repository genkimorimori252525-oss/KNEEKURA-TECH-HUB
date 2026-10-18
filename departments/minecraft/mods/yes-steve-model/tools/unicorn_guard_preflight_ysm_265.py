from unicorn import *
from unicorn.x86_const import *
def cpu(code):
 u=Uc(UC_ARCH_X86,UC_MODE_64);u.mem_map(0x100000,0x1000,UC_PROT_ALL);u.mem_write(0x100000,code);u.mem_protect(0x100000,0x1000,UC_PROT_READ|UC_PROT_EXEC);u.mem_map(0x200000,0x1000);u.reg_write(UC_X86_REG_RBX,0x200000);return u
u=cpu(bytes.fromhex('488903'));u.reg_write(UC_X86_REG_RAX,0x1122334455667788);u.hook_add(UC_HOOK_MEM_WRITE,lambda u,*args:u.emu_stop());u.emu_start(0x100000,0,count=1);print('WRITE_STOP_BYTES',bytes(u.mem_read(0x200000,8)).hex())
u=cpu(bytes.fromhex('488b03'));u.mem_write(0x200000,bytes.fromhex('8877665544332211'));u.reg_write(UC_X86_REG_RAX,0x99);u.hook_add(UC_HOOK_MEM_READ,lambda u,*args:u.emu_stop());u.emu_start(0x100000,0,count=1);print('READ_STOP_RAX',hex(u.reg_read(UC_X86_REG_RAX)))
u=cpu(bytes.fromhex('48ffc0'));u.reg_write(UC_X86_REG_RAX,0x99);u.hook_add(UC_HOOK_CODE,lambda u,*args:u.emu_stop());u.emu_start(0x100000,0,count=1);print('CODE_STOP_RAX',hex(u.reg_read(UC_X86_REG_RAX)))
u=cpu(bytes.fromhex('44870b'));u.reg_write(UC_X86_REG_R9,0xffffffffffffffff);u.emu_start(0x100000,0,count=1);assert u.reg_read(UC_X86_REG_R9)==0;print('XCHG32_OK')
u=cpu(bytes.fromhex('41c0eae1'));u.reg_write(UC_X86_REG_R10,0xde);u.reg_write(UC_X86_REG_EFLAGS,0x202);u.emu_start(0x100000,0,count=1);assert u.reg_read(UC_X86_REG_R10)==0x6f and u.reg_read(UC_X86_REG_EFLAGS)&0x800;print('SHR_FLAGS_OK')
print('UNICORN_VERSION',uc_version())
