# Twilight Forest — AI / Boss Behavior Map

Status: **major FRONTIER bosses mapped; direct Goal/Target composition cataloged across normal hostile/allied/passive mobs**

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

## FRONTIER normal-mob composition catalog v1

Machine-readable catalogs: `MOB-AI-CATALOG.json` and `CUSTOM-GOAL-CATALOG.json`.

The first whole-tree pass covers **53 non-boss entity classes** under `entity/monster` and `entity/passive`:

- 42 hostile/allied/abstract monster-side classes;
- 11 passive/abstract passive classes.

The catalog intentionally distinguishes **direct Goal/Target registration** from inheritance. A class with no direct registration is not labeled as having “no AI”; it may inherit vanilla/custom Goals or use imperative `tick/aiStep` logic.

Notable reusable compositions found in the direct registrations:

- **Kobold social behavior** — panic when flock members die, seek bread, run away while carrying bread, and flock with same-kind entities are separate Goals.
- **Redcap tactical explosives** — shyness, TNT lighting, and Sapper TNT planting are composable Goals.
- **Home-bounded flight** — Carminite Ghastguard and Wraith use distinct movement Goals around home/arena constraints.
- **Charge reuse** — Boggard, Minotaur, and Pinch Beetle share the charge-action pattern.
- **Breath reuse** — Fire Beetle and Winter Wolf share a breath-attack abstraction.
- **Mounted/rider interaction** — Lower Goblin Knight and Yeti expose rider-specific attack/throw behavior.

This confirms that Twilight Forest uses Goal composition as a reusable behavior library well beyond boss encounters.

## Remaining AI work

- custom Goal lifecycle semantics: mapped for all 43 FRONTIER classes; deeper helper-algorithm review remains for selected complex Goals;
- resolve inherited/imperative behavior for classes with no direct Goal registration;
- compare ANCHOR behavior against FRONTIER;
- separate server-authoritative behavior from client-only animation;
- identify AI patterns added/removed between tracks.

## Verified transition matrix v1

The following transitions were read from concrete Goal/state-machine classes rather than inferred from class names.

| Boss | Controller | Verified transition / trigger |
|---|---|---|
| Naga | `NagaMovementPattern` | `CIRCLE → INTIMIDATE → CHARGE/STUNLESS_CHARGE → CIRCLE`; if the target is above the Naga during INTIMIDATE, route through `CRUMBLE`; `DAZE` returns to CIRCLE |
| Lich | derived phase + phase-gated Goals | Phase 1 while shadow clone or shield > 0; Phase 2 while minions remain/to-summon; Phase 3 otherwise |
| Hydra | body coordinator + `HydraHeadContainer.State` per head | bite, flame and mortar each have beginning/active/ending chains followed by cooldown; head lifecycle includes `DYING → DEAD` and `BORN → ROAR_START → ROAR_RAWR → IDLE` |
| Snow Queen | synced `Phase` enum | `SUMMON → DROP` when summons are exhausted and minions are gone; `DROP → BEAM` after 2–4 successful drops; `BEAM → SUMMON` after its beaming damage budget |
| Alpha Yeti | Goal + synced rampage/tired flags | valid damage enables rampage; rampage runs for 180 ticks; ending it enters a 100-tick non-interruptible tired/recovery Goal |
| Ur-Ghast | damage budget + Goal gating | successful damage drains `damageUntilNextPhase`; reaching zero toggles tantrum; normal attack Goal is disabled in tantrum and incoming damage is divided by 10 |
| Knight Phantom | shared `Formation` + leader broadcast | selected knight can enter `ATTACK_PLAYER_START → ATTACK_PLAYER_ATTACK → WAITING_FOR_LEADER`, then adopts leader state or attacks again |
| Minoshroom | ordinary Goals + synced action flags | ground slam charges 30–59 ticks; charge Goal winds up 15–44 ticks before path-charging |

### Naga timing

`NagaMovementPattern` owns `CIRCLE`, `INTIMIDATE`, `CRUMBLE`, `CHARGE`, `STUNLESS_CHARGE`, and `DAZE`.

- DAZE lasts 60–99 ticks.
- CRUMBLE lasts 20–39 ticks.
- INTIMIDATE adds 15–24 ticks.
- Special “stunless” charge probability is derived from missing health plus local difficulty and clamped to at most 0.5.
- More than 15 damage during a current stun forces CIRCLE.

### Lich phase derivation

```text
shadow clone OR shield > 0
        -> Phase 1
else minions-to-summon > 0 OR live minions > 0
        -> Phase 2
else
        -> Phase 3
```

This is reconstructible encounter state rather than a fragile free-running phase timer.

### Hydra head state machine

```text
BITE_BEGINNING(40) -> BITE_READY(80) -> BITING(7) -> BITE_ENDING(40)
FLAME_BEGINNING(40) -> FLAMING(100) -> FLAME_ENDING(30)
MORTAR_BEGINNING(40) -> MORTAR_SHOOTING(25) -> MORTAR_ENDING(30)
                              ↓
                    ATTACK_COOLDOWN(80)
                              ↓
                            IDLE

DYING(70) -> DEAD
BORN(20) -> ROAR_START(10) -> ROAR_RAWR(50) -> IDLE
```

### Knight Phantom formation durations

`HOVER=90`; small circular formations `=90`; large circular and directional charge formations `=180`; `WAITING_FOR_LEADER=10`; both player-attack stages `=50`.

Machine-readable copy: `BOSS-AI-MATRIX.json`.

## Non-boss inheritance review

The 53-class non-boss catalog has now been manually reviewed for classes that appeared to have no direct Goal/Target registrations.

Resolved patterns include:

- custom-parent inheritance: ArmoredGiant→GiantMiner, CarminiteGhastling→CarminiteGhastguard, MistWolf→HostileWolf, TowerBroodling→SwarmSpider, Raven→FlyingBird;
- vanilla-parent inheritance: KingSpider→Spider, MazeSlime→Slime, Bighorn→Sheep;
- abstract behavior bases: BaseIceMob and Bird;
- corrected extraction false-negative: SkeletonDruid calls AbstractSkeleton registration then adds its own RangedAttackGoal;
- imperative exception: RisingZombie uses aiStep instead of a normal combat Goal scheduler, waking when observed and converting to a vanilla Zombie after its 130-tick emergence.

See `MOB-AI-CATALOG.json` for the per-class resolution.
