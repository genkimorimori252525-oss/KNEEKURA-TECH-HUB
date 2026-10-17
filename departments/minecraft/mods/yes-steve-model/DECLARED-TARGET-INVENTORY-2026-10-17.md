# Validate a search target before trusting a zero-call result

An exact-symbol scan can return zero simply because its owner/name/descriptor is misspelled. Before interpreting zero as evidence about a real method/field, verify that the intended declaration exists in the exact artifact. This is a narrow additional check, not a semantic review or full runtime call graph.

`tools/validate_member_targets_ysm_265.py` reads class declarations without executing them. Its reusable member validator rejects absent or malformed owner/name/descriptor triples and distinguishes method/field descriptors. Its explicit inventory-audit mode also recognizes class-only reference target lists. It does not infer original names, resolve external declarations or silently reinterpret inherited-owner references.

The ExecuteMolang producer scanner now requires this declaration check before capture or verification and records the checked targets. Its eight corruption controls include removal of that declaration proof. Eight unit tests for the helper include a one-character owner error, wrong overload/name/kind, missing class and resource-file exclusion.

An explicitly invoked one-time audit checked13 existing exact-target inventories,46 target rows, against all955 class declarations with no missing target. See [receipt](DECLARED-TARGET-INVENTORY-VERIFICATION-2026-10-17.json). Files without a target table are listed as skipped, not treated as covered. The receipt does not recompute every call inventory or retroactively change earlier frozen receipts.

Use for the current inventory, for example:

```bash
python tools/validate_member_targets_ysm_265.py --jar /absolute/path/ysm.jar \
  --evidence EXECUTE-MOLANG-PRODUCERS-EVIDENCE-2026-10-17.json \
  --out /tmp/target-declaration-check.json
```

Only choose --audit-target-inventories when an explicit batch check is needed. It scans the selected research root's local inventory JSONs; it is not a startup command, download, installation probe, source crawl, target execution or proof that valid targets have complete global caller coverage.
