# Garnet-MOD 1.6.4.082 — Framework and shared AI analysis

Primary evidence:
- Garnet archive SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`
- QB archive SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`

Garnet is not merely a bullet dependency. It provides most of the owner/servant/target/follow/combat framework used by QB-MOD.

## Base entity contract

`EntityGarnetBase` contributes:
- attackDamage attribute registration;
- periodic auto-healing hook;
- generic physical protection percentage;
- enchantment-aware melee attack;
- synchronized `isFlying` state;
- custom flying movement that bypasses normal fall behavior;
- shared texture-location convention.

This lets character classes concentrate on attacks/forms rather than rebuilding movement/damage plumbing.

## Tameable/owner state

`EntityGarnetTameable` synchronizes:
- enable/contracted flag;
- tactical mode;
- owner name.

Persistence stores owner as player-name string and mode as byte.

Interaction with the control item:
- unowned/disabled entity → becomes enabled, clears path/target, owner becomes interacting username, enters Standby;
- enabled + same owner → cycles mode.

QB-MOD overrides the control item globally through `EntityMadomagi.getControlItemID()` to Madoka's Ribbon and changes enable message to `Contracted!`.

Technique: **one interaction token both establishes ownership and later cycles tactical command state**.

ANCHOR must use owner UUID/profile identity, not mutable username strings.

## Tactical modes

Cycle:
- Standby
- Satellite, if enabled by config
- Free
- Follow
- back to Standby

Each transition:
- updates synchronized mode byte;
- dismounts;
- emits owner chat text;
- plays click sound;
- emits distinct particle type.

Mode is therefore both simulation state and presentation feedback.

### Standby

`EntityGarnetAIStandby`:
- also runs for disabled entities;
- while grounded/out of water, claims mutex and clears navigation path.

### Follow vs Free

`EntityGarnetAIFollowOwner` uses the same follow task for both, but different distance bands.

Free mode does **not** mean no owner-follow behavior. It simply allows a larger roaming radius before follow begins and stops farther from the owner.

If pathfinding fails and owner distance squared >=225:
- searches a 5×5 ring around owner;
- requires solid support and two free blocks;
- directly teleports companion to the valid location.

Technique: **pathfinding follower with distance-triggered safe-position teleport fallback**.

### Servant follow

`EntityGarnetAIFollowMaster` implements the same concept for non-player masters, with teleport fallback at distance squared >=144.

## Owner/master combat propagation

Garnet provides event-style target mirroring:
- owner hurt by enemy → companion attacks that enemy;
- owner attacks enemy → companion attacks that enemy;
- servant master hurt → servant attacks that enemy.

This is implemented by comparing the owner's latest hurt/attack timestamp so the task responds to a new combat event rather than continuously rewriting target state.

Technique: **combat-intent propagation through last-event counters**.

## Target suitability filter

`EntityGarnetAITarget.isGarnetSuitableTarget` adds policy over vanilla targeting:

- rejects self/dead entities;
- Creeper is rejected unless host explicitly supports explosive enemies;
- Ghast or `IGarnetEnemyFlying` targets are rejected unless host supports flying enemies;
- companions with the same owner are rejected;
- owner itself is rejected;
- invulnerable player targets are rejected for unowned entities under normal selection;
- home/range, sight and optional easy-reach/path checks apply.

Technique: **capability-gated target classes**, particularly explicit `canAttackFlying` / `canAttackExplosive`.

Modern KNEEKURA version should express this through traits/tags/capabilities rather than hardcoded Java class tests.

## Flying-target special search

When the selector is exactly `IGarnetEnemyFlying.garnetEnemySelector`, `EntityGarnetAINearestAttackableTarget` performs a custom search:
- scans targetClass in ±32 cube through the flying selector;
- separately appends Ghasts;
- Dragons;
- Withers;
- Homulilly Nutcracker;
- optional broad targetClass list when `allTarget` is true;
- sorts by distance and picks the first suitable entity.

This was an early attempt at a **cross-class tactical target category** before modern entity tags.

## Important architecture defect: Garnet ↔ QB reverse coupling

Although QB declares `after:Garnet-MOD`, Garnet's target AI source imports:

`puellamagi.mods.entity.monster.EntityHomulillyNutcracker`

and directly adds that class to its flying-target search.

The compiled `garnet.mods.EntityGarnetAINearestAttackableTarget.class` also contains the constant-pool class reference:

`puellamagi/mods/entity/monster/EntityHomulillyNutcracker`

An exhaustive scan of Garnet class files found this as the only compiled class containing a `puellamagi/` reference.

Therefore the framework is **not cleanly dependency-inverted**: the lower layer contains one concrete upper-layer QB type.

No claim is made here that standalone Garnet necessarily crashes; exact JVM/LaunchClassLoader resolution behavior and execution path would need runtime testing. But compile/runtime coupling is directly present in the distributed binary.

ANCHOR fix:
- remove QB class knowledge from framework;
- mark Nutcracker through a generic flying/enemy trait or entity tag;
- let QB register its own classification.

## Search-cost concern

`EntityGarnetAINearestAttackableTarget.continueExecuting()` returns:

`super.continueExecuting() && this.shouldExecute()`

Thus a continuing target task can call the full `shouldExecute` acquisition path repeatedly, including AABB scans, list concatenation and sorting.

For flying-target logic this can mean several ±32-cube queries on continuation checks.

This is a static performance-risk lead, not a measured TPS result.

ANCHOR design:
- retain current target until invalid/lost;
- perform expensive candidate acquisition on a budget/cooldown;
- separate target validation from target search.

## Attack-on-collide improvements over vanilla-style behavior

`EntityGarnetAIAttackOnCollide` adds:
- configurable attack cooldown;
- configurable extra range;
- path recompute jitter;
- failed-path penalty that grows by 10;
- stops continuation once failed-path penalty reaches 100.

Technique: **pathfinding backoff coupled to melee pursuit**.

## Full-auto networking

`PacketHandler` receives legacy custom payload:
- requires server-side player;
- checks currently equipped item is `ItemGarnetGun`;
- writes `packet.data[0]` into the held gun ItemStack's FullAuto state.

Positive boundary:
- packet cannot directly mutate an arbitrary non-gun held stack.

Risks:
- no visible payload-length check before `data[0]`;
- client input state is being transmitted directly as a weapon-control flag;
- legacy channel/direction model.

ANCHOR should use a typed packet with:
- exact payload validation;
- direction check;
- server-side cadence/ammo/reload authority;
- optional sequence/rate limiting.

## Source-only stale imports

Two Garnet Java files contain external imports that are never referenced in their bodies:

- `EntityGarnetAIFollowMaster.java` imports `itzombie.mods.entity.passive.EntityKorezon`;
- `EntityGarnetServant.java` imports `cunyarlko.mods.entity.passive.EntityKuko`.

The corresponding compiled classes contain no Korezon/Kuko references.

Interpretation:
- these look like development-history residue, not runtime dependencies of those class binaries;
- however a clean source compile can still fail if the imported packages are unavailable because Java resolves imports.

This further supports treating the shipped source as authoritative static evidence while **not assuming it is a turnkey reproducible source release**.

## Reusable Garnet primitives

Preserve independently:
1. owner/control-token contract;
2. tactical mode machine;
3. relaxed Free-mode follow radius;
4. safe-position teleport fallback;
5. master/servant lifetime and follow relation;
6. owner combat-intent propagation;
7. target capability filters;
8. target-search cooldown/backoff;
9. flying entity movement flag/base;
10. parameterized gun state machine;
11. generic projectile ownership and enchantment logic.

Do not port the QB-specific reverse dependency.