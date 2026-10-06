# QB-MOD 1.6.4.082 — Progression, economy and loot loop

Primary evidence: supplied QB-MOD source snapshot.

This MOD does not expose one explicit quest tree, but its acquisition rules form a recognizable progression loop.

## 1. Wild QB → contract → exchange

QB is the only naturally registered contract NPC.

Registry:
- Extreme Hills / Ice Mountains;
- spawn weight 1, one entity;
- local spawn gate independently succeeds only on a 1/20 random check;
- Y must be at least 63;
- block below must be grass, leaves or snow;
- collision/liquid checks must pass.

Before contraction, QB runs a player-avoidance AI at 16 blocks.

The shared Garnet control interaction is overridden through the Madomagi layer so Madoka's Ribbon is the contract/control token:
- first successful use enables QB;
- clears current path/attack target;
- records player username as owner;
- enters Standby;
- reports `Contracted!`.

After QB is enabled, interacting with a Grief Seed consumes one Seed and drops a reward.

Technique: **rare wild NPC → explicit contract token → owner-bound economy NPC**.

## 2. Clean Grief Seed → Soul Gem lottery

For a Grief Seed with item damage 0, QB does not use the material-reward table.

It rolls `nextInt(12)`:

| Result | Slots | Probability |
| --- | ---: | ---: |
| Madoka Soul Gem | 2 | 1/6 |
| Homura Soul Gem | 2 | 1/6 |
| Sayaka Soul Gem | 2 | 1/6 |
| Mami Soul Gem | 2 | 1/6 |
| Kyouko Soul Gem | 2 | 1/6 |
| Kirika Soul Gem | 1 | 1/12 |
| Yuri Soul Gem | 1 | 1/12 |

Therefore a pristine Grief Seed is primarily a **character-acquisition currency**, not just a purification item.

## 3. Damaged Grief Seed → QB material exchange

For item damage `d > 0`, QB rolls uniformly over integers `0..d`.

Reward thresholds:

| Roll | Reward |
| --- | --- |
| 0–6 | Mami Tea ×6 |
| 7–14 | Leather ×16 |
| 15–22 | normal Golden Apple ×12 |
| 23–30 | Iron Ingot ×8 |
| 31–38 | Bone Meal ×16 |
| 39–46 | Wood ×8, random metadata 0–3 |
| 47–54 | enchanted Golden Apple ×6 |
| 55–62 | Gunpowder ×8 |
| >=63 | Diamond ×1–3 |

The upper roll bound grows with Grief Seed damage. Higher damage therefore unlocks higher reward bands while retaining lower outcomes.

Examples:
- damage 1: Tea only;
- damage 7: Leather becomes reachable;
- damage 47: enchanted Golden Apple first becomes reachable;
- damage 55: Gunpowder first becomes reachable;
- damage 63: Diamond becomes reachable at exactly roll 63, probability 1/64 = 1.5625%.

Technique: **resource degradation value doubles as an economy-tier ceiling**.

## 4. JB uses the inverse roll geometry

JB also exchanges Grief Seeds, but uses:

`nextInt(64 - itemDamage)`

Rewards:

| Roll | Reward |
| --- | --- |
| 0 | Mami Tea ×4 |
| 1–6 | Glowstone ×8 |
| 7–14 | Lapis ×8 |
| 15–22 | Redstone ×8 |
| 23–30 | Iron ×8 |
| 31–46 | Gold ×4 |
| 47–54 | Emerald ×4 |
| 55–62 | Nether Quartz ×4 |
| >=63 | Diamond ×1–3 |

This creates the opposite progression shape:
- item damage 0 can reach all bands, including Diamond at 1/64;
- item damage 1 can no longer roll 63, so Diamond becomes unreachable;
- item damage 63 forces `nextInt(1)=0`, therefore Tea is guaranteed.

The source proves this inverse probability geometry. Whether it is deliberate lore/economy design or an old balancing oddity is UNKNOWN without historical author material.

Technique: **same resource field can drive deliberately different NPC economies by changing random-domain geometry**.

## 5. Hidden Incubator acquisition

QB has a highly specific death drop:

Incubator is dropped only when:
- the damage source is indirect;
- attacking entity is an EntityPlayer;
- source projectile is an `EntityGarnetBullet`.

Ordinary melee or unrelated projectile kills do not satisfy this code path.

This is effectively a hidden **weapon-class-gated loot condition**.

The Incubator is then used in both spawn-egg recipes:
- QB egg: Incubator surrounded by eight Eggs;
- JB egg: Incubator + three Grief Seeds + Eggs.

Thus the special QB kill condition feeds back into controlled QB/JB acquisition.

Technique: **combat-method-specific drop → crafting key → NPC spawn control**.

## 6. Magical-girl death round-trip

Every major magical-girl class returns its corresponding Soul Gem item through `getDropItemId()`.

Common `EntityMahoShojo.dropFewItems`:
- if a valid Soul Gem item exists;
- and entity is not in Ultimate Form;
- drops one Soul Gem with item damage equal to current Soul Gem corruption.

This closes the entity/item state round-trip:

`Soul Gem item damage → summoned character corruption → death → Soul Gem item with same corruption`

Ultimate Form is a deliberate exception: no Soul Gem drop from this common path.

Technique: **entity persistence resource encoded back into loot metadata**.

## 7. Witch → Grief Seed loop

Major witches/bosses drop a Grief Seed:
- Gertrud;
- Charlotte, only when final revival count reaches 0;
- Oktavia;
- Candeloro;
- Homulilly;
- Homulilly Nutcracker;
- non-phantom Ophelia;
- Walpurgisnacht;
- Kriemhild Gretchen.

The standalone `EntityGriefSeed` itself also drops an item Grief Seed carrying its current Soul Gem damage metadata.

This supports the core loop:

`magical girl / Soul Gem → corruption → witch → Grief Seed → purification / exchange / crafting / incubation`

## 8. Kriemhild duplicate-drop candidate

Kriemhild contains both:
1. an `onLivingUpdate` branch that, at health <=0 server-side, creates an explosion, calls `dropItem(GriefSeed)`, then `setDead()`;
2. `dropFewItems`, which also drops one Grief Seed.

Whether both paths execute in the same actual death lifecycle requires runtime or exact superclass-call tracing. This is recorded as a **potential duplicate-drop candidate**, not a proven two-Seed result.

## 9. Grief Seed as crafting catalyst

Grief Seed is also a recipe component for multiple signature weapons:
- Madoka Bow;
- Sayaka Cutlass;
- Mami Musket;
- Kyouko Spear;
- Kirika Claw;
- Yuri gun.

Therefore killing witches does not merely restore Soul Gems. It also unlocks/feeds signature equipment crafting.

This links loot, character power and witch combat into one resource economy.

## 10. Hidden incubation branch

A dropped Grief Seed placed in the special still-water + glass shell ritual becomes an incubating special seed that is intended to hatch Homulilly Nutcracker.

This turns the same resource into:
- purification;
- NPC exchange currency;
- weapon catalyst;
- ordinary witch incubation;
- hidden boss ritual.

The system gets considerable design density out of one item-state model.

## Reusable progression primitives

Keep independently:
1. rare contractable economy NPC;
2. clean-vs-damaged currency branch;
3. metadata-driven reward ceiling;
4. inverse reward-domain NPC variant;
5. attack-type-gated rare drop;
6. item↔entity state round-trip;
7. boss loot returning into purification/crafting;
8. one resource used across healing, economy, crafting and ritual;
9. final-phase-only boss loot;
10. hidden environmental incubation path.

For ANCHOR, these should be data-driven loot/recipe/trade rules where possible instead of hardcoded item IDs and Java threshold ladders.