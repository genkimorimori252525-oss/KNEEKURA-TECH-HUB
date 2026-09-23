# Twilight Forest Runtime R2 Design — First Dimension Entry

Status: **scenario contract / not yet measured**

R2 is a separate runtime scenario from R1. R1 startup timings must not be reused as R2 evidence.

## Pinned sources

- ANCHOR: `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`
- FRONTIER: `793c4d4c7b0a2892f702cbb9a8d751fbe7218828`
- fixed world seed: `20260923`
- source portal origin: Overworld `(0, 160, 0)` 2x2 portal pool
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

1. Build a 4x4 dirt support floor at y=159.
2. Build a 4x4 dirt layer at y=160.
3. Put `minecraft:fern` around the perimeter at y=161.
4. Clear the center 2x2 at y=161.
5. Replace the center 2x2 at y=160 with `twilightforest:twilight_portal`.
6. Summon one `minecraft:pig` with `NoAI:1b`, invulnerability, persistence and tag `kneekura_r2_probe` inside the portal.

`minecraft:dirt` is accepted by the portal-edge tag through `#minecraft:dirt`; `minecraft:fern` is explicitly accepted by both pinned portal-decoration tags.

The source world is freshly created for each R2 track. The Twilight dimension must have no pre-generated chunks before the probe entity enters.

## Arrival detection

The probe records the monotonic timestamp immediately before the summon command is flushed to server stdin.

It then polls from server console with a dimension-scoped command equivalent to:

`execute in twilightforest:twilight_forest if entity @e[tag=kneekura_r2_probe,limit=1] run say KNEEKURA_R2_ARRIVED`

The first observed `KNEEKURA_R2_ARRIVED` log line is the server-side R2 arrival marker.

After arrival, the probe records the entity position from the Twilight dimension, stops profiling, flushes the world save, removes the probe entity and shuts the server down.

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

- the Anvil region location table is used to enumerate saved destination chunks;
- chunk count/coordinates are derived without launching another Minecraft instance;
- structure activity is reported only when an unambiguous structure identifier/start can be extracted from generated chunk evidence or source-emitted logs.

If structure activity cannot be isolated reliably, R2 records it as unobserved rather than guessing.

R3, not R2, is responsible for controlled cold/warm per-chunk timing distributions.

## Built-in profiler boundary

The probe should issue `debug start` immediately before the portal-entry trigger and `debug stop` immediately after arrival.

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