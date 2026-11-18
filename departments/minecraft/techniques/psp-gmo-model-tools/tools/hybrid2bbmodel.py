"""GMOモデル -> Blockbench の立方体モデル（斜めの板 + ブロックのハイブリッド）。Bedrock Entity 形式。

使い方:
  python hybrid2bbmodel.py <model.gmo> <出力フォルダ> [--name walpurgis] [--size 128] [--plates ^AL_body]
         [--exclude TR_pattern] [--gain 1.3] [--sat 1.3] [--thickness 0.5] [--texel 1.0] [--unit 16]
         [--keep-front] [--dump-expected expected.json]

仕組み:
  --plates に合うパーツ（既定 AL_body = ドレス）は、メッシュの各面（三角形・四角形）に沿った**斜めの薄い板**にする。
    板は「面の法線方向を板の厚み方向」にした回転キューブ。ブロック格子の階段状にならない。
    色は元のテクスチャを 1 ブロック = 1 ピクセルのドット絵にして板に貼る（ブロックの代表色に最も近い色に量子化）。
  それ以外のパーツ（歯車・頭など）は、従来どおりブロックにして直方体へ統合（空洞充填・見えない箱/面の除去つき）。
  両方を同じ座標系（最長辺 --size ブロック）・同じテクスチャアトラスで 1 つのモデルにまとめる。

Blockbench 5.2.1 で実機確認した規則:
  回転キューブ: 回転は ZYX の Euler（度）で、origin（= ピボット）まわり。from/to はピボットを含む回転前の箱。
  geo.json: cube.origin=[-to_x, from_y, from_z], pivot=[-origin_x, origin_y, origin_z], rotation=[-rx, -ry, rz]。
  面UV: 上面(up) は u→+X, v→+Z、下面(down) は u→+X, v→-Z（面の局所座標）。
"""
import argparse, base64, json, math, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim, gmo, obj2schem, voxel2bbmodel
from gmo2obj import read_array, read_indices, read_scale_bias

NS = uuid.UUID('68796272-6964-6d6f-6465-6c0000000001')


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(str(p) for p in parts)))


# ---------------------------------------------------------------- ベクトル・回転


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def add(a, b):
    return [a[i] + b[i] for i in range(3)]


def mul(a, s):
    return [c * s for c in a]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def norm(a):
    n = math.sqrt(dot(a, a))
    return [c / n for c in a] if n > 1e-12 else None


def euler_zyx_from_columns(x_axis, y_axis, z_axis):
    """回転行列（列 = x,y,z 軸の向き）-> three.js 'ZYX' の Euler（度）。"""
    m = [[x_axis[r], y_axis[r], z_axis[r]] for r in range(3)]
    y = math.asin(-max(-1.0, min(1.0, m[2][0])))
    if abs(m[2][0]) < 0.9999999:
        x = math.atan2(m[2][1], m[2][2])
        z = math.atan2(m[1][0], m[0][0])
    else:
        x = 0.0
        z = math.atan2(-m[0][1], m[1][1])
    return [math.degrees(x), math.degrees(y), math.degrees(z)]


# ---------------------------------------------------------------- GMO の面を読む


def read_polygons(gmo_path, exclude):
    """除外に合わないパーツの全多角形。戻り: (polys, textures)。
    poly = dict(part, pos=[(x,y,z)...], uv=[(u,v)...] (v は上が0), tex=テクスチャ番号 or None)"""
    import re
    ex = re.compile(exclude) if exclude else None
    model = gmo.parse(open(gmo_path, 'rb').read())[0].children[0]
    sb = read_scale_bias(model)
    textures = []
    for t in model.kids(0x0a):
        pl = t.kid(0x8013).payload
        n = int.from_bytes(pl[:4], 'little')
        w, h, rgba = gim.decode(pl[4:4 + n])
        p12 = t.kid(0x8012)  # 元のファイル名（パス文字列）。--plate-tex の絞り込みに使う
        stem = os.path.splitext(p12.payload.split(b'\0')[0].decode('latin1').replace('\\', '/').split('/')[-1])[0] if p12 else f'tex{len(textures)}'
        textures.append(((w, h), rgba, stem))
    mat_tex = []
    for m in model.kids(8):
        ti = None
        for layer in m.kids(9):
            r = layer.kid(0x8091)
            if r is not None:
                ti = gmo.ref(int.from_bytes(r.payload[:4], 'little'))
                break
        mat_tex.append(ti if ti is not None and ti < len(textures) else None)
    polys = []
    for part in model.kids(5):
        if ex and ex.search(part.name):
            continue
        arrays = [read_array(a, sb) for a in part.kids(7)]
        for mesh in part.kids(6):
            mr = mesh.kid(0x8061)
            mi = gmo.ref(int.from_bytes(mr.payload[:4], 'little')) if mr is not None else None
            ti = mat_tex[mi] if mi is not None and mi < len(mat_tex) else None
            for ar, plist in read_indices(mesh):
                arr = arrays[ar]
                for q in plist:
                    polys.append(dict(part=part.name, pos=[arr['pos'][i] for i in q],
                                      uv=[arr['uv'][i] for i in q] if arr['uv'] else None, tex=ti))
    return polys, textures


# ---------------------------------------------------------------- 板


def sample_texture(tex, u, v):
    (tw, th), data = tex[0], tex[1]
    x = int(u * tw) % tw
    y = int(v * th) % th
    k = (y * tw + x) * 4
    return data[k], data[k + 1], data[k + 2], data[k + 3]


def tri_weights(p, a, b, c):
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-12:
        return None
    w0 = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) / d
    w1 = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) / d
    return w0, w1, 1 - w0 - w1


def make_plate(poly, textures, palette_fn, unit, thickness, texel, coverage=0.5):
    """多角形 -> 板（回転キューブ）の定義。BB座標（単位 = モデル単位）の頂点を渡す。作れなければ None。
    coverage: ピクセルを塗る条件（ピクセル内 3x3 サンプルのうち多角形の内側に入る割合）。
              0 に近いほど継ぎ目の隙間は減るが、隣の板からはみ出す（浮き出た斜めに見える）。0.5 = 半分以上覆うときだけ。
    thickness=0 なら厚み0の板（元のメッシュの面そのもの）。側面は描かない。"""
    P = poly['pos']
    n = len(P)
    C = [sum(p[k] for p in P) / n for k in range(3)]
    N = [0.0, 0.0, 0.0]
    for i in range(n):
        N = add(N, cross(P[i], P[(i + 1) % n]))
    N = norm(N)
    if N is None:
        return None
    # 最長辺を板の x 軸にする
    edges = [(math.dist(P[i], P[(i + 1) % n]), sub(P[(i + 1) % n], P[i])) for i in range(n)]
    e = max(edges, key=lambda t: t[0])[1]
    X = norm(sub(e, mul(N, dot(e, N))))
    if X is None:
        return None
    Z = cross(X, N)
    ab = [(dot(sub(p, C), X), dot(sub(p, C), Z)) for p in P]
    amin, amax = min(a for a, _ in ab), max(a for a, _ in ab)
    bmin, bmax = min(b for _, b in ab), max(b for _, b in ab)
    ca, cb = (amin + amax) / 2, (bmin + bmax) / 2
    w, h = max(amax - amin, 0.05 * unit), max(bmax - bmin, 0.05 * unit)
    Cp = add(add(C, mul(X, ca)), mul(Z, cb))
    tx = texel * unit
    pw, ph = max(1, math.ceil(w / tx - 1e-6)), max(1, math.ceil(h / tx - 1e-6))
    tris = [(0, 1, 2)] if n == 3 else [(0, 1, 2), (0, 2, 3)]
    tex = textures[poly['tex']] if poly['tex'] is not None and poly['uv'] else None
    fr = (1 / 6, 3 / 6, 5 / 6)
    pix = [None] * (pw * ph)
    need = max(1, math.ceil(coverage * len(fr) ** 2 - 1e-9))
    for pv in range(ph):
        for pu in range(pw):
            acc, cnt, inside = [0, 0, 0], 0, 0
            for fy in fr:
                for fx in fr:
                    a = ca - w / 2 + (pu + fx) / pw * w
                    b = cb - h / 2 + (pv + fy) / ph * h
                    for t in tris:
                        wt = tri_weights((a, b), ab[t[0]], ab[t[1]], ab[t[2]])
                        if wt and min(wt) >= -1e-9:
                            inside += 1
                            if tex:
                                u = sum(wt[k] * poly['uv'][t[k]][0] for k in range(3))
                                v = sum(wt[k] * poly['uv'][t[k]][1] for k in range(3))
                                r, g, bl, al = sample_texture(tex, u, v)
                                if al < 128:
                                    break
                            else:
                                r, g, bl = 200, 200, 200
                            acc = [acc[0] + r, acc[1] + g, acc[2] + bl]
                            cnt += 1
                            break
            # 半分以上（coverage）が多角形の内側で、内側の半分以上が不透明なら塗る
            if inside >= need and cnt * 2 >= inside:
                pix[pv * pw + pu] = palette_fn((acc[0] / cnt, acc[1] / cnt, acc[2] / cnt)) + (255,)
    if not any(pix):
        # 小さすぎてサンプルに掛からない多角形は、重心の色を1ピクセルに置く
        cen = (sum(a for a, _ in ab) / n, sum(b for _, b in ab) / n)
        for t in tris:
            wt = tri_weights(cen, ab[t[0]], ab[t[1]], ab[t[2]])
            if wt and min(wt) >= -1e-9 and tex:
                u = sum(wt[k] * poly['uv'][t[k]][0] for k in range(3))
                v = sum(wt[k] * poly['uv'][t[k]][1] for k in range(3))
                r, g, bl, al = sample_texture(tex, u, v)
                if al >= 128:
                    pix[0] = palette_fn((r, g, bl)) + (255,)
                break
    if not any(pix):
        return None  # 完全に透明（レースの抜けなど）
    opaque = [p for p in pix if p]
    whole = tuple(sum(p[k] for p in opaque) // len(opaque) for k in range(3)) + (255,)

    def avg(cells):
        cs = [p for p in cells if p]
        return tuple(sum(p[k] for p in cs) // len(cs) for k in range(3)) + (255,) if cs else whole
    # 側面の色は、その辺に沿った縁のピクセルの平均（局所座標: north=z-側, south=z+側, west=x-側, east=x+側）
    edge = dict(north=avg(pix[0:pw]), south=avg(pix[(ph - 1) * pw:ph * pw]),
                west=avg(pix[0::pw]), east=avg(pix[pw - 1::pw]))
    half = [w / 2, thickness * unit / 2, h / 2]
    return dict(C=Cp, X=X, N=N, Z=Z, w=w, h=h, t=thickness * unit, pw=pw, ph=ph, pix=pix, edge=edge,
                frm=sub(Cp, half), to=add(Cp, half), rot=euler_zyx_from_columns(X, N, Z))


# ---------------------------------------------------------------- 組み立て


def build(gmo_path, outdir, name='model', size=128, plates='^AL_body', exclude='TR_pattern', gain=1.3, sat=1.3,
          thickness=0.5, texel=1.0, unit=16, keep_front=False, dump_expected=None, plate_tex=None, quantize=True,
          coverage=0.5, fine_parts=None, fine_texel=None):
    import re
    fine_re = re.compile(fine_parts) if fine_parts else None
    from PIL import Image
    polys, textures = read_polygons(gmo_path, exclude)
    allpts = [p for q in polys for p in q['pos']]
    mn, cell, dims = obj2schem.bbox_frame(allpts, size)
    w, h, l = dims
    palette = obj2schem.build_palette()
    plate_re = re.compile(plates) if plates else None
    tex_re = re.compile(plate_tex) if plate_tex else None

    def is_plate(q):
        """板にする面か: パーツ名が --plates に合い、（指定時）テクスチャ名が --plate-tex に合う。"""
        if not (plate_re and plate_re.search(q['part'])):
            return False
        if tex_re is None:
            return True
        return q['tex'] is not None and bool(tex_re.search(textures[q['tex']][2]))

    def to_vox(p):  # 連続座標（ボクセル単位）。keep_front でなければ Y軸180°（x,z を反転）
        x, y, z = ((p[a] - mn[a]) / cell for a in range(3))
        return (x, y, z) if keep_front else (w - x, y, l - z)

    ox, oz = -(w // 2), -(l // 2)

    def to_bb(p):
        x, y, z = to_vox(p)
        return [(x + ox) * unit, y * unit, (z + oz) * unit]

    # --- ブロック部（板にしないパーツ）---
    V, VT, tris, texd = [], [], [], {}
    for ti, tx in enumerate(textures):
        texd[f'tex{ti}'] = (tx[0], tx[1])
    for q in polys:
        if is_plate(q):
            continue
        base = len(V)
        V += list(q['pos'])
        has_uv = q['uv'] is not None
        for k in range(len(q['pos'])):
            VT.append((q['uv'][k][0], 1.0 - q['uv'][k][1]) if has_uv else (0.0, 0.0))
        mat = f"tex{q['tex']}" if q['tex'] is not None else None
        idx = [(base + k + 1, base + k + 1) for k in range(len(q['pos']))]
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1], mat, q['part']))
    solid = {}
    if tris:
        _d, _c, colors = obj2schem.voxelize(V, VT, tris, texd, size, frame=(mn, cell, dims))
        for c, blk in obj2schem.to_blocks(colors, palette, gain, sat).items():
            solid[c if keep_front else (w - 1 - c[0], c[1], l - 1 - c[2])] = blk
    grid = voxel2bbmodel.fill_cavities(set(solid), dims) if solid else set()
    boxes, seed, axes = voxel2bbmodel.choose_partition(grid) if solid else ([], None, None)

    # --- 領域（アトラスに詰める画素の塊）---
    regions, pixels, uniq = [], [], {}

    def region(wid, hei, pix):
        key = (wid, hei, tuple(pix))
        if key not in uniq:
            uniq[key] = len(regions)
            regions.append((wid, hei))
            pixels.append(pix)
        return uniq[key]

    cubes = []  # dict(name, frm, to, origin, rot, faces={face: (region, flip)})
    expected_vox = []
    for i, b in enumerate(boxes):
        fm = {}
        for face in voxel2bbmodel.FACES:
            if not voxel2bbmodel.face_exposed(b, face, grid):
                continue
            fw, fh, nrm, cellf = voxel2bbmodel.face_cells(face, b)
            pix = []
            for pv in range(fh):
                for pu in range(fw):
                    c = cellf(pu, pv)
                    blk = solid.get(c)
                    rgb = palette[blk] if blk else (128, 128, 128)
                    pix.append(tuple(rgb) + (255,))
                    if dump_expected is not None and blk and (c[0] + nrm[0], c[1] + nrm[1], c[2] + nrm[2]) not in grid:
                        expected_vox.append([c[0] + ox, c[1], c[2] + oz, face, rgb[0], rgb[1], rgb[2]])
            fm[face] = (region(fw, fh, pix), False)
        (bx0, by0, bz0), (bx1, by1, bz1) = b
        cubes.append(dict(name=f'b{i}', frm=[(bx0 + ox) * unit, by0 * unit, (bz0 + oz) * unit],
                          to=[(bx1 + ox) * unit, by1 * unit, (bz1 + oz) * unit], origin=[0, 0, 0], rot=[0, 0, 0], faces=fm))
    n_vox = len(cubes)

    # --- 板部 ---
    cache = {}

    def pal_fn(rgb):
        if not quantize:  # 量子化なし: 明るさ・彩度だけ調整した実色（細かい絵になる）
            return tuple(int(round(c)) for c in obj2schem.adjust(rgb, gain, sat))
        q = (int(rgb[0]) >> 2, int(rgb[1]) >> 2, int(rgb[2]) >> 2)
        if q not in cache:
            blk = obj2schem.to_blocks({0: rgb}, palette, gain, sat)[0]
            cache[q] = tuple(palette[blk])
        return cache[q]

    expected_plates = []
    skipped = 0
    for q in polys:
        if not is_plate(q):
            continue
        bpoly = dict(q, pos=[to_bb(p) for p in q['pos']])
        tx = fine_texel if (fine_re and fine_texel and fine_re.search(q['part'])) else texel  # 顔など一部だけ細かい絵
        pl = make_plate(bpoly, textures, pal_fn, unit, thickness, tx, coverage)
        if pl is None:
            skipped += 1
            continue
        idx = len(cubes) - n_vox
        fm = {'up': (region(pl['pw'], pl['ph'], [p if p else (0, 0, 0, 0) for p in pl['pix']]), False),
              'down': (None, True)}
        if thickness > 0:
            fm['down'] = (fm['up'][0], True)  # 内側も同じ絵（上下反転で向きを合わせる）
        else:
            del fm['down']  # 厚み0では表裏が同じ位置で重なりチラつくので1面だけ。裏はテクスチャの両面表示で見せる
        if thickness > 0:  # 厚み0の板は側面を描かない（浮き出た斜めの線の原因）
            for f in ('north', 'south', 'east', 'west'):
                fm[f] = (region(1, 1, [pl['edge'][f]]), False)
        cubes.append(dict(name=f'p{idx}', frm=pl['frm'], to=pl['to'], origin=pl['C'], rot=pl['rot'], faces=fm))
        if dump_expected is not None:
            expected_plates.append(dict(name=f'p{idx}', C=pl['C'], X=pl['X'], N=pl['N'], Z=pl['Z'], w=pl['w'], h=pl['h'],
                                        t=pl['t'], pw=pl['pw'], ph=pl['ph'], pix=[list(p) if p else [0, 0, 0, 0] for p in pl['pix']]))
    n_plate = len(cubes) - n_vox

    # --- アトラス ---
    size_px, pos = voxel2bbmodel.pack(regions)
    img = Image.new('RGBA', (size_px, size_px), (0, 0, 0, 0))
    px = img.load()
    for (rw, _rh), (rx, ry), pix in zip(regions, pos, pixels):
        for i, rgba in enumerate(pix):
            px[rx + i % rw, ry + i // rw] = tuple(rgba) if len(rgba) == 4 else tuple(rgba) + (255,)
    os.makedirs(outdir, exist_ok=True)
    png_path = os.path.join(outdir, f'{name}.png')
    img.save(png_path, optimize=True)

    def uvrect(rid, flip):
        rx, ry = pos[rid]
        rw, rh = regions[rid]
        return [rx, ry + rh, rx + rw, ry] if flip else [rx, ry, rx + rw, ry + rh]

    elements, geo_cubes, child_ids = [], [], []
    for i, c in enumerate(cubes):
        faces = {f: ({'uv': uvrect(*c['faces'][f]), 'texture': 0} if f in c['faces'] else {'uv': [0, 0, 0, 0], 'texture': None})
                 for f in voxel2bbmodel.FACES}
        cid = uid('cube', i)
        child_ids.append(cid)
        rnd = lambda v: [round(x, 4) for x in v]
        el = dict(name=c['name'], box_uv=False, **{'from': rnd(c['frm']), 'to': rnd(c['to'])}, faces=faces, type='cube', uuid=cid)
        if any(abs(r) > 1e-6 for r in c['rot']):
            el['origin'] = rnd(c['origin'])
            el['rotation'] = rnd(c['rot'])
        elements.append(el)
        guv = {}
        for f in voxel2bbmodel.FACES:
            if f not in c['faces']:
                continue
            u1, v1, u2, v2 = faces[f]['uv']
            guv[f] = ({'uv': [u2, v2], 'uv_size': [-(u2 - u1), -(v2 - v1)]} if f in ('up', 'down')
                      else {'uv': [u1, v1], 'uv_size': [u2 - u1, v2 - v1]})
        frm, to = el['from'], el['to']
        g = {'origin': [-to[0], frm[1], frm[2]], 'size': [round(to[k] - frm[k], 4) for k in range(3)]}
        if 'rotation' in el:
            g['pivot'] = [-el['origin'][0], el['origin'][1], el['origin'][2]]
            g['rotation'] = [-el['rotation'][0], -el['rotation'][1], el['rotation'][2]]
        g['uv'] = guv
        geo_cubes.append(g)

    group_id = uid('group', 'root')
    tex = dict(
        path='', folder='', namespace='', id='0', group='', scope=0, name=f'{name}.png', width=size_px, height=size_px,
        uv_width=size_px, uv_height=size_px, particle=False, use_as_default=False, layers_enabled=False, sync_to_project='',
        file_format='png', render_mode='default', render_sides='double' if thickness == 0 else 'auto',  # 厚み0の板は両面表示
        wrap_mode='limited', pbr_channel='color',
        fps=7, frame_time=1, frame_order_type='loop', frame_order='', frame_interpolate=False, visible=True,
        internal=True, saved=False, uuid=uid('tex'),
        source='data:image/png;base64,' + base64.b64encode(open(png_path, 'rb').read()).decode('ascii'))
    doc = dict(
        meta=dict(format_version='5.0', model_format='bedrock', box_uv=False),
        name=name, model_identifier=name, visible_box=[1, 1, 0], variable_placeholders='', multi_file_ruleset='',
        variable_placeholder_buttons=[], timeline_setups=[], unhandled_root_fields={},
        resolution=dict(width=size_px, height=size_px), elements=elements,
        groups=[dict(name='root', uuid=group_id, export=True, locked=False, scope=0, selected=False, visibility=True,
                     origin=[0, 0, 0], rotation=[0, 0, 0], bedrock_binding='', color=0, children=child_ids,
                     reset=False, shade=True, mirror_uv=False, autouv=0, isOpen=True)],
        outliner=[dict(uuid=group_id, isOpen=True, children=child_ids)], textures=[tex])
    bb_path = os.path.join(outdir, f'{name}.bbmodel')
    with open(bb_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))

    # 可視範囲: 回転後の8頂点の外接箱（Blockbench は各キューブの実メッシュの外接箱を使う）+ 各軸 +8
    lo, hi = [1e18] * 3, [-1e18] * 3
    for c in cubes:
        rot = c['rot']
        if any(abs(r) > 1e-6 for r in rot):
            rz, ry, rx = (math.radians(rot[2]), math.radians(rot[1]), math.radians(rot[0]))
            cx, cy, cz = math.cos(rx), math.cos(ry), math.cos(rz)
            sx, sy, sz = math.sin(rx), math.sin(ry), math.sin(rz)
            R = [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
                 [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
                 [-sy, cy * sx, cy * cx]]
        else:
            R = None
        for ix in (0, 1):
            for iy in (0, 1):
                for iz in (0, 1):
                    p = [c['to'][0] if ix else c['frm'][0], c['to'][1] if iy else c['frm'][1], c['to'][2] if iz else c['frm'][2]]
                    if R:
                        d = sub(p, c['origin'])
                        p = add(c['origin'], [sum(R[r][k] * d[k] for k in range(3)) for r in range(3)])
                    for k in range(3):
                        lo[k], hi[k] = min(lo[k], p[k]), max(hi[k], p[k])
    radius = max(hi[0] + 8, hi[2] + 8, -(lo[0] + 8), -(lo[2] + 8))
    y_min, y_max = min(math.floor((lo[1] + 8) / 16), -0.5), max(math.ceil((hi[1] + 8) / 16), 0.5)
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': f'geometry.{name}', 'texture_width': size_px, 'texture_height': size_px,
                        'visible_bounds_width': max(math.ceil(radius * 2 / 16), 1), 'visible_bounds_height': y_max - y_min,
                        'visible_bounds_offset': [0, (y_max + y_min) / 2, 0]},
        'bones': [{'name': 'root', 'pivot': [0, 0, 0], 'cubes': geo_cubes}]}]}
    geo_path = os.path.join(outdir, f'{name}.geo.json')
    with open(geo_path, 'w', encoding='utf-8') as f:
        json.dump(geo, f, ensure_ascii=False, separators=(',', ':'))
    if dump_expected is not None:
        with open(dump_expected, 'w', encoding='utf-8') as f:
            json.dump(dict(vox=expected_vox, plates=expected_plates, unit=unit), f, separators=(',', ':'))
    quads = sum(len(c['faces']) for c in cubes)
    print(f'  ブロック部: ボクセル{len(solid)} -> キューブ{n_vox} / 板: キューブ{n_plate}(透明で省略 {skipped}) / 合計{len(cubes)}')
    print(f'  描画する面{quads} / 領域{len(regions)} / アトラス{size_px}x{size_px} / 寸法 {w}x{h}x{l} 前={"+Z(元)" if keep_front else "-Z"}')
    print('  ' + ', '.join(f'{os.path.basename(p)} {os.path.getsize(p) / 1024:.0f}KB' for p in (bb_path, geo_path, png_path)))
    return dict(cubes=len(cubes), vox=n_vox, plates=n_plate, quads=quads, atlas=size_px)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('gmo')
    ap.add_argument('outdir')
    ap.add_argument('--name', default='model')
    ap.add_argument('--size', type=int, default=128, help='最長辺のブロック数')
    ap.add_argument('--plates', default='^AL_body', help='斜めの板にするパーツ名（正規表現）')
    ap.add_argument('--exclude', default='TR_pattern', help='除外するパーツ名（正規表現）')
    ap.add_argument('--gain', type=float, default=1.3)
    ap.add_argument('--sat', type=float, default=1.3)
    ap.add_argument('--thickness', type=float, default=0.5, help='板の厚み（ブロック単位）')
    ap.add_argument('--texel', type=float, default=1.0, help='板のテクスチャ 1 ピクセルの大きさ（ブロック単位）')
    ap.add_argument('--unit', type=float, default=16, help='1ボクセルのモデル単位（--size を増やすなら 16*128/size 等にして全体の大きさを保つ）')
    ap.add_argument('--plate-tex', default=None, help='板にする面を、このテクスチャ名（正規表現）のものだけに絞る。残りはブロック')
    ap.add_argument('--no-quantize', action='store_true', help='板の絵をブロック色に量子化しない（実色。より細かい絵）')
    ap.add_argument('--coverage', type=float, default=0.5, help='板のピクセルを塗る、多角形の被覆率のしきい値')
    ap.add_argument('--fine-parts', default=None, help='このパーツ（正規表現）の板だけ絵を細かくする（例: ^AL_head）')
    ap.add_argument('--fine-texel', type=float, default=None, help='--fine-parts の板の 1 ピクセルの大きさ（ブロック単位）')
    ap.add_argument('--keep-front', action='store_true')
    ap.add_argument('--dump-expected', default=None)
    a = ap.parse_args()
    build(a.gmo, a.outdir, a.name, a.size, a.plates, a.exclude, a.gain, a.sat, a.thickness, a.texel, a.unit, a.keep_front,
          a.dump_expected, a.plate_tex, not a.no_quantize, a.coverage, a.fine_parts, a.fine_texel)
