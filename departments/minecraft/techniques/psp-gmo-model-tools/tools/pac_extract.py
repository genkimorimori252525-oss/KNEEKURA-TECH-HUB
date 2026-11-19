"""本作の .pac（u16 件数, u16 ?, u32 総サイズ, 以降 name[32]+offset(u32)+size(u32) × 件数）を展開する。
使い方: python pac_extract.py <pac> <出力先>
"""
import os, struct, sys

def read_pac(data):
    n, _, total = struct.unpack('<HHI', data[:8])
    out = []
    for i in range(n):
        p = 8 + i * 40
        name = data[p:p+32].split(b'\0')[0].decode('ascii', 'replace')
        off, size = struct.unpack('<II', data[p+32:p+40])
        out.append((name, off, size))
    return total, out

if __name__ == '__main__':
    src, outdir = sys.argv[1], sys.argv[2]
    data = open(src, 'rb').read()
    total, ents = read_pac(data)
    if total != len(data):
        print(f"warn: header total {total} != file {len(data)}", file=sys.stderr)
    os.makedirs(outdir, exist_ok=True)
    for name, off, size in ents:
        chunk = data[off:off+size]
        if len(chunk) != size:
            print(f"warn: {name} truncated", file=sys.stderr)
        open(os.path.join(outdir, name), 'wb').write(chunk)
        print(f"{size:>9} @0x{off:06x} {name}  magic={chunk[:12]!r}")
