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
| P12 | the 5 cards with dedicated entities: Musou Fuuin (0), Master Spark (1), Satuzin Doll (8), Hikouchuu Nest (10), Fafrotskies (15) + Nuclear Shot, Hanabeeper | done |
| P13 | danmaku-weapon items: Mini Hakkero, Nuclear Control Rod, Dragon Neck Jewel (+ entity); `itemEffectFinish` | done |
| P13b | Oharaibou R (Yin-Yang Orb) | done |
| P13c | Oharaibou S (Miracle Circle, Sanae Wind) | done |
| P13d | Gap (warp gaps), Gap Folding Umbrella (Houtou and the Henyori laser are dead code in X1) | done |
| P14 | power / point / bomb / extend items, `EntityTHItem`, player power, extend on death, config | done |
| P15 | danmaku crafting table (block, containers, GUIs, laser crafting) | done |
| P16 | remaining items and their entities (`entity/item`, `entity/effect`), 1.7.10 box intercepts (`X1Hit`); deferred: cursed decoy doll, Miko sword, Miracle Mallet, shot-item dispenser (need P17 mobs / P18 Divine Spirit); `EntityHakureiShield` has no spawner in X1 | done |
| P17 | X1 mobs (fairies, familiar, phantom, Rumia, Cirno, Wriggle, Toziko, Sakuya, Sanae, Reimu, Miko, Rinnosuke, cursed decoy doll), models, renderers, AI, spawning, traders, Miracle Mallet, shot-item dispenser, Hanabeeper spawns, `DanmakuPatternRegistry`, mob spell-card mode (checkpoints P17A–P17K) | done |
| P18 | blocks / tile entity (Divine Spirit), Miko sword (needs Divine Spirit), recipes, creative tabs, lang completeness | next |
| P19 | addons | |
