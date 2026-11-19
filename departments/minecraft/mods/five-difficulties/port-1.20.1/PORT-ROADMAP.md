# Five Difficulties X1 → 1.20.1 port roadmap

Target: the X1 core (`thKaguyaMod`, ~53k lines). Addons (Battler Sakuya, Last Judgment,
TOHOU MAIDs, Illusion Laser) come after the core.

Rule for every phase: literal X1 numbers and order of operations; pure-core regression for
the math; a dedicated-server scenario in CI; an in-world client check locally (private
overlay); a checkpoint document; commit, push, CI green before the next phase.

| Phase | Scope (X1 sources) | Status |
|---|---|---|
| P0–P6 | pattern core, Sakuya time stop, Watch / StopWatch, `EntityHomingAmulet` port | done (inherited) |
| P7 | client visual evidence (real client) | done |
| P8 | `EntityTHShot` Phase A, `THShotLib` emitters, normal sprite forms, 6 shot items | done |
| P9 | all `RenderTHShot` forms, special shots, 19 shot items, literal Homing / Diffusion Amulet | done |
| P10 | `LaserData`, `EntityTHLaser`, `EntityTHSetLaser`, `RenderTHLaser`, THShotLib laser emitters, `ItemTHLaser`, `ISpecialShot` registry | done |
| P11 | spell-card core: `EntitySpellCard`, `THSpellCard`, `SpellCardRegistry`, `ItemTHSpellCard`, spell-card circle, shot material; 30 of the 35 registered cards | done |
| P12 | the 5 cards with dedicated entities: Musou Fuuin (0), Master Spark (1), Satuzin Doll (8), Hikouchuu Nest (10), Fafrotskies (15) | next |
| P13 | entities thrown by items rather than cards: Onmyoudama, Sanae Wind, Dragon Neck Jewel, Ryuu Lightning Bolt, Sphere Shot, Henyori laser (may merge into P16) | |
| P14 | power / point / bomb / extend / shot-material items, player power, death handler, config | |
| P15 | danmaku crafting table (block, containers, GUIs, laser crafting) | |
| P16 | remaining items and their entities (`entity/item`, `entity/effect`) | |
| P17 | X1 mobs: models, renderers, AI, spawning, Sanae merchant, Miracle Mallet, `DanmakuPatternRegistry`, mob spell-card mode | |
| P18 | blocks / tile entity (Divine Spirit), recipes, creative tabs, lang completeness | |
| P19 | addons | |
