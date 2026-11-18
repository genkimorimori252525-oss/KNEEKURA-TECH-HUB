"""GMOモデル -> Blockbench の立方体モデル（斜めの板 + ブロックのハイブリッド）。Bedrock Entity 形式。

使い方:
  python hybrid2bbmodel.py <model.gmo> <出力フォルダ> [--name model] [--size 128] [--plates ^AL_body]
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
from gmo2gltf import read_bones, part_bone_lists, world_matrices, read_motion, trs

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


# ---------------------------------------------------------------- 骨のアニメ（グループ用）


def _m3(m4):
    return [row[:3] for row in m4[:3]]


def _m3mul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)] for r in range(3)]


def _m3T(a):
    return [[a[c][r] for c in range(3)] for r in range(3)]


def _nlerp_at(times, vals, frame):
    """クォータニオンのキー列を、最短経路の正規化線形補間で frame の時刻に標本化する。"""
    if frame <= times[0]:
        return list(vals[0])
    if frame >= times[-1]:
        return list(vals[-1])
    hi = next(i for i, t in enumerate(times) if t >= frame)
    lo = hi - 1
    u = (frame - times[lo]) / ((times[hi] - times[lo]) or 1)
    a, b = vals[lo], vals[hi]
    if sum(x * y for x, y in zip(a, b)) < 0:
        b = [-c for c in b]
    r = [x + (y - x) * u for x, y in zip(a, b)]
    n = math.sqrt(sum(c * c for c in r)) or 1
    return [c / n for c in r]


def _keyframe(channel, v, sec):
    """Blockbench のキーフレーム。uuid・色・補間（linear）は省略しても Blockbench が既定値で補うので書かない（容量削減）。"""
    return dict(channel=channel, data_points=[dict(x=round(v[0], 3), y=round(v[1], 3), z=round(v[2], 3))], time=sec)


def _lerp_at(times, vals, frame):
    if frame <= times[0]:
        return list(vals[0])
    if frame >= times[-1]:
        return list(vals[-1])
    hi = next(i for i, t in enumerate(times) if t >= frame)
    lo = hi - 1
    u = (frame - times[lo]) / ((times[hi] - times[lo]) or 1)
    return [x + (y - x) * u for x, y in zip(vals[lo], vals[hi])]


def _m3inv(m):
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    return [[(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
            [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
            [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det]]


def _polar(L):
    """3x3 行列に最も近い回転（極分解の直交成分）。R <- (R + R^-T)/2 の反復。"""
    R = [row[:] for row in L]
    for _ in range(40):
        it = _m3T(_m3inv(R))
        Rn = [[0.5 * (R[r][c] + it[r][c]) for c in range(3)] for r in range(3)]
        done = max(abs(Rn[r][c] - R[r][c]) for r in range(3) for c in range(3)) < 1e-12
        R = Rn
        if done:
            break
    return R


def _m3_to_quat(m):
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return [(m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s, 0.25 * s]
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        return [0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s, (m[2][1] - m[1][2]) / s]
    if m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        return [(m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s, (m[0][2] - m[2][0]) / s]
    s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
    return [(m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s, (m[1][0] - m[0][1]) / s]


def _blend_rotation(pairs):
    """[(重み, 回転行列)] -> 重み付きクォータニオン平均の回転行列（符号をそろえて足し、正規化）。
    行列をそのまま混ぜると、大きく違う回転どうし（回り続ける歯車など）で潰れるため。"""
    acc, ref = [0.0, 0.0, 0.0, 0.0], None
    for wv, m in pairs:
        q = _m3_to_quat(m)
        if ref is None:
            ref = q
        if sum(a * b for a, b in zip(q, ref)) < 0:
            q = [-c for c in q]
        acc = [a + wv * c for a, c in zip(acc, q)]
    return _m3(trs((0, 0, 0), acc))


def _continuous_euler(mats):
    """回転行列の列 -> 連続した ZYX Euler（度）の列（2通りの表現から直前に近い方、±360°も除く）。"""
    out, prev = [], [0.0, 0.0, 0.0]
    for m in mats:
        e0 = euler_from_m3(m)
        best = None
        for cand in (list(e0), [e0[0] + 180, 180 - e0[1], e0[2] + 180]):
            for k in range(3):
                while cand[k] - prev[k] > 180:
                    cand[k] -= 360
                while cand[k] - prev[k] < -180:
                    cand[k] += 360
            dist = sum(abs(cand[k] - prev[k]) for k in range(3))
            if best is None or dist < best[0]:
                best = (dist, cand)
        out.append(best[1])
        prev = best[1]
    return out


def build_blend_animations(motion_paths, bones, Wg, helpers, hgid, S4, S4i, prefix='', tol_pos=0.5, tol_rot=0.5):
    """補助の骨（重みが混ざった面のまとまり）のアニメ。各フレームで、元の骨の動き D_b（モデル座標）を
    重みどおりに混ぜた変換 M = Σ w_b D_b を作り、その線形部分に最も近い回転 R と、ピボット c の移動 M·c - c をキーにする。
    補助の骨は親なし・静止回転0のグループ。戻り: {アニメ名: (animators, 最終時刻)}"""
    from gmo2bbmodel import simplify
    from gmo2gltf import mul, rigid_inv
    Winv = [rigid_inv(W) for W in Wg]
    result = {}
    for mp in motion_paths:
        mo = read_motion(mp)
        if not mo:
            continue
        rate = mo['rate']
        name = os.path.splitext(os.path.basename(mp))[0]
        if prefix and name.upper().startswith(prefix):
            name = name[len(prefix):]
        chT, chQ = {}, {}
        for bone, cmd, fci in mo['channels']:
            _d, times, vals = mo['fcurves'][fci]
            if bone < len(bones) and times:
                if cmd == 0x48:
                    chT[bone] = (times, vals)
                elif cmd == 0x4b:
                    chQ[bone] = (times, vals)
        last = max([tv[0][-1] for tv in list(chT.values()) + list(chQ.values())] + [0.0])
        frames = list(range(0, int(math.ceil(last)) + 1))
        rots = {k: [] for k in range(len(helpers))}
        poss = {k: [] for k in range(len(helpers))}
        for fr in frames:
            T = [_lerp_at(chT[b][0], chT[b][1], fr) if b in chT else list(bones[b]['t']) for b in range(len(bones))]
            Q = [_nlerp_at(chQ[b][0], chQ[b][1], fr) if b in chQ else list(bones[b]['q']) for b in range(len(bones))]
            W = [None] * len(bones)

            def world(i):
                if W[i] is None:
                    loc = trs(T[i], Q[i])
                    W[i] = loc if bones[i]['parent'] < 0 else mul(world(bones[i]['parent']), loc)
                return W[i]
            D = {}
            for k, hp in enumerate(helpers):
                M = [[0.0] * 4 for _ in range(4)]
                for b, wgt in hp['wts'].items():
                    if b not in D:
                        D[b] = mul(mul(S4, mul(world(b), Winv[b])), S4i)
                    for r in range(4):
                        for c in range(4):
                            M[r][c] += wgt * D[b][r][c]
                c0 = hp['pivot_bb']
                mc = [sum(M[r][k2] * c0[k2] for k2 in range(3)) + M[r][3] for r in range(3)]
                rots[k].append(_blend_rotation([(wgt, [row[:3] for row in D[b][:3]]) for b, wgt in hp['wts'].items()]))
                poss[k].append([mc[a] - c0[a] for a in range(3)])
        animators, max_t = {}, 0.0
        for k, hp in enumerate(helpers):
            eu = _continuous_euler(rots[k])
            fr_f = [float(x) for x in frames]
            kfs = []
            # 補助の骨は毎フレーム標本化しているので、許容誤差（位置 tol_pos 単位、回転 tol_rot 度）で間引く。
            # 継ぎ目の開き（1〜2 ブロック）より十分小さければ見た目は変わらず、キーの数（＝ファイルの重さ）が大きく減る
            if any(abs(c) > 1e-3 for v in poss[k] for c in v):
                for i in simplify(fr_f, poss[k], tol_pos):
                    kfs.append(('position', fr_f[i], poss[k][i]))
            if any(abs(c) > 1e-3 for v in eu for c in v):
                for i in simplify(fr_f, eu, tol_rot):
                    kfs.append(('rotation', fr_f[i], eu[i]))
            if not kfs:
                continue
            keyframes = []
            for ch, t, v in kfs:
                sec = round(t / rate, 5)
                max_t = max(max_t, sec)
                keyframes.append(_keyframe(ch, v, sec))
            animators[hgid[k]] = dict(name=hp['name'], type='bone', rotation_global=False,
                                      quaternion_interpolation=False, keyframes=keyframes)
        result[name] = (animators, max_t)
    return result


def euler_from_m3(m):
    return euler_zyx_from_columns([m[0][0], m[1][0], m[2][0]], [m[0][1], m[1][1], m[2][1]], [m[0][2], m[1][2], m[2][2]])


def build_bone_animations(motion_paths, bones, Wg, gid, s, f, prefix=''):
    """モーションGMO -> Blockbench のグループ（骨）アニメ。グループの静止回転は 0 にしてあるので、
    回転キー = 親の静止ワールド回転 P で見た「その骨の局所回転の差分」:  F·P·(R_L(t)·R_Lrest^T)·P^T·F  の ZYX Euler（度）
    位置キー = 親の静止ワールド回転で見た「局所移動の差分」: s·F·P·(t_L(t) - t_Lrest)
    F は Y軸180°（f=-1 のとき x,z を反転）、s はゲーム単位 -> モデル単位の倍率。
    Blockbench はグループの回転・位置を静止姿勢へ単純に加算する（実機で確認）。"""
    from gmo2bbmodel import simplify
    F = (f, 1, f)
    I3 = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]

    def conjF(m):
        return [[F[r] * F[c] * m[r][c] for c in range(3)] for r in range(3)]
    anims = []
    for mp in motion_paths:
        mo = read_motion(mp)
        if not mo:
            continue
        rate = mo['rate']
        name = os.path.splitext(os.path.basename(mp))[0]
        if prefix and name.upper().startswith(prefix):
            name = name[len(prefix):]
        per = {}
        for bone, cmd, fci in mo['channels']:
            if bone < len(bones):
                per.setdefault(bone, {})[cmd] = mo['fcurves'][fci]
        animators, max_t = {}, 0.0
        for b, chans in per.items():
            par = bones[b]['parent']
            P = _m3(Wg[par]) if par >= 0 else I3
            PT = _m3T(P)
            kfs = []
            if 0x48 in chans:
                _d, times, vals = chans[0x48]
                tr = bones[b]['t']
                dd = []
                for v in vals:
                    delta = [v[k] - tr[k] for k in range(3)]
                    wv = [sum(P[r][k] * delta[k] for k in range(3)) for r in range(3)]
                    dd.append([wv[0] * s * f, wv[1] * s, wv[2] * s * f])
                if any(abs(c) > 1e-3 for v in dd for c in v):
                    for i in simplify(times, dd, 0.02):
                        kfs.append(('position', times[i], dd[i]))
            if 0x4b in chans:
                _d, ktimes, kvals = chans[0x4b]
                # 元データはキーの間をクォータニオンで補間する。Blockbench は Euler を成分ごとに直線補間するので、
                # 毎フレームで元どおりに標本化してから Euler にし、後で間引く（間引きの許容誤差 = 元の経路との差の上限）
                times = sorted(set(ktimes) | set(float(fr) for fr in range(int(math.ceil(ktimes[0])), int(ktimes[-1]) + 1)))
                vals = [_nlerp_at(ktimes, kvals, fr) for fr in times]
                RrestT = _m3T(_m3(trs((0, 0, 0), bones[b]['q'])))
                eu, prev = [], [0.0, 0.0, 0.0]
                for v in vals:
                    Rd = _m3mul(_m3(trs((0, 0, 0), v)), RrestT)
                    e0 = euler_from_m3(conjF(_m3mul(_m3mul(P, Rd), PT)))
                    # 同じ回転を表す ZYX Euler は2通り: (x,y,z) と (x+180, 180-y, z+180)。
                    # 直前のキーに近いほうを選ぶ（歯車のように回り続ける骨で、表現の切り替わりをまたいだ補間が暴れないように）
                    best = None
                    for cand in (list(e0), [e0[0] + 180, 180 - e0[1], e0[2] + 180]):
                        for k in range(3):  # ±360° のジャンプを除く
                            while cand[k] - prev[k] > 180:
                                cand[k] -= 360
                            while cand[k] - prev[k] < -180:
                                cand[k] += 360
                        dist = sum(abs(cand[k] - prev[k]) for k in range(3))
                        if best is None or dist < best[0]:
                            best = (dist, cand)
                    e = best[1]
                    eu.append(e)
                    prev = e
                if any(abs(c) > 1e-3 for v in eu for c in v):
                    for i in simplify(times, eu, 0.05):
                        kfs.append(('rotation', times[i], eu[i]))
            if not kfs:
                continue
            frames = []
            for ch, t, v in kfs:
                sec = round(t / rate, 5)
                max_t = max(max_t, sec)
                frames.append(_keyframe(ch, v, sec))
            animators[gid[b]] = dict(name=bones[b]['name'], type='bone', rotation_global=False,
                                     quaternion_interpolation=False, keyframes=frames)
        length = max(max_t, mo['loop'][1] / rate if mo['loop'][1] else 0.0)
        anims.append(dict(uuid=uid('anim', name), name=name, loop='loop' if 'IDLE' in name.upper() else 'once',
                          override=False, length=round(length, 5), snapping=int(round(rate)), animators=animators))
    return anims


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
    # 骨: 面ごとに「一番効いている骨」を決める（立方体モデルはスキニングできないので、各キューブを1本の骨に固定する）
    bones = read_bones(model)
    plists = part_bone_lists(model, bones)
    polys = []
    for pi, part in enumerate(model.kids(5)):
        if ex and ex.search(part.name):
            continue
        refs = plists.get(pi, ([], []))[0]
        arrays = [read_array(a, sb) for a in part.kids(7)]
        for mesh in part.kids(6):
            mr = mesh.kid(0x8061)
            mi = gmo.ref(int.from_bytes(mr.payload[:4], 'little')) if mr is not None else None
            ti = mat_tex[mi] if mi is not None and mi < len(mat_tex) else None
            pal = mesh.kid(0x8062)
            palette = None
            if pal is not None:
                k = int.from_bytes(pal.payload[:4], 'little')
                palette = [int.from_bytes(pal.payload[4 + 4 * j:8 + 4 * j], 'little') for j in range(k)]
            for ar, plist in read_indices(mesh):
                arr = arrays[ar]
                wc = gmo.ge_layout(arr['fmt'])['weights'][2] if 'weights' in gmo.ge_layout(arr['fmt']) else 0
                pals = palette if palette is not None else list(range(wc))
                for q in plist:
                    votes, vws = {}, []
                    for i in q:
                        vw = {}
                        for k, wgt in enumerate(arr['weights'][i] if arr['weights'] else []):
                            if wgt > 0 and k < len(pals) and pals[k] < len(refs):
                                b = refs[pals[k]]
                                votes[b] = votes.get(b, 0.0) + wgt
                                vw[b] = vw.get(b, 0.0) + wgt
                        t = sum(vw.values())
                        vws.append({b: v / t for b, v in vw.items()} if t else None)
                    bone = max(votes, key=votes.get) if votes else (refs[0] if refs else 0)
                    tot = sum(votes.values())
                    wts = {b: v / tot for b, v in votes.items()} if tot else {bone: 1.0}  # 面の平均の重み（骨 -> 割合）
                    vws = [w if w else {bone: 1.0} for w in vws]  # 頂点ごとの重み（面の中の伸び縮みを追うのに使う）
                    polys.append(dict(part=part.name, pos=[arr['pos'][i] for i in q],
                                      uv=[arr['uv'][i] for i in q] if arr['uv'] else None, tex=ti, bone=bone, wts=wts,
                                      vw=vws))
    return polys, textures, bones


# ---------------------------------------------------------------- 伸び縮みする面の分割（rig 用）


def sample_deforms(motion_paths, bones, every=8):
    """全モーションを every フレームおきに標本化し、各時刻の骨ごとの変形 D_b = W_b(t)·W_b(静止)^-1（ゲーム座標）の列を返す。"""
    from gmo2gltf import mul as m4mul, rigid_inv
    Winv = [rigid_inv(W) for W in world_matrices(bones, 1.0)]
    out = []
    for mp in motion_paths:
        mo = read_motion(mp)
        if not mo:
            continue
        chT, chQ = {}, {}
        for bone, cmd, fci in mo['channels']:
            _d, times, vals = mo['fcurves'][fci]
            if bone < len(bones) and times:
                if cmd == 0x48:
                    chT[bone] = (times, vals)
                elif cmd == 0x4b:
                    chQ[bone] = (times, vals)
        last = max([tv[0][-1] for tv in list(chT.values()) + list(chQ.values())] + [0.0])
        for fr in range(0, int(math.ceil(last)) + 1, every):
            T = [_lerp_at(chT[b][0], chT[b][1], fr) if b in chT else list(bones[b]['t']) for b in range(len(bones))]
            Q = [_nlerp_at(chQ[b][0], chQ[b][1], fr) if b in chQ else list(bones[b]['q']) for b in range(len(bones))]
            W = [None] * len(bones)

            def world(i):
                if W[i] is None:
                    loc = trs(T[i], Q[i])
                    W[i] = loc if bones[i]['parent'] < 0 else m4mul(world(bones[i]['parent']), loc)
                return W[i]
            out.append([m4mul(world(b), Winv[b]) for b in range(len(bones))])
    return out


def _apply4(M, p):
    return [sum(M[r][k] * p[k] for k in range(3)) + M[r][3] for r in range(3)]


def _mix(ws, cs):
    """重み辞書の線形結合 Σ c_i·w_i。"""
    out = {}
    for w, c in zip(ws, cs):
        for b, v in w.items():
            out[b] = out.get(b, 0.0) + c * v
    return out


def subdivide_for_skin(polys, Ds, cell, budget, match, max_depth=6, min_edge=1.0):
    """元のスキニング（頂点ごとの重み）は面の中で伸び縮みするが、板やブロックは1つの骨に乗ると硬い。
    1つの面の中で重みが大きく変わると、面全体を1つの動きにしたとき継ぎ目が大きく割れる（実測で最大十数ブロック）。
    そこで match に合う面を、「面の重心の重みで動かしたときの、頂点ごとの元の変形からのずれ」の見積もりが
    budget ブロック以下になるまで 4 分割する（辺の中点で切り、UV と頂点の重みは線形補間）。
    ずれの見積もり: Σ_b |w_b(頂点) - w_b(重心)| × max_t |D_b(t)·x - D_dom(t)·x|（dom = 重心で一番効く骨）。
    戻り: 新しい面のリスト（分割した面は wts = 重心の重み、bone = その最大の骨）。"""
    cache = {}

    def mrel(x, b, dom):
        k = (round(x[0], 2), round(x[1], 2), round(x[2], 2), b, dom)
        if k not in cache:
            cache[k] = max(math.dist(_apply4(D[b], x), _apply4(D[dom], x)) for D in Ds) / cell if Ds else 0.0
        return cache[k]

    out = []

    def emit(src, P, UV, VW, depth):
        wc = _mix(VW, [1 / len(VW)] * len(VW))
        out.append(dict(src, pos=P, uv=UV, vw=VW, wts=wc, bone=max(wc, key=wc.get), split=depth > 0))

    def split(src, P, UV, VW, depth):
        wc = _mix(VW, [1 / 3] * 3)
        dom = max(wc, key=wc.get)
        err = 0.0
        for p, vw in zip(P, VW):
            err = max(err, sum(abs(vw.get(b, 0.0) - wc.get(b, 0.0)) * mrel(p, b, dom) for b in set(vw) | set(wc) if b != dom))
        edge = max(math.dist(P[i], P[(i + 1) % 3]) for i in range(3)) / cell
        if err <= budget or edge <= min_edge or depth >= max_depth:
            emit(src, P, UV, VW, depth)
            return
        M = [tuple((P[i][a] + P[(i + 1) % 3][a]) / 2 for a in range(3)) for i in range(3)]
        MU = [tuple((UV[i][a] + UV[(i + 1) % 3][a]) / 2 for a in range(2)) for i in range(3)] if UV else None
        MW = [_mix([VW[i], VW[(i + 1) % 3]], (0.5, 0.5)) for i in range(3)]
        for a, b, c in ((0, 'm0', 'm2'), ('m0', 1, 'm1'), ('m2', 'm1', 2), ('m0', 'm1', 'm2')):
            idx = [a, b, c]
            pick = lambda arr, marr: [arr[i] if isinstance(i, int) else marr[int(i[1])] for i in idx]
            split(src, pick(P, M), pick(UV, MU) if UV else None, pick(VW, MW), depth + 1)

    for q in polys:
        if not match(q) or 'vw' not in q:
            out.append(q)
            continue
        P, UV, VW = q['pos'], q['uv'], q['vw']
        for k in range(1, len(P) - 1):  # 四角形以上は扇形に三角形へ
            tri = [0, k, k + 1]
            split(q, [P[i] for i in tri], [UV[i] for i in tri] if UV else None, [VW[i] for i in tri], 0)
    return out


def expand_triangle(P, UV, margin, max_scale=2.0):
    """三角形を内心まわりに広げ、各辺を margin（P と同じ単位）だけ外へ出す。UV も同じ比率で外へ延ばす（絵が続く）。
    切った小片どうしは別の補助の骨に乗るので、動くと細い隙間が開く。少し重ねてその隙間を隠すために使う。"""
    a, b, c = (math.dist(P[1], P[2]), math.dist(P[2], P[0]), math.dist(P[0], P[1]))
    per = a + b + c
    if per <= 1e-12:
        return P, UV
    inc = [(a * P[0][k] + b * P[1][k] + c * P[2][k]) / per for k in range(3)]
    s = (per / 2)
    area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))
    r = area / s
    if r <= 1e-12:
        return P, UV
    f = min(max_scale, (r + margin) / r)
    P2 = [tuple(inc[k] + (p[k] - inc[k]) * f for k in range(3)) for p in P]
    if not UV:
        return P2, UV
    uinc = [(a * UV[0][k] + b * UV[1][k] + c * UV[2][k]) / per for k in range(2)]
    return P2, [tuple(uinc[k] + (u[k] - uinc[k]) * f for k in range(2)) for u in UV]


def seam_report(polys, Ds, cell, nb, helpers):
    """継ぎ目の開き（ブロック）を測る。元のスキニングで離れない共有頂点（静止位置が同じ頂点）について、
    各面が乗る骨（または補助の骨: ピボット中心の平均回転 + M·c）で動かしたときの散らばりを、標本化した全時刻で集計する。
    polys の各面は key（骨番号 or nb+補助の骨番号）と vw（頂点ごとの重み）を持つこと。"""
    vkey = lambda p: tuple(round(c / cell * 64) for c in p)
    share = {}
    for i, q in enumerate(polys):
        for k, p in enumerate(q['pos']):
            share.setdefault(vkey(p), []).append((i, k))
    share = [v for v in share.values() if len({i for i, _ in v}) > 1]
    piv = [[sum(p[a] for p in hp['pts']) / len(hp['pts']) for a in range(3)] for hp in helpers]
    gaps = []
    worst = 0.0
    for D in Ds:
        H = []
        for hp, c0 in zip(helpers, piv):
            M = [[sum(w * D[b][r][c] for b, w in hp['wts'].items()) for c in range(4)] for r in range(4)]
            R = _blend_rotation([(w, _m3(D[b])) for b, w in hp['wts'].items()])
            H.append((R, c0, _apply4(M, c0)))

        def pos(q, k):
            p = q['pos'][k]
            if q['key'] < nb:
                return _apply4(D[q['key']], p)
            R, c0, mc = H[q['key'] - nb]
            return [sum(R[r][j] * (p[j] - c0[j]) for j in range(3)) + mc[r] for r in range(3)]

        def lbs(q, k):
            out = [0.0, 0.0, 0.0]
            for b, w in q['vw'][k].items():
                v = _apply4(D[b], q['pos'][k])
                out = [out[a] + w * v[a] for a in range(3)]
            return out
        for v in share:
            L = [lbs(polys[i], k) for i, k in v]
            if max(math.dist(a, b) for a in L for b in L) / cell > 0.05:
                continue  # 元の変形でも離れる頂点（別の部品の重なり）は継ぎ目ではない
            P = [pos(polys[i], k) for i, k in v]
            g = max(math.dist(a, b) for a in P for b in P) / cell
            gaps.append(g)
            worst = max(worst, g)
    gaps.sort()
    pc = lambda p: round(gaps[min(len(gaps) - 1, int(len(gaps) * p))], 3) if gaps else 0.0
    return dict(samples=len(gaps), max=round(worst, 3), p50=pc(0.5), p95=pc(0.95), p99=pc(0.99),
                over_half_block=round(sum(g > 0.5 for g in gaps) / max(1, len(gaps)), 4))


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
          coverage=0.5, fine_parts=None, fine_texel=None, rig=False, motion_paths=(), blend=True, blend_step=0.1,
          blend_parts='^AL_body', blend_budget=2.0, seams=False, blend_tol=0.25, blend_margin=0.5):
    """rig=True: 元の骨をグループにして、各キューブを骨に固定する。motion_paths でアニメも付ける。
    blend=True: 重みが2本以上の骨に混ざる面（スカートなど）は、重みを blend_step 刻みに丸めた「混ぜ方」ごとの
    補助の骨（blend_N）にまとめ、元の変形に近い動きをさせる（1本の骨に固定すると継ぎ目が割れるため）。"""
    import re
    fine_re = re.compile(fine_parts) if fine_parts else None
    from PIL import Image
    polys, textures, bones = read_polygons(gmo_path, exclude)
    allpts = [p for q in polys for p in q['pos']]
    mn, cell, dims = obj2schem.bbox_frame(allpts, size)
    w, h, l = dims
    n_split, Ds, seam_stats = 0, None, None
    if rig and blend and motion_paths and blend_budget and blend_budget > 0:
        # 面の中で重みが大きく変わる面（伸び縮みする所）を細かく切ってから、板・ブロックにする
        bre = re.compile(blend_parts) if blend_parts else None
        Ds = sample_deforms(motion_paths, bones)
        before = len(polys)
        polys = subdivide_for_skin(polys, Ds, cell, blend_budget, lambda q: bre is None or bool(bre.search(q['part'])))
        n_split = len(polys) - before
        print(f'skin subdivision: {before} -> {len(polys)} faces (budget {blend_budget} blocks, {len(Ds)} sampled poses)')
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

    # --- rig: 面ごとの骨（重みが混ざる面は「混ぜ方」ごとの補助の骨にまとめる）---
    helpers = []
    if rig:
        hkey = {}
        blend_re = re.compile(blend_parts) if blend_parts else None
        for q in polys:
            q['key'] = q['bone']
            # 補助の骨はなめらかに変形する部位（ドレス）だけ。歯車など固い部品は1本の骨のまま
            if not blend or (blend_re and not blend_re.search(q['part'])):
                continue
            rounded = {b: round(v / blend_step) * blend_step for b, v in q['wts'].items()}
            rounded = {b: v for b, v in rounded.items() if v > 1e-9}
            if len(rounded) < 2:
                if rounded:
                    q['key'] = next(iter(rounded))
                continue
            tot = sum(rounded.values())
            sig = tuple(sorted((b, round(v / tot, 4)) for b, v in rounded.items()))
            if sig not in hkey:
                hkey[sig] = len(bones) + len(helpers)
                helpers.append(dict(name=f'blend_{len(helpers)}', wts=dict(sig), pts=[]))
            q['key'] = hkey[sig]
            helpers[q['key'] - len(bones)]['pts'] += list(q['pos'])
        for hp in helpers:
            cen = [sum(p[a] for p in hp['pts']) / len(hp['pts']) for a in range(3)]
            hp['pivot_bb'] = [round(x, 4) for x in to_bb(cen)]
        if seams and motion_paths:
            sre = re.compile(blend_parts) if blend_parts else None
            sp = [q for q in polys if 'vw' in q and (sre is None or sre.search(q['part']))]
            seam_stats = seam_report(sp, Ds if Ds else sample_deforms(motion_paths, bones), cell, len(bones), helpers)
            print('seams (blocks):', seam_stats)

    # --- ブロック部（板にしないパーツ）---
    texd = {f'tex{ti}': (tx[0], tx[1]) for ti, tx in enumerate(textures)}

    def voxel_solid(sub):
        V, VT, tris = [], [], []
        for q in sub:
            base = len(V)
            V += list(q['pos'])
            has_uv = q['uv'] is not None
            for k in range(len(q['pos'])):
                VT.append((q['uv'][k][0], 1.0 - q['uv'][k][1]) if has_uv else (0.0, 0.0))
            mat = f"tex{q['tex']}" if q['tex'] is not None else None
            idx = [(base + k + 1, base + k + 1) for k in range(len(q['pos']))]
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1], mat, q['part']))
        out = {}
        if tris:
            _d, _c, colors = obj2schem.voxelize(V, VT, tris, texd, size, frame=(mn, cell, dims))
            for c, blk in obj2schem.to_blocks(colors, palette, gain, sat).items():
                out[c if keep_front else (w - 1 - c[0], c[1], l - 1 - c[2])] = blk
        return out

    # rig のときは骨ごとにボクセル化（1つのキューブが2本の骨にまたがらないように）。重なったセルは先の骨が取る
    by_bone = {}
    for q in polys:
        if not is_plate(q):
            by_bone.setdefault(q['key'] if rig else None, []).append(q)
    solids, claimed = {}, set()
    for b in sorted(by_bone, key=lambda x: -1 if x is None else x):
        sol = {c: blk for c, blk in voxel_solid(by_bone[b]).items() if c not in claimed}
        claimed |= set(sol)
        if sol:
            solids[b] = sol
    solid = {c: blk for sol in solids.values() for c, blk in sol.items()}

    # --- 領域（アトラスに詰める画素の塊）---
    regions, pixels, uniq = [], [], {}

    def region(wid, hei, pix):
        key = (wid, hei, tuple(pix))
        if key not in uniq:
            uniq[key] = len(regions)
            regions.append((wid, hei))
            pixels.append(pix)
        return uniq[key]

    cubes = []  # dict(name, frm, to, origin, rot, faces={face: (region, flip)}, bone)
    expected_vox = []
    for bone_id, sol in solids.items():
        # 空洞は、この骨の殻の中だけ埋める（他の骨のセルは埋めない）。露出も、この骨の中だけで判定（動いても穴が開かない）
        grid = voxel2bbmodel.fill_cavities(set(sol), dims) - (claimed - set(sol))
        boxes, _seed, _axes = voxel2bbmodel.choose_partition(grid)
        for b in boxes:
            fm = {}
            for face in voxel2bbmodel.FACES:
                if not voxel2bbmodel.face_exposed(b, face, grid):
                    continue
                fw, fh, nrm, cellf = voxel2bbmodel.face_cells(face, b)
                pix = []
                for pv in range(fh):
                    for pu in range(fw):
                        c = cellf(pu, pv)
                        blk = sol.get(c)
                        rgb = palette[blk] if blk else (128, 128, 128)
                        pix.append(tuple(rgb) + (255,))
                        if dump_expected is not None and blk and (c[0] + nrm[0], c[1] + nrm[1], c[2] + nrm[2]) not in grid:
                            expected_vox.append([c[0] + ox, c[1], c[2] + oz, face, rgb[0], rgb[1], rgb[2]])
                fm[face] = (region(fw, fh, pix), False)
            (bx0, by0, bz0), (bx1, by1, bz1) = b
            cubes.append(dict(name=f'b{len(cubes)}', frm=[(bx0 + ox) * unit, by0 * unit, (bz0 + oz) * unit],
                              to=[(bx1 + ox) * unit, by1 * unit, (bz1 + oz) * unit], origin=[0, 0, 0], rot=[0, 0, 0],
                              faces=fm, bone=bone_id))
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
        src = q
        if q.get('split') and blend_margin > 0 and len(q['pos']) == 3:
            # 切った小片は少し広げて隣と重ねる（動いたときの細い隙間を隠す）
            P2, UV2 = expand_triangle(q['pos'], q['uv'], blend_margin * cell)
            src = dict(q, pos=P2, uv=UV2)
        bpoly = dict(src, pos=[to_bb(p) for p in src['pos']])
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
        cubes.append(dict(name=f'p{idx}', frm=pl['frm'], to=pl['to'], origin=pl['C'], rot=pl['rot'], faces=fm,
                          bone=q['key'] if rig else None, wts=q['wts']))
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
    rnd = lambda v: [round(x, 4) for x in v]
    for i, c in enumerate(cubes):
        faces = {f: ({'uv': uvrect(*c['faces'][f]), 'texture': 0} if f in c['faces'] else {'uv': [0, 0, 0, 0], 'texture': None})
                 for f in voxel2bbmodel.FACES}
        cid = uid('cube', i)
        c['uuid'] = cid
        child_ids.append(cid)
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

    # ---- 骨（グループ）とアニメ ----
    group_id = uid('group', 'root')
    s_scale, fsign = unit / cell, (1 if keep_front else -1)
    rig_info = None
    if rig:
        Wg = world_matrices(bones, 1.0)  # 元データの骨のワールド行列（静止姿勢・ゲーム単位）
        nb = len(bones)
        ng = nb + len(helpers)
        gname = [b['name'] for b in bones] + [hp['name'] for hp in helpers]
        gparent = [b['parent'] for b in bones] + [-1] * len(helpers)
        gid = {g: uid('group', gname[g]) for g in range(ng)}
        kids = {g: [j for j in range(ng) if gparent[j] == g] for g in range(ng)}
        roots = [g for g in range(ng) if gparent[g] < 0]
        pivots = {b: rnd(to_bb((Wg[b][0][3], Wg[b][1][3], Wg[b][2][3]))) for b in range(nb)}
        for k, hp in enumerate(helpers):
            pivots[nb + k] = hp['pivot_bb']
        cubes_of = {g: [i for i, c in enumerate(cubes) if c['bone'] == g] for g in range(ng)}
        groups = [dict(name=gname[g], uuid=gid[g], export=True, locked=False, scope=0, selected=False, visibility=True,
                       origin=pivots[g], rotation=[0, 0, 0], bedrock_binding='', color=g % 8, children=[], reset=False,
                       shade=True, mirror_uv=False, autouv=0, isOpen=False) for g in range(ng)]

        def tree(b):
            return dict(uuid=gid[b], isOpen=False, children=[cubes[i]['uuid'] for i in cubes_of[b]] + [tree(j) for j in kids[b]])
        outliner = [tree(b) for b in roots]
        order = []

        def walk(b):
            order.append(b)
            for j in kids[b]:
                walk(j)
        for r in roots:
            walk(r)
        geo_bones = []
        for b in order:
            bone = {'name': gname[b]}
            if gparent[b] >= 0:
                bone['parent'] = gname[gparent[b]]
            bone['pivot'] = [-pivots[b][0], pivots[b][1], pivots[b][2]]
            if cubes_of[b]:
                bone['cubes'] = [geo_cubes[i] for i in cubes_of[b]]
            geo_bones.append(bone)
        prefix = os.path.splitext(os.path.basename(gmo_path))[0].upper() + '_'
        anims = build_bone_animations(motion_paths, bones, Wg, gid, s_scale, fsign, prefix) if motion_paths else []
        if helpers and motion_paths:
            c0 = to_bb((0, 0, 0))
            A = [fsign * s_scale, s_scale, fsign * s_scale]
            S4 = [[A[0], 0, 0, c0[0]], [0, A[1], 0, c0[1]], [0, 0, A[2], c0[2]], [0, 0, 0, 1]]
            S4i = [[1 / A[0], 0, 0, -c0[0] / A[0]], [0, 1 / A[1], 0, -c0[1] / A[1]], [0, 0, 1 / A[2], -c0[2] / A[2]], [0, 0, 0, 1]]
            hgid = {k: gid[nb + k] for k in range(len(helpers))}
            extra = build_blend_animations(motion_paths, bones, Wg, helpers, hgid, S4, S4i, prefix,
                                           tol_pos=blend_tol * unit, tol_rot=max(0.5, 4 * blend_tol))
            for an in anims:
                if an['name'] in extra:
                    animators, mt = extra[an['name']]
                    an['animators'].update(animators)
                    an['length'] = round(max(an['length'], mt), 5)
        rig_info = dict(mn=mn, cell=cell, dims=dims, unit=unit, keep_front=keep_front, ox=ox, oz=oz,
                        split_faces=n_split, seams=seam_stats,
                        cube_bone={c['name']: gname[c['bone']] for c in cubes},
                        blend_weights={hp['name']: {bones[b]['name']: wv for b, wv in hp['wts'].items()} for hp in helpers},
                        plate_weights={c['name']: {bones[b]['name']: wv for b, wv in c['wts'].items()}
                                       for c in cubes if c['name'][0] == 'p' and c.get('wts')})
    else:
        groups = [dict(name='root', uuid=group_id, export=True, locked=False, scope=0, selected=False, visibility=True,
                       origin=[0, 0, 0], rotation=[0, 0, 0], bedrock_binding='', color=0, children=child_ids,
                       reset=False, shade=True, mirror_uv=False, autouv=0, isOpen=True)]
        outliner = [dict(uuid=group_id, isOpen=True, children=child_ids)]
        geo_bones = [{'name': 'root', 'pivot': [0, 0, 0], 'cubes': geo_cubes}]
        anims = []
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
        groups=groups, outliner=outliner, textures=[tex])
    if anims:
        doc['animations'] = anims
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
        'bones': geo_bones}]}
    geo_path = os.path.join(outdir, f'{name}.geo.json')
    with open(geo_path, 'w', encoding='utf-8') as f:
        json.dump(geo, f, ensure_ascii=False, separators=(',', ':'))
    if dump_expected is not None:
        with open(dump_expected, 'w', encoding='utf-8') as f:
            json.dump(dict(vox=expected_vox, plates=expected_plates, unit=unit, rig=rig_info), f, separators=(',', ':'))
    if anims:
        print(f'  骨 {len(bones)} 本・アニメ {len(anims)} 本（' + ', '.join(a['name'] for a in anims) + '）')
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
    ap.add_argument('--rig', action='store_true', help='元の骨をグループにして、各キューブを一番効いている骨に固定する')
    ap.add_argument('--motion', nargs='*', default=[], help='モーションGMO（--rig と一緒に。Blockbench のアニメにする）')
    ap.add_argument('--no-blend', action='store_true', help='重みが混ざる面も一番効く骨1本に固定する（継ぎ目が割れる。比較用）')
    ap.add_argument('--blend-step', type=float, default=0.1, help='補助の骨にまとめるときの重みの丸め幅')
    ap.add_argument('--blend-parts', default='^AL_body', help='補助の骨を使うパーツ（正規表現）。なめらかに変形する部位だけにする')
    ap.add_argument('--blend-budget', type=float, default=2.0,
                    help='伸び縮みする面を切る細かさ: 元の変形からのずれの見積もりがこのブロック数以下になるまで面を4分割する（0=切らない）')
    ap.add_argument('--seam-report', action='store_true',
                    help='継ぎ目の開き（元のスキニングでつながる頂点が、骨に固定した板/ブロックでどれだけ離れるか）を全アニメで測って表示')
    ap.add_argument('--blend-tol', type=float, default=0.25,
                    help='補助の骨のキーを間引く許容誤差（ブロック）。回転は 4 倍の度数（最低 0.5°）。大きいほど軽い')
    ap.add_argument('--blend-margin', type=float, default=0.5,
                    help='切った小片の板を、各辺でこのブロック数だけ外へ広げて隣と重ねる（動いたときの細い隙間を隠す。0=広げない）')
    a = ap.parse_args()
    build(a.gmo, a.outdir, a.name, a.size, a.plates, a.exclude, a.gain, a.sat, a.thickness, a.texel, a.unit, a.keep_front,
          a.dump_expected, a.plate_tex, not a.no_quantize, a.coverage, a.fine_parts, a.fine_texel, a.rig, a.motion,
          not a.no_blend, a.blend_step, a.blend_parts, a.blend_budget, a.seam_report, a.blend_tol, a.blend_margin)
