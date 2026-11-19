import struct

def decompress(d):
    if d[:8] != b'CRILAYLA':
        return d
    usize, hoff = struct.unpack('<II', d[8:16])
    out = bytearray(usize + 0x100)
    out[0:0x100] = d[len(d)-0x100:]
    src = len(d) - 0x100 - 1
    state = {'src': src, 'pool': 0, 'left': 0}

    def bits(n):
        v = 0
        pool, left, s = state['pool'], state['left'], state['src']
        while n > 0:
            if left == 0:
                pool = d[s]; s -= 1; left = 8
            take = min(left, n)
            v = (v << take) | ((pool >> (left - take)) & ((1 << take) - 1))
            left -= take; n -= take
        state['pool'], state['left'], state['src'] = pool, left, s
        return v

    dst = usize + 0x100 - 1
    while dst >= 0x100:
        if bits(1):
            off = bits(13) + 3
            ln = 3
            for lvl in (2, 3, 5):
                v = bits(lvl); ln += v
                if v != (1 << lvl) - 1: break
            else:
                while True:
                    v = bits(8); ln += v
                    if v != 255: break
            for _ in range(ln):
                if dst < 0x100: break
                out[dst] = out[dst + off]; dst -= 1
        else:
            out[dst] = bits(8); dst -= 1
    return bytes(out)
