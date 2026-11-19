import struct, sys
iso = sys.argv[1]
f = open(iso, 'rb')
def rd(lba, n=2048): f.seek(lba*2048); return f.read(n)
pvd = rd(16)
root = pvd[156:190]
rlba = struct.unpack('<I', root[2:6])[0]; rlen = struct.unpack('<I', root[10:14])[0]
def walk(lba, ln, path, out):
    data = b''.join(rd(lba + i) for i in range((ln + 2047)//2048))
    p = 0
    while p < len(data):
        l = data[p]
        if l == 0:
            p = (p//2048 + 1)*2048
            if p >= len(data): break
            continue
        rec = data[p:p+l]
        elba = struct.unpack('<I', rec[2:6])[0]; elen = struct.unpack('<I', rec[10:14])[0]
        flags = rec[25]; nl = rec[32]; name = rec[33:33+nl]
        p += l
        if name in (b'\x00', b'\x01'): continue
        name = name.decode('latin1').split(';')[0]
        full = path + '/' + name
        if flags & 2: walk(elba, elen, full, out)
        else: out.append((full, elba, elen))
out = []
walk(rlba, rlen, '', out)
for n, l, s in sorted(out, key=lambda x: x[1]):
    print(f"{s:>12} {l*2048:>12} {n}")
