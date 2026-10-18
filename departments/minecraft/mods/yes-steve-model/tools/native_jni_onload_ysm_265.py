#!/usr/bin/env python3
"""Continue exact YSM JNI_OnLoad only after all initializers in the isolated scenario."""
import argparse,hashlib,json
from pathlib import Path
from native_jni_fixture_ysm_265 import JniGuardedCPU
from native_guarded_checkpoint_ysm_265 import read_checkpoint,write_checkpoint
from native_initializer_sequence_ysm_265 import prepare_call
ENTRY=0x418760

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--allow-stack-extension',action='store_true',help='Explicitly migrate a legacy small-stack snapshot into the bounded larger-stack scenario');p.add_argument('--batch-size',type=int,default=1,help='Optional guarded instruction batch size; 1 uses the legacy backend');p.add_argument('--java-base',type=Path);p.add_argument('--jar',type=Path);p.add_argument('--jvm-image',type=Path);p.add_argument('--image',type=Path,required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--initializer-checkpoint',type=Path);g.add_argument('--resume-jni-checkpoint',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--checkpoint-out',type=Path,required=True);p.add_argument('--steps',type=int,default=4000000);p.add_argument('--seconds',type=int,default=180);a=p.parse_args();data=a.image.read_bytes();before=hashlib.sha256(data).hexdigest()
    with a.out.open('w') as out:
        cpu_type=JniGuardedCPU
        if a.batch_size!=1:
            from native_batched_cpu_ysm_265 import BatchedJni
            cpu_type=BatchedJni
        c=cpu_type(out,'proc-fixture',a.steps,a.seconds);c.batch_size=a.batch_size;c.load_image(data);c.configure_loader('image-only');read_checkpoint(c,a.initializer_checkpoint or a.resume_jni_checkpoint,allow_stack_extension=a.allow_stack_extension)
        if a.initializer_checkpoint and (c.init_phase!='done' or c.init_array_completed!=list(range(45)) or c.call_in_progress or c.jni_state is not None):raise ValueError('Require completed initializer checkpoint before JNI')
        if a.initializer_checkpoint:c.configure_jni();prepare_call(c,ENTRY);c.reg('RDI',c.jni_state['vm']);c.reg('RSI',0)
        elif c.jni_state is None or not c.call_in_progress:raise ValueError('Require unfinished JNI checkpoint')
        if a.jvm_image:c.configure_jvm_artifact(a.jvm_image.read_bytes(),initial=bool(a.initializer_checkpoint))
        elif c.jni_state['jvm_artifact'] is not None:raise ValueError('Resume requires the same read-only JVM artifact')
        if a.java_base or a.jar:
            from native_java_metadata_ysm_265 import JavaMetadata
            c.configure_java_metadata(JavaMetadata(jar_path=a.jar,java_base_path=a.java_base))
        elif c.jni_state['java_sources'] is not None:raise ValueError('Resume requires the same Java metadata inputs')
        c.oracle_enabled=False;r=c.run(c.reg('RIP'))
        if r['reason']=='ENTRY_RETURN':
            if any(c.reg(k)!=v for k,v in c.call_saved.items()):raise ValueError('JNI_OnLoad callee-saved mismatch')
            c.call_in_progress=False
        digest=write_checkpoint(c,a.checkpoint_out)
    if hashlib.sha256(a.image.read_bytes()).hexdigest()!=before:raise AssertionError('Original file changed')
    print(json.dumps({'stop':r,'attempted':c.attempted,'completed':c.completed,'jni_calls':c.jni_state['calls'],'checkpoint_sha256':digest,'host_jvm_called':False,'pending_exception':c.jni_state['pending_exception'],'return_value':c.reg('RAX') if r['reason']=='ENTRY_RETURN' else None,'batch_size':a.batch_size}))
if __name__=='__main__':main()
