"""Narrow GNU C-locale fixture from public API/layout contracts; no host locale access.

Private __locales fields remain unknown. Only exposed ctype/name fields are modeled.
The fixture is read-only and reserved from the existing1MiB private-memory budget.
"""
import struct
MASK=(1<<64)-1
IMPORTS={182:('strerror_r',0x184d5c8,0x14a048b),54:('tolower',0x184d1c8,0x149286e),133:('__newlocale',0x184d440,0x14317d7),134:('__freelocale',0x184d448,0x153d476),135:('__duplocale',0x184d450,0x14f696d),143:('__uselocale',0x184d490,0x162872d),148:('__ctype_get_mb_cur_max',0x184d4b8,0x14ae489),159:('__wctype_l',0x184d510,0x14317e1),162:('__iswctype_l',0x184d528,0x141e7ae),163:('wctob',0x184d530,0x1619a68),164:('btowc',0x184d538,0x1411a32)}
SYMBOLS={x[0] for x in IMPORTS.values()}
CLASSES=('upper','lower','alpha','digit','xdigit','space','print','graph','blank','cntrl','punct','alnum')
DESC=0x760000000000

def properties(c):
    upper=65<=c<=90;lower=97<=c<=122;digit=48<=c<=57;alpha=upper or lower;graph=33<=c<=126
    return (upper,lower,alpha,digit,digit or 65<=c<=70 or 97<=c<=102,c in (9,10,11,12,13,32),32<=c<=126,graph,c in (9,32),0<=c<=31 or c==127,graph and not(alpha or digit),alpha or digit)
def classification(c):
    bits=properties(c)
    return sum(((1<<i)<<8 if i<8 else (1<<i)>>8) for i,v in enumerate(bits) if v)
def convert(c,upper):
    if c==-1:return -1
    if c<0:return c+256
    if upper and 97<=c<=122:return c-32
    if not upper and 65<=c<=90:return c+32
    return c

def ensure_c_locale(cpu):
    if cpu.c_locale_handle:return cpu.c_locale_handle
    base=cpu.reserve_fixture(0x2000);b=base+0x100;lower=base+0x400;upper=base+0xa00;name=base+0x1000
    cpu.write_private(b,struct.pack('<384H',*(classification(i) for i in range(-128,256))))
    cpu.write_private(lower,struct.pack('<384i',*(convert(i,False) for i in range(-128,256))))
    cpu.write_private(upper,struct.pack('<384i',*(convert(i,True) for i in range(-128,256))))
    cpu.write_private(name,b'C\0');cpu.write_private(base+104,struct.pack('<QQQ',b+256,lower+512,upper+512))
    for i in range(13):
        if i!=6:cpu.write_private(base+128+i*8,struct.pack('<Q',name))
    # __locales[13] and the invalid LC_ALL name slot intentionally stay unknown.
    cpu.private_readonly.append((base,base+0x2000));cpu.c_locale_handle=base
    cpu.emit('VIRTUAL_C_LOCALE',f'handle={base:x}','ctype_layout=gnu-64bit','private_locale_fields=unknown','fixture_readonly=true','host_locale_access=false')
    return base

def require_c(cpu,handle):cpu.demand(cpu.c_locale_handle!=0 and handle==cpu.c_locale_handle,'UNKNOWN_C_LOCALE_HANDLE',handle)
def model(cpu,symbol):
    if symbol=='strerror_r':
        # GNU ABI: known error returns a stable readonly literal, ignores buf/len.
        # glibc string/_strerror.c and sysdeps/gnu/errlist.h, C-locale EPERM.
        cpu.demand(cpu.reg('RDI')&0xffffffff==1,'UNMODELED_STRERROR_NUMBER')
        cpu.demand(cpu.thread_locale in (MASK,cpu.c_locale_handle),'UNMODELED_STRERROR_LOCALE')
        text=b'Operation not permitted\0'
        if not cpu.strerror_eperm:
            address=cpu.reserve_fixture(len(text));cpu.write_private(address,text);cpu.private_readonly.append((address,address+len(text)));cpu.strerror_eperm=address
        result=cpu.strerror_eperm
    elif symbol=='tolower':
        c=cpu.reg('RDI')&0xffffffff;cpu.demand(c<=255 or c==0xffffffff,'UNDEFINED_TOLOWER_INPUT',c);result=convert(-1 if c==0xffffffff else c,False)&0xffffffff
    elif symbol=='__newlocale':
        mask=cpu.reg('RDI')&0xffffffff;name=cpu.ascii(cpu.reg('RSI'));base=cpu.reg('RDX')
        cpu.demand(name=='C' and (mask==64 or mask&~0x1fbf==0) and (base==0 or (cpu.c_locale_handle and base==cpu.c_locale_handle)),'UNMODELED_LOCALE_REQUEST')
        result=ensure_c_locale(cpu)
    elif symbol in ('__duplocale','__freelocale'):
        require_c(cpu,cpu.reg('RDI'));result=cpu.c_locale_handle if symbol=='__duplocale' else cpu.reg('RAX')
    elif symbol=='__uselocale':
        value=cpu.reg('RDI');cpu.demand(value in (0,MASK) or (cpu.c_locale_handle and value==cpu.c_locale_handle),'UNKNOWN_C_LOCALE_HANDLE',value);result=cpu.thread_locale
        if value:cpu.thread_locale=value
    elif symbol=='__ctype_get_mb_cur_max':result=1
    elif symbol=='__wctype_l':
        require_c(cpu,cpu.reg('RSI'));name=cpu.ascii(cpu.reg('RDI'));result=DESC+CLASSES.index(name)+1 if name in CLASSES else 0
    elif symbol=='__iswctype_l':
        require_c(cpu,cpu.reg('RDX'));index=cpu.reg('RSI')-DESC-1;cpu.demand(0<=index<len(CLASSES),'UNKNOWN_WCTYPE_DESCRIPTOR',cpu.reg('RSI'));result=int(properties(cpu.reg('RDI')&0xffffffff)[index])
    elif symbol=='wctob':
        c=cpu.reg('RDI')&0xffffffff;result=c if c<128 else 0xffffffff
    elif symbol=='btowc':
        c=cpu.reg('RDI')&0xffffffff;cpu.demand(c<=255 or c==0xffffffff,'UNMODELED_BTOWC_RANGE',c);result=c if c<128 else 0xffffffff
    else:raise ValueError('Unknown C-locale model')
    cpu.locale_model_calls+=1;cpu.emit('VIRTUAL_C_LOCALE_CALL',symbol,f'result={result:x}','host_locale_access=false');return result
