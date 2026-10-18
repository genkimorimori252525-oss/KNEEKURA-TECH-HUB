"""Explicit virtual JNI invocation tables; no JVM or target native host execution.

Only explicit invocation, reference, exception and metadata lookups are modeled.
Other calls stop with their actual slot. Handles/table copies are not real JVM
objects; artifact-derived function addresses are intercepted before execution.
"""
import copy,hashlib,struct,time
from unicorn import UC_PROT_READ,UC_PROT_EXEC
from native_pthread_once_fixture_ysm_265 import OnceThreadCPU
from native_unicorn_guarded_ysm_265 import ModelHalt
TRAPS=0x780000000000;ENV_TABLE=TRAPS+0x1000;VM_TABLE=TRAPS+0x2000;VERSION=0x000a0000
# Official JDK21 jni.h SHA256 99e64ebbe749e6df284f852f11b3c73f6ea97baf15120428f40f887fe0616e61
# JNI10 fixture uses slots0..233; later-version slot234 is excluded.
ENV_NAMES=['reserved0', 'reserved1', 'reserved2', 'reserved3', 'GetVersion', 'DefineClass', 'FindClass', 'FromReflectedMethod', 'FromReflectedField', 'ToReflectedMethod', 'GetSuperclass', 'IsAssignableFrom', 'ToReflectedField', 'Throw', 'ThrowNew', 'ExceptionOccurred', 'ExceptionDescribe', 'ExceptionClear', 'FatalError', 'PushLocalFrame', 'PopLocalFrame', 'NewGlobalRef', 'DeleteGlobalRef', 'DeleteLocalRef', 'IsSameObject', 'NewLocalRef', 'EnsureLocalCapacity', 'AllocObject', 'NewObject', 'NewObjectV', 'NewObjectA', 'GetObjectClass', 'IsInstanceOf', 'GetMethodID', 'CallObjectMethod', 'CallObjectMethodV', 'CallObjectMethodA', 'CallBooleanMethod', 'CallBooleanMethodV', 'CallBooleanMethodA', 'CallByteMethod', 'CallByteMethodV', 'CallByteMethodA', 'CallCharMethod', 'CallCharMethodV', 'CallCharMethodA', 'CallShortMethod', 'CallShortMethodV', 'CallShortMethodA', 'CallIntMethod', 'CallIntMethodV', 'CallIntMethodA', 'CallLongMethod', 'CallLongMethodV', 'CallLongMethodA', 'CallFloatMethod', 'CallFloatMethodV', 'CallFloatMethodA', 'CallDoubleMethod', 'CallDoubleMethodV', 'CallDoubleMethodA', 'CallVoidMethod', 'CallVoidMethodV', 'CallVoidMethodA', 'CallNonvirtualObjectMethod', 'CallNonvirtualObjectMethodV', 'CallNonvirtualObjectMethodA', 'CallNonvirtualBooleanMethod', 'CallNonvirtualBooleanMethodV', 'CallNonvirtualBooleanMethodA', 'CallNonvirtualByteMethod', 'CallNonvirtualByteMethodV', 'CallNonvirtualByteMethodA', 'CallNonvirtualCharMethod', 'CallNonvirtualCharMethodV', 'CallNonvirtualCharMethodA', 'CallNonvirtualShortMethod', 'CallNonvirtualShortMethodV', 'CallNonvirtualShortMethodA', 'CallNonvirtualIntMethod', 'CallNonvirtualIntMethodV', 'CallNonvirtualIntMethodA', 'CallNonvirtualLongMethod', 'CallNonvirtualLongMethodV', 'CallNonvirtualLongMethodA', 'CallNonvirtualFloatMethod', 'CallNonvirtualFloatMethodV', 'CallNonvirtualFloatMethodA', 'CallNonvirtualDoubleMethod', 'CallNonvirtualDoubleMethodV', 'CallNonvirtualDoubleMethodA', 'CallNonvirtualVoidMethod', 'CallNonvirtualVoidMethodV', 'CallNonvirtualVoidMethodA', 'GetFieldID', 'GetObjectField', 'GetBooleanField', 'GetByteField', 'GetCharField', 'GetShortField', 'GetIntField', 'GetLongField', 'GetFloatField', 'GetDoubleField', 'SetObjectField', 'SetBooleanField', 'SetByteField', 'SetCharField', 'SetShortField', 'SetIntField', 'SetLongField', 'SetFloatField', 'SetDoubleField', 'GetStaticMethodID', 'CallStaticObjectMethod', 'CallStaticObjectMethodV', 'CallStaticObjectMethodA', 'CallStaticBooleanMethod', 'CallStaticBooleanMethodV', 'CallStaticBooleanMethodA', 'CallStaticByteMethod', 'CallStaticByteMethodV', 'CallStaticByteMethodA', 'CallStaticCharMethod', 'CallStaticCharMethodV', 'CallStaticCharMethodA', 'CallStaticShortMethod', 'CallStaticShortMethodV', 'CallStaticShortMethodA', 'CallStaticIntMethod', 'CallStaticIntMethodV', 'CallStaticIntMethodA', 'CallStaticLongMethod', 'CallStaticLongMethodV', 'CallStaticLongMethodA', 'CallStaticFloatMethod', 'CallStaticFloatMethodV', 'CallStaticFloatMethodA', 'CallStaticDoubleMethod', 'CallStaticDoubleMethodV', 'CallStaticDoubleMethodA', 'CallStaticVoidMethod', 'CallStaticVoidMethodV', 'CallStaticVoidMethodA', 'GetStaticFieldID', 'GetStaticObjectField', 'GetStaticBooleanField', 'GetStaticByteField', 'GetStaticCharField', 'GetStaticShortField', 'GetStaticIntField', 'GetStaticLongField', 'GetStaticFloatField', 'GetStaticDoubleField', 'SetStaticObjectField', 'SetStaticBooleanField', 'SetStaticByteField', 'SetStaticCharField', 'SetStaticShortField', 'SetStaticIntField', 'SetStaticLongField', 'SetStaticFloatField', 'SetStaticDoubleField', 'NewString', 'GetStringLength', 'GetStringChars', 'ReleaseStringChars', 'NewStringUTF', 'GetStringUTFLength', 'GetStringUTFChars', 'ReleaseStringUTFChars', 'GetArrayLength', 'NewObjectArray', 'GetObjectArrayElement', 'SetObjectArrayElement', 'NewBooleanArray', 'NewByteArray', 'NewCharArray', 'NewShortArray', 'NewIntArray', 'NewLongArray', 'NewFloatArray', 'NewDoubleArray', 'GetBooleanArrayElements', 'GetByteArrayElements', 'GetCharArrayElements', 'GetShortArrayElements', 'GetIntArrayElements', 'GetLongArrayElements', 'GetFloatArrayElements', 'GetDoubleArrayElements', 'ReleaseBooleanArrayElements', 'ReleaseByteArrayElements', 'ReleaseCharArrayElements', 'ReleaseShortArrayElements', 'ReleaseIntArrayElements', 'ReleaseLongArrayElements', 'ReleaseFloatArrayElements', 'ReleaseDoubleArrayElements', 'GetBooleanArrayRegion', 'GetByteArrayRegion', 'GetCharArrayRegion', 'GetShortArrayRegion', 'GetIntArrayRegion', 'GetLongArrayRegion', 'GetFloatArrayRegion', 'GetDoubleArrayRegion', 'SetBooleanArrayRegion', 'SetByteArrayRegion', 'SetCharArrayRegion', 'SetShortArrayRegion', 'SetIntArrayRegion', 'SetLongArrayRegion', 'SetFloatArrayRegion', 'SetDoubleArrayRegion', 'RegisterNatives', 'UnregisterNatives', 'MonitorEnter', 'MonitorExit', 'GetJavaVM', 'GetStringRegion', 'GetStringUTFRegion', 'GetPrimitiveArrayCritical', 'ReleasePrimitiveArrayCritical', 'GetStringCritical', 'ReleaseStringCritical', 'NewWeakGlobalRef', 'DeleteWeakGlobalRef', 'ExceptionCheck', 'NewDirectByteBuffer', 'GetDirectBufferAddress', 'GetDirectBufferCapacity', 'GetObjectRefType', 'GetModule']
CALLBACK_RETURN=TRAPS+0xff0
JVM_IMPORT_SLOTS={'JNI_GetCreatedJavaVMs':0xd2d078,'JNI_CreateJavaVM':0xd2d080,'JNI_GetDefaultJavaVMInitArgs':0xd2d088}
CALLEE=('RBX','RBP','R12','R13','R14','R15')
VM_NAMES=['reserved0','reserved1','reserved2','DestroyJavaVM','AttachCurrentThread','DetachCurrentThread','GetEnv','AttachCurrentThreadAsDaemon']

def table(names,base):return b''.join(struct.pack('<Q',0 if n.startswith('reserved') else TRAPS+16*(base+i)) for i,n in enumerate(names))
class JniGuardedCPU(OnceThreadCPU):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.jni_state=None;self.jni_expected={};self.jni_gateways={};self.jvm_artifact_bytes=None;self.jvm_view=None;self.jvm_interfaces_ready=False;self.java_metadata=None
    def jni_hit(self,a,n):return any(lo<a+n and a<lo+len(v) for lo,v in getattr(self,'jni_expected',{}).items())
    def interface_bytes(self,kind):
        interfaces=(self.jni_state or {}).get('jvm_interfaces')
        if interfaces is not None:return b''.join(struct.pack('<Q',x) for x in interfaces[kind])
        return table(VM_NAMES,0) if kind=='vm' else table(ENV_NAMES,8)
    def rebuild_jni_interfaces(self,initial_mapping=False):
        gateways={CALLBACK_RETURN:('continuation',0,'dl_iterate_phdr-return')}
        for kind,names in [('vm',VM_NAMES),('env',ENV_NAMES)]:
            addresses=struct.unpack('<'+'Q'*len(names),self.interface_bytes(kind))
            for i,(address,name) in enumerate(zip(addresses,names)):
                if name.startswith('reserved'):continue
                if address in gateways:raise ValueError('Ambiguous JNI gateway address')
                gateways[address]=(kind,i,name)
        self.jni_gateways=gateways;code=bytearray(4096)
        for a in gateways:
            if TRAPS<=a<TRAPS+4096:code[a-TRAPS]=0xc3
        for a,data,perm in [(TRAPS,bytes(code),UC_PROT_READ|UC_PROT_EXEC),(ENV_TABLE,self.interface_bytes('env').ljust(4096,b'\0'),UC_PROT_READ),(VM_TABLE,self.interface_bytes('vm').ljust(4096,b'\0'),UC_PROT_READ)]:
            if initial_mapping:self.uc.mem_map(a,4096,perm)
            self.uc.mem_write(a,data);self.jni_expected[a]=data
    def configure_jni_pages(self):
        if self.jni_expected:raise ValueError('JNI fixture already mapped')
        self.rebuild_jni_interfaces(initial_mapping=True)
    def configure_jni(self):
        if self.jni_state is not None:raise ValueError('JNI fixture already configured')
        for name,slot in JVM_IMPORT_SLOTS.items():
            if self.shadow_region(slot,8) is not None and name not in self.external_data_bindings and [slot,name] not in self.external_data_slots:
                if bytes(self.uc.mem_read(slot,8))!=bytes(8):raise ValueError('Unexpected unbound JVM import')
                self.external_data_slots.append([slot,name])
        self.configure_jni_pages();vm=self.reserve_fixture(8);env=self.reserve_fixture(8);self.write_private(vm,struct.pack('<Q',VM_TABLE));self.write_private(env,struct.pack('<Q',ENV_TABLE));self.private_readonly.extend([(vm,vm+8),(env,env+8)])
        self.jni_state={'table_slots':len(ENV_NAMES),'version':VERSION,'vm':vm,'env':env,'calls':[],'getenv_calls':0,'getversion_calls':0,'cpuid_basic_calls':0,'phdr_info':0,'phdr_callbacks':0,'pending_callbacks':[],'classes':{},'jvm_artifact':None,'pending_exception':None,'deleted_local_refs':[],'jvm_loader_calls':0,'jvm_open_refs':0,'jvm_phdr_info':0,'jvm_name':0,'jvm_interfaces':None,'java_sources':None,'java_source_extensions':[],'class_proofs':{},'global_refs':[],'methods':{},'fields':{}};self.emit('JNI_SCENARIO','jni_version=0xa0000','virtual_thread=attached','synthetic_vm_and_env=true','host_jvm=false')
    def configure_jvm_artifact(self,data,initial=False):
        if self.jni_state is None or not 64<=len(data)<=64*1024*1024 or data[:6]!=b'\x7fELF\x02\x01':raise ValueError('Invalid read-only JVM artifact')
        metadata={'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'virtual_path':'/virtual/jdk/lib/server/libjvm.so'}
        previous=self.jni_state['jvm_artifact']
        if previous!=metadata and not(initial and previous is None):raise ValueError('JVM artifact mismatch; changed input requires fresh JNI scenario')
        self.jvm_artifact_bytes=bytes(data);self.jni_state['jvm_artifact']=metadata
        if self.jvm_view is None:
            from native_jvm_artifact_view_ysm_265 import JvmArtifactView
            self.jvm_view=JvmArtifactView(self,data)
        interfaces={}
        for kind,names in [('vm',VM_NAMES),('env',ENV_NAMES)]:
            interfaces[kind]=[0 if n.startswith('reserved') else self.jvm_view.local_function('jni_'+n)['address'] for n in names]
        old=self.jni_state['jvm_interfaces']
        if old!=interfaces and not(initial and old is None):raise ValueError('Artifact-backed interface change requires fresh JNI scenario')
        self.jni_state['jvm_interfaces']=interfaces;self.rebuild_jni_interfaces()
        for page in {a&~4095 for group in interfaces.values() for a in group if a}:self.uc.mem_protect(page,4096,UC_PROT_READ|UC_PROT_EXEC)
        for name,slot in JVM_IMPORT_SLOTS.items():
            if self.shadow_region(slot,8) is None:continue
            address=self.jvm_view.symbol(name)['address']
            if name not in self.external_data_bindings:
                if not initial or [slot,name] not in self.external_data_slots or bytes(self.uc.mem_read(slot,8))!=bytes(8):raise ValueError('JVM binding requires fresh guarded scenario')
                self.uc.mem_write(slot,struct.pack('<Q',address));self.commit_write(slot,8);self.external_data_slots.remove([slot,name]);self.external_data_bindings[name]=address;self.external_binding_events+=1;self.emit('ARTIFACT_JVM_IMPORT_BINDING',name,f'slot={slot:x}',f'address={address:x}','host_linker_called=false')
            elif self.external_data_bindings[name]!=address or bytes(self.uc.mem_read(slot,8))!=struct.pack('<Q',address):raise ValueError('Changed JVM import binding')
        if self.jni_state['jvm_name'] and self.ascii(self.jni_state['jvm_name'])!=metadata['virtual_path']:raise ValueError('Changed JVM module name fixture')
        if self.jni_state['jvm_phdr_info']:
            from native_jvm_artifact_view_ysm_265 import BASE
            expected=struct.pack('<QQQH6xQQ',BASE,self.jni_state['jvm_name'],BASE+self.jvm_view.phoff,self.jvm_view.phnum,2,0)
            if self.read_known(self.jni_state['jvm_phdr_info'],48)!=expected:raise ValueError('Changed JVM program header fixture')
        self.jvm_interfaces_ready=True
        self.emit('JVM_ARTIFACT_INPUT',metadata['sha256'],f'bytes={len(data)}','host_library_loaded=false','artifact_bytes_mapped_readonly=true','jvm_code_execution=false','writable_runtime_data=unknown','file_bytes_only=true')
    def configure_java_metadata(self,metadata,*,allow_source_extension=False):
        previous=self.jni_state['java_sources'];added={}
        if previous is not None and previous!=metadata.sources:
            if not allow_source_extension or not all(metadata.sources.get(k)==v for k,v in previous.items()) or not set(previous)<set(metadata.sources):raise ValueError('Java metadata artifacts changed; additive source extension requires explicit opt-in')
            added={k:v for k,v in metadata.sources.items() if k not in previous}
            if any(k in ('ysm','java.base') for k in added) or len(self.jni_state['java_source_extensions'])>=8:raise ValueError('Invalid Java dependency extension')
        for name,proof in self.jni_state['class_proofs'].items():
            info=metadata.class_info(name)
            if info is None or info['class_sha256']!=proof['sha256'] or info['source']!=proof['source']:raise ValueError('Java class proof changed')
        for kind in ('methods','fields'):
            lookup=metadata.lookup_method if kind=='methods' else metadata.lookup_field
            for item in self.jni_state[kind].values():
                record=lookup(item['requested_class'],item['name'],item['descriptor'],item['static'])
                if record is None or any(record[k]!=item[k] for k in ['declaring_class','class_sha256','source']):raise ValueError('Java member metadata changed')
        if added:
            self.jni_state['java_source_extensions'].append({'added':copy.deepcopy(added)});self.emit('JAVA_METADATA_SOURCE_EXTENSION',str(added),'existing_proofs_revalidated=true','equivalent_scenario=false','host_java_execution=false')
        self.java_metadata=metadata;self.jni_state['java_sources']=copy.deepcopy(metadata.sources);self.emit('JAVA_METADATA_INPUTS',str(metadata.sources),'host_java_execution=false')
    def code_allowed(self,a,n=1):return (a in getattr(self,'jni_gateways',{}) and n<=15 and (TRAPS<=a<TRAPS+4096 or self.jvm_interfaces_ready)) or super().code_allowed(a,n)
    def unknown(self,a,n):
        view=getattr(self,'jvm_view',None)
        if view is not None and view.hit(a,n):return view.unknown(a,n)
        if any(lo<=a and a+n<=lo+len(v) for lo,v in getattr(self,'jni_expected',{}).items()):return None
        return super().unknown(a,n)
    def _write(self,uc,access,a,n,value,user):
        view=getattr(self,'jvm_view',None)
        if view is not None and view.hit(a,n):
            for at in range(a,a+n):
                if view.hit(at,1):self.journal.append((at,bytes(uc.mem_read(at,1))))
            self.fail('JVM_ARTIFACT_WRITE_BLOCKED',a,n);return
        if self.jni_hit(a,n):
            for at in range(a,a+n):
                if self.jni_hit(at,1):self.journal.append((at,bytes(uc.mem_read(at,1))))
            self.fail('JNI_FIXTURE_WRITE_BLOCKED',a,n);return
        super()._write(uc,access,a,n,value,user)
    def _code(self,uc,address,size,user):
        if address in self.jni_gateways:
            if self.stop:return
            if not self.code_allowed(address,size):self.fail('UNVALIDATED_JVM_INTERFACE',address,size);return
            if time.monotonic()>self.deadline:self.fail('TIME_BUDGET',address);return
            self.pc=address;self.current_raw=bytes(uc.mem_read(address,size));self.attempted+=1;self.pending='jni-import';self.emit('JNI_GATEWAY_INTERCEPT',f'address={address:x}','intercepted_before_first_instruction=true','jvm_code_executed=false');uc.emu_stop();return
        super()._code(uc,address,size,user)
    def validate_interface(self,kind,pointer):
        address=int.from_bytes(self.read_known(pointer,8),'little');expected=self.interface_bytes(kind)
        self.demand(self.read_known(address,len(expected))==expected,'UNRECOGNIZED_JNI_INTERFACE_COPY',pointer);return address
    def begin_phdr_callback(self,sp,target):
        s=self.jni_state;function,data=self.reg('RDI'),self.reg('RSI')
        self.demand(s is not None and self.code_allowed(function) and function not in self.jni_gateways and len(s['pending_callbacks'])<8 and s['phdr_callbacks']<1024,'INVALID_PROGRAM_HEADER_CALLBACK',function)
        if not s['phdr_info']:
            self.demand(self.read_known(0,6)==b'\x7fELF\x02\x01','PROGRAM_HEADER_IMAGE_ABI');offset=int.from_bytes(self.read_known(32,8),'little');count=int.from_bytes(self.read_known(56,2),'little');size=int.from_bytes(self.read_known(54,2),'little');self.demand(size==56 and 0<count<=256,'PROGRAM_HEADER_IMAGE_ABI');self.read_known(offset,count*size)
            info=struct.pack('<QQQH6xQQQQ',0,self.loader_name,offset,count,2 if self.jvm_view else 1,0,1,self.tls_block);a=self.reserve_fixture(64);self.write_private(a,info);self.private_readonly.append((a,a+64));s['phdr_info']=a
        infos=[s['phdr_info']]
        if self.jvm_view is not None:
            from native_jvm_artifact_view_ysm_265 import BASE
            if not s['jvm_phdr_info']:
                name=s['jvm_artifact']['virtual_path'].encode()+b'\0';q=self.reserve_fixture(len(name));self.write_private(q,name);self.private_readonly.append((q,q+len(name)));s['jvm_name']=q
                value=struct.pack('<QQQH6xQQ',BASE,q,BASE+self.jvm_view.phoff,self.jvm_view.phnum,2,0);a=self.reserve_fixture(64);self.write_private(a,value);self.private_readonly.append((a,a+64));s['jvm_phdr_info']=a
            infos.append(s['jvm_phdr_info'])
        frame={'sp':sp,'target':target,'function':function,'data':data,'infos':infos,'module_index':0,'saved':{r:self.reg(r) for r in CALLEE}};self.write_private(sp+24,struct.pack('<Q',CALLBACK_RETURN));s['pending_callbacks'].append(frame);s['phdr_callbacks']+=1
        self.reg('RSP',sp+24);self.reg('RDI',s['phdr_info']);self.reg('RSI',64);self.reg('RDX',data);self.reg('RIP',function);self.emit('VIRTUAL_PHDR_CALLBACK_ENTER',f'function={function:x}',f'modules={len(infos)}','module_views=original-ysm-and-optional-readonly-jvm','image_base=0','real_guest_callback_executes=true','host_loader_called=false')
    def finish_phdr_callback(self):
        s=self.jni_state;self.demand(bool(s['pending_callbacks']),'UNEXPECTED_CALLBACK_RETURN');f=s['pending_callbacks'][-1];self.demand(self.reg('RSP')==f['sp']+32 and self.reg('DF')==0 and all(self.reg(r)==v for r,v in f['saved'].items()),'CALLBACK_ABI_MISMATCH');result=self.reg('RAX')&0xffffffff
        if result==0 and f['module_index']+1<len(f['infos']):
            self.demand(s['phdr_callbacks']<1024,'PROGRAM_HEADER_CALLBACK_BUDGET');f['module_index']+=1;s['phdr_callbacks']+=1;self.write_private(f['sp']+24,struct.pack('<Q',CALLBACK_RETURN));self.reg('RSP',f['sp']+24);self.reg('RDI',f['infos'][f['module_index']]);self.reg('RSI',64);self.reg('RDX',f['data']);self.reg('RIP',f['function']);self.emit('VIRTUAL_PHDR_CALLBACK_NEXT',f"module_index={f['module_index']}");return
        self.write_private(f['sp']+24,struct.pack('<Q',f['target']));s['pending_callbacks'].pop();self.reg('RSP',f['sp']+32);self.reg('RIP',f['target']);self.reg('RAX',result);self.emit('VIRTUAL_PHDR_CALLBACK_RETURN',f'result={result:x}','iteration_complete=true')
    def model(self,kind):
        if kind=='cpuid-leaf1' and self.jni_state is not None and self.reg('RAX')&0xffffffff==7 and self.reg('RCX')&0xffffffff==0:
            self.demand(self.jni_state['cpuid_basic_calls']<4096,'JNI_CPUID_BUDGET')
            for name in ('RAX','RBX','RCX','RDX'):self.reg(name,0)
            self.jni_state['cpuid_basic_calls']+=1;self.reg('RIP',self.pc+2);self.emit('VIRTUAL_CPUID_BASIC','leaf=7','subleaf=0','outside_advertised_max1=true','returns_max_basic_leaf1_zero_fixture=true','host_cpu_queried=false');return
        if kind=='cpuid-leaf1' and self.jni_state is not None and self.reg('RAX')&0xffffffff==0:
            self.demand(self.jni_state['cpuid_basic_calls']<4096,'JNI_CPUID_BUDGET')
            values=(1,int.from_bytes(b'Genu','little'),int.from_bytes(b'ntel','little'),int.from_bytes(b'ineI','little'))
            for name,value in zip(('RAX','RBX','RCX','RDX'),values):self.reg(name,value)
            self.jni_state['cpuid_basic_calls']+=1;self.reg('RIP',self.pc+2);self.emit('VIRTUAL_CPUID_BASIC','max_basic_leaf=1','vendor=GenuineIntel','explicit_synthetic_input=true','host_cpu_queried=false');return
        if kind!='jni-import':return super().model(kind)
        category,index,name=self.jni_gateways[self.pc]
        if category=='continuation':self.finish_phdr_callback();return
        s=self.jni_state;self.demand(s is not None and len(s['calls'])<4096,'JNI_MODEL_BUDGET');sp,target=self.frame(False)
        self.emit('JNI_CALL_FRONTIER',f'kind={category}',f'index={index}',name,*(f'{r}={self.reg(r):x}' for r in ['RDI','RSI','RDX','RCX','R8','R9']))
        self.validate_interface(category,self.reg('RDI'))
        if category=='env' and s['pending_exception'] is not None:
            self.demand(name in ('ExceptionCheck','DeleteLocalRef','DeleteGlobalRef'),'JNI_CALL_WITH_PENDING_EXCEPTION',index)
        if category=='vm' and name=='GetEnv':
            self.demand(self.reg('RDX')&0xffffffff==VERSION,'UNMODELED_JNI_VERSION');self.write_model_memory(self.reg('RSI'),struct.pack('<Q',s['env']));result=0;s['getenv_calls']+=1
        elif category=='env' and name=='FindClass':
            name_input=self.ascii(self.reg('RSI'))
            try:info=self.java_metadata.class_info(name_input) if self.java_metadata is not None else None
            except ValueError:self.demand(False,'UNMODELED_JAVA_CLASS')
            self.demand(info is not None or name_input=='java/lang/RuntimeException','UNMODELED_JAVA_CLASS');self.demand(len(s['classes'])<1024,'JAVA_CLASS_HANDLE_BUDGET')
            result=0x790000000000+256*len(s['classes']);s['classes'][str(result)]=name_input
            if info is not None:s['class_proofs'][name_input]={'sha256':info['class_sha256'],'source':info['source']}
            self.emit('VIRTUAL_FIND_CLASS',name_input,f'handle={result:x}',f'artifact_metadata_verified={info is not None}','host_class_loading=false')
        elif category=='env' and name=='NewGlobalRef':
            ref=self.reg('RSI');self.demand(ref==0 or(str(ref) in s['classes'] and ref not in s['deleted_local_refs']),'UNKNOWN_JNI_REFERENCE')
            result=0
            if ref:
                self.demand(len(s['classes'])<1024,'JAVA_CLASS_HANDLE_BUDGET');result=0x790000000000+256*len(s['classes']);s['classes'][str(result)]=s['classes'][str(ref)];s['global_refs'].append(result)
        elif category=='env' and name=='DeleteGlobalRef':
            ref=self.reg('RSI');self.demand(ref==0 or ref in s['global_refs'],'UNKNOWN_JNI_GLOBAL_REFERENCE')
            if ref:s['global_refs'].remove(ref);s['deleted_local_refs'].append(ref)
            result=self.reg('RAX')
        elif category=='env' and name in ('GetMethodID','GetStaticMethodID','GetFieldID','GetStaticFieldID'):
            is_field=name in ('GetFieldID','GetStaticFieldID');collection=s['fields' if is_field else 'methods'];label='FIELD' if is_field else 'METHOD';base=0x7d0000000000 if is_field else 0x7c0000000000
            ref=self.reg('RSI');self.demand(str(ref) in s['classes'] and ref not in s['deleted_local_refs'] and self.java_metadata is not None,'JAVA_'+label+'_METADATA_REQUIRED');owner=s['classes'][str(ref)];member=self.ascii(self.reg('RDX'));descriptor=self.ascii(self.reg('RCX'));static=name in ('GetStaticMethodID','GetStaticFieldID')
            try:record=(self.java_metadata.lookup_field if is_field else self.java_metadata.lookup_method)(owner,member,descriptor,static)
            except ValueError:self.demand(False,'UNMODELED_JAVA_'+label)
            self.demand(record is not None,'UNMODELED_JAVA_'+label)
            item={'requested_class':owner,'name':member,'descriptor':descriptor,'static':static,'declaring_class':record['declaring_class'],'class_sha256':record['class_sha256'],'source':record['source']};self.demand(len(collection)<4096 or item in collection.values(),'JAVA_'+label+'_HANDLE_BUDGET');result=next((int(k) for k,v in collection.items() if v==item),base+16*len(collection));collection[str(result)]=item;self.emit('VERIFIED_JAVA_'+label+'_ID',owner,member,descriptor,f'handle={result:x}','metadata_only=true','java_initialization_not_executed=true')
        elif category=='env' and name=='ExceptionCheck':result=int(s['pending_exception'] is not None)
        elif category=='env' and name=='ThrowNew':
            cls=self.reg('RSI');self.demand(str(cls) in s['classes'] and s['classes'][str(cls)]=='java/lang/RuntimeException' and cls not in s['deleted_local_refs'] and s['pending_exception'] is None,'INVALID_JNI_THROW_CLASS_OR_STATE');message=self.ascii(self.reg('RDX'));s['pending_exception']={'class':s['classes'][str(cls)],'message':message};result=0;self.emit('VIRTUAL_JAVA_EXCEPTION_PENDING',s['classes'][str(cls)],f'message_sha256={hashlib.sha256(message.encode()).hexdigest()}','host_exception_created=false')
        elif category=='env' and name=='DeleteLocalRef':
            ref=self.reg('RSI');self.demand(ref==0 or(str(ref) in s['classes'] and ref not in s['deleted_local_refs'] and ref not in s['global_refs']),'UNKNOWN_JNI_LOCAL_REFERENCE')
            if ref:s['deleted_local_refs'].append(ref)
            result=self.reg('RAX')
        elif category=='env' and name=='GetVersion':result=VERSION;s['getversion_calls']+=1
        else:self.demand(False,'UNMODELED_JNI_CALL',index)
        s['calls'].append([category,index,name]);self.reg('RAX',result);self.reg('RSP',sp+8);self.reg('RIP',target);self.emit('VIRTUAL_JNI_CALL',name,f'result={result:x}','host_jvm_called=false')
    def report_preservation(self):
        ok=all(bytes(self.uc.mem_read(a,len(v)))==v for a,v in self.jni_expected.items());self.emit('JNI_FIXTURE_PRESERVATION',f'unchanged={ok}')
        if not ok:raise AssertionError('JNI fixture changed')
        if self.jvm_view is not None:
            good=self.jvm_view.unchanged(self);self.emit('JVM_ARTIFACT_PRESERVATION',f'unchanged={good}','jvm_code_executed=false')
            if not good:raise AssertionError('JVM artifact view changed')
        super().report_preservation()
    def capture_sparse(self):
        if self.jvm_view is not None and not self.jvm_view.unchanged(self):raise ValueError('Cannot checkpoint mutated JVM artifact view')
        if not all(bytes(self.uc.mem_read(a,len(v)))==v for a,v in self.jni_expected.items()):raise ValueError('Cannot checkpoint mutated JNI fixture')
        s=super().capture_sparse();s['jni']=copy.deepcopy(self.jni_state);return s
    def restore_sparse(self,s):
        super().restore_sparse(s);state=s.get('jni')
        if state is None:return
        state=copy.deepcopy(state);state.setdefault('cpuid_basic_calls',0);state.setdefault('phdr_info',0);state.setdefault('phdr_callbacks',0);state.setdefault('pending_callbacks',[]);state.setdefault('classes',{});state.setdefault('jvm_artifact',None);state.setdefault('pending_exception',None);state.setdefault('deleted_local_refs',[]);state.setdefault('jvm_loader_calls',0);state.setdefault('jvm_open_refs',0);state.setdefault('jvm_phdr_info',0);state.setdefault('jvm_name',0);state.setdefault('jvm_interfaces',None);state.setdefault('java_sources',None);state.setdefault('java_source_extensions',[]);state.setdefault('class_proofs',{});state.setdefault('global_refs',[]);state.setdefault('methods',{});state.setdefault('fields',{})
        if set(state)!={'table_slots','version','vm','env','calls','getenv_calls','getversion_calls','cpuid_basic_calls','phdr_info','phdr_callbacks','pending_callbacks','classes','jvm_artifact','pending_exception','deleted_local_refs','jvm_loader_calls','jvm_open_refs','jvm_phdr_info','jvm_name','jvm_interfaces','java_sources','java_source_extensions','class_proofs','global_refs','methods','fields'} or state['version']!=VERSION or state['table_slots']!=len(ENV_NAMES) or len(state['calls'])>4096:raise ValueError('Invalid JNI scenario')
        for key in ['getenv_calls','getversion_calls','cpuid_basic_calls']:
            if type(state[key]) is not int or not 0<=state[key]<=4096:raise ValueError('Invalid JNI counter')
        if any(call not in [['vm',6,'GetEnv'],['env',4,'GetVersion'],['env',6,'FindClass'],['env',14,'ThrowNew'],['env',23,'DeleteLocalRef'],['env',21,'NewGlobalRef'],['env',22,'DeleteGlobalRef'],['env',33,'GetMethodID'],['env',113,'GetStaticMethodID'],['env',228,'ExceptionCheck'],['env',94,'GetFieldID'],['env',144,'GetStaticFieldID']] for call in state['calls']) or state['getenv_calls']!=state['calls'].count(['vm',6,'GetEnv']) or state['getversion_calls']!=state['calls'].count(['env',4,'GetVersion']):raise ValueError('Invalid JNI call ledger')
        for key,expected in [('vm',VM_TABLE),('env',ENV_TABLE)]:
            if not any(lo<=state[key] and state[key]+8<=hi for lo,hi in self.private_readonly) or not self.private_region(state[key],8) or self.read_known(state[key],8)!=struct.pack('<Q',expected):raise ValueError('Invalid JNI handle')
        exception=state['pending_exception']
        if exception is not None and (set(exception)!={'class','message'} or exception['class']!='java/lang/RuntimeException' or not isinstance(exception['message'],str) or len(exception['message'])>256 or not exception['message'].isascii()):raise ValueError('Invalid pending exception')
        if not isinstance(state['deleted_local_refs'],list) or len(state['deleted_local_refs'])>1024 or len(set(state['deleted_local_refs']))!=len(state['deleted_local_refs']) or any(type(x) is not int or str(x) not in state['classes'] for x in state['deleted_local_refs']):raise ValueError('Invalid local reference ledger')
        if any(type(state[k]) is not int or not 0<=state[k]<=1024 for k in ('jvm_loader_calls','jvm_open_refs')) or state['jvm_open_refs']>state['jvm_loader_calls']:raise ValueError('Invalid JVM loader ledger')
        artifact=state['jvm_artifact']
        if artifact is not None and (set(artifact)!={'sha256','size','virtual_path'} or not isinstance(artifact['sha256'],str) or len(artifact['sha256'])!=64 or any(x not in '0123456789abcdef' for x in artifact['sha256']) or type(artifact['size']) is not int or not 64<=artifact['size']<=64*1024*1024 or artifact['virtual_path']!='/virtual/jdk/lib/server/libjvm.so'):raise ValueError('Invalid JVM artifact metadata')
        interfaces=state['jvm_interfaces']
        if interfaces is not None:
            if artifact is None or set(interfaces)!={'vm','env'}:raise ValueError('Invalid artifact-backed interfaces')
            for key,names in [('vm',VM_NAMES),('env',ENV_NAMES)]:
                values=interfaces[key]
                if not isinstance(values,list) or len(values)!=len(names) or any(type(x) is not int or (x!=0 if name.startswith('reserved') else not 0x7b0000000000<=x<0x7b0008000000) for x,name in zip(values,names)):raise ValueError('Invalid artifact interface addresses')
        if not isinstance(state['classes'],dict) or len(state['classes'])>1024 or any(str(int(k))!=k or not 0x790000000000<=int(k)<0x790000040000 or int(k)%256 or not isinstance(v,str) or not 0<len(v)<=256 or not v.isascii() or '\0' in v for k,v in state['classes'].items()):raise ValueError('Invalid declared class handle')
        if not isinstance(state['class_proofs'],dict) or any(name not in state['classes'].values() or set(proof)!={'sha256','source'} or not isinstance(proof['sha256'],str) or len(proof['sha256'])!=64 for name,proof in state['class_proofs'].items()):raise ValueError('Invalid Java class proof')
        if (state['class_proofs'] or state['methods'] or state['fields']) and state['java_sources'] is None:raise ValueError('Java metadata source missing')
        extensions=state['java_source_extensions'];seen=set()
        if not isinstance(extensions,list) or len(extensions)>8:raise ValueError('Invalid Java source extension history')
        for item in extensions:
            if not isinstance(item,dict) or set(item)!={'added'} or not isinstance(item['added'],dict) or not 0<len(item['added'])<=8 or state['java_sources'] is None:raise ValueError('Invalid Java source extension record')
            for key,value in item['added'].items():
                if key in seen or key in ('ysm','java.base') or state['java_sources'].get(key)!=value:raise ValueError('Java source extension provenance mismatch')
                seen.add(key)

        if not isinstance(state['global_refs'],list) or len(state['global_refs'])>1024 or any(type(x) is not int or str(x) not in state['classes'] or x in state['deleted_local_refs'] for x in state['global_refs']) or len(set(state['global_refs']))!=len(state['global_refs']):raise ValueError('Invalid global reference ledger')
        for kind,base in [('methods',0x7c0000000000),('fields',0x7d0000000000)]:
            if not isinstance(state[kind],dict) or len(state[kind])>4096:raise ValueError('Invalid member metadata budget')
            for key,item in state[kind].items():
                if str(int(key))!=key or not base<=int(key)<base+0x10000 or int(key)%16 or set(item)!={'requested_class','name','descriptor','static','declaring_class','class_sha256','source'} or type(item['static']) is not bool:raise ValueError('Invalid member metadata handle')
        if type(state['phdr_callbacks']) is not int or not 0<=state['phdr_callbacks']<=1024 or len(state['pending_callbacks'])>8:raise ValueError('Invalid program header callback count')
        if state['phdr_info'] and (not self.private_region(state['phdr_info'],64) or not any(lo<=state['phdr_info'] and state['phdr_info']+64<=hi for lo,hi in self.private_readonly)):raise ValueError('Invalid program header callback storage')
        for key,n in [('jvm_phdr_info',64),('jvm_name',1)]:
            if type(state[key]) is not int or state[key]<0 or(state[key] and(not self.private_region(state[key],n) or not any(lo<=state[key] and state[key]+n<=hi for lo,hi in self.private_readonly))):raise ValueError('Invalid JVM metadata fixture storage')
        if state['pending_callbacks'] and (not state['phdr_info'] or state['phdr_callbacks']<len(state['pending_callbacks'])):raise ValueError('Incoherent pending callback count')
        for f in state['pending_callbacks']:
            f.setdefault('infos',[state['phdr_info']]);f.setdefault('module_index',0)
            if not isinstance(f['infos'],list) or not 1<=len(f['infos'])<=2 or type(f['module_index']) is not int or not 0<=f['module_index']<len(f['infos']) or any(x not in [state['phdr_info'],state['jvm_phdr_info']] or not x for x in f['infos']):raise ValueError('Invalid callback module list')
            if any(type(f.get(k)) is not int or not 0<=f[k]<(1<<64) for k in ['sp','target','function','data']) or not isinstance(f.get('saved'),dict) or any(type(v) is not int or not 0<=v<(1<<64) for v in f['saved'].values()):raise ValueError('Invalid guest callback numeric value')
            if set(f)!={'sp','target','function','data','saved','infos','module_index'} or set(f['saved'])!=set(CALLEE) or not self.private_allowed(f['sp'],32) or not self.code_allowed(f['function']) or not self.return_target_allowed(f['target'],f['sp']+32):raise ValueError('Invalid pending guest callback')
        self.jni_state=copy.deepcopy(state);self.configure_jni_pages()
