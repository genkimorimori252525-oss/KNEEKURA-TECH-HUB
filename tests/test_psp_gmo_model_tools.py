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
