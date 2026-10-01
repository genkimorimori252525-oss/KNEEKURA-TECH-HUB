# Bounded Blockbench repair acceptance — 2026-10-01

The requested partial-part repair, before/after comparison, and separate UV/texture/display-slot adjustments are implemented. This record binds the completed desktop run to its exact tested source. Later LAB source work does not change this historical evidence.

- TECH HUB source: `78785ed9723e2cdc569730d8c87eac745f88643f`
- Source tree: `9cca009f7b8ae1905c1e2f317c65d7542bdf363e`
- [Hosted Blockbench desktop run](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36808072671): success
- [Hosted full Python suite](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36808072665): 2944 passed, 331 skipped
- Retained desktop artifact ID: `11138780068`
- Artifact ZIP SHA-256: `8c3e85826bc07fa75a701dee63bafd5d3260c329749b4c23cd810508e611b05b`

## Verified editor behavior

The owned Celestial Staff project retained generations 0 through 10: five bounded injected changes and five restorations. Each mutation bound the request/project/generation and stable part, face, palette region or display-slot identity to expected old values. Independent full-state checks confirmed the allowed change and verified unrelated fields stayed unchanged.

The four requested repair categories were exercised separately:

- Part geometry: the upper star tip was restored from Y30 to Y28.5. Raw front/back images show the restored gap.
- Face UV: one north-face rectangle was restored from `[0,0,4,4]` to `[24,24,28,28]`. The intended front accent changed; other views retain their recorded visibility limits.
- Texture: rectangle `[24,24,32,32]` was restored to purple `#864fc7`. Raw front/back pixels confirm the intended accent.
- Holding display: `thirdperson_righthand.translation.y` was restored from 6 to 4. Native/model/export structure verifies this value; the regular editor captures are pixel-identical and do not prove the in-game holding appearance.

A fifth geometry control changed scene bounds and verified that comparison still used the retained camera instead of fitting each generation independently. All 11 captures/exports and 33 per-direction camera metadata records passed independent checks. The 141 original evidence files remained unchanged during review.

## Scope limits

Source tests, editor structural checks, exported artifact identity and visible raw-image findings are distinct evidence. The run did not launch Minecraft. Runtime acceptance is `NOT_RUN`, and loaded runtime revision is `UNATTESTED`. In-game holding appearance remains untested.

The local full Python suite at this source had 3170 passed, 104 skipped, and one known environment failure: the sandbox places Git markers above all writable directories, so the test requiring a private directory outside every Git ancestor cannot construct its expected fixture. The exact-head hosted suite above covers the normal filesystem case without excluding that test.
