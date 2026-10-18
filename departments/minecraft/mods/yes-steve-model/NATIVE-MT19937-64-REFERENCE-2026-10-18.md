# Authored MT19937-64 numerical reference checker

## Result and use

Ten standard-library Python tests pass, including an independent pinned official GCC numerical test: with the standard default seed5489, the10000th MT19937-64 output is9981545732273789042. The other tests are explicitly authored synthetic checks, not original-YSM execution or asset processing.

Run offline from the tools directory:

    PYTHONDONTWRITEBYTECODE=1 python test_native_mt19937_64_reference_ysm_265.py
    PYTHONDONTWRITEBYTECODE=1 python native_mt19937_64_reference_ysm_265.py --seed 5489 --words 4

`tools/native_mt19937_64_reference_ysm_265.py` is standalone. `MT19937_64(seed).next_u64()` returns one64-bit word; `.words(count)` returns a list. `ByteStream(seed).read(count)` consumes little-endian bytes with a retained partial-word tail. `.xor(bytes)` XORs an authored input with the next stream bytes. A new instance with the same seed is required for reapplication. Inputs are validated as unsigned64-bit integer seeds and nonnegative integer lengths; no implicit seed truncation is performed.

There is no file-input option, asset decoder, original16-byte seed mixer, JNI/GL interface, target loader, original-code emulator, or runtime override. The CLI displays numerical words only. The reference's seed5489 is the standard default for reproducibility, not a claim that the target uses that seed.

## Independent primary-source anchor

[Official GCC test at pinned commit](https://github.com/gcc-mirror/gcc/blob/2ee5e4300186a92ad73f1a1a64cb918dc76c8d67/libstdc%2B%2B-v3/testsuite/26_numerics/random/mt19937_64.cc), retained externally as `gcc-mt19937_64.cc`, SHA2560b5bacbeb73374322a84f7c15ce3c1df557c816154b7baf7f4fc43edf674183e. Its test default-constructs the engine, discards9999 outputs, then checks the next value. The reference reproduces that numerical result without compiling or running GCC's source.

The prior `texture-generator-comparison` cohort pins the official alias, integer-seeding, refresh, and output formulas at the same commit. Its header's default_seed constant is5489. The preserved comparison establishes operation/parameter equivalence from original disassembly; this checker provides a reusable mathematical implementation of those operations. Agreement with a source vector increases confidence in the reference implementation, but does not independently prove native bit-equivalence, runtime seed contents, or texture restoration.

## Test coverage

- Official10000th-output value, spanning repeated312-word state refreshes.
- Synthetic seed invariants for0,1,5489,maximum64-bit, and an authored mixed seed.
- Index transitions at311/312 and subsequent refreshes.
- A fixed-word stub independently checks low-to-high byte order, empty reads, cached tails, and word-consumption counts.
- Every split position for lengths0..32 under three seeds.
- Selected splits around byte2496 and4992, plus chunk sizes1,2,3,7,8,9,31,312,2496, over5011 bytes and four seeds.
- Fresh-stream XOR reapplication, preserved intervening mutation delta, and an example showing that an advanced stream does not reset itself.
- Zero-length state preservation and invalid inputs.

The split/roundtrip checks compare authored reference components and mathematical identities. They are synthetic cross-checks, not additional external test vectors or proof against original machine execution. Default/seed constructor sources fetched during the targeted search are retained for provenance only and are not64-bit numerical oracles.

Repository adaptation retains only authored Python and the numerical vector with its pinned URL/hash. The original GCC source stays external; tests do not require a network or source download. This differs from the external test harness, which additionally checked the retrieved source hash. Run the scoped tests above; whole-project validation is not required for using this isolated checker.
