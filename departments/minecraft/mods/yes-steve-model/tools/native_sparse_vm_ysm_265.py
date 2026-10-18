"""Bounded sparse anonymous guest memory: large address reservations, small backing cap.

Never asks the host to reserve the requested guest size. Only touched 4KiB pages
are mapped into Unicorn, with at most8MiB of guest page backing. No sparse code
execution. Every committed store is checked against its own expected-page ledger.
"""
import copy,hashlib
from unicorn import UC_MEM_READ_UNMAPPED,UC_MEM_WRITE_UNMAPPED,UC_MEM_READ_PROT,UC_MEM_WRITE_PROT,UC_MEM_FETCH_UNMAPPED,UC_MEM_FETCH_PROT
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_unicorn_guarded_ysm_265 import ModelHalt
PAGE=4096;BASE=0x400000000000;LIMIT=0x600000000000
class SparseGuardedCPU(ShadowGuardedCPU):
    MAX_PAGES=2048;MAX_VIRTUAL=1<<40;MAX_REGIONS=64;MAX_VM_WRITE_BYTES=64<<20;MAX_VM_EVENTS=1000000
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.vm_regions=[];self.vm_pages={};self.vm_next=BASE;self.vm_write_events=self.vm_write_bytes=self.vm_map_calls=self.vm_unmap_calls=self.vm_protect_calls=0
        self.os_fixture={'errno_block':0,'errno_input':2,'entropy_offset':0,'entropy_open':False,'entropy_seed':'ysm265-isolated-snmalloc-fixture-v1','monotonic_ns':0,'clock_calls':0,'calls':0,'names':[],'advice':[]}
        self.emit('SPARSE_SCENARIO_INPUTS','page_size=4096',f'physical_page_cap={self.MAX_PAGES}',f'virtual_bytes_cap={self.MAX_VIRTUAL}','errno_initial=2','entropy_seed=ysm265-isolated-snmalloc-fixture-v1','anonymous_initial_bytes=zero','mmap_address_policy=deterministic-power-of-two-aligned','host_os_calls=false')
    def vm_cover(self,a,n,access=0):
        if n<=0 or a<BASE or a+n>LIMIT:return None
        cursor=a;out=[]
        for r in sorted(self.vm_regions,key=lambda r:r['start']):
            if r['end']<=cursor:continue
            if r['start']>cursor:return None
            if access and not r['prot']&access:return None
            out.append(r);cursor=min(a+n,r['end'])
            if cursor==a+n:return out
        return None
    def vm_overlap(self,a,n):return any(r['start']<a+n and a<r['end'] for r in self.vm_regions)
    def vm_reserved(self):return sum(r['end']-r['start'] for r in self.vm_regions)
    def vm_map(self,n,prot=3):
        size=(n+PAGE-1)&~(PAGE-1);self.demand(0<n<=1<<38 and prot in (0,1,3),'UNMODELED_ANONYMOUS_MAPPING',n)
        alignment=max(PAGE,1<<(size-1).bit_length());start=(self.vm_next+alignment-1)&~(alignment-1)
        self.demand(len(self.vm_regions)<self.MAX_REGIONS and self.vm_reserved()+size<=self.MAX_VIRTUAL and start+size<=LIMIT,'SPARSE_VIRTUAL_BUDGET',start,size)
        self.vm_regions.append({'start':start,'end':start+size,'prot':prot});self.vm_next=start+size+PAGE;self.vm_map_calls+=1
        self.emit('VIRTUAL_ANON_RESERVATION',f'address={start:x}',f'bytes={size}',f'prot={prot}','host_large_reservation=false','materialized_pages=0');return start
    def vm_materialize(self,a,n,access):
        cover=self.vm_cover(a,n,access)
        if cover is None:self.fail('SPARSE_PERMISSION_OR_RANGE',a,n);return False
        first=a&~(PAGE-1);end=(a+n+PAGE-1)&~(PAGE-1)
        if (end-first)//PAGE>self.MAX_PAGES:self.fail('SPARSE_BACKING_BUDGET',a,n);return False
        pages=range(first,end,PAGE);new=[p for p in pages if p not in self.vm_pages]
        if len(self.vm_pages)+len(new)>self.MAX_PAGES:self.fail('SPARSE_BACKING_BUDGET',a,n);return False
        for page in new:
            region=next(r for r in cover if r['start']<=page<r['end']);self.uc.mem_map(page,PAGE,region['prot']);self.uc.mem_write(page,bytes(PAGE));self.vm_pages[page]=bytearray(PAGE)
        return True
    def unknown(self,a,n):
        if self.vm_cover(a,n) is not None:return None
        return super().unknown(a,n)
    def read_known(self,a,n):
        if self.vm_overlap(a,n):
            if not self.vm_materialize(a,n,1):raise ModelHalt(self.stop['reason'])
            return bytes(self.uc.mem_read(a,n))
        return super().read_known(a,n)
    def _read(self,uc,access,a,n,value,user):
        if self.vm_overlap(a,n):self.vm_materialize(a,n,1);return
        super()._read(uc,access,a,n,value,user)
    def _write(self,uc,access,a,n,value,user):
        if not self.vm_overlap(a,n):return super()._write(uc,access,a,n,value,user)
        # Preserve existing mapped bytes even when the candidate is out of range.
        for at in range(a,a+n):
            if (at&~(PAGE-1)) in self.vm_pages:self.journal.append((at,bytes(uc.mem_read(at,1))))
        pending=[(x,z) for x,z in self.writes if self.vm_overlap(x,z)]
        if self.vm_write_events+len(pending)+1>self.MAX_VM_EVENTS or self.vm_write_bytes+sum(z for x,z in pending)+n>self.MAX_VM_WRITE_BYTES:self.fail('SPARSE_WRITE_BUDGET',a,n);return
        if not self.vm_materialize(a,n,2):return
        self.journal.append((a,bytes(uc.mem_read(a,n))));self.writes.append((a,n))
    def _invalid(self,uc,access,a,n,value,user):
        if self.stop:return False
        if self.vm_overlap(a,n):
            if access in (UC_MEM_FETCH_UNMAPPED,UC_MEM_FETCH_PROT):self.fail('SPARSE_EXECUTION_BLOCKED',a,n);return False
            if access in (UC_MEM_READ_UNMAPPED,UC_MEM_READ_PROT):return self.vm_materialize(a,n,1)
            if access in (UC_MEM_WRITE_UNMAPPED,UC_MEM_WRITE_PROT):return self.vm_materialize(a,n,2)
        return super()._invalid(uc,access,a,n,value,user)
    def commit_write(self,a,n):
        if not self.vm_overlap(a,n):return super().commit_write(a,n)
        data=bytes(self.uc.mem_read(a,n));cursor=0
        while cursor<n:
            at=a+cursor;page=at&~(PAGE-1);length=min(n-cursor,PAGE-(at-page));self.vm_pages[page][at-page:at-page+length]=data[cursor:cursor+length];cursor+=length
        self.vm_write_events+=1;self.vm_write_bytes+=n;self.emit('SPARSE_COMMITTED_WRITE',f'pc={self.pc:x}',f'address={a:x}',f'size={n}',f'sha256={hashlib.sha256(data).hexdigest()}')
    def write_model_memory(self,a,data):
        if not data:return
        if not self.vm_overlap(a,len(data)):return super().write_model_memory(a,data)
        self.demand(self.vm_write_events+1<=self.MAX_VM_EVENTS and self.vm_write_bytes+len(data)<=self.MAX_VM_WRITE_BYTES,'SPARSE_WRITE_BUDGET',a,len(data))
        if not self.vm_materialize(a,len(data),2):raise ModelHalt(self.stop['reason'])
        self.uc.mem_write(a,data);self.commit_write(a,len(data))
    def model(self,kind):
        if kind=='copy' and (self.vm_overlap(self.reg('RSI'),1) or self.vm_overlap(self.reg('RDI'),1)):
            self.modeled_copies+=1;n=self.reg('RCX')
            if n==0:self.reg('RIP',self.pc+2);return
            src,dst=self.reg('RSI'),self.reg('RDI');data=self.read_known(src,1);self.write_model_memory(dst,data);step=-1 if self.reg('DF') else 1;self.reg('RSI',src+step);self.reg('RDI',dst+step);self.reg('RCX',n-1);self.reg('RIP',self.pc);return
        super().model(kind)
    def vm_change(self,a,n,prot=None,remove=False):
        end=(a+n+PAGE-1)&~(PAGE-1);self.demand(a%PAGE==0 and n>0 and self.vm_cover(a,end-a) is not None,'SPARSE_RANGE_CHANGE_REJECTED',a,n)
        self.demand(remove or prot in (0,1,3),'SPARSE_EXECUTABLE_PERMISSION_REJECTED',a,n)
        updated=[]
        for r in self.vm_regions:
            if r['end']<=a or end<=r['start']:updated.append(r);continue
            if r['start']<a:updated.append({**r,'end':a})
            if not remove:updated.append({'start':max(a,r['start']),'end':min(end,r['end']),'prot':prot})
            if end<r['end']:updated.append({**r,'start':end})
        merged=[]
        for r in sorted(updated,key=lambda r:r['start']):
            if merged and merged[-1]['end']==r['start'] and merged[-1]['prot']==r['prot']:merged[-1]['end']=r['end']
            else:merged.append(r)
        self.demand(len(merged)<=self.MAX_REGIONS,'SPARSE_REGION_BUDGET')
        for page in list(self.vm_pages):
            if a<=page<end:
                if remove:self.uc.mem_unmap(page,PAGE);del self.vm_pages[page]
                else:self.uc.mem_protect(page,PAGE,prot)
        self.vm_regions=merged
        if remove:self.vm_unmap_calls+=1
        else:self.vm_protect_calls+=1
        self.emit('VIRTUAL_ANON_RANGE_CHANGE',f'address={a:x}',f'bytes={end-a}',f'remove={remove}',f'prot={prot}','host_os_call=false')
    def vm_advice(self,a,n,advice):
        self.demand(a%PAGE==0 and self.vm_cover(a,(n+PAGE-1)&~(PAGE-1)) is not None and advice in (4,8,16,17),'UNMODELED_MEMORY_ADVICE',a,n)
        self.demand(len(self.os_fixture['advice'])<4096,'MEMORY_ADVICE_BUDGET')
        if advice==4:
            self.demand(a%PAGE==0,'UNALIGNED_DISCARD',a)
            for page in list(self.vm_pages):
                if a<=page<a+n:
                    self.uc.mem_write(page,bytes(PAGE));self.vm_pages[page][:]=bytes(PAGE)
        self.os_fixture['advice'].append([a,n,advice]);self.emit('VIRTUAL_MEMORY_ADVICE',f'address={a:x}',f'bytes={n}',f'advice={advice}','host_os_call=false')
    def expected_sparse_matches(self):return all(bytes(self.uc.mem_read(a,PAGE))==v for a,v in self.vm_pages.items())
    def report_preservation(self):
        ok=self.expected_sparse_matches();self.emit('SPARSE_PRESERVATION',f'ledger_matches={ok}',f'virtual_reserved_bytes={self.vm_reserved()}',f'materialized_pages={len(self.vm_pages)}',f'guest_page_backing_bytes={PAGE*len(self.vm_pages)}',f'write_events={self.vm_write_events}','host_large_reservation=false')
        if not ok:raise AssertionError('Unaccounted sparse-memory mutation')
        super().report_preservation()
    def capture_sparse(self):
        from native_guarded_checkpoint_ysm_265 import pack
        if not self.expected_sparse_matches():raise ValueError('Invalid sparse checkpoint state')
        return {'regions':self.vm_regions,'next':self.vm_next,'pages':{str(a):pack(v) for a,v in self.vm_pages.items()},'write_events':self.vm_write_events,'write_bytes':self.vm_write_bytes,'map_calls':self.vm_map_calls,'unmap_calls':self.vm_unmap_calls,'protect_calls':self.vm_protect_calls,'os_fixture':self.os_fixture}
    def restore_sparse(self,s):
        from native_guarded_checkpoint_ysm_265 import unpack
        if self.vm_regions or self.vm_pages:raise ValueError('Sparse restore requires fresh state')
        regions=s['regions'];pages=s['pages'];previous=BASE
        if len(regions)>self.MAX_REGIONS or len(pages)>self.MAX_PAGES:raise ValueError('Sparse checkpoint resource limit')
        for key,limit in [('write_events',self.MAX_VM_EVENTS),('write_bytes',self.MAX_VM_WRITE_BYTES),('map_calls',self.MAX_VM_EVENTS),('unmap_calls',self.MAX_VM_EVENTS),('protect_calls',self.MAX_VM_EVENTS)]:
            if type(s[key]) is not int or not 0<=s[key]<=limit:raise ValueError('Invalid sparse checkpoint counter')
        os=copy.deepcopy(s['os_fixture']);os.setdefault('monotonic_ns',0);os.setdefault('clock_calls',0)
        if set(os)!=set(self.os_fixture) or type(os['entropy_open']) is not bool or type(os['entropy_offset']) is not int or not 0<=os['entropy_offset']<=4096 or os['entropy_seed']!=self.os_fixture['entropy_seed'] or os['errno_input']!=2:raise ValueError('Invalid allocator OS fixture')
        if type(os['clock_calls']) is not int or not 0<=os['clock_calls']<=self.MAX_VM_EVENTS or os['monotonic_ns']!=os['clock_calls']*1000000:raise ValueError('Invalid virtual clock fixture')
        if type(os['calls']) is not int or not 0<=os['calls']<=self.MAX_VM_EVENTS or len(os['names'])>4096 or len(os['advice'])>4096:raise ValueError('Invalid allocator OS budget')
        if os['errno_block'] and (not self.private_region(os['errno_block'],16) or not any(a==os['errno_block'] and n==16 for a,n in self.fixture_regions)):raise ValueError('Invalid errno fixture storage')
        for a,n,name in os['names']:
            if not BASE<=a<a+n<=LIMIT or name!='snmalloc':raise ValueError('Invalid VMA name metadata')
        for a,n,advice in os['advice']:
            if not BASE<=a<a+n<=LIMIT or a%PAGE or advice not in (4,8,16,17):raise ValueError('Invalid advice metadata')
        for r in sorted(regions,key=lambda r:r['start']):
            if not previous<=r['start']<r['end']<=LIMIT or r['start']%PAGE or r['end']%PAGE or r['prot'] not in (0,1,3):raise ValueError('Invalid sparse interval')
            previous=r['end']
        if sum(r['end']-r['start'] for r in regions)>self.MAX_VIRTUAL or not previous<=s['next']<=LIMIT:raise ValueError('Invalid virtual reservation state')
        decoded={}
        for key,value in pages.items():
            a=int(key);r=next((r for r in regions if r['start']<=a and a+PAGE<=r['end']),None)
            if a%PAGE or r is None:raise ValueError('Invalid sparse page')
            if a in decoded:raise ValueError('Duplicate sparse page')
            decoded[a]=(unpack(value,PAGE),r['prot'])
        self.vm_regions=copy.deepcopy(regions);self.vm_next=s['next']
        for a,(data,prot) in decoded.items():self.uc.mem_map(a,PAGE,prot);self.uc.mem_write(a,data);self.vm_pages[a]=bytearray(data)
        for attr,key in [('vm_write_events','write_events'),('vm_write_bytes','write_bytes'),('vm_map_calls','map_calls'),('vm_unmap_calls','unmap_calls'),('vm_protect_calls','protect_calls')]:setattr(self,attr,s[key])
        self.os_fixture=os
