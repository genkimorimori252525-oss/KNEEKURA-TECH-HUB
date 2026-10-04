# Code map

## Core ORIGINAL_SOURCE / ORIGINAL_BINARY

| Subsystem | Representative paths |
|---|---|
| bootstrap | `thKaguyaMod/THKaguyaCore`, `CommonProxy`, `client/ClientProxy` |
| projectile profiles | `ShotData`, `LaserData`, `DanmakuConstants` |
| geometry API | `THShotLib`, `THKaguyaLib` |
| pattern registry | `registry/DanmakuPatternRegistry` |
| spell registry | `registry/SpellCardRegistry` |
| special shot registry | `registry/SpecialShotRegistry` |
| generic shot | `entity/shot/EntityTHShot` |
| persistent laser | `entity/shot/EntityTHLaser`, `EntityTHSetLaser` |
| spell lifecycle | `entity/spellcard/EntitySpellCard`, `THSpellCard` |
| time stop | `entity/item/EntitySakuyaWatch`, `EntitySakuyaStopWatch`, `event/THKaguyaTimeStopEventHandler` |
| rendering | `client/render/shot/RenderTHShot`, `RenderTHLaser`, `client/render/RenderSpellCard` |
| items/content | `item/**`, `init/THKaguyaItems`, `THKaguyaRecipe` |
| GUI/crafting | `gui/**` |

The distributed X1 archive contains 266 `sources/java/` files and 276 class files.

## Add_Battler_Sakuya

- `EntityangSakuya` — combat encounter/state machine built on `EntityDanmakuMob`
- addon proxy/bootstrap — entity registration, spawn and renderer
- familiar entity — encounter support

## Add_Last Judgment

- addon bootstrap — collision-aware spell ID search/registration
- `Spell_last_judgement` — `THSpellCard` choreography
- `EntityTacticsShot` — thin `EntityTHShot` specialization

## TOHOU MAIDs

- `New_EntityMode_Toho` — LMM mode registration + item/equipment dispatch
- specialized AI tasks for ordinary danmaku / knife throwing / special items
- ballistic elevation utility inside knife AI
- hard class reference to `illusion_Laser.Item_LaserCore`

## Illusion Laser

- `Item_LaserCore` — item NBT activation/cooldown
- `Entity_LaserCore` — attached beam controller
- `PacketFixClientLaser` — client rotation correction packet
- `sendLaserRotation` — serialized yaw/pitch value object
