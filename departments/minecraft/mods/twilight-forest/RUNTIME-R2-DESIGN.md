# Twilight Forest Runtime R2 Design — First Dimension Entry

Status: **scenario contract / not yet measured**

R2 is a separate runtime scenario from R1. R1 startup timings must not be reused as R2 evidence.

## Pinned sources

- ANCHOR: `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`
- FRONTIER: `793c4d4c7b0a2892f702cbb9a8d751fbe7218828`
- fixed world seed: `20260923`
- source portal origin: Overworld `(8, 160, 8)` 2x2 portal pool
- probe entity tag: `kneekura_r2_probe`

## Why the fixture is a server-side entity

R2 must work headlessly on the registered dedicated-server runner without a manual client.

A controlled non-player entity is used so both pinned generations exercise the real Twilight portal/teleporter path while avoiding client input and player-only progression state.

ANCHOR behavior from the pinned source:

- `TFPortalBlock.entityInside` calls `attemptSendEntity(entity, false, true)`.
- `attemptSendEntity` resolves the Twilight destination and calls `entity.changeDimension(serverWorld, new TFTeleporter(...))`.
- `TFTeleporter` searches/creates the destination portal and loads destination chunks.

FRONTIER behavior from the pinned source:

- `TFPortalBlock` implements the vanilla-style `Portal` API.
- `entityInside` calls `entity.setAsInsidePortal(...)`.
- non-player `getPortalTransitionTime` returns 0.
- `getPortalDestination` calls `TFTeleporter.createTransition(...)`.
- `createTransition` searches an existing portal or calls `createPosition`, which runs safe-coordinate selection, destination portal creation and placement.

This means the fixture preserves each generation's actual portal transition implementation rather than substituting a direct cross-dimension teleport command.

## Source portal construction

The probe creates a deterministic portal fixture at y=160 after the dedicated server reaches ready.

1. Force-load block range (7,7) through (10,10), wholly inside source chunk (0,0), for deterministic fixture construction.
2. Build a 4x4 dirt support floor at y=159 over x/z 7..10.
3. Build a 4x4 dirt layer at y=160 over x/z 7..10.
4. Put `minecraft:fern` around that perimeter at y=161.
5. Clear the center 2x2 at x/z 8..9, y=161.
6. Replace the center 2x2 at x/z 8..9, y=160 with `twilightforest:twilight_portal`.
7. Summon one `minecraft:pig` at (8.5,160.1,8.5) with `NoAI:1b`, invulnerability, persistence and tag `kneekura_r2_probe` inside the portal.

`minecraft:dirt` is accepted by the portal-edge tag through `#minecraft:dirt`; `minecraft:fern` is explicitly accepted by both pinned portal-decoration tags.

The source world is freshly created for each R2 track. The Twilight dimension must have no pre-generated chunks before the probe entity enters.

## Headless control and arrival detection

The Gradle development-run wrapper does not reliably forward its stdin to the child Minecraft dedicated server. R2 therefore uses the server's built-in **RCON** interface bound to `127.0.0.1` with an ephemeral fixed local-only password.

After the dedicated-server ready marker:

1. establish authenticated localhost RCON within a bounded control timeout;
2. construct the fixed portal fixture through RCON;
3. verify both portal blocks through an `execute if block ... run seed` command;
4. issue `debug start`;
5. record the monotonic trigger timestamp immediately before summoning the probe pig;
6. poll the Twilight dimension through RCON with:
   `execute in twilightforest:twilight_forest if entity @e[tag=kneekura_r2_probe,limit=1] run data get entity @e[tag=kneekura_r2_probe,limit=1] Pos`.

A parseable Twilight-dimension `Pos` response is accepted only after an immediate second RCON query confirms the tagged probe is absent from `minecraft:overworld`. This two-sided check prevents a selector/control ambiguity from being mistaken for a dimension transition.

After arrival, the probe issues `debug stop`, `save-all flush`, removes the probe entity and requests `stop` through RCON. RCON connection, fixture setup, debug/trigger setup, entry polling and shutdown are all explicitly bounded; no post-ready stage may wait indefinitely.

## R2 primary metrics

Compact metrics should include:

- `entry_command_elapsed_seconds`: summon command -> first Twilight-dimension arrival marker.
- `destination_prepare_start_elapsed_seconds`: first unambiguous TFTeleporter destination-creation marker when present.
- `destination_portal_ready_elapsed_seconds`: first unambiguous portal-placement/cache marker when present.
- `destination_prepare_elapsed_seconds`: difference between those markers when both are observable.
- actual destination coordinates/chunk of the probe entity.
- generated Twilight chunk count after the first entry, derived from saved Anvil region headers.
- built-in debug-profiler duration/tick count if the vanilla `debug start/stop` command emits it unambiguously.
- maximum `Can't keep up!` warning delay/ticks if such warnings occur.
- process/JVM memory observations only when they can be tied unambiguously to the server process.

Null metrics must include a reason; absence of a log warning is not proof that no tick spike occurred.

## First-chunk and structure evidence

The teleporter's destination preparation forces/searches destination chunks as part of real portal placement. R2 records the transition as a composite first-entry path.

Saved Twilight region files are inspected after shutdown:

- all saved Anvil region directories are enumerated rather than assuming one folder layout;
- the Twilight region directory is selected by explicit `twilightforest/twilight_forest` path when unique, otherwise by a single non-vanilla region-directory fallback; ambiguous or absent candidates produce a null-with-reason result rather than a fake zero;
- the Anvil region location table is used to enumerate saved destination chunks;
- chunk count/coordinates are derived without launching another Minecraft instance;
- structure activity is reported only when an unambiguous structure identifier/start can be extracted from generated chunk evidence or source-emitted logs.

If structure activity cannot be isolated reliably, R2 records it as unobserved rather than guessing.

R3, not R2, is responsible for controlled cold/warm per-chunk timing distributions.

## Built-in profiler boundary

The probe issues `debug start` through localhost RCON immediately before the portal-entry trigger and `debug stop` through the same authenticated control channel immediately after arrival.

Profiler output is retained as a raw workflow artifact. Compact evidence may promote only stable, unambiguous values such as profiler duration/tick count. It must not invent allocation bytes or per-tick distributions if the built-in profile does not expose them.

## Existing teleporter quirk preserved

Both pinned ANCHOR and FRONTIER implementations of `TFTeleporter.loadSurroundingArea` compute:

- X chunk from the destination X coordinate;
- the variable named Z chunk from the destination **Y** coordinate.

R2 does not correct or compensate for this source behavior. It is part of the pinned implementation being measured. Any effect it has on generated chunks or transition time remains runtime evidence, not a harness fix.

## Evidence contract

Each track should produce:

```text
runtime/<track>/<run-id>/r2/
  environment.json
  scenario.json
  metrics.json
  manifest.json
  evidence-summary.md
  logs/
    console.log
    rcon-transcript.json
  profiler/
```

Large raw console logs, debug profiles and optional world-inspection extracts remain artifact-only. TECH HUB commits compact manifests, hashes and derived observations.

## Interpretation boundary

R2 measures one deterministic first-entry fixture only. It does not establish:

- general ANCHOR-vs-FRONTIER performance;
- steady-state chunk-generation performance;
- structure-family benchmarks;
- boss tick cost;
- rendering performance;
- network throughput;
- resource reload performance;
- an overall performance score.

The next scenario after verified R2 is **R3 — steady chunk generation**, with fixed cold and warm coordinate lists and per-chunk timing distributions.