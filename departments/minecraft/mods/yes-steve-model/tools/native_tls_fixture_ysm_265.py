"""Single virtual-thread ELF TLS template and local module-ID model. No host TLS calls."""
import struct,hashlib
IMPORTS={122:('__tls_get_addr',0x184d3e8,0x14f0844)}
def configure(cpu,spec):
    if cpu.tls_spec is not None and cpu.tls_spec!=spec:raise ValueError('TLS template changed across checkpoint')
    if not 0<=spec['file_size']<=spec['memory_size']<=0x10000 or spec['alignment']!=16:raise ValueError('Unsupported TLS size/alignment')
    if not spec['descriptors'] or any(not 0<=offset<spec['memory_size'] for address,offset in spec['descriptors']):raise ValueError('Invalid TLS offset')
    cpu.tls_spec=spec

def model(cpu):
    spec=cpu.tls_spec;cpu.demand(spec is not None,'TLS_TEMPLATE_NOT_CONFIGURED');address=cpu.reg('RDI');descriptors=dict(spec['descriptors']);cpu.demand(address in descriptors,'UNKNOWN_TLS_DESCRIPTOR',address)
    # Validate exact local-module descriptors and known offsets before any mutation.
    for slot,offset in descriptors.items():
        module,actual=struct.unpack('<QQ',cpu.read_known(slot,16));cpu.demand(actual==offset and module==(1 if cpu.tls_block else 0),'UNMODELED_TLS_MODULE_OR_OFFSET',slot)
    if not cpu.tls_block:
        template=cpu.read_known(spec['address'],spec['file_size']);image=template+bytes(spec['memory_size']-spec['file_size']);base=cpu.reserve_fixture(spec['memory_size']);cpu.demand(base%16==0,'TLS_ALIGNMENT_MISMATCH',base)
        cpu.write_private(base,image)
        for slot,offset in descriptors.items():
            cpu.uc.mem_write(slot,struct.pack('<Q',1));cpu.commit_write(slot,8);cpu.external_binding_events+=1
        cpu.tls_block=base;cpu.emit('VIRTUAL_TLS_TEMPLATE',f'base={base:x}',f'initialized_file_bytes={len(template)}',f'total_bytes={len(image)}',f'sha256={hashlib.sha256(image).hexdigest()}','module_id=1','virtual_threads=1','host_tls_access=false')
    result=cpu.tls_block+descriptors[address];cpu.tls_calls+=1;cpu.emit('VIRTUAL_TLS_GET_ADDR',f'descriptor={address:x}',f'offset={descriptors[address]:x}',f'result={result:x}','host_tls_access=false');return result
