"""GMOのチャンク木をダンプする（解析用）。python gmo_tree.py <gmo> [最大深さ]"""
import struct, sys

def walk(d, pos, end, depth, maxd, out):
    while pos + 8 <= end:
        t, hs, ds = struct.unpack('<HHI', d[pos:pos+8])
        leaf = bool(t & 0x8000)
        if leaf:
            hs = 8
        if hs < 8 or pos + ds > end or ds < hs:
            out.append(f"{'  '*depth}!! bad chunk @0x{pos:x} t=0x{t:04x} hs={hs} ds={ds}")
            return
        extra = d[pos+8:pos+hs] if not leaf else d[pos+8:pos+min(ds, 8+32)]
        out.append(f"{'  '*depth}@0x{pos:06x} type=0x{t:04x} hs={hs} ds={ds} {'DATA' if leaf else 'hdr'}={extra.hex(' ')}")
        if not leaf and depth + 1 < maxd and ds > hs:
            walk(d, pos + hs, pos + ds, depth + 1, maxd, out)
        pos += ds

if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    maxd = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    assert d[:11] == b'OMG.00.1PSP', d[:12]
    out = []
    walk(d, 16, len(d), 0, maxd, out)
    print('\n'.join(out))
