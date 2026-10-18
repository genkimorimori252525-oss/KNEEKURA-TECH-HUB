"""Authored numerical MT19937-64 reference and little-endian XOR byte stream.

Standard-library Python only. No target loading, original assets, seed-mixer,
image decoding, JNI, GL, or filesystem input. Not a native execution oracle.
"""
MASK = (1 << 64) - 1
N, M = 312, 156
A = 0xB5026F5AA96619E9
UPPER, LOWER = 0xFFFFFFFF80000000, 0x7FFFFFFF
F = 6364136223846793005


def _count(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError('count must be a nonnegative integer')
    return value


class MT19937_64:
    """Integer-seeded 64-bit reference; default seed is the standard's 5489.

    The target uses its own seed derivation, which is deliberately absent here.
    Seeds must be explicit unsigned 64-bit integers (no silent input wrapping).
    """
    def __init__(self, seed=5489):
        if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= MASK:
            raise ValueError('seed must be an unsigned 64-bit integer')
        self.state = [seed]
        for i in range(1, N):
            previous = self.state[-1]
            self.state.append((F * (previous ^ (previous >> 62)) + i) & MASK)
        self.index = N

    def _refresh(self):
        # Ascending in-place updates intentionally use already-refreshed wrapped
        # words in the second half, including word zero in the final update.
        for i in range(N):
            joined = (self.state[i] & UPPER) | (self.state[(i + 1) % N] & LOWER)
            self.state[i] = self.state[(i + M) % N] ^ (joined >> 1) ^ (A if joined & 1 else 0)
        self.index = 0

    def next_u64(self):
        if self.index == N:
            self._refresh()
        x = self.state[self.index]
        self.index += 1
        x ^= (x >> 29) & 0x5555555555555555
        x ^= (x << 17) & 0x71D67FFFEDA60000
        x ^= (x << 37) & 0xFFF7EEE000000000
        x ^= x >> 43
        return x & MASK

    def words(self, count):
        return [self.next_u64() for _ in range(_count(count))]


class ByteStream:
    """Consume low-to-high bytes of each generated word, retaining split tails.

    Reapplication needs a fresh instance with the same seed. Reusing an advanced
    stream does not rewind it. This models numerical byte order and cursor only.
    """
    def __init__(self, seed=5489):
        self.engine = MT19937_64(seed)
        self.pending = b''

    def read(self, count):
        count = _count(count)
        chunks = []
        while count:
            if not self.pending:
                self.pending = self.engine.next_u64().to_bytes(8, 'little')
            take = min(count, len(self.pending))
            chunks.append(self.pending[:take])
            self.pending = self.pending[take:]
            count -= take
        return b''.join(chunks)

    def xor(self, data):
        if not isinstance(data, bytes):
            raise TypeError('data must be bytes')
        return bytes(a ^ b for a, b in zip(data, self.read(len(data))))


if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=lambda s: int(s, 0), default=5489)
    parser.add_argument('--words', type=int, default=4)
    args = parser.parse_args()
    if not 0 <= args.words <= 10000:
        parser.error('--words must be between 0 and 10000')
    print(json.dumps({'seed': args.seed, 'words': MT19937_64(args.seed).words(args.words),
                      'kind': 'authored numerical reference, not target execution'}))
