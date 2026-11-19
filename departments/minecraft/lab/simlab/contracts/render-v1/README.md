# KNEEKURA Render Contracts v1

This directory is the machine-checkable boundary between capture/compiler code and the Thin Viewer.

## Contracts

- `renderpack-manifest.schema.json`: self-contained pack identity/provenance/files.
- `render-mesh.schema.json`: static mesh/skeleton/draw-group descriptor.
- `materials.schema.json`: explicit material/render-state descriptor.
- `render-frame.schema.json`: one render invocation with source authority, final matrices/final vertices, visibility, and draw state.
- `validator.mjs`: dependency-free semantic validation that JSON Schema alone cannot express.

## Deliberate v1 rules

1. Major schema mismatches are hard errors.
2. Pack and layout hash mismatches are hard errors.
3. `runtimeMatrix` is authoritative; `offlineYsmEmulator` is predicted.
4. A legacy TRS palette must be converted before the Thin Renderer.
5. An authoritative frame may not contain Molang/controller/Bedrock reconstruction payloads.
6. Pack-relative file paths may not escape the pack root.
7. Source fidelity ordering is explicit and testable.
8. Unknown material/render state remains the literal `UNKNOWN`; producers must not turn missing evidence into opaque/blend/cull/depth guesses.
9. Missing bind/inverse-bind matrices remain `null` only with explicit `*Authority: "UNKNOWN"` metadata.

## Local test

```bash
npm run test:contracts
```

No npm dependency is required.