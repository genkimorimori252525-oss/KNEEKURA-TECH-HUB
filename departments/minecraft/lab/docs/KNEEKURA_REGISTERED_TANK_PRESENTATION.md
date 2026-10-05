# Registered Tank presentation

The debug bridge can render the existing Tank's one-block grid and `OBSERVATION_BRIGHT` lightmap during an explicitly registered, finite scoped-owner run. This restores the presentation used by the separate g3 Tank implementation without importing that branch's coordinator, resize, reset or entity-management protocols. Server lighting, blocks, entity effects and physics are unchanged.

This is optional. Existing registrations and non-ZIP resource artifacts remain valid without presentation. Include `kneekura/tank-presentation.json` in the SHA-256-bound registered resource ZIP to opt in. The capsule contains `status`, `displayMode`, `recipeHash` and `recipe` from the saved world's `kneekura-tank-owner.json`; it must not contain owner credentials. `status` must be `GEOMETRY_VERIFIED`, and the canonical recipe hash must match. The recipe must have `v: 1`, `kind: "tank_recipe"`, dimension `minecraft:overworld`, integer origin and dimensions, and `presentation.gridSpacing: 1`. Supported modes are `OBSERVATION_BRIGHT` and `NATIVE`; the latter retains native lighting with the grid.

The parsed registered view must equal the parsed saved-world view. Presentation requires the integrated `KNEEKURA_DEBUG_WORLD`, an exact current owner/session/run/snapshot/process identity, safe owner state and an unexpired capture lease. The immutable context retains the original owner lease's issued/deadline nanoseconds and actual server reference. Both render consumers check current singleplayer-server identity and monotonic elapsed time even when server ticks are paused; disconnect/another server cannot reuse the view. Owner uninstall clears it. Render-tick transitions mark the native lightmap dirty once, retaining invalidation across a missing client level, so expired bright pixels are recomputed rather than retained in the lightmap cache. This uses the existing `LightTexture.tick()` dirty-update path; it does not advance server/game ticks. Invalid or mismatching data leaves presentation unavailable. A failed opt-in is not retried within the same run. ZIP entry count and expanded sizes, strict UTF-8, geometry/world bounds and duplicate capsule entries are bounded or rejected. Presentation does not grant mutation authority or extend a lease.

Both Before and After must bind the same presentation capsule and mode when comparing another change. Full-bright rendering is an observation perturbation; it is not evidence of native ambient lighting or complete loaded-resource equivalence. Raw image and camera metadata remain unmodified.

[Pre-experiment Tank rotation](KNEEKURA_REGISTERED_TANK_ROTATION.md) disables this presentation for the maintenance owner. After geometry verification and old-owner closure, a fresh run must register a capsule matching the new saved recipe. The old capsule or display lease cannot be reused. [Frozen R62 native reconnect](../../vanilla-ai/TANK-ROTATION-NATIVE-2026-10-05.md) observes the actual new-recipe display context and its original120s expiry; pixel brightness/grid quality and loaded-resource/full-target attestation remain unverified.

Source reference: g3 LAB `8e36ea8b1c8634bb1422c965b0e5f179d54f1cdf`, `KneekuraDebugTankView.java`. The retained renderer uses the existing Forge events and has no new dependency. The pure-JVM presentation contract has30checks (19recipe plus11lifecycle/lightmap-transition checks); the integration also requires genuine Forge API compilation and native image verification. This document alone does not establish native acceptance.

## Tank status and finite preflight

The additive `TANK_PRESENTATION_STATUS` lane samples request/registration/eligibility/draw submission separately. Submission is not pixel visibility. Samples use the original owner lease and process clock; stored rows describe historical state. A single optional waiting slot shares the existing writer while keeping its evidence queue capacity and heartbeat clocks unchanged. Optional status is coalesced or suppressed under pressure; it does not hide ordinary evidence drops. Notifications are at most1Hz in steady state and at most2/sec including changes.

Create an explicit private profile, for example:

```json
{"kind":"OBSERVE_GRID","grid":true,"brightness":false,"motion":false,"decisionChannels":["SERVER_ENTITY_STATE"]}
```

For a benchmark, use `kind: "BENCHMARK"` and explicitly specify every display/channel flag, including grid OFF when required. `NATIVE` still draws the grid; grid OFF means a newly registered resource without a Tank capsule. No mode silently modifies the saved world marker. The declared flags alone do not prove channel coverage or completed performance acceptance.

Before registering a new request, generate a new capsule from the private copy's verified saved marker (commands run from the LAB subtree):

```powershell
node debug-workspace/cli.mjs tank-resource --config <config.json> --saved-recipe <saved-marker.json> --profile <profile.json> --output <new-resource.zip>
```

The output is created exclusively; existing artifacts are not overwritten. Only the four display/recipe fields enter the capsule. Register its hash as the resource artifact before owner preparation; resource generation itself does not register or authorize a run. Keep all other experiment bindings consistent. Existing generic launch defaults are unchanged.

For a retained/current run, supply its exact Arena epoch:

```powershell
node debug-workspace/cli.mjs tank-status --config <config.json> --arena-epoch 0 --recipe-hash <canonical-recipe-sha256>
node debug-workspace/cli.mjs tank-preflight --config <config.json> --arena-epoch 0 --recipe-hash <canonical-recipe-sha256> --profile <profile.json> --time-budget <budget.json>
```

Budget example: `{"experimentMs":30000,"finalizationMs":5000,"cleanupMs":5000,"marginMs":5000}` requires45,000ms. `READY` requires current matching display evidence, required channels and a fresh scoped-owner lease sample; unknown/stored clocks remain `UNKNOWN`. Reported remaining time is never dispatch authority. Add the same `timeBudget` to the existing private `submit_action` control command when starting the planned experiment. Publication rechecks the current owner; the native dispatch marker carries the optional bounded `minRemainingMs`, and the JVM rechecks the original monotonic lease immediately before executing. Older dispatches keep their existing shape and rules. Confirmation/capture time is consumed from the original lease; nothing extends or reuses it.

These source/contract checks do not establish native pixel visibility or the T6 performance/non-degradation acceptance. Appearance comparisons require grid OFF and brightness correction OFF control images; presentation diagnostics retain their differing conditions.
