"""OBJ(+MTL, PNG)の簡易プレビュー（ソフトウェア描画。Pillowのみ）。
使い方: python obj_preview.py <model.obj> <出力.png> [yaw度] [pitch度] [サイズ]
画像は左上原点。深度バッファ付き、テクスチャのαは0.5未満を抜く。"""
import math, os, sys
from PIL import Image


def load(path):
    base = os.path.dirname(path)
    V, VT, F, mtl_of = [], [], [], {}
    cur = None
    mtlfile = None
    for ln in open(path, encoding='utf-8'):
        s = ln.split()
        if not s:
            continue
        if s[0] == 'v':
            V.append(tuple(map(float, s[1:4])))
        elif s[0] == 'vt':
            VT.append((float(s[1]), float(s[2])))
        elif s[0] == 'usemtl':
            cur = s[1]
        elif s[0] == 'mtllib':
            mtlfile = s[1]
        elif s[0] == 'f':
            idx = [tuple(int(x) if x else 0 for x in t.split('/')) for t in s[1:]]
            F.append((idx, cur))
    tex = {}
    if mtlfile:
        name = None
        for ln in open(os.path.join(base, mtlfile), encoding='utf-8'):
            s = ln.split()
            if not s:
                continue
            if s[0] == 'newmtl':
                name = s[1]
            elif s[0] == 'map_Kd' and name:
                tex[name] = Image.open(os.path.join(base, s[1])).convert('RGBA')
    return V, VT, F, tex


def render(path, out, yaw=0.0, pitch=0.0, size=700):
    V, VT, F, tex = load(path)
    ya, pa = math.radians(yaw), math.radians(pitch)
    cy, sy, cp, sp = math.cos(ya), math.sin(ya), math.cos(pa), math.sin(pa)

    def rot(p):
        x, y, z = p
        x, z = x * cy + z * sy, -x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        return x, y, z

    R = [rot(p) for p in V]
    xs, ys = [p[0] for p in R], [p[1] for p in R]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sc = (size - 20) / max(maxx - minx, maxy - miny, 1e-9)
    ox, oy = 10 - minx * sc, 10 + maxy * sc

    def proj(p):
        return p[0] * sc + ox, -p[1] * sc + oy

    img = Image.new('RGBA', (size, size), (28, 30, 40, 255))
    px = img.load()
    zb = [[-1e18] * size for _ in range(size)]
    for idx, mat in F:
        t = tex.get(mat)
        tw, th = (t.size if t else (1, 1))
        tp = t.load() if t else None
        a, b, c = [R[i[0] - 1] for i in idx[:3]]
        sa, sb, sc_ = proj(a), proj(b), proj(c)
        uv = [VT[i[1] - 1] if len(i) > 1 and i[1] else (0, 0) for i in idx[:3]]
        # 面の向き（陰影）
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        nl = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
        shade = 0.55 + 0.45 * abs(nz / nl)
        x0 = max(int(min(sa[0], sb[0], sc_[0])), 0)
        x1 = min(int(max(sa[0], sb[0], sc_[0])) + 1, size - 1)
        y0 = max(int(min(sa[1], sb[1], sc_[1])), 0)
        y1 = min(int(max(sa[1], sb[1], sc_[1])) + 1, size - 1)
        den = (sb[1] - sc_[1]) * (sa[0] - sc_[0]) + (sc_[0] - sb[0]) * (sa[1] - sc_[1])
        if abs(den) < 1e-9:
            continue
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                l1 = ((sb[1] - sc_[1]) * (x + .5 - sc_[0]) + (sc_[0] - sb[0]) * (y + .5 - sc_[1])) / den
                l2 = ((sc_[1] - sa[1]) * (x + .5 - sc_[0]) + (sa[0] - sc_[0]) * (y + .5 - sc_[1])) / den
                l3 = 1 - l1 - l2
                if l1 < -1e-4 or l2 < -1e-4 or l3 < -1e-4:
                    continue
                z = l1 * a[2] + l2 * b[2] + l3 * c[2]
                if z <= zb[y][x]:
                    continue
                if tp:
                    u = l1 * uv[0][0] + l2 * uv[1][0] + l3 * uv[2][0]
                    v = l1 * uv[0][1] + l2 * uv[1][1] + l3 * uv[2][1]
                    col = tp[int(u * tw) % tw, int(v * th) % th]
                    if col[3] < 128:
                        continue
                    col = (int(col[0] * shade), int(col[1] * shade), int(col[2] * shade), 255)
                else:
                    g = int(200 * shade)
                    col = (g, g, g, 255)
                zb[y][x] = z
                px[x, y] = col
    img.save(out)


if __name__ == '__main__':
    a = sys.argv
    render(a[1], a[2], float(a[3]) if len(a) > 3 else 0, float(a[4]) if len(a) > 4 else 0, int(a[5]) if len(a) > 5 else 700)
