# KNEEKURA Render Architecture v1 — Normative Specification

Status: FROZEN for implementation
Date: 2026-08-28 JST
Workflow: 1fde56e48f81433ab35bf9b8cffb5b78

## 0. Normative language

MUST / MUST NOT are implementation requirements. SHOULD is the default unless a concrete compatibility reason prevents it. MAY is optional.

## 1. Architectural objective

KNEEKURA Viewer MUST run without Minecraft, Forge, YSM, `.minecraft`, or a Minecraft client jar. Minecraft + the target renderer/mod are compile/teach-time dependencies only. They are used to capture authoritative static and dynamic render results and to generate self-contained Render Packs and Golden Oracle data.

The runtime boundary is:

- Render Pack: long-lived model/render assets.
- Render Frame: one rendered state at one render invocation.
- Golden Oracle: verification-only expected results.
- Thin Viewer: generic replay engine that understands only KNEEKURA IR.
- Offline Emulator: optional predictor that understands YSM semantics and emits the same RenderFrameIR contract as runtime capture.

## 2. Hard boundaries

### 2.1 Viewer runtime MUST NOT read

- `.minecraft/`
- YSM installation or custom YSM source directories
- Forge installation
- Minecraft client jar
- raw Bedrock geometry as an authoritative input
- raw YSM animation/controller/Molang data except through the isolated Offline Emulator bundle

### 2.2 Authoritative renderer MUST NOT

- parse Bedrock geometry
- evaluate Molang
- execute YSM animation controllers
- infer dynamic visibility
- reconstruct YSM TRS conventions
- silently fall back to a lower-fidelity source when a higher-fidelity source exists but is invalid

### 2.3 Compiler / capture side MAY know

Minecraft, Forge, YSM, GeckoLib, RenderType, VertexConsumer, model loaders, texture resolvers, source coordinate conventions, animation/controller internals, and mod-specific hooks.

## 3. Source separation and authority

Every RenderFrameIR MUST carry:

- `source.type`
- `source.authority`
- `source.fidelityTier`

Initial source types:

- `runtimeFinalVertex`
- `runtimeMatrix`
- `runtimePaletteConverted`
- `recordedPose`
- `animationLibrary`
- `offlineYsmEmulator`

Authority classes:

- `authoritative`: direct final runtime result or direct final runtime matrix/state capture.
- `derived`: based on runtime measurements but requiring a KNEEKURA-side conversion.
- `predicted`: reconstructed without the authoritative runtime for that frame.

Fidelity precedence for automatic selection:

A. runtimeFinalVertex
B. runtimeMatrix
C. runtimePaletteConverted
D. recordedPose
E. animationLibrary
F. offlineYsmEmulator

A higher source MUST NOT be mixed with a lower source inside the same logical field set. Missing required fields make that source/frame invalid; they do not authorize silent inference.

## 4. Render Pack v1

Render Pack v1 is a self-contained directory format. Archiving/compression MAY be added later without changing its logical schema.

Recommended layout:

```text
renderpacks/<model-id>/<pack-hash>/
  manifest.json
  mesh/
    mesh.json
    mesh.bin
    skeleton.json
    groups.json
  materials/
    materials.json
  textures/
    <content-hash>.<ext>
  emulator/
    manifest.json
    animations.json
    controllers.json
    molang.json
    metadata.json
```

`emulator/` is optional. `golden/` is NOT required runtime pack content; Golden Oracle is a separate artifact keyed to `packHash`.

Generated packs containing third-party/Minecraft assets SHOULD remain local/generated artifacts unless redistribution rights are known. Repository tests SHOULD use synthetic or repository-owned fixtures.

## 5. Manifest contract

`manifest.json` MUST contain at least:

```json
{
  "schema": "kneekura.renderpack",
  "schemaVersion": "1.0.0",
  "modelId": "...",
  "packHash": "sha256:...",
  "layoutHash": "sha256:...",
  "compiler": {"name":"...","version":"..."},
  "source": {
    "adapter":"ysm",
    "modVersion":"...",
    "modJarHash":"sha256:...",
    "modelResourceHash":"sha256:..."
  },
  "coordinateSystem": "KNEEKURA_RH_Y_UP_BLOCK",
  "files": [{"path":"...","sha256":"..."}]
}
```

Rules:

- `schemaVersion` uses semantic versioning.
- Major mismatch MUST be rejected.
- Unknown optional fields in a compatible major version SHOULD be ignored.
- Every referenced file MUST have a digest.
- `packHash` is computed from a canonical manifest payload plus referenced file digests, excluding volatile timestamps.
- `layoutHash` changes when vertex layout, index topology, bone slot order, bind data, or draw-group topology changes.
- A RenderFrameIR with a non-matching `layoutHash` MUST be rejected.

## 6. Canonical coordinate and matrix rules

KNEEKURA IR uses one canonical coordinate convention independent of the source mod:

- right-handed
- +Y is up
- model length unit is one Minecraft block
- source-specific pivot/origin/sign/unit conversions happen before data crosses into KNEEKURA IR

All authoritative matrices are float32 4x4, column-major, and multiply column vectors.

`skinMatrix[i]` MUST directly map a bind/model-space vertex contribution for bone slot `i` into posed model space. The Thin Viewer MUST NOT rebuild parent hierarchy transforms to obtain authoritative posed matrices.

`modelToWorldMatrix` MUST map posed model space to KNEEKURA world space. Decomposed position/yaw/scale MAY be included for UI/debugging but MUST NOT be used as the authoritative transform when the matrix exists.

## 7. RenderMeshIR v1

RenderMeshIR answers "what can be drawn".

Required logical fields:

- `modelId`
- `layoutHash`
- vertex streams:
  - position float32x3
  - normal float32x3
  - uv0 float32x2
  - color0 normalized RGBA
  - joints uint16x4
  - weights float32x4
- index stream uint32
- bone slots
- bind matrices / inverse bind matrices
- draw groups

YSM rigid vertices use one joint with weight 1.0; the generic layout keeps up to four weights for future adapters.

The Viewer MUST NOT regenerate authoritative mesh geometry from Bedrock cubes.

## 8. SkeletonIR v1

`skeleton.json` includes:

- bone slot index
- stable bone name
- optional source path/name
- parent slot or null
- bind matrix
- inverse bind matrix
- debug metadata

Parent hierarchy is retained for inspection/emulation/debugging; authoritative rendering uses supplied skin matrices rather than re-evaluating hierarchy rules.

## 9. DrawGroupIR v1

Each draw group MUST contain:

- stable `groupId`
- index `start` and `count`
- `materialId`
- static default order
- optional bone/debug association

The compiler MUST preserve source draw-call ordering semantics. Multiple textures/material passes are first-class; "one model = one texture/material" is forbidden.

## 10. MaterialIR v1

Static material data MUST be explicit rather than inferred from a `RenderType.toString()` string alone.

Minimum fields:

- `materialId`
- base texture reference
- optional normal/emissive references
- alpha mode and cutoff
- blend enable/equation/factors
- cull mode
- depth test function
- depth write
- emissive/fullbright flags
- generic fog output mode (`colorMixPreserveAlpha` / `rgbaFade` / explicit `UNKNOWN`)
- sampler state where material
- default vertex tint behavior
- lightmap/overlay participation flags
- source RenderType string MAY be retained as provenance/debug text

MaterialIR v1 uses these meanings:

- `lightmap`: the captured source RenderType enables Minecraft's lightmap state for that draw
- `fullbright`: the proven shader profile does not attenuate fragment color by sampled lightmap input; this is independent of whether packed light values are present in a final-vertex stream
- `emissive`: the proven shader profile is self-lit/emissive in behavior; this is orthogonal to blend mode and depth-write state
- `vertexTint`: how captured vertex RGBA participates in the proven shader profile; for authoritative `finalVertices`, the concrete per-vertex RGBA values are already present in the final stream
- `overlay`: the captured source RenderType enables Minecraft's overlay state; authoritative `finalVertices` also preserve concrete overlay coordinates per vertex
- `fogMode`: generic fragment fog semantics proven by a version-pinned shader profile; `colorMixPreserveAlpha` mixes RGB while preserving input alpha, while `rgbaFade` fades the full RGBA output

A field MUST remain `UNKNOWN` when those semantics cannot be proven from captured state or a version-pinned canonical shader/state profile. RenderType/shader display names alone are never proof.

For authoritative final-vertex replay, `MaterialIR.replay` is also mandatory. It stores only generic, version-pinned operations: vertex-lighting mode and constants, fog-distance mode, base-texture/color multiplication order, alpha-discard source, overlay combine, and lightmap combine. A shader/profile name may remain provenance, but the Thin Viewer MUST NOT branch on it. If the generic replay description is `UNKNOWN`, the frame remains unpromoted.

Textures are copied/resolved during compile time and referenced by Render Pack-relative content-addressed paths.

## 11. RenderFrameIR v1

RenderFrameIR answers "what was/will be drawn at one render invocation".

Required identity:

- `runId`
- `entityUuid`
- `renderSequence`
- `gameTime`
- `partialTick`
- `modelId`
- `packHash`
- `layoutHash`

`renderSequence` is the stable unique ordering key within a run/entity. `gameTime` and `partialTick` are mandatory temporal matching data and MUST be captured for every render invocation. Float `partialTick` is not used as the sole database key.

Required source metadata:

- `source.type`
- `source.authority`
- `source.fidelityTier`

Required transform:

- `modelToWorldMatrix`

For authoritative `runtimeFinalVertex`, the frame MUST also carry the directly observed generic `globalShaderState` for the same real draw invocation:

- matrix convention
- model-view and projection matrices
- inverse view-rotation matrix
- two directional-light vectors
- shader color / color modulator
- fog curve, start/end, RGBA color, shape, and distance space

These values are observed from the live RenderSystem before and after the same `geoRender`; they MUST NOT be reconstructed from biome, weather, render-distance, or YSM semantics. If the before/after state changes or any replay-critical value is unavailable, capture fails closed.

Deformation is a tagged union:

1. `skinMatrices`
   - array of final 4x4 matrices in bone-slot order
2. `finalVertices`
   - dynamic final position/normal stream or draw stream reference for adapters that cannot expose matrices
   - visibility already resolved by the source renderer MAY be represented with an empty `visibility.bones` only when `bonesResolvedInFinalVertices=true`
   - the frame MUST still carry complete group visibility, draw order, texture/material state, color multiplier, light, overlay, and primitive topology needed to replay the observed draw

`legacyPalette` MUST NOT reach the Thin Renderer. A compatibility converter MAY consume legacy palette capture and emit a normal `skinMatrices` RenderFrameIR with source type `runtimePaletteConverted` and authority `derived`.

Frame state MUST include complete runtime visibility and draw state required for the selected source:

- bone visibility mask
- group visibility mask
- resolved draw order
- per-group texture override where applicable
- tint/color multiplier
- light/lightmap values
- overlay/hurt values
- any dynamic material flags required by MaterialIR

Authoritative frames MUST NOT ask the Viewer to guess missing visibility or YSM controller state.

Authoritative `runtimeFinalVertex` capture MUST carry `source.auxiliarySamplerInputs = "resolved-per-vertex-rgba"` and `KNEEKURA_FINAL_VERTEX_V2`. The V2 stream preserves the original overlay/lightmap integer coordinates for evidence and appends generic resolved overlay RGBA plus lightmap RGBA for every vertex. Capture MUST read those colors from immutable snapshots of the live runtime textures used by the same draw invocation, compare the snapshots before/after the same `geoRender`, and fail closed on missing, ambiguous, changed, or out-of-range data. The Thin Viewer MUST consume the resolved RGBA and MUST NOT sample Minecraft Sampler1/Sampler2 textures. It also MUST use the directly observed outer normal matrix carried by the frame; deriving that normal matrix from the position transform is not authoritative.

Resolving these auxiliary colors removes this specific self-containment blocker, but does NOT by itself prove pixel parity. Generic Thin Viewer shader replay and strict real Windows Golden framebuffer comparison remain separate required evidence.

## 12. Thin Viewer v1

The Thin Viewer MAY know:

- RenderPack manifest/version/hash validation
- generic vertex/index buffers
- generic skin matrices or final-vertex deformation mode
- generic material/draw state
- camera/world matrices
- the directly observed outer 3x3 normal matrix for authoritative final vertices
- generic replay operations from `MaterialIR.replay`
- WebGL implementation details

It MUST NOT contain YSM/Bedrock/Molang/controller-specific authoritative logic.

The rendering pipeline is conceptually:

```text
RenderMeshIR + MaterialIR + RenderFrameIR
  -> validate pack/layout/source
  -> bind generic buffers/materials
  -> apply skinMatrices OR finalVertices
  -> apply modelToWorldMatrix
  -> apply complete visibility/draw order/dynamic state
  -> WebGL draw
```

## 13. Offline YSM Emulator v1

The existing `ysm.js` logic is retained and moved behind an emulator boundary.

Inputs MAY include:

- self-contained emulator bundle from Render Pack
- simulation state
- time/partial tick
- user what-if variables

The emulator MAY parse Bedrock/YSM semantics, Molang, animation controllers, and physics approximations.

Its output MUST be a valid RenderFrameIR, preferably `skinMatrices`, with:

- `source.type = offlineYsmEmulator`
- `source.authority = predicted`
- fidelity tier F

The Thin Viewer renders this output using the exact same renderer as authoritative frames.

## 14. Capture adapter contract

Core interface:

```text
RenderCaptureAdapter
  probeCapabilities()
  captureStaticAssets()
  captureFrame()
  captureOracle()
```

Initial capability flags:

- `staticMesh`
- `skeleton`
- `materials`
- `textures`
- `skinMatrices`
- `finalVertices`
- `visibility`
- `dynamicMaterialState`
- `pixelGolden`

The YSM adapter is the first concrete adapter. GeckoLib/Vanilla/unknown mods can be added without changing the Viewer contract.

If an adapter cannot expose skin matrices but can expose final vertices, authoritative replay MAY use `finalVertices`; KNEEKURA MUST NOT invent matrices from guesses.

## 15. YSM capture points

The YSM/decrypted/static-analysis repository is used to locate observation points, not to copy renderer semantics into the Viewer.

Target hooks:

A. after static mesh/model loading and source geometry interpretation
B. after final animation/controller/physics bone transforms and skin matrix construction
C. after render group/material/texture state resolution
D. at/around VertexConsumer final output for Oracle capture

PR3 specifically targets B and the frame-level state at C, with D retained for verification.

## 16. Golden Oracle

Golden Oracle is verification-only and keyed to:

- `packHash`
- `layoutHash`
- source hashes/version
- scenario id
- frame identity

Representative scenarios SHOULD include:

idle, walk, jump, attack, hurt, death, eye variants, mouth variants, equipment/Gohei visible+hidden, and relevant YSM variables such as weapon-state branches.

Comparison order:

1. topology/counts
2. geometry positions
3. UV
4. normals
5. visibility/draw order
6. material/render state
7. fixed-camera pixel diff

Thresholds are stored in the Golden manifest and are adapter/version-specific. Visibility, topology, draw-group assignment, and material identity SHOULD be exact. Floating geometry/normal/pixel tolerances MUST be explicit rather than hidden in code.

Model Fidelity and Render Fidelity are reported separately.

## 17. Strict offline CI

At least one CI job MUST run with no accessible Minecraft installation.

The test environment MUST prevent accidental dependency on:

- `.minecraft`
- `.minecraft-simlab`
- YSM installation
- Forge installation
- Minecraft client jar

The job MUST cover at minimum:

- Render Pack schema/hash load
- mesh/material/texture load from pack only
- authoritative replay fixture
- Offline Emulator fixture where bundle exists
- Golden replay/verification fixture
- static scan or runtime guard against forbidden Viewer paths/imports

Any reintroduction of `.minecraft`/client-jar reads in Viewer runtime MUST fail CI.

## 18. Migration mapping

Existing assets are retained and reassigned:

- `SimVertexRecorder` -> Golden Oracle / final-vertex capability
- `SimModelDump` -> RenderMeshIR/asset compiler input
- `SimPaletteTrace` -> legacy measured capture; superseded by final matrix capture
- `livePalette` -> legacy transport; converted before Thin Viewer
- `ysm.js` -> Offline YSM Emulator
- `gl.js` -> split into generic Thin Renderer plus source-selection/UI layers
- `serve.mjs` -> source `.minecraft` access moves to compiler/capture side; runtime server serves Render Packs/frames only

## 19. Implementation PR sequence

PR1. Render Pack v1 and IR contracts
PR2. Self-contained asset compiler
PR3. Final matrices + full RenderFrame capture
PR4. Thin Render IR Viewer
PR5. Offline YSM Emulator isolation
PR6. Golden Oracle + fidelity verifier
PR7. Strict offline CI + adapter extensibility + final migration cleanup

Each PR MUST be focused, preserve a runnable migration path where practical, include tests for its new contract, and must not claim full completion until PR7 final regression satisfies all workflow DoD items.

## 20. Non-negotiable invariants

1. Minecraft is compiler/teacher, never a Viewer runtime engine.
2. Viewer understands KNEEKURA IR, not YSM semantics.
3. Runtime and emulator produce the same RenderFrameIR shape.
4. Authoritative data is never silently contaminated by prediction.
5. Final matrices are preferred over TRS reconstruction.
6. Final vertices are an authoritative fallback/oracle, not a reason to duplicate every frame unnecessarily.
7. Textures/material state are pack data, not runtime `.minecraft` lookups.
8. `partialTick` and every render invocation matter.
9. Visibility is captured as result, not inferred by the Viewer.
10. Model Fidelity and Render Fidelity are separate measurable contracts.
11. Pack/layout hash mismatch is a hard error.
12. Offline CI is the enforcement mechanism for the Minecraft-free runtime promise.