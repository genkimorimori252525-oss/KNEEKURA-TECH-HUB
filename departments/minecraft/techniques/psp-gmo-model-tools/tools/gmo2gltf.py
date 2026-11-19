"""GMO(キャラモデル) + モーションGMO群 -> GLB（骨・スキンウェイト・アニメ付き）。

使い方:
  python gmo2gltf.py <model.gmo> <out.glb> [--motion a.gmo b.gmo ...] [--scale 0.01]

確定した構造（PSPのボス級モデルで実測）:
  骨 0x0004 : 0x8041 親(参照) / 0x8048 translation(3f) / 0x804b 回転クォータニオン(x,y,z,w)
              0x8044 スキン用の骨リスト(参照の並び) / 0x8045 その逆バインド行列(4x4, 行ベクトル規約) / 0x804e 持ち主パーツ
  メッシュのパレット 0x8062 = パーツの骨リストへの添字。重みの本数 = パレット数。パレットなし = リスト順。
  モーション 0x000b: 0x80b1 ループ(開始,終了フレーム) / 0x80b2 フレームレート
              0x80b3 (対象参照, cmd, _, fカーブ参照) cmd: 0x48 移動 / 0x4b 回転 / 0x4c 拡縮 / 0x98 UV(未対応)
              fカーブ 0x000c: 本体 = fmt,dims,keys,0 の後に keys 個の [時刻, 値×dims]（すべて float16、時刻はフレーム）
"""
import argparse, json, math, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim, gmo
from gmo2obj import read_array, read_indices, read_scale_bias

# ---------------------------------------------------------------- 行列 (4x4, 行優先の二重リスト, 列ベクトル規約)


def ident():
    return [[1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]


def mul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def trs(t, q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    m = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), t[0]],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), t[1]],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), t[2]],
         [0.0, 0.0, 0.0, 1.0]]
    return m


def rigid_inv(m):
    r = [[m[c][rr] for c in range(3)] for rr in range(3)]  # 転置
    t = [-sum(r[i][k] * m[k][3] for k in range(3)) for i in range(3)]
    return [r[0] + [t[0]], r[1] + [t[1]], r[2] + [t[2]], [0.0, 0.0, 0.0, 1.0]]


def colmajor(m):
    return [m[r][c] for c in range(4) for r in range(4)]


# ---------------------------------------------------------------- モデル読み取り


def read_bones(model):
    bones = []
    for b in model.kids(4):
        par = b.kid(0x8041)
        tr = b.kid(0x8048)
        rot = b.kid(0x804b)
        bones.append(dict(
            name=b.name,
            parent=gmo.ref(struct.unpack_from('<I', par.payload)[0]) if par else -1,
            t=struct.unpack_from('<3f', tr.payload) if tr else (0.0, 0.0, 0.0),
            q=struct.unpack_from('<4f', rot.payload) if rot else (0.0, 0.0, 0.0, 1.0),
            chunk=b))
    return bones


def world_matrices(bones, scale):
    W = [None] * len(bones)

    def get(i):
        if W[i] is None:
            b = bones[i]
            local = trs([v * scale for v in b['t']], b['q'])
            W[i] = local if b['parent'] < 0 else mul(get(b['parent']), local)
        return W[i]
    for i in range(len(bones)):
        get(i)
    return W


def part_bone_lists(model, bones):
    """パーツ番号 -> そのパーツのスキン骨リスト(グローバル骨番号の並び) と 逆バインド行列(ファイル値)。"""
    out = {}
    for b in bones:
        p = b['chunk'].kid(0x804e)
        lst = b['chunk'].kid(0x8044)
        if p is None or lst is None:
            continue
        n = struct.unpack_from('<I', lst.payload)[0]
        refs = [gmo.ref(v) for v in struct.unpack_from('<%dI' % n, lst.payload, 4)]
        mats = b['chunk'].kid(0x8045)
        ibs = [struct.unpack_from('<16f', mats.payload, 4 + 64 * k) for k in range(n)] if mats else []
        out[gmo.ref(struct.unpack_from('<I', p.payload)[0])] = (refs, ibs)
    return out


# ---------------------------------------------------------------- モーション


def read_motion(path):
    d = open(path, 'rb').read()
    model = gmo.parse(d)[0].children[0]
    take = model.kid(0x0b)
    if take is None:
        return None
    # 0x80b1 の中身: float 開始フレーム, float 終了フレーム (実測: 00 00 00 00 | 00 00 c8 43 = 0, 400)
    loop = struct.unpack_from('<2f', take.kid(0x80b1).payload, 0) if take.kid(0x80b1) else (0.0, 0.0)
    rate = struct.unpack_from('<f', take.kid(0x80b2).payload)[0] if take.kid(0x80b2) else 30.0
    fcs = []
    for fc in take.kids(0x0c):
        b = fc.body
        _fmt, dims, keys, _ = struct.unpack_from('<4I', b, 0)
        per = 2 * (1 + dims)
        times, vals = [], []
        for k in range(keys):
            row = struct.unpack_from('<%de' % (1 + dims), b, 16 + k * per)
            times.append(row[0])
            vals.append(list(row[1:]))
        fcs.append((dims, times, vals))
    chans = []
    for a in take.kids(0x80b3):
        tgt, cmd, _ix, fcref = struct.unpack_from('<4I', a.payload)
        if (tgt >> 16) == 4 and cmd in (0x48, 0x4b, 0x4c) and gmo.ref(fcref) < len(fcs):
            chans.append((gmo.ref(tgt), cmd, gmo.ref(fcref)))
    return dict(rate=rate or 30.0, loop=loop, fcurves=fcs, channels=chans)


# ---------------------------------------------------------------- glTF 組み立て


class Glb:
    def __init__(self):
        self.bin = bytearray()
        self.views, self.accessors = [], []

    def view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        v = dict(buffer=0, byteOffset=len(self.bin), byteLength=len(data))
        if target:
            v['target'] = target
        self.bin += data
        self.views.append(v)
        return len(self.views) - 1

    def accessor(self, fmt, values, ctype, atype, target=None, minmax=False):
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[atype]
        flat = [x for v in values for x in (v if isinstance(v, (list, tuple)) else (v,))]
        data = struct.pack('<%d%s' % (len(flat), fmt), *flat)
        a = dict(bufferView=self.view(data, target), componentType=ctype, count=len(values), type=atype)
        if minmax and values:
            cols = [[(v if isinstance(v, (list, tuple)) else (v,))[i] for v in values] for i in range(n)]
            a['min'] = [min(c) for c in cols]
            a['max'] = [max(c) for c in cols]
        self.accessors.append(a)
        return len(self.accessors) - 1


F32, U16 = 5126, 5123


def build(model_path, motion_paths, out_path, scale=0.01):
    d = open(model_path, 'rb').read()
    model = gmo.parse(d)[0].children[0]
    sb = read_scale_bias(model)
    bones = read_bones(model)
    W = world_matrices(bones, scale)
    plists = part_bone_lists(model, bones)
    g = Glb()

    # 自己検証: 逆バインド行列(ファイル) と 骨ワールド行列の逆行列の一致
    worst = 0.0
    W1 = world_matrices(bones, 1.0)
    for refs, ibs in plists.values():
        for r, ib in zip(refs, ibs):
            mine = colmajor(rigid_inv(W1[r]))
            worst = max(worst, max(abs(a - b) for a, b in zip(mine, ib)))
    print(f'  逆バインド行列の最大誤差(ファイル値 vs 骨から計算): {worst:.4f}')

    # --- テクスチャ/材質 ---
    images, textures = [], []
    alpha_of = []
    for t in model.kids(0x0a):
        pl = t.kid(0x8013).payload
        n = struct.unpack_from('<I', pl)[0]
        png, partial, zero = gim.to_png_bytes(pl[4:4 + n])
        images.append(dict(bufferView=g.view(png), mimeType='image/png', name=t.name))
        textures.append(dict(source=len(images) - 1, sampler=0))
        alpha_of.append('BLEND' if partial else 'MASK' if zero else 'OPAQUE')
    materials = []
    for m in model.kids(8):
        ti = None
        for layer in m.kids(9):
            r = layer.kid(0x8091)
            if r is not None:
                ti = gmo.ref(struct.unpack_from('<I', r.payload)[0])
                break
        mat = dict(name=m.name, doubleSided=True,
                   pbrMetallicRoughness=dict(metallicFactor=0.0, roughnessFactor=1.0))
        if ti is not None and ti < len(textures):
            mat['pbrMetallicRoughness']['baseColorTexture'] = dict(index=ti)
            mat['alphaMode'] = alpha_of[ti]
            if alpha_of[ti] == 'MASK':
                mat['alphaCutoff'] = 0.5
        materials.append(mat)

    # --- 骨ノード ---
    nodes = []
    for i, b in enumerate(bones):
        n = dict(name=b['name'], translation=[v * scale for v in b['t']])
        if any(abs(c) > 1e-9 for c in b['q'][:3]) or abs(b['q'][3] - 1) > 1e-9:
            nq = math.sqrt(sum(c * c for c in b['q'])) or 1.0
            n['rotation'] = [c / nq for c in b['q']]
        children = [j for j, o in enumerate(bones) if o['parent'] == i]
        if children:
            n['children'] = children
        nodes.append(n)
    ib_acc = g.accessor('f', [colmajor(rigid_inv(W[i])) for i in range(len(bones))], F32, 'MAT4')
    skin = dict(name='skin', joints=list(range(len(bones))), inverseBindMatrices=ib_acc)

    # --- パーツごとのメッシュ ---
    meshes = []
    for pi, part in enumerate(model.kids(5)):
        refs, _ibs = plists[pi]
        arrays = part.kids(7)
        cache = {}
        merged = {}  # (配列キー, 材質) -> 索引列。同じ頂点配列・材質のメッシュは1プリミティブに統合
        prims = []
        for mesh in part.kids(6):
            mr = mesh.kid(0x8061)
            mi = gmo.ref(struct.unpack_from('<I', mr.payload)[0]) if mr is not None else None
            pal = mesh.kid(0x8062)
            palette = None
            if pal is not None:
                k = struct.unpack_from('<I', pal.payload)[0]
                palette = tuple(struct.unpack_from('<%dI' % k, pal.payload, 4))
            for ar, polys in read_indices(mesh):
                key = (ar, palette)
                if key not in cache:
                    arr = read_array(arrays[ar], sb)
                    lay = gmo.ge_layout(arr['fmt'])
                    wc = lay['weights'][2]
                    pals = palette if palette is not None else tuple(range(wc))
                    pos = [[c * scale for c in p] for p in arr['pos']]
                    attrs = dict(POSITION=g.accessor('f', pos, F32, 'VEC3', 34962, True))
                    if arr['nrm']:
                        # 8bit量子化の法線は長さが1からずれるので正規化（glTFは単位長を要求）
                        nrm = []
                        for v in arr['nrm']:
                            ln = math.sqrt(sum(c * c for c in v)) or 1.0
                            nrm.append([c / ln for c in v])
                        attrs['NORMAL'] = g.accessor('f', nrm, F32, 'VEC3', 34962)
                    if arr['uv']:
                        attrs['TEXCOORD_0'] = g.accessor('f', [list(v) for v in arr['uv']], F32, 'VEC2', 34962)
                    joints, weights = [], []
                    for w in arr['weights']:
                        ent = sorted(((refs[pals[k]], w[k]) for k in range(wc) if w[k] > 0), key=lambda e: -e[1])
                        if not ent:
                            ent = [(refs[pals[0]], 1.0)]
                        tot = sum(e[1] for e in ent)
                        ent = [(j, x / tot) for j, x in ent]
                        ent += [(0, 0.0)] * (8 - len(ent)) if len(ent) < 8 else []
                        joints.append([e[0] for e in ent[:8]])
                        weights.append([e[1] for e in ent[:8]])
                    attrs['JOINTS_0'] = g.accessor('H', [j[:4] for j in joints], U16, 'VEC4', 34962)
                    attrs['WEIGHTS_0'] = g.accessor('f', [w[:4] for w in weights], F32, 'VEC4', 34962)
                    if any(w[4] > 0 for w in weights):
                        attrs['JOINTS_1'] = g.accessor('H', [j[4:] for j in joints], U16, 'VEC4', 34962)
                        attrs['WEIGHTS_1'] = g.accessor('f', [w[4:] for w in weights], F32, 'VEC4', 34962)
                    cache[key] = attrs
                tris = []
                for q in polys:
                    if len(q) == 3:
                        tris.append(tuple(q))
                    else:  # 四角: 輪郭順 (a,b,c,d) -> (a,b,c),(a,c,d)
                        tris += [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
                merged.setdefault((key, mi), []).extend(i for t in tris for i in t)
        for (key, mi), idx in merged.items():
            prim = dict(attributes=cache[key], mode=4,
                        indices=g.accessor('H', idx, U16, 'SCALAR', 34963))
            if mi is not None and mi < len(materials):
                prim['material'] = mi
            prims.append(prim)
        meshes.append(dict(name=part.name, primitives=prims))
    mesh_nodes = []
    for i, m in enumerate(meshes):
        nodes.append(dict(name=m['name'], mesh=i, skin=0))
        mesh_nodes.append(len(nodes) - 1)

    # --- アニメーション ---
    anims = []
    for mp in motion_paths:
        mo = read_motion(mp)
        if not mo:
            continue
        samplers, channels = [], []
        for bone, cmd, fci in mo['channels']:
            if bone >= len(bones):
                continue
            dims, times, vals = mo['fcurves'][fci]
            if not times:
                continue
            secs = [t / mo['rate'] for t in times]
            if cmd == 0x48:
                path, out = 'translation', [[c * scale for c in v] for v in vals]
            elif cmd == 0x4c:
                path, out = 'scale', vals
            else:
                path = 'rotation'
                out, prev = [], None
                for v in vals:
                    n = math.sqrt(sum(c * c for c in v)) or 1.0
                    v = [c / n for c in v]
                    if prev and sum(a * b for a, b in zip(v, prev)) < 0:
                        v = [-c for c in v]
                    out.append(v)
                    prev = v
            si = len(samplers)
            samplers.append(dict(
                input=g.accessor('f', secs, F32, 'SCALAR', None, True),
                output=g.accessor('f', out, F32, {'translation': 'VEC3', 'scale': 'VEC3', 'rotation': 'VEC4'}[path]),
                interpolation='LINEAR'))
            channels.append(dict(sampler=si, target=dict(node=bone, path=path)))
        name = os.path.splitext(os.path.basename(mp))[0]
        prefix = os.path.splitext(os.path.basename(model_path))[0].upper() + '_'
        if name.upper().startswith(prefix):
            name = name[len(prefix):]
        anims.append(dict(name=name, samplers=samplers, channels=channels,
                          extras=dict(frameRate=mo['rate'], loopStartFrame=mo['loop'][0], loopEndFrame=mo['loop'][1])))

    gltf = dict(
        asset=dict(version='2.0', generator='gmo2gltf (自作)'),
        scene=0,
        scenes=[dict(nodes=[i for i, b in enumerate(bones) if b['parent'] < 0] + mesh_nodes)],
        nodes=nodes, meshes=meshes, skins=[skin], materials=materials,
        textures=textures, images=images,
        samplers=[dict(magFilter=9729, minFilter=9987, wrapS=10497, wrapT=10497)],
        accessors=g.accessors, bufferViews=g.views,
        buffers=[dict(byteLength=len(g.bin))])
    if anims:
        gltf['animations'] = anims
    js = json.dumps(gltf, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    js += b' ' * (-len(js) % 4)
    binb = bytes(g.bin) + b'\0' * (-len(g.bin) % 4)
    with open(out_path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binb)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A) + js)
        f.write(struct.pack('<II', len(binb), 0x004E4942) + binb)
    nprim = sum(len(m['primitives']) for m in meshes)
    print(f'  -> {out_path}  骨{len(bones)} メッシュ{len(meshes)} プリミティブ{nprim} 材質{len(materials)} '
          f'テクスチャ{len(images)} アニメ{len(anims)} ({os.path.getsize(out_path) / 1024:.0f} KB)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('gmo')
    ap.add_argument('out')
    ap.add_argument('--motion', nargs='*', default=[])
    ap.add_argument('--scale', type=float, default=0.01)
    a = ap.parse_args()
    build(a.gmo, a.motion, a.out, a.scale)
