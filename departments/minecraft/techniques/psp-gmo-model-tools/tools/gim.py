"""Sony GIM (MIG.00.1PSP) テクスチャ -> RGBA。
ブロック: u16 type, u16 pad, u32 size, u32 next, u32 data_off(=0x10)。
  0x02 root / 0x03 picture / 0x04 image / 0x05 palette / 0xff fileinfo
画像・パレットのヘッダ(データ先頭から):
  +0x04 u16 format  +0x06 u16 order(0=linear,1=PSPスウィズル) +0x08 w +0x0a h
  +0x0c bpp_align +0x0e pitch_align +0x10 height_align
  +0x18 offsets_off +0x1c images_off(ピクセル開始) +0x20 total_size
format: 0 RGB565, 1 RGBA5551, 2 RGBA4444, 3 RGBA8888, 4 IDX4, 5 IDX8, 6 IDX16, 7 IDX32
"""
import struct

BPP = {0: 16, 1: 16, 2: 16, 3: 32, 4: 4, 5: 8, 6: 16, 7: 32}


def _blocks(g, pos, end, out):
    while pos + 16 <= end:
        ty, _pad, sz, _nxt, _doff = struct.unpack_from('<HHIII', g, pos)
        if sz < 16:
            return
        if ty in (2, 3):
            _blocks(g, pos + 16, pos + sz, out)
        elif ty in (4, 5):
            out.setdefault(ty, []).append((pos, sz))
        pos += sz


def _plane(g, pos, sz):
    d = pos + 16
    fmt, order, w, h, _ba, pa, ha = struct.unpack_from('<7H', g, d + 4)
    img_off = struct.unpack_from('<I', g, d + 0x1c)[0]
    return dict(fmt=fmt, order=order, w=w, h=h, pitch_align=max(pa, 1), height_align=max(ha, 1),
                data=g[d + img_off: pos + sz])


def _linear(pl):
    """スウィズル解除して「行ごとに詰めた生バイト列」と行バイト数を返す。"""
    bpp = BPP[pl['fmt']]
    pitch_px = (pl['w'] + pl['pitch_align'] - 1) // pl['pitch_align'] * pl['pitch_align']
    row_bytes = pitch_px * bpp // 8
    hh = (pl['h'] + pl['height_align'] - 1) // pl['height_align'] * pl['height_align']
    data = pl['data']
    if pl['order'] == 1:
        out = bytearray(row_bytes * hh)
        bw = row_bytes // 16
        p = 0
        for by in range(hh // 8):
            for bx in range(bw):
                for r in range(8):
                    dst = (by * 8 + r) * row_bytes + bx * 16
                    out[dst:dst + 16] = data[p:p + 16]
                    p += 16
        data = bytes(out)
    return data, row_bytes


def _rgba(fmt, raw):
    if fmt == 3:
        return raw[0], raw[1], raw[2], raw[3]
    v = raw[0] | (raw[1] << 8)
    if fmt == 0:
        return ((v & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, ((v >> 11) & 31) * 255 // 31, 255)
    if fmt == 1:
        return ((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31, 255 if v & 0x8000 else 0)
    if fmt == 2:
        return ((v & 15) * 17, ((v >> 4) & 15) * 17, ((v >> 8) & 15) * 17, ((v >> 12) & 15) * 17)
    raise ValueError(fmt)


def decode(g):
    """GIMバイト列 -> (w, h, RGBA bytes)。"""
    if g[:11] != b'MIG.00.1PSP':
        raise ValueError('not GIM')
    blocks = {}
    _blocks(g, 16, len(g), blocks)
    img = _plane(g, *blocks[4][0])
    fmt, w, h = img['fmt'], img['w'], img['h']
    data, rowb = _linear(img)
    out = bytearray(w * h * 4)
    if fmt in (4, 5, 6, 7):
        pal = _plane(g, *blocks[5][0])
        pdata, _ = _linear(pal)
        pfmt = pal['fmt']
        psz = BPP[pfmt] // 8
        nent = pal['w'] * pal['h']
        table = [_rgba(pfmt, pdata[i * psz:(i + 1) * psz]) for i in range(nent)]
        for y in range(h):
            row = data[y * rowb:(y + 1) * rowb]
            for x in range(w):
                if fmt == 5:
                    i = row[x]
                elif fmt == 4:
                    i = (row[x >> 1] >> ((x & 1) * 4)) & 15
                elif fmt == 6:
                    i = row[x * 2] | (row[x * 2 + 1] << 8)
                else:
                    i = struct.unpack_from('<I', row, x * 4)[0]
                out[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes(table[i] if i < len(table) else (255, 0, 255, 255))
    else:
        bs = BPP[fmt] // 8
        for y in range(h):
            row = data[y * rowb:(y + 1) * rowb]
            for x in range(w):
                out[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes(_rgba(fmt, row[x * bs:(x + 1) * bs]))
    return w, h, bytes(out)


def to_png_bytes(g):
    """GIM -> (PNGバイト列, 半透明あり, 完全透明あり)。"""
    import io
    from PIL import Image
    w, h, rgba = decode(g)
    alphas = set(rgba[3::4])
    buf = io.BytesIO()
    Image.frombytes('RGBA', (w, h), rgba).save(buf, 'PNG')
    return buf.getvalue(), any(0 < a < 255 for a in alphas), 0 in alphas


def to_png(g, path):
    from PIL import Image
    w, h, rgba = decode(g)
    Image.frombytes('RGBA', (w, h), rgba).save(path)
    return w, h
