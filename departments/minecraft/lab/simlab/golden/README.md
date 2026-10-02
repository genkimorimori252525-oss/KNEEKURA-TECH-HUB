# KNEEKURA Golden Oracle

Golden Oracle compares the final pixels produced by two independent paths:

1. the real Minecraft/YSM client, treated as the golden source
2. the KNEEKURA Thin Viewer, consuming Render Pack + RenderFrameIR

The comparator is intentionally independent from YSM semantics. It does not evaluate Molang, animation controllers, Bedrock geometry, or the legacy viewer/ysm.js emulator.

## Current scope

This first layer accepts:

- one real-client PNG
- one Viewer PNG
- the matching RenderFrameIR JSON metadata (required)

It produces:

- report.json
- report.md
- diff.png

The default gates are strict: every pixel and channel must match exactly.

Optional tolerances can be supplied for known rasterization differences, but the report always records the actual metrics. Tolerances therefore cannot hide a mismatch.

## Metrics

The report contains:

- total pixels
- identical pixels and identical ratio
- changed pixels
- mean absolute RGB error
- mean absolute alpha error
- maximum RGB channel error
- maximum alpha error
- silhouette mismatch pixels and ratio

Silhouette occupancy is derived from alpha. The alpha threshold is configurable.

The diff image stores amplified absolute RGB differences and marks changed pixels opaque. Identical pixels are transparent.

## Frame identity

The RenderFrameIR JSON file is mandatory. It is validated and the following identity is copied into the report:

- runId
- entityUuid
- renderSequence
- gameTime
- partialTick
- modelId
- packHash
- layoutHash
- source metadata

Input SHA-256 hashes are also recorded so a report can be tied back to the exact PNG and RenderFrame artifacts.

## What this does NOT prove yet

CI currently uses synthetic deterministic PNG fixtures. Therefore CI proves the comparator itself, not that the real YSM client and Thin Viewer are pixel-identical.

Real-client parity can only be claimed after a Windows/TLM run supplies:

- a deterministic real-client framebuffer PNG
- the matching authoritative RenderFrameIR
- a Thin Viewer PNG produced from that same frame/camera contract

Until those artifacts exist, KNEEKURA must say "Golden Oracle infrastructure passes" rather than "YSM pixel parity is proven".

## Real-client capture mode

The bridge now exposes:

    /tlmsim golden

Golden mode requires an explicit `-Dtlm.sim.run=<runId>`. It targets the nearest Reimu maid and attempts one isolated comparison frame.

The capture does not call YSM render a second time. It uses Forge render stages around the normal entity pass:

1. `AFTER_CUTOUT_BLOCKS`: save `background-before-entities.png` plus `background-before-entities.depth-f32le`
2. the existing YSM `geoRender` runs once and the final-vertex tee records the same draw stream
3. `AFTER_ENTITIES`: save `golden-after-entities.png`
4. only when camera/projection/framebuffer identity is stable and the raw final-vertex frame was attached is `capture.json` committed

The background color and depth are intentionally part of the evidence. The Thin Viewer must compose the matching RenderFrameIR over that exact color buffer while initializing depth from the captured float32 depth buffer; color-only composition is not evidence-grade because terrain occlusion would otherwise be lost.

Golden v1 fails closed unless:

- the camera is first-person
- no renderable entity other than the target Reimu and local player exists
- reimu-mod reports no visible chat bubble and no live SpellCircle, Somersault, or SwordSlash fallback state, including retained fade/trail state
- entity-dispatcher shadow and debug-hitbox rendering are suppressed only for the Golden frame and restored immediately afterward
- the target is rejected when Minecraft would draw a fire animation or glowing outline
- the camera, projection matrix, render tick, partialTick, framebuffer, viewport and window dimensions remain unchanged across the two stage boundaries
- the target YSM geoRender is actually observed in the same frame
- final-vertex raw capture completes
- pre/post screenshots have matching dimensions

The Node bundle loader additionally rejects:

- unbound run identity
- entity UUID mismatch
- missing YSM-only fallback-isolation proof
- partialTick mismatch
- unsafe/symlinked screenshot paths
- PNG dimensions that disagree with captured framebuffer metadata
- completely identical pre/post screenshots, because that means no entity framebuffer contribution was observed

The real-client bundle contains `background-before-entities.png`, `background-before-entities.depth-f32le`, `golden-after-entities.png`, final-vertex group buffers, and one `capture.json` tying them to the same run/entity/renderSequence/camera contract.

## Remaining real-client proof

CI still cannot prove real YSM pixel parity. The Java bridge is not compiled or executed against the user's live Forge/YSM installation in this repository.

A Windows/TLM run must still demonstrate that:

- `/tlmsim golden` produces the expected bundle
- the main render target at `AFTER_ENTITIES` contains the YSM contribution for the active graphics mode
- the real MaterialIR is complete enough for the raw frame to be promoted to authoritative RenderFrameIR
- the Thin Viewer can render that RenderFrameIR over the captured background
- the Golden Oracle comparison then passes the chosen gates

If a graphics mode renders entities into an auxiliary target that is not composited into the main target by `AFTER_ENTITIES`, the bundle loader should reject an unchanged pre/post image instead of treating it as proof.

Until a real Windows bundle exists, KNEEKURA must say "Golden capture/comparison infrastructure passes" rather than "YSM pixel parity is proven".

## Failure diagnosis

The intended debugging order is:

1. final vertices / draw stream
2. draw order and group visibility
3. texture and MaterialIR state
4. camera/projection/modelToWorld
5. final pixels

This lets a failed pixel comparison identify the first layer where the Viewer diverges from the real client instead of treating every visual mismatch as a shader problem.

### Isolation notes

PatPat pose scaling is allowed because it modifies the same PoseStack consumed by the captured YSM geoRender; the final-vertex recorder observes that transform rather than treating it as an independent post-process.

Arbitrary third-party listeners on `RenderMaidEvent` remain outside KNEEKURA's direct control. Real parity runs should therefore use the controlled sim profile. Golden v1 does not claim isolation from unknown third-party listeners that inject their own pixels before the YSM call.

## Bound oracle

`golden:compare-bound` is the evidence-grade comparator entrypoint. It refuses to compare pixels unless the RenderFrame carries a `goldenBinding` whose runId, entity UUID, renderSequence, gameTime, partialTick, render tick, framebuffer dimensions, camera pose/quaternion, projection matrix, and depth contract exactly match the real-client capture. Only after that binding passes does it run the strict Golden Oracle and write `binding.json` beside the normal report/diff artifacts.


## Windows headless Thin Viewer

`viewer:render-bound` renders one authoritative final-vertex RenderFrame over the exact captured pre-entity color + float32 depth buffers. The browser is only a thin WebGL2 execution surface: draw planning, shaders, material semantics and final-vertex validation come from `simlab/viewer/thin-final-vertex.js`.

The renderer never screenshots browser UI. It renders into an offscreen RGBA8 + DEPTH_COMPONENT32F framebuffer, reads the result with `gl.readPixels`, vertically normalizes the framebuffer rows, then uses KNEEKURA's deterministic PNG encoder.

On Windows the verified deterministic headless backend is ANGLE `d3d11-warp-webgl`, which rendered successfully through Microsoft Basic Render Driver on the self-hosted runner. `KNEEKURA_ANGLE_BACKEND` may override this for diagnostics, but evidence runs record the requested backend and actual WebGL renderer in `viewer-render.json`.

For one-command evidence collection, use:

```text
npm run golden:render-compare -- <capture-dir> <pack-dir> <frame.json> <viewer.png> <report-dir>
```

The command first renders the bound Thin Viewer frame, records the actual WebGL vendor/renderer/version in `viewer-render.json`, then invokes the bound zero-tolerance Golden Oracle and writes `pipeline.json`. A real pixel-parity claim still requires this command to pass against a real Windows/TLM Golden bundle; synthetic headless CI only proves the renderer path itself.
