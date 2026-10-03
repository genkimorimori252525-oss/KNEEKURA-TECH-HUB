# ANCHOR Decision component snapshot

This continuation uses PR #79's foundation at `57e52f9ef44c082daf7abbb0b0f5ada3a258a406`. Exact ANCHOR source evidence is retained in `departments/minecraft/vanilla-ai/ANCHOR-BYTECODE-LEDGER-2026-10-03.json`, including the additional `LivingEntity.brain` accessor/storage owner.

## Implemented slice

`debug-workspace/cli.mjs target <UUID> --decision-snapshot --config <private-config>` explicitly arms the selected target. Omitting the flag, clearing the target, or starting a fresh target selection leaves the new snapshot OFF. Existing baseline lanes and raw images retain their meaning.

The existing `AI_DECISION` lane carries `kneekura.vanilla-decision-snapshot/v1`. Each observation is an actual five-tick sample with its target revision, canonical run/process/Arena identity, sample tick and exact source observation ID. Goal/reference tokens are stable within the observed selection and bounded to 256 identities; exhausted identity capacity is partial capture.

Sections cover the two Goal selectors (registered priority/flags/running, cached disabled flags/flag owners), registered Brain memory presence/TTL/bounded typed values, core/default/active activities, the current declared Path, and cached base movement/look/jump fields. Arrays stop at 64 entries. The payload reserves envelope headroom within the existing 64 KiB row limit. Member failure is `NOT_EXPOSED`, truncation is `PARTIAL`; arbitrary memory objects are not traversed or stringified.

Declared fields are read from the exact owning ANCHOR class, avoiding overridden Goal/controller/Brain getter callbacks. No `canUse`, continuation, sensor, behavior execution or second path search is invoked. A custom Path subclass is unavailable until its semantics are established. Base custom-controller fields do not claim its full steering target. Brain storage presence does not establish an active Brain tick mechanism.

The existing Decision adapter consumes valid bounded snapshots into optional STATE/EXECUTION stages and typed drill-downs. It rejects mixed selection revisions as well as existing run/process/Arena fences. Complete sampled Goal running-set changes cite both samples and an interval; they retain unknown transition tick/reason and temporal association. Partial captures cannot create a false stopped-goal event.

`observerCostNanos` measures only the synchronous snapshot capture, including its payload budget check; it excludes writer/consumer/rendering and is not a claim of negligible observer effect.

## Validation and remaining scope

Brain TTL is a decimal string, preserving the `Long.MAX_VALUE` no-expiry sentinel through JavaScript JSON parsing. ExpirableValue's cached value/TTL fields are read directly, including for subclasses whose getters execute custom logic.

Signed 64-bit memory values likewise retain an exact decimal string with `INT64_DECIMAL_STRING` encoding. Actual Java tests cover both long extrema and a small long, avoiding precision loss in the JavaScript consumer.

- Motion/Decision/target-control contracts: 35 passed, zero skipped.
- Actual ANCHOR GoalSelector self-test: bounded capture, stable/reselected identities, unchanged running/registered state; stateful eligibility/start/stop/tick/custom-getter/stringification sentinels were not invoked.
- Actual dependency source contracts: writer claim 3, image writer 6, registered world 73, tank presentation 30, plus the new GoalSelector check passed.
- All Forge bridge Java sources compiled against SHA-verified exported dependency artifacts and the verified existing MOD output. API substitutes were not used.

Native runtime acceptance is pending at this record's initial generation. Original saves remain read-only; private trial world/logs/JARs are excluded from Git.

The first five private startup trials produced no observations; they are not native acceptance. Trials 1/3/4 failed Gradle task/configuration guards before gameplay. Trials 2/5 reached the native client but timed out at 600 seconds, with TacZ generated gunpack IO identified in the retained logs/thread dump. Native process exit was verified after these timeouts. Complete gunpack preparation and the mod's existing opt-out of automatic overwriting are being applied only to the dedicated private game directory; source saves and prior generated folders are retained.

This slice does **not** install original eligibility/lifecycle hooks, retained PathFinder frontier/neighbor-candidate capture, terrain/malus volume consumers, decision burst, custom Boss adapters, client live overlay or controlled observer-effect acceptance. Those remain subsequent steps of the approved handoff, not inferred from snapshot/unit/compile success.
