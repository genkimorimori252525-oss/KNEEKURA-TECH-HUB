# Opt-in method evidence viewer

Use after the [evidence locator](EVIDENCE-LOCATOR-2026-10-17.md) identifies a relevant file. This is a local one-file viewer, not an auditor, decompiler, artifact loader or mandatory startup step. It reads one explicitly selected JSON file, outputs a small method summary by default, and never scans other evidence files or runs tools automatically.

## Why

Large evidence files preserve complete operands and support classes for reproducibility. An AI following a single method should not have to load all of that into context. A measured lexer-file example reduced the returned JSON from426,069 file bytes to2,714 summary bytes for the selected owner. This is an output-size observation, not a semantic-completion or general performance percentage.

## Summary first

Run from this research directory:

```bash
python tools/inspect_member_evidence_ysm_265.py \
  --evidence LEXER-TOKEN-DIAGNOSTICS-EVIDENCE-2026-10-17.json \
  --owner com/elfmcys/yesstevemodel/oOOooOo0OO00ooO00OOO00o0
```

The owner must be the exact internal or dotted class name. Human-readable comparison aliases belong to the locator; this viewer does not silently convert them into established names. Optional --name and --descriptor narrow the summary. Default limit20, maximum100; --offset pages sorted owner/name/descriptor identities. total_matches and truncated remain explicit.

## Full member only when needed

```bash
python tools/inspect_member_evidence_ysm_265.py \
  --evidence NATIVE-TEXTURE-JAVA-BOUNDARY-EVIDENCE-2026-10-17.json \
  --owner com/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0 \
  --name O00OOOooOoooOoo0o0o0oO0O --descriptor '()V' --full
```

This example returns the native upload declaration without invented instructions. Full mode requires exact owner/name/descriptor and exactly one unique match. It returns the stored record unchanged, including handlers or supplemental operands when present; it does not truncate or summarize a body while calling it full.

Supported top-level collections are members, bounded_dependency_support, constructor_members, caller_methods and writer_methods. Identical duplicate records are deduplicated with their collection provenance retained; conflicting records fail rather than arbitrarily winning. Unknown/malformed schemas fail explicitly. Evidence names must be flat JSON filenames resolving inside the selected research root, including symlink checks. --root changes the research root explicitly.

## Trust boundary

Every response includes the actual selected-file SHA-256 and the artifact hash DECLARED by that file. It explicitly says artifact/source not rechecked, auditors not run, target not executed and confidence unchanged. Reading an evidence snapshot is not independent verification against the original JAR. Use the existing relevant scoped auditor only when verification is the task. Native/abstract methods remain without Code.

Twelve unit tests plus six actual repository cases cover exact overloaded selection, summaries, full records, support/caller collections, native/abstract declarations, duplication conflicts, pagination, unsafe paths and single-file reads. See [verification receipt](MEMBER-EVIDENCE-VIEWER-VERIFICATION-2026-10-17.json). No network access, tool installation checks, source scanning, global validation or semantic promotion occurs on lookup.
