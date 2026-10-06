# QB-MOD 1.6.4.082 — Player items, weapons and ritual mechanics

Primary evidence: supplied QB-MOD/Garnet-MOD Java source.

This pass focuses on mechanics available directly to the player and on world-state rituals that are easy to miss when only reading entity AI.

## Madoka Bow

Source: `item/ItemMadokaBow.java`

Player-fired bow:
- consumes Light Arrow ammo unless creative/Infinity;
- draw strength follows vanilla bow charge curve;
- each release emits **5 EntityLightArrow** projectiles;
- each projectile gets an additional +2 Power contribution;
- spread/inaccuracy 6;
- melee hit with the bow also applies knockback;
- four draw-stage icons are selected from use duration.

Technique: **one ammo item → multi-projectile magical bow burst**, while retaining Forge ArrowNock/ArrowLoose hooks.

## Homura Bow

Source: `item/ItemHomuraBow.java`

Player release:
- emits **8 EntityLightArrow2** projectiles;
- homing behavior is implemented by the projectile, not the item;
- spread/inaccuracy 12;
- consumes one Light Arrow item for the entire volley.

Community reconnaissance for the older 1.6.4.080 generation describes this bow as an eight-arrow auto-tracking weapon whose damage increases with time aloft. That matches LightArrow2's expanding-search homing and age-based damage logic.

Technique: **volley weapon delegates post-launch intelligence to each projectile**.

## Kyouko Spear

Source:
- `item/ItemKyoukoSpear.java`
- `entity/projectile/EntitySpear2.java`
- `entity/projectile/EntitySpear.java`

Right-click:
- costs 32 durability unless creative;
- launches one EntitySpear2 carrier projectile;
- melee enchantment damage and Fire Aspect are partially transferred.

EntitySpear2 impact:
- on living target: creates 6 child EntitySpear projectiles around/at the victim;
- on terrain: creates 6 child Spears using impact position/reference;
- child Spears inherit damage/fire and terrain branch also inherits knockback.

This directly explains the contemporary player-facing description that a thrown spear can create many additional spears after impact.

Technique: **single thrown weapon → impact-triggered six-way secondary weapon burst**.

## Sayaka Cutlass

Source: `item/ItemSayakaCutlass.java`

Right-click:
- if Regeneration is not already active;
- costs 48 durability unless creative;
- grants Regeneration V for 600 ticks.

The AI's thrown-sword mechanic is separate from this player item action.

Technique: **weapon durability used as a magic-resource substitute for self-healing**.

## Kirika Claw

Source: `item/ItemKirikaClaw.java`

Right-click:
- costs 32 durability;
- launches a Claw projectile;
- transfers melee enchantment damage/Fire Aspect;
- explicit projectile speed 2.0 and inaccuracy 6.

Technique: **melee weapon doubles as durability-funded ranged weapon**.

## Gun framework

Source:
- Garnet `item/ItemGarnetGun.java`
- QB Homura/Mami/Yuri gun subclasses
- Garnet packet handler/channel

The gun base implements magazine state inside ItemStack NBT:
- `Reload`
- `Bolt`
- `FullAuto`

Reload uses item damage as magazine consumption state. Right-click begins either firing or reload sequence depending on state.

Full-auto:
- checks held/use state in `onUpdate`;
- cycles a bolt flag;
- legacy client key state is communicated over `Packet250CustomPayload("GarnetGun", ...)`;
- server/client state then gates automatic bullet emission.

Shot recoil is implemented by directly mutating player pitch/yaw.

### Homura Desert Eagle
- 7-round magazine;
- reloadTime 10;
- semi-auto;
- bulletSpeed 2.4;
- bulletForce +8.

### Homura Type 89
- 30-round magazine;
- reloadTime 10;
- full-auto;
- bulletSpeed 2.0;
- bulletForce +2;
- reloadRatio 3, so one ammo item can cover multiple rounds under the base reload loop.

### Mami Musket
- 1-round magazine;
- reloadTime 28;
- semi-auto;
- bulletSpeed 2.8;
- bulletForce +28.

### Yuri handgun
- effectively very large durability/magazine budget (1561);
- reloadTime 20;
- semi-auto;
- bulletSpeed 2.4;
- bulletForce +13;
- every shot additionally consumes 1 food level when possible;
- reloadRatio 1561.

Technique: **shared firearm state machine parameterized by magazine, reload ratio, cadence and force**.

ANCHOR rewrite:
- SimpleChannel/custom payload replacement;
- never read client keybinds as authoritative server state;
- validate fire cadence/server-side ammo;
- move NBT state to modern data components/capability strategy as appropriate.

## Mami Ribbon

Source: `item/ItemMamiRibbon.java`

The active pull mechanic is commented out.

The abandoned design would:
- search nearby dropped items;
- attach a FishHook-like entity to them;
- toggle a connection state;
- consume durability when releasing/pulling.

This is useful as a **design archaeology note**, not an implemented feature.

## Soul Gem item

Source: `item/ItemSoulGem.java`

### Visual corruption

Max damage is 63 and item color darkens in four bands:
- <16 white;
- <32 light gray;
- <48 dark gray;
- >=48 black.

Thus item durability is also the visible corruption meter.

### Threat/proximity indicator

When the Soul Gem is actively held:
- scans EntityCreature within 15 blocks;
- if an EntityGriefSeed or EntityMajo is within squared distance <=225;
- stores `nearGriefSeed=true` in ItemStack NBT;
- item gains enchantment glint and Rare rarity.

Technique: **held item becomes a local supernatural detector using its own NBT-render state**.

### Summoning

Soul Gem subtype maps directly to one magical-girl entity class.
On summon:
- item damage/corruption is copied into the new entity's Soul Gem state;
- the world entity is spawned with randomized yaw.

Technique: **itemized entity state round-trip**, where corruption survives entity↔item transitions.

## Grief Seed item and incubation ritual

Source:
- `item/ItemGrifSeed.java`
- `entity/monster/EntityGriefSeed.java`

### Normal use

Using the item on a block:
- creates a thrown/physical EntityGriefSeed;
- transfers item damage to the entity;
- consumes the item unless creative.

### Hidden Homulilly ritual

A dropped Grief Seed checks four nearby quarter-offset water cells.

If it is in still water and the surrounding 3×3×3 shell is glass:
- creates an EntityGriefSeed in the water;
- assigns a new countdown;
- sets `isHomulilly=true`;
- destroys the dropped item.

When that special seed later hatches, `chooseMajo` returns **EntityHomulillyNutcracker** directly.

Technique: **spatial block arrangement + dropped item + fluid = alternate boss incubation ritual**.

This mechanic is easy to miss from registry or entity lists alone and strongly validates the TECH-HUB player-facing reconnaissance requirement.

## Grief Seed entity incubation

Once a player is within 16 blocks:
- uninitialized countdown is created;
- countdown decrements only while a player remains nearby;
- base countdown: `500 + rand(0..999) - corruption*5`;
- as countdown approaches zero, red particle frequency increases;
- at zero, a witch is selected/spawned.

Normal random witch selection uses five reachable random branches:
- Gertrud
- Charlotte
- Oktavia
- Candeloro
- Homulilly

The switch default names Walpurgisnacht, but `nextInt(5)` yields only 0–4, so the default/Walpurgis branch is unreachable in this method.

Static anomaly lead: **unreachable default branch in Grief Seed witch selection**.

If no spawn position is available:
- tries random positions first;
- then expands shells around the seed;
- synchronously removes obstructing blocks;
- protected: bedrock, Mami Ribbon, Kyouko Shield;
- eventually forces space for the witch.

Technique: **proximity-activated incubation + escalating particles + fallback terrain excavation**.

ANCHOR should keep the ritual/state machine but move terrain excavation into bounded work queues.

## Food / buff items

### Mami Tea
Applies long-duration:
- Regeneration III;
- Haste V;
- Water Breathing V;
- Fire Resistance V.

### Incubator
Applies:
- Hunger V;
- Speed V;
- Night Vision V.

These are straightforward buff bundles rather than complex systems.

## Highest-value item-side techniques

1. multi-projectile ammo-efficient bow;
2. intelligent projectile delegated from a normal weapon;
3. impact fan-out weapon;
4. durability-funded active magic;
5. firearm magazine/reload/full-auto framework;
6. held-item proximity sensor with visual state change;
7. itemized entity-state round-trip;
8. dropped-item + environment ritual;
9. proximity-paused incubation countdown;
10. forced world-space creation when spawn clearance fails.

These should remain independent primitives in TECH-HUB.