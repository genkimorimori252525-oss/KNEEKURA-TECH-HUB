# Bedrock Wither — Current Status

Updated: 2026-10-04
Lifecycle: **PROTOTYPE / source-backed software implementation**
Milestone: **BWR-M1 — standalone boss code completion**

## Current completion boundary

The user chose to finish the code without empirical Bedrock or Tank measurements. Ordinary combat now runs from source-backed, explicitly labelled policies rather than waiting for external measured values. Software acceptance is build, ordinary-runtime-path and regression verification; experimentally demonstrated Bedrock identity is not claimed.

Current work is in [Draft PR81](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/81), stacked on the existing Wither branch/PR75. The original branch remains unchanged. No merge or deployment is performed.

## Implemented and exercised

- Independent `kneekura_bedrock_wither:bedrock_wither`; vanilla Java Wither is unchanged. Forge 1.20.1 / 47.2.0 / Java 17 remains the anchor
- Difficulty health 300/450/600, 1×3 collision box, follow range 70, movement/flying attribute 0.6, boss HUD 55/sky darkening, undead family, fire/freezing/water contracts and undead-source rejection
- Official persistent-boss behavior prevents ordinary distance/idle-random despawning, including legacy false-persistence NBT; the earlier Peaceful-removal branch is preserved
- Highest-damage eligible Player, retaliation, then visible nearest eligible target. Creative/spectator attackers cannot retain priority-1 targeting or enter immediate combat controllers
- Pinned public supplemental goals are now present: `behavior.float` priority 1, `look_at_target` priority 5 and `look_at_player` priority 6. The look adapter preserves public distance 8 / probability 0.02 and the Wither-specific 1..2 second look window without replacing the dedicated three-head controller
- Ordinary phase-1 ascent, target-relative reposition, hover and 3-normal/1-dangerous center volleys; finite failed-path recovery
- Per-shot acceleration uses an explicit historical-native fallback, with the corrected maxHP/6 interval. The documented 75-HP NBT bucket is separate. Phase reset, large-hit, healing and reload policies are tested
- Reported 140-tick inter-volley pause is independent of per-shot cadence. Phase1 then repositions/settles; phase 2 emits its next projectile after the selected 140-tick pause
- Half-health descent precedes one explosion and difficulty-aware skeleton summon; phase 2 projectile immunity and independent AirAttack shield presentation
- Ordinary phase 2 continues volleys, prepares a charge after alternate bursts, executes bounded target-directed motion/destruction and resumes firing. Invalid/lost targets, unbreakable collisions, nonfinite vectors and spawn/death overrides are guarded
- Side-head scheduling runs outside protected movement/transition/charge gates in both combat phases
- Actual skull collisions dispatch direct damage/effects once, preserve owner kill healing, and use source-defined zero gravity and air/liquid inertia. Owner launch grace and non-damaging projectile reflection are exercised; prior Forge skipped impacts are respected
- Pinned official body/swell/skin math and white/blue armor UV passes are wired through production-used presentation functions. Java texture/tint substitutes are explicitly documented
- Accepted death uses native phase0, cancels residual combat motion and runs the historical-provisional visual countdown/flicker. Save/reload preserves progression; positive-health Forge cancellation preserves the live combat state
- Ordinary player-attributed death/loot/XP events, actual 50 XP and one Nether Star, and reward idempotency remain covered. The star's documented unlimited lifetime survives item NBT reload
- Independent-boss kill credit now restores Wither Rose behavior lost by intentionally not inheriting Java `WitherBoss`: place the rose when `mobGriefing` and survival rules permit, otherwise drop exactly one rose item
- Wither sound integration now exposes ambient/hurt/death sounds and uses Java 1.20.1 Wither level-event bridges for block break (1022), spawn (1023) and skull shoot (1024)
- Renderer-facing spawn ticks and independent head pitch remain synchronized through actual entity-data snapshot/dirty-data boundaries
- Transient movement/preparation/charge reloads recover safely; volley alternation, rate cursor and pending transition work persist; obsolete hurt-state saves normalize into valid combat

## Verification

The source-completion generation originally passed **60/60 required Forge GameTests**. The post-completion parity-polish code source `a2d838cf50052d3fb0e1dfeb3a826084e8e6da6b` now passes **64/64 required Forge GameTests** in hosted run `37147781105`: the original 60 plus four supplemental goal/sound/Wither-Rose regressions. The same exact code source passed the complete hosted Tech Hub suite in run `37147783747` with **3141 passed / 332 skipped / 8 warnings**.

[Current source-completion verification receipt](evidence/source-completion-2026-10-03.json) records the original 60-test completion. [Parity-polish receipt](evidence/parity-polish-2026-10-04.json) records the audit-derived supplement, its initial compile RED at `725960309...`, the typed-predicate repair, and the exact accepted code source/hosted checks. [PR81](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/81) remains the publication line.

Historical hosted checkpoint `6e2faafcb5789ce5f3d8c355bf208d037cf96646` passed [24 GameTests](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37138822902) and [3141 Python tests /332 skipped](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37138825757). Those are prior-generation results, not evidence for the current parity-polish source.

## Declared reconstruction choices

See [ADOPTION](ADOPTION.md) and the [source audit](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/SOURCE-AUDIT-2026-10-03.md) for exact provenance/version limits.

- Reposition radius10, uniform-angle choice and Java flying navigation are declared adapters; native-shaped modifier15 and stop delay20 are historical inputs. Java control uses 180° pitch and 90° yaw per control update; the official max-turn180 input does not establish native yaw equivalence
- Aerial height5/damping0.6/ascent0.5 are historical-native inputs integrated into Java movement
- Dash preparation20, horizontal speed2 and recovery20 are historical-shaped policies; active20 is the retained technical report, disagreeing with historical active10
- A finite 120-tick path budget and 100-tick/void-bounded descent fallback are Java safety policies
- Firing rounding/minimum1 and phase cursor reset are explicit Java adaptations; the current exact Bedrock acceleration equation is not claimed
- Reflection vector/speed and same-vehicle grace use documented Java adaptations; zero configured reflection immunity does not prove native repeated-reflector behavior
- Death200/power7/swell/overlay/flicker are historical-provisional policies. Forge reward timing remains ordinary and is not made to mimic delayed historical rewards
- Native ShieldHealth remains a non-authoritative diagnostic field; no unsupported finite shield pool is invented
- Java 1.20.1 Wither sound events are now wired as compatibility bridges, but exact Bedrock audio assets/mix/attenuation/timing, exact Bedrock textures, particles, live client/wire rendering and ServerPlayer advancement grants are not established by these headless tests

## Handoff / next action

Review the current Draft PR and its exact-head checks. No empirical measurement, Tank run, home runner or optional vanilla replacement is needed to complete the requested source-backed code pass. Unknown current-native details remain disclosed limitations, not permanently unreachable code paths.

Read [current plan](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/SOURCE-COMPLETION-PLAN-2026-10-03.md), [acceptance](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/ACCEPTANCE.md) and ADOPTION before changing these policies. Preserve source identity, independent review and complete regression checks for later changes.
