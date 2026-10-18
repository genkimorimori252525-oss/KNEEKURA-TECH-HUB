"""Opaque, bounded single-virtual-thread synchronization objects. No host sync calls."""
import copy,struct
from native_sparse_vm_ysm_265 import SparseGuardedCPU
IMPORTS={31:('sem_wait',0x184d110,0x183cf8d),32:('sem_trywait',0x184d118,0x1506576),33:('sem_post',0x184d120,0x160a642),34:('sem_init',0x184d128,0x14c9ea9),35:('sem_destroy',0x184d130,0x147efbe)}
SYMBOLS={r[0] for r in IMPORTS.values()};SIZE=32;MAX_VALUE=(1<<31)-1
class SyncGuardedCPU(SparseGuardedCPU):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.sync_objects={};self.sync_calls=0
    def sync_hit(self,a,n):return next((int(k) for k,v in getattr(self,'sync_objects',{}).items() if int(k)<a+n and a<int(k)+v['size']),None)
    def sync_storage(self,a,n):
        return self.private_allowed(a,n) or self.shadow_writable(a,n) or self.vm_cover(a,n,2) is not None
    def unknown(self,a,n):
        hit=self.sync_hit(a,n)
        return max(a,hit) if hit is not None else super().unknown(a,n)
    def read_known(self,a,n):
        self.demand(self.sync_hit(a,n) is None,'OPAQUE_SYNC_OBJECT_READ',a,n);return super().read_known(a,n)
    def _read(self,uc,access,a,n,value,user):
        if self.sync_hit(a,n) is not None:self.fail('OPAQUE_SYNC_OBJECT_READ',a,n);return
        super()._read(uc,access,a,n,value,user)
    def _write(self,uc,access,a,n,value,user):
        # Parent must journal the possible pending store before emu_stop.
        super()._write(uc,access,a,n,value,user)
        if self.sync_hit(a,n) is not None:self.fail('OPAQUE_SYNC_OBJECT_WRITE',a,n)
    def model(self,kind):
        if kind=='copy' and self.reg('RCX'):
            self.demand(self.sync_hit(self.reg('RSI'),1) is None,'OPAQUE_SYNC_OBJECT_READ',self.reg('RSI'),1)
            self.demand(self.sync_hit(self.reg('RDI'),1) is None,'OPAQUE_SYNC_OBJECT_WRITE',self.reg('RDI'),1)
        return super().model(kind)
    def write_private(self,a,data,log=True):
        self.demand(self.sync_hit(a,len(data)) is None,'OPAQUE_SYNC_OBJECT_WRITE',a,len(data));return super().write_private(a,data,log)
    def write_model_memory(self,a,data):
        self.demand(self.sync_hit(a,len(data)) is None,'OPAQUE_SYNC_OBJECT_WRITE',a,len(data));return super().write_model_memory(a,data)
    def vm_change(self,a,n,prot=None,remove=False):
        self.demand(self.sync_hit(a,n) is None,'SYNC_STORAGE_MAPPING_CHANGE',a,n);return super().vm_change(a,n,prot,remove)
    def vm_advice(self,a,n,advice):
        self.demand(self.sync_hit(a,n) is None,'SYNC_STORAGE_ADVICE',a,n);return super().vm_advice(a,n,advice)
    def capture_sparse(self):
        s=super().capture_sparse();s['sync']={'objects':copy.deepcopy(self.sync_objects),'calls':self.sync_calls};return s
    def restore_sparse(self,s):
        state=s.get('sync',{'objects':{},'calls':0});objects=state['objects']
        if len(objects)>1024 or type(state['calls']) is not int or not 0<=state['calls']<=1000000:raise ValueError('Invalid synchronization budget')
        for key,obj in objects.items():
            a=int(key)
            if str(a)!=key or a%8 or set(obj)!={'kind','size','value','active'} or obj['kind']!='semaphore' or obj['size']!=SIZE or type(obj['active']) is not bool or type(obj['value']) is not int or not 0<=obj['value']<=MAX_VALUE:raise ValueError('Invalid semaphore state')
        starts=sorted(map(int,objects))
        if any(a+SIZE>b for a,b in zip(starts,starts[1:])):raise ValueError('Overlapping semaphore objects')
        super().restore_sparse(s)
        if any(not self.sync_storage(int(k),SIZE) for k in objects):raise ValueError('Missing semaphore storage')
        self.sync_objects=copy.deepcopy(objects);self.sync_calls=state['calls']

def error(cpu,errno):
    from native_allocator_os_fixture_ysm_265 import model as os_model
    a=os_model(cpu,'__errno_location');cpu.write_private(a,struct.pack('<i',errno));return 0xffffffff

def model(cpu,symbol):
    cpu.demand(isinstance(cpu,SyncGuardedCPU),'SYNC_BACKEND_REQUIRED');cpu.demand(cpu.sync_calls<1000000,'SYNC_CALL_BUDGET');a=cpu.reg('RDI');key=str(a)
    if symbol=='sem_init':
        cpu.demand(cpu.reg('RSI')==0,'UNMODELED_SHARED_SEMAPHORE');cpu.demand(a%8==0 and cpu.sync_storage(a,SIZE),'INVALID_SEMAPHORE_STORAGE',a,SIZE)
        old=cpu.sync_objects.get(key);cpu.demand(old is None or not old['active'],'SEMAPHORE_ALREADY_INITIALIZED',a)
        cpu.demand(all(int(k)==a or not (int(k)<a+SIZE and a<int(k)+SIZE) for k in cpu.sync_objects),'OVERLAPPING_SEMAPHORE',a)
        value=cpu.reg('RDX')&0xffffffff
        if value>MAX_VALUE:result=error(cpu,22)
        else:
            cpu.demand(old is not None or len(cpu.sync_objects)<1024,'SYNC_OBJECT_BUDGET');cpu.sync_objects[key]={'kind':'semaphore','size':SIZE,'value':value,'active':True};result=0
    else:
        obj=cpu.sync_objects.get(key);cpu.demand(obj is not None and obj['active'],'UNKNOWN_OR_DESTROYED_SEMAPHORE',a)
        if symbol=='sem_post':
            if obj['value']==MAX_VALUE:result=error(cpu,75)
            else:obj['value']+=1;result=0
        elif symbol in ('sem_wait','sem_trywait'):
            if obj['value']:obj['value']-=1;result=0
            elif symbol=='sem_trywait':result=error(cpu,11)
            else:cpu.demand(False,'VIRTUAL_SEMAPHORE_WOULD_BLOCK',a)
        elif symbol=='sem_destroy':obj['active']=False;result=0
        else:raise ValueError('Unknown semaphore model')
    cpu.sync_calls+=1;cpu.emit('VIRTUAL_SEMAPHORE',symbol,f'address={a:x}',f'result={result:x}','opaque_storage=true','single_virtual_thread=true','host_sync_called=false');return result
