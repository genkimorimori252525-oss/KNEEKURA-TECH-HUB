# Tank operation for AI agents

2026-10-08. Read with [Project Guide](PROJECT-GUIDE.md) and [AI Feedback](AI-FEEDBACK.md). Use the integrated `departments/minecraft/lab`; the standalone LAB is historical. Minecraft supplies actual runtime/render evidence; browser diagrams interpret retained samples.

Reconciled the user-provided [older guide](https://chatgpt.com/space/page_83f4ca35a65c81919f1b0b9eca36ff76) and its MD export (SHA256 `e42296a4295260bc1eefa85fe68d3a9f46ad78f8f7befc1561df87bb12580c43`) against local camera-branch source `97a130f`. Older source pins `c369953`/PR96 `6b745627` remain historical, not reset instructions. Select matching Python/LAB/MOD source and repin materials before execution; the original dirty checkout lacks these runtime tools. Documentation availability is not installation or runtime acceptance.

## Choose the observation

| Need | Existing path | Limit |
| --- | --- | --- |
| Motion/AI diagnosis | Exact UUID server state, finite motion/Decision evidence | Sampled facts; private AI may be NOT_EXPOSED |
| Spatial review | Workbench X/Z and tick-vs-Y; Decision fixed-isometric view | Derived diagrams, not new native cameras or complete room roster |
| Frozen appearance | Registered `cardinal-4-snapshot-v1` | One detached camera; four sequential native frames; pause/server hold; explicit restoration |
| Live mob-eye inspection | Registered `mob-eye-live-v1` | Spectator observer, finite lease; zero default PNGs; optional explicit snapshot |
| Human movement review | Manual Player camera | Human observation; DEBUG0/no observer launch has no current canonical telemetry |

Use structured evidence first, then requested diagrams/images. Physical room, presentation grid, action Arena and combat region can have different bounds. An image, selected UUID trace or action-AABB occupant guard cannot establish every room resident. The whole-room on-demand live roster remains AF-0017's recorded gap. Legacy `/api/entities` lists summonable entity types from `entities.json`, not living occupants and their coordinates.

## Prepare one coherent experiment

1. State intended change, protected behavior and acceptance scope. Implement a coherent work unit, then group relevant checks; add earlier checks when failure would compromise safety or invalidate the unit. NaturalGhast is also a Tank usability trial: record friction and useful missing capabilities even when the MOD succeeds. Prioritize observed defects before further tactics/danmaku.
2. Use the official world authority's **fresh private copy**, consistent source snapshot and source/copy inventory hashes. Preserve old/failed runs. Never open an original or finalized save with Minecraft `RegionFile`; inspect another disposable copy. Never open one save with two Minecraft processes. Read the actual saved `kneekura-tank-owner.json` and fixture changes; historical19×11×19 is not a universal limit. Reimu dependencies are not mandatory Reimu residents.
3. Declare dimension, physical origin/extent, intended/unexpected residents, UUID/type/base position/AABB, and coverage (saved versus loaded/live, unknown or limited). Current NaturalGhast manual interior cells are `[0,224,0]`..`[52,248,52)`, so local `(x,y-224,z)`; initial saved poses are not current positions. Verify a 4×4 Ghast's body clearance, not its base point alone.
4. Bind source/material/world/request/assertion/run/snapshot/process/Arena identities and target revision. Prepare immutable owner/control, declared action/capture slots and finite budget before launch. Lease expiry, launch timeout and sampled tick are distinct clocks. Registration alone does not launch, install a live owner or establish READY.
5. Use Minecraft Java1.20.1/JDK17 and source-compatible Forge. Select `KNEEKURA_DEBUG_MOD_PROFILE=TANK_CORE`; `FULL_COMPAT` changes inputs. `FAST_DEBUG` is separate, not a MOD filter. Inspect actual loaded MODs/external JARs/init scripts. NaturalGhast's established host uses Forge47.4.10; its older47.2 host cannot load the target constructor API.
6. Keep `gameDir` equal to Forge `workingDirectory`, using a private init script and new registrations after path/hash changes. Use measured low-latency storage with adequate capacity. Keep daemon/incremental compilation; avoid routine `clean` or `-x compileJava`. Keep Decision hooks/motion overlays OFF unless required. No automatic image history or recording.

All Node commands below run from the selected LAB subtree. Uppercase values are verified caller inputs, not usable credentials/IDs. `kneekura-minecraft` is that source's Python console entry; alternatively use `python -m kneekura_tech_hub.minecraft` with that checkout's `PYTHONPATH=src` and dependencies.

```text
node debug-workspace/cli.mjs doctor --config CONFIG
node debug-workspace/cli.mjs start --config CONFIG
node debug-workspace/cli.mjs status --config CONFIG
node debug-workspace/cli.mjs timeline --config CONFIG
```

Use the applicable `config.tank-core.example.json`/`config.fast-iteration.example.json`/`config.official-tank.example.json`; adapt to the private copy, preserving `requireExistingWorld` and `requireGitIdentity`. Require actual handshake/READY, exact identity and owned process, not just an open window. [Fast iteration](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/lab/docs/KNEEKURA_TANK_FAST_ITERATION.md).

## Grid, brightness and geometry

The one-block grid is a client renderer. A registered resource ZIP's `kneekura/tank-presentation.json` must match the private saved recipe/hash and finite scoped owner. `OBSERVATION_BRIGHT` modifies the client lightmap, not lamps/server light/physics/Night Vision. `NATIVE` still draws the grid; grid OFF uses a newly registered resource without the capsule. Expired/mismatched ownership can disable presentation; draw submission does not prove visible pixels. Manual Night Vision is a separate fixture change.

Explicit profile example: `{"kind":"OBSERVE_GRID","grid":true,"brightness":true,"motion":false,"decisionChannels":["SERVER_ENTITY_STATE"]}`. Example budget: `{"experimentMs":30000,"finalizationMs":5000,"cleanupMs":5000,"marginMs":5000}`. Generate exclusively outside retained runs, then register the resource hash before owner preparation:

```text
node debug-workspace/cli.mjs tank-resource --config CONFIG --saved-recipe MARKER.json --profile PROFILE.json --output NEW_RESOURCE.zip
node debug-workspace/cli.mjs tank-status --config CONFIG --arena-epoch N --recipe-hash RECIPE_HASH
node debug-workspace/cli.mjs tank-preflight --config CONFIG --arena-epoch N --recipe-hash RECIPE_HASH --profile PROFILE.json --time-budget BUDGET.json
```

Preflight requires fresh matching evidence/remaining budget; it neither grants authority nor renews a lease. [Presentation contract](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/lab/docs/KNEEKURA_REGISTERED_TANK_PRESENTATION.md).

Registered pre-experiment rotation uses a separate maintenance owner to create/verify/save a disjoint empty region, preserving old regions. Integer edges1..64, inner volume≤65536; unloaded/nonempty/unsafe scope is rejected. Success closes the old owner; a fresh run/capsule binds the new saved epoch/recipe. Interrupted rotation remains UNKNOWN for reconciliation, not blind retry/reservation deletion. This is not live resize/full-state reset. NaturalGhast's offline new-copy fixture preparation is a separate explicitly recorded path. [Rotation contract](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/lab/docs/KNEEKURA_REGISTERED_TANK_ROTATION.md).

## Select, inspect and retrieve

```text
node debug-workspace/cli.mjs target UUID --decision-snapshot --config CONFIG
node debug-workspace/cli.mjs target-status --config CONFIG
node debug-workspace/cli.mjs evidence-status --config CONFIG
node debug-workspace/cli.mjs evidence-entity UUID --config CONFIG
```

Omit `--decision-snapshot` for ordinary selection. Clear/reselect changes context. Forward-filled state is not a new sample; never connect gaps, teleports, deletion or dimension/identity/run/process/Arena/selection boundaries. Actual movement and declared navigation remain separate. Trail colors/fading are presentation, not collision/hit/causality; inspect timestamps and retained data after trails expire. Optional hooks need explicit launch configuration and bounded selection.

**Cardinal:** use already prepared scoped control and declared capture index; each slot consumes four images. Check each view's visibility/occlusion, exact UUID/revision/identity, frame order, actual pose/matrices/FOV/viewport/ticks, raw PNG hashes, completeness and observed restoration. v1 poses derive from registered action Arena bounds and can sit outside opaque room shells. Explicit `tank-cardinal-4-snapshot-v2` instead derives inward eye poses from a separately sealed Tank interior. Mouse/keyboard interference can invalidate capture; preserve that trial. No simultaneous-four-camera or zero-observer-effect claim.

```text
kneekura-minecraft experiment inspect-control --registry CONTROL.json
kneekura-minecraft experiment inspect-owner --registry CONTROL.json --request-hash HASH
kneekura-minecraft experiment request-capture --registry CONTROL.json --request-hash HASH --capture-index 0
```

Transport receipt alone is not image completion. `evidence-capture` retains structured pre-roll, **not a native screenshot**. Event-driven images require a separately armed typed-event watch/reserved slots; missing pre-event frames stay NOT_CAPTURED. [Capture contract](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/lab/docs/KNEEKURA_CARDINAL_CAPTURE_SOURCE_20261001.md), [scoped controls](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/mod-ai/LAB-SCOPED-CONTROL.md).

**Mob POV:** private integrated server, spectator observer, loaded registered Mob, `MOB_POV_CAMERA`, matching immutable rig and actual viewport, finite lease. `max_captures:0` is view-only;1..16 allows requested PNGs. Wait for each immutable receipt before the next index (0..31); inspect UNKNOWN at its original index instead of resubmitting elsewhere.

```text
kneekura-minecraft experiment mob-pov --registry CONTROL.json --request-hash HASH --command-index 0 --camera-operation attach --subject-uuid UUID --duration-ms 10000
kneekura-minecraft experiment inspect-mob-pov --registry CONTROL.json --request-hash HASH --command-index 0
kneekura-minecraft experiment mob-pov --registry CONTROL.json --request-hash HASH --command-index 1 --camera-operation snapshot
kneekura-minecraft experiment inspect-mob-pov --registry CONTROL.json --request-hash HASH --command-index 1
kneekura-minecraft experiment mob-pov --registry CONTROL.json --request-hash HASH --command-index 2 --camera-operation return
kneekura-minecraft experiment inspect-mob-pov --registry CONTROL.json --request-hash HASH --command-index 2
```

Snapshot is optional. After CAPTURED, `readMobPovImage({runDir,envelopeHash,commandIndex})` verifies/retrieves bytes. Live view does not hold server ticks or change Mob AI/transforms. Its server reference is asynchronous; rendered eye view is not AI perception. Expiry/death/unload/owner loss terminates viewing; restore only the still-owned camera, preserving external replacements. Native evidence covers frozen Reimu/explicit PNG/return/expiry; moving Ghast/death/unload/external-camera scenarios remain unverified. Follow `departments/minecraft/lab/debug-workspace/bridge/MOB-POV.md` in the selected camera worktree, including its preserved failed pilot and smaller sealed audit. AF-0019 now records A–D implementation and the blocked v2 eye presentation; v1 remains spectator-only.

## Browser, comparison and finish

```text
node debug-workspace/cli.mjs tank-view UUID --config CONFIG --arena-epoch N --revision R --start-tick A --end-tick B --cursor-limit 32 --output NEW_OUTSIDE_RUN.html
node debug-workspace/cli.mjs evidence-decision-view UUID --config CONFIG --arena-epoch N --revision R --start-tick A --end-tick B --output NEW_OUTSIDE_RUN_DECISION.html
```

Open the standalone derived HTML; layers default OFF. Keep UUID/revision/cursor/source ticks aligned. Legacy `node simlab/serve.mjs` serves `http://localhost:8777`, its configured `run/sim/traces`; debug evidence does not automatically become that format. Legacy summon/kill/run/RCON are separate controls, not scoped-owner authority. Its listener omits an explicit loopback bind; do not expose it remotely. Prefer retained HTML when a live legacy server is unnecessary.

TECH HUB transport is registered local files, not an assumed `/api/debug`. Registration-only `kneekura.lab.local-bridge.v1` differs from `kneekura.lab.scoped-control.v1`. Register prepared materials; submit only immutable declared action IDs, then inspect application receipts. REQUESTED/ALREADY_RECORDED/OUTCOME_UNKNOWN are not gameplay PASS. Changed source needs fresh complete module pins, not validation bypasses.

Within the finite owner window, reconcile cleanup, then owned process shutdown and evidence finalization separately:

```text
kneekura-minecraft experiment request-cleanup --registry CONTROL.json --request-hash HASH
kneekura-minecraft experiment inspect-cleanup --registry CONTROL.json --request-hash HASH
node debug-workspace/cli.mjs stop --config CONFIG
kneekura-minecraft experiment export-result --registry CONTROL.json --request-hash HASH --observation-id OBSERVATION_ID
kneekura-minecraft experiment import-export --registry CONTROL.json --request-hash HASH --manifest-hash EXPORTED_HASH
kneekura-minecraft experiment resume --result-hash IMPORTED_RESULT_HASH
```

Cleanup uses the declared supported reset allowance, not full-world rollback. Verify actual flush/ACK, drops/queue/writer sequence/seal, camera quiescence and owned exit. Forced/unacknowledged shutdown remains distinct; never stop unrelated Java/game processes. Export/import retains original bytes; runtime attestation may remain NOT_ESTABLISHED. Resume is read-only, not replay authorization.

For `experiment-summary`/`experiment-reproduction`, supply `--config`, `--run-dir`, original `--request`/`--assertions`, `--uuid`, `--revision`, `--arena-epoch`, `--start-tick`/`--end-tick`; reproduction output is outside runs. `experiment-compare` takes before/after digests and explicit intended differences. Action-aligned comparisons use matching application identity/receipt and documented `--action-keys`/sealed `--context-relative`, not equal absolute ticks. Match source/fixture/pose/camera/FOV/viewport/channels/timing. Appearance controls use grid/brightness OFF; diagnostic ON comparisons declare identical presentation. FULL_COMPAT versus TANK_CORE is an input difference. [Workbench](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/lab/docs/KNEEKURA_TANK_WORKBENCH.md).

Handoff: purpose/intended change; source and loaded profile; private copy/recipe/saved epoch; run/snapshot/process/Arena/UUID/revision; request/assertion/action/observer; sampled window/source IDs; image hashes/visibility/restoration; cleanup/exit/finalization; export/import hashes; facts/inferences/unknowns; next bounded inspection. Keep credentials/raw private saves out of public commits.

After each coherent unit, briefly audit feedback: reproducible defect, operational friction, missing visibility, useful idea, rejected shortcut and adoption cost. Record actor, exact scope/evidence, smallest proposal, protected quality, verification and reconsideration trigger. Successful MOD work can still reveal Tank gaps. Do not hide uncertainty, add continuous recording, weaken physical/authority checks, or infer moving-Boss acceptance from static capture. AF-0018 tracks this guide reconciliation; AF-0019 tracks camera usability proposals.

## Bounded room discovery and camera diagnostics (camera worktree)

These routes require the camera worktree's matching Python/LAB revision and complete36-file control source closure; they are not installed by copying this MD to the original checkout. Source implementation is complete; native acceptance/results are recorded separately in AF-0017/0019 and the [implementation plan](superpowers/plans/2026-10-08-tank-observation-usability.md).

Add `TANK_OBSERVATION_READ` to a **new** private operator's world permissions and optional `tankObservation` object before owner preparation: schemaVersion1, scope`TANK_OBSERVATION_READ`, dimensionId`minecraft:overworld`, integer min/max, recipeHash without `sha256:`, maxEntities1..64 and maxSamples1..8. Bounds/hash must match the private `GEOMETRY_VERIFIED` saved recipe. Current native recipe supports Overworld only. This seals `control/owner-tank-observation.json` and `tankObservationHash`; changing it requires a fresh owner/run, not editing prepared files. Rotation maintenance cannot share this observation owner.

Interior `[min,max)` is half-open; shell allocation spans `[min−1,max+1)`. Action bounds remain a separate unchanged grant. Sample budgets apply to the entire immutable owner/run, not each caller or renewed lease. Limits: edges≤64, volume≤65536, residents≤64, passenger depth≤8, transport≤64KiB with4KiB payload headroom. No chunk loading, teleports, automatic registration or background sampling.

```text
kneekura-minecraft experiment tank-roster --registry CONTROL.json --request-hash HASH --sample-index 0
kneekura-minecraft experiment inspect-tank-roster --registry CONTROL.json --request-hash HASH --sample-index 0
kneekura-minecraft experiment camera-plan --registry CONTROL.json --request-hash HASH
kneekura-minecraft experiment request-capture --registry CONTROL.json --request-hash HASH --capture-index 0
kneekura-minecraft experiment inspect-capture --registry CONTROL.json --request-hash HASH --capture-index 0
kneekura-minecraft experiment capture-bundle --registry CONTROL.json --request-hash HASH --capture-index 0
```

`REQUESTED` is pending. Reconcile each roster sample at its original index before the next one; UNKNOWN cannot be bypassed by another slot. Canonical `TANK_ROOM_ROSTER` returns native UUID/type, world/local xyz (`world−min`), AABB, living/Mob/Player flags, known subject ID and vehicle/passenger references. A positive AABB overlap counts even when the base is outside. COMPLETE requires every intersecting chunk loaded and no entity/depth/byte truncation. PARTIAL sets `missingEntityNotAbsent:true`; enumeration-limited results are an internal-order-dependent subset, sorted only after selection. A reference may identify an entity outside this scope; do not infer its coordinates or presence inside. Discover residents first, then explicitly register/select desired subjects for Motion/Decision. A room sample does not automatically enable their traces or prove current positions later.

`camera-plan` reads prepared/retained facts, consuming zero native-read/image slots. It reports action/interior/physical bounds, registered poses/FOV/viewport, slot availability and last retained roster tick. Framing is `PREDICTED_FROM_RETAINED_STATE`, or UNKNOWN without matching state. Occlusion remains UNKNOWN: no fresh raycast and no pixel-visibility assertion. Neither a prediction nor a past room receipt is current-world evidence.

For `tank-cardinal-4-snapshot-v2`, grant separate `CARDINAL_CAPTURE_PAUSE_CAMERA`, declare rig FOV30..100/viewport64..2048 and four images per set. Eye positions use a1.5-block inward inset, center height and horizontal inward yaw; dimensions≤3, unloaded eyes or collision-blocked eyes fail without clearing blocks. Existing pause/tick hold and restoration contracts apply; freeze perturbs behavior, and the four frames are sequential. Actual matrices/ticks/PNG/state/restoration establish the result, not the plan. v2 metadata carries both unchanged action `arenaBounds` and sealed `observationBounds`.

`inspect-capture` and `capture-bundle` never request another capture. They verify original owner/slot/reservation/canonical manifest and raw PNG hashes, returning fixed north/east/south/west references with camera metadata, frozen state and recorded restoration. Missing images produce PARTIAL; corrupt/inconsistent sources produce UNKNOWN/error. Artifact role: `REFERENCES_TO_RAW_AND_STRUCTURED_EVIDENCE`; roster is `CANONICAL_STRUCTURED_EVIDENCE`, plan is `DERIVED_PLANNING`. Structured state is authoritative for coordinates; the bundle does not synchronize an independent roster tick or decide visibility/Boss acceptance. Optional Node `writeCaptureContactSheet({runDir,envelopeHash,captureIndex,outputFile})` creates one new derived self-contained HTML outside retained runs. Original evidence stays unchanged.

`mob-eye-observe-v2` is **BLOCKED / NOT_RELEASED**. Mapped source confirms camera-dependent `GameRenderer.pick` can affect hitResult; a future detached render-only camera must prove Player camera/hitResult restoration before normal attack/use/input and preserve external replacements. Required native input proof is NOT_RUN. Do not switch the real combat Player to spectator or freeze/teleport the accepted Ghast to manufacture moving-Boss POV acceptance. Existing `mob-eye-live-v1` remains available only within its original spectator/registered/action-bounds contract.
