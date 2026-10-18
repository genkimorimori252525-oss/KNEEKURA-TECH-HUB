# Temporary-path environment frontier: bounded static plan

## Decision

Yes: explicitly declaring a named environment key absent can be modeled as a null result without claiming any filesystem success. TMPDIR absence alone does not select `/tmp`: the original code next queries TMP, TEMP and TEMPDIR, in that order. An all-four-absent scenario reaches the literal fallback `/tmp`, then a mandatory filesystem status query. Keep that status query blocked unless a separately reviewed virtual filesystem fixture supplies its contract.

No implementation, checkpoint resume, host environment access or original instruction execution occurred. Original checkpoint SHA256037e49c09fa15750aef36853a0b0bde9874e73ff3abb0e6944b29602c4c3e635 is unchanged. This plan does not propose successful temp-directory creation or writable-directory assumptions.

## Exact original selection

Function311760 stores its destination path in RBP. At311769 it loads table d1b2e0 and bounds iteration at table+0x20. Four original RELATIVE relocations point to NUL-terminated literal keys:

- d1b2e0 →421c6: TMPDIR
- d1b2e8 →3f000: TMP
- d1b2f0 →45e63: TEMP
- d1b2f8 →45912: TEMPDIR

31178a loads the current key;31178d calls d14e70. The stopped caller return311792 tests RAX. Null advances the table by8 at31179b;3117a2 loops until all four were queried. All-null sets length4 and literal source3f55a (`/tmp`) at3117a4..ab.

Nonnull branches311830, preserves the returned pointer and calls strlen at311838. It constructs the destination from that pointer and measured length through3117b0..c2. An empty but nonnull environment value is therefore selected immediately with length0; it is not equivalent to an absent key. No search for a later key is made after a nonnull selection, even if subsequent directory validation fails. The selected bytes are copied into native path-owned storage; a hypothetical present-value environment model would need stable, bounded NUL-terminated guest storage through this copy.

## Import-name refinement

The preceding receipt uses operation label `getenv`. Original ELF provenance is more precise:

31178d → PLT d14e70 → pointer slot d30bc0, R_X86_64_RELATIVE addend13d7136 → indirect slot184d3e0, named R_X86_64_JUMP_SLOT symbol **secure_getenv**.

This agrees with the existing harness's import index121 entry and `secure_getenv` model. The active model currently accepts only GLIBCXX_TUNABLES and returns null; TMPDIR triggers UNMODELED_ENVIRONMENT_KEY. Therefore extend the semantic secure_getenv operation's declared environment input, not a new per-PC getenv success stub. Absence of a key yields null without needing to assert secure-execution mode; a present-value extension would additionally need an explicit secure-getenv policy/context instead of assuming ordinary getenv behavior.

The import chain for311838 resolves strlen. The status and errno chains below resolve __xstat and __errno_location. evidence.json records all four two-stage chains, not just raw byte-pattern matches.

## Mandatory filesystem boundary

After path construction and helpers318dd0/3196a0,3117f8 calls311210(path,&error_code). There is no inline mkdir/open/create/write in this immediate path-selection routine. This is not a whole-image absence claim or a promise concerning later callers.

311210 loads the selected path's string pointer into RSI, sets EDI=1 and RDX=&stack_stat, then calls d14af0 at311229. Its two-stage import resolves __xstat at slot184d220. This is the Linux stat ABI already used by the harness, but its path is now the selected temp candidate, not one of the two currently permitted executable/JVM paths. Existing native_allocator_os_fixture_ysm_265.py demands ABI1 and path equal to fixture exe_path or `/virtual/jdk/lib/server/libjvm.so`; `/tmp` therefore reaches UNMODELED_STAT_PATH_OR_ABI. Do not add `/tmp` to the existing regular-file success branch: it would return a regular-file mode and is the wrong semantic fixture anyway.

On status success,311260 reads stat mode at output+0x18. It masks0xf000 and maps0x4000 to status tag2 at311279/311308. Caller311805..807 accepts only AL==2. A non-directory successful status sets error value20 at31180e. On status failure,311232 calls __errno_location and stores the returned errno into the error_code; errno2/20/75 have explicit status classifications at31123e..258, but the caller still takes its nonzero-error route. Error paths lead to311704's exception construction through31eb30 and throw helper2abe00; exception allocation/formatting/unwind are separate stop categories, not reasons to fabricate successful filesystem status.

Thus selecting `/tmp` proves neither existence, directory type, permissions, writability, free space nor successful later initialization. Even directory type alone would not establish the remaining properties. The finite useful first stop is the unresolved status query itself.

## Proposed generic input contract and finite validation scope

- Add an explicit bounded absent-key set to the existing virtual environment scenario. Keep GLIBCXX_TUNABLES behavior/provenance intact. Support TMPDIR alone if that is the chosen scenario, or explicitly declare all four keys absent to exercise the deterministic fallback; unknown keys must still stop.
- Validate the incoming guest key as a bounded NUL-terminated string and dispatch by the resolved import identity and key, not caller address. Return zero only for explicitly absent keys. Never read the host process environment; never use Python temporary-directory discovery as target input.
- Preserve the declared set and lookup ledger across checkpoint save/restore. A scenario extension must be explicit and reviewed; no inferred mutation of the prior snapshot. Counts should reflect the exact key sequence.
- Tests may use authored model calls/algebra: declared absence gives null, undeclared key stops, TMPDIR-only permits one lookup then stops at TMP, all-four-absent establishes the original `/tmp` selection, duplicate or malformed configuration rejects, metadata/import mismatch rejects, and source checkpoint remains unchanged. These are not executions or observations of original target code.
- Do not implement present values in the first cohort. If later needed, distinguish absent versus empty, preserve first-nonnull precedence, bound returned-string lifetime, and declare secure execution policy. Do not silently redirect paths.
- Leave __xstat guarded. A later independent FS scenario would need a path-keyed immutable status result including ABI layout, return code and errno transition; it must distinguish directory/non-directory/missing/error cases and cannot derive those from a path literal. Any subsequent mkdir/open/read/write/permission check remains a fresh boundary outside this plan.

Expected immediate stop categories: unknown environment key; malformed/unbounded guest key; unsupported present/secure-getenv state; then selected-path __xstat (UNMODELED_STAT_PATH_OR_ABI under current fixture). If a later explicit status-failure scenario is supplied, errno and exception-construction/unwind contracts become relevant. No blanket success modeling is warranted.

## Evidence

reproduce.py checks the pinned original SO, unchanged checkpoint, three authoritative instruction windows, four environment-key relocation records/literal spans and four two-stage import chains. evidence.json hashes those and the exact existing fixture sources/previous continuation receipt. Exploratory windows starting311700/13d6fd0/13d7120 include mid-instruction bytes and are not authoritative evidence ranges. No assets or repository files were changed.

The source manifest is published as [evidence](NATIVE-TEMP-ENVIRONMENT-MODEL-EVIDENCE-2026-10-18.json). Binary windows and reproduction script remain in the external `temp-environment-plan` evidence directory. A separate read-only artifact check confirmed three exported window hashes, two fixture-source hashes and prior receipt/checkpoint hashes; it did not rederive imports from the original image. The reproduction script regenerates its outputs, so it must not be mistaken for an immutable-manifest comparison.
