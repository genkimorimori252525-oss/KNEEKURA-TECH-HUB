"""ブロック構成(.schem) -> Blockbench の立方体モデル（Bedrock Entity 形式: .bbmodel + .geo.json + テクスチャPNG）。

使い方:
  python voxel2bbmodel.py <in.schem> <出力フォルダ> [--name walpurgis] [--unit 16] [--keep-front]
                          [--legacy] [--pretty] [--dump-expected expected.json]

仕組み:
  1. （最適化）外から見えない閉じた空洞を埋める。外から見える面は一切変わらない。
  2. ボクセルを、幾何だけで直方体に統合する（色は無視）。伸ばす軸の順と走査順の36通りから、見える箱が最少のものを選ぶ。
  3. 外から1ピクセルも見えない箱は捨て、箱の中で隠れている面は書かない（Bedrock は書かれていない面を描画しない）。
  4. 各面に、1ボクセル = 1ピクセルでテクスチャ領域を割り当てる（面ごとのUV）。色はブロック色（obj2schem の代表色）。
  5. 領域を1枚のアトラスに詰めて PNG にする。.bbmodel と、Blockbench の書き出しと同じ規則の .geo.json を作る。
  --legacy は最適化なし（空洞を埋めず、固定の統合順、全6面を出力）。前後比較用。

UVの向き（Blockbench 5.2.1 のジオメトリを実測。矩形 [u1,v1,u2,v2] の左上 = (u1,v1)）:
  east(+X):  u→-Z, v→-Y     west(-X):  u→+Z, v→-Y
  up(+Y):    u→+X, v→+Z     down(-Y):  u→+X, v→-Z
  south(+Z): u→+X, v→-Y     north(-Z): u→-X, v→-Y
Blockbench の仕様（実機とソースで確認）: face.texture が null の面は描画されず、geo.json にも書き出されない。
geo.json への書き出し: cube.origin = [-to_x, from_y, from_z]、up/down 面は uv=[u2,v2], uv_size=[-(u2-u1), -(v2-v1)]、
  それ以外は uv=[u1,v1], uv_size=[u2-u1, v2-v1]。可視範囲は Blockbench の calculateVisibleBox と同じ式。
向き: 既定ではモデルをY軸まわりに180°回し、前（顔）を -Z（マイクラのエンティティの北向き）にする。--keep-front で元の向き(+Z)。
"""
import argparse, base64, collections, gzip, itertools, json, math, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obj2schem
import schem_check

NS = uuid.UUID('76786c32-6262-6d6f-6465-6c0000000001')
FACES = ('north', 'east', 'south', 'west', 'up', 'down')
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(str(p) for p in parts)))


def load_schem(path):
    raw = gzip.open(path, 'rb').read()
    _name, root, _ok = schem_check.read_nbt(raw)
    w, h, l = root['Width'] & 0xFFFF, root['Height'] & 0xFFFF, root['Length'] & 0xFFFF
    pal = {v: k for k, v in root['Palette'].items()}
    solid = {}
    for i, c in enumerate(schem_check.decode_varints(root['BlockData'])):
        if c:
            solid[(i % w, i // (w * l), (i // w) % l)] = pal[c]
    return (w, h, l), solid


# ---------------------------------------------------------------- 最適化: 空洞埋め・統合


def fill_cavities(cells, dims):
    """外の空気から6近傍で洪水充填し、届かない空きセル（閉じた空洞）を埋めた集合を返す。"""
    w, h, l = dims
    outside = {(-1, -1, -1)}
    dq = collections.deque([(-1, -1, -1)])
    while dq:
        x, y, z = dq.popleft()
        for d in N6:
            n = (x + d[0], y + d[1], z + d[2])
            if n in outside or n in cells or not (-1 <= n[0] <= w and -1 <= n[1] <= h and -1 <= n[2] <= l):
                continue
            outside.add(n)
            dq.append(n)
    filled = set(cells)
    for x in range(w):
        for y in range(h):
            for z in range(l):
                if (x, y, z) not in cells and (x, y, z) not in outside:
                    filled.add((x, y, z))
    return filled


def partition(cells, seed, axes):
    """幾何だけの貪欲分割（重なりなし）。seed = 走査順（軸の並び）、axes = 伸ばす軸の順。戻り: [(lo, hi)]（hi排他）。"""
    used = set()
    boxes = []
    for c in sorted(cells, key=lambda p: (p[seed[0]], p[seed[1]], p[seed[2]])):
        if c in used:
            continue
        lo, hi = list(c), [c[0] + 1, c[1] + 1, c[2] + 1]
        for ax in axes:
            while True:
                ranges = [range(lo[i], hi[i]) for i in range(3)]
                ranges[ax] = [hi[ax]]
                if all(q in cells and q not in used for q in itertools.product(*ranges)):
                    hi[ax] += 1
                else:
                    break
        for q in itertools.product(*[range(lo[i], hi[i]) for i in range(3)]):
            used.add(q)
        boxes.append((tuple(lo), tuple(hi)))
    return boxes


# 面名 -> (軸, 向き)
FACE_AXIS = {'east': (0, 1), 'west': (0, -1), 'up': (1, 1), 'down': (1, -1), 'south': (2, 1), 'north': (2, -1)}


def face_exposed(box, face, grid):
    """この箱の面に、外へ露出するピクセル（隣のセルが grid に無い）が1つでもあるか。"""
    lo, hi = box
    ax, sign = FACE_AXIS[face]
    outn = hi[ax] if sign > 0 else lo[ax] - 1
    ranges = [range(lo[i], hi[i]) for i in range(3)]
    ranges[ax] = [outn]
    return any(q not in grid for q in itertools.product(*ranges))


def visible_box(box, grid):
    return any(face_exposed(box, f, grid) for f in FACES)


def choose_partition(grid):
    best = None
    for seed in itertools.permutations(range(3)):
        for axes in itertools.permutations(range(3)):
            vis = [b for b in partition(grid, seed, axes) if visible_box(b, grid)]
            if best is None or len(vis) < len(best[0]):
                best = (vis, seed, axes)
    return best


# 面ごとの: 領域の幅・高さ, (pu,pv)->セル の写像（箱は (lo, hi)）
def face_cells(face, b):
    (x0, y0, z0), (x1, y1, z1) = b
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    if face == 'east':
        return dz, dy, (1, 0, 0), lambda pu, pv: (x1 - 1, y1 - 1 - pv, z1 - 1 - pu)
    if face == 'west':
        return dz, dy, (-1, 0, 0), lambda pu, pv: (x0, y1 - 1 - pv, z0 + pu)
    if face == 'up':
        return dx, dz, (0, 1, 0), lambda pu, pv: (x0 + pu, y1 - 1, z0 + pv)
    if face == 'down':
        return dx, dz, (0, -1, 0), lambda pu, pv: (x0 + pu, y0, z1 - 1 - pv)
    if face == 'south':
        return dx, dy, (0, 0, 1), lambda pu, pv: (x0 + pu, y1 - 1 - pv, z1 - 1)
    return dx, dy, (0, 0, -1), lambda pu, pv: (x1 - 1 - pu, y1 - 1 - pv, z0)  # north


def pack(regions):
    """棚詰め。regions: [(w,h)]。戻り: (S, [(x,y)])。正方形で最小の2冪を探す。"""
    order = sorted(range(len(regions)), key=lambda i: (-regions[i][1], -regions[i][0]))
    area = sum(w * h for w, h in regions)
    s = 16
    while s * s < area:
        s *= 2
    while True:
        pos = [None] * len(regions)
        x = y = row_h = 0
        ok = True
        for i in order:
            w, h = regions[i]
            if w > s or h > s:
                ok = False
                break
            if x + w > s:
                x, y, row_h = 0, y + row_h, 0
            if y + h > s:
                ok = False
                break
            pos[i] = (x, y)
            x += w
            row_h = max(row_h, h)
        if ok:
            return s, pos
        s *= 2


def build(schem_path, outdir, name='model', unit=16, keep_front=False, dump_expected=None, legacy=False, pretty=False):
    from PIL import Image
    dims, solid = load_schem(schem_path)
    w, h, l = dims
    palette = obj2schem.build_palette()
    if not keep_front:  # Y軸180°: x,z を反転して前を -Z に
        solid = {(w - 1 - x, y, l - 1 - z): b for (x, y, z), b in solid.items()}
    ox, oz = -(w // 2), -(l // 2)  # 中心を原点に（x,z）。足元は y=0

    if legacy:
        grid = set(solid)
        boxes = partition(grid, (1, 2, 0), (0, 2, 1))
        info = f'legacy: 空洞埋めなし・固定の統合順・全6面'
    else:
        grid = fill_cavities(set(solid), dims)
        boxes, seed, axes = choose_partition(grid)
        info = f'最適化: 空洞を埋めた({len(grid) - len(solid)}セル) / 統合順 seed={seed} axes={axes}'

    uniq, regions, pixels = {}, [], []
    cube_faces, expected = [], []
    quad_count = 0
    for b in boxes:
        fm = {}
        for face in FACES:
            fw, fh, n, cell = face_cells(face, b)
            exposed_any = face_exposed(b, face, grid)
            if not exposed_any and not legacy:
                continue  # 見えない面は書かない
            pix = []
            for pv in range(fh):
                for pu in range(fw):
                    c = cell(pu, pv)
                    blk = solid.get(c)
                    rgb = palette[blk] if blk else (128, 128, 128)
                    pix.append(rgb)
                    if dump_expected is not None and blk and (c[0] + n[0], c[1] + n[1], c[2] + n[2]) not in grid:
                        expected.append([c[0] + ox, c[1], c[2] + oz, face, rgb[0], rgb[1], rgb[2]])
            if not exposed_any:  # legacy: 完全に隠れる面は共有の1ピクセル
                key, fw, fh, pix = (1, 1, ((128, 128, 128),)), 1, 1, [(128, 128, 128)]
            else:
                key = (fw, fh, tuple(pix))
            if key not in uniq:
                uniq[key] = len(regions)
                regions.append((fw, fh))
                pixels.append(pix)
            fm[face] = uniq[key]
            quad_count += 1
        cube_faces.append(fm)
    size, pos = pack(regions)
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    px = img.load()
    for (rw, _rh), (rx, ry), pix in zip(regions, pos, pixels):
        for i, rgb in enumerate(pix):
            px[rx + i % rw, ry + i // rw] = (rgb[0], rgb[1], rgb[2], 255)
    os.makedirs(outdir, exist_ok=True)
    png_path = os.path.join(outdir, f'{name}.png')
    img.save(png_path, optimize=True)

    def uvrect(rid):
        rx, ry = pos[rid]
        rw, rh = regions[rid]
        return [rx, ry, rx + rw, ry + rh]

    elements, geo_cubes, child_ids = [], [], []
    for i, (b, fm) in enumerate(zip(boxes, cube_faces)):
        (bx0, by0, bz0), (bx1, by1, bz1) = b
        frm = [(bx0 + ox) * unit, by0 * unit, (bz0 + oz) * unit]
        to = [(bx1 + ox) * unit, by1 * unit, (bz1 + oz) * unit]
        faces = {f: ({'uv': uvrect(fm[f]), 'texture': 0} if f in fm else {'uv': [0, 0, 0, 0], 'texture': None}) for f in FACES}
        cid = uid('cube', i)
        child_ids.append(cid)
        elements.append(dict(name=f'b{i}', box_uv=False, **{'from': frm, 'to': to}, faces=faces, type='cube', uuid=cid))
        guv = {}
        for f in FACES:
            if f not in fm:
                continue
            u1, v1, u2, v2 = faces[f]['uv']
            guv[f] = ({'uv': [u2, v2], 'uv_size': [-(u2 - u1), -(v2 - v1)]} if f in ('up', 'down')
                      else {'uv': [u1, v1], 'uv_size': [u2 - u1, v2 - v1]})
        geo_cubes.append({'origin': [-to[0], frm[1], frm[2]], 'size': [to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]], 'uv': guv})

    group_id = uid('group', 'root')
    tex = dict(
        path='', folder='', namespace='', id='0', group='', scope=0, name=f'{name}.png', width=size, height=size,
        uv_width=size, uv_height=size, particle=False, use_as_default=False, layers_enabled=False, sync_to_project='',
        file_format='png', render_mode='default', render_sides='auto', wrap_mode='limited', pbr_channel='color',
        fps=7, frame_time=1, frame_order_type='loop', frame_order='', frame_interpolate=False, visible=True,
        internal=True, saved=False, uuid=uid('tex'),
        source='data:image/png;base64,' + base64.b64encode(open(png_path, 'rb').read()).decode('ascii'))
    doc = dict(
        meta=dict(format_version='5.0', model_format='bedrock', box_uv=False),
        name=name, model_identifier=name, visible_box=[1, 1, 0], variable_placeholders='', multi_file_ruleset='',
        variable_placeholder_buttons=[], timeline_setups=[], unhandled_root_fields={},
        resolution=dict(width=size, height=size), elements=elements,
        groups=[dict(name='root', uuid=group_id, export=True, locked=False, scope=0, selected=False, visibility=True,
                     origin=[0, 0, 0], rotation=[0, 0, 0], bedrock_binding='', color=0, children=child_ids,
                     reset=False, shade=True, mirror_uv=False, autouv=0, isOpen=True)],
        outliner=[dict(uuid=group_id, isOpen=True, children=child_ids)], textures=[tex])
    bb_path = os.path.join(outdir, f'{name}.bbmodel')
    with open(bb_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))

    # 可視範囲は Blockbench の calculateVisibleBox と同じ式（BB座標の外接箱に各軸 +8 して計算）
    xmin, xmax = min(e['from'][0] for e in elements), max(e['to'][0] for e in elements)
    ymin, ymax = min(e['from'][1] for e in elements), max(e['to'][1] for e in elements)
    zmin, zmax = min(e['from'][2] for e in elements), max(e['to'][2] for e in elements)
    radius = max(xmax + 8, zmax + 8, -(xmin + 8), -(zmin + 8))
    y_min = min(math.floor((ymin + 8) / 16), -0.5)
    y_max = max(math.ceil((ymax + 8) / 16), 0.5)
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': f'geometry.{name}', 'texture_width': size, 'texture_height': size,
                        'visible_bounds_width': max(math.ceil(radius * 2 / 16), 1),
                        'visible_bounds_height': y_max - y_min,
                        'visible_bounds_offset': [0, (y_max + y_min) / 2, 0]},
        'bones': [{'name': 'root', 'pivot': [0, 0, 0], 'cubes': geo_cubes}]}]}
    geo_path = os.path.join(outdir, f'{name}.geo.json')
    with open(geo_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(geo, f, ensure_ascii=False, indent='\t')
        else:
            json.dump(geo, f, ensure_ascii=False, separators=(',', ':'))
    if dump_expected is not None:
        with open(dump_expected, 'w', encoding='utf-8') as f:
            json.dump(expected, f, separators=(',', ':'))
    sizes = ', '.join(f'{os.path.basename(p)} {os.path.getsize(p) / 1024:.0f}KB' for p in (bb_path, geo_path, png_path))
    print(f'  {info}')
    print(f'  ボクセル{len(solid)} -> キューブ{len(boxes)} / 描画する面{quad_count} / 領域{len(regions)} / アトラス{size}x{size}')
    print(f'  {sizes}')
    return dict(cubes=len(boxes), quads=quad_count, atlas=size, solid=len(solid), expected=len(expected))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('schem')
    ap.add_argument('outdir')
    ap.add_argument('--name', default='model')
    ap.add_argument('--unit', type=int, default=16, help='1ボクセルのモデル単位（16 = 1ブロック）')
    ap.add_argument('--keep-front', action='store_true', help='向きを元のまま（既定は前を -Z にする）')
    ap.add_argument('--legacy', action='store_true', help='最適化なし（前後比較用）')
    ap.add_argument('--pretty', action='store_true', help='geo.json をインデント付きで書く（既定は圧縮）')
    ap.add_argument('--dump-expected', default=None, help='検証用: 露出面ごとの期待色を書き出す')
    a = ap.parse_args()
    build(a.schem, a.outdir, a.name, a.unit, a.keep_front, a.dump_expected, a.legacy, a.pretty)
