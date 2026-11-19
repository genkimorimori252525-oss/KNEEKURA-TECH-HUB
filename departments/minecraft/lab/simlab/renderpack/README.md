# Render Pack compiler

PR-A introduces a Minecraft-independent compiler boundary for static render captures.

The compiler accepts an adapter-produced `kneekura.static-render-capture` object and writes a self-contained directory:

```text
<output>/<model-id>/<pack-hash>/
  manifest.json
  mesh/
    mesh.json
    mesh.bin
    skeleton.json
    groups.json
  materials/
    materials.json
  textures/
    <sha256>.<ext>
```

## PR-A rules

- Every non-empty draw group is first-class. The compiler never selects only the largest group.
- `order`, `sourceRenderType`, per-group material, and per-group texture assignment are preserved.
- Texture files are copied into the pack by content hash.
- `layoutHash` and `packHash` are deterministic.
- Pack-relative paths are validated and path traversal is rejected.
- A compiled pack is loadable after its capture directory is deleted.
- Missing render-state knowledge is stored as `UNKNOWN`; PR-A does not infer opaque/blend/cull/depth/emissive defaults.
- Missing bind/inverse-bind matrices may be represented as `null` only with explicit `*Authority: "UNKNOWN"` metadata.
- The current SimVertexRecorder stream exposes position/UV/normal/color but not source joints/weights, so those descriptors are explicitly marked unavailable instead of fabricated.

`loader.mjs` re-hashes every manifest-listed file and validates mesh/material contracts before returning a pack.

`dumpmodels-adapter.mjs` consumes the additive `renderGroups/v1` extension emitted by `SimModelDump`. `texture-resolver.mjs` is compile-time only: it resolves `ysm:`, mod assets, and vanilla client-jar texture bytes before packaging. Ambiguous YSM packs fail closed instead of selecting the first directory. The adapter labels this current path `runtimeVertexSnapshot`; it does not claim the unproven Hook-A `sourceInterpretedStaticMesh` authority.

## Tests

```bash
npm run test:renderpack
```

The fixture intentionally makes `body` the largest group and still requires `body`, `hair`, and `glow` to survive compilation. This is the regression guard for the old maximum-group-only behavior.

## Measured MaterialIR

The Forge bridge attaches a `material` object to each `renderGroups/v1` entry. The probe remains fail-closed: every field starts as literal `UNKNOWN` and is promoted only when its meaning can be demonstrated from the actual CompositeState.

Direct structural measurements:

- cull enabled -> `cullMode: "back"`; disabled -> `"none"`
- lightmap enabled/disabled
- overlay enabled/disabled
- depth-test function
- depth write, using constructor-calibrated `WriteMaskStateShard` booleans
- texture `bilinear` / `mipmap` flags, using constructor-calibrated `TextureStateShard` booleans

Standard Minecraft state calibration:

- the probe creates canonical 1.20.1 entity RenderTypes with a dummy texture
- observed transparency and shader shards are compared by **object identity**, not by RenderType/shader text
- standard no-transparency, translucent and additive transparency shards can therefore provide measured blend enable/factors/equation
- standard entity solid/cutout/translucent/translucent-emissive/eyes shader shards can provide an explicit `shaderProfile`, alpha mode/cutoff, emissive/fullbright flags and vertex-color participation
- `lightmap` means the RenderType enables Minecraft's lightmap state; `fullbright` means the canonical shader does not attenuate fragment color by lightmap input. Therefore 1.20.1 `entity_translucent_emissive` and `eyes` are fullbright while their measured lightmap participation is false
- `emissive` identifies canonical self-lit/emissive shader behavior; it does not imply depth writes or a specific blend mode
- custom or ambiguous shards remain `UNKNOWN` and cannot be promoted to authoritative replay

For translucent entity profiles, the alpha discard cutoff is preserved alongside `alphaMode: "blend"`; blend and discard are separate raster facts.

The runtime final-vertex stream already carries per-vertex RGBA, overlay coordinates and packed light coordinates, but this does **not** waive raster-state requirements. Blend, depth write, alpha discard, sampler state and the standard shader profile must still be measured before authoritative promotion.

Source RenderType/shard names remain provenance/debug text only. No `RenderType.toString()` or shader-name classification is used to derive render semantics.

This is intentionally separate from Viewer rendering. Minecraft/YSM are used only on the capture/compiler side; the Thin Viewer consumes explicit KNEEKURA MaterialIR and never executes RenderType/YSM semantics.