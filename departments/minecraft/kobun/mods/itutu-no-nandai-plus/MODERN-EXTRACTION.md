# MODERN-EXTRACTION — derived reusable technology

Temporal role: **MODERN_EXTRACTION**

Nothing in this document rewrites the ORIGINAL 1.7.10 implementation as modern code.

## 1. Projectile profile separate from pattern geometry

**Historical mechanism:** `ShotData` / `LaserData` carry projectile parameters; `THShotLib` creates formations.

**Invariant concept:** separate “what a projectile is” from “how a pattern places projectiles.”

**Modern reconstruction:** immutable projectile-profile records/codecs + a deterministic pattern-geometry library.

**Do not copy literally:** mutable/positional DataWatcher-era encoding.

## 2. Composable danmaku geometry library

**Historical mechanism:** ring, random ring, sphere, wide/spread and laser primitives are centralized.

**Invariant concept:** spell choreography should compose a small set of tested geometry operators.

**Modern reconstruction:** pure geometry functions produce emission descriptors; server owns spawning/authority.

## 3. Data-driven difficulty profiles

**Historical mechanism:** `DanmakuPatternRegistry` rewrites count/span/speed/form by danmaku level.

**Invariant concept:** difficulty changes pattern parameters instead of branching/duplicating spell code.

**Modern reconstruction:** named difficulty/pattern profiles loaded through a validated registry or data file.

## 4. Lifecycle host + behavior plugin

**Historical mechanism:** `EntitySpellCard` owns world identity/lifetime while `THSpellCard` owns choreography.

**Invariant concept:** persistent world host and effect behavior should be separate responsibilities.

**Modern reconstruction:** namespaced behavior registry + typed factory. Avoid `Class.newInstance` and global integer IDs.

## 5. Extensible special projectile motion

**Historical mechanism:** `SpecialShotRegistry` attaches homing/diffusion/fall behavior to a generic shot entity.

**Invariant concept:** movement policy can be modular without creating a new entity class for every shot.

**Modern reconstruction:** typed strategy/component selected by namespaced ID, with deterministic/server-authoritative state.

## 6. Controller entity + effect entity

**Historical mechanism:** `EntityTHSetLaser` and Illusion `Entity_LaserCore` control beams that retain core laser collision/render behavior.

**Invariant concept:** one object owns attachment/lifetime/input, another owns the physical effect.

**Modern reconstruction:** controller capability/entity + beam/effect entity; synchronize only state required for deterministic client reconstruction.

## 7. Compact authoritative state -> client reconstruction

**Historical mechanism:** DataWatcher packs projectile form/color/lifetime/orientation while renderers rebuild geometry client-side.

**Invariant concept:** network semantic state, not rendered vertices.

**Modern reconstruction:** `SynchedEntityData` or versioned custom payload codec with explicit bounds.

## 8. Time domains with explicit exemptions

**Historical mechanism:** watch entities simulate stop by restoring state; `THSpellCard` can opt into special processing.

**Invariant concept:** effects need explicit policy for whether they advance during a changed time domain.

**Modern reconstruction:** central tick/time-domain policy with typed exemptions. Do not reproduce large-area prevPos rollback/decremented counters/type-specific repair tables literally.

## 9. Ballistic solver as reusable utility

**Historical mechanism:** TOHOU MAIDs solves throw elevation from gravity, launch speed, horizontal distance and height difference.

**Invariant concept:** projectile aiming should depend on a projectile physics profile, not entity-specific magic constants.

**Modern reconstruction:** reusable ballistic solution utility returning valid solution/no-solution, integrated with target prediction separately.

## 10. Stable addon surface

**Historical mechanism:** external encounter/spell/maid/laser addons extend THKaguyaMod through base classes, registries and projectile APIs.

**Invariant concept:** a content MOD becomes a technology platform when addons can register behavior without editing the core.

**Modern reconstruction:** public namespaced APIs, compatibility adapters and optional-mod discovery. Never hard-reference an optional addon class in an always-loaded code path.

## DO NOT PORT LITERALLY

- Java `ObjectOutputStream` network payloads;
- two per-tick `sendToAll` rotation packets;
- direct client entity mutation inside packet handler;
- numeric DataWatcher slots and packed magic integers without schema;
- global numeric spell/mode IDs;
- `Class.newInstance`;
- GL11 immediate rendering;
- SRG symbol calls as API contracts;
- world-wide/local time stop implemented as repetitive entity rollback.
