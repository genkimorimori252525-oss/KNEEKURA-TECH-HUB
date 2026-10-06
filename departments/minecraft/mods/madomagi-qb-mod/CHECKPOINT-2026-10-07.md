# QB-MOD / Madoka Magica MOD — Static whole-tree checkpoint

Date: 2026-10-07

Branch: `jolly/research-madomagi-qb-2026-10-07`

## State

**STATIC WHOLE-TREE MAPPED, NOT COMPLETE**

The supplied QB-MOD/Garnet-MOD 1.6.4.082 source trees have been inventoried and broadly analyzed across the content-MOD surfaces required by `ANALYSIS-SPEC-v1.md`.

Completion is deliberately not claimed because:
- original Minecraft 1.6.4 runtime has not been executed;
- save/reload defect candidates have not been reproduced;
- performance is static-risk-mapped, not benchmarked;
- historical upstream Issue/PR/fix provenance is unavailable;
- FRONTIER/later upstream is unpinned;
- Minecraft 1.20.1 Forge ANCHOR is designed but not implemented.

## Evidence identity

QB-MOD:
`52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`

Garnet-MOD:
`5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

Texture pack:
`2f868b66ec3d4ea9baae91c8dc601d46b3215be067a17b7ad3ed02fddb636aec`

Full derived ZIP-member manifest receipt:
`4b77975dcf27490fb8365262702c9e66772b2f7a087e044b1182a62bba4e2f89`

Source/class declaration index:
- 193/193 Java declarations parsed;
- 190 classes;
- 3 interfaces;
- 0 parse misses;
- full JSON receipt: `e556bad269ee2216d57e191746ed5f6c6083938a0d99f27ce014bc4091f6ce2c`;
- full TSV receipt: `7bc90ecf3dafb61fcc4e83fea693fb80ec995c7b75cc3c62beb568037462d409`.

## Highest-value recovered systems

### Character combat
- distance-banded short/mid/long attack dispatch;
- staged Musket/Cutlass world props as visible attack stock;
- Madoka homing-arrow rain;
- Homura oscillatory flight, firearm bursts, teleport/TNT and Ultimate execution escalation;
- Kyouko spear fan-out and Rebellion clone pool;
- Sayaka form-bound servant;
- Kirika debuff-first pressure;
- Yuri conditional terrain-to-TNT attack;
- idle Tea Time/self-heal acting goal.

### Projectiles
- Gaussian ballistic;
- delayed acquire-and-home;
- launch-upward-then-home;
- target-lock collision;
- parent-on-impact fan-out;
- embedded projectile→delayed minion;
- kinetic mob projectile;
- motion-matched TNT;
- terrain→hazard conversion.

### Bosses
- Walpurgis world-encounter controller;
- damage cap + super-armor;
- low-health attack phase;
- anti-air punishment;
- terrain-to-TNT conversion;
- projectile-seeded minions;
- encounter ambience/death staging;
- Kriemhild drain/heal giant;
- Homulilly teleport retaliation;
- Nutcracker collision destruction/servant ecosystem;
- Charlotte replacement/revival phase;
- Oktavia kinetic Wheel bursts.

### Ecology
- age-driven familiar metamorphosis;
- kill-accelerated evolution;
- ecosystem population caps;
- maturation loops;
- parent/servant kill feedback;
- inventory/armor mutation attacks;
- hostile character imitation archetypes.

### Progression
- QB rare contract NPC;
- clean Grief Seed → Soul Gem acquisition;
- damaged Grief Seed → tiered QB resource economy;
- inverse JB economy;
- weapon-class-gated Incubator drop;
- witch → Grief Seed → purification/crafting/incubation loop;
- hidden still-water+glass Nutcracker ritual.

### Framework / architecture
- Garnet owner/mode/follow/servant foundation;
- owner combat-intent propagation;
- generic projectile/gun framework;
- safe-position teleport fallback;
- target capability categories;
- one concrete Garnet→QB reverse dependency that should be removed in ANCHOR.

## Continuation findings added after the initial checkpoint

### Historical/version boundary
- contemporary 2013-11 material pins a public 1.6.4.080-era update and actual .080 installations;
- supplied .082 archive members cluster around 2014-01-04, with late-December/early-January Rebellion/Homulilly source work;
- public GitHub repository/code searches did not establish a supported later source lineage; FRONTIER remains **unfound/unpinned**, not disproven;
- .080 community description of Homura UF resembles .082 Homura Rebellion much more than .082 Ultimate, producing a strong but unproven version-delta lead.

### Stronger binary correspondence
Selected `javap -c -p` method-body spot checks verify that several unusual source findings are present in the shipped classes:
- Grief Seed `nextInt(5)` + unreachable-through-selector Walpurgis default;
- Homulilly `nextInt(1)`;
- Walpurgis self-poison anti-air fallback;
- additive `setSoulGemDamage`;
- shared GUI container field;
- Garnet packet byte-zero read;
- JB inverse economy threshold behavior.

This upgrades those specific findings from Java-text-only observations to **selected source+distributed-bytecode correspondence**, while full 193-class semantic equivalence remains NOT_ANALYZED.

### Presentation/readability
A dedicated telegraph/VFX pass recovered:
- Mami Muskets and Sayaka Cutlasses as visible, mechanically consumed attack stock;
- Homura 128-particle teleport trail + dual endpoint sounds;
- Homura-vs-Walpurgis firework as a presentation/tracer entity distinct from TNT damage;
- corruption and Grief Seed countdown expressed through escalating particle density;
- Prickle's embedded one-second-ish delayed-minion telegraph;
- Light Arrow pulsing crossed-plane renderer;
- Charlotte 0.5×→5× model/scale phase discontinuity;
- Walpurgis world ambience, rotating gear silhouette, health-linked shaft angle and sustained death fireworks;
- Garnet command modes using redundant text + click sound + semantic particle feedback.

The modernizable lesson is **state readability**, not the literal GL11/particle implementation.

## Strong static defect / anomaly candidates

Not historically proven bugs unless stated otherwise:

- Walpurgis anti-air poison targets the boss itself;
- Grief Seed special `isHomulilly` ritual state is not persisted;
- Charlotte second-form state is not persisted;
- witch ecology age/summon clocks are not persisted;
- encounter/master object references are mostly runtime-only;
- Walpurgis singleton admission flag is process-local, not world-persisted;
- Oktavia wheel spawn prints to stdout inside candidate loops;
- Homulilly uses `nextInt(1)`, leaving an apparent selection branch unreachable;
- Grief Seed `nextInt(5)` makes its switch default/Walpurgis branch unreachable;
- TexturePack Madoka UF starts with full-width `ｍ`, not ASCII `m`;
- Garnet target AI directly references QB Nutcracker;
- Garnet source contains stale external imports absent from shipped class references;
- legacy shared GUI handler stores mutable request-specific container state;
- legacy gun packet reads byte 0 without visible length validation;
- Sayaka Bat connected-block breaker has no explicit work cap;
- Kriemhild has a possible duplicate Grief Seed death path requiring runtime/lifecycle proof;
- Oriko/Yuma/Jewel config slots exist without usable implementation;
- Madoka Ribbon is simultaneously contract/control token and 100-damage weapon against EntityMadomagi.

## ANCHOR direction

Minecraft 1.20.1 Forge reconstruction should preserve behavioral intent but replace legacy mechanisms:

- numeric IDs → registry keys / DeferredRegister;
- DataWatcher → SynchedEntityData;
- username ownership → UUID;
- static Walpurgis gate → SavedData-backed encounter registry;
- Packet250 → typed server-validated channel;
- singleton GUI container → per-player MenuType/AbstractContainerMenu;
- hardcoded protected blocks → block tags;
- raw parent references → durable encounter/master IDs;
- synchronous terrain mutation → bounded `EncounterBlockEditService`;
- mass TNT → encounter-budgeted hazard system;
- direct health/capability mutation → rule-aware combat mechanics;
- global ambience mutation → scoped/reversible encounter presentation.

## Next evidence, in priority order

1. **Bounded Minecraft 1.6.4 save/reload verification**
   - Homulilly ritual seed;
   - Charlotte second form;
   - witch age;
   - parent-linked servants;
   - Walpurgis restart admission.

2. **Bounded legacy combat observation**
   - projectile trajectories;
   - staged weapon arrays;
   - boss phases;
   - encounter cleanup.

3. **Performance probes / ANCHOR LAB reconstruction**
   - terrain edits;
   - target searches;
   - projectile counts;
   - minion population;
   - ItemBreaker connected structures.

4. **Historical archive recovery**
   - original forum snapshots;
   - older/newer release ZIPs;
   - repair/change history.

5. **FRONTIER search**
   - determine whether a later source/release lineage exists and keep it separate from the 1.6.4.082 track.

Until those steps are performed, the current static findings are the correct stopping boundary for source-only analysis.
