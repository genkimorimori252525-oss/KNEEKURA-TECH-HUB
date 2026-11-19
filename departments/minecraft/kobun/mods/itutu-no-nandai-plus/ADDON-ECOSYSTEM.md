# Addon ecosystem

## Add_Battler_Sakuya

`EntityangSakuya` extends the core `EntityDanmakuMob` and reuses `THShotLib` rather than implementing a parallel projectile system.

Its battle flow changes danmaku phases, maps later phases to core spell-card IDs, cleans familiars, resets combat parameters and eventually adds a merchant recipe that exchanges shot material for the Sakuya watch.

The addon therefore acts as an **encounter script layered on the core battle APIs**.

## Add_Last Judgment

This addon demonstrates the explicit spell plugin surface.

During pre-init it scans numeric spell IDs starting at 60 until it finds an unused `SpellCardRegistry` slot, then registers `Spell_last_judgement` under its own domain.

`Spell_last_judgement` extends `THSpellCard` and composes existing core vector helpers, shot geometry and `EntityTHLaser`. Its custom `EntityTacticsShot` subclasses `EntityTHShot` rather than defining an incompatible projectile stack.

This is strong evidence that the core was designed for external spell additions.

## EntityModeTOHOU MAIDs 2.61

The addon extends `LMM_EntityMode_Basic` and creates a DanmakuMaid mode with specialized AI tasks for:

- ordinary Touhou items;
- thrown knives;
- special/spell items.

Mode selection uses a configurable numeric ID. When configured as -1 it derives an ID from `maidEntityModeList.size()+1`. This is a heuristic, not proof that the ID is globally free.

The knife AI has configurable range/gravity/speed/ammo/reload/aim values and includes a ballistic elevation solver based on target height, horizontal distance, gravity and launch speed.

### Hidden dependency

The binary directly references `illusion_Laser.Item_LaserCore` in normal mode logic, but `@Mod` declares only THKaguyaMod and lmmx.

This creates JVM linkage risk when Illusion Laser is absent. Contemporary crash evidence reports exactly that missing class.

## Illusion Laser mod 2.2

The addon defines an item-owned activation/cooldown state in ItemStack NBT and spawns `Entity_LaserCore` on use.

`Entity_LaserCore` is a controller. It creates two core `EntityTHLaser` beams, keeps them attached to the user and updates their origin/aim/size/lifetime.

For rotation correction the addon creates a dedicated `SimpleNetworkWrapper` channel and broadcasts two client messages during updates. Each packet contains entity ID plus a Java-`Serializable` rotation object written through `ObjectOutputStream`; the client resolves the beam entity and mutates current/previous yaw/pitch directly.

This is historically useful evidence for persistent attached effects, but the packet encoding/broadcast strategy is not promoted.

## Ecosystem architecture

The common pattern is:

```text
THKaguyaMod core
  ├─ projectile geometry/data APIs
  ├─ spell-card registry/lifecycle
  ├─ base danmaku mobs/entities
  └─ rendering/entity infrastructure
       ↑
       ├─ encounter addon
       ├─ spell addon
       ├─ maid integration
       └─ attached-laser item
```

The main reusable technology is the **stable addon surface**, not any one addon class.
