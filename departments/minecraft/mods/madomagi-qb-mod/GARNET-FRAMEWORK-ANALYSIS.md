# Garnet-MOD 1.6.4.082 — Framework analysis beneath QB-MOD

Primary evidence: Garnet-MOD archive SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`.

Garnet should not be treated as a trivial dependency. QB-MOD builds significant behavior on top of a reusable NPC/combat framework.

## 1. EntityGarnetBase

Common features include:
- attackDamage attribute registration;
- protection percentage for non-player, non-fire damage;
- vanilla-like melee enchantment integration;
- synchronized flying flag;
- custom flight-aware movement/fall handling;
- periodic automatic healing;
- capability hooks such as `canAttackExplosive` and `canAttackFlying`.

Technique: **small combat-NPC base class separating movement mode, damage policy, attack enchantments and healing cadence**.

For ANCHOR, prefer composition/capabilities or narrow interfaces over one deep inheritance tree where possible.

---

## 2. EntityGarnetTameable ownership contract

Locators:
- synchronized fields: `EntityGarnetTameable.java:72-79`;
- persistence: lines 81-107;
- interaction: 116-140;
- modes: 176-277;
- owner lookup: 279-292.

Synchronized state:
- watcher 15: enabled/claimed;
- watcher 16: mode;
- watcher 17: owner name string.

Persistence writes owner username and mode.

Using the control item:
- unclaimed/non-owner path claims the entity, clears path/target, records `player.username`, and enters Standby;
- owner interaction cycles mode.

Legacy ownership must become UUID-based on ANCHOR.

### Mode machine

States:
- Standby = 0;
- Free = 1;
- Follow = 2;
- Satellite = 3.

Cycle:
- Standby → Satellite if supported, otherwise Free;
- Satellite → Free;
- Free → Follow;
- Follow/other → Standby.

Mode change emits sound and a particle cue.

If an enabled entity is in Standby but is in water or not on the ground, it automatically switches to Follow so the stationary state does not strand it.

Technique: **player-command mode state machine with environmental escape from unsafe Standby**.

---

## 3. Control item dual role

If a player damages a Garnet tameable while holding its control item, incoming damage is forced to 100.

The same control item is used for claiming/mode cycling through interaction.

That conflation is convenient in old Minecraft APIs but semantically ambiguous. ANCHOR should split:
- claim/control interaction;
- dismiss/return-to-token interaction;
- actual combat damage.

---

## 4. Owner feedback

`chatMessage`:
- sends deduplicated messages to the owner;
- also prints every message to stdout.

The chat deduplication does not prevent stdout printing after the owner exists.

This can produce unnecessary console noise during frequent HP/heal updates and is a source-level logging/performance cleanup candidate.

Use structured throttled logging and optional player UI feedback on ANCHOR.

---

## 5. Generic summoner item

`ItemGarnetSummoner` is intentionally tiny:
- resolves the clicked face;
- adjusts spawn position;
- special-cases fence top offset;
- calls abstract `spawnGarnetBase`;
- consumes one item if spawning succeeds and player is not creative.

QB's Soul Gems plug directly into this factory.

Technique: **thin placement/summoning shell with subclass-owned entity factory**.

---

## 6. Servant lifetime contract

`EntityGarnetServant` stores a runtime Master reference.

Server behavior:
- no master → servant dies;
- dead master → servant dies.

On servant death:
- if master implements `ISummonerGarnet` and remains alive;
- invokes `readySummon(true)`.

`ISummonerGarnet` exposes:
- `canSummon()`;
- `readySummon(boolean)`;
- `doSummon()`.

This forms a reusable **single/multi-slot summon lifecycle**:
`summoner consumes ready flag → creates servant → servant death returns readiness`.

QB character systems use this for Sayaka, Yuri and Kyouko-style summons/clones, though individual character implementations may add their own count rules.

### Persistence warning

The base servant's master is an in-memory entity reference, not a robust persisted UUID/id link. Chunk unload/save/load behavior therefore needs explicit redesign for ANCHOR.

---

## 7. Generic gun

`ItemGarnetGun` provides:
- per-weapon reload time;
- bullet item id;
- ammo/reload ratio;
- semi/full-auto flag;
- projectile speed;
- projectile force.

It centralizes:
- magazine release;
- reload;
- ammo consumption;
- full-auto cycling;
- projectile construction;
- Power/Punch/Flame transfer;
- sound;
- recoil.

The specific QB guns are parameter profiles over this base.

Technique: **parameterized weapon chassis with subclass profiles**.

---

## 8. Full-auto network bridge

Garnet declares channels `Garnet` and `GarnetGun` using legacy `@NetworkMod`.

Client full-auto loop polls the use-item key and sends:
- channel: `GarnetGun`;
- payload: one byte, normally `0x10`.

Server PacketHandler:
- requires EntityPlayerMP;
- requires current equipped item to be ItemGarnetGun;
- writes `packet.data[0]` into ItemStack NBT.

Positive design:
- server still derives the target ItemStack from the server player;
- client does not directly name an arbitrary inventory slot.

Risks:
- handler does not verify payload length before `data[0]`;
- direction/schema is implicit;
- generic byte is accepted rather than an enum/boolean contract;
- client key polling is mixed directly into Item logic;
- `try/catch(Error/Exception)` around client input/network send suppresses failures.

ANCHOR:
- typed custom payload;
- explicit serverbound direction;
- validate payload;
- validate player state/held item/action rate;
- separate client input detection from item state machine.

---

## 9. Reload representation

Garnet uses ItemStack damage for magazine depletion and one NBT integer for reload phases.

The high nibble encodes phase-like information and low bits preserve previous depletion.

This is a clever compact representation for 1.6.4 but hard to audit.

Recommended ANCHOR model:
- `ammoInMagazine`;
- `reloadPhase` enum;
- `reloadTicksRemaining`;
- optional `magazineDetached`;
- server authoritative transitions.

---

## 10. Framework techniques to preserve independently

1. owner-aware companion contract;
2. four-mode command machine;
3. environmental escape from Standby;
4. shared flight flag/movement behavior;
5. periodic NPC auto-heal;
6. thin summon-item factory;
7. master-bound servant lifetime;
8. death-returned summon readiness;
9. parameterized gun chassis;
10. reload state machine;
11. full-auto server signal;
12. enchantment propagation into bullets;
13. recoil through shooter orientation.

Garnet is best catalogued as a **legacy combat-NPC substrate**, not buried inside the Madoka-specific notes.