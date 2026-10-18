"""Authored binary32 geometry predicate, NOT a decoder/native execution oracle.

Source: NATIVE-GEOMETRY-CLASSIFIER-PREDICATE-2026-10-18.md and its static
0x376c4a..0x3774b8 evidence. Inputs are six authored records, not packed assets.
Only RN-ties-even, FTZ=False, DAZ=False and nontrapping value semantics are
supported. The target's ambient MXCSR and resolved acosf are UNKNOWN. Quiet
NaNs are supported by category; payload/sign selection, SNaNs, exception flags,
traps and errno are NOT modeled. No claim of bit-exact target equivalence.

Finite add/sub/mul/div/sqrt round separately to binary32 with gradual underflow.
An injected provider supplies an already-binary32 acos result, with mandatory
provenance. The optional Python math.acos provider is comparison-only.
Output is the eventual low byte at frame+c, not a function return or a complete
native dword. Provisional EAX stores have unspecified upper bits.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import struct
from typing import Callable


def binary32_from_bits(bits: int) -> float:
    """Construct an authored binary32 value; reject signaling NaN encodings."""
    if type(bits) is not int or not 0 <= bits <= 0xffffffff:
        raise ValueError('bits must be an unsigned 32-bit integer')
    if bits & 0x7f800000 == 0x7f800000 and bits & 0x007fffff and not bits & 0x00400000:
        raise ValueError('signaling NaNs are outside the reference scope')
    return struct.unpack('<f', struct.pack('<I', bits))[0]


def _check_float(value: float) -> None:
    if type(value) is not float:
        raise TypeError('components and provider results must be Python floats representing binary32')
    bits = struct.unpack('<Q', struct.pack('<d', value))[0]
    if math.isnan(value):
        if not bits & (1 << 51):
            raise ValueError('signaling NaNs are outside the reference scope')
        return
    try:
        rounded = struct.unpack('<f', struct.pack('<f', value))[0]
    except OverflowError as error:
        raise ValueError('value is not binary32; round authored inputs explicitly') from error
    if rounded != value:
        raise ValueError('value is not binary32; round authored inputs explicitly')


@dataclass(frozen=True)
class Triple:
    x: float
    y: float
    z: float

    def __post_init__(self):
        for value in (self.x, self.y, self.z):
            _check_float(value)

    def values(self) -> tuple[float, float, float]:
        return self.x, self.y, self.z


@dataclass(frozen=True)
class Record:
    points: tuple[Triple, Triple, Triple, Triple]
    reference: Triple

    def __post_init__(self):
        if type(self.points) is not tuple or len(self.points) != 4:
            raise ValueError('a record requires an immutable tuple of four authored triples')
        if any(type(p) is not Triple for p in self.points) or type(self.reference) is not Triple:
            raise TypeError('record components must be authored Triple instances')


@dataclass(frozen=True)
class FloatScope:
    rounding: str = 'nearest-even'
    ftz: bool = False
    daz: bool = False

    def __post_init__(self):
        if self.rounding != 'nearest-even' or self.ftz is not False or self.daz is not False:
            raise ValueError('only nearest-even, FTZ=False, DAZ=False are supported')


@dataclass(frozen=True)
class AcosProvider:
    evaluate: Callable[[float], float]
    provenance: str

    def __post_init__(self):
        if not callable(self.evaluate) or type(self.provenance) is not str or not self.provenance.strip():
            raise ValueError('acos requires a callable and nonempty provenance')


@dataclass(frozen=True)
class Operation:
    label: str
    kind: str
    operands: tuple[float, ...]
    result: float


@dataclass(frozen=True)
class RecordTrace:
    index: int
    direction: Triple
    radius: float
    skipped: bool
    quotient: float | None = None
    clamped: float | None = None
    angle: float | None = None
    degrees: float | None = None
    accepted: bool = False


@dataclass(frozen=True)
class Result:
    low_byte: int
    reason: str
    acos_provenance: str
    scope: FloatScope
    means: tuple[Triple, ...] = ()
    centroid: Triple | None = None
    tests: tuple[RecordTrace, ...] = ()
    operations: tuple[Operation, ...] = ()


EPSILON = binary32_from_bits(0x358637bd)
PI_F = binary32_from_bits(0x40490fdb)


def _round(value: Fraction, negative_zero: bool = False) -> float:
    """Exact rational -> binary32 RN-even; private to this arithmetic recipe."""
    if not value:
        return -0.0 if negative_zero else 0.0
    negative = value < 0
    value = abs(value)
    n, d = value.numerator, value.denominator
    exponent = n.bit_length() - d.bit_length()
    if (n < d << exponent) if exponent >= 0 else (n << -exponent < d):
        exponent -= 1
    step = max(exponent - 23, -149)
    if step >= 0:
        d <<= step
    else:
        n <<= -step
    q, remainder = divmod(n, d)
    if 2 * remainder > d or (2 * remainder == d and q & 1):
        q += 1
    result = math.ldexp(float(q), step)
    if result >= 2.0 ** 128:
        result = math.inf
    return -result if negative else result


def _sqrt(value: float) -> float:
    if math.isnan(value) or value < 0:
        return math.nan
    if not value or math.isinf(value):
        return value
    # Locate adjacent binary32 roots by exact squared comparisons. The midpoint
    # comparison below avoids relying on host sqrt/double-rounding behavior.
    target = Fraction(value)
    low, high = 0, 0x7f7fffff
    while low < high:
        mid = (low + high + 1) // 2
        x = Fraction(binary32_from_bits(mid))
        if x * x <= target:
            low = mid
        else:
            high = mid - 1
    a, b = binary32_from_bits(low), binary32_from_bits(low + 1)
    midpoint = (Fraction(a) + Fraction(b)) / 2
    square = midpoint * midpoint
    return b if target > square or (target == square and low & 1) else a


def _arithmetic(kind: str, a: float, b: float = 0.) -> float:
    if kind == 'sqrt':
        return _sqrt(a)
    if kind == 'max':
        return a if a > b else b  # source on equal or unordered
    if kind == 'min':
        return a if a < b else b  # source on equal or unordered
    if kind == 'sub':
        return _arithmetic('add', a, -b)
    if kind == 'add':
        if not math.isfinite(a) or not math.isfinite(b):
            return a + b
        return _round(Fraction(a) + Fraction(b), a == 0. and b == 0. and
                      math.copysign(1., a) < 0 and math.copysign(1., b) < 0)
    if kind == 'mul':
        if not math.isfinite(a) or not math.isfinite(b):
            return a * b
        return _round(Fraction(a) * Fraction(b), math.copysign(1., a) != math.copysign(1., b))
    if kind == 'div':
        if math.isnan(a) or math.isnan(b) or (a == 0. and b == 0.) or (math.isinf(a) and math.isinf(b)):
            return math.nan
        negative = math.copysign(1., a) != math.copysign(1., b)
        if b == 0. or math.isinf(a):
            return -math.inf if negative else math.inf
        if math.isinf(b):
            return -0. if negative else 0.
        return _round(Fraction(a) / Fraction(b), negative)
    raise ValueError('unsupported operation')


def comparison_acos_provider() -> AcosProvider:
    """Host binary64 math.acos then RN-even binary32: NOT target acosf."""
    def evaluate(x: float) -> float:
        value = math.acos(x)
        return value if math.isnan(value) else _round(Fraction(value))
    return AcosProvider(evaluate, 'comparison-only: Python math.acos binary64 then binary32 RN-even; not target acosf')


def classify(records: tuple[Record, ...] | None, *, span_bytes: int,
             acos: AcosProvider | None, scope: FloatScope = FloatScope()) -> Result:
    """Apply the authored recipe. Rejected spans never inspect records/provider.

    Accepted spans require exactly six immutable authored records. span_bytes is
    a declared source span, not a pointer/allocation validation or binary parser.
    Provider exceptions propagate; arbitrary provider results are not repaired.
    """
    if type(span_bytes) is not int:
        raise TypeError('span_bytes must be an integer')
    if type(scope) is not FloatScope:
        raise TypeError('scope must be FloatScope')
    if span_bytes != 0x480:
        return Result(0, 'span-rejected', 'not consulted: span rejected', scope)
    if type(records) is not tuple or len(records) != 6 or any(type(r) is not Record for r in records):
        raise ValueError('accepted span requires exactly six authored Record instances in a tuple')
    if type(acos) is not AcosProvider:
        raise ValueError('accepted span requires an explicit AcosProvider')
    operations: list[Operation] = []
    def op(label, kind, *args):
        result = _arithmetic(kind, *args)
        operations.append(Operation(label, kind, args, result))
        return result
    means = []
    for i, record in enumerate(records):
        components = []
        for k, axis in enumerate('xyz'):
            label = f'mean.{i}.{axis}'
            s = op(label + '.add0', 'add', record.points[0].values()[k], 0.)
            for j in range(1, 4):
                p = record.points[j].values()[k]
                args = (p, s) if i > 0 and k < 2 else (s, p)
                s = op(label + f'.add{j}', 'add', *args)
            components.append(op(label + '.scale', 'mul', s, 0.25))
        means.append(Triple(*components))
    components = []
    for k, axis in enumerate('xyz'):
        s = op(f'centroid.{axis}.add0', 'add', means[0].values()[k], 0.)
        for i in range(1, 6):
            s = op(f'centroid.{axis}.add{i}', 'add', s, means[i].values()[k])
        components.append(op(f'centroid.{axis}.divide', 'div', s, 6.))
    centroid = Triple(*components)
    tests = []
    for i, record in enumerate(records):
        prefix = f'test.{i}'
        direction = Triple(*(op(f'{prefix}.direction.{axis}', 'sub', means[i].values()[k], centroid.values()[k])
                             for k, axis in enumerate('xyz')))
        xx = op(prefix + '.square.x', 'mul', direction.x, direction.x)
        yy = op(prefix + '.square.y', 'mul', direction.y, direction.y)
        xy = op(prefix + '.square.xy', 'add', xx, yy)
        zz = op(prefix + '.square.z', 'mul', direction.z, direction.z)
        total = op(prefix + '.square.total', 'add', zz, xy)
        radius = op(prefix + '.radius', 'sqrt', total)
        if EPSILON >= radius:  # ordered: a quiet NaN must NOT skip
            tests.append(RecordTrace(i, direction, radius, True))
            continue
        xn = op(prefix + '.dot.x', 'mul', direction.x, record.reference.x)
        yn = op(prefix + '.dot.y', 'mul', direction.y, record.reference.y)
        xy = op(prefix + '.dot.xy', 'add', xn, yn)
        zn = op(prefix + '.dot.z', 'mul', direction.z, record.reference.z)
        dot = op(prefix + '.dot.total', 'add', zn, xy)
        quotient = op(prefix + '.quotient', 'div', dot, radius)
        lo = op(prefix + '.lower', 'max', -1., quotient)
        clamped = op(prefix + '.upper', 'min', 1., lo)
        angle = acos.evaluate(clamped)
        _check_float(angle)
        operations.append(Operation(prefix + '.acos', 'provider', (clamped,), angle))
        scaled = op(prefix + '.degrees.scale', 'mul', angle, 180.)
        degrees = op(prefix + '.degrees.divide', 'div', scaled, PI_F)
        accepted = degrees > 90.  # ordered: equality and quiet NaNs fail
        tests.append(RecordTrace(i, direction, radius, False, quotient, clamped, angle, degrees, accepted))
        if accepted:
            return Result(1, 'ordered-angle-pass', acos.provenance, scope, tuple(means), centroid,
                          tuple(tests), tuple(operations))
    return Result(0, 'no-ordered-angle-pass', acos.provenance, scope, tuple(means), centroid,
                  tuple(tests), tuple(operations))
