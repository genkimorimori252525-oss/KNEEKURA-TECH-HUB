# QB-MOD / Garnet-MOD — Minecraft 1.20.1 Forge ANCHOR portability matrix

Date: 2026-10-07

LEGACY source: QB-MOD/Garnet-MOD 1.6.4.082.

ANCHOR: Minecraft 1.20.1 + Forge.

This is a reconstruction map, not a copy/paste plan. The old API calls are evidence of intent; the implementation must use ANCHOR-native contracts.

Official Forge 1.20.1 documentation checked:
- registries: https://docs.minecraftforge.net/en/1.20.1/concepts/registries/
- networking/SimpleImpl: https://docs.minecraftforge.net/en/1.20.1/networking/simpleimpl/
- entity synchronization: https://docs.minecraftforge.net/en/1.20.1/networking/entities/
- menus: https://docs.minecraftforge.net/en/1.20.1/gui/menus/
- tags: https://docs.minecraftforge.net/en/1.20.1/resources/server/tags/
- config: https://docs.minecraftforge.net/en/1.20.1/misc/config/
- SavedData: https://docs.minecraftforge.net/en/1.20.1/datastorage/saveddata/

## Core platform map

| Legacy concept/API | Invariant intent | ANCHOR direction | Feasibility | Main semantic risk |
| --- | --- | --- | --- | --- |
| numeric item/block/entity IDs | stable registered content identity | `DeferredRegister` + `RegistryObject` / registry keys | rewrite, straightforward | old save IDs cannot be copied |
| `LanguageRegistry` | localized names | `assets/<modid>/lang/*.json` | rewrite, straightforward | translation-key compatibility |
| code recipes | crafting graph | JSON/data generation | rewrite, straightforward | preserve exact ingredient metadata/outputs |
| hardcoded drops | progression loot | entity loot tables where practical; custom code only for stateful metadata | moderate rewrite | Soul Gem/Grief Seed metadata round-trip |
| legacy `Configuration` | player/server tuning | `ForgeConfigSpec` | rewrite, straightforward | choose CLIENT/COMMON/SERVER authority correctly |
| DataWatcher numeric indices | server→client dynamic entity state | `SynchedEntityData` + `EntityDataAccessor` | direct concept rewrite | define accessors only on owned entity classes |
| custom entity NBT | durable entity state | `CompoundTag` save/load hooks | direct concept rewrite | legacy missing fields/typos must be consciously migrated |
| username owner string | persistent ownership | UUID/profile-backed ownership | rewrite required | name changes/offline lookup |
| static Walpurgis gate | global encounter singleton | world/server `SavedData` + encounter registry | rewrite required | restart/unload duplication |
| `Packet250CustomPayload` | client trigger intent | typed `SimpleChannel` message | rewrite required | trust boundary, malformed packets, cadence authority |
| `IGuiHandler` singleton container | entity inventory UI | `MenuType` / `AbstractContainerMenu`; send entity ID through open-menu extra data | rewrite required | never retain per-player menu in global singleton |
| `InventoryBasic` five-slot NPC store | tactical item store | `ItemStackHandler` / `IItemHandler` or explicit Container implementation | moderate rewrite | preserve AI/server ownership of mutations |
| old `EntityAIBase` tasks | goals/target goals | `Goal`, `goalSelector`, `targetSelector` | semantic rewrite | cadence and mutex/flags differ |
| direct navigator/path APIs | chase/follow | modern `PathNavigation`, `MoveControl` | semantic rewrite | giant/flying entities need custom navigation choice |
| direct velocity flight | scripted airborne movement | custom `MoveControl` or bounded per-tick velocity controller | good | client prediction, collision, speed caps |
| `RenderLiving` + GL11 | entity presentation | `MobRenderer`/layers + `PoseStack` + render types | full renderer rewrite | preserve form/model/scale separation |
| `ModelBiped` / custom ModelBase | character/boss geometry | modern `EntityModel`/HumanoidModel/layer definitions or chosen animation library | full model adaptation | old rotation conventions |
| `BossStatus.setBossStatus` | boss health UI | server-managed BossEvent/`ServerBossEvent` | rewrite required | UI must not depend on renderer invocation |
| direct vanilla particle names | lightweight effects | vanilla `ParticleOptions`; custom particle type only when needed | straightforward | server/client spawn side |
| hardcoded protected block classes | terrain immunity | block `TagKey` such as boss-terrain-protected | strong direct replacement | tag ownership/datapack overrides |
| broad class checks for flying/explosive enemies | tactical entity categories | entity type tags and/or explicit combat traits/interfaces | strong replacement | class inheritance is no longer the category source |
| raw parent entity pointer | encounter/master relation | UUID/encounter ID durable state + cached resolved reference | rewrite required if durable | chunk unload / dimension changes |
| synchronous large block loops | spectacle/world mutation | KNEEKURA bounded block-edit job | rewrite required | preserve pacing while capping tick work |
| vanilla TNT mass creation | delayed explosive spectacle | budgeted custom hazard or capped TNT pool | redesign recommended | chain explosion amplification |
| direct `setHealth` execution | percentage/execute mechanic | custom DamageType/rule-aware damage pipeline | redesign required | armor/events/invulnerability compatibility |
| creative/flying flag mutation | anti-cheese intent | boss counterplay/anti-air mechanics | do not port implementation | player-state corruption |
| global time/weather mutation | encounter ambience | scoped/reversible encounter ambience, optionally client-local visual layer | redesign required | unrelated players/world state |

## Registration and data

Forge 1.20.1 recommends `DeferredRegister` for ordinary registries. Entity classes should be represented through registered `EntityType` factories rather than legacy global numeric IDs.

Recommended split:
- Java registration: items, blocks, entity types, menu types, particle types if custom;
- server data: recipes, loot tables, tags;
- language JSON: names/messages;
- model/texture resources: exact normalized resource paths.

The alternate texture-pack full-width-`ｍ` defect demonstrates why exact ResourceLocation-compatible paths should be validated during asset import.

## Config mapping

Legacy system options:

| Legacy key | ANCHOR authority |
| --- | --- |
| EasyMode | SERVER/Common gameplay config |
| GSLightLevel | SERVER world/spawn config |
| GSSpawning | SERVER world/spawn config |
| canWalpurgisSpawn | split: config = encounter enabled; runtime singleton state = SavedData |
| SatelliteMode | SERVER gameplay config, client receives entity mode normally |
| HeightCorrection | CLIENT rendering config |

Do not reuse `canWalpurgisSpawn` as one mutable config value for both user policy and encounter runtime state.

## Entity synchronization vs persistence

Forge 1.20.1 entity docs explicitly separate dynamic synchronized data from durable data.

Recommended classification:

### SynchedEntityData
- magical-girl form;
- posture/pose selector;
- Charlotte phase;
- Shadow type;
- selected boss presentation phase;
- tactical mode where client UI/rendering needs it.

### Durable entity NBT
- owner UUID;
- form;
- corruption;
- tactical mode;
- NPC inventory;
- Grief Seed countdown;
- special Nutcracker incubation flag;
- Charlotte second-form/revival state;
- ecology age if chosen durable;
- master/encounter UUID if relation must survive load.

### SavedData
- active Walpurgis encounter identity/global admission gate;
- optional per-world encounter coordinator.

### Runtime-only
- current target;
- path cache;
- action timer;
- open-menu state;
- resolved parent object pointer;
- transient projectile search counters unless persistence is intentionally required.

## Menus/inventory

Forge 1.20.1 menus are per-player dynamic objects. The legacy shared `MadomagiGuiHandler.container` pattern should be eliminated.

Recommended flow:
1. server interaction validates ownership/access;
2. server opens registered MenuType and sends target entity ID;
3. both sides resolve/create the appropriate menu instance;
4. server menu keeps authoritative reference to NPC inventory;
5. distance/alive/ownership checks happen in `stillValid`;
6. slot mutations remain server authoritative.

Five-slot inventory can remain exactly five slots; the migration issue is lifetime/authority, not size.

## Networking

The only explicit custom legacy gameplay packet found is Garnet gun full-auto state.

ANCHOR message should mean something like:
`GunTriggerState(pressed: boolean)`

Server handler validates:
- PLAY_TO_SERVER direction;
- sender exists;
- held item is the expected gun;
- sequence/rate;
- reload/magazine state;
- whether a shot may actually fire.

The packet should never mean “the client authorizes a bullet.”

## AI architecture

Do not build one `MagicalGirlGoal` with every legacy branch.

Recommended reusable Goal primitives:
- short/mid/long range dispatcher;
- staged-world-prop weapon controller;
- burst/cadence controller;
- flight pursuit controller;
- oscillatory flight modifier;
- homing-volley controller;
- summon budget controller;
- terrain-hazard attack job;
- anti-air pressure;
- damage-throttle boss phase;
- teleport reposition service;
- ecology/evolution controller.

Character classes compose these primitives with data/parameters.

This preserves QB-MOD's diversity instead of turning all future NPCs into one template.

## Projectile reconstruction

### Use real entities when
- projectile can be hit/interacted with;
- it embeds in terrain;
- it later becomes a minion seed;
- its physical presence is attack stock;
- target selection changes after launch.

Examples:
- Prickle;
- Wheel;
- staged Musket/Cutlass;
- LightArrow2/3 if exact homing collision semantics are required.

### Prefer lighter visual/effect systems when
- projectile is purely decorative;
- hundreds are expected;
- server collision does not matter.

LAB should compare visual bullets vs physical entities before selecting one universal danmaku implementation.

## Terrain interaction

All destructive systems should use one shared ANCHOR service:

`EncounterBlockEditService`

Inputs:
- encounter ID;
- source entity;
- candidate region/positions;
- allowed operation;
- protected block tag;
- per-tick budget;
- total attack budget;
- chunk-loaded policy.

Consumers:
- witch transformation clearance;
- Grief Seed forced hatch clearance;
- Walpurgis TNT conversion;
- Yuri terrain TNT;
- Nutcracker body destruction;
- Charlotte second-form destruction;
- FireLance block cut.

This is preferable to six unrelated direct `Level#setBlock` loops.

## Encounter ownership

Introduce durable `EncounterId` for boss-created objects:
- Walpurgis;
- Prickle;
- Shadow Puella;
- boss TNT/hazards where cleanup matters;
- Nutcracker + its servant tree;
- optional Kriemhild effects.

Use it for:
- cleanup;
- population caps;
- kill attribution;
- telemetry;
- safe server restart recovery.

This replaces raw object references and giant class-based cleanup scans.

## Progression/data migration

Keep the legacy loop but data-drive it:
- Grief Seed corruption/value;
- QB clean-seed Soul Gem table;
- QB damaged-seed reward ranges;
- JB inverse table;
- signature weapon recipes;
- witch loot;
- hidden Incubator condition;
- environmental Nutcracker ritual.

The two NPC exchange formulas are intentionally recorded separately because their probability geometry is opposite.

## Rendering modernization

Preserve these contracts:
- form → model family;
- form → texture;
- posture → pose;
- phase → scale/model discontinuity;
- simulation dimensions independent of render scale.

Do not infer hitbox from `15×` Kriemhild render scale.

Light Arrow crossed-plane luminous rendering is a good candidate for a modern translucent render layer or particle-like visual, but server collision semantics should remain a separate decision.

## Compatibility risks

Highest-risk direct ports:
1. hardcoded numeric IDs;
2. username ownership;
3. shared GUI container;
4. direct player capability mutation;
5. direct target health mutation;
6. static process-local encounter state;
7. mass TNT;
8. synchronous block destruction;
9. raw parent object pointers;
10. Garnet reverse dependency on QB concrete class;
11. repeated target reacquisition scans;
12. source-only stale imports.

## Direct-backport feasibility labels

### High
- form state machine concept;
- Soul Gem corruption loop;
- range-banded attack selection;
- staged weapon prop concept;
- summon/evolution graph;
- visual model/texture state separation;
- five-slot tactical inventory.

### Medium
- homing projectiles;
- teleport combat;
- servant/master relations;
- boss super-armor;
- terrain-protected barriers;
- QB/JB economy;
- hidden incubation ritual.

### Rewrite-heavy
- giant collision destruction;
- Walpurgis encounter/global ambience;
- mass TNT;
- legacy packet/gun networking;
- GUI handler;
- direct health execution;
- any behavior relying on player capability mutation.

## Validation gate for ANCHOR

A faithful 1.20.1 reconstruction should not be called equivalent until it passes:
- state transition tests;
- save/reload tests;
- dedicated-server networking tests;
- owner/multiplayer menu concurrency tests;
- projectile trajectory/target tests;
- encounter cleanup tests;
- block-edit budget tests;
- performance soak with high entity/projectile counts.

The static legacy analysis supplies the behavioral oracle; ANCHOR runtime evidence must be collected separately.