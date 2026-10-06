# QB-MOD 1.6.4.082 — Gameplay Feature Map (initial)

Community material is reconnaissance only. Implementation claims are tied back to the supplied 1.6.4.082 source.

| Feature / behavior hint | Engineering evidence | Result | State |
| --- | --- | --- | --- |
| Soul Gems summon Madomagi characters | readme + ItemSoulGem.java + Garnet ItemGarnetSummoner.java | Summoning is built on a reusable Garnet summoner/servant framework. | EVIDENCE_BACKED |
| QB is wild and contracted with Madoka Ribbon | mod_QB.java:726-730; EntityQB.java; Garnet tameable base | Explicit biome spawn plus stricter local spawn gate; owner/control inherited from Garnet. | EVIDENCE_BACKED |
| Standby / Free / Follow / optional Satellite | EntityGarnetTameable.java:186-277; EntityMadomagi.java | Mode is synchronized state; Satellite is config-gated and inserted between Standby and Free. | EVIDENCE_BACKED |
| Auto transformation on combat | EntityMahoShojo.java:85-176 | Normal form transforms when target exists, not Standby/Satellite, and corruption <56. | EVIDENCE_BACKED |
| Golden apple manual transformation | EntityMahoShojo.java:299-337 | Interaction consumes golden apple unless creative and switches form. | EVIDENCE_BACKED |
| Rebellion form | EntityMahoShojo.java:98-137,338-355,542-574 + character overrides | Character-specific item + HP threshold; can auto-trigger from internal inventory or direct interaction. | EVIDENCE_BACKED |
| Ultimate Form via diamond | EntityMahoShojo.java:356-374,576-592 | Allowed characters enter UF; Soul Gem is cleansed and internal inventory is ejected. | EVIDENCE_BACKED |
| UF timeout | EntityMahoShojo.java:138-162 | 1500-tick timer advances only while no attack target exists: idle/combat-aware, not strict wall-clock lifetime. | EVIDENCE_BACKED |
| Soul Gem darkness → witch | EntityMahoShojo.java:165-176,429-509,611-627 | At 64+ a character-specific witch is created; Peaceful uses Law-of-the-Cycle disappearance instead. | EVIDENCE_BACKED |
| Witch conversion reshapes terrain | EntityMahoShojo.java:429-509 | Deletes surrounding obstructing blocks until witch spawn is viable; protects bedrock/Mami barrier/Kyouko shield. | EVIDENCE_BACKED |
| Grief Seed cleans Soul Gem | EntityMahoShojo.java:199-211,375-391 | Seed durability/resource is consumed to reduce corruption. | EVIDENCE_BACKED |
| Normal magical girls place torches | EntityMahoShojo.java:180-198 | Uses internal inventory and local light <=8 to place torches. | EVIDENCE_BACKED |
| Character-specific short/mid/long combat | EntityMahoShojo.java:665-667 + per-character source + three range AI goals | Range band dispatches to distinct character projectile/melee patterns. | EVIDENCE_BACKED |
| Walpurgis as world encounter | EntityWalpurgisnacht.java + three Walpurgis AI classes | Spawn gate, weather/time control, phases, terrain damage, anti-air pressure and death staging form one encounter. | EVIDENCE_BACKED |
| Walpurgis low-health escalation | EntityMajoAIWalpurgisnachtAttack.java:44-60 | Aggressive phase activates at HP <=30 of max 90. | EVIDENCE_BACKED |
| Walpurgis damage throttle | EntityWalpurgisnacht.java:88-149 | Valid hit capped to 1 damage, then 20-tick super-armor; rejected living-attacker hit can trigger countershot. | EVIDENCE_BACKED |
| Walpurgis terrain-to-TNT attack | EntityMajoAIWalpurgisnachtAttack.java:177-306 | Bounded connected-block traversal converts local solid terrain to stationary primed TNT with fuse 100. | EVIDENCE_BACKED |
| Walpurgis anti-air | Attack AI:115-145; Play AI:94-124 | Prolonged airborne target gets forced downward and explosion punishment. Likely bug: fallback poison is applied to the boss, not target. | EVIDENCE_BACKED |
| Walpurgis anti-cheese legacy code | EntityWalpurgisnacht.java:99-109 | Mutates player creative/flying capability flags. Do not port literally. | EVIDENCE_BACKED |
| Walpurgis ambience | EntityWalpurgisnacht.java:186-197 | Repeatedly forces overworld rain/thunder/time 23200. Strong presentation, risky global state mutation. | EVIDENCE_BACKED |
| Walpurgis death scene | EntityWalpurgisnacht.java:240-284,383-395 | Congratulations, 200-block EntityMob cleanup, fireworks, Grief Seed. | EVIDENCE_BACKED |
| Kriemhild Gretchen | EntityKriemhildGretchen.java + absorb AI | Giant 2000-HP absorber/healer boss, very large terminal explosion. | MAPPED |
| Homulilly | EntityHomulilly.java + attack AI | Teleport evasion and TNT combat. | MAPPED |
| Oktavia | EntityOktavia.java + Oktavia AI + EntityWheel.java | Stationary boss delegates pressure to spawned moving Wheel hazards. | MAPPED |
| Charlotte | EntityCharlotte.java + RenderCharlotte.java | Synchronized phase/model state and entity replacement/revival-like behavior. | MAPPED |
| Form rendering | EntityMahoShojo.java:52-67; RenderMahoShojo.java:35-80 | Synchronized form switches both model and texture; posture separately drives bow pose. | EVIDENCE_BACKED |
| Shared GUI container | MadomagiGuiHandler.java; EntityMahoShojo.java:701-748 | Legacy handler stores mutable shared container; redesign per-player/per-entity on ANCHOR. | EVIDENCE_BACKED |
| Gun full-auto sync | Garnet mod_Garnet.java, PacketHandler.java, ItemGarnetGun.java | Legacy custom payload controls gun state; modern Forge networking rewrite required. | MAPPED |
| Alternate texture pack | TexturePack archive SHA + assets/puellamagi/textures/mobs/ | 20 character/form PNGs; presentation evidence only. | INVENTORIED |

## Community reconnaissance checked

- Original distribution topic: http://forum.minecraftuser.jp/viewtopic.php?f=13&t=8468 — repeatedly corroborated by contemporary posts/videos, but inaccessible to current fetcher; DISCOVERED_NOT_REVIEWED.
- Creator introduction: https://www.nicovideo.jp/watch/sm19563098 — mirrored metadata identifies the uploader as the MOD creator and points to the distribution topic.
- Bahamut 1.6.4 guide/update: https://forum.gamer.com.tw/Co.php?bsn=18673&sn=404365 — documents prerequisites, controls and the 11/4 UF inventory changes; source was used to verify implementation.
- Contemporary gameplay indexes provide hypotheses about Grief Seed rarity, Walpurgis and Homulilly spacing. They do not override source.

Retrieved: 2026-10-07.