"""PSP GMO/GIM モデル変換ツールの単体テスト。

ゲーム由来のデータは一切使わず、仕様どおりに組み立てた合成データだけで検証する。
標準ライブラリだけで動く（GIM→PNGの変換は Pillow が要るのでここでは使わない）。
"""
import math
import struct
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / 'departments' / 'minecraft' / 'techniques' / 'psp-gmo-model-tools' / 'tools'
sys.path.insert(0, str(TOOLS))

import gim  # noqa: E402
import gmo  # noqa: E402
import gmo2bbmodel  # noqa: E402
import gmo2gltf  # noqa: E402
import gmo2obj  # noqa: E402
import obj2schem  # noqa: E402
import schem_check  # noqa: E402
import voxel2bbmodel  # noqa: E402
import hybrid2bbmodel  # noqa: E402


# ---------------------------------------------------------------- 合成GMOの組み立て


def chunk(type_, payload=b'', header=b''):
    """通常チャンク: u16 type, u16 header_size, u32 total_size + header + payload。"""
    hs = 8 + len(header)
    return struct.pack('<HHI', type_, hs, hs + len(payload)) + header + payload


def leaf(type_, payload):
    """属性(リーフ)チャンク: 0x8000 が立ち、ヘッダ長は0、データは+8から。"""
    return struct.pack('<HHI', type_ | 0x8000, 0, 8 + len(payload)) + payload


def named_header(name):
    """容器チャンクのヘッダ: u32, u32, 名前(16Bまで)。"""
    raw = name.encode('ascii')
    return struct.pack('<II', 0, 0) + raw + b'\0' * (-len(raw) % 4 or 4)


def synthetic_gmo():
    scale_bias = leaf(0x15, struct.pack('<I6f', 384, 1.0, 2.0, 3.0, 100.0, 200.0, 300.0))
    uv_bias = leaf(0x15, struct.pack('<I4f', 3, -0.5, 0.25, 1.0, 0.5))
    model = chunk(3, scale_bias + uv_bias, named_header('model-0'))
    root = chunk(2, model, struct.pack('<II', 0x10, 0x10)[:8])
    return b'OMG.00.1PSP\0\0\0\0\0' + root


# ---------------------------------------------------------------- gmo


def test_ge_layout_matches_real_vertex_types():
    # 重み8bit×1, UV16bit, 色4444, 法線8bit, 位置16bit => 18バイト、位置は+12
    lay = gmo.ge_layout(0x1200133a)
    assert lay['stride'] == 18
    assert lay['weights'] == (0, 1, 1)
    assert lay['tc'] == (2, 2)
    assert lay['pos'] == (12, 2)
    assert lay['index'] == 2 and lay['morphs'] == 1
    # 色なし: 重み, UV, 法線, 位置 => 16バイト、位置は+10
    lay = gmo.ge_layout(0x10001322)
    assert lay['stride'] == 16 and lay['pos'] == (10, 2) and 'color' not in lay


def test_ge_layout_weight_count():
    # 0x14015322: 重みの本数が bits14-16 に入る
    assert gmo.ge_layout(0x14015322)['weights'][2] == 6
    assert gmo.ge_layout(0x1601d322)['weights'][2] == 8


def test_parse_container_and_leaf_chunks():
    tree = gmo.parse(synthetic_gmo())
    assert [c.type for c in tree] == [2]
    model = tree[0].children[0]
    assert model.type == 3 and model.name == 'model-0'
    leaves = model.kids(0x8015)
    assert len(leaves) == 2 and all(c.leaf and c.hs == 8 for c in leaves)
    assert struct.unpack_from('<I', leaves[0].payload)[0] == 384


def test_ref_masks_low_12_bits():
    assert gmo.ref(0x00071000) == 0
    assert gmo.ref(0x00082003) == 3


def test_read_scale_bias_both_forms():
    model = gmo.parse(synthetic_gmo())[0].children[0]
    pos_bias, pos_scale, uv_bias, uv_scale = gmo2obj.read_scale_bias(model)
    assert pos_bias == (1.0, 2.0, 3.0) and pos_scale == (100.0, 200.0, 300.0)
    assert uv_bias == (-0.5, 0.25) and uv_scale == (1.0, 0.5)


# ---------------------------------------------------------------- 行列・回転


def test_euler_zyx_known_rotations():
    ex = gmo2bbmodel.euler_zyx((-1.0, 0.0, 0.0, 0.0))  # X軸180度（左側の骨）
    assert abs(abs(ex[0]) - 180) < 1e-6 and abs(ex[1]) < 1e-6 and abs(ex[2]) < 1e-6
    s = math.sqrt(0.5)
    ez = gmo2bbmodel.euler_zyx((0.0, 0.0, s, s))  # Z軸90度
    assert abs(ez[0]) < 1e-6 and abs(ez[1]) < 1e-6 and abs(ez[2] - 90) < 1e-6


def test_euler_roundtrip_through_matrix():
    q = (0.1, 0.2, 0.3, math.sqrt(1 - 0.01 - 0.04 - 0.09))
    e = [math.radians(v) for v in gmo2bbmodel.euler_zyx(q)]
    # three.js の 'ZYX' 順: R = Rz * Ry * Rx
    cx, cy, cz = (math.cos(v) for v in e)
    sx, sy, sz = (math.sin(v) for v in e)
    r = [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
         [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
         [-sy, cy * sx, cy * cx]]
    m = gmo2gltf.trs((0, 0, 0), q)
    for i in range(3):
        for j in range(3):
            assert abs(r[i][j] - m[i][j]) < 1e-9


def test_rigid_inverse_is_identity():
    m = gmo2gltf.trs((10.0, -4.0, 7.5), (0.2, -0.4, 0.1, math.sqrt(1 - 0.04 - 0.16 - 0.01)))
    p = gmo2gltf.mul(m, gmo2gltf.rigid_inv(m))
    for i in range(4):
        for j in range(4):
            assert abs(p[i][j] - (1.0 if i == j else 0.0)) < 1e-9


def test_qmul_composes_like_matrices():
    a = (0.0, 1.0, 0.0, 0.0)  # Y軸180度
    b = (0.0, 0.0, math.sqrt(0.5), math.sqrt(0.5))
    q = gmo2bbmodel.qmul(a, b)
    ma, mb = gmo2gltf.trs((0, 0, 0), a), gmo2gltf.trs((0, 0, 0), b)
    mq = gmo2gltf.trs((0, 0, 0), q)
    prod = gmo2gltf.mul(ma, mb)
    for i in range(3):
        for j in range(3):
            assert abs(prod[i][j] - mq[i][j]) < 1e-9


# ---------------------------------------------------------------- キー間引き


def test_simplify_drops_linear_keys_but_keeps_spike():
    times = list(range(11))
    linear = [[2.0 * t] for t in times]
    assert gmo2bbmodel.simplify(times, linear, 0.01) == [0, 10]
    spiky = [list(v) for v in linear]
    spiky[5] = [50.0]
    kept = gmo2bbmodel.simplify(times, spiky, 0.01)
    assert 5 in kept and kept[0] == 0 and kept[-1] == 10


# ---------------------------------------------------------------- GIM


def gim_block(type_, body):
    return struct.pack('<HHIII', type_, 0, 16 + len(body), 16 + len(body), 16) + body


def gim_plane(fmt, order, w, h, pitch_align, height_align, pixels):
    header = bytearray(0x40)
    struct.pack_into('<H', header, 0, 0x30)
    struct.pack_into('<7H', header, 4, fmt, order, w, h, 0, pitch_align, height_align)
    struct.pack_into('<I', header, 0x1c, 0x40)  # ピクセル開始オフセット
    return bytes(header) + pixels


def test_gim_decode_swizzled_index8():
    w, h = 32, 8
    palette = [(10 * i, 20 * i, 30 * i, 255 - i) for i in range(4)]
    idx = [[(x + y) % 4 for x in range(w)] for y in range(h)]
    # PSPスウィズル: 16バイト幅×8行のブロックを横に並べて順に格納
    swz = bytearray()
    for bx in range(w // 16):
        for r in range(8):
            swz += bytes(idx[r][bx * 16:(bx + 1) * 16])
    pal_pixels = b''.join(bytes(c) for c in palette)
    image = gim_block(4, gim_plane(5, 1, w, h, 16, 8, bytes(swz)))
    pal = gim_block(5, gim_plane(3, 0, 4, 1, 1, 1, pal_pixels))
    picture = gim_block(3, pal + image)
    root = gim_block(2, picture)
    data = b'MIG.00.1PSP\0\0\0\0\0' + root
    out_w, out_h, rgba = gim.decode(data)
    assert (out_w, out_h) == (w, h)
    for y in range(h):
        for x in range(w):
            assert tuple(rgba[(y * w + x) * 4:(y * w + x) * 4 + 4]) == palette[idx[y][x]]


def test_gim_decode_rejects_non_gim():
    try:
        gim.decode(b'not a gim file at all....')
    except ValueError:
        return
    raise AssertionError('ValueError が出るはず')


# ---------------------------------------------------------------- ボクセル化 / .schem


def test_varint_known_values():
    assert obj2schem.varint(0) == b'\x00'
    assert obj2schem.varint(127) == b'\x7f'
    assert obj2schem.varint(128) == b'\x80\x01'
    assert obj2schem.varint(300) == b'\xac\x02'
    assert schem_check.decode_varints(b'\x00\x7f\x80\x01\xac\x02') == [0, 127, 128, 300]


def test_palette_roundtrips_through_nearest_color():
    pal = obj2schem.build_palette()
    assert len(pal) >= 50 and all(n.startswith('minecraft:') for n in pal)
    exact = obj2schem.to_blocks({(i, 0, 0): rgb for i, rgb in enumerate(pal.values())}, pal)
    assert [exact[(i, 0, 0)] for i in range(len(pal))] == list(pal)


def test_adjust_is_identity_at_one_and_brightens():
    c = (40.0, 50.0, 90.0)
    assert obj2schem.adjust(c, 1.0, 1.0) == c
    b = obj2schem.adjust(c, 1.3, 1.0)
    assert all(b[i] > c[i] for i in range(3))
    assert max(obj2schem.adjust((250.0, 250.0, 250.0), 2.0, 1.0)) == 255.0


def test_voxelize_makes_a_hollow_shell_inside_bounds():
    # 立方体の 1 面だけ（2 三角形）。テクスチャなし → 灰色。中は塗られない。
    V = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0), (0, 0, 10), (10, 0, 10)]
    tris = [((1,), (2,), (3,), None, 'g'), ((1,), (3,), (4,), None, 'g')]
    dims, cell, colors = obj2schem.voxelize(V, [], tris, {}, 10)
    assert cell == 1.0 and dims[2] == 1  # 面は z=0 の 1 層だけ
    assert all(0 <= k[a] < dims[a] for k in colors for a in range(3))
    assert len(colors) >= 90  # 10x10 の面をほぼ埋める


def test_schem_write_then_independent_check(tmp_path=None):
    import tempfile
    d = Path(tmp_path) if tmp_path else Path(tempfile.mkdtemp())
    blocks = {(0, 0, 0): 'minecraft:blue_concrete', (2, 1, 3): 'minecraft:white_concrete',
              (1, 3, 2): 'minecraft:blue_concrete'}
    path = d / 't.schem'
    obj2schem.write_schem(str(path), (3, 4, 4), blocks, 't')
    mats = d / 't.materials.tsv'
    mats.write_text('block\tcount\nminecraft:blue_concrete\t2\nminecraft:white_concrete\t1\n', encoding='utf-8')
    info, problems = schem_check.check(str(path), str(mats), allow=list(obj2schem.build_palette()))
    assert problems == [] and info['dims'] == (3, 4, 4) and info['solid'] == 3
    assert info['data_version'] == 3465 and info['version'] == 2


def test_schem_check_detects_tampering():
    import gzip
    import tempfile
    d = Path(tempfile.mkdtemp())
    path = d / 'bad.schem'
    obj2schem.write_schem(str(path), (2, 2, 2), {(0, 0, 0): 'minecraft:stone'}, 'bad')
    raw = bytearray(gzip.open(path, 'rb').read())
    raw = raw[:-3]  # 末尾を切って壊す
    bad = d / 'bad2.schem'
    with gzip.open(bad, 'wb') as f:
        f.write(bytes(raw))
    try:
        info, problems = schem_check.check(str(bad))
    except ValueError:
        return  # 構造が壊れていれば例外で止まってよい
    assert problems


# ---------------------------------------------------------------- 立方体モデル（ボクセル → Blockbench）


def _l_shape():
    return {(x, y, z) for x in range(4) for y in range(2) for z in range(3)} | {(0, 2, 0), (0, 3, 0), (1, 2, 0)}


def test_partition_covers_cells_exactly_once():
    cells = _l_shape()
    for seed in ((0, 1, 2), (2, 1, 0)):
        for axes in ((0, 1, 2), (1, 2, 0)):
            boxes = voxel2bbmodel.partition(cells, seed, axes)
            seen = []
            for lo, hi in boxes:
                seen += [(x, y, z) for x in range(lo[0], hi[0]) for y in range(lo[1], hi[1]) for z in range(lo[2], hi[2])]
            assert len(seen) == len(set(seen)) and set(seen) == cells  # 重なりなし・過不足なし


def test_fill_cavities_fills_closed_but_not_open_shells():
    dims = (5, 5, 5)
    shell = {(x, y, z) for x in range(5) for y in range(5) for z in range(5)
             if x in (0, 4) or y in (0, 4) or z in (0, 4)}
    assert len(voxel2bbmodel.fill_cavities(shell, dims)) == 125  # 内側 3x3x3 = 27 が埋まる
    holed = shell - {(2, 4, 2)}  # 上に穴 -> 外とつながるので埋めない
    assert voxel2bbmodel.fill_cavities(holed, dims) == holed


def test_face_cell_mapping_follows_blockbench_uv_directions():
    box = ((0, 0, 0), (2, 1, 3))  # dx=2, dy=1, dz=3
    w, h, n, cell = voxel2bbmodel.face_cells('east', box)
    assert (w, h, n) == (3, 1, (1, 0, 0)) and cell(0, 0) == (1, 0, 2) and cell(2, 0) == (1, 0, 0)  # u→-Z
    assert voxel2bbmodel.face_cells('west', box)[3](0, 0) == (0, 0, 0)                               # u→+Z
    assert voxel2bbmodel.face_cells('north', box)[3](0, 0) == (1, 0, 0)                              # u→-X
    assert voxel2bbmodel.face_cells('south', box)[3](0, 0) == (0, 0, 2)                              # u→+X
    assert voxel2bbmodel.face_cells('up', box)[3](1, 2) == (1, 0, 2)                                 # u→+X, v→+Z
    assert voxel2bbmodel.face_cells('down', box)[3](0, 0) == (0, 0, 2)                               # v→-Z


def test_hidden_faces_and_boxes_are_detected():
    grid = {(x, y, z) for x in range(3) for y in range(3) for z in range(3)}
    center = ((1, 1, 1), (2, 2, 2))
    assert not voxel2bbmodel.visible_box(center, grid)  # 完全に埋もれた箱は捨てられる
    corner = ((0, 0, 0), (1, 1, 1))
    exposed = [f for f in voxel2bbmodel.FACES if voxel2bbmodel.face_exposed(corner, f, grid)]
    assert sorted(exposed) == ['down', 'north', 'west']  # 角のセルは 3 面だけ露出


def test_pack_regions_do_not_overlap_and_fit():
    regions = [(5, 3), (1, 1), (7, 2), (4, 4), (3, 3), (1, 1)]
    size, pos = voxel2bbmodel.pack(regions)
    taken = set()
    for (w, h), (x, y) in zip(regions, pos):
        assert x + w <= size and y + h <= size
        cells = {(x + i, y + j) for i in range(w) for j in range(h)}
        assert not (cells & taken)
        taken |= cells


def test_build_cube_model_end_to_end_with_hidden_face_culling():
    try:
        import PIL  # noqa: F401
    except ImportError:
        return  # PNG の書き出しに Pillow が要る。無ければこのテストは省く
    import json
    import tempfile
    d = Path(tempfile.mkdtemp())
    dims = (6, 6, 6)
    # 上に穴のある殻（外とつながるので空洞は埋まらない）
    shell = {(x, y, z): 'minecraft:stone' for x in range(6) for y in range(6) for z in range(6)
             if (x in (0, 5) or y in (0, 5) or z in (0, 5)) and not (y == 5 and 2 <= x <= 3 and 2 <= z <= 3)}
    schem = d / 's.schem'
    obj2schem.write_schem(str(schem), dims, shell, 's')
    stats = voxel2bbmodel.build(str(schem), str(d), name='t', keep_front=True)
    legacy = voxel2bbmodel.build(str(schem), str(d / 'legacy'), name='t', keep_front=True, legacy=True)
    assert stats['cubes'] <= legacy['cubes']
    assert legacy['quads'] == 6 * legacy['cubes']    # legacy は全6面
    assert stats['quads'] < 6 * stats['cubes']       # 最適化版は見えない面を出さない
    # 独立に数えた「外に露出するボクセル面」の数。書いた面のピクセル数はこれ以上でなければ足りない
    exposed = sum(1 for (x, y, z) in shell for dx, dy, dz in voxel2bbmodel.N6
                  if (x + dx, y + dy, z + dz) not in shell)
    geo = json.loads((d / 't.geo.json').read_text(encoding='utf-8'))
    cubes = geo['minecraft:geometry'][0]['bones'][0]['cubes']
    assert len(cubes) == stats['cubes']
    for c in cubes:
        assert set(c['uv']) <= set(voxel2bbmodel.FACES) and c['uv']  # 書かれた面だけ（0 面の箱は無い）
        for f in ('up', 'down'):
            if f in c['uv']:
                assert c['uv'][f]['uv_size'][0] < 0 and c['uv'][f]['uv_size'][1] < 0  # 上下面は符号反転
    bb = json.loads((d / 't.bbmodel').read_text(encoding='utf-8'))
    disabled = [f for e in bb['elements'] for f in e['faces'].values() if f['texture'] is None]
    assert disabled  # 無効化した面は texture=null（Blockbench は描画も書き出しもしない）
    area = sum((f['uv'][2] - f['uv'][0]) * (f['uv'][3] - f['uv'][1]) for e in bb['elements']
               for f in e['faces'].values() if f['texture'] is not None)
    assert area >= exposed


# ---------------------------------------------------------------- 斜めの板（ハイブリッド）


def _zyx_matrix(deg):
    x, y, z = (math.radians(v) for v in deg)
    cx, cy, cz, sx, sy, sz = math.cos(x), math.cos(y), math.cos(z), math.sin(x), math.sin(y), math.sin(z)
    return [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
            [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
            [-sy, cy * sx, cy * cx]]


def test_euler_from_columns_rebuilds_the_frame():
    X = hybrid2bbmodel.norm([1.0, 0.4, -0.3])
    N = hybrid2bbmodel.norm(hybrid2bbmodel.cross([0.2, 0.1, 1.0], X))
    Z = hybrid2bbmodel.cross(X, N)
    m = _zyx_matrix(hybrid2bbmodel.euler_zyx_from_columns(X, N, Z))
    for r in range(3):
        for c, axis in enumerate((X, N, Z)):
            assert abs(m[r][c] - axis[r]) < 1e-9  # Blockbench の ZYX 回転で板の軸が元に戻る


def _ident(rgb):
    return tuple(int(c) for c in rgb)


def test_plate_for_square_is_flat_centered_and_fully_painted():
    sq = dict(pos=[(0, 0, 0), (32, 0, 0), (32, 0, 32), (0, 0, 32)], uv=None, tex=None)
    pl = hybrid2bbmodel.make_plate(sq, [], _ident, 16, 0.0, 1.0)
    assert (pl['pw'], pl['ph']) == (2, 2) and all(pl['pix'])              # 1ブロック=1ピクセル、全部塗る
    assert all(abs(a - b) < 1e-9 for a, b in zip(pl['C'], (16, 0, 16)))   # 中心
    assert abs(pl['frm'][1] - pl['to'][1]) < 1e-9                         # 厚み0
    assert abs(abs(pl['N'][1]) - 1) < 1e-9                                # 法線は面に垂直


def test_plate_coverage_threshold_controls_edge_pixels():
    # 辺がピクセルを斜めに切る不規則な三角形（直角二等辺だと辺がちょうど角を通り、しきい値で差が出ない）
    tri = dict(pos=[(0, 0, 0), (70, 0, 0), (13, 0, 47)], uv=None, tex=None)
    strict = hybrid2bbmodel.make_plate(tri, [], _ident, 16, 0.0, 1.0, coverage=0.5)
    loose = hybrid2bbmodel.make_plate(tri, [], _ident, 16, 0.0, 1.0, coverage=0.12)
    n_strict = sum(1 for p in strict['pix'] if p)
    n_loose = sum(1 for p in loose['pix'] if p)
    assert 0 < n_strict < n_loose < len(loose['pix'])  # 三角形の外は透明、しきい値を下げるほど縁まで塗る


# ---- rig: 補助の骨・伸び縮みする面の分割・継ぎ目の測定

def _translate(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def _rot_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def _area(P):
    a = [P[1][k] - P[0][k] for k in range(3)]
    b = [P[2][k] - P[0][k] for k in range(3)]
    c = hybrid2bbmodel.cross(a, b)
    return 0.5 * math.sqrt(hybrid2bbmodel.dot(c, c))


def test_blend_rotation_is_a_quaternion_average():
    R = hybrid2bbmodel._blend_rotation([(0.5, _rot_z(0)), (0.5, _rot_z(90))])
    assert abs(math.degrees(math.atan2(R[1][0], R[0][0])) - 45) < 1e-6
    # 符号違いのクォータニオン（同じ回転）を混ぜても潰れない
    R = hybrid2bbmodel._blend_rotation([(0.5, _rot_z(170)), (0.5, _rot_z(-170))])
    assert abs(abs(math.degrees(math.atan2(R[1][0], R[0][0]))) - 180) < 1e-6


def test_continuous_euler_has_no_jumps_through_a_full_turn():
    mats = [_rot_z(d) for d in range(0, 721, 10)]
    eu = hybrid2bbmodel._continuous_euler(mats)
    for a, b in zip(eu, eu[1:]):
        assert sum(abs(b[k] - a[k]) for k in range(3)) < 11  # 1 コマ 10° 回すだけで、±180/360 の飛びがない
    assert abs(eu[-1][2] - 720) < 1e-6


def test_subdivide_for_skin_splits_only_where_weights_change():
    # 骨1 は骨0 に対して 10 ブロック動く。重みが一様な面は切らず、重みが変わる面は見積もりが予算以下になるまで切る
    Ds = [[_translate(0, 0, 0), _translate(10, 0, 0)]]
    tri = [(0, 0, 0), (16, 0, 0), (0, 0, 16)]
    flat = dict(part='skirt', pos=tri, uv=None, tex=None, vw=[{0: 1.0}] * 3, wts={0: 1.0}, bone=0)
    ramp = dict(part='skirt', pos=tri, uv=[(0, 0), (1, 0), (0, 1)], tex=None,
                vw=[{0: 1.0}, {1: 1.0}, {0: 1.0}], wts={0: 2 / 3, 1: 1 / 3}, bone=0)
    other = dict(part='head', pos=tri, uv=None, tex=None, vw=[{0: 1.0}, {1: 1.0}, {0: 1.0}], wts={0: 1.0}, bone=0)
    out = hybrid2bbmodel.subdivide_for_skin([flat, ramp, other], Ds, 1.0, 2.0, lambda q: q['part'] == 'skirt')
    flats = [q for q in out if q['vw'] == [{0: 1.0}] * 3 and q['part'] == 'skirt']
    ramps = [q for q in out if q['part'] == 'skirt' and q not in flats]
    assert len(flats) == 1 and flats[0]['pos'] == tri          # 一様な面はそのまま
    assert [q for q in out if q['part'] == 'head'] == [other]  # 対象外のパーツもそのまま
    assert len(ramps) > 4                                       # 伸びる面は切られた
    assert abs(sum(_area(q['pos']) for q in ramps) - _area(tri)) < 1e-6  # 隙間も重なりもなく元の面を覆う
    for q in ramps:
        w1 = [v.get(1, 0.0) for v in q['vw']]
        # 見積もり = 頂点の重みと重心の重みの差 × 骨どうしの動きの差(10) が予算 2 以下（または辺が 1 ブロック以下）
        assert max(abs(w - sum(w1) / 3) for w in w1) * 10 <= 2.0 + 1e-9 or \
            max(math.dist(q['pos'][i], q['pos'][(i + 1) % 3]) for i in range(3)) <= 1.0
        assert abs(q['wts'][1] - sum(w1) / 3) < 1e-9 and q['bone'] == max(q['wts'], key=q['wts'].get)
        # UV も位置と同じ比率で補間されている（この面では u = x/16, v = z/16）
        for p, uv in zip(q['pos'], q['uv']):
            assert abs(uv[0] - p[0] / 16) < 1e-9 and abs(uv[1] - p[2] / 16) < 1e-9


def test_expand_triangle_moves_every_edge_out_by_the_margin_and_keeps_uv_affine():
    P = [(0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (0.0, 0.0, 8.0)]   # 3-4-5 の倍、内接円の半径 2
    UV = [(0.0, 0.0), (0.6, 0.0), (0.0, 0.8)]                 # u = x/10, v = z/10
    P2, UV2 = hybrid2bbmodel.expand_triangle(P, UV, 0.5)

    def dist_to_line(p, a, b):
        ab = [b[k] - a[k] for k in range(3)]
        ap = [p[k] - a[k] for k in range(3)]
        c = hybrid2bbmodel.cross(ab, ap)
        return math.sqrt(hybrid2bbmodel.dot(c, c)) / math.dist(a, b)
    inc = (2.0, 0.0, 2.0)
    for i in range(3):  # 内心から各辺までの距離が 2 → 2.5
        assert abs(dist_to_line(inc, P2[i], P2[(i + 1) % 3]) - 2.5) < 1e-9
    for p, uv in zip(P2, UV2):  # UV は位置と同じ一次の関係のまま（絵がそのまま外へ続く）
        assert abs(uv[0] - p[0] / 10) < 1e-9 and abs(uv[1] - p[2] / 10) < 1e-9
    # 細すぎる三角形でも広げすぎない（上限 2 倍）
    thin = [(0.0, 0.0, 0.0), (100.0, 0.0, 0.0), (50.0, 0.0, 0.01)]
    T2, _ = hybrid2bbmodel.expand_triangle(thin, None, 0.5)
    assert math.dist(T2[0], T2[1]) <= 2 * 100 + 1e-6


def test_seam_report_is_zero_when_neighbours_share_a_bone_and_opens_when_they_do_not():
    Ds = [[_translate(0, 0, 0), _translate(3, 0, 0)]]
    a = dict(pos=[(0, 0, 0), (4, 0, 0), (0, 0, 4)], vw=[{0: 1.0}] * 3, key=0)
    b = dict(pos=[(4, 0, 0), (4, 0, 4), (0, 0, 4)], vw=[{0: 1.0}] * 3, key=0)
    assert hybrid2bbmodel.seam_report([a, b], Ds, 1.0, 2, [])['max'] == 0
    # 元のスキニングでも動く頂点（重みが同じ）だけを数える。片方を別の骨に乗せると、共有頂点が 3 ブロック離れる
    b2 = dict(b, key=1)
    rep = hybrid2bbmodel.seam_report([a, b2], Ds, 1.0, 2, [])
    assert rep['samples'] == 2 and abs(rep['max'] - 3) < 1e-9
    # 重みが半々の補助の骨（平行移動だけなので M·c - c = 1.5）なら、半分の 1.5 ブロック
    hp = dict(wts={0: 0.5, 1: 0.5}, pts=list(b['pos']))
    rep = hybrid2bbmodel.seam_report([a, dict(b, key=2)], Ds, 1.0, 2, [hp])
    assert abs(rep['max'] - 1.5) < 1e-9


if __name__ == '__main__':  # pytest なしでも直接実行できる
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            try:
                fn()
                print('PASS', name)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print('FAIL', name, repr(e))
    sys.exit(1 if failed else 0)
