# KNEEKURA MOD shared debug system — deferred product-wide roadmap

**Decision date:** 2026-10-09
**State:** ACCEPTED DIRECTION / RESEARCH AND IMPLEMENTATION NOT STARTED.
**Owner system:** TECH-HUB existing Minecraft MOD-AI + LAB; **not** an additional stand-alone debug service.

## Owner's intent

Design one coherent diagnostic, observability and experiment system for KNEEKURA-created mods, initially:

- `Kirby_mod` → new canonical product folder `departments/minecraft/projects/kirby-mod/` after migration
- `NaturalGhastmod` → independent project, ghast AI/flight/barrage
- `reimu-mod` → planned later integration, Reimu AI/Molang/animation

Legacy per-mod debug commands, ad-hoc text dumps and the Kirby `/tlm` implementation are incomplete and non-canonical. During source migration preserve them for compatibility and provenance but **do not duplicate, extend or accept them as the shared debug system**. Replacement/deprecation must be gated by feature-equivalence proof and migration tests.

## Reuse — audit before building

The TECH-HUB repository already has:

1. `departments/minecraft/lab/debug-workspace/`: Supervisor, run/session/source identity, READY/runtime attestation, bounded capture, exact target UUID, server/client lanes, exported evidence and action controls. Its README includes historical milestone paragraphs: the 2026-10-02 current handoff supersedes those old status passages.
2. `departments/minecraft/lab/bridge/tlm-forge/`: product-specific probes and trace data; extract generalizable *adapters/contracts* without importing TLM assumptions as universal semantics.
3. `departments/minecraft/mod-ai/`: SourceSnapshot, TaskContext, test/evidence and editor integration; do not create a second knowledge store, authority layer or artificial observation.
4. Existing Water Tank trajectory/decision observability plans; reconcile with their current status and retain all run-bound provenance.

Start with a capability/gap inventory per module. Do not rewrite working G1/G2/G3/arena/tank adapters on speculation.

## Proposed shared interface — not implemented

Define a versioned, low-overhead event envelope from an optional Forge-side adapter to one LAB intake:

- `schema_version`, `producer_mod_id`, `event_kind`, `logical_side`, `mc_tick`
- `session_id`, `run_id`, `process_epoch`, `build_hash`, `source_hash`
- optional exact `dimension` / `entity_uuid` / ability or attack ID / `correlation_id`
- `capture_mode`, `sample_rate`, `dropped_count`, `evidence_status`, typed `payload`

Do not assert a causality claim merely because two timelines line up. Keep raw observations, derived findings and controlled interventions separate; use existing LAB run IDs and fences.

Suggested lanes, each opt-in:

- **Mob AI:** decision/state/goal ownership, candidate rejection, navigation and target selection, recent state transitions.
- **Combat/physics:** attacks, projectiles, collisions, knockback, movement trajectory and ability ownership.
- **Visual:** GeckoLib or YSM animation/state, model variant, Molang/pose and authoritative vs client-render discrepancy.
- **Networking:** packet type/direction, sync boundary, server authority, receipt and stale-state warnings.
- **Performance:** tick/MSPT, per-entity cost budgets, spikes, heap / allocations, drop counters.
- **Operations:** build/version mismatch, config, dependency errors, server/client warnings and structured crash metadata.

Product-specific fields remain namespaced extensions: `kirby.*`, `ghast.*`, `reimu.*`. No one-size-fits-all AI decision template; a common envelope is not a universal behavior model.

## Research and evidence admission gate

Research broadly in GitHub source and commit/issue repair histories, official Forge and Minecraft engineering documentation, established diagnostics/profiler code, specialized articles, and community reports (including Reddit). Score proposals for **specificity to Forge 1.20.1**, observed implementation, reproducibility, throughput impact, false-positive risk, side separation, test support, and maintainability. Reject attractive but unsupported claims.

Initial external sources to evaluate:

- Forge 1.20.x [events](https://docs.minecraftforge.net/en/1.20.x/concepts/events/), [logical/physical sides](https://docs.minecraftforge.net/en/1.20.x/concepts/sides/) and [Debug Profiler](https://docs.minecraftforge.net/en/1.20.x/misc/debugprofiler/) (anchor references).
- [spark](https://github.com/lucko/spark) and its [tick-loop guide](https://spark.lucko.me/docs/guides/The-tick-loop) (performance profiling reference; do not blindly vendor its implementation).
- [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/) (consistent event names and attributes; **not** a decision to depend on the full SDK).
- [Reddit example of intermittent modded Forge 1.20.1 client/server join NPE](https://www.reddit.com/r/ModdedMC/comments/1gun0o2/) — **anecdotal failure-mode hypothesis only**; use to create reproducible client/server regression scenarios, not to attribute arbitrary crashes to a named mod.
- More community solutions may be added with exact post/commit date and validation outcome; popularity is not proof.

Exclude by default: full-world scans every tick, unlimited entity/per-tick log streaming, undefined private-reflection hacks, crash-only retrospective guesses, unconditional packet payload capture, remote arbitrary command/script execution, and automatic actions based solely on AI interpretation. Production/developer worlds must remain separated.

## Design / execution sequence for later session

1. Pin latest TECH-HUB, LAB and all three product source snapshots. Inventory all legacy debug code, events, commands, instrumentation and what actually works.
2. Build a strict capability-gap and source-evidence matrix; score and prune community suggestions; specify typed schema and compatibility strategy.
3. Specify sampling/backpressure/ring buffers, access permissions, safe shutdown, sensitive-data redaction, monotonic ordering, client/server join and false-causality handling.
4. Build one smallest Forge 1.20.1 adapter and run-bound LAB test using a disposable debug world; derive a baseline for measurable profiler overhead.
5. Add Kirby, Ghast, Reimu adapters separately, with independent semantics and opt-in lanes. Retain temporary compatibility with legacy `/tlm`.
6. Validate fixture tests, exact UUID target isolation, event loss markers, server vs client discrepancy, repeatability, intentional fault injection, performance and multi-MOD coexistence.
7. Decide a documented promotion/deprecation migration only after passing parity checks. Do not remove legacy probes prematurely.

### Completion criteria

- One shared API/event contract and one observation/evidence workspace, versioned and documented.
- All three mod adapters provide needed state/AI/combat/visual evidence without a duplicate per-mod debug *system*.
- Explicit source→build→runtime↔observation linkage and distinguishable NOT_RUN/PARTIAL/PASS results.
- Demonstrably bounded overhead and memory in declared game scenarios, with no data leakage or privileged command expansion.
- Tests for inter-mod interference, client-server synchronization and backward compatibility.
- Unresolved findings remain UNKNOWN, never a manufactured PASS.

**No runtime implementation or acceptance is claimed by this planning record.**
