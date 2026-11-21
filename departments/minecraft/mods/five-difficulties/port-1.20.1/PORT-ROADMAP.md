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
| P18 | Divine Spirit blocks / tile renderer / entity, Toyosatomimi sword (P18A); 109 X1 recipes with the config-gated recipeless set, yin-yang orb (P18B); creative tabs and lang audited — every item is in a tab (white pearl / white knife hidden as in X1), names come from X1 keys; effect entities keep X1's missing names | done |
| P18C | completion audit (static): every registered item/block/entity/spell card has en_us + ja_jp names (X1 ja_JP text where X1 had it; effect entities, the fairy ghost form and roukanken senpuuzin, raw keys in X1, now take their item's name); spell-card tab title and hot/cold colours from X1 ja_JP; bloodthirsty yin-yang orb texture restored (duplicate import key, now rejected by the importer); models, textures, blockstates, loot tables, recipe ids and biome modifiers cross-checked. X1 ships no .ogg files; sounds.json is added so player-supplied .ogg files play (X1 readme) | done |
| P18D | port change requested by the owner (not X1): a player's spell card no longer needs an enemy on the exact sight line. X1's line is tried first; then the visible enemy nearest the view direction within 30 degrees and 32 blocks is locked on (players, animals, villagers, golems, allies and armour stands are skipped); with none, the card is declared at an invisible, never-spawned point where the player looks (16 blocks or the first block). Mob declarations keep X1's rule | done |
| P19 | addons: only compiled `.class` files exist (Battler Sakuya, Last Judgment, TOHOU MAIDs — the last needs LittleMaidMob); Illusion Laser is not in the archive. Needs a decision before work | blocked (decision) |
