# Ages of Dominion — RTS client / UX technology deep dive — 2026-10-04

## 1. Scope

This is the client-side continuation of the source-backed Ages of Dominion v4.2.0 study.

Pinned upstream remains:

- repository: `NssIs/Ages-of-Dominion-ModJam-2026`
- revision: `c1e71a021ba88a053a378292c6011cb89828fd36`
- Minecraft: 26.1.2
- NeoForge: 26.1.2.87
- Java: 25
- license: All Rights Reserved for original upstream code/assets

This report does **not** copy upstream implementation into KNEEKURA. It extracts interaction,
rendering, scheduling and information-flow techniques for reconstruction.

Evidence labels:

- **DIRECT_OBSERVATION** — visible in the pinned source.
- **INFERENCE** — reusable engineering lesson derived from that implementation.
- **UNKNOWN** — not established by this pass.

Previous report:
[RTS-ARCHITECTURE-RESEARCH-2026-10-04.md](RTS-ARCHITECTURE-RESEARCH-2026-10-04.md).

## 2. Why this second pass matters

The first pass recovered command authority, worker FSMs, navigation, construction, economy and
siege logic. That explains how the simulation behaves, but not how Minecraft becomes usable as an
RTS.

The client bootstrap registers independent systems for:

- free RTS cursor and mouse ownership;
- isometric camera;
- box selection;
- world-to-screen projection;
- build ghost / building selection;
- minimap;
- natural-tree transparency;
- through-wall unit outlines;
- command-path feedback;
- vanilla-HUD suppression;
- responsive panel layout and GUI-scale protection.

The core lesson is that "RTS mode" is not one camera hack. It is a coordinated replacement of
Minecraft's first-person interaction contract.

## 3. Input ownership: decide once at press time

`RtsMouseController` receives the actual `InputEvent.MouseButton.Pre` press/release edge.

DIRECT_OBSERVATION:

- it does not infer the initial click from a later client tick;
- the **first button press** decides whether the whole hold belongs to HUD or world interaction;
- that decision is retained for the gesture instead of being recomputed as the pointer crosses HUD;
- all RTS-mode mouse presses are cancelled before vanilla can automatically grab the mouse and warp
  the pointer to the centre;
- the saved cursor position is restored when the RTS drag grab ends.

Locator:
- upstream `client/input/RtsMouseController.java#L198-L294`

The source comments record why: polling at tick/render cadence created races, and recomputing
"cursor over HUD?" during a drag caused camera movement to die when the drag crossed a bar.

**Technique:** gesture ownership is an edge-triggered state transition, not a continuously
re-evaluated hover property.

For KNEEKURA, define an explicit gesture owner such as:

`NONE | HUD | WORLD_CLICK | MARQUEE | CAMERA_PAN | CAMERA_ROTATE | BUILD_GHOST`.

Never let two consumers independently interpret the same held mouse button.

## 4. One left button, three world gestures

DIRECT_OBSERVATION:

- movement >= **6 GUI pixels** becomes marquee selection;
- if the pointer stays inside that movement threshold for **1000 ms**, the same held press may
  become camera pan;
- quick release below both conditions remains a normal world click;
- mouse grab begins only once pan/right-drag is active, not merely because a button is held.

Locators:
- `RtsMouseController.java#L33-L35`
- `RtsMouseController.java#L315-L363`
- `RtsMouseController.java#L417-L456`

The priority is effectively:

`pointer movement -> selection`
before
`long hold -> pan`
before
`release -> click`.

**Technique:** resolve ambiguous gestures by thresholds and latching, then emit one semantic action.
Do not have camera, selection and world-click systems all poll raw mouse state.

## 5. RTS mode is a complete input boundary

The mod does not merely hide the hotbar.

DIRECT_OBSERVATION:

- inventory/hotbar/offhand/drop/spectator-hotbar key presses are drained while RTS mode is active;
- inventory/container screens are blocked only while RTS mode owns input;
- screen/mode transitions clear transient RTS mouse edges;
- the custom RTS cursor is hidden/shown independently of mouse grab;
- cursor wrapping is allowed only while visible/free and no mouse button is held;
- RTS input is considered active only when both the synced RTS flag and spectator state agree.

Locators:
- `RtsMouseController.java#L370-L415`
- `RtsMouseController.java#L417-L529`
- `RtsMouseController.java#L534-L568`
- `RtsVanillaHudSuppressor.java`

**Technique:** changing visual HUD without changing input leaves invisible vanilla behavior active.
RTS conversion must handle rendering **and** queued key actions.

The transition guard is especially useful: client state can receive the RTS attachment and
gamemode in different packets, so checking both avoids a short window where RTS code steals a
vanilla click.

## 6. Isometric camera is still attached to a Minecraft player

DIRECT_OBSERVATION:

- tactical pitch is fixed at **60 degrees**;
- camera distance is clamped to **18..86** with default 44;
- keyboard and drag pan are expressed in camera-relative X/Z vectors;
- pan speed scales with zoom;
- wheel remains zoom even during building placement;
- normal mouse yaw is suppressed unless the right button is held.

Locator:
- `client/camera/IsometricCameraController.java#L25-L38`
- `#L72-L229`

This stays compatible with Minecraft's player-centric world model by moving the local player anchor
and separately controlling detached-camera distance/presentation.

**Technique:** separate:

1. **authoritative player anchor** — server-visible location used for chunk/range context;
2. **client camera transform** — visual pitch/yaw/distance;
3. **RTS cursor ray** — world ray reconstructed from the actual camera and free pointer.

Do not assume the first-person eye ray remains the interaction ray.

## 7. Terrain-following camera without a full vertical scan every tick

The camera anchor must avoid sinking into hills or snapping under terrain.

DIRECT_OBSERVATION:

- it samples a **13x13** `WORLD_SURFACE` heightmap window around the integer camera column;
- the cached window is rebuilt only when the anchor column/level changes;
- if the cheap height values are unchanged, the expensive terrain-Y scan is skipped;
- if values changed, the implementation scans downward from those heightmap tops to find terrain;
- the player anchor is kept two blocks above the recovered terrain surface.

Locator:
- `IsometricCameraController.java#L236-L310`

**Technique:** cache the cheap spatial summary that tells you whether an expensive geometric scan
can possibly have changed.

This generalizes to camera height, local nav diagnostics and tactical overlays.

## 8. One shared world-to-GUI projection

`RtsUnitScreenProjection` converts world coordinates with the current camera view-projection
matrix into GUI-scaled coordinates.

DIRECT_OBSERVATION:

- camera-relative world vector -> clip space;
- reject points behind the camera;
- divide by W -> NDC;
- map NDC into GUI-scaled screen coordinates;
- reject points well outside the screen.

Locator:
- `client/RtsUnitScreenProjection.java`

The same projection is used for drag selection and other unit overlays.

**Technique:** screen selection should share one projection contract with health markers / tactical
overlays. Separate projection implementations drift at unusual aspect ratios or zooms.

## 9. Marquee selection is screen-space, not world-volume selection

DIRECT_OBSERVATION:

- the selection rectangle is a GUI overlay;
- all currently renderable allied entities within **192 blocks of the camera** are projected into
  screen space;
- a unit is selected if its projected torso point is inside the rectangle;
- this box-selection path intentionally does not require line-of-sight.

Locators:
- `RtsUnitSelectionOverlay.java`
- `BuildingSelectionController.java#L441-L466`

Single-click selection is different: `BuildingRaycast.pickEntity` stops at the first non-faded
solid obstruction, so a click cannot normally select through a wall.

**Technique:** use different visibility semantics for precision click and strategic marquee.

- click = occlusion-sensitive
- marquee = screen-space strategic selection

This matches RTS expectations better than forcing both through the same ray rule.

## 10. Free-cursor world ray from inverse camera matrix

Minecraft's normal player ray is unsuitable once the pointer is free and the camera is detached.

`BuildingRaycast`:

1. inverts the camera view-projection matrix;
2. converts cursor screen coordinates to NDC;
3. unprojects near and far points;
4. builds a normalized ray from the actual camera;
5. extends it up to **256 blocks**;
6. runs vanilla voxel traversal.

Locator:
- `client/build/BuildingRaycast.java#L21-L123`

The ray treats only the currently-authoritative faded natural-tree positions as visual cover.
Ordinary structures, fluids and other blocks remain normal ray blockers.

**Technique:** the object that is visually transparent should have matching input semantics only
when that transparency was intentionally granted. Do not globally ignore all leaves/logs in
raycasts.

## 11. Contextual click is a two-stage command

A selected worker clicking world geometry is ambiguous:

- mine?
- farm?
- damaged building?
- active construction?
- tree?
- ordinary ground?

The client cannot safely identify every authoritative building from visual blocks alone.

DIRECT_OBSERVATION:

- client creates a `PendingOrder` containing selected entities + clicked position + movement target;
- client asks the server to resolve the tracked building at that position;
- when the response returns, the command is classified into repair/mine/farm/construction/tree/move;
- the same response explicitly reports whether it was **consumed by the pending unit command**, so
  it does not also become ordinary building-panel selection.

Locator:
- `BuildingSelectionController.java#L249-L429`
- `network/ClientPayloadHandlers.java#L93-L122`

**Technique:** asynchronous context resolution should have an explicit pending-intent object and an
explicit response-consumed result. One packet must not accidentally advance two client state
machines.

## 12. Destructive UI actions are bound to object identity

Building demolish uses a two-click confirmation window.

DIRECT_OBSERVATION:

- first click arms one exact building ID for **60 ticks**;
- second click must refer to the same selected ID while the window is live;
- changing selection re-arms instead of confirming;
- Town Hall deletion is rejected client-side before a request is sent.

Locator:
- `BuildingSelectionController.java#L45-L173`

Server authority still matters, but this eliminates a common UI failure: confirm-on-old-selection
after selection has changed.

**Technique:** destructive confirmation should bind to immutable object identity, not just
"confirmation mode is true".

## 13. Building preview is a compressed server-supplied shell

The client does not receive the full structure template for every tray icon/ghost.

DIRECT_OBSERVATION in `ModPayloads.buildPreview`:

- air is dropped;
- technical/invisible markers are dropped from preview;
- blocks fully enclosed on all six sides are dropped;
- visible preview blocks are capped at **2048**;
- palette is capped at **256** block IDs;
- each preview block is one 32-bit int:
  - x: 8 bits
  - y: 8 bits
  - z: 8 bits
  - palette index: 8 bits

`BuildingPreviewPayload` comments estimate about **8 KB** for the allowed worst case.

Locators:
- `network/ModPayloads.java#L169-L177`
- `network/ModPayloads.java#L1750-L1797`
- `network/BuildingPreviewPayload.java`

The server comment states shell culling is typically a **five- to ten-fold reduction** for solid
buildings.

**Technique:** send the representation needed by the UI, not the full gameplay object.

The authoritative server still validates placement against the real template, so preview
approximation cannot grant illegal placement.

## 14. One preview payload feeds multiple client products

The same `BuildingPreviewPayload` is consumed twice:

- tray/isometric building icon;
- world placement ghost / occupancy.

`BuildingPreviewShape` turns the payload into MapColor voxels and lazily caches occupancy per
rotation. A rotation map is computed at most once for each of the four rotations.

Locator:
- `client/build/BuildingPreviewShape.java`

**Technique:** decoded geometry should be a shared client cache. Do not make the icon renderer and
placement tool each fetch/parse the same structure.

## 15. Lightweight ghost instead of real block-model rendering

`BuildGhostRenderer` deliberately renders translucent per-block boxes rather than invoking the
full arbitrary BlockState rendering pipeline.

DIRECT_OBSERVATION:

- translucent boxes use each block's MapColor;
- boxes are slightly inset to avoid face z-fighting;
- path/wall preview gets bright ground rails;
- entire ghost turns red only for **geometry** errors;
- affordability/progression failures remain textual, because the geometry itself is valid.

Locator:
- `client/build/BuildGhostRenderer.java`

**Technique:** visual semantics should match error semantics. "Cannot afford" and "will collide"
should not be represented by the same red-world geometry if they mean different things.

Also: at RTS zoom, a low-detail massing model can convey placement more reliably and cheaply than
faithfully rendering every block model.

## 16. Client ghost is a courtesy; server revalidates real geometry

DIRECT_OBSERVATION:

- client uses shell-only preview occupancy to produce responsive green/red feedback;
- move/upgrade preview ignores the source building's own bounds;
- server placement handler reloads the actual structure and re-runs progression, cost and
  `BuildingPlacement.checkGeometry` from scratch.

Locators:
- `BuildGhost.java#L235-L390`
- `network/ModPayloads.java#L337-L344`

**Technique:** share the validation rules when possible, but never elevate a client preview
approximation into authority.

## 17. Minimap is an incremental scrolling cache

`RtsMinimap` is not rebuilt whenever the camera moves.

DIRECT_OBSERVATION:

- texture: **256x256**;
- coverage: **256x256 world blocks / 16x16 chunks** at one block per pixel;
- origin snaps to chunk boundaries;
- crossing a chunk boundary scrolls the existing pixel/height buffers;
- only newly exposed bands become unknown;
- newly exposed budget: **2 chunk cells per client tick**;
- background refresh: every **10 ticks**, **2 cells**;
- texture upload cooldown: **2 ticks**;
- only dirty row range is copied into the NativeImage before upload.

Locator:
- `client/ui/RtsMinimap.java#L47-L159`
- `#L183-L305`

**Technique:** preserve spatial cache continuity when the viewport moves. Shift old data and compute
only the newly visible strip.

This is useful for any scrolling tactical map or heatmap.

## 18. Minimap fog uses actual client chunk availability

The minimap does not calculate a theoretical render-distance circle.

DIRECT_OBSERVATION:

- `ClientChunkCache.getChunk(..., false) == null` is treated as fog;
- unloaded cells are still marked "sampled", preventing the priority loop from retrying permanent
  outer fog cells forever;
- a slow cyclic refresh later catches chunks that become available;
- loaded/unloaded boundaries are feathered toward fog;
- terrain uses MapColor plus vanilla-style north-neighbour height brightness;
- tactical dots are drawn from currently loaded entities.

Locator:
- `RtsMinimap.java#L317-L455`
- `#L495-L575`

The current side panel deliberately consumes minimap clicks. `screenToWorld` exists, but current
minimap navigation is **informational**, not a camera-teleport control.

**Technique:** unavailable data should have its own state and retry policy. Do not let permanently
missing cells starve available work.

## 19. Natural-tree transparency is a bounded corridor effect

The solution to "camera is inside/behind foliage" is not "make all leaves transparent".

DIRECT_OBSERVATION:

- only active at close zoom (camera distance <= **32**);
- scans the camera-to-player segment;
- corridor radius: **1.65 blocks**;
- sample step: **0.65**;
- max samples: **64**;
- aggregate faded block cap: **8192**;
- scan cadence: every **2 ticks**;
- motion during cooldown is coalesced to the newest camera/player endpoints;
- only complete recognized natural-tree components are admitted;
- when the set changes, only render sections containing changed membership are dirtied.

Locator:
- `NaturalTreeTransparencyController.java`

**Technique:** visibility assistance should target the actual occlusion corridor, not alter the
entire world.

## 20. Fading preserves the real tree mesh

`SectionCompilerMixin` does not replace the tree with a simplified fake.

For positions in the fade set it:

- avoids marking the faded tree opaque in the chunk visibility graph;
- renders the same block model while a thread-local "faded mesh" scope is active;
- routes that model into the translucent chunk layer;
- multiplies the baked quad colour/alpha (opacity 0.33).

Locator:
- `mixin/SectionCompilerMixin.java`

**Technique:** visual state can be expressed as a rendering-layer/material transform on the
existing geometry, preserving shape while changing occlusion.

The thread-local scope prevents unrelated block compilation from inheriting the faded layer when
section compilation happens off the main interaction code path.

## 21. Through-wall outline is only a fallback for true occlusion

A tactical outline is not permanently painted on units.

DIRECT_OBSERVATION:

- samples feet, torso, head and left/right torso positions;
- if **any** sample has a clear ray to the camera, no through-wall outline is added;
- outline appears only when all sampled points are hidden;
- intentionally invisible mine workers are excluded.

Locator:
- `client/RtsUnitThroughWallOutline.java`

**Technique:** "unit partly obscured" and "unit lost behind geometry" are different states. Use
outlines only for the latter to avoid visual noise.

## 22. Command breadcrumbs show intent, not fake navigation truth

`RtsUnitPathState` / `RtsUnitPathRenderer` do not mirror the server's real Path.

DIRECT_OBSERVATION:

- after an issued order, client stores only unit ID + destination + expiry;
- visible lifetime: **9 seconds**;
- straight line from unit to requested target;
- waypoint spacing: **2.4 blocks**;
- max markers: **64**;
- removed when destination is reached, unit dies/disappears or timer expires.

Locator:
- `client/RtsUnitPathState.java`
- `client/RtsUnitPathRenderer.java`

**Technique:** explicitly label a visualization by what it knows.

This is **command intent feedback**, not a path debugger. That is often preferable for normal
players: it confirms "where I told them to go" without pretending the client knows the
server's future route.

KNEEKURA's technical LAB path renderer should remain separate from this user-facing intent layer.

## 23. HUD replacement is rendering plus behavior suppression

`RtsVanillaHudSuppressor` removes:

- ordinary hotbar;
- spectator teleport bar;
- selected-item label;
- XP level;
- crosshair.

It intentionally keeps vanilla overlay messages and moves their vertical anchor above the RTS
bottom bar.

Separately, `RtsMouseController` drains the key actions that would still modify/drop inventory
behind a hidden HUD.

It also temporarily disables Minecraft's first-person movement tutorial and restores the previous
tutorial setting when RTS mode ends.

**Technique:** when replacing a UI metaphor, remove its behavioral affordances as well as its pixels.

## 24. Responsive RTS panels without stretching source art

`RtsPanel` slices its panel art into top/middle/bottom/side rails and tiles the middle rather than
stretching one giant background image.

Notable details:

- tiles can overrun and are clipped with scissor instead of being squeezed;
- tile phase is locked to screen origin so adjacent panels share one continuous pattern;
- edge flags allow stacked panels to omit internal rails;
- top/bottom rails retain proportions even for very short panels.

`HudScale` uses one uniform transform for content and background band and applies the exact same
derived size to hit testing.

Locator:
- `client/ui/RtsPanel.java`
- `client/ui/HudScale.java`

**Technique:** visual scale, layout scale and input hitboxes must come from one geometry model.

## 25. GUI scale is treated as an operating condition

The authored HUD targets GUI scale **2**.

`RtsGuiScaleGuard`:

- applies scale 2 the first time RTS mode is entered when current scale is Auto or >2;
- later changes above 2 produce a warning;
- user can explicitly continue at their own risk;
- cancel reverts to a safe value.

Locator:
- `client/RtsGuiScaleGuard.java`

**Technique:** a dense tactical HUD should either be fully responsive across all scales or state its
supported scale envelope explicitly. Silent clipping is worse than a transparent compatibility
warning.

## 26. Additional recovered techniques for KNEEKURA

The second pass adds these reusable items beyond the original AI/worker report:

1. **Gesture ownership latch** — classify HUD/world at press edge and keep ownership stable.
2. **Semantic gesture arbitration** — click vs marquee vs pan thresholds.
3. **Free-cursor grab suppression** — stop vanilla mouse capture before it warps the pointer.
4. **Hard RTS/vanilla input boundary** — clear queued edges on mode/screen transitions.
5. **Shared world-to-GUI projection** — one contract for selection and overlays.
6. **Different occlusion semantics for click vs marquee**.
7. **Free-cursor inverse camera ray** — interaction originates from tactical camera, not player eye.
8. **Pending contextual order state** — server-resolved world object chooses the final command.
9. **Identity-bound destructive confirmation**.
10. **Shell-only preview transport** — send visible UI geometry, not the full structure.
11. **Packed preview voxels + shared block palette**.
12. **Shared decoded preview cache** — tray and ghost use one payload.
13. **Low-detail massing ghost** — clarity/portability over full BlockModel fidelity.
14. **Client courtesy validation / server real validation**.
15. **Scrolling minimap cache** — shift old pixels instead of rebuilding.
16. **Priority + background map sampling** — missing regions cannot starve loaded regions.
17. **Dirty-row texture upload**.
18. **Bounded close-zoom occlusion corridor**.
19. **Render-layer tree fade using original mesh**.
20. **Only-changed-section invalidation**.
21. **Multi-sample true-occlusion outline**.
22. **Intent breadcrumbs distinct from path debugging**.
23. **Rendering suppression + input suppression as one UI replacement contract**.
24. **Tiled/scissored scalable panel system**.
25. **GUI-scale compatibility guard**.

## 27. 1.20.1 Forge reconstruction notes

The concepts are portable; the exact hooks are not.

Potential 1.20.1 rewrite boundaries include:

- camera distance/angle hooks;
- mouse input interception semantics;
- modern `GuiGraphicsExtractor` / render-state APIs;
- modern chunk section compiler pipeline and `QuadInstance`;
- current payload codec/registrar APIs;
- current camera view-projection access;
- NeoForge UI layer events.

For KNEEKURA's Forge 1.20.1 target, reconstruct the contracts first:

- `GestureState`
- `TacticalCameraTransform`
- `WorldScreenProjection`
- `CursorWorldRay`
- `SelectionIntent`
- `PendingContextCommand`
- `PreviewGeometryCache`
- `TacticalMapCache`
- `OcclusionAssistSet`

Then map each contract to actual Forge 47.4.x/Minecraft 1.20.1 APIs.

Do not copy the current 26.1 implementation mechanically.

## 28. Boundaries / non-findings

- The minimap has an inverse `screenToWorld` helper, but current side-panel behavior consumes map
  clicks and does not use it for camera movement.
- Command breadcrumbs do not prove or expose the actual server navigation route.
- Box selection includes strategically visible/rendered units behind walls; single-click does not.
- Tree fading is natural-tree-specific, not a general building-roof transparency system.
- No runtime FPS/CPU/GPU benchmark was performed.
- The upstream code remains All Rights Reserved.
- No native Forge 1.20.1 version was found.

## 29. Primary upstream files

Pinned revision:
https://github.com/NssIs/Ages-of-Dominion-ModJam-2026/tree/c1e71a021ba88a053a378292c6011cb89828fd36

Key files:

- `client/input/RtsMouseController.java`
- `client/camera/IsometricCameraController.java`
- `client/RtsUnitScreenProjection.java`
- `client/ui/RtsUnitSelectionOverlay.java`
- `client/build/BuildingRaycast.java`
- `client/build/BuildingSelectionController.java`
- `client/build/BuildGhost.java`
- `client/build/BuildGhostRenderer.java`
- `client/build/BuildingPreviewShape.java`
- `client/ui/RtsBuildingPreview.java`
- `network/BuildingPreviewPayload.java`
- `network/ModPayloads.java`
- `client/ui/RtsMinimap.java`
- `client/NaturalTreeTransparencyController.java`
- `mixin/SectionCompilerMixin.java`
- `client/RtsUnitThroughWallOutline.java`
- `client/RtsUnitPathState.java`
- `client/RtsUnitPathRenderer.java`
- `client/ui/RtsVanillaHudSuppressor.java`
- `client/ui/RtsPanel.java`
- `client/ui/HudScale.java`
- `client/RtsGuiScaleGuard.java`
