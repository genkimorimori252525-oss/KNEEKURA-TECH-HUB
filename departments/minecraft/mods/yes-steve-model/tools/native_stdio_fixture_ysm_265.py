"""Explicit opaque standard-stream data bindings, never real FILE objects or host I/O."""
import struct
SLOTS={'stdin':0xd2d300,'stdout':0xd2d190,'stderr':0xd2d198}
NAMES=('stdin','stdout','stderr')
HANDLE=0x770000000000

def ensure_stdio_bindings(cpu):
    if not cpu.external_data_guard_applied:raise ValueError('Standard streams require unresolved-data guards')
    missing=[name for name in NAMES if name not in cpu.external_data_bindings]
    if not missing:return
    for name in missing:
        if [SLOTS[name],name] not in cpu.external_data_slots:raise ValueError('Missing exact unresolved standard-stream slot')
        if bytes(cpu.uc.mem_read(SLOTS[name],8))!=bytes(8):raise ValueError('Unexpected unresolved standard-stream value')
    if not cpu.stdio_fixture_base:
        base=cpu.reserve_fixture(64)
        for i,name in enumerate(NAMES):cpu.write_private(base+i*8,struct.pack('<Q',HANDLE+i*0x100))
        cpu.private_readonly.append((base,base+64));cpu.stdio_fixture_base=base
    for name in missing:
        address=cpu.stdio_fixture_base+NAMES.index(name)*8;slot=SLOTS[name]
        # Logical loader binding at/before first use. Guest page permissions are unchanged.
        cpu.uc.mem_write(slot,struct.pack('<Q',address));cpu.commit_write(slot,8);cpu.external_data_slots.remove([slot,name]);cpu.external_data_bindings[name]=address;cpu.external_binding_events+=1
        cpu.emit('VIRTUAL_EXTERNAL_DATA_BINDING',name,f'slot={slot:x}',f'variable={address:x}',f'opaque_FILE={HANDLE+NAMES.index(name)*0x100:x}','host_stream_access=false','FILE_contents=unknown','guest_permissions_unchanged=true')
    if not cpu.expected_image_matches():raise AssertionError('Standard-stream binding disagrees with image ledger')
