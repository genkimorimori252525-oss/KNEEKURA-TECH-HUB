"""Bounded malloc/free aliases over private modeled storage; no host allocator calls."""
from native_unicorn_guarded_ysm_265 import HEAP
IMPORTS={119:('free',0x184d3d0,0x1428357),120:('malloc',0x184d3d8,0x15499d5),206:('_ZdlPv',0x184d688,0x13f415e),212:('malloc',0x184d6b8,0x14bcaa6),218:('free',0x184d6e8,0x14ea479),242:('_ZdaPv',0x184d7a8,0x1560882)}
SYMBOLS={x[0] for x in IMPORTS.values()}

def model(cpu,symbol):
    address=cpu.reg('RDI')
    if symbol=='malloc':return cpu.allocate(address)
    if symbol not in ('free','_ZdlPv','_ZdaPv'):raise ValueError('Unknown heap model')
    if address:
        allocation=next(((i,n) for i,(a,n) in enumerate(cpu.allocations) if a==address),None)
        cpu.demand(allocation is not None,'UNKNOWN_FREE_POINTER',address)
        i,n=allocation;cpu.demand(not any(lo<=address<hi for lo,hi in cpu.private_readonly),'READONLY_FIXTURE_FREE',address)
        cpu.allocations.pop(i);cpu.known[HEAP][address-HEAP:address-HEAP+n]=bytes(n)
        for at in range(address,address+n):cpu.opaque.pop(at,None)
    cpu.heap_free_calls+=1;cpu.emit('VIRTUAL_FREE',symbol,f'address={address:x}','host_allocator_called=false','storage_reuse=false');return cpu.reg('RAX')
