import struct, sys

def parse_utf(buf):
    assert buf[:4] == b'@UTF', buf[:4]
    size = struct.unpack('>I', buf[4:8])[0]
    b = buf[8:8+size]
    # note: ">I I I I H H I" -> 4+4+4+4+2+2+4 = 24 (b[0] is actually 'unk' ver/enc)
    # Actual layout: unk(2) rows_off(2)?? -> use the known: version(2) rows_offset(2) str_offset(4) data_offset(4) name(4) cols(2) rowsize(2) rows(4)
    rows_off, str_off, data_off, name_off, ncols, row_w, nrows = struct.unpack('>IIIIHHI', b[0:24])
    def cstr(o):
        s = b[str_off+o:]
        return s[:s.index(b'\0')].decode('utf-8', 'replace')
    p = 24
    cols = []
    for _ in range(ncols):
        flag = b[p]; p += 1
        nameo = struct.unpack('>I', b[p:p+4])[0]; p += 4
        st = flag & 0xF0; ty = flag & 0x0F
        const = None
        if st == 0x30:
            const, p = readval(b, p, ty, str_off, data_off, cstr)
        cols.append((cstr(nameo), st, ty, const))
    rows = []
    for r in range(nrows):
        p = rows_off + r*row_w
        row = {}
        for (n, st, ty, const) in cols:
            if st == 0x30: row[n] = const
            elif st == 0x10: row[n] = None
            else:
                v, p = readval(b, p, ty, str_off, data_off, cstr)
                row[n] = v
        rows.append(row)
    return rows

def readval(b, p, ty, str_off, data_off, cstr):
    if ty == 0: return b[p], p+1
    if ty == 1: return struct.unpack('>b', b[p:p+1])[0], p+1
    if ty == 2: return struct.unpack('>H', b[p:p+2])[0], p+2
    if ty == 3: return struct.unpack('>h', b[p:p+2])[0], p+2
    if ty == 4: return struct.unpack('>I', b[p:p+4])[0], p+4
    if ty == 5: return struct.unpack('>i', b[p:p+4])[0], p+4
    if ty == 6: return struct.unpack('>Q', b[p:p+8])[0], p+8
    if ty == 7: return struct.unpack('>q', b[p:p+8])[0], p+8
    if ty == 8: return struct.unpack('>f', b[p:p+4])[0], p+4
    if ty == 0xA: return cstr(struct.unpack('>I', b[p:p+4])[0]), p+4
    if ty == 0xB:
        o, s = struct.unpack('>II', b[p:p+8]); return (data_off+o, s), p+8
    raise ValueError(ty)

def toc(path):
    f = open(path, 'rb')
    f.seek(0); h = f.read(16)
    assert h[:4] == b'CPK ', h[:4]
    sz = struct.unpack('<Q', h[8:16])[0]
    f.seek(16); hdr = parse_utf(f.read(sz))
    hdr = hdr[0]
    toc_off = hdr['TocOffset']; content_off = hdr.get('ContentOffset')
    f.seek(toc_off); t = f.read(16)
    assert t[:4] == b'TOC ', t[:4]
    tsz = struct.unpack('<Q', t[8:16])[0]
    rows = parse_utf(f.read(tsz))
    return hdr, rows, toc_off, content_off, f

if __name__ == '__main__':
    hdr, rows, toc_off, content_off, f = toc(sys.argv[1])
    print({k: v for k, v in hdr.items() if not isinstance(v, tuple)}, file=sys.stderr)
    for r in rows:
        off = r['FileOffset'] + (toc_off if content_off is None or toc_off < content_off else content_off)
        print(f"{r['FileSize']}\t{r['ExtractSize']}\t{r['DirName']}/{r['FileName']}")
