# Runtime final-vertex RenderFrame capture

This directory implements the PR-C boundary between a real Minecraft/YSM render invocation and the generic KNEEKURA RenderFrameIR.

## Two-stage trust model

A renderer-side capture is **raw evidence**, not automatically a replayable RenderFrameIR.

```text
actual YSM geoRender
  -> VertexConsumer tee
  -> raw final-vertex capture
  -> validate against one self-contained Render Pack
  -> require complete replay-critical draw/material state
  -> authoritative RenderFrameIR
```

The capture path never calls `render()` or `geoRender()` itself. It records the same VertexConsumer calls already being sent to the screen. The recorder copy removes only the observed outer PoseStack transform; it does not reconstruct YSM TRS, Molang, animation controllers, or Bedrock geometry.

## Raw vertex format

`KNEEKURA_FINAL_VERTEX_V2` stores 24 float32 values per emitted vertex, in source order:

1. position: x, y, z
2. uv0: u, v
3. normal: x, y, z
4. vertex color: r, g, b, a
5. overlay coordinates: u, v
6. packed light/lightmap coordinates: u, v
7. resolved overlay color: r, g, b, a
8. resolved lightmap color: r, g, b, a

The last eight values are captured from immutable snapshots of the live runtime auxiliary textures used by the same draw invocation. Overlay uses the exact integer UV1 texel and lightmap uses the exact integer UV2/16 texel rule of the pinned Minecraft 1.20.1 entity vertex shader. Those source-specific coordinate rules stop at capture time: the Thin Viewer receives only generic resolved RGBA attributes and never reads Minecraft overlay/lightmap textures.

The before/after texture snapshots must be byte-identical across the same `geoRender`. Any missing texture, ambiguous private `DynamicTexture` field, out-of-range texel coordinate, or changed snapshot discards the artifact. Primitive mode is stored per draw group. The raw capture does not triangulate or reorder the observed stream.

The outer `PoseStack` matrix is recorded separately as `modelToWorldMatrix`. Only the recorder branch applies its inverse so final vertices cross into KNEEKURA IR in posed model space. The real screen branch receives the original values unchanged.

The current capture also records the global RenderSystem shader RGBA multiplier observed immediately before the geoRender and requires the same value immediately after it. A change across the invocation fails closed. Mid-invocation global-state changes that are restored before return remain a real-client validation risk and are not claimed as solved by this PR.

## Promotion requirements

`compileFinalVertexRenderFrame()` promotes raw evidence only when all required facts can be verified.

It requires:

- explicit `tlm.sim.run` identity
- matching Render Pack `modelId`
- matching static draw group identity and RenderType provenance
- matching compile-time texture resource identity
- known primitive mode
- exact final-vertex V2 buffer byte length and finite float contents
- integer auxiliary sampler coordinates plus normalized resolved overlay/lightmap RGBA
- direct runtime auxiliary texture evidence with stable before/after snapshots
- safe regular files inside the capture root
- complete replay-critical MaterialIR state
- a valid Render Pack `packHash` and `layoutHash`

The real MaterialIR probe currently measures only the fields that can be proven directly. Therefore a real YSM raw capture may correctly remain **unpromoted** while alpha/blend/depth-write/emissive/sampler/tint state is still `UNKNOWN`. Raw evidence is retained; authoritative status is not guessed.

For `runtimeFinalVertex`, bone visibility is already resolved into the emitted geometry. The IR may therefore use an empty `visibility.bones` only together with `bonesResolvedInFinalVertices=true`. Group visibility, actual draw order, texture/material state, color multiplier, light, overlay, and primitive topology remain mandatory.

## Draw-call boundary guard

The current Render Pack v1 assigns one stable group to each captured RenderType. If one actual render invocation requests RenderTypes in a pattern such as `A -> B -> A`, merging by RenderType would destroy a real draw-call boundary. The renderer-side tee detects this non-contiguous re-entry and refuses the capture instead of silently reordering it.

## reimu-mod hook

The actual `EntityMaidRenderer` lives in the separate `reimu-mod` repository. Its integration is intentionally a tiny optional reflection bridge:

- no compile-time dependency on KNEEKURA-LAB
- normal gameplay passes the original `MultiBufferSource` through unchanged
- when the KNEEKURA capture bridge is present and explicitly requested, the existing single YSM `geoRender` receives the tee buffer
- no second render invocation is introduced

## Viewer boundary

Nothing in this directory authorizes the Viewer to execute YSM semantics. The Thin Viewer consumes only validated KNEEKURA IR. `ysm.js` and YSM controller/Molang knowledge remain research/emulator-side concerns.