"""GMO(OMG.00.1PSP) -> OBJ + MTL + PNG。基準姿勢（スキニング前）で書き出す。

使い方: python gmo2obj.py <in.gmo> <出力フォルダ> [--scale 0.01] [--quad strip|ring|auto] [--flip auto|yes|no]

基準姿勢について: スキン部の逆バインド行列は骨ワールド行列の逆行列で、積は単位行列になる
（PSPのボス級モデルで実測）。つまり頂点データはそのままモデル空間の座標。
"""
import argparse, math, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim, gmo


def read_scale_bias(model):
    pos_bias, pos_scale, uv_bias, uv_scale = (0, 0, 0), (1, 1, 1), (0, 0), (1, 1)
    for c in model.kids(0x8015):
        pl = c.payload
        kind = struct.unpack_from('<I', pl)[0]
        if kind == 384:
            f = struct.unpack_from('<6f', pl, 4)
            pos_bias, pos_scale = f[:3], f[3:]
        elif kind == 3:
            f = struct.unpack_from('<4f', pl, 4)
            uv_bias, uv_scale = f[:2], f[2:]
    return pos_bias, pos_scale, uv_bias, uv_scale


def read_array(a, sb):
    """頂点配列チャンク -> dict(pos=[(x,y,z)], uv=[(u,v)], nrm=[...], weights=[[...]])。"""
    pos_bias, pos_scale, uv_bias, uv_scale = sb
    b = a.body
    fmt, n = struct.unpack_from('<II', b, 0)
    lay = gmo.ge_layout(fmt)
    stride, base = lay['stride'], 16
    out = dict(pos=[], uv=[], nrm=[], weights=[], fmt=fmt)
    for i in range(n):
        o = base + i * stride * lay['morphs']  # モーフ0だけ使う
        po, pt = lay['pos']
        if pt == 2:
            x, y, z = (v / 32768.0 for v in struct.unpack_from('<3h', b, o + po))
        elif pt == 1:
            x, y, z = (v / 128.0 for v in struct.unpack_from('<3b', b, o + po))
        else:
            x, y, z = struct.unpack_from('<3f', b, o + po)
        out['pos'].append((x * pos_scale[0] + pos_bias[0], y * pos_scale[1] + pos_bias[1], z * pos_scale[2] + pos_bias[2]))
        if 'tc' in lay:
            to, tt = lay['tc']
            if tt == 2:
                u, v = (q / 32768.0 for q in struct.unpack_from('<2H', b, o + to))
            elif tt == 1:
                u, v = (q / 128.0 for q in struct.unpack_from('<2B', b, o + to))
            else:
                u, v = struct.unpack_from('<2f', b, o + to)
            out['uv'].append((u * uv_scale[0] + uv_bias[0], v * uv_scale[1] + uv_bias[1]))
        if 'normal' in lay:
            no, nt = lay['normal']
            if nt == 1:
                nx, ny, nz = (q / 127.0 for q in struct.unpack_from('<3b', b, o + no))
            elif nt == 2:
                nx, ny, nz = (q / 32767.0 for q in struct.unpack_from('<3h', b, o + no))
            else:
                nx, ny, nz = struct.unpack_from('<3f', b, o + no)
            out['nrm'].append((nx, ny, nz))
        if 'weights' in lay:
            wo, wt, wc = lay['weights']
            if wt == 1:
                out['weights'].append([q / 128.0 for q in struct.unpack_from('<%dB' % wc, b, o + wo)])
    return out


def read_indices(mesh):
    """メッシュ内の 0x8066 -> [(配列番号, [面の頂点index列...])]。
    primType 3: 三角形リスト(a1=索引数)。primType 5: a1頂点ずつの多角形をa2個(3=三角,4=四角)。"""
    res = []
    for c in mesh.kids(0x8066):
        pl = c.payload
        ar, _unk, prim, a1, a2 = struct.unpack_from('<HHiii', pl, 0)
        ar = gmo.ref(ar)
        if prim == 3:
            n = a1
            idx = struct.unpack_from('<%dH' % n, pl, 16)
            polys = [idx[i:i + 3] for i in range(0, n - 2, 3)]
        elif prim == 5:
            stride, cnt = a1, a2
            idx = struct.unpack_from('<%dH' % (stride * cnt), pl, 16)
            polys = [idx[i * stride:(i + 1) * stride] for i in range(cnt)]
        else:
            print(f'  ! 未対応primType={prim}', file=sys.stderr)
            continue
        res.append((ar, polys))
    return res


def dist(p, q):
    return math.dist(p, q)


def convert(path, outdir, scale=1.0, quad='auto', flip='auto'):
    d = open(path, 'rb').read()
    model = gmo.parse(d)[0].children[0]
    parts = model.kids(5)
    if not parts:
        print('  (形状なし: モーション/ボーンのみ)')
        return None
    sb = read_scale_bias(model)
    name = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(outdir, exist_ok=True)
    texdir = os.path.join(outdir, 'textures')
    os.makedirs(texdir, exist_ok=True)

    # --- テクスチャ ---
    texfiles = []
    for i, t in enumerate(model.kids(0x0a)):
        p12, p13 = t.kid(0x8012), t.kid(0x8013)
        orig = p12.payload.split(b'\0')[0].decode('latin1').replace('\\', '/').split('/')[-1] if p12 else f'tex{i}'
        stem = os.path.splitext(orig)[0]
        fn = f'{i:02d}_{stem}.png'
        pl = p13.payload
        n = struct.unpack_from('<I', pl)[0]
        gim.to_png(pl[4:4 + n], os.path.join(texdir, fn))
        texfiles.append(fn)

    # --- 材質 ---
    mats = []
    for m in model.kids(8):
        tex = None
        for layer in m.kids(9):
            r = layer.kid(0x8091)
            if r is not None:
                ti = gmo.ref(struct.unpack_from('<I', r.payload)[0])
                if ti < len(texfiles):
                    tex = texfiles[ti]
                    break
        mats.append((m.name, tex))
    with open(os.path.join(outdir, name + '.mtl'), 'w', encoding='utf-8') as f:
        for i, (mn, tex) in enumerate(mats):
            f.write(f'newmtl mat{i}_{mn}\nKa 1 1 1\nKd 1 1 1\nKs 0 0 0\nd 1\n')
            if tex:
                f.write(f'map_Kd textures/{tex}\nmap_d textures/{tex}\n')
            f.write('\n')

    # --- 形状を集める ---
    P = []  # (part名, mesh名, 材質, 頂点配列, polys)
    arrays_by_part = []
    for pt in parts:
        arrs = [read_array(a, sb) for a in pt.kids(7)]
        arrays_by_part.append(arrs)
        for mesh in pt.kids(6):
            mr = mesh.kid(0x8061)
            mi = gmo.ref(struct.unpack_from('<I', mr.payload)[0]) if mr is not None else None
            for ar, polys in read_indices(mesh):
                P.append((pt.name, mesh.name, mi, arrs[ar], polys))

    # --- 四角形の頂点順を実測で決める ---
    ring_better = strip_better = 0
    for _p, _m, _mi, arr, polys in P:
        for q in polys:
            if len(q) == 4:
                v = [arr['pos'][i] for i in q]
                ring = dist(v[0], v[1]) + dist(v[1], v[2]) + dist(v[2], v[3]) + dist(v[3], v[0])
                strip = dist(v[0], v[1]) + dist(v[1], v[3]) + dist(v[3], v[2]) + dist(v[2], v[0])
                if ring < strip - 1e-6:
                    ring_better += 1
                elif strip < ring - 1e-6:
                    strip_better += 1
    if quad == 'auto':
        quad = 'ring' if ring_better >= strip_better else 'strip'
    print(f'  四角形の頂点順: ring有利={ring_better} strip有利={strip_better} -> {quad}')

    def tris_of(q):
        if len(q) == 3:
            return [tuple(q)]
        a, b, c, e = q
        if quad == 'ring':
            return [(a, b, c), (a, c, e)]
        return [(a, b, c), (c, b, e)]

    # --- 面の向きを法線で判定 ---
    agree = disagree = 0
    for _p, _m, _mi, arr, polys in P:
        if not arr['nrm']:
            continue
        for q in polys:
            for (i, j, k) in tris_of(q):
                a, b, c = arr['pos'][i], arr['pos'][j], arr['pos'][k]
                u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
                v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
                fn = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                n = [sum(arr['nrm'][t][ax] for t in (i, j, k)) for ax in range(3)]
                dot = fn[0] * n[0] + fn[1] * n[1] + fn[2] * n[2]
                if dot > 0:
                    agree += 1
                elif dot < 0:
                    disagree += 1
    if flip == 'auto':
        flip = 'yes' if disagree > agree else 'no'
    print(f'  面の向き: 法線と一致={agree} 逆={disagree} -> 反転={flip}')

    # --- OBJ書き出し ---
    base = 1
    seen = {}
    nf = 0
    with open(os.path.join(outdir, name + '.obj'), 'w', encoding='utf-8') as f:
        f.write(f'# {name}  (GMO -> OBJ, rest pose)\nmtllib {name}.mtl\n')
        # 配列ごとに頂点を一度だけ書く
        for pi, arrs in enumerate(arrays_by_part):
            for ai, arr in enumerate(arrs):
                seen[(pi, ai)] = base
                for (x, y, z) in arr['pos']:
                    f.write(f'v {x * scale:.5f} {y * scale:.5f} {z * scale:.5f}\n')
                for (u, v) in arr['uv']:
                    f.write(f'vt {u:.6f} {1.0 - v:.6f}\n')
                for (nx, ny, nz) in arr['nrm']:
                    f.write(f'vn {nx:.5f} {ny:.5f} {nz:.5f}\n')
                arr['_base'] = base
                base += len(arr['pos'])
        for pname, mname, mi, arr, polys in P:
            f.write(f'g {pname}__{mname}\n')
            if mi is not None and mi < len(mats):
                f.write(f'usemtl mat{mi}_{mats[mi][0]}\n')
            has_vt, has_vn = bool(arr['uv']), bool(arr['nrm'])
            for q in polys:
                for tri in tris_of(q):
                    if flip == 'yes':
                        tri = (tri[0], tri[2], tri[1])
                    refs = []
                    for i in tri:
                        g = arr['_base'] + i
                        refs.append(f'{g}/{g}/{g}' if has_vt and has_vn else f'{g}//{g}' if has_vn else f'{g}/{g}' if has_vt else f'{g}')
                    f.write('f ' + ' '.join(refs) + '\n')
                    nf += 1
    print(f'  -> {name}.obj  頂点{base - 1} 面{nf} パーツ{len(parts)} 材質{len(mats)} テクスチャ{len(texfiles)}')
    return dict(quad=quad, flip=flip, verts=base - 1, faces=nf)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('gmo')
    ap.add_argument('outdir')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--quad', default='auto', choices=['auto', 'ring', 'strip'])
    ap.add_argument('--flip', default='auto', choices=['auto', 'yes', 'no'])
    a = ap.parse_args()
    convert(a.gmo, a.outdir, a.scale, a.quad, a.flip)
