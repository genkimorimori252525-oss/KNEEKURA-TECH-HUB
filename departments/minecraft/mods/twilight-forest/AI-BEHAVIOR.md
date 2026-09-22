# Twilight Forest — AI / Boss Behavior Map

Status: **major bosses mapped at first-pass level; full mob catalog still in progress**.

## Shared boss infrastructure in FRONTIER

A dedicated `BaseTFBoss` now centralizes boss-bar handling, custom death animation hooks, and server-side boss-bar ticking. This class does not exist in the ANCHOR tree under the same path.

Bosses are also constrained to their landmark/home structures rather than behaving as unconstrained vanilla mobs. Several bosses add restriction-return goals and validate targets against the home region.

## Naga

FRONTIER goal priority:

1. Float
2. Simplified attack
3. Naga smash
4. `NagaMovementPattern`
5. return-home behavior
8. random stroll only while inside home and without target

Targeting uses retaliation plus nearest player, but player targeting is rejected when attacker/target violates the home-area constraint.

Important mechanics:

- body segment count is derived from health;
- losing segments modifies movement and destroys tail parts;
- server AI can destroy leaves/blocks while charging or outside home;
- it teleports home when trapped too far below its restriction point;
- it heals after a damage-free interval;
- stun damage can force its movement pattern back into circling.

This is not merely GoalSelector composition: a considerable part of the encounter state is maintained directly in boss tick/server-AI code.

## Lich

The latest Lich explicitly exposes three combat phases through goal eligibility:

- Phase 1: shadow/clone behavior through `LichShadowsGoal`;
- Phase 2: minion behavior through `LichMinionsGoal`;
- Phase 3: direct melee.

Supporting state includes shield strength, minions remaining, attack type, teleport invisibility, master/clone references, cooldowns and summoned-clone identity.

Home recovery can switch from navigation to teleport when pathing fails. This is a strong pattern for boss reliability: normal navigation first, encounter-preserving fallback second.

## Minoshroom

Goal priority includes:

- ground attack;
- charge attack;
- melee attack;
- return-to-restriction goals;
- normal wandering/look behavior.

The charge and ground-smash states are synchronized entity data; the client turns those states into animation/particles. This is a clean server-authoritative behavior → synchronized state → client presentation boundary.

## Knight Phantom

Knight Phantoms implement group-level encounter state, not independent identical mobs.

The formation enum includes:

- hover;
- large/small clockwise and anticlockwise formations;
- four directional charge formations;
- leader-wait state;
- attack-start and attack-execution states.

Custom goals coordinate watching/attacking, formation movement, attack start and thrown weapons. Shared boss-bar progress aggregates nearby group health. Loot/death behavior depends on whether the group still has surviving members.

## Other major bosses

The full classes for Hydra, Ur-Ghast, Snow Queen and Alpha Yeti are pinned in the inventory and are in the next deep-pass set. Their class families already show that the encounters use dedicated subordinate entities/goals rather than one monolithic boss method:

- Hydra: head, neck, multipart body and mortar entities;
- Ur-Ghast: dedicated flight/attack/look goals;
- Snow Queen: shield entity and custom combat state;
- Alpha Yeti: rampage/tired state goals.

## Reusable design lesson

Twilight Forest does not rely on a single “smart AI” abstraction. It composes:

- vanilla goals;
- custom goals;
- synchronized flags/data;
- boss-local finite states;
- group/formation state;
- landmark/home restrictions;
- server-authoritative encounter rules;
- client-only animation and effects.

That layered approach is a better extraction target than copying individual AI classes.
