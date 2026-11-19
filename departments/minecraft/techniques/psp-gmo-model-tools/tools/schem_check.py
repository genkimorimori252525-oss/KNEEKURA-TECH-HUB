"""Sponge Schematic v2 (.schem) の独立した検査（書き出し側のコードは使わない）。

使い方: python schem_check.py <file.schem> [--materials <file.materials.tsv>] [--allow <ブロックID...>]
確認すること: gzip/NBT の構造、必須タグ、パレットの連続性、BlockData の varint 復号、
              全セルが範囲内、非空気セル数 = 材料表、（指定時）パレットが許可リスト内。
"""
import argparse, gzip, struct, sys


class Reader:
    def __init__(self, data):
        self.d, self.p = data, 0

    def take(self, n):
        if self.p + n > len(self.d):
            raise ValueError('NBT が途中で終わっている')
        b = self.d[self.p:self.p + n]
        self.p += n
        return b

    def string(self):
        return self.take(struct.unpack('>H', self.take(2))[0]).decode('utf-8')

    def payload(self, t):
        if t == 1:
            return struct.unpack('>b', self.take(1))[0]
        if t == 2:
            return struct.unpack('>h', self.take(2))[0]
        if t == 3:
            return struct.unpack('>i', self.take(4))[0]
        if t == 4:
            return struct.unpack('>q', self.take(8))[0]
        if t == 5:
            return struct.unpack('>f', self.take(4))[0]
        if t == 6:
            return struct.unpack('>d', self.take(8))[0]
        if t == 7:
            n = struct.unpack('>i', self.take(4))[0]
            if n < 0:
                raise ValueError('負の配列長')
            return self.take(n)
        if t == 8:
            return self.string()
        if t == 9:
            et = self.take(1)[0]
            n = struct.unpack('>i', self.take(4))[0]
            return [self.payload(et) for _ in range(n)]
        if t == 10:
            out = {}
            while True:
                tt = self.take(1)[0]
                if tt == 0:
                    return out
                key = self.string()  # 代入は右辺が先に評価されるので、名前を先に読む
                out[key] = self.payload(tt)
        if t == 11:
            n = struct.unpack('>i', self.take(4))[0]
            return list(struct.unpack('>%di' % n, self.take(4 * n)))
        raise ValueError(f'未知のタグ型 {t}')


def read_nbt(raw):
    r = Reader(raw)
    t = r.take(1)[0]
    if t != 10:
        raise ValueError('ルートが Compound ではない')
    name = r.string()
    return name, r.payload(10), r.p == len(raw)


def decode_varints(data):
    out, i = [], 0
    while i < len(data):
        v = shift = 0
        while True:
            if i >= len(data):
                raise ValueError('varint が途中で終わっている')
            b = data[i]
            i += 1
            v |= (b & 0x7F) << shift
            if not b & 0x80:
                break
            shift += 7
            if shift > 35:
                raise ValueError('varint が長すぎる')
        out.append(v)
    return out


def check(path, materials=None, allow=None):
    problems, info = [], {}
    raw = gzip.open(path, 'rb').read()
    name, root, fully_consumed = read_nbt(raw)
    if not fully_consumed:
        problems.append('NBT の後ろに余分なバイトがある')
    info['root'] = name
    for k in ('Version', 'DataVersion', 'Width', 'Height', 'Length', 'Palette', 'PaletteMax', 'BlockData', 'Offset'):
        if k not in root:
            problems.append(f'必須タグ {k} がない')
    if problems:
        return info, problems
    info.update(version=root['Version'], data_version=root['DataVersion'])
    if root['Version'] != 2:
        problems.append(f'Version={root["Version"]}（2 のはず）')
    w, h, l = root['Width'] & 0xFFFF, root['Height'] & 0xFFFF, root['Length'] & 0xFFFF
    info['dims'] = (w, h, l)
    pal = root['Palette']
    ids = sorted(pal.values())
    if ids != list(range(len(ids))):
        problems.append('パレットの番号が 0..N-1 で連続していない')
    if root['PaletteMax'] != len(pal):
        problems.append(f'PaletteMax={root["PaletteMax"]} と実数 {len(pal)} が違う')
    if pal.get('minecraft:air') != 0:
        problems.append('minecraft:air が 0 番ではない')
    cells = decode_varints(root['BlockData'])
    if len(cells) != w * h * l:
        problems.append(f'セル数 {len(cells)} が {w}x{h}x{l}={w * h * l} と違う')
    if cells and max(cells) >= len(pal):
        problems.append('パレット範囲外の番号がある')
    inv = {v: k for k, v in pal.items()}
    counts = {}
    for c in cells:
        if c:
            counts[inv.get(c, '?')] = counts.get(inv.get(c, '?'), 0) + 1
    info['solid'] = sum(counts.values())
    info['kinds'] = len(counts)
    if allow is not None:
        bad = sorted(set(pal) - set(allow) - {'minecraft:air'})
        if bad:
            problems.append(f'許可リスト外のブロック: {bad}')
    if materials:
        exp = {}
        for ln in open(materials, encoding='utf-8').read().splitlines()[1:]:
            b, n = ln.split('\t')
            exp[b] = int(n)
        if exp != counts:
            problems.append('材料表と BlockData の集計が一致しない')
    return info, problems


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('schem')
    ap.add_argument('--materials')
    a = ap.parse_args()
    info, problems = check(a.schem, a.materials)
    print(info)
    if problems:
        print('NG:')
        for p in problems:
            print('  -', p)
        sys.exit(1)
    print('OK')
