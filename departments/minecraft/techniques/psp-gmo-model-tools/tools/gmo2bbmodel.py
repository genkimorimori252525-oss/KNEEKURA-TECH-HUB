"""GMO(キャラモデル) -> Blockbench .bbmodel（Generic Model / メッシュ + 骨格 + ウェイト + テクスチャ）。

使い方:
  python gmo2bbmodel.py <model.gmo> <out.bbmodel> [--scale 0.05] [--north] [--motion a.gmo ...]

Blockbench 5.2.1 を実機で確認した書式:
  - armature の下に armature_bone（入れ子）と mesh を並べる。メッシュの頂点は骨の「現在の姿勢」を束縛姿勢として扱う。
  - 骨 origin は親からの相対（親の回転も効く）、rotation は Euler ZYX の度数。
  - ウェイトは骨側 vertex_weights["<メッシュuuid先頭6文字>:<頂点キー>"] = 重み。Blockbench は頂点あたり最大4本。
  - 面 faces[key] = {vertices:[...], uv:{頂点キー:[u,v]}(テクスチャのピクセル), texture:番号}
  --north: モデルをY軸まわりに180°回し、前を -Z（マイクラのエンティティの北向き）にする。既定は元の向き(+Z)のまま。
"""
import argparse, base64, json, math, os, struct, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim, gmo
from gmo2gltf import read_bones, part_bone_lists, read_motion, trs
from gmo2obj import read_array, read_indices, read_scale_bias

NS = uuid.UUID('6b6f6d61-646f-6b61-6d61-6769636f7061')


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(str(p) for p in parts)))


def euler_zyx(q):
    """クォータニオン(x,y,z,w) -> three.js 'ZYX' の Euler(度)。"""
    m = trs((0, 0, 0), q)
    y = math.asin(-max(-1.0, min(1.0, m[2][0])))
    if abs(m[2][0]) < 0.9999999:
        x = math.atan2(m[2][1], m[2][2])
        z = math.atan2(m[1][0], m[0][0])
    else:
        x = 0.0
        z = math.atan2(-m[0][1], m[1][1])
    return [math.degrees(x), math.degrees(y), math.degrees(z)]


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def build(model_path, out_path, scale=0.05, north=False, motion_paths=()):
    d = open(model_path, 'rb').read()
    model = gmo.parse(d)[0].children[0]
    sb = read_scale_bias(model)
    bones = read_bones(model)
    plists = part_bone_lists(model, bones)
    name = os.path.splitext(os.path.basename(model_path))[0]

    def tp(p):  # 位置の変換（スケール + 任意で北向き）
        x, y, z = p
        if north:
            x, z = -x, -z
        return [x * scale, y * scale, z * scale]

    # --- テクスチャ ---
    textures, tex_size = [], []
    for i, t in enumerate(model.kids(0x0a)):
        p12, p13 = t.kid(0x8012), t.kid(0x8013)
        orig = p12.payload.split(b'\0')[0].decode('latin1').replace('\\', '/').split('/')[-1] if p12 else f'tex{i}'
        pl = p13.payload
        n = struct.unpack_from('<I', pl)[0]
        gimdata = pl[4:4 + n]
        w, h, _ = gim.decode(gimdata)
        png, _partial, _zero = gim.to_png_bytes(gimdata)
        tex_size.append((w, h))
        textures.append(dict(
            path='', folder='', namespace='', id=str(i), group='', scope=0,
            name=os.path.splitext(orig)[0] + '.png', width=w, height=h, uv_width=w, uv_height=h,
            particle=False, use_as_default=False, layers_enabled=False, sync_to_project='',
            file_format='png', render_mode='default', render_sides='double', wrap_mode='limited',
            pbr_channel='color', fps=7, frame_time=1, frame_order_type='loop', frame_order='',
            frame_interpolate=False, visible=True, internal=True, saved=False,
            uuid=uid('tex', i), source='data:image/png;base64,' + base64.b64encode(png).decode('ascii')))
    # --- 材質 -> テクスチャ番号 ---
    mat_tex = []
    for m in model.kids(8):
        ti = None
        for layer in m.kids(9):
            r = layer.kid(0x8091)
            if r is not None:
                ti = gmo.ref(struct.unpack_from('<I', r.payload)[0])
                break
        mat_tex.append(ti if ti is not None and ti < len(textures) else None)

    # --- 骨 ---
    ry = (0.0, 1.0, 0.0, 0.0)  # Y軸180°
    bone_el = []
    for i, b in enumerate(bones):
        t, q = list(b['t']), tuple(b['q'])
        if north and b['parent'] < 0:
            t = [-t[0], t[1], -t[2]]
            q = qmul(ry, q)
        kids = [j for j, o in enumerate(bones) if o['parent'] == i]
        length = (math.dist((0, 0, 0), [c * scale for c in bones[kids[0]]['t']]) if kids else 8.0)
        bone_el.append(dict(
            isOpen=False, uuid=uid('bone', i), type='armature_bone', name=b['name'],
            children=[uid('bone', j) for j in kids], export=True, locked=False, scope=0,
            origin=[c * scale for c in t], rotation=euler_zyx(q),
            length=round(max(length, 1.0), 4), width=2, connected=False, color=i % 8,
            vertex_weights={}, allow_mirror_modeling=True))

    # --- メッシュ ---
    mesh_el, notes = [], dict(over4=0, verts=0, welded=0, faces=0, quads=0)
    for pi, part in enumerate(model.kids(5)):
        refs, _ibs = plists[pi]
        arrays = part.kids(7)
        built = {}  # (配列, パレット) -> mesh dict
        for mesh in part.kids(6):
            mr = mesh.kid(0x8061)
            mi = gmo.ref(struct.unpack_from('<I', mr.payload)[0]) if mr is not None else None
            ti = mat_tex[mi] if mi is not None and mi < len(mat_tex) else None
            pal = mesh.kid(0x8062)
            palette = None
            if pal is not None:
                k = struct.unpack_from('<I', pal.payload)[0]
                palette = tuple(struct.unpack_from('<%dI' % k, pal.payload, 4))
            for ar, polys in read_indices(mesh):
                key = (ar, palette)
                if key not in built:
                    arr = read_array(arrays[ar], sb)
                    wc = gmo.ge_layout(arr['fmt'])['weights'][2]
                    pals = palette if palette is not None else tuple(range(wc))
                    mid = uid('mesh', pi, ar, palette)
                    # 頂点ごとの重み（上位4本）
                    vw = []
                    for w in arr['weights']:
                        ent = sorted(((refs[pals[k]], w[k]) for k in range(wc) if w[k] > 0), key=lambda e: -e[1])
                        if not ent:
                            ent = [(refs[pals[0]], 1.0)]
                        if len(ent) > 4:
                            notes['over4'] += 1
                            ent = ent[:4]
                        tot = sum(e[1] for e in ent)
                        vw.append(tuple((j, round(x / tot, 5)) for j, x in ent))
                    # 位置と重みが同じ頂点を統合
                    weld, verts, vmap = {}, {}, []
                    for vi, p in enumerate(arr['pos']):
                        wk = (tuple(round(c, 3) for c in p), vw[vi])
                        if wk not in weld:
                            weld[wk] = f'v{len(weld)}'
                            verts[weld[wk]] = tp(p)
                            for j, x in vw[vi]:
                                bone_el[j]['vertex_weights'][f'{mid[:6]}:{weld[wk]}'] = x
                        vmap.append(weld[wk])
                    notes['verts'] += len(arr['pos'])
                    notes['welded'] += len(verts)
                    built[key] = dict(
                        name=f'{part.name}.{ar:02d}', color=0, origin=[0, 0, 0], rotation=[0, 0, 0], shading='flat',
                        export=True, visibility=True, locked=False, render_order='default', scope=0,
                        allow_mirror_modeling=True, vertices=verts, faces={}, type='mesh', uuid=mid,
                        _vmap=vmap, _uv=arr['uv'])
                me = built[key]
                vmap, uvs = me['_vmap'], me['_uv']
                for q in polys:
                    vk = [vmap[i] for i in q]
                    if len(set(vk)) < 3:
                        continue  # 退化面
                    face = dict(vertices=vk)
                    if ti is not None and uvs:
                        tw, th = tex_size[ti]
                        face['uv'] = {vmap[i]: [uvs[i][0] * tw, uvs[i][1] * th] for i in q}
                        face['texture'] = ti
                    else:
                        face['uv'] = {vmap[i]: [0, 0] for i in q}
                    me['faces'][f'f{len(me["faces"])}'] = face
                    notes['faces'] += 1
                    notes['quads'] += len(q) == 4
        for me in built.values():
            me.pop('_vmap')
            me.pop('_uv')
            mesh_el.append(me)

    # --- 配置(outliner) ---
    def tree(i):
        return dict(uuid=uid('bone', i), isOpen=False, children=[tree(j) for j, o in enumerate(bones) if o['parent'] == i])

    arm_id = uid('armature')
    arm = dict(isOpen=True, uuid=arm_id, type='armature', name='armature',
               children=[uid('bone', i) for i, b in enumerate(bones) if b['parent'] < 0] + [m['uuid'] for m in mesh_el],
               export=True, locked=False, scope=0)
    outliner = [dict(uuid=arm_id, isOpen=True,
                     children=[tree(i) for i, b in enumerate(bones) if b['parent'] < 0] + [m['uuid'] for m in mesh_el])]

    prefixes = [m['uuid'][:6] for m in mesh_el]
    assert len(prefixes) == len(set(prefixes)), 'メッシュuuid先頭6文字が衝突'

    doc = dict(
        meta=dict(format_version='5.0', model_format='free', box_uv=False),
        name=name, model_identifier='', visible_box=[1, 1, 0], variable_placeholders='',
        multi_file_ruleset='', variable_placeholder_buttons=[], timeline_setups=[], unhandled_root_fields={},
        resolution=dict(width=max(w for w, _ in tex_size), height=max(h for _, h in tex_size)),
        elements=[arm] + bone_el + mesh_el, groups=[], outliner=outliner, textures=textures)

    anims = build_animations(motion_paths, bones, scale, north, ry, name.upper() + '_') if motion_paths else []
    if anims:
        doc['animations'] = anims

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
    print(f'  -> {out_path}  骨{len(bone_el)} メッシュ{len(mesh_el)} 頂点{notes["welded"]}(統合前{notes["verts"]}) '
          f'面{notes["faces"]}(四角{notes["quads"]}) テクスチャ{len(textures)} アニメ{len(anims)} '
          f'4本超の重みを切り捨てた頂点{notes["over4"]} ({os.path.getsize(out_path) / 1024:.0f} KB)')
    return doc


def simplify(times, vals, tol):
    """線形補間で再現できる範囲でキーを間引く（Ramer–Douglas–Peucker, 時間軸つき）。"""
    n = len(times)
    if n <= 2:
        return list(range(n))
    keep = {0, n - 1}
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        worst, wi = 0.0, -1
        for i in range(a + 1, b):
            u = (times[i] - times[a]) / ((times[b] - times[a]) or 1.0)
            err = max(abs(vals[i][k] - (vals[a][k] + (vals[b][k] - vals[a][k]) * u)) for k in range(len(vals[i])))
            if err > worst:
                worst, wi = err, i
        if worst > tol and wi >= 0:
            keep.add(wi)
            stack += [(a, wi), (wi, b)]
    return sorted(keep)


def build_animations(motion_paths, bones, scale, north, ry, prefix=''):
    """モーションGMO -> Blockbench のアニメーション。
    骨のrest姿勢への加算で再生される（位置: 加算 / 回転: ZYX Euler成分の加算 / 拡縮: 乗算）ので、
    キーは「アニメ値 − rest値」に変換する。回転はEulerを時間方向に連続化（±360°のジャンプ除去）する。"""
    rest = []
    for b in bones:
        t, q = list(b['t']), tuple(b['q'])
        if north and b['parent'] < 0:
            t = [-t[0], t[1], -t[2]]
            q = qmul(ry, q)
        rest.append((t, q, euler_zyx(q)))
    anims = []
    for mp in motion_paths:
        mo = read_motion(mp)
        if not mo:
            continue
        rate = mo['rate']
        name = os.path.splitext(os.path.basename(mp))[0]
        if prefix and name.upper().startswith(prefix):
            name = name[len(prefix):]
        animators, max_t = {}, 0.0
        per_bone = {}
        for bone, cmd, fci in mo['channels']:
            if bone < len(bones):
                per_bone.setdefault(bone, {})[cmd] = mo['fcurves'][fci]
        for bone, chans in per_bone.items():
            rt, rq, re_ = rest[bone]
            kfs = []
            # 位置
            if 0x48 in chans:
                _dims, times, vals = chans[0x48]
                vv = []
                for v in vals:
                    t = list(v)
                    if north and bones[bone]['parent'] < 0:
                        t = [-t[0], t[1], -t[2]]
                    vv.append([(t[k] - rt[k]) * scale for k in range(3)])
                if any(abs(c) > 1e-4 for v in vv for c in v):
                    for i in simplify(times, vv, 0.01):
                        kfs.append(('position', times[i], vv[i]))
            # 回転
            if 0x4b in chans:
                _dims, times, vals = chans[0x4b]
                eu, prev = [], re_
                for v in vals:
                    q = tuple(v)
                    if north and bones[bone]['parent'] < 0:
                        q = qmul(ry, q)
                    e = euler_zyx(q)
                    for c in range(3):
                        while e[c] - prev[c] > 180:
                            e[c] -= 360
                        while e[c] - prev[c] < -180:
                            e[c] += 360
                    eu.append(e)
                    prev = e
                dd = [[e[c] - re_[c] for c in range(3)] for e in eu]
                if any(abs(c) > 1e-3 for v in dd for c in v):
                    for i in simplify(times, dd, 0.05):
                        kfs.append(('rotation', times[i], dd[i]))
            # 拡縮
            if 0x4c in chans:
                _dims, times, vals = chans[0x4c]
                if any(abs(c - 1.0) > 1e-3 for v in vals for c in v[:3]):
                    for i in simplify(times, [v[:3] for v in vals], 0.002):
                        kfs.append(('scale', times[i], list(vals[i][:3])))
            if not kfs:
                continue
            frames = []
            for ch, t, v in kfs:
                sec = round(t / rate, 5)
                max_t = max(max_t, sec)
                frames.append(dict(
                    channel=ch, data_points=[dict(x=round(v[0], 4), y=round(v[1], 4), z=round(v[2], 4))],
                    uuid=uid('kf', name, bone, ch, round(t, 3)), time=sec, color=-1, interpolation='linear'))
            animators[uid('bone', bone)] = dict(name=bones[bone]['name'], type='armature_bone', keyframes=frames)
        length = max(max_t, mo['loop'][1] / rate if mo['loop'][1] else 0.0)
        anims.append(dict(
            uuid=uid('anim', name), name=name, loop='loop' if 'IDLE' in name.upper() else 'once',
            override=False, length=round(length, 5), snapping=int(round(rate)), animators=animators))
    return anims


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('gmo')
    ap.add_argument('out')
    ap.add_argument('--scale', type=float, default=0.05)
    ap.add_argument('--north', action='store_true')
    ap.add_argument('--motion', nargs='*', default=[])
    a = ap.parse_args()
    build(a.gmo, a.out, a.scale, a.north, a.motion)
