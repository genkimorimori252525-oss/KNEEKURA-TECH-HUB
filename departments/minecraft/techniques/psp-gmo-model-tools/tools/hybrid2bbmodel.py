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


def _rodrigues(w):
    """回転ベクトル（ラジアン）-> 3x3 回転行列。"""
    th = math.sqrt(sum(c * c for c in w))
    if th < 1e-12:
        return [[1.0, -w[2], w[1]], [w[2], 1.0, -w[0]], [-w[1], w[0], 1.0]]
    k = [c / th for c in w]
    c, s = math.cos(th), math.sin(th)
    K = [[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]]
    KK = _m3mul(K, K)
    return [[(1.0 if r == cc else 0.0) + s * K[r][cc] + (1 - c) * KK[r][cc] for cc in range(3)] for r in range(3)]


def _solve_small(A, b):
    """小さい連立一次方程式（部分ピボットのガウス消去）。特異なら 0 を返す。"""
    n = len(b)
    M = [A[r][:] + [b[r]] for r in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        if abs(M[c][c]) < 1e-18:
            return [0.0] * n
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for cc in range(c, n + 1):
                    M[r][cc] -= f * M[c][cc]
    return [M[r][n] / M[r][r] for r in range(n)]


def join_helpers(pairs, H, Dfix, nb, lam, r0, corr=None, sweeps=6, damp=0.8):
    """結合処理（1 時刻ぶん）。補助の骨 h は剛体で、点 p を x = R_h (p - c_h) + m_h に運ぶ（H[h] = (R, c, m)）。
    継ぎ目の組 pairs = [(keyA, pA, keyB, pB)]（静止位置が同じ点。key < nb は元の骨で動かさない: Dfix[key] の 4x4）について、
    補助の骨ごとに小さな補正（m まわりの回転 ω と移動 t）を足し、継ぎ目の点が一致するように寄せる。
    元の動きから離れすぎないよう、補正の大きさに罰 λ（回転は半径 r0 で長さに換算）を付ける。Jacobi 反復（減衰 damp）。
    戻り: 補正 [(ω, t)]（各補助の骨）。次の時刻の初期値に使える。"""
    nh = len(H)
    corr = [(list(w), list(t)) for w, t in corr] if corr else [([0.0] * 3, [0.0] * 3) for _ in range(nh)]

    def place(key, p, Rc):
        if key < nb:
            return _apply4(Dfix[key], p)
        h = key - nb
        R, c0, m = H[h]
        x = [sum(R[r][j] * (p[j] - c0[j]) for j in range(3)) for r in range(3)]  # m からの相対
        y = [sum(Rc[h][r][j] * x[j] for j in range(3)) for r in range(3)]
        t = corr[h][1]
        return [y[a] + m[a] + t[a] for a in range(3)], [y[a] for a in range(3)]
    for _ in range(sweeps):
        Rc = [_rodrigues(w) for w, _ in corr]
        AtA = [None] * nh
        Atb = [None] * nh
        cnt = [0] * nh
        for ka, pa, kb, pb in pairs:
            A = place(ka, pa, Rc)
            B = place(kb, pb, Rc)
            xa, ra = (A, None) if ka < nb else A
            xb, rb = (B, None) if kb < nb else B
            e = [xa[a] - xb[a] for a in range(3)]
            for key, sgn, r in ((ka, 1.0, ra), (kb, -1.0, rb)):
                if key < nb:
                    continue
                h = key - nb
                if AtA[h] is None:
                    AtA[h] = [[0.0] * 6 for _ in range(6)]
                    Atb[h] = [0.0] * 6
                # x(δω, δt) ≈ x + δω × r + δt  → ヤコビアン J = [-[r]×, I]
                J = [[0.0, r[2], -r[1], 1.0, 0.0, 0.0], [-r[2], 0.0, r[0], 0.0, 1.0, 0.0], [r[1], -r[0], 0.0, 0.0, 0.0, 1.0]]
                for a in range(3):
                    Ja = J[a]
                    for u in range(6):
                        if Ja[u]:
                            Atb[h][u] -= sgn * Ja[u] * e[a]
                            for v in range(6):
                                AtA[h][u][v] += Ja[u] * Ja[v]
                cnt[h] += 1
        for h in range(nh):
            if not cnt[h]:
                continue
            w, t = corr[h]
            reg = [lam * cnt[h] * r0 * r0] * 3 + [lam * cnt[h]] * 3
            cur = w + t
            A = [[AtA[h][u][v] + (reg[u] if u == v else 0.0) for v in range(6)] for u in range(6)]
            d = _solve_small(A, [Atb[h][u] - reg[u] * cur[u] for u in range(6)])
            corr[h] = ([w[a] + damp * d[a] for a in range(3)], [t[a] + damp * d[3 + a] for a in range(3)])
    return corr


def build_blend_animations(motion_paths, bones, Wg, helpers, hgid, S4, S4i, prefix='', tol_pos=0.5, tol_rot=0.5,
                           join_pairs=None, join_lam=0.02, join_r0=128.0, join_every=3, join_sweeps=6, join_stats=None):
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
        nb = len(bones)
        fixed = sorted({k for ka, _a, kb, _b in (join_pairs or []) for k in (ka, kb) if k < nb})
        Dfix_frames = []
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
            if fixed:
                Dfix_frames.append({b: D[b] if b in D else mul(mul(S4, mul(world(b), Winv[b])), S4i) for b in fixed})
        if join_pairs and helpers:
            # 結合処理: join_every フレームごとに解き（前の解から始める）、間は補正を線形補間して全フレームに掛ける
            solve_at = list(range(0, len(frames), join_every))
            if solve_at[-1] != len(frames) - 1:
                solve_at.append(len(frames) - 1)
            sols, corr = {}, None
            for fi in solve_at:
                H = [(rots[k][fi], helpers[k]['pivot_bb'], [poss[k][fi][a] + helpers[k]['pivot_bb'][a] for a in range(3)])
                     for k in range(len(helpers))]
                Dfx = Dfix_frames[fi] if fixed else {}
                corr = join_helpers(join_pairs, H, Dfx, nb, join_lam, join_r0, corr,
                                    sweeps=join_sweeps if sols else 3 * join_sweeps)
                sols[fi] = corr
                if join_stats is not None:  # 継ぎ目の開き（寄せる前・後、モデル単位）
                    zero = [([0.0] * 3, [0.0] * 3)] * len(helpers)
                    for cc, lst in ((zero, join_stats.setdefault('before', [])), (corr, join_stats.setdefault('after', []))):
                        Rc = [_rodrigues(wv) for wv, _ in cc]

                        def at(key, p):
                            if key < nb:
                                return _apply4(Dfx[key], p)
                            R, c0, m = H[key - nb]
                            x = [sum(R[r][j] * (p[j] - c0[j]) for j in range(3)) for r in range(3)]
                            Rk, t = Rc[key - nb], cc[key - nb][1]
                            return [sum(Rk[r][j] * x[j] for j in range(3)) + m[r] + t[r] for r in range(3)]
                        lst.extend(math.dist(at(ka, pa), at(kb, pb)) for ka, pa, kb, pb in join_pairs)
            for i0, i1 in zip(solve_at, solve_at[1:] + [solve_at[-1]]):
                for fi in range(i0, (i1 if i1 > i0 else i0 + 1)):
                    u = (fi - i0) / (i1 - i0) if i1 > i0 else 0.0
                    for k in range(len(helpers)):
                        (w0, t0), (w1, t1) = sols[i0][k], sols[i1][k]
                        w = [w0[a] + (w1[a] - w0[a]) * u for a in range(3)]
                        t = [t0[a] + (t1[a] - t0[a]) * u for a in range(3)]
                        rots[k][fi] = _m3mul(_rodrigues(w), rots[k][fi])  # m（ピボットの行き先）まわりの回転
                        poss[k][fi] = [poss[k][fi][a] + t[a] for a in range(3)]
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


def subdivide_for_skin(polys, Ds, cell, budget, match, max_depth=6, min_piece=4.0):
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
    # 元の面の辺が、ほかの面と共有されているか（共有されていない辺 = 服の縁などの外周。広げるとはみ出す）
    ekey = lambda a, b: tuple(sorted((tuple(round(c / cell * 64) for c in a), tuple(round(c / cell * 64) for c in b))))
    ecount = {}
    for q in polys:
        if match(q) and 'vw' in q:
            n = len(q['pos'])
            for i in range(n):
                k = ekey(q['pos'][i], q['pos'][(i + 1) % n])
                ecount[k] = ecount.get(k, 0) + 1

    def emit(src, P, UV, VW, depth, tags):
        wc = _mix(VW, [1 / len(VW)] * len(VW))
        # grow[i]: 辺 i（P[i]→P[i+1]）を広げてよいか。元の面の内側の辺（切って生まれた辺・対角線）か、隣と共有の辺
        grow = [t is None or ecount.get(t, 0) >= 2 for t in tags]
        out.append(dict(src, pos=P, uv=UV, vw=VW, wts=wc, bone=max(wc, key=wc.get), split=depth > 0, grow=grow))

    def split(src, P, UV, VW, depth, tags):
        wc = _mix(VW, [1 / 3] * 3)
        dom = max(wc, key=wc.get)
        err = 0.0
        for p, vw in zip(P, VW):
            err = max(err, sum(abs(vw.get(b, 0.0) - wc.get(b, 0.0)) * mrel(p, b, dom) for b in set(vw) | set(wc) if b != dom))
        edge = max(math.dist(P[i], P[(i + 1) % 3]) for i in range(3)) / cell
        # 切った子の最長辺（= edge/2）が min_piece ブロック未満になるなら切らない。小さすぎる板は絵が 1〜2 ピクセルになり、
        # 色がモザイク状に崩れる（胸・袖など、もともと面の細かい所が壊れた）。切るのは大きな面（スカート）だけ
        if err <= budget or edge / 2 < min_piece or depth >= max_depth:
            emit(src, P, UV, VW, depth, tags)
            return
        M = [tuple((P[i][a] + P[(i + 1) % 3][a]) / 2 for a in range(3)) for i in range(3)]
        MU = [tuple((UV[i][a] + UV[(i + 1) % 3][a]) / 2 for a in range(2)) for i in range(3)] if UV else None
        MW = [_mix([VW[i], VW[(i + 1) % 3]], (0.5, 0.5)) for i in range(3)]
        T0, T1, T2 = tags
        # 子の三角形と、その 3 辺が親のどの辺の上にあるか（None = 親の内側に新しくできた辺）
        for idx, ctags in (((0, 'm0', 'm2'), (T0, None, T2)), (('m0', 1, 'm1'), (T0, T1, None)),
                           (('m2', 'm1', 2), (None, T1, T2)), (('m0', 'm1', 'm2'), (None, None, None))):
            pick = lambda arr, marr: [arr[i] if isinstance(i, int) else marr[int(i[1])] for i in idx]
            split(src, pick(P, M), pick(UV, MU) if UV else None, pick(VW, MW), depth + 1, ctags)

    for q in polys:
        if not match(q) or 'vw' not in q:
            out.append(q)
            continue
        P, UV, VW = q['pos'], q['uv'], q['vw']
        n = len(P)
        for k in range(1, n - 1):  # 四角形以上は扇形に三角形へ（対角線は内側の辺）
            tri = [0, k, k + 1]
            tags = (ekey(P[0], P[1]) if k == 1 else None, ekey(P[k], P[k + 1]),
                    ekey(P[k + 1], P[0]) if k + 1 == n - 1 else None)
            split(q, [P[i] for i in tri], [UV[i] for i in tri] if UV else None, [VW[i] for i in tri], 0, tags)
    return out


def _pt_tri_dist2(p, a, b, c):
    """点 p と三角形 abc の最短距離の 2 乗（Ericson, Real-Time Collision Detection 5.1.5）。"""
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0:
        return dot(ap, ap)
    bp = sub(p, b)
    d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0 and d4 <= d3:
        return dot(bp, bp)
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1 - d3)
        q = sub(p, add(a, mul(ab, v)))
        return dot(q, q)
    cp = sub(p, c)
    d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0 and d5 <= d6:
        return dot(cp, cp)
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2 - d6)
        q = sub(p, add(a, mul(ac, w)))
        return dot(q, q)
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        q = sub(p, add(b, mul(sub(c, b), w)))
        return dot(q, q)
    den = 1.0 / (va + vb + vc)
    v, w = vb * den, vc * den
    q = sub(p, add(a, add(mul(ab, v), mul(ac, w))))
    return dot(q, q)


def cells_to_bones(cells, polys, to_vox, bucket=8):
    """ボクセルのセル -> 骨（key）の割り当て。セルの中心に一番近い元の三角形の key を取る。
    戻り: {key: {セル: ブロック}}。polys の各面は key を持つこと。to_vox はゲーム座標 -> 連続のボクセル座標。"""
    tris = []
    for q in polys:
        P = [list(to_vox(p)) for p in q['pos']]
        for k in range(1, len(P) - 1):
            tris.append((P[0], P[k], P[k + 1], q['key']))
    grid = {}
    for ti, (a, b, c, _k) in enumerate(tris):
        lo = [math.floor((min(a[i], b[i], c[i]) - 1.5) / bucket) for i in range(3)]
        hi = [math.floor((max(a[i], b[i], c[i]) + 1.5) / bucket) for i in range(3)]
        for x in range(lo[0], hi[0] + 1):
            for y in range(lo[1], hi[1] + 1):
                for z in range(lo[2], hi[2] + 1):
                    grid.setdefault((x, y, z), []).append(ti)
    out = {}
    for cc, blk in cells.items():
        p = [cc[i] + 0.5 for i in range(3)]
        cand = grid.get(tuple(math.floor(p[i] / bucket) for i in range(3)))
        if not cand:  # 近くの三角形が無い（ほぼ起きない）: 全部から探す
            cand = range(len(tris))
        best = min(cand, key=lambda ti: _pt_tri_dist2(p, *tris[ti][:3]))
        out.setdefault(tris[best][3], {})[cc] = blk
    return out


def expand_triangle(P, UV, margins, cap):
    """三角形の辺ごとに外へ margins[i]（辺 i = P[i]→P[i+1]、P と同じ単位）だけ出す。角の移動は cap 以下に抑える
    （細長い三角形で角が大きく飛び出し、トゲになるのを防ぐ。超えるときは全辺の出し幅を同じ比率で縮める）。
    新しい角は元の三角形の平面上（重心座標の一次結合）に置き、UV も同じ重心座標で延ばす（絵がそのまま続く）。
    切った小片どうしは別の補助の骨に乗るので、動くと細い隙間が開く。少し重ねてその隙間を隠すために使う。"""
    if not any(m > 0 for m in margins):
        return P, UV
    ex = [P[1][k] - P[0][k] for k in range(3)]
    ln = math.sqrt(sum(c * c for c in ex))
    nrm = cross(ex, [P[2][k] - P[0][k] for k in range(3)])
    if ln <= 1e-12 or dot(nrm, nrm) <= 1e-24:
        return P, UV
    ex = [c / ln for c in ex]
    ey = norm(cross(nrm, ex))
    Q = [(dot(sub(p, P[0]), ex), dot(sub(p, P[0]), ey)) for p in P]  # 2D（反時計回り）

    def corners(ms):
        lines = []
        for i in range(3):
            a, b = Q[i], Q[(i + 1) % 3]
            d = (b[0] - a[0], b[1] - a[1])
            L = math.hypot(*d)
            n = (d[1] / L, -d[0] / L)  # 反時計回りの三角形の外向き法線
            lines.append((n, n[0] * a[0] + n[1] * a[1] + ms[i]))
        out = []
        for j in range(3):  # 角 j = 辺 j-1 と辺 j の交点
            (n1, c1), (n2, c2) = lines[j - 1], lines[j]
            det = n1[0] * n2[1] - n1[1] * n2[0]
            if abs(det) < 1e-12:
                return None
            out.append(((c1 * n2[1] - c2 * n1[1]) / det, (n1[0] * c2 - n2[0] * c1) / det))
        return out
    C = corners(margins)
    if C is None:
        return P, UV
    move = max(math.dist(C[j], Q[j]) for j in range(3))
    if move > cap:  # 出し幅に比例して角が動くので、同じ比率で縮める
        C = corners([m * cap / move for m in margins])
        if C is None:
            return P, UV

    def bary(x):
        (x0, y0), (x1, y1), (x2, y2) = Q
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        w0 = ((y1 - y2) * (x[0] - x2) + (x2 - x1) * (x[1] - y2)) / d
        w1 = ((y2 - y0) * (x[0] - x2) + (x0 - x2) * (x[1] - y2)) / d
        return (w0, w1, 1 - w0 - w1)
    W = [bary(c) for c in C]
    P2 = [tuple(sum(w[i] * P[i][k] for i in range(3)) for k in range(3)) for w in W]
    UV2 = [tuple(sum(w[i] * UV[i][k] for i in range(3)) for k in range(2)) for w in W] if UV else UV
    return P2, UV2


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
          blend_parts='^AL_body', blend_budget=2.0, seams=False, blend_tol=0.25, blend_margin=0.5, blend_min_piece=4.0,
          join_lam=0.02):
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
    n_split, Ds, seam_stats, join_report = 0, None, None, None
    if rig and blend and motion_paths and blend_budget and blend_budget > 0:
        # 面の中で重みが大きく変わる面（伸び縮みする所）を細かく切ってから、板・ブロックにする
        bre = re.compile(blend_parts) if blend_parts else None
        Ds = sample_deforms(motion_paths, bones)
        before = len(polys)
        polys = subdivide_for_skin(polys, Ds, cell, blend_budget, lambda q: bre is None or bool(bre.search(q['part'])),
                                   min_piece=blend_min_piece)
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

    # ブロックは骨に関係なく一度にボクセル化する（静止姿勢の形と色を、骨なしの最終形と完全に同じにする）。
    # rig のときは、各セルを「一番近い元の三角形」の骨に割り当てる（1つのキューブが2本の骨にまたがらないよう、骨ごとに統合する）
    nonplate = [q for q in polys if not is_plate(q)]
    allsol = voxel_solid(nonplate)
    claimed = set(allsol)
    if rig:
        solids = cells_to_bones(allsol, nonplate, to_vox)
    else:
        solids = {None: allsol} if allsol else {}
    solid = allsol

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
            P2, UV2 = expand_triangle(q['pos'], q['uv'], [blend_margin * cell if g else 0.0 for g in q['grow']],
                                      2 * blend_margin * cell)
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
            # 結合処理の継ぎ目: 静止位置が同じで頂点の重みも同じ（元のメッシュでは同じ頂点）なのに、別の骨に乗っている点の組
            join_pairs, join_stats = None, None
            if join_lam and join_lam > 0:
                jre = re.compile(blend_parts) if blend_parts else None
                jp = [q for q in polys if 'vw' in q and (jre is None or jre.search(q['part']))]
                share = {}
                for i, q in enumerate(jp):
                    for k, p in enumerate(q['pos']):
                        share.setdefault(tuple(round(c / cell * 64) for c in p), []).append((i, k))
                same_w = lambda x, y: all(abs(x.get(b, 0.0) - y.get(b, 0.0)) < 1e-3 for b in set(x) | set(y))
                join_pairs = []
                for v in share.values():
                    # 注意: l は寸法（w, h, l = dims）。ループ変数に使うと to_bb の向きが壊れる（実際に踏んだ）
                    for (i, k), (j, kj) in zip(v, v[1:]):
                        a_, b_ = jp[i]['key'], jp[j]['key']
                        if a_ != b_ and (a_ >= nb or b_ >= nb) and same_w(jp[i]['vw'][k], jp[j]['vw'][kj]):
                            join_pairs.append((a_, to_bb(jp[i]['pos'][k]), b_, to_bb(jp[j]['pos'][kj])))
                join_stats = {}
            extra = build_blend_animations(motion_paths, bones, Wg, helpers, hgid, S4, S4i, prefix,
                                           tol_pos=blend_tol * unit, tol_rot=max(0.5, 4 * blend_tol),
                                           join_pairs=join_pairs, join_lam=join_lam, join_r0=8 * unit, join_stats=join_stats)
            if join_stats:
                def _st(a):
                    a = sorted(x / unit for x in a)
                    pc = lambda p: round(a[min(len(a) - 1, int(len(a) * p))], 3)
                    return dict(max=round(a[-1], 3), p99=pc(0.99), p95=pc(0.95), p50=pc(0.5))
                join_report = dict(pairs=len(join_pairs), before=_st(join_stats['before']), after=_st(join_stats['after']))
                print('join (seam gap in blocks, solved frames):', join_report)
            for an in anims:
                if an['name'] in extra:
                    animators, mt = extra[an['name']]
                    an['animators'].update(animators)
                    an['length'] = round(max(an['length'], mt), 5)
        rig_info = dict(mn=mn, cell=cell, dims=dims, unit=unit, keep_front=keep_front, ox=ox, oz=oz,
                        split_faces=n_split, seams=seam_stats, join=join_report,
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
    ap.add_argument('--blend-min-piece', type=float, default=4.0,
                    help='面を切るときの小片の最小の大きさ（ブロック）。これより小さくは切らない（小さい板は絵が崩れる）')
    ap.add_argument('--join', type=float, default=0.02,
                    help='結合処理の強さ λ（小さいほど継ぎ目を強く寄せ、元の動きから離れる。0 = 結合しない）')
    a = ap.parse_args()
    build(a.gmo, a.outdir, a.name, a.size, a.plates, a.exclude, a.gain, a.sat, a.thickness, a.texel, a.unit, a.keep_front,
          a.dump_expected, a.plate_tex, not a.no_quantize, a.coverage, a.fine_parts, a.fine_texel, a.rig, a.motion,
          not a.no_blend, a.blend_step, a.blend_parts, a.blend_budget, a.seam_report, a.blend_tol, a.blend_margin,
          a.blend_min_piece, a.join)
