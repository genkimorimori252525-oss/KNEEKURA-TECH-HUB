"""Authored fixtures only; no model files, original execution or libm oracle."""
import importlib.util
import math
import struct
import unittest

MODULE = 'native_geometry_classifier_reference_ysm_265'
if importlib.util.find_spec(MODULE):
    import native_geometry_classifier_reference_ysm_265 as ref
else:
    ref = None


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


class GeometryReferenceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ref, 'authored classifier reference must exist')

    def records(self, centers=None, references=None):
        centers = centers or [(1., 0., 0.), (-1., 0., 0.)] * 3
        references = references or [(0., 0., 0.)] * 6
        return tuple(ref.Record((ref.Triple(*p),) * 4, ref.Triple(*n))
                     for p, n in zip(centers, references))

    def run_reference(self, records, provider=None):
        return ref.classify(records, span_bytes=0x480,
                            acos=provider or ref.comparison_acos_provider())

    def test_span_rejection_does_not_inspect_records_or_call_provider(self):
        result = ref.classify(None, span_bytes=0, acos=None)
        self.assertEqual(result.low_byte, 0)
        self.assertEqual(result.reason, 'span-rejected')
        self.assertEqual(result.operations, ())

    def test_short_and_exact_epsilon_directions_skip(self):
        e = ref.EPSILON
        centers = [(e, 0., 0.), (-e, 0., 0.), (0., 0., 0.)] * 2
        result = self.run_reference(self.records(centers))
        self.assertEqual(result.low_byte, 0)
        self.assertTrue(all(row.skipped for row in result.tests))
        self.assertEqual(result.tests[0].radius, e)

    def test_all_six_equal_90_fail(self):
        result = self.run_reference(self.records())
        self.assertEqual(result.low_byte, 0)
        self.assertEqual(len(result.tests), 6)
        self.assertTrue(all(row.degrees == 90. for row in result.tests))

    def test_first_ordered_pass_stops(self):
        ns = [(0., 0., 0.), (1., 0., 0.)] + [(0., 0., 0.)] * 4
        result = self.run_reference(self.records(references=ns))
        self.assertEqual(result.low_byte, 1)
        self.assertEqual(len(result.tests), 2)
        self.assertTrue(result.tests[-1].accepted)
        self.assertEqual(result.tests[-1].degrees, 180.)

    def test_nonunit_reference_is_not_normalized_and_clamps(self):
        ns = [(0.5, 100., 0.)] + [(0., 0., 0.)] * 5
        result = self.run_reference(self.records(references=ns))
        self.assertEqual(result.tests[0].quotient, 0.5)
        ns[0] = (2., 100., 0.)
        result = self.run_reference(self.records(references=ns))
        self.assertEqual(result.tests[0].clamped, 1.)

    def test_nan_radius_proceeds_and_nan_angle_fails_ordered_test(self):
        centers = [(math.nan, 0., 0.)] + [(0., 0., 0.)] * 5
        result = self.run_reference(self.records(centers))
        self.assertEqual(len(result.tests), 6)
        self.assertTrue(all(not row.skipped for row in result.tests))
        self.assertTrue(all(math.isnan(row.clamped) for row in result.tests))
        self.assertEqual(result.low_byte, 0)

    def test_nan_reference_is_not_clamped_to_finite_endpoint(self):
        ns = [(math.nan, 0., 0.)] + [(0., 0., 0.)] * 5
        result = self.run_reference(self.records(references=ns))
        self.assertTrue(math.isnan(result.tests[0].clamped))
        self.assertEqual(result.low_byte, 0)

    def test_provider_is_explicit_and_validated(self):
        with self.assertRaises(ValueError):
            ref.classify(self.records(), span_bytes=0x480, acos=None)
        with self.assertRaises(ValueError):
            ref.AcosProvider(lambda x: x, '')
        with self.assertRaises(ValueError):
            self.run_reference(self.records(), ref.AcosProvider(lambda x: 0.1, 'non-f32'))
        with self.assertRaises(TypeError):
            self.run_reference(self.records(), ref.AcosProvider(lambda x: 0, 'not-float'))
        result = self.run_reference(self.records(), ref.AcosProvider(lambda x: math.nan, 'authored qNaN'))
        self.assertEqual(result.low_byte, 0)
        self.assertEqual(result.acos_provenance, 'authored qNaN')
        def failure(x):
            raise RuntimeError('provider failed')
        with self.assertRaisesRegex(RuntimeError, 'provider failed'):
            self.run_reference(self.records(), ref.AcosProvider(failure, 'authored exception'))

    def test_separate_rounding_and_record_addition_operand_order(self):
        records = list(self.records())
        points = tuple(ref.Triple(x, 0., 0.) for x in (16777216., 1., -16777216., 4.))
        records[0] = ref.Record(points, ref.Triple(0., 0., 0.))
        records[1] = records[0]
        result = self.run_reference(tuple(records))
        self.assertEqual(result.means[0].x, 1.)  # exact-sum/reassociation would give 1.25
        ops = {op.label: op for op in result.operations}
        self.assertEqual(ops['mean.0.x.add1'].operands, (16777216., 1.))
        self.assertEqual(ops['mean.1.x.add1'].operands, (1., 16777216.))

    def test_norm_and_dot_z_multiply_follow_xy_add(self):
        result = self.run_reference(self.records())
        labels = [op.label for op in result.operations]
        self.assertLess(labels.index('test.0.square.xy'), labels.index('test.0.square.z'))
        self.assertLess(labels.index('test.0.dot.xy'), labels.index('test.0.dot.z'))

    def test_binary32_ties_underflow_overflow_and_sqrt_edges(self):
        a = ref._arithmetic
        half_ulp = 2. ** -24
        self.assertEqual(a('add', 1., half_ulp), 1.)
        odd = ref.binary32_from_bits(0x3f800001)
        even = ref.binary32_from_bits(0x3f800002)
        self.assertEqual(a('add', odd, half_ulp), even)
        self.assertEqual(a('add', -odd, -half_ulp), -even)
        tiny = ref.binary32_from_bits(1)
        self.assertEqual(a('div', tiny, 2.), 0.)
        self.assertEqual(a('mul', 3. * tiny, 0.5), 2. * tiny)
        self.assertEqual(math.copysign(1., a('div', -tiny, 2.)), -1.)
        maximum = ref.binary32_from_bits(0x7f7fffff)
        self.assertEqual(a('mul', maximum, 2.), math.inf)
        self.assertEqual(a('add', maximum, 2. ** 102), maximum)
        self.assertEqual(a('add', maximum, 2. ** 103), math.inf)
        self.assertEqual(a('sqrt', 2.), ref.binary32_from_bits(0x3fb504f3))
        self.assertEqual(a('sqrt', 4.), 2.)
        self.assertEqual(a('sqrt', 2. ** -148), 2. ** -74)
        self.assertEqual(math.copysign(1., a('sqrt', -0.)), -1.)
        self.assertTrue(math.isnan(a('sqrt', -1.)))
        self.assertTrue(math.isnan(a('mul', math.inf, 0.)))
        self.assertTrue(math.isnan(a('div', math.inf, math.inf)))
        self.assertEqual(a('div', 1., -0.), -math.inf)
        self.assertEqual(math.copysign(1., a('div', 1., -math.inf)), -1.)

    def test_unsupported_inputs_and_settings_rejected(self):
        with self.assertRaises(ValueError):
            ref.Triple(0.1, 0., 0.)
        with self.assertRaises(TypeError):
            ref.Triple(True, 0., 0.)
        with self.assertRaises(ValueError):
            ref.binary32_from_bits(0x7f800001)
        for kwargs in ({'rounding': 'toward-zero'}, {'ftz': True}, {'daz': True}):
            with self.assertRaises(ValueError):
                ref.FloatScope(**kwargs)
        with self.assertRaises(ValueError):
            self.run_reference(self.records()[:5])
        with self.assertRaises(TypeError):
            ref.classify(None, span_bytes=True, acos=None)

    def test_underflow_rounding_and_signed_zero_are_explicit(self):
        tiny = ref.binary32_from_bits(1)
        records = self.records([(tiny, -0., 0.)] * 6)
        result = self.run_reference(records)
        self.assertEqual(result.means[0].x, tiny)
        self.assertEqual(math.copysign(1., result.means[0].y), 1.)
        self.assertEqual(result.low_byte, 0)


if __name__ == '__main__':
    unittest.main()
