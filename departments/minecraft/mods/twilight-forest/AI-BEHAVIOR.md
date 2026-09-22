# Twilight Forest — AI / Boss Behavior Map

Status: **major FRONTIER bosses mapped; full mob catalog still in progress**

Source snapshot: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828`.

## Design taxonomy

Twilight Forest does not use one universal boss-AI framework. It mixes four reusable control styles:

1. prioritized Minecraft Goals;
2. explicit boss phases;
3. local finite-state machines for multipart sub-actors;
4. synchronized group/formation state.

This is more valuable than any single boss class: the project chooses the control model that fits the encounter.

## Naga — Goal composition + dynamic multipart body

Evidence:

- `src/main/java/twilightforest/entity/boss/Naga.java`
- blob `e30e1371af2bdd140bf368601adc71596469abfa`

Goal order includes Float, SimplifiedAttack, NagaSmash, NagaMovementPattern, return-home behavior and restricted wandering. Target selection is also bounded by the arena/home constraint.

The body has up to 12 segments. Segment count follows health; losing segments removes body parts and changes movement speed. Server AI also handles arena recovery, block/leaf destruction, healing after a damage-free interval and path advancement.

**Reusable pattern:** combat, arena ownership and body topology are one encounter system rather than independent features.

## Lich — three-phase encounter inside the Goal scheduler

Evidence:

- `src/main/java/twilightforest/entity/boss/Lich.java`
- blob `070bae826b6862ddb1cac7a440ed4db76fa83734`

The source labels:

- Phase 1 → `LichShadowsGoal`
- Phase 2 → `LichMinionsGoal`
- Phase 3 → direct melee

Supporting state includes shield strength, minion budget, attack/pop cooldowns, teleport invisibility, master/clone identity and summoned-clone IDs. Phase 3 attempts normal melee navigation first and teleports to line of sight if navigation cannot reach.

**Reusable pattern:** keep normal Goal scheduling, but let explicit encounter phase gate Goal eligibility.

## Hydra — authoritative coordinator + one state machine per head

Evidence:

- `src/main/java/twilightforest/entity/boss/Hydra.java`
- `src/main/java/twilightforest/entity/boss/HydraHeadContainer.java`
- Head-container blob `9ae85ee35800d8776d8d07d6d27773db140dfd1f`

Each head owns timed states:

```text
IDLE
BITE_BEGINNING -> BITE_READY -> BITING -> BITE_ENDING
FLAME_BEGINNING -> FLAMING -> FLAME_ENDING
MORTAR_BEGINNING -> MORTAR_SHOOTING -> MORTAR_ENDING
ATTACK_COOLDOWN -> IDLE
DYING -> DEAD
BORN -> ROAR_START -> ROAR_RAWR -> IDLE
```

The body coordinator selects attacks by distance/chance, limits concurrent attacks, weights bite attacks more heavily, assigns the primary target to available heads, allows side heads to select secondary targets, respawns heads and persists active-head state.

Damage is also multipart-aware: hits to an open mouth are treated differently from armored parts.

**Reusable pattern:** one server-authoritative coordinator schedules multiple semi-autonomous combat actors, while each actor owns a deterministic local state machine.

## Snow Queen — explicit SUMMON / DROP / BEAM phases

Evidence:

- `src/main/java/twilightforest/entity/boss/SnowQueen.java`
- blob `4ab76655c39b9f944ca6612ac398f6a6e5257c9c`

Explicit phase enum:

```text
SUMMON
DROP
BEAM
```

Corresponding Goals are `HoverSummonGoal`, `HoverThenDropGoal`, and `HoverBeamGoal`. Phase is synchronized in entity data and the boss maintains seven ice-shield parts.

**Reusable pattern:** phase enum + phase-specific Goals + synchronized presentation-visible state.

## Alpha Yeti — high-power action followed by recovery

Evidence:

- `src/main/java/twilightforest/entity/boss/AlphaYeti.java`
- blob `c058c2521e795450935f81f642135850af7817d6`

Key Goals:

- `YetiTiredGoal`
- `YetiRampageGoal`
- ranged attack
- grab/throw rider
- restriction/home movement

Rampage and tired are synchronized flags. A rampaging landing produces an area hit/knock-up; entering tired state removes immediate rampage eligibility.

**Reusable pattern:** strong attack state → explicit recovery/vulnerability state.

## Ur-Ghast — flight/attack Goals + damage-budget phase switching

Evidence:

- `src/main/java/twilightforest/entity/boss/UrGhast.java`
- blob `b3e0adad4b546e82087ec42443bc6f546eea0962`

Goals:

- `UrGhastFlightGoal`
- `UrGhastLookGoal`
- `UrGhastAttackGoal`
- player target

The boss stores attack status/timers, charging and tantrum state. A `damageUntilNextPhase` budget triggers phase switching. During tantrum incoming damage is heavily reduced. The encounter also tracks trap locations and uses no-clip movement.

**Reusable pattern:** phase transitions can be driven by accumulated incoming damage rather than only health percentage or elapsed time.

## Knight Phantom — synchronized group formation controller

Evidence:

- `src/main/java/twilightforest/entity/boss/KnightPhantom.java`
- blob `9568efbfc7ed4ebb151905c04606bc74eb460b84`

Goals coordinate watching, formation movement, attack start and weapon throwing.

Formation states include:

- HOVER
- LARGE / SMALL CLOCKWISE
- LARGE / SMALL ANTICLOCKWISE
- four directional CHARGE formations
- WAITING_FOR_LEADER
- ATTACK_PLAYER_START
- ATTACK_PLAYER_ATTACK

Nearby knights synchronize formation and progress with a leader. Charging changes attack/armor modifiers and physical dimensions.

**Reusable pattern:** group AI can be deterministic around a shared formation state and progress clock instead of every unit independently choosing motion.

## Minoshroom — conventional Goals with small synchronized action state

Evidence:

- `src/main/java/twilightforest/entity/boss/Minoshroom.java`
- blob `c74fe6b7e56ecded49dde145976e0249cea853a5`

Goal priority combines ground attack, charge, melee, home restriction, wandering/look and player targeting. Synced state exposes charge and ground-attack progress so the client can animate and emit particles.

**Reusable pattern:** ordinary Goal AI remains sufficient when only a few encounter actions need explicit state.

## Shared extraction model for KNEEKURA

Do not force these into one giant generic “BossAI”.

Prefer composable units:

- `GoalSchedule`
- `PhaseState`
- `LocalActorStateMachine`
- `GroupFormationController`
- `ArenaConstraint`
- `MultipartController`
- `SyncedPresentationState`
- `AttackBudget / CooldownPolicy`

A boss should compose only the pieces it needs.

## Remaining AI work

- inventory every custom Goal and activation/stop condition;
- map normal hostile/passive mob AI;
- compare ANCHOR behavior against FRONTIER;
- separate server-authoritative behavior from client-only animation;
- identify AI patterns added/removed between tracks.
