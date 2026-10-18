#!/usr/bin/env python3
"""Continue exact YSM JNI_OnLoad only after all initializers in the isolated scenario."""
import argparse,hashlib,json
from pathlib import Path
from native_jni_fixture_ysm_265 import JniGuardedCPU
from native_guarded_checkpoint_ysm_265 import read_checkpoint,write_checkpoint
from native_initializer_sequence_ysm_265 import prepare_call,callback_frames_complete
ENTRY=0x418760

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--forge-runtime-profile',choices=('forgeclient','forgeserver'));p.add_argument('--forge-runtime-initialized',action='store_true');p.add_argument('--forge-production-property',choices=('absent','present'));p.add_argument('--dependency',action='append',nargs=3,metavar=('ID','SHA256','JAR'),default=[]);p.add_argument('--allow-java-source-extension',action='store_true');p.add_argument('--allow-stack-extension',action='store_true',help='Explicitly migrate a legacy small-stack snapshot into the bounded larger-stack scenario');p.add_argument('--batch-size',type=int,default=1,help='Optional guarded instruction batch size; 1 uses the legacy backend');p.add_argument('--java-base',type=Path);p.add_argument('--jar',type=Path);p.add_argument('--jvm-image',type=Path);p.add_argument('--image',type=Path,required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--initializer-checkpoint',type=Path);g.add_argument('--resume-jni-checkpoint',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--checkpoint-out',type=Path,required=True);p.add_argument('--steps',type=int,default=4000000);p.add_argument('--seconds',type=int,default=180);a=p.parse_args()
    if a.forge_runtime_profile:
        if not a.forge_runtime_initialized or a.forge_production_property is None:p.error('Forge runtime profile requires explicit initialized-state and production-property presence inputs')
    elif a.forge_runtime_initialized or a.forge_production_property is not None:p.error('Forge runtime-state inputs require --forge-runtime-profile')
    data=a.image.read_bytes();before=hashlib.sha256(data).hexdigest()
    with a.out.open('w') as out:
        cpu_type=JniGuardedCPU
        if a.batch_size!=1:
            from native_batched_cpu_ysm_265 import BatchedJni
            cpu_type=BatchedJni
        if a.forge_runtime_profile:
            from native_forge_runtime_fixture_ysm_265 import ForgeRuntimeCPU
            cpu_type=ForgeRuntimeCPU
            if a.batch_size!=1:
                from native_batched_cpu_ysm_265 import BatchedMixin
                class BatchedForge(BatchedMixin,ForgeRuntimeCPU):pass
                cpu_type=BatchedForge
        c=cpu_type(out,'proc-fixture',a.steps,a.seconds);c.batch_size=a.batch_size;c.load_image(data);c.configure_loader('image-only');read_checkpoint(c,a.initializer_checkpoint or a.resume_jni_checkpoint,allow_stack_extension=a.allow_stack_extension)
        if a.initializer_checkpoint and (c.init_phase!='done' or c.init_array_completed!=list(range(45)) or c.call_in_progress or c.jni_state is not None):raise ValueError('Require completed initializer checkpoint before JNI')
        if a.initializer_checkpoint:c.configure_jni();prepare_call(c,ENTRY);c.reg('RDI',c.jni_state['vm']);c.reg('RSI',0)
        elif c.jni_state is None or not c.call_in_progress:raise ValueError('Require unfinished JNI checkpoint')
        if a.jvm_image:c.configure_jvm_artifact(a.jvm_image.read_bytes(),initial=bool(a.initializer_checkpoint))
        elif c.jni_state['jvm_artifact'] is not None:raise ValueError('Resume requires the same read-only JVM artifact')
        if a.java_base or a.jar or a.dependency:
            from native_java_metadata_ysm_265 import JavaMetadata
            if len({x[0] for x in a.dependency})!=len(a.dependency):raise ValueError('Duplicate dependency ID')
            c.configure_java_metadata(JavaMetadata(jar_path=a.jar,java_base_path=a.java_base,dependency_paths={key:(Path(path),digest) for key,digest,path in a.dependency}),allow_source_extension=a.allow_java_source_extension)
        elif c.jni_state['java_sources'] is not None:raise ValueError('Resume requires the same Java metadata inputs')
        if a.forge_runtime_profile:c.configure_forge_runtime(a.forge_runtime_profile,initialized=a.forge_runtime_initialized,production_property_present=a.forge_production_property=='present')
        c.oracle_enabled=False;r=c.run(c.reg('RIP'))
        if r['reason']=='ENTRY_RETURN' and callback_frames_complete(c):
            if any(c.reg(k)!=v for k,v in c.call_saved.items()):raise ValueError('JNI_OnLoad callee-saved mismatch')
            c.call_in_progress=False
            if c.threads_enabled:c.thread_boundary()
        r=c.stop;digest=write_checkpoint(c,a.checkpoint_out)
    if hashlib.sha256(a.image.read_bytes()).hexdigest()!=before:raise AssertionError('Original file changed')
    print(json.dumps({'stop':r,'attempted':c.attempted,'completed':c.completed,'jni_calls':c.jni_state['calls'],'checkpoint_sha256':digest,'host_jvm_called':False,'pending_exception':c.jni_state['pending_exception'],'return_value':c.reg('RAX') if r['reason']=='ENTRY_RETURN' else None,'batch_size':a.batch_size,'forge_runtime_profile':a.forge_runtime_profile,'forge_runtime_calls':len(c.forge_runtime['calls']) if getattr(c,'forge_runtime',None) else 0}))
if __name__=='__main__':main()
