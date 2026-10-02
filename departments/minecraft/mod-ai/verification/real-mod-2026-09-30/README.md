# Actual staff MOD static provider/Core acceptance

This bounded acceptance experiment exercises the existing adapters and Core staging
caller on the local Celestial Staff MOD targeting Minecraft 1.20.1 / Forge 47.4.6.
`summary.json` is derived evidence only. Raw inputs, logs, full receipts, CAS,
Mojang mappings, JARs and local paths are intentionally excluded.

## Proven scope

- Pinned Vineflower decompiled seven actual staff classes using all 101 exact
  ordered Forge compile dependencies; all generated Java recompiled with Java 17
- Pinned tiny-remapper remapped actual staff bytecode from Mojmap to SRG
- All seven remapped classes match the prior ForgeGradle distribution build in
  normalized javap signatures/constants/instructions; six resources match bytewise
- Original/recompiled/remapped pure-policy smoke callers passed without starting
  Minecraft; this is not runtime or client-input acceptance
- Actual source research and review-only Core staging passed real Core schemas;
  the existing human ingestion gate rejected an AI reviewer with zero writes
- Focused provider/mapping/Core regression: 46 passed

The prior static comparison JAR (`2cc36031…`) and later package (`15fd766e…`) are
separate raw builds. Their source inventory and class/resource bytes match; only
the manifest's Implementation-Timestamp and associated ZIP metadata differ. No
exact signed-run/package-generation equivalence or runtime acceptance is claimed.

Mapping conversion is one-off acceptance input preparation, not a missing reusable
provider contract. The existing adapter intentionally requires an explicitly
pinned Tiny v2 mapping. `ConvertMappings.java` invokes mapping-io already bundled
inside the pinned tiny-remapper JAR. It combines verified official Mojang mapping
descriptors with the exact ForgeGradle TSRG2 names; all 96,612 names were checked
against that input. The derived Tiny file is not an upstream-distributed artifact.

## Reproduce without new downloads or game launches

Prerequisites are the existing requested checkout and its Python test environment,
the completed disposable staff acceptance directory (including `mdk/` and
`review-evidence/cas/`), and the accepted provider directory containing the pinned
tool JARs and `jdk-17.0.20.1+1/`. They are local, intentionally unpublished inputs.
The scripts verify input hashes and refuse to overwrite an existing output folder.
They are a Linux acceptance harness for this specific pilot, not a new tool platform.

From the repository root, set `EVIDENCE_DIR` to this folder, `STAFF_ACCEPTANCE_ROOT`
and `PINNED_PROVIDER_ROOT` to those existing private input directories, and
`NEW_OUTPUT_DIRECTORY` to a fresh directory outside the checkout. Then run:

```sh
PYTHONPATH=src python "$EVIDENCE_DIR/run_actual.py" \
  --repository . --staff "$STAFF_ACCEPTANCE_ROOT" \
  --providers "$PINNED_PROVIDER_ROOT" --work "$NEW_OUTPUT_DIRECTORY"
PYTHONPATH=src python "$EVIDENCE_DIR/verify_outputs.py" \
  --work "$NEW_OUTPUT_DIRECTORY"
JAVA_HOME="$PINNED_PROVIDER_ROOT/jdk-17.0.20.1+1" \
  PATH="$PINNED_PROVIDER_ROOT/jdk-17.0.20.1+1/bin:$PATH" \
  pytest -q tests/test_minecraft_providers.py tests/test_minecraft_mappings.py \
    tests/test_minecraft_core_bridge.py
```

The first script invokes the existing capture/index/provider/Core APIs. The second
independently verifies receipts, all mapping names, output inventories, bytecode
parity, package-generation distinction, and pure-policy execution. Outputs remain
private in the requested new directory. Schema/backend/canonical/runtime limits
stay explicit in the derived summary.

## Reviewed verifier repairs

A fresh reproduction now requires exact class/resource inventories and fails on any normalized class mismatch, reads policy
constants reflectively from each actual output, and binds the research profile
to the captured MOD revision rather than the adapter repository's revision.
Sixteen focused regressions include a separately compiled changed-constant negative.
The corrected fresh run again verified all seven classes, six resources and three
policy outputs. Previous local receipts/profiles are retained unchanged and are
not used as the corrected lineage claim. `summary.json` records the separate
MOD/adapter revisions and fresh receipt references.

To reverify an existing captured run without overwriting its prior verification, use
`--verification-name verification-new` (a new simple directory name only).
