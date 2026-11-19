# Bedrock Wither — Direct Reference Measurement Scenarios v1

Prepared: 2026-10-03

Protocol: `BWR-MEASURE-v1`

Repository source baseline: `c1221d3c6cb46ee719923d9f99abd8739ddb802d`

Status: **PREPARED / NOT EXECUTED**

## Purpose and authority

This is the Phase 0 direct-Bedrock scenario deliverable and a preparation for Phase 4 measured-value replacement in the [implementation plan](../../../../docs/superpowers/plans/2026-10-02-bedrock-wither-reconstruction.md). It contains no observed results, accepted new constants, gameplay implementation, automation, or new control API. An execution-ready run still requires the preflight fields below. Preparing this document does not authorize operating a game, altering a world, starting CI, or publishing captures.

Current product truth remains [STATUS](../../../../deliverables/minecraft/bedrock-wither/STATUS.md), [ADOPTION](../../../../deliverables/minecraft/bedrock-wither/ADOPTION.md), and retained [evidence](../../../../deliverables/minecraft/bedrock-wither/evidence/README.md). The [full handoff](../../../../deliverables/minecraft/bedrock-wither/LOCAL-AI-HANDOFF-2026-10-03.md) distinguishes branch history from the last runtime-accepted source. Its retained 18/18 Java GameTests are implementation-contract evidence, not direct Bedrock parity evidence. This protocol does not advance either acceptance status.

Read [DESIGN](DESIGN.md), [SOURCES](SOURCES.md), [ACCEPTANCE](ACCEPTANCE.md), and the current [BDS structure map](BDS-STRUCTURE-2026-10-02.md) together. Older design names/checklists do not override current product status; the reconstruction comparison entity is `kneekura_bedrock_wither:bedrock_wither`, with vanilla `minecraft:wither` kept separate.

Use the existing evidence hierarchy without conflating kinds of proof:

1. Pinned Mojang/Microsoft definitions establish what they explicitly expose. Absence from JSON does not establish absence at runtime.
2. Current BDS headers establish native fields, function boundaries and state separation, not hidden function bodies or constant values. The recorded BDS 1.26.51.1 structural anchor is not a claim about the version that will be measured.
3. Retained, version-bound direct Bedrock observations resolve observable behavior, including native overrides of exposed components.
4. Bedrock technical documentation supplies measurement hypotheses; version-labelled historical native notes supply relationship hypotheses.
5. Community reports supply edge cases. Java/BEStyleWither code supplies engineering ideas, never Bedrock gameplay truth.

Keep disagreements and provenance. The original design's `D` label denotes direct runtime observation, not a lower quality rank. Nothing below promotes a historical or provisional product value merely by using it as a hypothesis.

## 1. Freeze an execution manifest before capture

Every run has a unique run ID, scenario/cell ID, protocol revision, preparation timestamp and immutable manifest hash. Populate each field with the actual value or an explicit unavailable reason. A required unavailable measurement blocks only the corresponding claim; it must not become an assumed value.

| Area | Required provenance and fixed conditions |
|---|---|
| Bedrock identity | Exact client version/build, platform/OS, release or Preview channel; local integrated world or exact BDS version/package identity; client/server mismatch if any; session topology, participating clients and latency evidence |
| Content | Vanilla behavior/resource-pack identities and hashes where available; all enabled add-ons, experiments and settings; no Wither-behavior-changing pack in the reference cohort |
| World | Seed, dimension, world-generation settings, isolated disposable fixture revision/hash, pristine save identity, coordinates/origin/axes, arena dimensions/material/block states, lighting/weather/time and relevant game rules including difficulty, mob spawning, griefing, drops and regeneration settings |
| Simulation | Simulation/render distances, loaded-region boundary, configured tick rate if exposed, actual tick/time observation method and its precision, pause behavior, lag indicators and any tick gaps; record `unknown` if actual tick timing is unavailable |
| Capture | Recording tool/version, resolution, configured FPS and observed frame timestamps/frame pacing, dropped/duplicated frames, audio timing if used, camera position/orientation/FOV/UI scale, graphics/particle settings and capture hashes |
| Participants | Boss/target/reflector identities, positions and poses; player mode, health/equipment/effects, target eligibility and damage history; observer participation that might change targeting; all other eligible entities |
| Boss preparation | Summon/preparation method, completed spawn evidence, current/max health and measurement method, complete relevant damage/healing/minimum-health history, visible phase evidence; actual native fields only when existing read-only evidence exposes them |
| Procedure | Exact cell values, actor action sequence/cues, observation start/stop, finite attempt/time budget, repeat count/order, allowed deviations, independent reset method, invalidation criteria and uncertainty calculation |
| Analysis | Event definitions, head/projectile classification method, coordinate calibration and error, health resolution, frame/tick synchronization bounds, metrics and reference-validation split; comparison criteria before Java scoring |

Do not use the seed alone as a reproducibility claim: entity RNG and action timing may differ between fresh summons and restored sessions. Record whether the world/save contains an already spawned entity and whether repeats restart the process. Cloned-state repeats test repeatability; they are not automatically independent random samples.

### Fixture and reset contract

- Use a disposable, isolated arena, never a production world. Keep an immutable pristine fixture and identify its reset method before starting. Existing authorized in-game preparation or existing bounded observation facilities may be used later; this protocol introduces no new controls, plugins, instrumentation or remote service.
- Fix one eligible primary target, fixed camera/calibration markers and no unrelated mobs for baseline cells. Keep cameras/observers from becoming unintended targets. Use materials with an explicit correspondence when later building the Java fixture; identical names alone do not prove identical explosion or collision semantics.
- Complete and record the spawn sequence before combat measurements. Preparation damage and its delayed reactions belong in the ledger; do not begin a clean cadence/movement window while a preparation reaction or projectile is unresolved. Do not reset hidden state by guessing a wait duration.
- Before every independent repetition, restore terrain, boss and actor histories, health/equipment, projectiles, summoned mobs, drops, weather and relevant settings to the declared starting fixture. Verify the reset with retained evidence. Do not simply heal/reposition a previously used boss and call it fresh.
- A deliberately cumulative cell, such as lowest-health history or repeated reflection, keeps its within-cell history. Reset between repetitions, not between the steps whose history is being tested.
- Use five independent valid repetitions per cell as the initial sampling budget. This is an experimental choice, not a Bedrock mechanic or proof of a full distribution. Predeclare a finite maximum number of attempts and observation duration for each cell. Retain every attempted run, including invalid and censored ones; do not keep only successful events.
- Choose the cell order before recording, interleaving paired cells to limit session drift. Do not pool Easy/Normal/Hard, client/BDS versions, different fixtures, or different recording modes into one constant.
- A bounded window with no event is `NOT_OBSERVED_IN_WINDOW`, not proof that the behavior never occurs. Insufficient independent events, inadequate resolution or unresolved confounds produce `UNKNOWN`, not a value of zero.

## 2. What the instruments can actually establish

Maintain a common event ledger with run/cell ID, event type, actor/projectile/head identity, health interval and source, spatial estimate and error, tick or timestamp interval, evidence locator/frame range, and confidence/reason. Preserve raw observations separately from derived metrics.

### Time and space

- Video frame index/FPS is not a simulation tick counter. Use actual presentation timestamps; variable FPS, interpolation, stalls and client/server latency prevent assuming one frame or a fixed number of frames equals one tick. Do not multiply elapsed seconds by a nominal tick rate and label the result exact native ticks.
- A visual event lies between the last frame showing its absence and first frame showing it. Include capture/synchronization uncertainty. Two events whose uncertainty intervals overlap have **unresolved ordering**, even if annotations assign them the same frame.
- Exact simulation timing requires an existing, validated, read-only tick/event source with known event semantics and synchronization. Name it and retain its evidence. If unavailable, report seconds/frame intervals and keep the exact-tick question `TBD_MEASURE`.
- Calibrate visible coordinates against fixed world markers. Use synchronized calibrated views or an existing read-only position source for 3D trajectories; otherwise report projected displacement only. A camera-following view without calibration cannot establish world-space speed or destination radius.
- Keep simulation time and wall-clock time separate during lag. Capture gaps can invalidate an exact interval without invalidating all earlier visible events; specify this at metric level before analysis.

### Observable boundary

| Can be measured with adequate visible evidence | Requires additional existing read-only evidence; cannot be inferred from video alone |
|---|---|
| Visible movement trajectory, turning/hover episodes, relative height and attack positions | Chosen but unreached path destination, RNG distribution, `mWantsMove`, `mIsPathing`, internal retry or stop predicate |
| Projectile appearance/origin, observed type/order and launch intervals | `mFireRate`, `mSecondVolley`, `mDelayShot`, `mTimeTillNextShot`, exact HP or lowest-health bucket when no reliable health readout exists |
| Incoming/outgoing skull trajectory and confirmed visible redirection | Internal reflection vector formula, `mReflectImmunityTicks`, `mLastReflectActor`; an unsuccessful swing does not establish an immunity rejection |
| Shield visibility, transition effects, visible dash segments, blocked/unblocked damage with valid measurements | Native phase-write order, `ShieldHealth`, `MAX_SHIELD_HEALTH`, exact projectile-immunity activation without controlled damage evidence |
| Swell/overlay/flicker appearance, explosion, first visible XP/star, boss bar disappearance and last visible model | Semantic death callback tick, killer/loot attribution, XP creation versus first rendered appearance, server removal tick and native visual equations |

These distinctions apply even if the Java reconstruction exposes all of those fields. Java telemetry does not reveal the corresponding Bedrock hidden state. Explosion crater shape alone does not identify an exact native explosion-power constant.

## 3. Scenario families

Cell parameters below must be filled and frozen in the manifest; they are not new game constants. Expanded cells receive unique suffixes for each condition (for example, `M01-C-height` and `M01-C-obstacle`), difficulty and health point. Baseline and intervention runs change only the stated factor. If a requested intervention cannot be achieved and verified with the available unchanged-engine setup, retain the cell as `BLOCKED` and collect only the independently valid observational cells.

### M01 — Phase-1 special movement and firing relationship

Question: What visible repositioning, height, travel speed and stopping behavior surrounds phase-1 firing, and how does it change with target position or visibility? This measures output behavior, not the hidden destination-selection algorithm.

Cells:

- `M01-A`: Fresh phase-1 boss, stationary eligible target, unobstructed calibrated arena, no damage during the capture window.
- `M01-B`: Same fixture; target follows a preregistered lateral route at recorded cues. Keep target health/mode/eligibility unchanged and record actual rather than intended positions.
- `M01-C`: Same baseline with one fixed target-height offset, then a separate cell with one specified line-of-sight obstacle. Do not combine height and visibility changes.
- `M01-D`: Target becomes unavailable by one declared, verified method at a recorded cue. Record whether it remains targetable; do not equate hiding behind a wall with native target invalidation.

Start at the declared post-spawn/preparation boundary and observe for the fixed window, without requiring a desired movement to occur. Cover Normal baseline first; independently repeat baseline on Easy and Hard before any cross-difficulty claim. Expanded height/route/obstacle cells remain difficulty-labelled.

Record body position/orientation, target position, displacement/velocity with calibration error, approach/turn/hover episodes, projectile origins and intervals, damage, visibility changes and any arena boundary contact. Define movement/hover detection from the preflight tracking-noise floor and minimum detectable interval, not by fitting it to the Java controller. Report target-relative horizontal/vertical distributions and movement-to-launch intervals.

Do not label a visually reached point as the chosen native destination or a pause as `mFramesTillMove`. Arena/ceiling contact makes a free-flight speed cell invalid; retain it separately as constrained movement. If the target cannot survive or remain at its route/position, that baseline repetition is invalid rather than evidence of a movement rule.

### M02 — Health-dependent cadence and independent dangerous shots

Question: How do intra-volley timing, inter-volley timing and side-head/passive shots vary with current health, previous minimum health and difficulty?

Before capture, specify a health grid independently for each difficulty using the actual verified max-health domain. Include full-health phase-1 baseline and verified points bracketing the existing ledger's candidate health-bucket/speedup boundaries. Treat 75-HP bucket tracking as a current contract/hypothesis to compare, not proof of a cadence equation. Freeze exact HP points, measurement precision and phase exclusions before collecting the reference set. Do not reuse Hard absolute-health fixtures on Easy/Normal.

Cells:

- `M02-A`: Independent fresh/prepared bosses at each selected stable health point, same stationary target and geometry, no incoming damage or healing inside the timed window.
- `M02-B`: Paired histories ending at the same verified current HP and visible phase: one reaches it directly; the other first reaches a lower verified minimum and returns by a documented, supported preparation. Retain the full healing/damage method and side effects. If these histories cannot be prepared without changing the behavior being tested, the memory-effect question stays blocked.
- `M02-C`: Separate no-eligible-target windows for side-head/passive dangerous-shot observation on each difficulty; confirm the lack of eligible targets. Do not merge these intervals with targeted center-head cadence.

Record every visible launch, origin/head (center/left/right/unknown), type (normal/dangerous/unknown), target evidence, HP history, movement and reaction events. Enumerate a volley only after origin/type evidence supports its boundary. Report shot-to-shot intervals, last-shot-to-next-first-shot gap and first-shot-to-next-first-shot cycle separately; an approximately seven-second description cannot decide which interval it denotes.

Analyze within-run intervals and between-run variance separately. Side-head shots, hurt-reaction shots, occluded launches and unidentified origins must not be silently counted in the center 3+1 sequence. Preserve incomplete volleys as censored. HP drift, target loss or preparation reactions invalidate the affected fixed-health window. Boss-bar pixels alone may support a health band, not an exact HP threshold or hidden `firerate` value. Phase-crossing windows belong to M04 instead.

### M03 — Dangerous-skull reflection and repeated contact

Question: Which observable incoming/outgoing trajectory changes follow a confirmed hit, and how do incident geometry, reflector identity and delay affect repeated redirection?

Use naturally produced, positively identified projectiles from the reference boss, with a known launch/head context and a clear calibrated flight corridor. Identify each projectile continuously; a later skull is not a second reflection of the first. Do not initialize hidden projectile fields to make a convenient fixture.

Cells:

- `M03-A`: Dangerous skull, no attempted hit, to establish unobstructed trajectory/noise; normal skull with the same documented hit procedure as a separate negative-control cell.
- `M03-B`: Dangerous skull, one attempted hit; repeat a declared frontal geometry and a separately declared oblique geometry. Fix equipment, player pose/look direction and intended contact position; record actual contact uncertainty.
- `M03-C`: The same dangerous skull receives two attempted hits by the same reflector, then in a separate cell by a second reflector. Predeclare spacing bins and finite attempt budgets. Classify by measured spacing and identity, preserving misses and out-of-bin attempts.

Record incoming/outgoing position samples, contact bounds, actor location/look vector, projectile identity/type, damage/contact confirmation method, speed/direction changes, disappearance/explosion and intervening obstacles. With adequate 3D evidence, report measured vectors and angular/speed uncertainty, not an assumed look-vector, reverse-vector or surface-normal formula.

A swing animation or apparent overlap is not proof that native hurt/reflection processing accepted contact. If rejection cannot be distinguished from a miss, report `UNKNOWN` for reflection immunity. Success/failure observations can bracket an observable re-reflection interval only with validated contact evidence and frozen geometry. They do not by themselves recover `mReflectImmunityTicks` or actor-ownership semantics. Occlusion, projectile replacement, intervening collisions or an unverified contact invalidate the corresponding vector/immunity inference.

### M04 — Half-health transition, dash preparation and termination

Question: What is the observable transition timeline, followed by dash start, direction, speed and termination under controlled conditions?

Run independent Easy/Normal/Hard cohorts; do not derive threshold HP from an assumed difficulty maximum. Use actual measured health when available. Cells:

- `M04-A`: Fresh boss prepared just above the candidate half-health boundary; apply one documented, bounded damage event intended to cross it. Record before/after HP and the actual hit interval. A visual-only cohort can locate transition presentation but cannot prove the exact threshold.
- `M04-B`: Matched baseline remaining above the boundary; then, separately, a boss already below it receiving another comparable hit. Observe whether the transition presentation repeats without assuming that it must or must not.
- `M04-C`: Post-transition, fixed stationary target and clear corridor; observe naturally initiated dash candidates. Do not force a guessed native charge state. Include the preparation period and preceding shots/movement in the retained window.
- `M04-D`: Change one factor per cell: target lateral movement, verified target unavailability, a specified breakable obstruction, or a specified unbreakable obstruction. Keep initial geometry and target history matched; measure both collision outcome and end-of-motion evidence.

For transition, separately mark damage acceptance, cessation/continuation of firing, first visible shield change, swelling/pose changes, explosion effects, first visible skeletons/count/type, first dash-like movement and subsequent control recovery. Use distinct matched trials for projectile-damage probes before/during/after transition; probes can themselves change timing and cannot be inserted into the clean ordering baseline. Record hit validity and health change/resolution; a missed projectile is not evidence of immunity.

For dash, record body/target trajectories and uncertainty, onset/end criteria calibrated before the run, heading changes, visible acceleration/preparation, active travel duration, displacement, collision and destruction events. Keep continuous dash-like movement distinct from ordinary flight; when the visible boundary is ambiguous, report bounded intervals. The existing 20-tick execution contract is a hypothesis for reference comparison, not the measurement clock or an automatic cutoff.

Retain a before/after block-state map and event timeline for obstruction cells. Attribute destruction to charge, transition explosion, hurt reaction or projectile only when evidence separates them; label overlapping causes unknown. Report observed broken sets and geometry, not an inferred exact power from crater size. Do not induce an unbounded tunnel to gather more samples: fix a spatial/time limit and record right-censoring if the behavior exceeds it. Such a run does not establish normal termination.

### M05 — Death, shield presentation and exact-timing limits

Question: When do visible death, shield/swell/flicker changes, explosion, XP/star appearance and cleanup occur, and which corresponding server events can actually be timed?

Cells:

- `M05-A`: Controlled fatal hit in a clean, verified phase-2 state, stable camera and background, no unrelated particles/projectiles/drops; retain the whole final-hit-to-removal window.
- `M05-B`: Matched nonfatal hit in the same visible state, to distinguish hurt effects from death presentation.
- `M05-C`: Fixed-camera shield timeline spanning M04's transition, and a separate stable phase-2 damage sequence. If a supported, unchanged-engine setup can restore health above the boundary, observe a separate healing-history cell; do not assume shield persistence or disappearance.
- `M05-D`: Separate complete spawn recording as a skin/swell timing control, without treating the product's 220-tick target as measured Bedrock truth. Keep this distinct from death and phase-transition clocks.

Repeat the death baseline per difficulty. A phase-1 fatal-hit variant is eligible only if a documented ordinary preparation can achieve it without forcing hidden state; otherwise leave it blocked rather than substituting a kill/remove command. Fix killer identity/equipment and collection distance. Keep drops/XP visible before collection, or record unavoidable collection/occlusion as censoring.

Annotate final damage/contact bounds, first death presentation, body scale relative to calibrated markers, visible overlay/flicker/shield-layer states, explosion effects, first visible XP and Nether Star, boss-bar disappearance, last model frame and later scene cleanup. Use fixed exposure/graphics/background and track camera distance so illumination, perspective and particles do not masquerade as a swell/overlay equation.

Keep separate columns for semantic death, visual onset, XP creation, first visible XP, loot creation, first visible loot and server removal. Only fill semantic/server columns from a validated existing event source; video visibility is not semantic life, kill credit or a server timestamp. In particular, a model remaining visible after a fatal hit is not evidence that the boss is still semantically alive.

Report each visual change as an interval and the actual sample resolution. An exact total duration, explosion tick, XP tick or shield-switch tick is accepted only if the named measurement source resolves that event. Do not infer `ShieldHealth`, `MAX_SHIELD_HEALTH`, `AirAttack`, native phase or Molang/native equations from colors or flicker alone. A fitted visual curve is a version-bound approximation until independently validated, not recovered source code.

## 4. Invalidation, repeats and interpretation

Before a run, fix which of these conditions invalidates a whole run versus one metric:

- Version/content/settings/fixture mismatch, unverified reset or unexpected eligible target.
- Wrong starting phase or HP/history, unrecorded damage/healing, unresolved preparation effects.
- Missing entity/projectile identity, ambiguous head/type/contact, simultaneous events whose causes cannot be separated.
- Camera movement or occlusion beyond the predeclared calibration budget; dropped frames, recording pause or event-source desynchronization that crosses a timing boundary.
- Tick/latency evidence outside the preregistered timing-quality envelope; unknown actual tick timing blocks exact-tick claims even when visual observations remain usable.
- Arena boundary contact in an unconstrained cell, actor route deviation, unexpected death/escape, insufficient observation duration or exhausted attempt budget.

Retain the reason, raw capture, affected metric and replacement-run ID for every invalidation. Valid unexpected behavior is a result, not an excuse to discard a run. Preserve lag, tunneling and other anomalies as version-bound findings instead of turning them into default mechanics. New hypotheses require new cells/revisions; they do not silently change the current cohort.

Use outcome labels deliberately:

- `PREPARED` / `BLOCKED`: no usable observation for the requested claim.
- `MEASURED`: a bounded observable and uncertainty, without a parity decision.
- `UNKNOWN`: insufficient/conflicting evidence, unresolved causality or instrument limits.
- `FAIL`: a valid comparator run violates frozen acceptance criteria.
- `PASS`: that specific comparator/scenario/metric meets frozen criteria; never whole-game or hidden-code parity.

## 5. Reference freeze and later Java/Tank comparison

1. Finish preflight calibration/preparation trials separately from reference data. If health control, event visibility or observation budgets need adjustment, revise and freeze the manifest before collecting the reference cohort. Calibration outcomes are not confirmatory results.
2. Collect the preregistered reference repetitions. Retain all event rows and uncertainty bounds, within/between-run variation, sample counts and censored outcomes. A minimum sampling budget is not evidence that a rare tail or all RNG outcomes have been covered.
3. Freeze a version-bound reference report/hash. Specify the tested metric, uncertainty propagation, aggregation and validation rule. Counts/types/order use exact criteria only where reference identity is unambiguous; stochastic movement/cadence use declared distribution/range criteria rather than requiring identical RNG trajectories.
4. Define spatial/timing tolerances from reference variance and instrument resolution, with a separate reference-validation set fixed before examining reconstruction performance. A deterministic tick criterion requires tick-resolved reference evidence. Leave unsupported criteria `TBD_MEASURE`; do not fill them with product provisional values.
5. Run separately identified vanilla Java control and reconstruction cohorts later through the existing bounded Tank/observer workflow. Pin Java/Forge/product commit/JAR identity and fixture adaptation. Match difficulty, initial geometry, material semantics, health history, actor inputs and observable event definitions. Any unmatched condition is a declared limitation, not silently comparable data.
6. Compare the frozen reference metrics to each Java cohort. Retain source and derived evidence hashes plus mismatches. Do not widen tolerances after seeing a failure. A justified change requires a new scenario revision, preserved old failure and fresh applicable reference/comparator validation; it cannot retroactively turn the old run into PASS.
7. Before replacing any `TBD_MEASURE` in product code, update the source/adoption contract with exact version, method, accepted value/range and limits, and add a regression test capable of detecting the wrong transfer. Protocol preparation alone does none of these steps.

Screenshots/video support acceptance but do not replace the [R2–R5](ACCEPTANCE.md) evidence requirements. Where Bedrock has only visual evidence and Java has rich telemetry, compare only shared observables; keep hidden-state equivalence unclaimed.

## 6. Retention and completion checklist

For each later executed run, retain a small manifest and event/measurement summary with hashes and authorized bounded-runtime/CAS locators. Follow the [product evidence retention policy](../../../../deliverables/minecraft/bedrock-wither/evidence/README.md): do not commit raw worlds, large logs, videos/image dumps, third-party assets or private runtime captures. Collection does not authorize external sharing or publication.

The protocol is ready for an execution review when its scenario cell manifest can answer:

- Which exact Bedrock build, difficulty, seed/fixture and actor/health history is being tested?
- Which visible or validated server event defines each start/end, and at what tick/frame/spatial resolution?
- What is fixed, what single factor changes, and how is the scene independently reset?
- How many attempts/repetitions and what finite observation/spatial limit apply, including no-event outcomes?
- What makes a metric invalid, and where will every attempt and uncertainty be retained?
- Which results can become measured constants, which remain visible approximations, and which hidden questions remain unresolved?
- Has the reference and comparison rule been frozen before looking at Java pass/fail results?

**Current execution result: none.** All five measurement families are prepared only. Direct Bedrock observation, reference freeze, paired Tank acceptance and any product constant changes remain future work.
