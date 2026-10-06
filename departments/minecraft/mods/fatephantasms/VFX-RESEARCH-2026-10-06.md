# FatePhantasms VFX Research — 2026-10-06

Status: **STATIC RECONNAISSANCE / DEPENDENCY-SOURCE ANALYSIS**  
Target: `Terry0333/FatePhantasms`  
Primary interest: **how the Mod achieves unusually strong combat presentation and what can be reconstructed as reusable 1.20.1 Forge design knowledge**

This report follows the TECH HUB distinction between target evidence, dependency evidence, secondary behavior hints and inference. It does **not** claim that every Photon capability below is used by FatePhantasms. Exact target bindings remain pending until the distributed JAR can be inventoried.

---

## 1. Evidence classes used here

- **DIRECT_OBSERVATION — TARGET METADATA**: GitHub repository/release data or upstream README directly inspected.
- **AUTHOR_CLAIM — TARGET**: behavior/change described by the target author's release notes.
- **DIRECT_OBSERVATION — DEPENDENCY SOURCE**: inspected Photon 1.20.1 source.
- **INFERENCE — TARGET USE**: a plausible FatePhantasms implementation derived from target dependency declarations plus dependency capabilities, but not yet proven from target bytecode/resources.
- **SECONDARY_BEHAVIOR_HINT**: an independent implementation explicitly describing itself as FatePhantasms-like. Useful for search/design hypotheses only.
- **UNKNOWN**: not established by the evidence currently acquired.

---

## 2. Target identity and current release

### ANCHOR / current observed release

- Repository: `https://github.com/Terry0333/FatePhantasms`
- Minecraft: **1.20.1**
- Loader: **Forge**
- Release tag: `8`
- Release name: `FatePhantasms-1.0.0-r284`
- Published: **2026-10-06**
- Asset: `FatePhantasms-1.0.0-r284.jar`
- Size: **4,445,896 bytes**
- GitHub-published SHA-256:
  `68158d03ae033577def23d51c4e238c8f9aa082243c8da16fbe0e4f9a3fcc88c`

The current default branch exposes a README but not the Mod's full source tree. The README describes the project as a Fate Noble Phantasm/skill Mod and links an Ea showcase; it also states that the Mod code was developed through automods.cn AI.

**Finding:** source-available whole-target interpretation is not possible from the upstream default branch alone. Distribution bytecode/resources are the required next authority for implementation claims.

---

## 3. Release chronology: presentation is a first-class subsystem

The release history is unusually informative because multiple releases explicitly describe presentation work rather than only damage/balance changes.

| Release | Upstream note | Engineering interpretation |
| --- | --- | --- |
| r205 / tag 1 | summoning animation and some effects changed; skill chant expanded to a full version; some animation changed; overall cast duration became longer | **AUTHOR_CLAIM — TARGET.** Timing/choreography was intentionally lengthened for presentation rather than minimized for responsiveness. |
| r224 / tag 2 | “enhanced effects” version; **Photon + LDLib required**; chant/charging effects heavily reworked; multiplayer animation/effects tested/fixed | **Critical transition.** Strong evidence that the VFX architecture changed materially here and that dependency-backed FX became central. |
| r225 / tag 3 | key/summon animation adjusted | Continued refinement of summon readability. |
| r250 / tag 4 | summoning animation changed; skill-use held-item position fixed | Presentation includes pose/hand-placement correctness, not only particles. |
| r278 / tag 5 | added **Chain of Heaven / Enkidu** and **Gate of Babylon** | Introduces spatially complex multi-origin skills suitable for gate/chain/projectile choreography. |
| r280 / tag 6 | skills ignore resistance | Gameplay rule change; useful separator from VFX changes. |
| r282 / tag 7 | compatibility improved for damage against bosses from other Mods; Photon + LDLib still required | Integration/gameplay compatibility pass; VFX dependency remains. |
| r284 / tag 8 | holding Ea allows flight; multiplayer bugs fixed | Current observed release. |

### Main conclusion from chronology

The strongest architectural clue is **r224**.

Before r224, the author was already iterating summon/chant timing. At r224, the project explicitly became an “enhanced effects” build, added Photon + LDLib as prerequisites, and heavily reworked chant/charge effects while also addressing multiplayer presentation. That combination makes r205 → r224 the highest-value binary differential for recovering the actual VFX migration.

This does **not** prove which Photon classes/resources FatePhantasms invokes. It does establish that Photon/LDLib adoption and a major VFX rework occurred together according to the author.

---

## 4. Why Photon is technically capable of producing this style

Photon's own 1.20.1 branch was inspected because FatePhantasms declares it as a prerequisite. The dependency source reveals several mechanisms that match the kinds of presentation FatePhantasms is trying to create.

### 4.1 FX attached to a moving entity

Source:
`Low-Drag-MC/Photon@1.20.1/common/src/main/java/com/lowdragmc/photon/client/fx/EntityEffect.java`

**DIRECT_OBSERVATION — DEPENDENCY SOURCE**

Photon's entity effect wrapper:

- associates an FX runtime with a Minecraft entity;
- updates the FX root position every rendered frame using interpolated entity position;
- supports positional offsets;
- supports root rotation and scale;
- destroys the runtime when the bound entity dies;
- can prevent duplicate instances of the same effect;
- supports automatic orientation modes based on:
  - entity forward direction,
  - look direction,
  - visual Y rotation.

### Why this matters for Fate-style skills

A skill effect can remain attached to the caster while the caster turns, aims, flies or animates. This is far more robust than spawning a fixed cloud of vanilla particles at one world coordinate.

For a staged Ea cast, for example, one can conceptually attach:

- a hand/weapon aura to the player;
- a charge ring or rotating field to the player's root;
- a forward-facing release element to the look vector.

**Target use remains INFERENCE** until the FatePhantasms JAR is searched for the relevant Photon entrypoints.

---

## 5. FX as a hierarchy, not a single particle

Source:
`Low-Drag-MC/Photon@1.20.1/common/src/main/java/com/lowdragmc/photon/client/fx/FXRuntime.java`

**DIRECT_OBSERVATION — DEPENDENCY SOURCE**

Photon represents an effect as a scene/runtime with:

- a root FX object;
- multiple child FX objects identified by UUID;
- parent/child transforms;
- lifecycle emission and destruction;
- named-object lookup.

This is important because a “skill effect” can be treated as a **composite scene** rather than one emitter.

A high-quality combat skill can therefore be authored conceptually as:

```text
Skill FX root
├─ pre-cast aura
├─ summon ring
├─ weapon glow
├─ charge spirals
├─ central beam/rift
├─ outer trail/rays
├─ impact flash
└─ lingering afterglow
```

The major reusable lesson is not “use more particles.” It is **compose several independently timed visual objects under one transform/lifecycle**.

That model also makes iteration easier: artists/designers can alter one layer without rewriting the entire gameplay controller.

---

## 6. Beam rendering: why thick energy attacks stay readable

Source:
`Low-Drag-MC/Photon@1.20.1/common/src/main/java/com/lowdragmc/photon/client/gameobject/particle/BeamParticle.java`

**DIRECT_OBSERVATION — DEPENDENCY SOURCE**

Photon's 1.20.1 beam implementation provides:

- configurable color over lifetime;
- width over lifetime;
- animated UVs;
- an emission/UV-scroll parameter;
- optional light handling;
- full-bright behavior when bloom is active;
- interpolation between tick states;
- a textured quad generated between the emitter origin and beam end;
- camera-relative orientation so the beam remains visually broad/readable instead of collapsing into a thin line from many view angles.

### Reusable implication

For Noble Phantasm-scale attacks, a camera-facing beam/ribbon is a better primitive than trying to fake a continuous attack with hundreds of independent vanilla particles.

A beam can then be layered:

1. dark/wide low-alpha body;
2. saturated energy shell;
3. narrow bright core;
4. moving UV/noise layer;
5. bloom;
6. sparse sparks/trails around the silhouette.

The apparent complexity comes from layered materials and timing, not necessarily huge particle counts.

Again, this is a **Photon capability**, not yet a proven statement that FatePhantasms' Ea uses this exact class.

---

## 7. Trails and bloom are native concepts in Photon 1.20.1

Photon's 1.20.1 tree contains dedicated:

- `TrailParticle`
- trail emitter subsystem;
- beam emitter subsystem;
- particle emitter subsystem;
- `BloomEffect` post-processing implementation;
- custom particle render-type machinery.

**DIRECT_OBSERVATION — DEPENDENCY SOURCE**

Photon's public project description also presents it as a Unity-inspired VFX editor and advertises particle/trailing systems, custom shader material support and built-in bloom.

### Engineering consequence

This dependency is capable of supplying three visual families that are especially valuable for anime/Fate combat:

- **beam/ribbon**: release attacks, spatial tears, energy columns;
- **trail**: sword arcs, projectile streaks, orbiting charge lines;
- **bloom/additive highlight**: emphasizing a small luminous core or key accent.

This strongly explains why the r224 dependency migration could raise visual quality sharply without requiring every effect to be hand-rendered in the FatePhantasms Java code.

---

## 8. The presentation model suggested by the release history

The target release chronology supports a staged skill timeline.

The exact timings are **UNKNOWN**, but the architecture worth recovering is:

```text
SUMMON / READY
    ↓
CHANT
    ↓
CHARGE / BUILD
    ↓
LOCK / TELEGRAPH
    ↓
RELEASE
    ↓
IMPACT
    ↓
AFTERGLOW / CLEANUP
```

### Why this matters

r205 explicitly says the full chant made the overall cast longer. That is a strong clue that the author accepts deliberate latency when it improves spectacle.

A technically simple attack can feel expensive if each phase has a distinct visual purpose:

- **SUMMON** establishes the weapon/source;
- **CHANT** gives anticipation and character;
- **CHARGE** increases visual density/scale;
- **LOCK/TELEGRAPH** makes direction/target readable;
- **RELEASE** changes motion abruptly and concentrates luminance;
- **IMPACT** provides a short peak;
- **AFTERGLOW** lets the eye read what just happened.

The core reusable technique is therefore a **timeline/state machine that coordinates gameplay, animation and VFX**, not one monolithic “spawn particles” method.

---

## 9. Spatial composition: Gate of Babylon and Enkidu hints

A separate public project, `CWZMorro/Fate-Mod`, contains multiple source comments explicitly describing its presentation as “like FatePhantasms” or “after FatePhantasms”.

This material is **not FatePhantasms source**. It is recorded only as `SECONDARY_BEHAVIOR_HINT`.

### 9.1 Gate of Babylon hint

Secondary source:
`CWZMorro/Fate-Mod/src/main/java/io/github/cwzmorro/fatemod/gate/GateWall.java`

Its stated FatePhantasms-inspired design places gates:

- behind Gilgamesh;
- in staggered rows;
- with a wider-than-tall wall composition;
- rising from above the shoulders;
- with small positional disorder instead of a perfect sterile grid;
- relative to the caster's orientation/size.

**Useful hypothesis:** FatePhantasms' visual appeal may come partly from composing many origins as one large silhouette around/behind the actor, rather than treating every projectile as an unrelated spawn.

The numerical constants in that recreation are **not target evidence** and must not be copied into a FatePhantasms specification.

### 9.2 Enkidu hint

Secondary sources:
- `CWZMorro/Fate-Mod/.../chain/ChainLayout.java`
- `.../client/chain/ChainDrawing.java`
- `.../client/chain/ChainBindRenderer.java`

The recreation describes an effect sequence where:

1. golden gates open around a target;
2. chains emerge spike-first;
3. chains reach and coil around the target;
4. glow intensifies while tightening;
5. on release, chains retract;
6. gates close.

Its chain drawing uses separate base-metal and additive-glow passes, pulse modulation and camera-aware presentation.

**Reusable composition hypothesis:** use **phase changes in geometry**, not merely increasing particle count. “Open → launch → wrap → tighten → retract → close” gives the skill a readable mechanical story.

These phase details should be searched in the real distribution before being promoted beyond behavior hints.

---

## 10. What is probably doing the heavy lifting

Current confidence ranking:

### High confidence

1. **Presentation timing is deliberate.**  
   Supported directly by r205/r224/r250 release notes.

2. **Photon + LDLib are part of the enhanced-effects architecture.**  
   Supported directly by the r224/r282 dependency statements.

3. **Photon 1.20.1 is capable of entity-following, look-oriented, hierarchical FX with beam/trail/bloom primitives.**  
   Supported directly by inspected Photon source.

### Medium confidence / target inference

4. **FatePhantasms likely uses Photon projects/resources as the VFX authoring layer and Java/gameplay code as orchestration.**  
   This is technically plausible and consistent with the release transition, but the target JAR must prove it.

5. **The strong impression comes from layering and choreography more than raw vanilla-particle count.**  
   Supported as a design interpretation, not a bytecode fact.

### Low confidence / unknown until JAR or reviewed video

6. Exact camera shake, FOV manipulation or cinematic camera control.
7. Exact shader programs/material graphs used by each skill.
8. Exact impact hit-stop/slow motion.
9. Exact sound cue scheduling.
10. Exact multiplayer synchronization strategy.
11. Exact skill-to-`.fx` resource names.
12. Whether Ea's main release beam uses Photon `BeamParticle` directly or another custom/Photon path.

Do not promote these without target evidence.

---

## 11. Reusable KNEEKURA design lessons

These are design-level abstractions, not copied implementation.

### A. Separate skill mechanics from presentation choreography

Use a server-authoritative skill state and a client presentation timeline.

Example conceptual API:

```text
SkillState
  PREPARE
  CHANT
  CHARGE
  RELEASE
  IMPACT
  RECOVER
```

The client maps those phases to VFX/animation/sound. Damage logic should not depend on whether a cosmetic emitter rendered successfully.

### B. Use effect anchors

Give every VFX layer a declared anchor:

- actor root;
- hand/weapon;
- actor look vector;
- target root;
- target bounding volume;
- world impact point.

This avoids hand-authored coordinate hacks and makes effects survive movement/rotation.

### C. Build composite FX from a small vocabulary

Prefer reusable primitives:

- ring / portal;
- beam / ribbon;
- trail;
- sprite/particle field;
- mesh/model;
- bloom/highlight;
- distortion/post-process if available.

A skill is a timeline of configured primitives, not a new renderer class every time.

### D. Make spatial layout a first-class data object

For multi-origin attacks, represent:

- origin count;
- arrangement family;
- spread/scale;
- actor-relative transform;
- deterministic seed;
- opening delay;
- launch order.

This makes “wall behind caster”, “sphere around target”, “arc overhead” and “random-but-repeatable cloud” variations of one system.

### E. Synchronize intent, reconstruct cosmetics

For multiplayer, prefer synchronizing compact skill state / seed / timestamps, then let clients reconstruct expensive visual placement deterministically when feasible.

This is a design recommendation motivated by the target's repeated multiplayer animation/effect fixes and by the need to avoid network-spamming every cosmetic particle. It is **not yet a claim about FatePhantasms' implementation**.

### F. Give brightness a hierarchy

Do not bloom everything.

A readable high-end attack usually has:

- dark or low-luminance mass;
- saturated middle layer;
- narrow bright core;
- very bright short-lived peak.

This preserves silhouette and prevents the entire screen from becoming uniform white.

---

## 12. Why r205 → r224 should be the next binary diff

A whole latest-JAR decompile is useful, but the historical pair is more diagnostic.

### r205 tells us

- the project already had summon/effect work;
- full chant and longer cast timing existed;
- this is a pre-enhanced-effects baseline.

### r224 tells us

- Photon + LDLib became prerequisites;
- chant/charge effects were heavily reworked;
- multiplayer animation/effects were explicitly tested/fixed.

### Differential questions

For the two JARs, compare:

- dependency metadata;
- added packages/classes;
- new `assets/**` extensions;
- Photon FX/project files;
- textures and render resources;
- shader/material resources;
- animation files;
- sounds and `sounds.json`;
- networking classes;
- new references to Photon API types;
- class call sites that start/stop effects;
- timing constants/state machines;
- resource names attached to each skill.

This should reveal the exact technology introduced at the visual-quality jump with much less ambiguity than reading only r284.

---

## 13. Target JAR inspection checklist

When the r284 binary is available locally:

### Identity

- verify:
  `SHA-256 = 68158d03ae033577def23d51c4e238c8f9aa082243c8da16fbe0e4f9a3fcc88c`
- record file size, release URL and acquisition timestamp.

### Metadata / dependencies

Inspect:

- `META-INF/mods.toml`;
- manifest;
- declared Mod ID;
- dependency ranges for Forge, Minecraft, Photon and LDLib;
- any optional animation/render libraries.

### Resource inventory

Inventory by extension/path:

- Photon effect/project resources;
- textures;
- shader/material data;
- models;
- animation resources;
- sounds;
- localization;
- item models;
- custom data formats.

### Bytecode search seeds

Search for names/packages related to:

- `com.lowdragmc.photon`;
- `EntityEffect`;
- `BlockEffect`;
- `FX` / `FXRuntime`;
- beam/trail emitter classes;
- effect-resource loaders;
- network messages carrying skill phase, entity ID, position, rotation, seed or timestamp.

### Skill map

For every skill found, map:

```text
input/trigger
→ server validation
→ skill phase/state
→ target selection / hit logic
→ client packet/event
→ animation
→ VFX resource(s)
→ sound
→ release/impact timing
→ cleanup
```

Particular priority:

- Ea / Enuma Elish;
- Gate of Babylon;
- Chain of Heaven / Enkidu;
- key/weapon summon;
- chant/charge transitions.

---

## 14. Rights and reuse boundary

The FatePhantasms public project metadata currently reports **All Rights Reserved**.

Therefore:

- do not vendor the target JAR, decompiled source, textures/models/effects or sounds into normal TECH HUB history;
- do not assume that publicly downloadable means reusable;
- retain hashes, path inventories, call graphs, minimized descriptions and independently written design abstractions;
- if implementation is needed, reconstruct the technique against Minecraft/Forge/Photon public APIs and independently authored assets/configuration.

Photon/LDLib have their own licenses and must be evaluated separately before code/resource reuse. Dependency accessibility does not change the target Mod's rights status.

---

## 15. Current Feature Map

| Facet | State | Basis |
| --- | --- | --- |
| platform / release identity | EVIDENCE_BACKED | GitHub release + upstream README |
| current r284 artifact digest | EVIDENCE_BACKED | GitHub release asset digest |
| Photon + LDLib dependency | EVIDENCE_BACKED | target author release notes / project metadata |
| summon/chant/charge evolution | EVIDENCE_BACKED as AUTHOR_CLAIM | r205/r224/r225/r250 release notes |
| target exact resource tree | NOT_ANALYZED | binary unavailable through current connector |
| target exact Java/bytecode VFX calls | NOT_ANALYZED | binary unavailable through current connector |
| Photon entity-bound auto-rotating FX | EVIDENCE_BACKED for dependency | Photon 1.20.1 source |
| Photon hierarchical FX runtime | EVIDENCE_BACKED for dependency | Photon 1.20.1 source |
| Photon beam/trail/bloom primitives | EVIDENCE_BACKED for dependency | Photon 1.20.1 source/tree |
| target use of those exact primitives | MAPPED / INFERENCE | dependency + release transition; target proof pending |
| Gate of Babylon spatial arrangement | SECONDARY_BEHAVIOR_HINT | independent recreation explicitly cites FatePhantasms |
| Enkidu open/launch/coil/tighten/retract | SECONDARY_BEHAVIOR_HINT | independent recreation explicitly cites FatePhantasms |
| showcase-video timing/visual confirmation | DISCOVERED_NOT_REVIEWED | video links located but not reviewed with timestamp evidence |
| sound system | NOT_ANALYZED | no target binary/resource inventory |
| camera/FOV/shake | UNKNOWN | no target proof |
| performance cost | NOT_ANALYZED | no bounded runtime measurement |
| multiplayer VFX synchronization | AUTHOR_CLAIM that fixes/tests occurred; implementation UNKNOWN | release history only |
| failure/repair history | NOT_ANALYZED | no bounded Issue/PR/history pass yet |

---

## 16. Research conclusion

FatePhantasms is valuable to TECH HUB not merely as a collection of Fate attacks but as a compact example of a **cinematic skill-presentation pipeline**.

The strongest present finding is the combination of:

1. **intentional long-form skill choreography**;
2. **dependency-backed hierarchical FX authoring**;
3. **entity/look-relative anchoring capability**;
4. **beam/trail/bloom primitives for stable large-form visuals**;
5. **spatial composition around the caster/target rather than only at an impact point**;
6. **repeated multiplayer presentation fixes, implying synchronization is part of the design problem**.

The best lesson to carry into KNEEKURA is therefore:

> Build a reusable cinematic skill timeline and FX-composition layer, then author each attack as data/configuration over that layer. Do not hard-code one bespoke particle routine per skill.

The exact FatePhantasms implementation is intentionally left unclaimed until its distribution bytes can be acquired and inspected.
