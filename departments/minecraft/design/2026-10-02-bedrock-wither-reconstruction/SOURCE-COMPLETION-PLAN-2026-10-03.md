# Source-backed Wither completion implementation plan

> For agentic workers: use test-driven implementation and independent review for each bounded change; run the complete Forge and repository suites before publication.

**Goal:** Finish the existing standalone Wither's ordinary combat and lifecycle code using the retained sources, without requiring direct Bedrock/Tank measurements.

**Architecture:** Keep the existing independent entity and controller boundaries. Connect currently unreachable phase-1 movement and phase-2 combat, distinguish accepted observations from explicitly provisional historical-native/Java adaptations, and preserve Forge death compatibility.

**Tech stack:** Java 17, Minecraft Java 1.20.1, Forge 47.2.0.

**Spec:** `DESIGN.md`, as amended by the user-directed completion boundary below.

## Completion boundary and global constraints

- The user's 2026-10-03 direction is to finish code and not perform empirical Bedrock measurement. Measurement is therefore not a software-completion prerequisite. The earlier measurement protocol remains unexecuted historical preparation.
- Software completion means the documented ordinary combat paths are reachable, persisted state recovers safely, declared behavior is covered by automated tests, and build/repository checks pass. It does not mean experimentally established Bedrock identity.
- Preserve the pinned Mojang sample revision `46ba6ea985fb5a92d79a9419198f10dda14c199d` (entity format 1.26.50) and structural BDS anchor. Date/revision-label older Wiki/native material; never promote it to current binary proof.
- Prefer explicit official values, then corroborated technical reports, then isolated historical-native defaults. Where an engine adapter must choose a rule, name and document it rather than inventing a Bedrock fact.
- No new dependencies, upstream code copying, Bedrock texture redistribution, live game measurements, home runner, merge, or deployment.
- Existing PR81 is the authorized publication destination; verify the exact remote head and GitHub-hosted workflows before and after publication.

## Review focus

1. Ordinary AI must reach movement, volleys, alternating phase-2 charge, recovery and death without tests manually calling the entry controller.
2. Spawn/transition/death gates must prevent unrelated random-stroll and attack processing from overriding special states.
3. Reloading during movement, volley, transition or charge must not duplicate explosions/skeletons, resume stale motion, or permanently stall.
4. Target loss, invalid directions, obstructed paths and unbreakable blocks must terminate or recover finitely; no arbitrary entity/world scanning.
5. Positive-health death cancellation and exactly-once ordinary rewards must retain all existing regression coverage.

## Task 1: Complete ordinary combat orchestration

Files: entity `BedrockWitherEntity`, `BedrockWitherState`, `BedrockWitherRuntimeState`, `BedrockWitherVolleyController`, `BedrockWitherSpecialMovementController`, `BedrockWitherDashController`, `BedrockWitherPhaseController`; new `gametest/BedrockWitherCombatGameTests`.

- [x] Add failing ordinary-AI tests for phase-1 reposition/hover/fire, phase-2 continuing volleys and alternate-burst charge, target-loss recovery, and source-defined inter-volley independence from `fireRate`.
- [x] Preserve the existing 3-normal/1-dangerous order and 140-tick reported volley pause. Keep accelerated-rate policy explicitly historical/provisional, separate from the documented 75-HP NBT bucket.
- [x] Supply source-derived provisional movement/charge constants and connect production entry paths. Keep the measured-entry APIs only as explicit adapters, never the sole route to combat behavior.
- [x] Represent half-health transition and one-shot explosion/summons without a permanently stalled prep state. Label any retained uncertainty in exact ground-contact/order semantics.
- [x] Test save/load across these paths through entity NBT and ordinary ticking; conservatively cancel stale charge/navigation and resume a valid phase.
- [x] Run the new tests RED then GREEN and the full Forge suite; independently review production reachability and bounds.

## Task 2: Close documented visual and projectile contracts

Files: `client/BedrockWitherArmorLayer`, `client/BedrockWitherRenderer`, existing skull entity and focused test utilities only as required.

- [x] Compare current renderer with both pinned official armor controllers, including blue-layer UV equations and light behavior. Implement the missing source-defined layer using existing Java texture substitutes, without claiming texture parity.
- [x] Test pure timing/UV and visibility inputs used by production code, including partial ticks and phase/death boundaries. Headless checks do not establish actual rendered appearance.
- [x] Check official projectile default `reflect_immunity=0` seconds and `owner_launch_immunity_ticks=5`, distinct from native repeated-reflector semantics. Test existing damage/projectile reflection paths before adding only confirmed missing behavior.
- [x] Keep exact reflection-vector policy version-labelled: current JSON proves the gate, historical body is evidence for a fallback, and Java engine behavior is an adaptation.

## Task 3: Close lifecycle/state and acceptance documentation

Files: death controller, focused lifecycle tests, `ADOPTION.md`, `STATUS.md`, current handoff, design/acceptance docs, compact evidence/failure records.

- [x] Test and fix first-phase death retaining native phase 1 when documented death state is phase 0, while preserving cancellation/reward contracts.
- [x] Audit all public controller entry points and source-declared behaviors for unreachable, neutral-placeholder or permanently waiting code; resolve code paths or explicitly bound a non-goal without claiming full parity.
- [x] Record every newly adopted source, revision, provisional numeric choice and adaptation consequence before final review.
- [x] Replace obsolete 'measurement required to proceed' completion wording with the user-directed software boundary, preserving earlier evidence as history.
- [x] Run `gradle build runGameTestServer`, repeat the final complete Forge suite, and run the full repository Python suite with Java17 and a Git-external temporary directory.
- [x] Independent whole-diff review and narrow re-review of all confirmed findings
- [ ] Publish to existing Draft PR81, verify remote tree, then watch both GitHub-hosted checks to terminal success. Record failures accurately and do not merge.
