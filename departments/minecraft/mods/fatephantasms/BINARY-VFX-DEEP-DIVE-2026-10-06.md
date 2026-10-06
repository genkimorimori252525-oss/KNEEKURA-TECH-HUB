# FatePhantasms Binary VFX Deep Dive — r205 / r224 / r284

Date: **2026-10-06**  
Status: **EVIDENCE_BACKED STATIC BINARY ANALYSIS**  
Target: `Terry0333/FatePhantasms`  
ANCHOR: Minecraft **1.20.1 Forge**  
Research lane: `jolly/research-fatephantasms-vfx-2026-10-06`

This document supersedes the earlier dependency-only inferences where the distributed
JAR now provides direct evidence. Raw JARs, audio, textures, models and decompiled
source are not committed to TECH HUB. Findings below are derived from version-pinned
JAR hashes, ZIP inventory and `javap` bytecode inspection.

## 1. Distribution identities

| Release | SHA-256 | Entries | Classes | Resources | Photon/LDLib caller candidates |
| --- | --- | ---: | ---: | ---: | ---: |
| r205 | `1372be839df53214b53481dfce989486025c5d8b9273b0e3aa51450660ede9d1` | 97 | 46 | 29 | 0 |
| r224 | `6842008cea5107c13fa806bf433224841f3147c9c832be9d894837f0bf677d36` | 106 | 55 | 29 | 9 |
| r284 | `68158d03ae033577def23d51c4e238c8f9aa082243c8da16fbe0e4f9a3fcc88c` | 168 | 94 | 44 | 15 |

Evidence generation:
- GitHub Actions run `37485453489`, job `112344171330`
- deep-r284 run `37486911279`, job `112349206094`
- original release bytes were downloaded to runner-local temporary storage only
- only hashes, inventory and disassembly-derived summaries were retained

## 2. r205 → r224 is the actual VFX architecture transition

### Direct binary result

r205 has:
- 46 classes;
- 29 resources;
- **zero** class-byte references to Photon/LDLib.

r224 has:
- 55 classes;
- the **same 29 resources**;
- **9** Photon/LDLib caller candidates.

The nine new class entries include:

- `client/EaPhotonEffects.class`
- `client/EaPhotonEffects$CastVisual.class`
- `client/EaPhotonEffects$Placement.class`
- `client/EaPhotonEffects$ScaleMode.class`
- `client/EaPhotonEffects$ShapeKind.class`
- `client/EaPhotonEffects$ShapeSpec.class`
- related helper classes
- `EaSwordSpinState$CastState.class`

The transition also changes the existing:
- `EaAbility`
- `EaAbility$Cast`
- `EaAbility$CastTiming`
- `ModNetwork`
- `ModNetwork$CastStartMessage`
- `ModNetwork$ScreenShakeMessage`
- `EaSwordChargeAura`
- `EaSwordClientEvents`
- `EaSwordItemRenderer`
- `EaSwordSpinState`

### Dependency metadata

r205 declares Forge + Minecraft only.

r224 adds:

```text
modId="photon"
mandatory=true
versionRange="[1.1.17,)"
ordering="AFTER"
side="BOTH"
```

The JAR does not separately declare LDLib in `mods.toml`; Photon itself is the direct
declared dependency surface.

### Important conclusion

**The r224 visual-quality jump is not explained by a new asset pack.**

The resource count remains 29 and no resource path is added across r205 → r224.
The new capability is predominantly **Java-side procedural Photon composition**:
emitters, shapes, curves, colors, materials, transforms and lifecycle orchestration
are constructed at runtime.

This corrects the earlier hypothesis that FatePhantasms might primarily load
pre-authored Photon `.fx` projects. For Ea in r224/r284, the binary instead shows
substantial programmatic construction.

## 3. r284 changes the dependency boundary again

r284 keeps Photon `[1.1.17,)`, but changes it to:

```text
mandatory=false
ordering="AFTER"
side="BOTH"
```

The client code contains `photonAvailable`, reflective type/constructor/method
caches and failure handling. Therefore r284 is designed as a **hybrid renderer with
an optional Photon enhancement path**, not a hard “Photon renders everything” Mod.

This is an important reusable pattern:

```text
authoritative gameplay
    +
always-available custom Minecraft rendering
    +
optional high-end Photon layer
```

## 4. Ea / Enuma Elish — authoritative timeline

Primary binary locators:
- `EaAbility.class`
- `EaAbility$Cast.class`
- `EaAbility$CastTiming.class`
- `ModConfig.class`
- `ModNetwork$CastStartMessage.class`
- `client/EaSwordSpinState.class`
- `client/EaPhotonEffects*.class`
- `client/EaSwordClientEvents.class`

### Default server timing

`ModConfig` directly defines:

| Phase/config | Default ticks | Approx. time |
| --- | ---: | ---: |
| chantOne / charge | 164 | 8.2 s |
| chantTwo / spin / raise | 316 | 15.8 s |
| chantThree / forward release delay | 46 | 2.3 s |
| beam | 140 | 7.0 s |
| finish / aftermath | 76 | 3.8 s |

Default release therefore occurs at:

`164 + 316 + 46 = 526 ticks` ≈ **26.3 s**

Beam end:

`526 + 140 = 666 ticks` ≈ **33.3 s**

Visual/gameplay total:

`666 + 76 = 742 ticks` ≈ **37.1 s**

The cast-start packet also carries a separate `soundEndTicks=833` value, showing
that sound timing is tracked independently from the main gameplay/visual total.

### Server steering and lock-in

Before release, `EaAbility.tick`:
- continually reads the player's current look vector;
- steers the stored direction toward it with factor `0.55`;
- updates the cast origin from the player's current position.

At the release tick:
- direction is sampled again from the player's current look;
- origin is re-anchored;
- subsequent beam attack uses that locked cast state.

So the long cinematic wind-up remains aimable, but the final release has a defined
lock point.

### Network contract

`ModNetwork$CastStartMessage` carries:
- caster UUID;
- charge ticks;
- spin-end ticks;
- release ticks;
- beam ticks;
- sound-end ticks;
- total ticks.

Client handling calls:
- `EaSwordSpinState.beginCast(...)` for the local caster;
- `EaSwordSpinState.beginRemoteCast(...)` for remote players;
- `EaPhotonEffects.beginCast(...)` for VFX.

This is a clean **state/timing synchronization contract**. The server does not send
every cosmetic particle.

## 5. Ea Photon layer — procedural scene composition

`EaPhotonEffects` does not merely spawn one emitter. It exposes procedural builders:

- `sparks(...)`
- `smoke(...)`
- `ringPulse(...)`
- `glowCore(...)`
- `convergence(...)`
- `beamVortex(...)`
- `spatialShards(...)`
- `beamSparks(...)`
- shape builders for sphere / circle / cylinder / box
- constant/random/color/gradient/curve/vector functions
- material and shape configuration
- optional bloom removal

The code reflectively constructs Photon:
- `ParticleEmitter`
- number functions and curves
- color/gradient/random-color functions
- texture material
- renderer modes
- simulation space
- velocity/orbital settings
- UV animation
- shape objects

### Named Ea composition layers

`EaPhotonEffects$CastVisual.createEffects` contains named layers including:

**Opening**
- `opening_dark_air`
- `opening_red_halo`

**Nebula / charge volume**
- `nebula_volume`
- `nebula_shattered_stars`

**Blade / storm escalation**
- `blade_red_lightning`
- `blade_black_geometry`
- `ascending_crimson_gale`
- `ascending_red_arcs`
- `gale_pressure_rings`
- `gale_pressure_rings_upper`
- `gale_pressure_rings_top`
- `tornado_red_gold_streams`
- `tornado_pressure_fronts`
- `tornado_pressure_fronts_upper`
- `tornado_pressure_fronts_top`
- `world_piercing_tornado`

**Compression / crossing / boiling**
- `compressed_white_core`
- `white_hot_compression`
- `white_lightning`
- `gold_cross_shards`
- `boiling_gold_energy`

**Enuma terminal layers**
- `enuma_root_eruption`
- `enuma_sonic_breach_rings`
- `enuma_abyssal_counter_spiral`
- `enuma_abyssal_twin_spiral`
- `enuma_molten_gold_arcs`
- `enuma_spatial_tears`
- `enuma_terminal_black_shards`
- `enuma_terminal_molten_gold`
- `enuma_terminal_white_hot_core`

The key lesson is a **named layer graph** whose elements have independent start
delays, lifetimes, emission rates, shapes, sizes, velocity and colors.

## 6. Ea beam is not only Photon

r284 `EaPhotonEffects` also includes a substantial custom beam renderer:

- `renderRiftBeam`
- `emitTaperedShell`
- `emitSpiralRibbon`
- `emitLightningArcs`
- `emitBeamStroke`
- `emitSpatialShards`
- `renderPerpendicularRings`
- `renderTerminalSurge`
- `emitBeamAnnulus`

This is rendered from `RenderLevelStageEvent`, with:
- frustum checks;
- detail-level selection;
- custom geometry;
- a tapered shell;
- spiral ribbons;
- lightning;
- perpendicular rings;
- terminal surge/shards.

Therefore the visible Ea attack is best described as:

```text
Photon procedural volumetric/particle layers
+ custom Minecraft vertex geometry
+ server-side gameplay particles/impact
+ GUI overlay
+ player/item animation
+ sound
+ camera shake
```

No single subsystem explains the effect.

## 7. Ea summon path — separate 3D + Photon + full-screen composition

Primary locators:
- `EaSummoningEntity.class`
- `client/EaSummoningRenderer.class`
- `client/EaKeySummonPhotonEffects*.class`
- `ModNetwork$SummonFinaleMessage.class`
- `client/EaSwordClientEvents.class`

### World renderer

`EaSummoningRenderer` has dedicated methods for:
- unlock-key rendering;
- rune rendering;
- rune disappearance/collapse;
- summoning orb;
- cross glow;
- sphere and box geometry.

### Photon summon layers

The key-summon Photon layer contains:

- `key_aura_smoke`
- `key_core_glow`
- `key_red_embers`
- `key_ember_convergence`
- `key_ripple_stream`
- `key_ripple_burst_a/b/c/d`
- `key_ripple_burst_sparks`
- `key_collapse_embers`
- `key_collapse_core`
- `key_collapse_shock_a/b/c`
- `key_ready_burst`
- `key_ready_flash`
- `key_ready_ripple_a/b`

`EaKeySummonPhotonEffects.tick` discovers `EaSummoningEntity` instances and
activates this layer after the summon has progressed far enough.

### Full-screen finale

The server sends a dedicated `SummonFinaleMessage`.
Client handling calls `EaSwordClientEvents.startSummonFinale(entityId,total)`.

The GUI finale is explicitly staged:

- **0–20 ticks:** `renderGoldenContact`
- **20–24:** `renderChromaticShock`
- **24 onward:** dark/void overlay via `renderVoidEdgeEcho`
- **from 34:** `renderGlassCracks` + `renderPalmSparks`
- **50–56:** `renderRadialBeams`
- **56–60:** `renderTitleSlices`
- **60 onward:** `renderGlassShards`, with progress ramped over 35 ticks

Additional reusable overlay helpers include:
- star dust;
- red nebula filter;
- void patches;
- light streaks;
- lattice overlay;
- current-frame inversion;
- title card;
- vertical title text.

This is strong evidence that FatePhantasms treats **screen-space composition as an
independent VFX layer**, not merely a world-particle effect.

## 8. Camera shake is explicit and multi-axis

`EaSwordClientEvents.onCameraAngles(ViewportEvent.ComputeCameraAngles)` modifies:

- yaw with a sinusoidal term up to roughly `2.6° × envelope`;
- pitch with a cosine term up to roughly `2.0° × envelope`;
- roll with a sinusoidal term up to roughly `1.8° × envelope`.

The envelope stays strong through roughly 80% of the shake and fades over the final
20%, with an additional low-amplitude modulation.

`ModNetwork$ScreenShakeMessage` triggers `startShake(ticks)`, so camera impact is
a synchronized client presentation event.

## 9. Gate of Babylon — deterministic high-count formation

Primary locators:
- `GateOfBabylonAbility*.class`
- `GateOfBabylonData*.class`
- `GateOfBabylonProjectile.class`
- `client/GateOfBabylonClientState*.class`
- `client/GateOfBabylonRenderer.class`
- `client/GateWeaponRenderer.class`
- `client/GateOfBabylonProjectileRenderer.class`
- `client/GateOfBabylonPhotonEffects*.class`
- Gate state/action network messages

### Volley presets

`GateOfBabylonData$Volley` directly defines:

| Preset | Gate count | firing window |
| --- | ---: | ---: |
| SMALL | 5–8 | 30 ticks |
| MEDIUM | 15–25 | 54 ticks |
| LARGE | 46–54 | 96 ticks |
| ULTRA | 150–200 | 150 ticks |

### Server state machine

A session stores:
- caster UUID/dimension;
- random seed;
- count;
- phase;
- age / fire age;
- deterministic portal list;
- deterministic shot schedule;
- next-shot index.

Opening phase can remain active for up to **900 ticks**.

On fire:
- phase changes to firing;
- shot cursor resets;
- a volley-release sound is played;
- scheduled shots are emitted when `fireAge >= shot.tick`;
- the session remains alive until **26 ticks after the final scheduled shot**.

### Projectile aiming

For each shot:
- the gate's world position is reconstructed from caster position/yaw + portal data;
- an aim point is obtained;
- a small random disc offset is applied around the aim point, with radial scale
  reaching approximately `0.62`;
- the final direction is normalized;
- weapon kind/scale determine muzzle offset and render scale;
- a dedicated `GateOfBabylonProjectile` is fired.

This produces slight convergence variation without losing the common target.

### Client reconstruction

`GateStateMessage` carries:
- caster UUID;
- phase;
- seed;
- count;
- volley ordinal.

The client reconstructs portals and fire timing from the same data.
This is the reusable networking pattern:

> synchronize compact intent + deterministic seed, reconstruct hundreds of visual
> origins locally.

### Gate renderer

`GateOfBabylonRenderer` manually renders:
- portal rings;
- arcs;
- glow quads;
- streak quads;
- weapon emergence.

It includes frustum visibility and distance/detail-level logic.

`GateWeaponRenderer` loads a data-driven mesh catalog from:
`assets/mod_47ef859b/gate/gate_weapons.json`.

The r284 catalog contains **4 weapon entries**; the derived schema contains weapon
name, half-units, y bounds and cube geometry. The raw copyrighted mesh data is not
copied here.

`GateOfBabylonProjectileRenderer` adds:
- multiple trail layers;
- trail quads;
- impact glow;
- textured projectile geometry.

### Photon enhancement for Gate of Babylon

The Photon client follows reconstructed `GateOfBabylonClientState`.

During fire it creates:
- `gob_volley_flash`
- `gob_volley_drift`

The opening bundle also creates wide box-distributed spark fields. Because r284
marks Photon optional, portal/weapon/projectile rendering remains a separate custom
path and Photon acts as an enhancement layer.

## 10. Enkidu — geometry-driven staged bind

Primary locators:
- `EnkiduAbility*.class`
- `EnkiduData*.class`
- `EnkiduChainEntity.class`
- `client/EnkiduChainRenderer.class`
- `EnkiduSounds.class`

### Spawn layout

The ability creates **12** chain entities.

If a living target is available, portal origins are scattered around its AABB with
a radius derived from target size plus an offset. If no target is locked, the
precomputed actor-relative anchor layout is used.

### State machine

The session uses four phases.

**Phase 0 — emerge/open**
- 12 chains exist around the target/aim point;
- ripple/open and friction sounds are played;
- after **16 ticks**, every chain is commanded to `launch()`.

**Phase 1 — fly**
- waits for a chain to report state `BOUND`;
- if a live target is present, enters bind;
- if chains are gone or the phase exceeds **90 ticks**, releases/cancels.

**Phase 2 — bound**
- `beginBind` stores the target position as a fixed bind anchor;
- immediate bind damage: **14**;
- every tick `hold`:
  - zeros velocity;
  - keeps target at the bind anchor;
  - clears Mob navigation/target when applicable;
  - reapplies short status effects;
- at **46 ticks** of bound phase, one-time `tighten` runs:
  - additional damage: **40**;
  - tighten sound;
  - concentrated particle burst.

**Phase 3 — release**
- each surviving chain receives `release()`;
- release sound plays;
- session ends after **24 ticks**.

### Chain renderer

`EnkiduChainRenderer` is custom geometry, with dedicated methods for:
- portal/ripple drawing;
- chain link emission;
- alternating link orientation;
- spike head;
- edge/glow pass;
- coiling around target AABB;
- release/flight trail.

This is significant: Enkidu does **not** require Photon to produce its core visual
identity. It is an example of a complex skill where custom geometry is the better
primitive.

## 11. Sound is phase-aware

Custom r284 sound events include:

- `ea_full`
- `ea_summon`
- `ea_reveal`
- `ea_rune_bass`
- `gate_open`
- `gate_unsheathe`

Gate of Babylon and Enkidu also use helper classes around vanilla sound events.
Those helpers rate-limit repeated impact/friction/bind sounds, preventing a
150–200 projectile/chain effect from turning into an uncontrolled audio flood.

Reusable lesson: **sound needs its own concurrency/rate-limit policy**, especially
for high-count skills.

## 12. Architecture recovered from the binary

The actual r284 design is more interesting than “this Mod uses Photon”.

```text
SERVER
  authoritative skill state
  deterministic seeds/layout
  hit/damage/world interaction
  phase transitions
  compact network messages
        |
        v
CLIENT
  player/item animation state
  deterministic layout reconstruction
  custom vertex renderers
  optional Photon procedural emitters
  screen-space GUI composition
  camera shake
  sound presentation
```

Each presentation technique is chosen by the shape of the problem:

- **Photon particles/volumes** for atmosphere, smoke, sparks, halos and broad energy;
- **custom mesh/vertex rendering** for a stable beam silhouette, portals, chains,
  weapons and projectile trails;
- **GUI-space rendering** for cinematic contact/shock/glass/title sequences;
- **network packets** for timing/seed/state only;
- **server entities/state** for actual gameplay.

## 13. Reusable KNEEKURA design rules recovered

### 13.1 Do not make one renderer responsible for an entire ultimate

An ultimate should be a synchronized composition of:
- gameplay state;
- actor animation;
- effect layers;
- deterministic geometry;
- sound;
- camera;
- optional GUI overlay.

### 13.2 Use Photon as a procedural material/emitter toolkit, not necessarily an asset loader

FatePhantasms builds many Photon objects programmatically. A KNEEKURA VFX API can
therefore expose reusable builders such as:

- smoke volume;
- spark field;
- ring pulse;
- glow core;
- convergence;
- vortex;
- shards;
- gradient/curve helpers.

This is more flexible than requiring one opaque `.fx` file per skill.

### 13.3 Keep custom geometry for visually critical silhouettes

Ea beam, Gate portals/projectiles and Enkidu chains all use custom vertex geometry.
Particles decorate those silhouettes instead of replacing them.

### 13.4 Synchronize intent, not cosmetics

Gate of Babylon proves this scales to **150–200 gates**:
seed + phase + count + preset are enough for deterministic client reconstruction.

### 13.5 Screen-space effects are a separate design surface

The summon finale demonstrates that a high-end skill can move intentionally among:
world-space → screen-space → world-space presentation.

### 13.6 Optional premium VFX can fail gracefully

r284's Photon dependency is optional and the code tracks `photonAvailable`.
A reusable KNEEKURA system should support:
- baseline custom renderer;
- enhanced dependency layer;
- deterministic fallback when the enhanced layer is absent/fails.

## 14. Confidence boundary

EVIDENCE_BACKED:
- all hashes/counts above;
- r205→r224 Photon transition;
- default Ea timings;
- packet/client call relationships;
- named Photon layers;
- custom renderer method families;
- Gate volley values and deterministic state;
- Enkidu phase timing/damage;
- custom sound-event inventory.

Not established by this static pass:
- measured GPU/CPU cost;
- exact visual appearance on every shader pack;
- observed multiplayer latency behavior under packet loss;
- subjective fidelity to Fate source material;
- exact names of obfuscated vanilla status effects applied during Enkidu hold.

Those remain runtime-validation questions, not static-analysis claims.
