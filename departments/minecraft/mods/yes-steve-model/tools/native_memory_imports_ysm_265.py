"""Bounded byte-level C memory/string import models, no host libc invocation."""
IMPORTS={7:('strlen',0x184d050,0x145cdc4),9:('memcmp',0x184d060,0x18496d6),78:('strcmp',0x184d288,0x15c47e1),128:('strncmp',0x184d418,0x15bd0f5),198:('memcpy',0x184d648,0x1845005),211:('strncmp',0x184d6b0,0x15e6473),219:('strlen',0x184d6f0,0x15cae7e)}
SYMBOLS={x[0] for x in IMPORTS.values()}
MAX_BYTES=0x100000
MAX_STRING=0x10000

def model(cpu,symbol):
    a,b,n=cpu.reg('RDI'),cpu.reg('RSI'),cpu.reg('RDX')
    if symbol in ('memcmp','memcpy','strncmp'):cpu.demand(n<=MAX_BYTES,'MEMORY_MODEL_SIZE_LIMIT',n)
    if symbol=='memcpy':
        cpu.demand(n==0 or not(a<b+n and b<a+n),'UNDEFINED_MEMCPY_OVERLAP',a,n)
        data=cpu.read_known(b,n) if n else b''
        if n:cpu.write_model_memory(a,data)
        result=a
    elif symbol=='memcmp':
        left=cpu.read_known(a,n) if n else b'';right=cpu.read_known(b,n) if n else b'';result=next((x-y for x,y in zip(left,right) if x!=y),0)&0xffffffff
    elif symbol=='strlen':
        result=None
        for i in range(MAX_STRING):
            if cpu.read_known(a+i,1)==b'\0':result=i;break
        cpu.demand(result is not None,'STRING_MODEL_LIMIT',a)
    elif symbol in ('strcmp','strncmp'):
        result=0;limit=n if symbol=='strncmp' else MAX_STRING;terminated=False
        for i in range(limit):
            left=cpu.read_known(a+i,1)[0];right=cpu.read_known(b+i,1)[0]
            if left!=right:result=(left-right)&0xffffffff;terminated=True;break
            if left==0:terminated=True;break
        cpu.demand(symbol=='strncmp' or terminated,'STRING_MODEL_LIMIT',a)
    else:raise ValueError('Unknown memory model')
    cpu.memory_model_calls+=1;cpu.emit('VIRTUAL_MEMORY_IMPORT',symbol,f'result={result:x}','host_libc_called=false');return result
