import struct
"""Opaque already-loaded JVM handle in the virtual scenario, never dlopen on host."""
IMPORTS={3:('dladdr',0x184d030,0x14cd2b5),2:('dlsym',0x184d028,0x148d264),4:('dlopen',0x184d038,0x14fa167),5:('dlerror',0x184d040,0x155a14c)}
SYMBOLS={v[0] for v in IMPORTS.values()};HANDLE=0x7a0000000000

def model(cpu,symbol):
    s=getattr(cpu,'jni_state',None);cpu.demand(s is not None and s['jvm_artifact'] is not None and cpu.jvm_artifact_bytes is not None,'JVM_ARTIFACT_SCENARIO_REQUIRED');cpu.demand(s['jvm_loader_calls']<1024,'JVM_LOADER_BUDGET')
    if symbol=='dlopen':
        path=cpu.ascii(cpu.reg('RDI'));flags=cpu.reg('RSI');cpu.demand(path==s['jvm_artifact']['virtual_path'] and flags==5,'UNMODELED_JVM_DLOPEN');s['jvm_open_refs']+=1;result=HANDLE;cpu.emit('VIRTUAL_JVM_DLOPEN',path,'flags=RTLD_LAZY|RTLD_NOLOAD','already_loaded_jvm=declared','host_dlopen_called=false')
    elif symbol=='dlsym':
        name=cpu.ascii(cpu.reg('RSI'));cpu.demand(cpu.reg('RDI')==HANDLE and s['jvm_open_refs']>0,'UNKNOWN_JVM_HANDLE');cpu.emit('JVM_SYMBOL_FRONTIER',name)
        try:record=cpu.jvm_view.symbol(name)
        except ValueError:cpu.demand(False,'UNMODELED_JVM_SYMBOL')
        result=record['address'];cpu.emit('ARTIFACT_JVM_SYMBOL',name,f'address={result:x}',f"kind={record['kind']}",f"size={record['size']}",'source=exact-JVM-ELF-dynsym','host_dlsym=false','jvm_function_execution=false')
    elif symbol=='dladdr':
        from native_jvm_artifact_view_ysm_265 import BASE
        address=cpu.reg('RDI');cpu.demand(cpu.jvm_view.hit(address,1),'UNMODELED_DLADDR_MODULE',address)
        if not s['jvm_name']:
            data=s['jvm_artifact']['virtual_path'].encode()+b'\0';p=cpu.reserve_fixture(len(data));cpu.write_private(p,data);cpu.private_readonly.append((p,p+len(data)));s['jvm_name']=p
        record=cpu.jvm_view.dynamic_symbol_containing(address);name_address=record.get('name_address',0) if record else 0;symbol_address=record['address'] if record and name_address else 0
        cpu.write_model_memory(cpu.reg('RSI'),struct.pack('<QQQQ',s['jvm_name'],BASE,name_address,symbol_address));result=1;cpu.emit('ARTIFACT_JVM_DLADDR',f'address={address:x}',f'base={BASE:x}','host_dladdr=false','local_nonexported_symbols_not_fabricated=true')
    elif symbol=='dlerror':result=0
    else:raise ValueError('Unknown virtual JVM loader import')
    s['jvm_loader_calls']+=1;return result
