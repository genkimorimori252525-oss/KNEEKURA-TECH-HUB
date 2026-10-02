# Bedrock Wither — Current Status

Updated: 2026-10-02  
Lifecycle: **PROTOTYPE**  
Milestone: **BWR-M1 — standalone boss reconstruction**

## Current truth

Completed:
- Research/design is separated under `departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/`; product source remains under `deliverables/minecraft/bedrock-wither/mod/`.
- Evidence priority is official Mojang/Microsoft definitions → current BDS structure → direct Bedrock observation → Bedrock technical documentation → community reports → Java prior art.
- BEStyleWither is engineering prior art only and does not define Bedrock gameplay constants.
- Mojang `bedrock-samples` Wither definitions are pinned at `46ba6ea985fb5a92d79a9419198f10dda14c199d`.
- Current BDS 1.26.51.1 structure is mapped through LeviLamina generated headers; historical Bedrock reverse engineering is isolated as hypothesis/corroboration only.
- Standalone `kneekura_bedrock_wither:bedrock_wither` exists without replacing `minecraft:wither`.
- Official/native-resolved entity surface implemented: 1×3 collision box, follow range 70, effective runtime movement/flying speed 0.6 (public JSON still exposes 0.25), max-turn adaptation 180, undead family, fire/freezing immunity, water breathing, undead-source damage rejection, XP 50, boss HUD range 55 and sky darkening.
- Target priority implemented from current Bedrock definitions: highest-damage Player path, hurt-by-target, then visible nearest non-undead/non-inanimate target.
- Custom normal/dangerous skull entity owns Bedrock launch power 1.2/0.6, inertia 1.0, dangerous reflection gate, Bedrock→Java explosion-resistance translation with explicit unbreakable exceptions, explicit 5/8/12 impact damage, owner heal-on-kill=5, Wither II duration by difficulty, and power-1 explosion lifecycle.
- Center-head projectile order is represented as 3 normal + 1 dangerous; ~7-second inter-volley cooldown is observed/current, while accelerated ticks-per-shot remain evidence-gated. Current NBT-style `lastHealthInterval` tracking uses monotonic 75-point buckets.
- Official Bedrock model geometry, base scale 2 and body/head animation relationships are implemented without redistributing Bedrock texture bytes. AirAttack is synchronized separately from nativePhase and drives powered-shield visibility; the inflated armor geometry is implemented with Java's bundled Wither armor texture as a temporary asset substitute.
- Native-like runtime state mirrors current BDS phase/shield/head/charge/projectile/movement/skeleton fields for observation.
- Half-health transition uses native-like phase 1→0, one-shot latch, Normal/Hard skeleton count 3, Easy 0, projectile immunity in phase 2, and isolated provisional transition explosion power.
- Phase-1 hurt reaction uses a non-resetting 20-tick timer, range-1 AABB destruction geometry (4×6×4) and one dangerous skull; exact fallback aim remains an explicit adaptation.
- Phase-2 dash execution owns chargeDirection/chargeFrames/charging state, accepted 20-tick execution, range-2 destruction geometry (6×8×6) and 15 entity damage; exact current speed and preparation trigger remain measurement-gated.
- Official Bedrock Nether Star loot contract is present.
- Dedicated Forge CI passes build + GameTest.
- Latest accepted runtime generation: source `c230bd372ca2ee96bc0396e424071d2f4c06cb3a`, workflow run `36993986762`: **14/14 required GameTests passed** in isolated batches.
- RED→GREEN history is preserved under `history/failure-repair/`.

## Still unresolved / not claimed

- direct current-Bedrock reference measurements for remaining TBD values;
- exact phase-1 special reposition/path generation;
- exact current intra-volley cadence and health-speedup equation;
- exact current passive dangerous-skull interval;
- exact phase-transition action ordering and current binary confirmation of explosion power;
- dash preparation trigger and exact speed/collision termination;
- per-`WitherAttackType` current block-destruction predicate differences;
- exact dangerous-skull reflection vector;
- powered-shield query ↔ native shield-health relationship and armor-layer timing;
- spawn sequence is implemented as the current 220-tick target; direct Bedrock comparative timing/visual acceptance remains pending;
- death sequence duration/explosion/swell/flicker equations;
- Tank comparative acceptance.

## Next action

1. reconstruct the semantic/visual death lifecycle from current BDS death ECS + version-labelled native evidence;
2. implement the special `wither_random_attack_pos_goal` boundary without inventing unresolved position/timing constants;
3. bind remaining shield/death visual values only where current evidence is strong;
4. move unresolved firing-speed, dash-speed and special-movement constants into Tank/direct Bedrock measurement;
5. perform paired Tank acceptance before any final parity claim.

## Safety against stale handoff

This file is the current product truth. Old plans/checkpoints do not override it. Any later product change that materially advances or invalidates this status must update this file or explicitly record why it remains current.
