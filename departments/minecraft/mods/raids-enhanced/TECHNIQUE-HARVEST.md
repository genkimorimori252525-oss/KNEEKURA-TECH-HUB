# Raids: Enhanced — reusable engineering techniques (concept only)

Status: **source-backed research candidates, NOT canonical VALIDATED or deployed implementation**. Source: official [1.20.1 pinned commit `6354ebf97faaeba79affaf7e71d01ed5ae651e85`](https://github.com/FINDERFEED/raidsenhanced/tree/6354ebf97faaeba79affaf7e71d01ed5ae651e85), license All Rights Reserved; implement fresh code rather than copy.

| Technique | Source evidence | Independent reusable contract | KNEEKURA placement | Decision |
|---|---|---|---|---|
| Extra raid wave mini-boss | `RaidMixin` → `REMixinHandler` → `Raid.joinRaid/addWaveMob` | late-wave spawn adapter, idempotent registration, explicit raid affiliation and compatibility gates | Raid Encounter Engineering | **ADOPT CONCEPT**, avoid brittle global Mixin by default |
| Six weapon organs | `RaidBlimpCannonsController`, `RaidBlimpCannon`, bone controller | shared target census, independent FOV/range/LOS, assignment exclusion, cooldown, aim pose, projectiles | Boss Combat Toolkit / Air Combat | **HIGH PRIORITY** |
| Compound airship movement | `RaidBlimpMoveControl`, `RaidBlimpPathNavigation` | decoupled heading, nav nodes, arrival and braking; explicit obstacle checks | WarWareWing / aerial AI | **REFERENCE**, revise inertia model |
| Choreographed underground attack | `RaidDrill` + animation layers | burrow telegraph, invulnerability/visibility gate, bounded valid-surface search, reappear and summon | AI State Machine / encounter FX | **HIGH PRIORITY** |
| Modular melee + mortar | `GolemMeleeAttackGoal`, `GolemBombsAttack` | timed attack arbitration; cone/cylinder hit shapes; ballistic launch; FX markers | Boss Combat Toolkit | **ADOPT CONCEPT**, correct ally/claims boundary |
| Ring wave lightning | `ZapperIllager.LightningsAttack` | concentric radius/count progression, alternating phase offset, server gameplay/client cue separation | Danmaku / Combat FX | **HIGH PRIORITY** |
| Long-form beam Goal | `ZapperIllager.LaserAttackGoal` | wind-up → charge → sustain → recover, deterministic ray clip and collision checks | Boss Combat Toolkit | **ADOPT CONCEPT**, budget tracing |
| Rider-driven flight | `PlayerBlimpEntity` + `PlayerBlimpRotatingPacket` | acceleration, angular inertia, ascent/descent, rider input/authority | WarWareWing | **ADOPT CONCEPT WITH SECURITY GUARD** |
| Bedrock model + animation layers | `FDRaider`, `REModels`, `REAnimations`, cannon bone controller | separated action state/animation, model-bone aim hooks, constrained network events | Rendering / Animation / FDLib comparative | **RESEARCH ONLY**, no asset copy |

## High-value project applications

**Natural Ghast:** six-cannon pattern is more relevant as multiple independent combat emitters than as literal physical guns. Give each emitter unique target eligibility, cool-down, yaw/pitch budget, visibility and allegiance filters; pipe their state into the existing Water Tank orbit/thought observatory. For Ghast flight, preserve the existing bespoke acceleration/feint constraints; this mod's 0.95 damping is evidence of a simple separate approach, **not** a recommended replacement.

**Danmaku:** Zapper expanding radial rings can be re-expressed as a compact function of radius, count, phase offset and emit tick, with projectile geometry and material/particle art authored separately. Respect existing four-color palette design decisions (red/orange/dark red/black) without mirroring source assets.

**WarWareWing:** dual flight designs — automatic Blimp and player-operated craft — can be compared under velocity, turn acceleration and authority tests. The player-vehicle sender validation is a design warning, not proof of a malicious exploit.

**Raid engineering:** raids should be extended by a dedicated adapter with category policy, compatibility matrix and mixin-minimal fallback, not by copying a hard-coded `BadOmen 2/3/4/5` switch.

## Architecture proposed for independent reimplementation

```text
EncounterPolicy (raid scope, difficulty, wave, target membership)
   └─ ActorController (role, state, transition, timers, health/immune policy)
      ├─ Navigation (candidate field, hazard, flight/ground mode)
      ├─ TargetCensus (shared, cached, role filtered)
      ├─ WeaponController[] (cone, occlusion, cooldown, projectile authority)
      ├─ AttackArbitrator (eligibility, priority, exclusivity)
      ├─ ServerEffects (hit, projectile, block-edit gates)
      └─ PresentationEvents (model animation, aim bones, sound, particles)
```

Every emitted state needs explicit provenance `owner/mod-version/runtime-build`, server-client authority, save/load behavior, cancellation during death, and bounded cost. Claim/protection integration must respect native events and explicit protected-region tests.

## Proposed LAB test contracts

1. **Raid correctness:** Bad Omen 1–5, all waves, entity count and `Raid` bookkeeping, faction tags/bell and compatibility with another Mixin owner.
2. **Trajectory comparison:** nav segments, steering target and velocity vs actual observed Blimp movement and independently authored Ghast motion; deterministic seeds.
3. **Independent armament:** six side guns with 0/1/6/30 targets; duplicate-lock rejection; LOS through fluid/solid; cooldown under target death.
4. **Drill:** 51×51 candidate scan bound, protected terrain, water/ceiling/chunk border, 3-vs-5 source config conflict, repeated teleports, serialization.
5. **Boss FX and attack:** 4 radial ring phases, sustained beam and melee hit shapes; server hit vs client effect synchronization; friendly-fire exclusions.
6. **Reliability:** dedicated server + client joins, FDLib versions, peer IDs, pilot-sender authorization, TPS/profile latency, pause/rejoin/save/load and full world restoration.
7. **Provenance:** pin exact mod and FDLib binaries, record hashes, clean test worlds, store bounded test receipts only, do not copy the binaries publicly.

Results: **all NOT_RUN**. Do not claim 20 TPS/animation parity/compatibility until measured.

## Explicit non-adoptions

- Original code or assets: **DO NOT COPY** (All Rights Reserved).
- Global `Raid.spawnGroup()` injector: **NOT A UNIVERSAL DEFAULT**; version and mixin conflicts must be reviewed.
- Original Bad Omen tiers, health, attack damage, projectile values: **NOT GENERIC BALANCE CONSTANTS**.
- The user-reported crashes/Flan bypass: **REVIEW AND REPRODUCE**, not accepted root causes.
