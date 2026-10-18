# Authored geometry predicate reference

This reusable Python reference accepts authored mathematical records. It does not parse original model assets, execute original code, or assign a visual meaning to the classification byte.

From the repository root:

```sh
cd departments/minecraft/mods/yes-steve-model/tools
python -m unittest test_native_geometry_classifier_reference_ysm_265 -v
python -c 'import native_geometry_classifier_reference_ysm_265'
```

## Minimal authored example

Run from the tools directory above. All inputs below are newly authored numbers, not recovered model data.

```python
from native_geometry_classifier_reference_ysm_265 import (
    Triple, Record, classify, comparison_acos_provider,
)

centers = (1.0, -1.0, 1.0, -1.0, 1.0, -1.0)
records = tuple(
    Record(
        points=(Triple(x, 0.0, 0.0),) * 4,
        reference=Triple(-1.0, 0.0, 0.0),
    )
    for x in centers
)
result = classify(
    records, span_bytes=0x480, acos=comparison_acos_provider(),
)
assert result.low_byte == 1
assert result.tests[0].degrees == 180.0
print(result.low_byte, result.reason)
print(result.acos_provenance)
```

Expected first line: `1 ordered-angle-pass`. The provenance explicitly identifies Python math.acos as comparison-only. `means`, `centroid`, `tests`, and `operations` expose the arithmetic/branch trace. The trace preserves scalar arithmetic dependencies and operand order, not native instruction timing or the scheduling of independent packed lanes.

## Numerical and provider boundary

- Only round-to-nearest, ties-to-even, FTZ=False and DAZ=False, with nontrapping value semantics, are supported. Unsupported FloatScope settings are rejected. Actual target MXCSR is unknown.
- Finite add/subtract/multiply/divide operations use exact rational results and separate binary32 rounding. Square root uses exact squared midpoint comparisons. There is no reassociation or fused multiply-add.
- Triple components and provider results must be Python floats already exactly representable as binary32, or infinities/quiet NaNs. Non-binary32 values such as 0.1 are rejected; author rounding explicitly if needed. `binary32_from_bits` accepts explicit binary32 encodings but rejects signaling NaNs.
- Quiet NaNs are handled by category. NaN payload/sign propagation, signaling-NaN behavior, exception flags/masks/traps and errno are not modeled. This does not emulate ambient floating-point state.
- An accepted span requires an explicit AcosProvider(callable, provenance). The callable receives the clamped binary32 value and must return an already-binary32 float. Invalid outputs are rejected and provider exceptions propagate. Results retain provider provenance.
- The convenience comparison_acos_provider uses host Python math.acos in binary64, then rounds to binary32. It is not a recovered or bit-exact implementation of the target's dynamically resolved acosf.
- `span_bytes` is a declared byte span, not allocation validation. Values other than 0x480 return byte zero without inspecting records/provider. Accepted spans require an immutable tuple of exactly six records, each containing four authored Triple points and one reference Triple.
- Only the direction is normalized by its length. A reference vector may be nonunit. Ordered radius <= epsilon skips; NaN radius does not skip. The clamp selects its source on unordered/equal cases. Ordered rounded degrees > 90 accepts; equality and NaN do not.
- The result reports the eventual low byte at frame+c, not a function return value, a full native dword, or an inferred visual label.

## Validation

13 focused authored tests pass, plus 4 separately written independent reviewer tests. Independent review found no blocking issue. Coverage includes span rejection, short/equal-epsilon directions, all-six failure, first ordered pass, nonunit references, quiet NaNs/provider boundaries, operation order, RN-even ties, underflow/overflow/signed zero/sqrt, and adjacent binary32 pi/2 angle boundaries.

These are scoped reference tests, not broad repository CI or target compatibility proof. No original assets/native/JVM/guest execution, dependencies/installers were used. Exact reviewed file hashes and execution logs are recorded in NATIVE-GEOMETRY-CLASSIFIER-REFERENCE-VALIDATION-2026-10-18.json and the linked independent review receipt.

[Original-byte predicate](NATIVE-GEOMETRY-CLASSIFIER-PREDICATE-2026-10-18.md), [implementation](tools/native_geometry_classifier_reference_ysm_265.py), [tests](tools/test_native_geometry_classifier_reference_ysm_265.py), [validation receipt](NATIVE-GEOMETRY-CLASSIFIER-REFERENCE-VALIDATION-2026-10-18.json), [independent review](NATIVE-GEOMETRY-CLASSIFIER-REFERENCE-REVIEW-2026-10-18.json).
