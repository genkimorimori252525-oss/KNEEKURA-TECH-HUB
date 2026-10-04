# Youkai's Homecoming — Danmaku Technology Research

## Scope

- Target: **Gensokyo Delight ~ Youkai's Homecoming**
- Focus: **danmaku / spell-card / grazing / projectile virtualization**
- Research status: **TARGETED_DANMAKU_ARCHITECTURE_MAPPED**
- Whole-target status: **IN_PROGRESS / NOT COMPLETE**
- Research date: 2026-10-05

This workspace records reusable engineering techniques from Youkai's Homecoming.
It does not modify Minecraft implementation code.

## ANCHOR / FRONTIER

Current upstream latest still targets Minecraft 1.20.1, so ANCHOR and FRONTIER presently share
the same exact source identity.

- CurseForge project: `957437`
- release: `2.7.0`
- file ID: `8004757`
- file: `youkaishomecoming-2.7.0.jar`
- uploaded: 2026-04-28
- Minecraft: `1.20.1`
- loader: Forge + NeoForge distribution
- source: `Minecraft-LightLand/Youkai-Homecoming`
- exact revision: `6d5744269aa597370a265d5c20eeb69902629441`
- source Forge version: `47.1.3`
- Java: `17`
- mappings: official Mojang 1.20.1
- license: LGPLv2.1
- released-binary/source byte equality: **NOT_ESTABLISHED**

Pinned source tree:

- entries: **6,589**
- blobs: **6,099**
- Java files: **744**
- resource files: **5,320**
- broad danmaku/spell path surface: **1,014 entries**
- focused danmaku Java surface: **164 files**

## Core result

The system is much more than "spawn many projectile entities".

It separates danmaku into six cooperating layers:

```text
SpellCard / Ticker
  pattern timing and phases
        |
        v
CardHolder
  common emitter contract
        |
        v
DanmakuMover / TrailAction
  analytic trajectory + transformation
        |
        v
SimplifiedProjectile
  lightweight server simulation
        |
        +---- collision cache / graze / damage
        |
        v
virtual spawn packet
        |
        v
ClientDanmakuCache
  independent client tick/render
        |
        v
render-type batching / BulkDataWriter
```

The most important reusable idea is the **virtual projectile architecture**:

- server keeps accurate projectile objects and authoritative collision;
- many NPC bullets are not inserted into Minecraft's normal Level entity manager;
- the owning Youkai ticks them in a compact collection;
- newly-created bullets are synchronized in batches;
- clients reconstruct projectile objects into a dedicated danmaku cache;
- rendering is batched by visual projectile type.

This preserves Entity-like serialization and projectile semantics while avoiding much of the generic
entity-manager/render-dispatch overhead that dense bullet hell would otherwise pay.

Detailed report:
[DANMAKU-RESEARCH-2026-10-05.md](DANMAKU-RESEARCH-2026-10-05.md)

Bounded repair history:
[FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md)

Source inventory:
[SOURCE-INVENTORY-2026-10-05.json](SOURCE-INVENTORY-2026-10-05.json)

## Strongest recovered technologies

1. owner-managed **virtual projectile collections**
2. batched spawn synchronization
3. client-side virtual projectile cache
4. render-type batching instead of one ordinary entity render submission per bullet
5. per-tick section/entity collision cache
6. shooter-local section matrix cache
7. swept projectile collision against moving targets
8. separate direct-hit and graze hitboxes
9. serializable trajectory DSL
10. serializable Ticker mini-coroutines for spell patterns
11. projectile-expiry `TrailAction` transformation chains
12. independent `ShooterEntity` emitters
13. spell-pattern abstraction through `CardHolder`
14. server-authoritative spell-card battle sessions/resources
15. bulk danmaku erase semantics for bomb/life/miss transitions
16. explicit unsafe-render fast path + compatibility fallback

## Important boundaries

- The source contains automated/generator test material, but no focused danmaku runtime/performance
  regression suite was found.
- No benchmark was reproduced in this pass.
- Virtual bullets are intentionally outside normal world entity discovery in important NPC paths.
- Direct BufferBuilder writes are implementation-sensitive and have already required an
  ImmediatelyFast compatibility fallback.
- Some pattern code remains handwritten and can contain ordinary gameplay bugs; current
  `TargetTracker.vel()` is a concrete source-level example.
- The research is targeted at danmaku; the entire food/worldgen/entity content MOD is not claimed
  complete.
