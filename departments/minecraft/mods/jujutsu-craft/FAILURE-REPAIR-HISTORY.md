# Failure / repair history

Status: **PARTIAL — author changelog + current ANCHOR + community reconnaissance; no full historical binary diff**

## F1 — ver45 multiplayer animation bug

Author changelog: multiplayer animation bug fixed.

Current 50.1 has distinct player-animation packet sync and Gecko entity animation paths.

**Boundary:** exact repair diff not established.

**Lesson:** animation correctness must be verified across client/server actor types, not inferred from local rendering.

## F2 — ver49 performance / lag / particles

Author changelog explicitly reports performance optimization, lag reduction and smoother particle physics.

Current target has 310 renderers, 43 particle types, 151 animation files and many area-scan procedures.

**Boundary:** no quantitative before/after benchmark.

**Lesson:** large effect-heavy combat systems need bounded area scans/particles and real performance evidence.

## F3 — ver49.1 crashes / Six Eyes

Author changelog says crashes and the Six Eyes bug were fixed.

Current player state contains `FlagSixEyes` and several combat procedures branch on Six Eyes.

**Boundary:** exact failing branch and fix are unknown without old bytes.

## F4 — Mahoraga adaptation instability / ver50 environmental adaptation

Community reports before ver50 describe adaptation as inconsistent in then-current versions. These reports are reconnaissance only.

ver50 author changelog explicitly adds/improves environmental damage adaptation.

Current 50.1 has per-DamageSource NBT progression and full-adaptation responses for environmental damage categories.

**Lesson:** adaptation systems need stable damage identity, explicit progression observability and regression tests across source families.

## F5 — ver50.1 Limitless bug

Author changelog: Gojo's Limitless Technique bug fixed one day after ver50.

Current 50.1 includes spatial Infinity handling, event-level damage cancellation and centralized bypass policy.

**Boundary:** exact 50->50.1 changed instructions are not established.

**Lesson:** cross-cutting defenses should centralize both protection and bypass predicates and have targeted regression fixtures.

## F6 — embedded version drift

Public distribution is ver50.1 while `mods.toml` remains 50.

**Lesson:** pin exact artifact hash/File ID; never use embedded semantic version alone as reproducibility identity.

## F7 — contradictory dependency metadata

GeckoLib and PlayerAnimator appear as both mandatory and optional duplicate declarations.

**Lesson:** preserve raw dependency declarations and test actual loader resolution.

## F8 — empty mixin config

A mixin config exists but contains no active mixins.

**Lesson:** configuration presence is discovery evidence, not runtime transformation evidence.

## F9 — generated procedure sprawl

1,080 procedure classes distribute behavior across many tiny/generated call sites.

**Lesson:** map shared helpers and reachability before treating file/class count as system count.
