"""OBJ(+MTL+PNG) -> Minecraft 1.20.1 用 Sponge Schematic v2（.schem）。表面だけの殻にするボクセライザ。

使い方:
  python obj2schem.py <model.obj> <out.schem> [--size 128] [--exclude TR_pattern] [--preview out_prefix]

仕組み:
  1. 三角形を面積に応じて細かくサンプルし、テクスチャ色を拾って、入ったボクセルに平均する（αが低い所は飛ばす）。
     中は塗らないので、スカートのような面は中空の殻になる。
  2. 各ボクセルの色を、1.20.1 の標準ブロックの代表色（下の表）に CIELAB で最も近いものへ置き換える。
  3. 標準ライブラリだけで Sponge v2（DataVersion 3465）の .schem を書く。向きは元のまま（OBJ の +Y が上、+Z が南）。

注意: 代表色は私の知識による近似値で、実テクスチャの平均を測ったものではない。見た目は --preview で確認する。
"""
import argparse, collections, gzip, math, os, re, struct, sys

DATA_VERSION = 3465  # Minecraft 1.20.1

COLORS16 = {
    'white': (207, 213, 214), 'orange': (224, 97, 0), 'magenta': (169, 48, 159), 'light_blue': (36, 137, 199),
    'yellow': (241, 175, 21), 'lime': (94, 169, 24), 'pink': (214, 101, 143), 'gray': (54, 57, 61),
    'light_gray': (125, 125, 115), 'cyan': (21, 119, 136), 'purple': (100, 31, 156), 'blue': (45, 47, 143),
    'brown': (96, 60, 32), 'green': (73, 91, 36), 'red': (142, 33, 33), 'black': (8, 10, 15),
}
TERRACOTTA16 = {
    'white': (209, 178, 161), 'orange': (161, 83, 37), 'magenta': (149, 88, 108), 'light_blue': (113, 108, 137),
    'yellow': (186, 133, 36), 'lime': (103, 117, 53), 'pink': (161, 78, 78), 'gray': (57, 42, 35),
    'light_gray': (135, 107, 98), 'cyan': (87, 91, 91), 'purple': (118, 70, 86), 'blue': (74, 59, 91),
    'brown': (77, 51, 36), 'green': (76, 83, 42), 'red': (143, 61, 46), 'black': (37, 22, 16),
}
OTHERS = {
    'stone': (125, 125, 125), 'smooth_stone': (158, 158, 158), 'stone_bricks': (122, 121, 122),
    'polished_andesite': (132, 135, 134), 'deepslate_bricks': (70, 70, 71), 'polished_deepslate': (72, 72, 73),
    'smooth_basalt': (72, 72, 78), 'blackstone': (42, 36, 41), 'polished_blackstone': (53, 48, 56),
    'iron_block': (220, 220, 220), 'gold_block': (249, 236, 78), 'quartz_block': (236, 230, 223),
    'bone_block': (229, 226, 208), 'oak_planks': (162, 130, 78), 'spruce_planks': (115, 85, 49),
    'dark_oak_planks': (67, 43, 20), 'bricks': (151, 98, 83), 'nether_bricks': (45, 22, 26),
    'obsidian': (15, 11, 25), 'coal_block': (16, 15, 15), 'copper_block': (192, 107, 80),
    'purpur_block': (170, 126, 170), 'end_stone_bricks': (218, 224, 162), 'sandstone': (224, 214, 170),
    'snow_block': (249, 254, 254), 'prismarine_bricks': (99, 171, 158), 'dark_prismarine': (52, 92, 76),
    'lapis_block': (31, 67, 140), 'terracotta': (152, 94, 67),
}


def build_palette():
    pal = {}
    for k, c in COLORS16.items():
        pal[f'minecraft:{k}_concrete'] = c
    for k, c in TERRACOTTA16.items():
        pal[f'minecraft:{k}_terracotta'] = c
    for k, c in OTHERS.items():
        pal[f'minecraft:{k}'] = c
    return pal


# ---------------------------------------------------------------- 色空間


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb):
    r, g, b = (_lin(c) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


# ---------------------------------------------------------------- OBJ 読み込み


def load_obj(path, exclude):
    from PIL import Image
    base = os.path.dirname(path)
    V, VT, tris = [], [], []
    group, mat, mtlfile = '', None, None
    ex = re.compile(exclude) if exclude else None
    for ln in open(path, encoding='utf-8'):
        s = ln.split()
        if not s:
            continue
        if s[0] == 'v':
            V.append(tuple(map(float, s[1:4])))
        elif s[0] == 'vt':
            VT.append((float(s[1]), float(s[2])))
        elif s[0] == 'g':
            group = s[1]
        elif s[0] == 'usemtl':
            mat = s[1]
        elif s[0] == 'mtllib':
            mtlfile = s[1]
        elif s[0] == 'f':
            if ex and ex.search(group):
                continue
            idx = [tuple(int(x) if x else 0 for x in t.split('/')) for t in s[1:]]
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1], mat, group))
    tex = {}
    if mtlfile:
        name = None
        for ln in open(os.path.join(base, mtlfile), encoding='utf-8'):
            s = ln.split()
            if s and s[0] == 'newmtl':
                name = s[1]
            elif s and s[0] == 'map_Kd' and name:
                im = Image.open(os.path.join(base, s[1])).convert('RGBA')
                tex[name] = (im.size, im.tobytes())
    return V, VT, tris, tex


# ---------------------------------------------------------------- ボクセル化


def voxelize(V, VT, tris, tex, size):
    pts = [V[i[0] - 1] for t in tris for i in t[:3]]
    mn = [min(p[a] for p in pts) for a in range(3)]
    mx = [max(p[a] for p in pts) for a in range(3)]
    cell = max(mx[a] - mn[a] for a in range(3)) / size
    dims = [int((mx[a] - mn[a]) / cell) + 1 for a in range(3)]
    acc = collections.defaultdict(lambda: [0, 0, 0, 0])
    for a, b, c, mat, _grp in tris:
        pa, pb, pc = (tuple((V[i[0] - 1][k] - mn[k]) / cell for k in range(3)) for i in (a, b, c))
        ua, ub, uc = (VT[i[1] - 1] if len(i) > 1 and i[1] else (0.0, 0.0) for i in (a, b, c))
        edge = max(math.dist(pa, pb), math.dist(pb, pc), math.dist(pc, pa))
        n = max(1, math.ceil(edge / 0.45))
        t = tex.get(mat)
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                w = 1 - u - v
                x = w * pa[0] + u * pb[0] + v * pc[0]
                y = w * pa[1] + u * pb[1] + v * pc[1]
                z = w * pa[2] + u * pb[2] + v * pc[2]
                if t:
                    (tw, th), data = t
                    su = w * ua[0] + u * ub[0] + v * uc[0]
                    sv = w * ua[1] + u * ub[1] + v * uc[1]
                    px = (int(su * tw) % tw) + (int((1.0 - sv) * th) % th) * tw
                    r, g, bl, al = data[px * 4:px * 4 + 4]
                    if al < 128:
                        continue
                else:
                    r = g = bl = 200
                key = (min(int(x), dims[0] - 1), min(int(y), dims[1] - 1), min(int(z), dims[2] - 1))
                e = acc[key]
                e[0] += r
                e[1] += g
                e[2] += bl
                e[3] += 1
    return dims, cell, {k: (e[0] / e[3], e[1] / e[3], e[2] / e[3]) for k, e in acc.items()}


def adjust(rgb, gain, sat):
    """明るさ(gain)と彩度(sat)を調整する。ゲームのテクスチャは暗めで、そのままだとブロックが灰色寄りになるため。"""
    luma = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return tuple(max(0.0, min(255.0, (luma + (c - luma) * sat) * gain)) for c in rgb)


def to_blocks(colors, palette, gain=1.0, sat=1.0):
    names = list(palette)
    labs = [rgb_to_lab(palette[n]) for n in names]
    cache = {}
    out = {}
    for k, rgb in colors.items():
        rgb = adjust(rgb, gain, sat)
        q = (int(rgb[0]) >> 2, int(rgb[1]) >> 2, int(rgb[2]) >> 2)
        if q not in cache:
            lab = rgb_to_lab(rgb)
            cache[q] = min(range(len(names)), key=lambda i: sum((lab[a] - labs[i][a]) ** 2 for a in range(3)))
        out[k] = names[cache[q]]
    return out


# ---------------------------------------------------------------- NBT / Sponge v2


def _s(text):
    raw = text.encode('utf-8')
    return struct.pack('>H', len(raw)) + raw


def tag(type_, name, payload):
    return bytes([type_]) + _s(name) + payload


def t_int(name, v):
    return tag(3, name, struct.pack('>i', v))


def t_short(name, v):
    return tag(2, name, struct.pack('>h', v))


def t_str(name, v):
    return tag(8, name, _s(v))


def t_bytes(name, data):
    return tag(7, name, struct.pack('>i', len(data)) + bytes(data))


def t_ints(name, vals):
    return tag(11, name, struct.pack('>i', len(vals)) + b''.join(struct.pack('>i', v) for v in vals))


def t_compound(name, children):
    return tag(10, name, b''.join(children) + b'\x00')


def varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def write_schem(path, dims, blocks, name):
    w, h, l = dims
    index = {'minecraft:air': 0}
    for b in sorted(set(blocks.values())):
        index[b] = len(index)
    data = bytearray()
    grid = [0] * (w * h * l)
    for (x, y, z), b in blocks.items():
        grid[x + z * w + y * w * l] = index[b]
    for v in grid:
        data += varint(v)
    root = t_compound('Schematic', [
        t_int('Version', 2),
        t_int('DataVersion', DATA_VERSION),
        t_compound('Metadata', [t_str('Name', name), t_str('Generator', 'obj2schem (自作)')]),
        t_short('Width', w), t_short('Height', h), t_short('Length', l),
        t_ints('Offset', [0, 0, 0]),
        t_int('PaletteMax', len(index)),
        t_compound('Palette', [t_int(k, v) for k, v in index.items()]),
        t_bytes('BlockData', data),
    ])
    with gzip.open(path, 'wb', 9) as f:
        f.write(root)
    return index


# ---------------------------------------------------------------- プレビュー


def preview(dims, blocks, palette, prefix, px=4):
    from PIL import Image
    w, h, l = dims
    views = {
        'front': (lambda x, y, z: (x, h - 1 - y, -z), w, h),       # +Z側から見る
        'side': (lambda x, y, z: (l - 1 - z, h - 1 - y, -x), l, h),  # +X側から見る
        'top': (lambda x, y, z: (x, l - 1 - z, -y), w, l),
    }
    shade = {'front': 1.0, 'side': 0.8, 'top': 0.9}
    for name, (proj, vw, vh) in views.items():
        img = Image.new('RGB', (vw * px, vh * px), (28, 30, 40))
        depth = {}
        for (x, y, z), b in blocks.items():
            sx, sy, d = proj(x, y, z)
            if (sx, sy) not in depth or d > depth[(sx, sy)][0]:
                depth[(sx, sy)] = (d, b)
        pix = img.load()
        for (sx, sy), (_d, b) in depth.items():
            c = tuple(int(v * shade[name]) for v in palette[b])
            for dx in range(px):
                for dy in range(px):
                    pix[sx * px + dx, sy * px + dy] = c
        img.save(f'{prefix}_{name}.png')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('obj')
    ap.add_argument('out')
    ap.add_argument('--size', type=int, default=128, help='最長辺のブロック数')
    ap.add_argument('--exclude', default='', help='除外するグループ名の正規表現')
    ap.add_argument('--preview', default='', help='プレビュー画像の接頭辞')
    ap.add_argument('--gain', type=float, default=1.0, help='明るさの倍率（ブロック選びの前に適用）')
    ap.add_argument('--sat', type=float, default=1.0, help='彩度の倍率（ブロック選びの前に適用）')
    a = ap.parse_args()
    V, VT, tris, tex = load_obj(a.obj, a.exclude)
    print(f'  三角形{len(tris)} (除外: {a.exclude or "なし"})')
    dims, cell, colors = voxelize(V, VT, tris, tex, a.size)
    palette = build_palette()
    blocks = to_blocks(colors, palette, a.gain, a.sat)
    name = os.path.splitext(os.path.basename(a.out))[0]
    index = write_schem(a.out, dims, blocks, name)
    counts = collections.Counter(blocks.values())
    print(f'  寸法 {dims[0]}x{dims[1]}x{dims[2]} (幅x高さx奥行) / 1ブロック={cell:.1f}単位 / ブロック数 {len(blocks)} / 種類 {len(index) - 1}')
    with open(os.path.splitext(a.out)[0] + '.materials.tsv', 'w', encoding='utf-8') as f:
        f.write('block\tcount\n')
        for b, n in counts.most_common():
            f.write(f'{b}\t{n}\n')
    for b, n in counts.most_common(8):
        print(f'    {b:34} {n}')
    if a.preview:
        preview(dims, blocks, palette, a.preview)
        print(f'  preview -> {a.preview}_(front|side|top).png')
    print(f'  -> {a.out} ({os.path.getsize(a.out) / 1024:.0f} KB)')


if __name__ == '__main__':
    main()
