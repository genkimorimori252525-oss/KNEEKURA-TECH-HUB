#!/usr/bin/env python3
"""Bounded DT_INIT + ordered init-array sequence in an explicitly synthetic isolated loader view."""
import argparse,hashlib,json,struct,time
from pathlib import Path
from native_sync_fixture_ysm_265 import SyncGuardedCPU
from native_unicorn_guarded_ysm_265 import SP,RETURN,X
from native_guarded_checkpoint_ysm_265 import read_checkpoint,write_checkpoint
from native_elf_loader_view_ysm_265 import manifest,apply_loader_view
CALLEE=('RBX','RBP','R12','R13','R14','R15')
CALLER=('RAX','RCX','RDX','RSI','RDI','R8','R9','R10','R11')

def prepare_call(cpu,target):
    if cpu.call_in_progress:raise ValueError('Cannot overwrite an unfinished callback frame')
    if not cpu.code_allowed(target):raise ValueError('Initializer target outside executable image')
    for name in CALLER:cpu.reg(name,0)
    cpu.reg('RSP',SP);cpu.write_private(SP,struct.pack('<Q',RETURN),log=False);cpu.uc.reg_write(X.UC_X86_REG_EFLAGS,0x202);cpu.call_saved={name:cpu.reg(name) for name in CALLEE};cpu.call_in_progress=True;cpu.reg('RIP',target)
    cpu.emit('INITIALIZER_CALL',f'phase={cpu.init_phase}',f'index={cpu.init_array_index}',f'entry={target:x}','argc_argv_envp=synthetic-zero','caller_saved_registers=synthetic-zero','flags=202')

def callback_frames_complete(cpu):
    if getattr(cpu,'once_pending',[]) or (getattr(cpu,'jni_state',None) or {}).get('pending_callbacks',[]):
        cpu.emit('REJECTED_TOP_LEVEL_RETURN','pending_guest_callback=true','completion=false')
        cpu.stop=None;cpu.fail('UNFINISHED_GUEST_CALLBACK_AT_ENTRY_RETURN',cpu.reg('RIP'));return False
    return True

def advance_after_return(cpu):
    if cpu.stop['reason']!='ENTRY_RETURN':return False
    if not callback_frames_complete(cpu):return False
    if any(cpu.reg(name)!=value for name,value in cpu.call_saved.items()):raise ValueError('Initializer callee-saved register mismatch')
    cpu.call_in_progress=False
    if cpu.init_phase=='dt-init':cpu.init_phase='init-array';cpu.oracle_enabled=False
    elif cpu.init_phase=='init-array':
        if cpu.init_array_completed!=list(range(cpu.init_array_index)):raise ValueError('Initializer order changed')
        cpu.init_array_completed.append(cpu.init_array_index);cpu.init_array_index+=1
    else:raise ValueError('Invalid initializer phase')
    cpu.emit('INITIALIZER_RETURN',f'phase={cpu.init_phase}',f'completed_callbacks={len(cpu.init_array_completed)}')
    return True

def run_sequence(cpu,m,max_steps,seconds):
    began=time.monotonic();used=0
    while cpu.init_phase!='done':
        if cpu.init_phase=='init-array' and cpu.init_array_index==len(m['initializers']):cpu.init_phase='done';break
        remaining=max_steps-used;time_left=seconds-(time.monotonic()-began)
        if remaining<=0 or time_left<=0:cpu.emit('SEQUENCE_RESOURCE_LIMIT',f'used_steps={used}');break
        if not cpu.call_in_progress:
            target=m['dt_init'] if cpu.init_phase=='dt-init' else m['initializers'][cpu.init_array_index];prepare_call(cpu,target)
        cpu.origin_completed=getattr(cpu,'origin_completed',0)+cpu.completed;cpu.attempted=cpu.completed=0;cpu.stop=None;cpu.limit=remaining;cpu.seconds=time_left
        cpu.run(cpu.reg('RIP'));used+=cpu.attempted
        if not advance_after_return(cpu):break
    cpu.emit('INITIALIZER_SEQUENCE',f'phase={cpu.init_phase}',f'completed_callbacks={len(cpu.init_array_completed)}',f'total_callbacks={len(m["initializers"])}',f'active_callback={cpu.init_array_index}',f'call_in_progress={cpu.call_in_progress}',f'current_process_attempted={used}')
    return {'phase':cpu.init_phase,'completed_callbacks':len(cpu.init_array_completed),'active_callback':cpu.init_array_index,'stop':cpu.stop,'current_process_attempted':used}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--batch-size',type=int,default=1);p.add_argument('--deferred-threads',action='store_true');p.add_argument('--image',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--checkpoint-out',type=Path,required=True);p.add_argument('--resume-checkpoint',type=Path);p.add_argument('--steps',type=int,default=4000000);p.add_argument('--seconds',type=int,default=180);a=p.parse_args()
    data=a.image.read_bytes();before=hashlib.sha256(data).hexdigest();m=manifest(data)
    with a.out.open('w') as out:
        cpu_type=SyncGuardedCPU
        if a.deferred_threads:
            from native_pthread_once_fixture_ysm_265 import OnceThreadCPU
            cpu_type=OnceThreadCPU
        if a.batch_size!=1:
            from native_batched_cpu_ysm_265 import BatchedMixin
            cpu_type=type('BatchedInitializerCPU',(BatchedMixin,cpu_type),{})
        c=cpu_type(out,'proc-fixture',a.steps,a.seconds);c.batch_size=a.batch_size;c.load_image(data);c.configure_loader('image-only');c.virtual_platform=True;c.protection_result='success-input';c.cpuid_leaf1=(0,0,0,0);c.accelerate_crc=True
        if a.resume_checkpoint:
            c.emit('CHECKPOINT_SOURCE_SHA256',read_checkpoint(c,a.resume_checkpoint))
            if a.deferred_threads and not c.threads_enabled:raise ValueError('Cannot add thread capability to an old initializer checkpoint; replay fresh')
            if not c.loader_view_applied:raise ValueError('Cannot use an unrelocated scenario snapshot for this sequence')
            if not c.external_data_guard_applied:raise ValueError('Checkpoint predates external-data guards; replay fresh before making stronger claims')
        else:
            apply_loader_view(c,data)
            if a.deferred_threads:
                from native_thread_support_gate_ysm_265 import configure_thread_support
                configure_thread_support(c,data,[0x2fccb0])
        from native_stdio_fixture_ysm_265 import ensure_stdio_bindings
        ensure_stdio_bindings(c)
        from native_tls_fixture_ysm_265 import configure
        configure(c,m['tls'])
        r=run_sequence(c,m,a.steps,a.seconds);c.emit('CHECKPOINT_SAVED_SHA256',write_checkpoint(c,a.checkpoint_out))
    if hashlib.sha256(a.image.read_bytes()).hexdigest()!=before:raise AssertionError('Original file changed')
    print(json.dumps(r))
if __name__=='__main__':main()
