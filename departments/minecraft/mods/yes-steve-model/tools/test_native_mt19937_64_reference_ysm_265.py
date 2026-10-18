"""Offline tests: one pinned GCC numerical oracle; other cases are synthetic."""
import unittest
from native_mt19937_64_reference_ysm_265 import MT19937_64, ByteStream, MASK


class ReferenceTests(unittest.TestCase):
    def test_official_gcc_10000th_output(self):
        # Official GCC commit 2ee5e4300186a92ad73f1a1a64cb918dc76c8d67,
        # libstdc++-v3/testsuite/26_numerics/random/mt19937_64.cc.
        # Retrieved source SHA256 (source retained externally, never executed):
        # 0b5bacbeb73374322a84f7c15ce3c1df557c816154b7baf7f4fc43edf674183e
        self.assertEqual(MT19937_64().words(10000)[-1], 9981545732273789042)

    def test_seed_recurrence_invariant(self):
        for seed in [0, 1, 5489, MASK, 0x0123456789ABCDEF]:
            e = MT19937_64(seed)
            self.assertEqual(len(e.state), 312)
            self.assertEqual(e.index, 312)
            self.assertEqual(e.state[0], seed)
            for i in range(1, 312):
                x = e.state[i - 1]
                self.assertEqual(e.state[i], (0x5851F42D4C957F2D * (x ^ (x >> 62)) + i) & MASK)

    def test_word_index_wrap(self):
        e = MT19937_64(7)
        e.words(311)
        self.assertEqual(e.index, 311)
        e.next_u64()
        self.assertEqual(e.index, 312)
        e.next_u64()
        self.assertEqual(e.index, 1)
        e.words(312)
        self.assertEqual(e.index, 1)

    def test_authored_fixed_word_byte_order_and_cache(self):
        class FixedWords:
            def __init__(self):
                self.calls = 0
            def next_u64(self):
                values = [0x0706050403020100, 0x0F0E0D0C0B0A0908]
                result = values[self.calls]
                self.calls += 1
                return result
        s = ByteStream(0)
        s.engine = FixedWords()
        self.assertEqual(s.read(0), b'')
        self.assertEqual(s.engine.calls, 0)
        self.assertEqual(s.read(3), bytes([0, 1, 2]))
        self.assertEqual(s.pending, bytes([3, 4, 5, 6, 7]))
        self.assertEqual(s.read(6), bytes([3, 4, 5, 6, 7, 8]))
        self.assertEqual(s.engine.calls, 2)
        self.assertEqual(s.read(7), bytes(range(9, 16)))
        self.assertEqual(s.pending, b'')

    def test_all_short_split_positions(self):
        for seed in [0, 5489, MASK]:
            for length in range(33):
                expected = ByteStream(seed).read(length)
                for cut in range(length + 1):
                    s = ByteStream(seed)
                    self.assertEqual(s.read(cut) + s.read(0) + s.read(length - cut), expected)

    def test_long_splits_and_generator_refresh_boundaries(self):
        length = 5011  # crosses two 312-word refresh blocks, plus a tail
        for seed in [0, 1, 5489, MASK]:
            expected = ByteStream(seed).read(length)
            words = MT19937_64(seed).words((length + 7) // 8)
            self.assertEqual(expected, b''.join(w.to_bytes(8, 'little') for w in words)[:length])
            for cut in [0, 1, 7, 8, 9, 2495, 2496, 2497, 4991, 4992, 4993, length]:
                s = ByteStream(seed)
                self.assertEqual(s.read(cut) + s.read(length - cut), expected)
            for chunk in [1, 2, 3, 7, 8, 9, 31, 312, 2496]:
                s = ByteStream(seed)
                self.assertEqual(b''.join(s.read(min(chunk, length - i))
                                         for i in range(0, length, chunk)), expected)

    def test_fresh_stream_xor_reapplication(self):
        for seed in [0, 5489, MASK]:
            for length in [0, 1, 2, 7, 8, 9, 15, 16, 17, 2495, 2496, 2497, 5011]:
                authored = bytes((37 * i + 19) & 255 for i in range(length))
                changed = ByteStream(seed).xor(authored)
                self.assertEqual(ByteStream(seed).xor(changed), authored)

    def test_intervening_mutation_delta_survives(self):
        authored = bytes(range(32))
        changed = bytearray(ByteStream(13).xor(authored))
        changed[17] ^= 0x80
        expected = bytearray(authored)
        expected[17] ^= 0x80
        self.assertEqual(ByteStream(13).xor(bytes(changed)), bytes(expected))

    def test_advanced_stream_is_not_a_reset(self):
        authored = b'authored numerical test payload'
        s = ByteStream(5489)
        changed = s.xor(authored)
        self.assertNotEqual(s.xor(changed), authored)  # this synthetic example only
        self.assertEqual(ByteStream(5489).xor(changed), authored)

    def test_zero_and_invalid_inputs(self):
        e = MT19937_64(0)
        before = e.state.copy(), e.index
        self.assertEqual(e.words(0), [])
        self.assertEqual((e.state, e.index), before)
        for invalid in [-1, 1 << 64, True, 0.5, '1']:
            with self.assertRaises(ValueError):
                MT19937_64(invalid)
        for invalid in [-1, True, 0.5, '1']:
            with self.assertRaises(ValueError):
                ByteStream(0).read(invalid)
        with self.assertRaises(TypeError):
            ByteStream(0).xor(bytearray(1))


if __name__ == '__main__':
    unittest.main(verbosity=2)
