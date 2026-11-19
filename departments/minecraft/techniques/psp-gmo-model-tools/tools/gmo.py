"""Sony GMO (OMG.00.1PSP) モデルの読み取り。

構造は Rich Whitehouse の Dissidia GMO 文書と、本作のデータ実測から。
  チャンク: u16 type, u16 header_size, u32 total_size（total は先頭8バイトを含む）
  type に 0x8000 が立つものは「属性」(リーフ。ヘッダ長0＝データは+8から)
  参照値: u32、下位12bitが番号（例: 0x00071000 = 配列#0）
"""
import struct

HDR = struct.Struct('<HHI')


class Chunk:
    __slots__ = ('type', 'off', 'hs', 'size', 'children', 'leaf', 'data', 'buf')

    def __init__(self, buf, off, type_, hs, size):
        self.buf, self.off, self.type, self.hs, self.size = buf, off, type_, hs, size
        self.leaf = bool(type_ & 0x8000)
        if self.leaf:
            self.hs = 8
        self.children = []
        self.data = b''

    @property
    def name(self):
        """ヘッダ内の名前（0x0003〜0x000cの容器チャンク）。"""
        raw = self.buf[self.off + 16: self.off + self.hs]
        return raw.split(b'\0')[0].decode('ascii', 'replace')

    @property
    def payload(self):
        """属性チャンクの中身。"""
        return self.buf[self.off + 8: self.off + self.size]

    @property
    def body(self):
        """容器チャンクのヘッダの後ろ（頂点配列などはここから生データ）。"""
        return self.buf[self.off + self.hs: self.off + self.size]

    def kids(self, t):
        return [c for c in self.children if c.type == t]

    def kid(self, t):
        for c in self.children:
            if c.type == t:
                return c
        return None


def parse(buf, pos=16, end=None):
    end = len(buf) if end is None else end
    out = []
    while pos + 8 <= end:
        t, hs, ds = HDR.unpack_from(buf, pos)
        if ds < 8 or pos + ds > end:
            break
        c = Chunk(buf, pos, t, hs, ds)
        if not c.leaf and ds > c.hs >= 8 and t in (0x02, 0x03, 0x04, 0x05, 0x06, 0x08, 0x09, 0x0a, 0x0b):
            c.children = parse(buf, pos + c.hs, pos + ds)
        out.append(c)
        pos += ds
    return out


def ref(v):
    return v & 0xfff


# ---- PSP GE 頂点レイアウト ---------------------------------------------------
_SZ = {1: 1, 2: 2, 3: 4}


def ge_layout(fmt):
    """vtype -> dict(stride, weights(off,type,count), tc, color, normal, pos, morphs)。
    各要素は (offset, type)。順序: 重み, UV, 色, 法線, 位置。"""
    off, amax = 0, 1

    def place(size, align):
        nonlocal off, amax
        off = (off + align - 1) & ~(align - 1)
        at = off
        off += size
        amax = max(amax, align)
        return at

    lay = {}
    wt, wc = (fmt >> 9) & 3, ((fmt >> 14) & 7) + 1
    if wt:
        lay['weights'] = (place(_SZ[wt] * wc, _SZ[wt]), wt, wc)
    tt = fmt & 3
    if tt:
        lay['tc'] = (place(_SZ[tt] * 2, _SZ[tt]), tt)
    ct = (fmt >> 2) & 7
    if 4 <= ct <= 6:
        lay['color'] = (place(2, 2), ct)
    elif ct == 7:
        lay['color'] = (place(4, 4), ct)
    nt = (fmt >> 5) & 3
    if nt:
        lay['normal'] = (place(_SZ[nt] * 3, _SZ[nt]), nt)
    pt = (fmt >> 7) & 3
    if pt:
        lay['pos'] = (place(_SZ[pt] * 3, _SZ[pt]), pt)
    lay['stride'] = (off + amax - 1) & ~(amax - 1)
    lay['morphs'] = ((fmt >> 18) & 7) + 1
    lay['index'] = (fmt >> 11) & 3
    return lay
