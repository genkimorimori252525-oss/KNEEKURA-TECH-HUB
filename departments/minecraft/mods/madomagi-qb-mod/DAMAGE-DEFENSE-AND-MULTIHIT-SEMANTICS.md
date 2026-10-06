# QB-MOD / Garnet-MOD 1.6.4.082 — Damage / defense / multi-hit semantics

Date: 2026-10-07

Primary evidence:
- QB-MOD SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

This document connects three systems that must be understood together:
1. Garnet's protection percentage;
2. projectile i-frame reset;
3. boss-specific damage gates/retaliation.

Without all three, the apparent stats and barrage behavior are misleading.

## 1. Garnet protection is conditional percentage reduction with flooring

`EntityGarnetBase.attackEntityFrom` obtains `DamageSource.getEntity()`.

Protection applies only when:
- attacking entity is **not** an `EntityPlayer`;
- damage source is **not fire damage**.

When it applies:

`effective = floor(incoming * (100 - protectStrength) / 100)`.

Consequences:
- direct player-origin damage bypasses Garnet protection percentage;
- player-attributed indirect damage should also bypass when `DamageSource.getEntity()` resolves to the player;
- fire bypasses percentage protection;
- environmental/non-player/non-fire sources are reduced;
- flooring makes low-damage hits disproportionately easy to nullify.

Examples:

| incoming | protect10 | protect20 | protect30 | protect60 | protect90 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1 | 1 | 1 | 0 | 0 |
| 5 | 4 | 4 | 3 | 2 | 0 |
| 10 | 9 | 8 | 7 | 4 | 1 |

So even “10% defense” completely nullifies a non-player one-damage hit because `floor(0.9)=0`.

ANCHOR should decide whether this exact integer-floor behavior is part of the desired legacy feel or merely an implementation artifact.

## 2. Magical-girl protection table

Common Normal protection is0.

| Character | MS | Rebellion | UF |
| --- | ---: | ---: | ---: |
| Madoka | 10 | unsupported | 100 |
| Homura | 15 | 90 | 100 |
| Sayaka | 30 | 60 | 60 |
| Mami | 20 | unsupported | unsupported |
| Kyouko | 0 | 20 | unsupported |
| Kirika | 0 | unsupported | unsupported |
| Yuri | 20 | unsupported | unsupported |

Important: these values are only the shared percentage layer. Several characters override `attackEntityFrom` and add stronger mechanics.

## 3. EasyMode friendly-fire gate

`EntityMahoShojo.attackEntityFrom`:

When config `EasyMode=true`:
- if damage source entity is another `EntityMahoShojo`;
- this entity is enabled/owned;
- both resolve to the same owner object;

the damage is rejected entirely.

This is independent from ordinary target selection and protection percentage.

Technique:
**same-owner friendly-fire cancellation at the damage boundary**, so accidental projectile crossfire can be suppressed even if targeting logic was bypassed.

## 4. Projectile substrate resets target i-frames

Both:
- `EntityGarnetArrow`;
- `EntityGarnetThrowable`;

set the struck entity's `hurtResistantTime=0` immediately before applying damage.

Distributed class bytecode contains the corresponding write to obfuscated `Entity.field_70172_ad`.

This means QB-MOD's barrage counts are mechanically meaningful:
- separate projectiles can damage in rapid succession;
- vanilla post-hit invulnerability does not automatically collapse a burst into one hit.

This is a **global Garnet projectile rule**, not a one-character exception.

## 5. Critical Throwable is explosive damage mode

`EntityGarnetThrowable` critical flag:
- entity impact → strength6 explosion with terrain damage enabled;
- block impact → strength4 explosion with terrain damage enabled;
- normal projectile damage still follows the entity-impact explosion path.

`EntityGarnetBullet` inherits this behavior.

Mami `Tiro Finale!` sets its Garnet bullet critical, so the finisher is an explosive round.

The word “critical” therefore does not mean vanilla-style bonus particles only.

## 6. Madoka defense overrides

### ordinary transformed self-source rejection
If:
- server-side;
- damage source entity is Madoka herself;
- form is ordinary transformed;

damage is rejected.

### Ultimate
Madoka returns false for **all** incoming damage in Ultimate Form before the shared protection layer.

So her UF effective defense is stronger than “protect100”: it is an explicit damage-method rejection.

She also cannot be pushed/collided with normally in UF.

## 7. Homura defense is form-specific evasion, not just protection

### transformed form
For non-player, non-fire damage:
- tries up to64 random teleports;
- successful teleport cancels the hit;
- Standby changes to Follow;
- Soul Gem corruption +1.

If all teleports fail, normal protection15 still applies.

This creates:
**spatial evasion first → percentage reduction fallback**.

### Rebellion
Self-sourced damage is rejected.
Protection90 handles qualifying non-player/non-fire sources.

### Ultimate
Server-side Homura rejects all damage.

Again, UF immunity is stronger than the shared protect100 value alone.

## 8. Sayaka converts heavy Rebellion hits into corruption cost

If:
- server-side;
- Sayaka is in Rebellion;
- alive;
- raw incoming damage >5;

then Soul Gem corruption +1 before the common damage path.

The hit itself still passes through Rebellion protection60 where applicable.

Technique:
**large-hit pressure taxes the transformation resource in addition to HP**.

## 9. Kyouko uses active guard/dodge/clone layers

When:
- server-side;
- source entity is not a player;
- form is transformed or Rebellion;
- Kyouko alive;

damage handling order is:

1. if shared `actionTick ==0`:
   - chat `GUARD!`;
   - set actionTick12;
   - incoming damage becomes0;
2. else 10% random:
   - chat `DODGE!`;
   - reject hit;
3. else if `fantasma >0`:
   - chat `GUARD!`;
   - Soul Gem +1;
   - incoming becomes0;
4. otherwise:
   - shared percentage layer applies (0 in MS,20 in Rebellion).

Her defensive cooldown reuses the same `actionTick` field used by combat attack Goals, coupling offense cadence and defense state.

Technique:
**active defensive layers ahead of passive reduction**.

Rosso Fantasma count also becomes a defensive resource, not just offensive summon count.

## 10. Kirika has probabilistic transformed dodge

Against non-player sources while ordinary transformed:
- 1/5 = **20%** chance to reject the hit;
- announces `DODGE!`.

Her MS protection value itself is0.

Technique:
**evasion identity without passive armor**.

## 11. Walpurgisnacht: one-damage gate + retaliation against blocked hits

Incoming raw damage >=1 is normalized to1.

Then:
- source-less damage is rejected 80% of the time;
- fire damage causes extinguish but is not automatically zeroed by that branch;
- own Fire Lance / Prickle and self-origin are rejected;
- if `superArmor !=0`, damage becomes0;
- any accepted positive hit sets superArmor20.

Nominally this permits about one accepted point per ~20 ticks.

### Critical interaction with barrage systems

If damage is rejected to0 **and** the attacker is a living entity:
- Walpurgis spawns a Small Fireball aimed back at that attacker.

Therefore super-armor is not passive immunity. It is a **rapid-hit retaliation gate**.

Because Garnet projectiles clear target hurt-resistance before every impact, a dense volley can continue calling Walpurgis's damage method during its20-tick armor window.

Each blocked projectile attributed to a living shooter can therefore create another counter-fireball.

Conceptually:
`rapid barrage → first point accepted → following hits blocked → blocked hits become counter-projectiles`.

This is a strong anti-spam / anti-DPS design pattern.

Exact returned-fireball count depends on actual projectile collision timing and server tick ordering and should be measured in runtime before quoting a fixed number.

ANCHOR:
- preserve the “rapid fire feeds retaliation” mechanic explicitly;
- do not derive it accidentally from zero-damage calls;
- cap/telegraph counter-projectiles to avoid entity amplification.

## 12. Nutcracker: one-damage gate without fireball retaliation

Nutcracker:
- normalizes damage >=1 to1;
- rejects source-less hits80% of the time;
- servant-origin attacks heal1 and are rejected;
- superArmor20 blocks subsequent hits;
- accepted hit resets superArmor20.

It shares the one-point-per-window texture of Walpurgis but lacks the blocked-hit fireball retaliation.

It separately contains the unsafe creative/flying capability mutation on player attackers.

## 13. Kriemhild: fixed 20-tick cumulative damage budget

Kriemhild's damage logic is different.

Rules:
- fire →0;
- self-origin →0;
- source-less/environmental hit rejected2/3 of the time;
- each individual positive hit capped at10;
- `armorValue` accumulates accepted damage inside the current window;
- if a new hit would push armorValue above10, that hit is reduced to `10 - armorValue`;
- once armorValue reaches10, later hits in the window become0.

`onLivingUpdate`:
- decrements `superArmor`;
- when it reaches0, resets it to20 and armorValue to0.

So Kriemhild has a **fixed ~1-second damage bucket capped at10 total accepted damage**, not the Walpurgis/Nutcracker “one hit then invulnerable” model.

At nominal20 TPS, even perfect multi-hit saturation is therefore capped around10 HP/s by this custom bucket before considering other engine rules.

### Redundant condition

The method also checks:
`superArmor !=0 && armorValue >10`.

But the clamping logic prevents armorValue from being increased above10 through this method.

That condition is therefore structurally redundant/unreachable under the observed update path; the real cap comes from reducing later hit damage to zero at armorValue==10.

This is an archaeology lead, not a historical bug claim.

## 14. Homulilly: probabilistic teleport immunity with retaliation

On server damage:
- self-origin heals1 and is rejected;
- otherwise 1/3 of incoming attacks enter the evade branch;
- tries up to64 random teleports;
- on success:
  - cancels the hit;
  - if attacker is living, executes TNT retaliation.

Failed teleport attempts fall through to normal damage.

Technique:
**probabilistic evasion where successful reposition itself unlocks retaliation**.

## 15. Homulilly servants heal from sibling attacks

`EntityHomulillyServant.attackEntityFrom`:
- if source entity is another Homulilly servant;
- heals by the incoming damage amount;
- rejects damage.

This makes intra-family friendly fire **positive healing**, not merely immunity.

Technique:
**faction damage inversion**.

## 16. Wheel only accepts living-attacker damage

`EntityWheel.attackEntityFrom` rejects damage if:
- source entity is null;
- or source entity is not `EntityLivingBase`.

Environmental damage therefore cannot normally clear the kinetic hazard.

## 17. Grief Seed damage admission

Server-side `EntityGriefSeed` accepts attacks only when the source entity is:
- EntityPlayer;
- or EntityGarnetBase.

Other source entities are rejected.

This turns the incubation entity into a controlled gameplay object rather than ordinary environmental debris.

## 18. Defense model taxonomy

Recovered independent primitives:

1. percentage protection with integer-floor rounding;
2. damage-source-class bypass;
3. same-owner friendly-fire rejection;
4. projectile i-frame reset;
5. explosive critical projectile;
6. absolute form immunity;
7. teleport evasion;
8. heavy-hit resource tax;
9. active timed guard;
10. random dodge;
11. summon-count guard resource;
12. one-damage + super-armor gate;
13. blocked-hit counter-projectile;
14. fixed-window cumulative damage budget;
15. successful-evasion retaliation;
16. faction damage → healing;
17. source-category damage admission.

These should remain composable. Do not replace the entire legacy defense system with a single armor stat.

## 19. ANCHOR reconstruction rules

For Minecraft1.20.1 Forge:

- use explicit DamageType / event-aware policies;
- keep source-category rules readable and testable;
- decide multi-hit semantics per attack family;
- avoid globally zeroing `invulnerableTime`;
- represent boss damage budgets directly;
- generate retaliation from a bounded counter system;
- preserve same-owner friendly fire through faction/owner identity;
- do not mutate player creative/flying capabilities;
- instrument damage events/tick and spawned retaliation entities;
- test multiplayer attribution, indirect projectile ownership and modded DamageType interaction.

For fidelity tests, verify not just “HP after one hit” but:
- same-tick multi-hit;
- 20-tick barrage;
- player vs NPC shooter;
- fire vs non-fire;
- environmental damage;
- owner-friendly crossfire;
- boss saturation;
- retaliation count.
