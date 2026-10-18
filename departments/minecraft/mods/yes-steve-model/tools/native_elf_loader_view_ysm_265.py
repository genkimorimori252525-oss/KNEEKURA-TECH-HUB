"""Deterministic symbol-zero ELF RELATIVE fixups for the isolated working image only."""
import hashlib,struct
from native_simulation_copy_frontier_ysm_265 import IMAGE_SHA
MASK=(1<<64)-1
from native_export_backing_ysm_265 import regions,data_at
from native_image_metadata_ysm_265 import header
from native_initializer_inventory_ysm_265 import dynamic_records,rela_records,array_targets

def manifest(data):
    if hashlib.sha256(data).hexdigest()!=IMAGE_SHA:raise ValueError('Wrong ELF artifact')
    h=header(data);rs=regions(data);ph=[struct.unpack_from('<IIQQQQQQ',data,h['program_header_offset']+i*56) for i in range(h['program_header_count'])];dynamic=[p for p in ph if p[0]==2]
    if len(dynamic)!=1:raise ValueError('Missing unique dynamic segment')
    p=dynamic[0];records=dynamic_records(data[p[2]:p[2]+p[5]])
    def one(tag):
        values=[v for t,v in records if t==tag]
        if len(values)!=1:raise ValueError('Missing/duplicate dynamic tag')
        return values[0]
    if one(9)!=24 or one(20)!=7:raise ValueError('Unexpected relocation layout')
    rels=rela_records(data_at(data,rs,one(7),one(8)));plt=rela_records(data_at(data,rs,one(23),one(2)));fixups=[];unresolved=[]
    for address,info,addend in rels+plt:
        if info==8:
            if not any(r['address']<=address and address+8<=r['address']+r['memory_size'] and r['flags']&2 for r in rs):raise ValueError('RELATIVE destination outside writable ELF segment')
            fixups.append((address,addend&MASK))
        else:unresolved.append((address,info,addend))
    external_data=[];strings=data_at(data,rs,one(5),one(10))
    for address,info,addend in unresolved:
        symbol=info>>32;name,kind,other,section,value,size=struct.unpack('<IBBHQQ',data_at(data,rs,one(6)+symbol*24,24))
        symbol_name=strings[name:].split(b'\0')[0].decode('ascii')
        if section==0 and (kind&15 in (1,6) or symbol_name in ('JNI_GetCreatedJavaVMs','JNI_CreateJavaVM','JNI_GetDefaultJavaVMInitArgs')):external_data.append([address,symbol_name])
    init=array_targets(one(25),data_at(data,rs,one(25),one(27)),rels+plt)
    if len(fixups)!=8812 or len(init)!=45 or one(12)!=0x152eb19:raise ValueError('Pinned initializer inventory changed')
    tls_headers=[p for p in ph if p[0]==7]
    if len(tls_headers)!=1:raise ValueError('Missing unique TLS template')
    t=tls_headers[0];tls={'address':t[3],'file_size':t[5],'memory_size':t[6],'alignment':t[7],'descriptors':[[a,int.from_bytes(data_at(data,rs,a+8,8),'little')] for a,i,v in unresolved if i==16 and v==0]}
    if (tls['file_size'],tls['memory_size'],tls['alignment'])!=(216,15408,16) or len(tls['descriptors'])!=3:raise ValueError('Pinned TLS contract changed')
    writable=[(r['address']&~4095,r['address']+r['memory_size']-(r['address']&~4095),((r['flags']&4)>>2)|(r['flags']&2)|((r['flags']&1)<<2)) for r in rs if r['flags']&2]
    return {'dt_init':one(12),'initializers':[e['relative_target'] for e in init],'init_slots':[e['slot'] for e in init],'fixups':fixups,'writable':writable,'unresolved':unresolved,'external_data_slots':external_data,'tls':tls}

def apply_fixups(cpu,writable,fixups):
    if cpu.attempted or cpu.shadow_events or cpu.loader_view_applied:raise ValueError('Loader view must precede all target execution and image stores')
    if len(fixups)>10000 or len({a for a,v in fixups})!=len(fixups):raise ValueError('Invalid fixup count or duplicate destination')
    for a,v in fixups:
        if cpu.shadow_region(a,8) is None or not any(lo<=a and a+8<=lo+n and prot&2 for lo,n,prot in writable) or not 0<=v<=MASK:raise ValueError('Invalid deterministic loader fixup')
    for a,n,prot in writable:cpu.grant_shadow_range(a,n,prot)
    cpu.pc=0
    for a,v in fixups:
        cpu.uc.mem_write(a,struct.pack('<Q',v));cpu.commit_write(a,8)
    cpu.loader_relocation_events=len(fixups);cpu.loader_view_applied=True
    cpu.emit('LOADER_RELATIVE_VIEW',f'events={len(fixups)}',f'bytes={8*len(fixups)}','analysis_base=0','external_symbols_unresolved=true','host_loader_called=false','reference_file_unchanged=true')
    if not cpu.expected_image_matches():raise AssertionError('Loader working image disagrees with ledger')

def apply_loader_view(cpu,data):
    m=manifest(data);apply_fixups(cpu,m['writable'],m['fixups']);cpu.external_data_slots=m['external_data_slots'];cpu.external_data_guard_applied=True;return m
