# Wither: Reincarnated — AI and Combat Behavior

Evidence basis: static inspection of exact v1.0.5 ANCHOR JAR
`00589726de7d82628d92761394a8a3e6b153c28942f50c9ae6ba7860b0fab80a`.

This document describes the distribution bytecode/resources. It does not claim
that every timing was observed in a running game.

## 1. Health bands and targeting

The implementation has two explicit health thresholds that create three practical
combat bands.

### Above 2/3 max health

In the default configuration, player-target acquisition and retaliation against
players are gated off until health reaches the 2/3 region. A generic living-target
selector excludes players.

Practical result: the opening favors non-player targets and environmental
destruction rather than immediately focusing the player.

### At or below 2/3

The player-target path becomes available and the charge attack is eligible.
The ranged goal also begins its more active orbit/strafing combat.

### Powered/final state

Default powered entry is at approximately 1/3 max health, with hysteresis so the
state is not cleared by tiny healing oscillations; static bytecode shows the
powered state can remain until health rises above roughly 1/2.

The optional vanilla-phase configuration changes this threshold family, using a
higher entry/exit band.

While powered, projectile damage is rejected and several attack/movement timings
become more aggressive.

These are **Reincarnated design choices**, not Bedrock Wither evidence.

## 2. Goal stack

The server-side replacement path installs the following attack/movement priorities:

| Priority | Goal | Function |
|---:|---|---|
| 1 | `WitherBarrageGoal` | rare large-area projectile barrage |
| 2 | `WitherLaserGoal` | telegraphed continuous beam |
| 3 | `WitherChargeGoal` | wind-up, dash, collision and stun |
| 4 | `WitherBackUpGoal` | powered close-range spacing |
| 5 | `WitherRangedAttackGoal` | normal/dangerous skull combat + strafing |
| 6 | `WitherRandomTravelGoal` | long-distance travel/reposition |
| 7–8 | look goals | presentation/orientation |

This decomposition is one of the most reusable parts of the design: each high-level
attack owns its own start/continue/tick/stop lifecycle rather than sharing one
monolithic combat tick.

## 3. Charge

Static contract:

- available in the default design after the 2/3-health gate;
- approximately 20 ticks of preparation;
- direction/velocity is then committed into a dash;
- nearby entities are collected from the charge collision volume;
- configured direct damage default: 30;
- a successful shield interaction disables the defender's shield for a configured
  default of 400 ticks;
- if the damage attempt is rejected/blocked, the Wither enters an 80-tick stun;
- the recovery step pushes nearby living entities away;
- powered/final state uses shorter configured cooldown bounds and a more aggressive
  vertical movement component.

Reusable lesson: charge is represented as preparation → execution → collision
result → recovery/cooldown, not as generic navigation with damage attached.

## 4. Laser

The laser is server-authoritative and is not implemented as a separate projectile
entity.

Static contract:

- about 60 ticks of telegraph/preparation;
- tracks a target angle;
- ray-marches in 0.25-block increments;
- configured maximum beam length defaults to 128 blocks;
- beam length is truncated when the scan reaches blocking geometry;
- living entities intersecting the sampled beam are damaged by the server;
- configured laser damage default is 3;
- Wither effect duration is applied by the attack path;
- powered/final state turns/tracks more aggressively;
- the client receives angle/length state and reconstructs the beam visually.

At the configured maximum, the spatial scan can consider roughly
`128 / 0.25 = 512` sample steps in an active tick before other hit tests. This is
a static cost surface, not a measured TPS result.

## 5. Barrage

The barrage owns a bounded 150-tick sequence:

- early ticks: rotation/preparation;
- tick ~30: sound plus a large visual burst;
- next section: vertical ascent;
- ticks ~60–119: three Wither skulls are created per tick;
- late section: descent/recovery.

If uninterrupted, the firing window can create approximately 180 skull entities.

Configured cooldown defaults span roughly 1200–3600 ticks. This attack should be
treated as a rare high-entity-count stress case when designing performance tests.

## 6. Ranged orbit combat

`WitherRangedAttackGoal` owns both projectile cadence and lateral strafing/orbit
movement.

The class retains:

- normal attack timer;
- powered and normal strafe speed bounds/change amounts;
- strafe direction;
- previous target position;
- dangerous-skull state;
- animation tick state.

A dangerous main-head skull is selected probabilistically in non-powered combat.
Powered combat accelerates pressure while relying on projectile immunity rather
than simply increasing every projectile type.

## 7. Dangerous skull reflection

The MOD modifies vanilla `WitherSkull` behavior instead of introducing a wholly
separate projectile type.

Static behavior:

1. a dangerous skull is made hittable;
2. when struck by a LivingEntity, the original skull is discarded;
3. a new dangerous `WitherSkull` is created at the same location;
4. the attacker becomes the new projectile owner;
5. the attacker's look direction determines the return launch direction;
6. a reflected dangerous skull near a Wither is assisted into projectile hit
   handling, reducing near-miss ambiguity;
7. skulls are bounded by a roughly 200-tick lifetime.

Configured damage defaults recovered for this exact release:

| Case | Default |
|---|---:|
| normal skull direct | 16 |
| normal skull explosion damage | 12 |
| normal explosion size | 2 |
| dangerous skull direct | 22 |
| dangerous skull explosion damage | 18 |
| dangerous explosion size | 5 |
| dangerous skull returned to Wither | 30 |

Reusable lesson: ownership transfer is cleaner than merely multiplying the
velocity by -1 when a projectile changes allegiance.

## 8. Possession subsystem

Possession is implemented as state attached to ordinary Mobs rather than replacing
them with a special possessed entity.

`PossessedCapability` persists:

- possession time;
- intended possession duration;
- cooldown;
- owner entity/UUID state.

The state is serialized to NBT and synchronized to clients.

Eligibility observed in the server path includes:

- Mob;
- undead MobType;
- not in the `wither_cant_possess` tag;
- valid/attackable relative to the Wither;
- possession feature enabled;
- range and random-selection conditions.

The Wither searches a large local living-entity region (64-block AABB inflation in
the inspected path). The random gate used by the selected v1.0.5 path is sparse
rather than possessing every eligible mob immediately.

Observed configured/state behavior includes:

- temporary possession lasting on the order of 600–2400 ticks;
- separation/owner-invalid termination, including a 96-block distance check;
- approximately 1200 ticks of post-possession cooldown;
- temporary Speed while possessed;
- post-release debuffs and an unpossess sound;
- dedicated follow/owner-hurt target goals;
- alliance logic so owner and possessed mobs do not fight each other.

This design demonstrates an extensible "temporary faction overlay" over existing
Mob types.

## 9. Mob fear and data-driven exceptions

A general AI modification makes ordinary pathfinding mobs avoid the Wither unless
they are opted out or currently possessed.

The exception surface is data-driven through tags rather than a hard-coded list.
That is preferable for a modpack-facing boss because other mods can supply
compatibility data without patching the boss code.

## 10. Lifesteal

Damage caused by the Wither or a possessed minion can generate a delayed lifesteal
effect moving toward the owning Wither. On arrival, the owner heals for a fraction
of the source damage.

The vanilla WitherSkull heal path is separately suppressed to avoid double healing.

Reusable lesson: when adding a new global healing policy, first neutralize the
legacy healing source that would otherwise stack with it.

## 11. World interaction

The Wither performs regular bounded terrain destruction when mob griefing permits.
The inspected v1.0.5 path considers a compact cuboid around the entity at a
periodic interval rather than performing an unbounded flood or path search.

The boss also contains:

- time-of-day manipulation while active;
- time restoration behavior during death;
- anti-Elytra behavior that can force nearby fall-flying players out of flight;
- extended spawn/death presentation.

These mechanics are part of the MOD's authored encounter and should not be
generalized into Bedrock behavior without independent evidence.

## 12. What to reuse

Strong reusable concepts:

- independent Goal per major attack;
- health threshold as eligibility input, not the entire state machine;
- explicit preparation/execution/recovery attack phases;
- projectile ownership transfer for deflection;
- temporary faction/owner state as a capability;
- data tags for cross-MOD exclusions;
- server authority with compact client presentation sync.

Do not reuse Reincarnated numeric constants as generic boss defaults.
