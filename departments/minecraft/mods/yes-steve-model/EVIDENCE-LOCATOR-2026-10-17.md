# Opt-in evidence locator

Use this when an AI already knows a query name, class role, obfuscated owner or topic and needs the smallest relevant dossier. No installation, startup hook, JAR, source checkout, Java tool or full audit is required for lookup. Ordinary repository tasks do not need to run it.

From this directory:

```sh
python tools/evidence_locator_ysm_265.py --query bone_rot
python tools/evidence_locator_ysm_265.py --owner CtrlBinding
python tools/evidence_locator_ysm_265.py --owner oo0ooOOo00o0O0OO0O0OOO00
python tools/evidence_locator_ysm_265.py --topic CONTROL
```

The prebuilt JSON is about 277 KB instead of reading the full research directory. Results are bounded to 20 by default; --limit allows 1–100, with an explicit total/truncated field. Query search covers171 base query/YSM names plus109 ctrl/tlm/math names from the explicit additional registration-site catalog. Real/fallback sites remain separate; a hit is not proof that its runtime branch is active. See [additional catalog scope](EXTRA-BINDING-CATALOG-RECOVERY-2026-10-17.md). Topic search matches recovery-document filenames, not full text. Owner search matches normalized slash/dot names or existing class-role mappings; it does not infer new roles.

The index covers 450 distinct owner keys from supported member arrays, 80 evidence files, the central map, two query catalogs and 77 recovery documents at this checkpoint. This is navigation coverage, not semantic completion. Nine evidence files have unsupported schemas and are explicitly listed in the JSON; no references are mislabeled as captured method bodies. Exact membership can evolve when deliberately rebuilt.

A normal search reports UNCHECKED_SNAPSHOT and never scans/rebuilds the evidence directory. Add --check-selected to hash only returned evidence/documents and the relevant map or bounded query catalogs. A mismatch returns nonzero with STALE_OR_MISSING_SELECTED_FILE. A successful selective hash check does not establish that new files have been indexed, that all evidence is current, or that semantics are independently reviewed.

To deliberately rebuild after adding research:

```sh
python tools/evidence_locator_ysm_265.py --build
```

Build reads local JSON/Markdown and writes only the index. It does not run any verifier or target, install tools or download artifacts. Supported snapshot arrays are top-level members, bounded_dependency_support and constructor_members; other schemas are listed rather than guessed. Existing map confidence is copied only for navigation and not promoted. The index excludes its own index and verification receipts.

Tests: tools/test_evidence_locator_ysm_265.py, ten fixture cases covering deterministic extraction, duplicate owner normalization, role/query/topic search, bounded output, stale/missing selected files, document hashing, no implicit rebuild/global check, self-index exclusion, and retention of both optional real/fallback registration sites. Actual base and additional namespace lookups were checked against repository files. No game behavior is tested.
