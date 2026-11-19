"""GLBをビューアと同じ手順で読み（作成側のコードは使わない）、指定アニメ・時刻の姿勢を描画して検証する。
使い方: python glb_pose_check.py <in.glb> <出力フォルダ> <アニメ名|rest> <秒> [yaw] [pitch]
"""
import json, math, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obj_preview

CT = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load(path):
    d = open(path, 'rb').read()
    jl, _ = struct.unpack_from('<II', d, 12)
    js = json.loads(d[20:20 + jl])
    bl = struct.unpack_from('<I', d, 20 + jl)[0]
    binb = d[28 + jl: 28 + jl + bl]
    return js, binb


def acc(js, binb, i):
    a = js['accessors'][i]
    v = js['bufferViews'][a['bufferView']]
    f, sz = CT[a['componentType']]
    n = NC[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    flat = struct.unpack_from('<%d%s' % (a['count'] * n, f), binb, off)
    return [list(flat[k * n:(k + 1) * n]) for k in range(a['count'])]


def mmul(a, b):  # 列優先16要素
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


def local(t, q, s):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1
    x, y, z, w = x / n, y / n, z / n, w / n
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    m = [0.0] * 16
    for c in range(3):
        for rr in range(3):
            m[c * 4 + rr] = r[rr][c] * s[c]
    m[12], m[13], m[14], m[15] = t[0], t[1], t[2], 1.0
    return m


def sample(times, vals, t, quat):
    if t <= times[0]:
        return vals[0]
    if t >= times[-1]:
        return vals[-1]
    lo, hi = 0, len(times) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if times[mid] <= t:
            lo = mid
        else:
            hi = mid
    u = (t - times[lo]) / ((times[hi] - times[lo]) or 1)
    a, b = vals[lo], vals[hi]
    if quat and sum(p * q for p, q in zip(a, b)) < 0:
        b = [-c for c in b]
    r = [p + (q - p) * u for p, q in zip(a, b)]
    if quat:
        n = math.sqrt(sum(c * c for c in r)) or 1
        r = [c / n for c in r]
    return r


def main():
    src, outdir, anim, tsec = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    yaw = float(sys.argv[5]) if len(sys.argv) > 5 else 0
    pitch = float(sys.argv[6]) if len(sys.argv) > 6 else 0
    js, binb = load(src)
    os.makedirs(outdir, exist_ok=True)
    nodes = js['nodes']
    T = [list(n.get('translation', [0, 0, 0])) for n in nodes]
    Q = [list(n.get('rotation', [0, 0, 0, 1])) for n in nodes]
    S = [list(n.get('scale', [1, 1, 1])) for n in nodes]
    if anim != 'rest':
        an = next(a for a in js['animations'] if a['name'] == anim)
        for ch in an['channels']:
            s = an['samplers'][ch['sampler']]
            times = [x[0] for x in acc(js, binb, s['input'])]
            vals = acc(js, binb, s['output'])
            node, path = ch['target']['node'], ch['target']['path']
            v = sample(times, vals, tsec, path == 'rotation')
            {'translation': T, 'rotation': Q, 'scale': S}[path][node] = v
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []):
            parent[c] = i
    Wm = {}

    def world(i):
        if i not in Wm:
            m = local(T[i], Q[i], S[i])
            Wm[i] = m if i not in parent else mmul(world(parent[i]), m)
        return Wm[i]
    skin = js['skins'][0]
    ibs = acc(js, binb, skin['inverseBindMatrices'])
    jm = [mmul(world(j), ibs[k]) for k, j in enumerate(skin['joints'])]

    # テクスチャを書き出し
    for i, img in enumerate(js['images']):
        v = js['bufferViews'][img['bufferView']]
        open(os.path.join(outdir, f'tex{i}.png'), 'wb').write(binb[v['byteOffset']: v['byteOffset'] + v['byteLength']])
    mats = []
    with open(os.path.join(outdir, 'pose.mtl'), 'w') as f:
        for i, m in enumerate(js['materials']):
            f.write(f'newmtl m{i}\n')
            bc = m['pbrMetallicRoughness'].get('baseColorTexture')
            if bc:
                f.write(f"map_Kd tex{js['textures'][bc['index']]['source']}.png\n")
    vbase = 1
    lines = ['mtllib pose.mtl']
    for node in nodes:
        if 'mesh' not in node:
            continue
        for p in js['meshes'][node['mesh']]['primitives']:
            at = p['attributes']
            pos = acc(js, binb, at['POSITION'])
            uv = acc(js, binb, at['TEXCOORD_0'])
            J = acc(js, binb, at['JOINTS_0']) + [] if True else None
            Wt = acc(js, binb, at['WEIGHTS_0'])
            if 'JOINTS_1' in at:
                J1, W1 = acc(js, binb, at['JOINTS_1']), acc(js, binb, at['WEIGHTS_1'])
                J = [a + b for a, b in zip(J, J1)]
                Wt = [a + b for a, b in zip(Wt, W1)]
            for k, (x, y, z) in enumerate(pos):
                ox = oy = oz = 0.0
                for jj, ww in zip(J[k], Wt[k]):
                    if ww == 0:
                        continue
                    m = jm[int(jj)]
                    ox += ww * (m[0] * x + m[4] * y + m[8] * z + m[12])
                    oy += ww * (m[1] * x + m[5] * y + m[9] * z + m[13])
                    oz += ww * (m[2] * x + m[6] * y + m[10] * z + m[14])
                lines.append(f'v {ox:.5f} {oy:.5f} {oz:.5f}')
                lines.append(f'vt {uv[k][0]:.5f} {1 - uv[k][1]:.5f}')
            idx = [i[0] for i in acc(js, binb, p['indices'])]
            lines.append(f"usemtl m{p.get('material', 0)}")
            for a in range(0, len(idx) - 2, 3):
                lines.append('f ' + ' '.join(f'{vbase + idx[a + b]}/{vbase + idx[a + b]}' for b in range(3)))
            vbase += len(pos)
    open(os.path.join(outdir, 'pose.obj'), 'w').write('\n'.join(lines) + '\n')
    out = os.path.join(outdir, f'pose_{anim}_{tsec:g}.png')
    obj_preview.render(os.path.join(outdir, 'pose.obj'), out, yaw, pitch, 560)
    print(out)


main()
