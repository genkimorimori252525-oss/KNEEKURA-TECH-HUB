# Native blacklist regex options and match mode

## Result

The native compiler requests libstdc++-family ECMAScript grammar, case-insensitive matching and optimize through flags 0x15. Full-range match, rather than substring search, is independently supported by native executor acceptance logic. Case handling is locale-facet based, not a proven ASCII-only fold or Unicode regex engine. The original library/compiler release is still unidentified; pinned GCC 14.2.0 sources serve as explicit comparison evidence, not a claim that this binary was built with that release.

No target code, regex test, archive asset, user configuration or extractor was executed/read. Original native/checkpoint inputs remain immutable.

## Original-byte flag lineage

3d9b25 passes R8D=0x15 to compiler 32c1e0. That function saves it at compiler +0 (32c1fd), and scanner +94 (32c2c8). It selects scanner routine 339f50 when bit 0x10 is set (32c33f..32c358), otherwise 339ad0. The scanner receives the exact original line begin/end at +b8/+c0.

Within 32e110's atom construction, 32e690 tests bit 0x10 for the any-character grammar branch. At 32e76a bit 0x1 selects the transformed literal matcher; bit 0x8 selects its collation variant. With 0x15, bit 0x1 is set and 0x8 clear: the path 32ecd7..32ed50 transforms the pattern byte through a locale facet virtual call +20 and installs predicate 339600. That predicate transforms each input byte through the same facet slot at 339631 before comparing with the stored transformed pattern byte. This supplies direct native evidence for case-insensitive/facet-based comparison rather than just guessing flag names.

The selected any-character predicate is 3396d0 (32edc2). It transforms input and LF/CR through the same facet and accepts when input differs from both. Bit 0x10 therefore also selects an ECMAScript-like dot rule. Do not extrapolate full character-class/escape/backreference behavior from this bounded audit.

Pinned upstream regex_constants.h defines bits 0x1/0x4/0x10 as icase/optimize/ECMAScript. regex_compiler.tcc's atom selection, constructor EOF validation and locale matcher construction correspond structurally to the native paths above. Hence the option labels are supported by both pinned source and native use, while complete cross-version compatibility remains unproved. Optimize is a requested option; no speedup, specific optimizer choice or semantic change is established. Flags do not request collate, nosubs or multiline under this mapping.

## Exact-match acceptance

Caller 3d9872 supplies begin/end of the full original archive name, match flags R8D=0 and mode R9D=1. Wrapper 3d1930 preserves mode at stack+14. Its true branch at 3d1d69 calls executor 3d24c0 with mode argument zero at 3d1d75. The false branch calls with one and subsequently advances candidate starting positions (3d1dd0..3d1df5).

Executor 3d24c0 passes this mode to 3d3720 (3d264b). Native acceptance at 3d3e47..3d3e58 rejects when mode is zero AND current pointer differs from end. The wrapper's initial-position setup plus this end condition establish full-range matching. Pinned upstream regex.tcc and regex_executor.tcc corroborate true wrapper mode → exact executor mode and require current==end for exact acceptance. This is stronger evidence than only observing a single invocation.

The prefix-selection test remains separately case-sensitive. A case-insensitive regex does not broaden the exact assets/yes_steve_model/builtin/ prefix condition.

## Errors and empty patterns

Compiler 32c1e0 checks EOF token 0x1b after parsing at 32c5d4..32c5e3. Failure reaches 32c781, loads error code 5 and invokes 2fa678. Pinned regex_error.h maps code 5 to error_paren; the corresponding upstream constructor throws on leftover tokens. Other parser paths call error construction helper 32c9e0; unwind/cleanup paths are visible. No guarantee that malformed rules are silently skipped is supported. Complete outer exception handling and user-facing diagnostic text are outside this seam.

Empty or all-isblank configuration lines are removed BEFORE compiler invocation, as proved in the prior selection report. They therefore do not install an empty blacklist rule. At compiler level begin==end selects EOF at 32c399; pinned grammar supports an empty alternative via a dummy state. Its full-range semantics would accept only an empty range, not arbitrary nonempty builtin names. No synthetic empty pattern was executed. Nonempty regexes capable of matching the empty string still must consume the full input to exclude a nonempty record in exact mode.

## Pinned source provenance and limits

Six upstream files were fetched explicitly from gcc-mirror/gcc ref releases/gcc-14.2.0. upstream-provenance.json records each Git blob SHA1, verified against locally saved exact bytes, SHA256 and source URL. No unpinned local headers are used as the authority in this report. The original binary's exact libstdc++ release, locale/facet instances, non-ASCII behavior and complete dialect conformance remain unavailable.

Native image SHA256: 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. evidence.json hashes bounded original-byte windows. No passing filter model, extraction fixture, path-safety claim or integrity bypass was added.

## Recommended next seam (not researched here)

Prioritize numeric ostream/hash-manifest formatting: it affects every retained record and therefore every aggregate comparison. Resolve insertion overload, base/sign, locale/grouping and stream initialization before any byte-exact manifest contract. Duplicate-name policy remains important but affects a narrower condition and can follow. Neither was expanded in this task.

Published receipts: [compact contract](NATIVE-BLACKLIST-REGEX-2026-10-18.json), [native windows](NATIVE-BLACKLIST-REGEX-2026-10-18-EVIDENCE.json), [pinned upstream source provenance](NATIVE-BLACKLIST-REGEX-UPSTREAM-2026-10-18.json).
