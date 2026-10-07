# Tank observation and camera usability

2026-10-08. Status: **WRITTEN_DESIGN_REVIEW_PENDING**. User authorized implementing feedback before continuing NaturalGhast; implementation details below require review because they add cross-layer observation/camera contracts. English compression is intentional. Source baseline: Tech Hub `7006c51`; NaturalGhast `06686d9`, product/JAR source `182fcb7`. No runtime implementation is claimed by this document.

## Outcome and protected behavior

AI can enumerate a bounded Tank's residents with world/local xyz and body bounds, plan a feasible requested view, retrieve verified images/state/restoration together, and inspect a freely moving Ghast without constraining its approved region. NaturalGhast is also an acceptance fixture for Tank usability. User explicitly accepts the current broad retained-region movement; leave its AI, region, physical controller, balance and production JAR unchanged.

Preserve original/finalized saves, existing owner/material/lease checks, failed receipts, single physical velocity writer and zero default image history. No dependencies, fake-player MOD, chunk force-loading, continuous recording, published/multiplayer server support or implicit world/entity mutation. Work in the existing clean camera worktree; mirror only requested English guides/feedback to the original dirty checkout.

## Grounded findings

- `ObserveFlightTank.java` measures one Ghast UUID, not a room roster. Forge Arena preflight only rejects unexpected occupants in its small action AABB. Legacy `/api/entities` returns summonable types, not current entities.
- Cardinal v1 derives poses from action-Arena bounds. For the current native `[7,224,6]`..`[13,235,13]` Arena, its formula yields north `(10,232.25,-3)` and west `(-2.5,232.25,9.5)`, outside the physical room `[0,224,0]`..`[52,248,52)`. This is a reproducible source-geometry mismatch, not a native image verdict.
- `KneekuraDebugMobPovOwner.mob` requires the registered Mob's base position inside action bounds. A freely swimming Ghast can leave them even while safely inside its Tank.
- `KneekuraDebugMobPovCamera` requires a spectator observer. The private owner rejects published integrated servers. Changing the only real Player to spectator removes the combat target; a second LAN client cannot be used under this owner. Existing v1 cannot certify a live Player-engaged Ghast just by changing the fixture species.
- Existing async immutable operation receipts, canonical frames, raw-PNG readers, camera ownership/restoration and finalized export are reusable. Current Python/Node exact shapes and complete module pins require explicit cross-layer updates, not an isolated helper that bypasses them.

## Approach and alternatives

Recommended: add a sealed read-only observation scope alongside the unchanged action grant, then reuse the native camera/evidence pipeline with explicitly versioned rigs. Smaller alternative: docs/readers only; this leaves whole-room discovery, scope exits and spectator/target conflict unresolved. Larger alternative: separate observer client/new control server; rejected for this iteration because it adds runtime/dependencies and conflicts with the private integrated-server boundary.

## A. Sealed Tank observation scope

Optional private owner registration `tankObservation` has exact fields: `schemaVersion:1`, `scope:TANK_OBSERVATION_READ`, `dimensionId`, integer `min`/`max`, `recipeHash`, `maxEntities`, `maxSamples`. World registration explicitly grants `TANK_OBSERVATION_READ`; camera modes still require their independent existing camera permissions. Owner preparation derives/verifies bounds and recipe hash from the actual saved marker. Edges1..64, volume≤65536, valid world height; `maxEntities`1..64, `maxSamples`1..8. Reject a scope unrelated to that private Tank.

Seal `control/owner-tank-observation.json` and bind its hash in the owner envelope/snapshot. Python/Node/JVM agree on optional fields, permission whitelist and limits. Old registrations without this option retain existing behavior. Fresh complete module pins are mandatory after source changes; old pinned sources are not silently upgraded. Before and after each native read, revalidate current owner/world/material/scope/lease on the server thread. Observation bounds never authorize block operations, entity teleportation, cleanup or expanded action Arena.

## B. On-demand room roster

Add `tank-roster --registry CONTROL --request-hash HASH --sample-index I` and `inspect-tank-roster` for immutable sequential slots0..7 within the declared sample budget. Publication is a request, not a measured result. Inspection reconciles the original slot; unknown outcomes cannot be replayed at another index. No timer or background sampler.

One server-thread snapshot emits `TANK_ROOM_ROSTER` through the existing canonical evidence writer plus bounded operation receipt. Payload binds run/process/request/Arena/scope hash, dimension, world/local origin/bounds, server tick/gameTime, loaded-chunk coverage, enumeration/byte/depth limits and truncation. Each row includes UUID/type, base world xyz, derived local xyz, AABB, living/mob/player flags, known subject ID when applicable, and passenger/vehicle references. Unexpected residents are visible, not deleted or registered automatically.

Include entities whose AABB intersects the observation volume, even with a base point outside it. Use loaded entities only; inspect intersecting chunk availability without loading. Bound collection to `maxEntities+1`, deduplicate passengers with depth≤8 and the same total budget. Retain actual sampled numbers; do not manufacture interpolated positions. Sort retained rows by UUID for deterministic display. Missing chunks, excess entities/depth or a64KiB packet limit produce explicit partial/truncated coverage; no missing row can imply absence. Complete means complete **loaded-scope** enumeration at that tick, not unloaded/global knowledge.

A derived roster/map view reuses existing fixed X/Z and elevation conventions and adds explicit world/local coordinates, AABB/boundary flags and source tick. It does not invent walls, paths, target sensing or continuous motion. Saved/offline inventory remains a separately labeled source.

## C. Camera plan and capture bundle

Add read-only `camera-plan` over the prepared request/current bounded owner observations: rig, exact subjects/revision, physical/read/action bounds, per-direction predicted pose/FOV/viewport, available declared slots, budget/freshness and known/predicted occlusion. Historical or absent scene data remains UNKNOWN; planning neither consumes image slots nor grants authority. A pose outside the physical room is a measured geometric condition; predicted visibility is not a pixel observation.

Keep existing `request-capture` semantics. Add `inspect-capture` and `capture-bundle` keyed to its original slot. Bundle verifies canonical manifest, frame order/identity, raw PNG content/hashes, sampled subject state and observed restoration. Return stable image/state references with COMPLETE/PARTIAL/UNKNOWN and per-view limitations. Any bounded foreground wait is≤10s; timeout stays pending/unknown without issuing another request. Missing/late frames retain their original outcome. Optional self-contained contact-sheet HTML is a derived artifact outside retained runs, generated only when requested; raw originals remain authoritative.

Selected-subject facts from the frozen capture share its actual barrier tick. A separately requested roster is labeled with its own tick and must never be presented as synchronized. No second canonical store, screenshot fallback or rewritten sealed receipt.

## D. Fixed views inside the observation room

Retain `cardinal-4-snapshot-v1` and its exact pose/manifest contract. Add explicit `tank-cardinal-4-snapshot-v2`, still four sequential raw native frames with pause/server hold, declared four-image cost and restoration. It requires the sealed observation scope plus `CARDINAL_CAPTURE_PAUSE_CAMERA`.

Derive deterministic north/east/south/west eye poses from observation bounds: center height, horizontal1.5-block wall inset, inward facing toward room center. Reject insufficient room size or unloaded/blocked camera positions; do not clear blocks or teleport subjects. FOV/viewport are fixed registered inputs in existing bounds, not dynamically changed to force acceptance. Preflight reports predicted frustum coverage of selected AABBs; partial framing/occlusion remains explicit. Current52×24×52 fixture starts with FOV90 and actual640×480 viewport, subject to native readback rather than guessed settings.

Versioned validators/metadata bind the observation-scope hash, actual poses/matrices, state hash and restoration. Reuse the detached camera, calibration, render stage, bounded worker and shared camera claim. Do not reinterpret v1 manifests as v2 or call paused images live monitoring. A live fixed-camera mode is deferred.

## E. Practical moving-Ghast eye view

Retain spectator-only `mob-eye-live-v1`. Add opt-in `mob-eye-observe-v2` using the same native camera claim/render/restoration mechanism, while the actual local Player remains in its existing game mode. This is a spectator-style eye presentation, not a server game-mode change. Require both sealed observation scope and `MOB_POV_CAMERA`; attach only exact registered living Mob UUID/type/dimension, fully within observation bounds. Without new scope, v1 keeps its old bounds rules.

Do not alter Player/Mob transforms, target, input state, health, physics or AI. Preserve the local Player as the boss's real combat target. Explicit return/expiry/owner/target/world loss detaches; external camera replacement is preserved. Human input ends the owned view and restores presentation where still owned, without suppressing normal input or rewriting resulting world state. Document that user input may affect the Player; do not claim zero observer effect.

Keep finite immutable command indices0..31, remaining-lease duration cap and zero default PNGs. Snapshot is optional and consumes one declared image. Raw metadata retains actual camera interpolation and asynchronous server reference, not same-tick AI sensing. Existing validatedAtNanos availability issue remains separately recorded; reject invalid evidence rather than relax identity/timestamp checks.

## Implementation seams

Python: `experiment_cli.py`, `experiment_control.py`, request/visual validators and related source-closure checks. Node: owner-prelaunch/control/grant transport, new focused observation/plan/bundle modules, existing raw readers/finalization and CLI/views. JVM: owner-input/gate/connection integration, bounded roster reader, camera policy/session/capture owner and MobPov owner/camera. Preserve existing styles and isolate new behavior behind registered options/rig versions; no broad refactor. Development-only native fixture/pilot adapters belong under LAB bridge/native or NaturalGhast tools, never its product JAR.

## Grouped verification and acceptance

1. Pure contract/unit checks: world/local xyz and AABB overlap; registered/unexpected Reimu; passengers/dedup/depth; unloaded/truncated/oversize; exact optional scope, replay/order/permission/hash/lease; old-registration behavior; identical Java/Node pose derivation; image completeness/restoration; user input/external camera; stale status and no unsolicited image writes. Add regressions for small-Arena scope exit and spectator/Player-target distinction.
2. Real mapped Forge compilation and actual API-boundary checks; Python/Node transport/source-closure/old v1 regressions. No assertions that mirror implementation without protecting these behaviors.
3. Fresh private native copies, committed exact unchanged NaturalGhast artifact and registered source. Roster sees one intended active Ghast, no unintended Reimu, and known saved others with accurate scope; a deliberately unexpected entity belongs only in a separate explicit test fixture. Retain camera plan and four-view v2 native images/state/restoration; image quality/visibility judged separately from math.
4. Moving-Ghast v2: survival target remains real/acquired, region generation/center and movement retain prior behavior; server ticks advance; camera follows actual moving subject; default PNG count0, one requested snapshot, explicit/expiry returns. Separate bounded fixtures exercise death/unload/input/external camera/world loss; pure coverage is not native acceptance. If a prerequisite cannot be established, record NOT_RUN/UNKNOWN, never substitute a frozen Reimu verdict.
5. Cleanup/camera quiescence, owned exit, evidence finalization/export and original85 raw hashes/count. Preserve failed trials, scope limits and exact producers; no repeated launch for an already explained human-camera intervention. Update guides/AF entries after coherent units. User's accepted Ghast movement is protected and does not certify every new Tank function.

## Work boundaries and review

Coherent units: (1) sealed observation/roster plus diagnostic views; (2) camera-plan/bundle and fixed v2; (3) moving-Ghast eye v2 and grouped native acceptance. A written implementation plan follows design approval and fixes exact files/order/checks before code. Native execution uses fresh fixtures; do not modify the user's existing/manual world. No push/merge/deployment or new dependency is included.

Self-review: no continuous capture or entity mutation; v1 remains distinct; read bounds do not grant writes; the true Player target is retained; missing/finalized evidence remains explicit; native limitations are not hidden. Trade-off: several additive contracts instead of a shortcut that shrinks the Ghast's region or removes existing checks. Roll back only the new opt-in route if authority/restoration/coverage cannot be established, retaining failure evidence.
