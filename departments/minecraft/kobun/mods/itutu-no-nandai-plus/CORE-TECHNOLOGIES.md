# Core technologies — 五つの難題MOD+ X1

Evidence basis: distributed X1 classes plus bundled `sources/java/`.

## 1. Danmaku as parameter data + geometry operators

`ShotData` and `LaserData` carry the properties of a projectile/beam. Geometry is centralized in `THShotLib`.

The useful split is:

```text
what the shot is       -> ShotData / LaserData
how shots are arranged -> THShotLib
when they are emitted  -> item / mob / spell behavior
```

`THShotLib` supplies reusable primitives including individual shots, wide spreads, rings, random rings, spheres and lasers. Ring creation derives a local basis around the aim vector and rotates it through a full circle; sphere creation composes poles and ring slices.

This prevents each spell from owning a separate copy of the same trigonometry.

## 2. Pattern-level difficulty

`DanmakuPatternRegistry` owns count/span/speed/form data for named patterns and rewrites those values according to configured danmaku level.

Difficulty is therefore expressed at the **pattern data** level rather than by duplicating spell implementations.

## 3. Generic projectile + special motion

`EntityTHShot` is the generic projectile host.

It synchronizes compact state through old DataWatcher integer slots, including packed shot identity, size/lifetime and quantized orientation data. Client renderers reconstruct appearance from this compact state.

Special behavior is not hardwired into every entity. `SpecialShotRegistry` selects an `ISpecialShot` implementation; built-in examples include homing, diffusion and falling motion.

The homing behavior performs angular steering toward a valid visible target rather than snapping velocity directly to the target.

## 4. Persistent lasers

`EntityTHLaser` extends the projectile family with beam length and persistent geometry. Collision tests the beam segment against expanded entity bounds rather than checking only the entity origin.

`EntityTHSetLaser` demonstrates an attached/setting-beam pattern where a beam is anchored to another controller/position.

Some specials such as Gungnir combine beam growth/rotation with recoil and secondary projectile emission.

## 5. Spell cards as behavior plugins

`SpellCardRegistry` maps numeric IDs, names, domains and behavior classes.

`EntitySpellCard` is the lifecycle/world host. It reflectively instantiates a registered `THSpellCard` behavior and delegates initialization, per-tick choreography and cleanup.

This is a clean historical separation:

```text
world entity identity / lifetime
          +
spell behavior object
```

The registry is extensible enough that Add_Last Judgment can register a new spell without modifying the core.

## 6. Time stop

The class name `THKaguyaTimeStopEventHandler` is misleading if read without bytecode: its supplied Forge `CanUpdate` handler is effectively no-op.

Actual stopped-time behavior is implemented by Sakuya watch/stopwatch entities. They repeatedly scan a local area and restore affected entities toward previous position/rotation while suppressing velocity/fire/tick progress. Server players are moved through their server handler so authoritative position follows the rollback.

`THSpellCard` exposes time-stop-aware extension points such as `canMoveInTimeStop` / `specialProcessInTimeStop`, allowing selected effects to keep processing.

This is historically clever, but it is a rollback simulation rather than a true scheduler-level time domain.

## 7. Historical networking/render assumptions

Normal danmaku largely relies on old entity tracking + DataWatcher state rather than a dedicated general projectile packet protocol.

Rendering uses immediate GL11/Tessellator-era paths. The reusable invariant is **small authoritative state -> deterministic client reconstruction**; the rendering/network implementation itself is era-specific.

## 8. Bootstrap

`THKaguyaCore` / proxies register entities, renderers, items, recipes, spell registries, danmaku tables, GUIs, trades and spawn behavior through ordinary Forge/FML mechanisms.

No supplied coremod transformer/LaunchWrapper patch was found in these artifacts.
