# Opt-in evidence locator

Use this when an AI already knows a query name, class role, obfuscated owner or topic and needs the smallest relevant dossier. No installation, startup hook, JAR, source checkout, Java tool or full audit is required for lookup. Ordinary repository tasks do not need to run it.

From this directory:

```sh
python tools/evidence_locator_ysm_265.py --query bone_rot
python tools/evidence_locator_ysm_265.py --owner CtrlBinding
python tools/evidence_locator_ysm_265.py --owner oo0ooOOo00o0O0OO0O0OOO00
python tools/evidence_locator_ysm_265.py --topic CONTROL
```

The prebuilt JSON is a compact navigation file instead of the full research directory. Results are bounded to 20 by default; --limit allows 1–100, with an explicit total/truncated field. Query search covers171 base query/YSM names plus109 ctrl/tlm/math names from the explicit additional registration-site catalog. Real/fallback sites remain separate; a hit is not proof that its runtime branch is active. See [additional catalog scope](EXTRA-BINDING-CATALOG-RECOVERY-2026-10-17.md). Topic search matches recovery-document filenames, not full text. Owner search matches normalized slash/dot names existing class-role mappings or explicitly anchored comparative aliases; it does not infer or promote new mappings.

Exact navigation membership is recorded in the JSON's owners, source_hashes, documents and unindexed_evidence_schemas fields. These counts can grow during an explicit rebuild and are not semantic completion. Unsupported schemas are listed instead of being guessed as method bodies; a source-role catalog entry alone is not a complete body recovery.

A normal search reports UNCHECKED_SNAPSHOT and never scans/rebuilds the evidence directory. Add --check-selected to hash only returned evidence/documents and the relevant map or bounded query catalogs. A mismatch returns nonzero with STALE_OR_MISSING_SELECTED_FILE. A successful selective hash check does not establish that new files have been indexed, that all evidence is current, or that semantics are independently reviewed.

To deliberately rebuild after adding research:

```sh
python tools/evidence_locator_ysm_265.py --build
```

Build reads local JSON/Markdown and writes only the index. It does not run any verifier or target, install tools or download artifacts. Supported snapshot arrays are top-level members, bounded_dependency_support and constructor_members; other schemas are listed rather than guessed. Existing map confidence is copied only for navigation and not promoted. The index excludes its own index and its own verification receipt.

Tests: tools/test_evidence_locator_ysm_265.py, sixteen fixture cases covering deterministic extraction, duplicate owner normalization, role/query/topic search, bounded output, stale/missing selected files, document hashing, no implicit rebuild/global check, self-index exclusion, and retention of both optional real/fallback registration sites. Actual base and additional namespace lookups were checked against repository files. No game behavior is tested.

## Comparative source aliases without confidence promotion

Some useful source-role names have no central class mapping yet. Explicit anchored entries in NAVIGATION-COMPARISON-ALIASES-2026-10-17.json now make names such as SoundInstanceManager, PcmAudioStream and RenderUtil searchable with --owner. They appear under comparison_aliases with PRIMARY_STATIC_REVIEW_ONLY, separately from mapping (which remains null when absent). A prior central role/confidence is preserved even when a comparative name differs. These labels are not proven original unobfuscated symbols.

Explicit --build verifies each alias against a supported captured owner, exact evidence hash, source-track path/hash and recovery document. It rejects stale/missing/unsafe/duplicate entries. Normal search still reads only the compact index; --check-selected additionally checks the alias catalog and returned alias documents. No audit, download or installation is triggered. Tests cover unmapped aliases, preserved formal mapping, stale catalog, unsafe/missing anchors and no automatic source reads.
