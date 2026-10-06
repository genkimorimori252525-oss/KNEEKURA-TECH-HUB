# QB-MOD 1.6.4.082 — Item / weapon / interaction catalog

Primary evidence: supplied QB-MOD and Garnet-MOD source snapshots.

The player-usable items repeat many of the same combat primitives seen in NPC AI, which makes them useful for separating **mechanic** from **character implementation**.

## 1. Soul Gems

`ItemSoulGem` is a Garnet summoner:
- each character Soul Gem maps to one EntityMahoShojo subclass;
- item damage is copied into the spawned entity's Soul Gem corruption;
- the item also works as a 15-block witch/Grief Seed proximity sensor;
- multi-pass tinting visibly darkens with corruption.

Portable pattern: **item is both serialized character state and summon token**.

---

## 2. Madoka Bow

Locator: `item/ItemMadokaBow.java`.

- vanilla-style charge curve;
- consumes one Light Arrow ammo per release unless creative/Infinity;
- emits **5 EntityLightArrow** projectiles from one shot;
- each is re-headed using speed proportional to charge and inaccuracy 6;
- effective Power level receives an additional +2;
- Flame propagates;
- melee use deals 6 attack attribute and applies knockback equal to Punch+1;
- item icon has four charge-stage variants.

Technique: **one ammo → fan/burst of custom projectiles + charge-state presentation**.

---

## 3. Homura Bow

`ItemHomuraBow` parallels the Madoka bow but emits **8 EntityLightArrow2** homing projectiles per release.

The important distinction is not the bow UI but the projectile primitive: this is the player-facing version of the delayed acquire-and-home system.

Technique: **charged launcher feeding a homing-volley primitive**.

---

## 4. Sayaka Cutlass

Right-click:
- only activates if Regeneration is not already active;
- costs 48 durability unless creative;
- applies Regeneration for 600 ticks at amplifier 4.

Technique: **weapon durability converted into temporary self-regeneration**.

This mirrors Sayaka's identity without requiring a separate mana capability.

---

## 5. Kyouko Spear

Right-click:
- costs 32 durability unless creative;
- fires EntitySpear2 at speed 2;
- Sharpness + Smite + Bane contribute to projectile damage;
- Fire Aspect propagates.

EntitySpear2 then performs impact fan-out into multiple secondary Spears.

Technique: **melee enchantment metadata carried into a projectile/fan-out attack**.

---

## 6. Kirika Claw

Right-click:
- costs 32 durability;
- emits 3 EntityClaw projectiles;
- speed 2 / inaccuracy 6;
- Sharpness/Smite/Bane modify damage;
- Punch becomes projectile knockback;
- Fire Aspect becomes projectile fire.

Technique: **multi-projectile weapon that projects several melee enchantment channels into ranged state**.

---

## 7. Garnet gun framework used by Homura/Mami/Yuri

Garnet `ItemGarnetGun` uses ItemStack damage as current magazine depletion.

### Weapon profiles

Homura handgun:
- capacity-like max damage 7;
- reload time 10;
- reload ratio 1;
- semi-auto;
- bullet speed 2.4;
- bullet force 8.

Homura Type 89:
- max damage 30;
- reload time 10;
- reload ratio 3;
- full-auto;
- bullet speed 2.0;
- force 2.

Mami musket:
- max damage 1;
- reload time 28;
- ratio 1;
- semi-auto;
- speed 2.8;
- force 28.

Yuri gun:
- max damage 1561;
- reload time 20;
- reload ratio 1561;
- semi-auto;
- speed 2.4;
- force 13;
- each shot removes one food level if the player has food remaining.

Technique: one generic gun pipeline creates radically different weapon feel through **capacity/cost, reload ratio, cadence mode, speed and force**.

### Legacy reload state

The framework packs reload state into one NBT integer:
- initial -1;
- a removed magazine stores `0x1000 | previousItemDamage`;
- post-reload state uses `0x4000`;
- lower bits carry magazine depletion.

This is compact but opaque. ANCHOR should use named fields or a small explicit state machine.

### Full-auto input

The Type 89 client polls the use-item key and sends a one-byte `Packet250CustomPayload("GarnetGun", ...)`.

Server handler:
- checks current equipped item is a Garnet gun;
- reads `packet.data[0]`;
- copies that byte into ItemStack NBT `FullAuto`.

The handler does not itself verify payload length before indexing byte 0. This is a legacy network-validation anomaly candidate. Modern payload types should validate direction, schema and bounds.

### Recoil

`fireBullet` directly changes player rotation pitch/yaw after a shot.

Technique: **weapon recoil expressed as camera/orientation state, not projectile spread alone**.

---

## 8. Mami Tea

Drinking applies long-duration:
- Regeneration amplifier 2;
- Haste amplifier 4;
- Water Breathing amplifier 4;
- Fire Resistance amplifier 4.

This is a broad preparation/buff consumable rather than a narrow heal.

---

## 9. Incubator consumable

Drinking/eating Incubator applies:
- Hunger amplifier 4 for 1200 ticks;
- Speed amplifier 4 for 6000;
- Night Vision amplifier 4 for 6000.

Technique: **strong positive mobility/vision buff coupled to a negative hunger cost**.

---

## 10. Madoka Ribbon as control/termination item

`ItemMadokaRibbon.getDamageVsEntity` returns 100 damage against any `EntityMadomagi` and zero against other entities.

Garnet's tameable base independently treats its configured control item as a 100-damage hit.

The same control-item concept is therefore used both to:
- awaken/claim and cycle modes through interaction;
- perform an intentionally exceptional high-damage hit.

Do not generalize this into ordinary weapon damage. It is better understood as an **administrative/control interaction encoded through the combat channel** in the legacy design.

ANCHOR should represent return-to-token/dismissal explicitly rather than relying on magic damage values.

---

## 11. Mami Ribbon unfinished feature

`ItemMamiRibbon` contains a commented-out TODO for an eventual pull mechanic:
- searches nearby EntityItems;
- creates EntityFishHook objects attached to them.

It is non-executable source and must not be reported as shipped gameplay.

This is useful as a preservation example: distinguish **implemented behavior, dead/commented design and community recollection**.

---

## 12. Blocks used by combat systems

### Mami Ribbon block

Registered with:
- hardness 0.6;
- resistance 10;
- light value 0.25;
- nonstandard ribbon block behavior;
- no normal drop path in its block implementation.

Several terrain-destruction systems explicitly protect it.

### Kyouko Shield

Pane-like defensive block:
- hardness 1.2;
- extreme resistance 6,000,000;
- light 0.25;
- requires support beneath;
- removed if support disappears.

Many destructive boss/projectile routines explicitly exempt it.

Technique: **combat-created protected world geometry recognized by enemy destruction policy**.

ANCHOR should replace hard-coded block-ID exemptions with tags such as `boss_terrain_immune` / `encounter_barrier`.

---

## 13. QB / JB resource exchange

### QB

If enabled/owned and given a Grief Seed:
- a pristine damage-0 seed gives one of seven magical-girl Soul Gems.
- distribution is 2/12 each for Madoka/Homura/Sayaka/Mami/Kyouko and 1/12 each for Kirika/Yuri.

A used/damaged seed instead drives a resource table using `nextInt(itemDamage + 1)`.
As item damage grows, higher reward bands become reachable, ending in a diamond branch at values >=63.

QB drops Incubator on death only for a player-attributed Garnet Bullet kill.

Technique: **resource-state-dependent barter table plus weapon/source-specific drop condition**.

### JB

JB also consumes a Grief Seed but computes:

`nextInt(64 - itemDamage)`.

Its reward bands climb toward diamond only at `>=63`. Because Java `nextInt(n)` returns 0..n-1, that top branch is reachable **only when itemDamage = 0**: `nextInt(64)` can produce 63, giving a 1/64 diamond chance. Once itemDamage is 1 or greater, the upper bound is at most 62 and the diamond branch is no longer reachable.

The result is an intentionally or accidentally inverted economy relative to QB: a pristine Grief Seed exposes JB's highest reward band, while increasing damage progressively removes the upper bands.

---

## 14. Crafting as mechanic discovery

Recipes confirm intended player ownership of most signature weapons and barriers:
- Madoka bow requires Grief Seed + bow + red flower;
- Homura handgun / Type89 are craftable;
- Homura bow combines Madoka ribbons + Madoka bow;
- Sayaka Cutlass uses Grief Seed + diamond sword + jukebox;
- Mami musket uses Grief Seed + iron/flint;
- Kyouko spear uses Grief Seed + diamond sword + gold block;
- Kirika Claw uses Grief Seed + diamond sword + iron swords;
- Yuri gun uses Grief Seed + redstone block + quartz + iron;
- Mami Ribbon block and Kyouko Shield are explicitly craftable from their character items.

This means the combat primitives are not NPC-only presentation; many were deliberately exposed as player systems.

## 15. Reusable item-technique inventory

- summon token carrying corruption/damage state;
- multi-pass state tinting;
- held-item threat detector;
- one-ammo multi-projectile launcher;
- durability-to-self-buff conversion;
- enchantment propagation from melee item to projectile;
- parameterized generic firearm;
- NBT magazine/reload state machine;
- input packet → per-stack full-auto state;
- camera recoil;
- positive buff with negative resource cost;
- control/dismiss interaction encoded through special item;
- combat-protected block tags;
- durability-dependent barter table;
- kill-source-specific loot condition.