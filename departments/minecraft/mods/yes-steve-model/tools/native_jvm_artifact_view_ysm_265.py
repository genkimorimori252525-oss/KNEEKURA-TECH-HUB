"""Read-only static JVM ELF view. Writable runtime data stays unknown; no JVM code executes."""
import struct
from unicorn import UC_PROT_READ
from native_export_backing_ysm_265 import regions
BASE=0x7b0000000000
class JvmArtifactView:
    def __init__(self,cpu,data):
        self.data=data;self.ranges=[];self.known=[];self.expected=[];rs=regions(data)
        if not rs or sum(r['memory_size'] for r in rs)>64*1024*1024:raise ValueError('JVM artifact mapping limit')
        pages=set()
        for r in rs:
            a=BASE+r['address'];n=r['memory_size'];z=r['file_size'];offset=r['file_offset']
            if not 0<=z<=n or offset+z>len(data) or a+n>=BASE+128*1024*1024:raise ValueError('Invalid JVM load segment')
            if n and any(lo<a+n and a<hi for lo,hi in self.ranges):raise ValueError('Overlapping JVM load segments are unsupported')
            self.ranges.append((a,a+n));pages.update(range(a&~4095,(a+n+4095)&~4095,4096))
            if not r['flags']&2:self.known.append((a,a+z))
        runs=[]
        for page in sorted(pages):
            if runs and runs[-1][1]==page:runs[-1][1]+=4096
            else:runs.append([page,page+4096])
        for a,b in runs:cpu.uc.mem_map(a,b-a,UC_PROT_READ)
        for r in rs:
            a=BASE+r['address'];value=data[r['file_offset']:r['file_offset']+r['file_size']]+bytes(r['memory_size']-r['file_size']);cpu.uc.mem_write(a,value);self.expected.append((a,value))
        self.phoff=struct.unpack_from('<Q',data,32)[0];self.phnum=struct.unpack_from('<H',data,56)[0]
        if struct.unpack_from('<H',data,54)[0]!=56 or not 0<self.phnum<=256 or self.phoff+56*self.phnum>len(data):raise ValueError('Invalid JVM program headers')
    def hit(self,a,n):return any(lo<a+n and a<hi for lo,hi in self.ranges)
    def unknown(self,a,n):
        if any(lo<=a and a+n<=hi for lo,hi in self.known):return None
        return next((at for at in range(a,a+n) if not any(lo<=at<hi for lo,hi in self.known)),None)
    def unchanged(self,cpu):return all(bytes(cpu.uc.mem_read(a,len(v)))==v for a,v in self.expected)
    def _symbols(self):
        """Parse bounded ELF metadata once; static locals never become exports."""
        if getattr(self, '_symbol_cache', None) is not None:
            return self._symbol_cache
        data=self.data
        if len(data)<64:raise ValueError('Truncated JVM ELF header')
        offset=struct.unpack_from('<Q',data,40)[0];size,count=struct.unpack_from('<HH',data,58)
        if size!=64 or not 0<count<=4096 or offset+size*count>len(data):raise ValueError('Unrecognized JVM section table')
        sections=[struct.unpack_from('<IIQQQQIIQQ',data,offset+i*size) for i in range(count)]
        cache={11:{},2:{}};names_at={};total=0
        for section in sections:
            table_kind=section[1]
            if table_kind not in cache:continue
            start,length,link,entry=section[4],section[5],section[6],section[9]
            total+=length//24
            if entry!=24 or length%24 or total>1000000 or start+length>len(data) or link>=count:raise ValueError('Invalid JVM symbols')
            strings=sections[link]
            if strings[1]!=3 or strings[4]+strings[5]>len(data):raise ValueError('Invalid JVM symbol strings')
            names=data[strings[4]:strings[4]+strings[5]]
            for at in range(start,start+length,24):
                n,info,other,index,value,nbytes=struct.unpack_from('<IBBHQQ',data,at)
                if n>=len(names):raise ValueError('Invalid symbol string offset')
                end=names.find(b'\0',n,min(len(names),n+65537))
                if end<0:raise ValueError('Unterminated or oversized JVM symbol')
                if not index or index>=0xff00:continue
                if index>=count:raise ValueError('Invalid JVM symbol section')
                kind=info&15;binding=info>>4
                if table_kind==11:
                    if binding not in (1,2) or other&3 not in (0,3) or kind not in (1,2):continue
                elif binding!=0 or kind!=2:continue
                target=sections[index];extent=max(1,nbytes)
                if not target[2]&2 or (kind==2 and not target[2]&4):continue
                if not (target[3]<=value and value+extent<=target[3]+target[5]) or not any(lo<=BASE+value and BASE+value+extent<=hi for lo,hi in self.ranges):
                    raise ValueError('Unsupported JVM symbol kind/range')
                name=names[n:end]
                record=(BASE+value,kind,nbytes)
                cache[table_kind].setdefault(name,set()).add(record)
                # dladdr names must refer to actual mapped, known ELF bytes.
                name_address=BASE+strings[3]+n
                if table_kind==11 and strings[2]&2 and self.unknown(name_address,end-n+1) is None:
                    rs=regions(data)
                    if any(r['address']<=strings[3]+n and strings[3]+end+1<=r['address']+r['file_size'] and r['file_offset']+(strings[3]+n-r['address'])==strings[4]+n for r in rs):
                        names_at.setdefault((name,record),set()).add(name_address)
        self._symbol_cache=cache;self._symbol_names_at=names_at
        return cache

    def _lookup(self,name,table_kind):
        matches=self._symbols()[table_kind].get(name.encode('ascii'),set())
        if len(matches)!=1:raise ValueError('JVM symbol absent or ambiguous in pinned artifact')
        address,kind,size=next(iter(matches))
        return {'address':address,'kind':kind,'size':size}

    def symbol(self,name):
        """Defined public/weak dynamic symbol; preserve the original result shape."""
        return self._lookup(name,11)

    def local_function(self,name):
        """Defined STB_LOCAL/STT_FUNC from .symtab, not a dynamic export."""
        return self._lookup(name,2)

    def dynamic_symbol_containing(self,address):
        """Unique containing export only; never guess nearest/static symbols."""
        found=[]
        for name,records in self._symbols()[11].items():
            for record in records:
                start,kind,size=record
                if start<=address<start+max(1,size):
                    if len(records)!=1:return None
                    found.append((name,record))
        if len(found)!=1:return None
        name,record=found[0];start,kind,size=record
        try:decoded=name.decode('ascii')
        except UnicodeDecodeError:return None
        result={'name':decoded,'address':start,'kind':kind,'size':size}
        positions=self._symbol_names_at.get((name,record),set())
        if len(positions)==1:result['name_address']=next(iter(positions))
        return result
