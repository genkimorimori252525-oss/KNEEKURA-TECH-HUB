# QB-MOD / Garnet-MOD 1.6.4.082 — Defense / damage-gate taxonomy

Date: 2026-10-07

Primary evidence:
- QB-MOD SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

This document complements `DAMAGE-HIT-SEMANTICS.md`.

The combat system does **not** use one universal armor/invulnerability model. It layers several independent gates, which explains how rapid danmaku can multi-hit ordinary entities while bosses and special forms still resist burst deletion.

## 1. Gate A — vanilla hurt-resistance bypass for Garnet projectiles

Garnet Arrow/Throwable:
- set `target.hurtResistantTime = 0`;
- then call target `attackEntityFrom`.

Effect:
- ordinary vanilla recent-hit cooldown is bypassed;
- rapid projectiles can each enter the target's damage pipeline.

This is the common **multi-hit admission gate**.

It should be considered *upstream of* the target-specific defenses below.

## 2. Gate B — percentage protection by attacker class

`EntityGarnetBase.attackEntityFrom`:

if attacker is not a player and source is not fire damage:

`damage = floor(damage × (100 - protectStrength) / 100)`.

Form values include:

| Entity/form | protection |
| --- | ---: |
| Madoka transformed | 10% |
| Madoka UF | 100% |
| Homura transformed | 15% |
| Homura Rebellion | 90% |
| Homura UF | 100% |
| Mami transformed | 20% |
| Sayaka transformed | 30% |
| Sayaka Rebellion | 60% |
| Sayaka UF | 60% |
| Kyouko Rebellion | 20% |
| Yuri transformed | 20% |
| Kirika transformed | 0% |

Important semantics:
- player-attributed attacks skip this reduction;
- fire DamageSource skips it;
- NPC projectile direct hits normally use the shooter NPC as attacker and are reduced;
- repeated projectile hits can still pass after reduction because ordinary i-frames were cleared.

This is a **source-conditioned mitigation gate**, not generic armor.

Because the legacy path casts the reduced float to integer-like effective damage through the old damage flow, flooring materially affects small hits. Representative source-level percentage arithmetic:

| incoming | protect10 | protect20 | protect30 | protect60 | protect90 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1 | 1 | 1 | 0 | 0 |
| 5 | 4 | 4 | 3 | 2 | 0 |
| 10 | 9 | 8 | 7 | 4 | 1 |

Thus even a nominal 10% protection can erase a non-player one-damage hit after flooring. A modern reconstruction must decide explicitly whether that quantization is part of the intended combat feel.

## 3. Gate C — absolute form invulnerability

### Madoka Ultimate
`EntityMadoka.attackEntityFrom` returns false while Ultimate Form is active.

### Homura Ultimate
`EntityHomura.attackEntityFrom` returns false while Ultimate Form is active.

This happens before shared protection/vanilla damage processing.

Result:
**no amount of projectile i-frame bypass admits the hit**.

Modern abstraction:
`RejectDamageGate(form == UF)`.

## 4. Gate D — probabilistic/conditional evasion

### Homura transformed

For non-player, non-fire damage while transformed:
- tries up to 64 random teleports;
- first successful teleport:
  - may leave Standby for Follow;
  - adds Soul Gem corruption;
  - returns false.

This is effectively:
**incoming attack → reactive reposition → damage cancellation**.

Player-sourced and fire damage do not enter this teleport-defense branch.

### Homulilly

On roughly 1/3 of incoming server-side attacks:
- tries up to 64 random teleports;
- on success:
  - optionally retaliates with TNT toward attacker;
  - cancels the hit.

This is a probabilistic **evade + counterattack gate**.

### Kirika transformed

For non-player incoming damage:
- 1/5 chance to announce `DODGE!`;
- returns false.

### Kyouko transformed/Rebellion

For non-player incoming damage:
1. if `actionTick ==0`:
   - `GUARD!`;
   - set actionTick 12;
   - damage becomes 0;
2. else 1/10 chance:
   - `DODGE!`;
   - return false;
3. else if Rosso Fantasma count >0:
   - `GUARD!`;
   - Soul Gem +1;
   - damage becomes 0.

These are **reactive defense actions**, not passive armor.

## 5. Gate E — fixed per-hit cap + local super-armor

### Walpurgisnacht

Incoming:
- any damage >=1 is collapsed to 1;
- fire is extinguished;
- many source-less hits are rejected;
- own Flame Lance/Prickle and self-source are rejected;
- after an accepted positive hit:
  `superArmor =20`.

While superArmor is nonzero:
- subsequent damage is forced to 0;
- living attackers can trigger a SmallFireball retaliation path.

Thus:
**max 1 accepted damage → ~20-tick custom lockout**.

The lockout is independent from vanilla `hurtResistantTime`, so Garnet projectile i-frame reset cannot defeat it.

### Homulilly Nutcracker

Likewise:
- damage >=1 collapses to1;
- source-less hits mostly rejected;
- own Homulilly servants heal it instead;
- accepted hit sets `superArmor=20`.

This is the same broad primitive without Walpurgis's projectile-specific countershot.

Modern primitive:
`PerHitCap(1) + BossSuperArmor(20 ticks)`.

### Walpurgis blocked-hit retaliation under barrage

Walpurgis adds one extra rule that materially interacts with Garnet multi-hit projectiles:

If its local damage processing has reduced the current hit to zero and the attributed attacker is a living entity, it creates a Small Fireball aimed back at that attacker.

Because Garnet Arrow/Throwable clear ordinary target hurt-resistance before each direct hit, a dense volley can continue invoking Walpurgis's damage method throughout the custom 20-tick super-armor window.

Conceptually:

`rapid volley → first point admitted → later impacts blocked by boss gate → blocked impacts can become counter-projectiles`.

This is an **anti-spam / anti-DPS retaliation primitive**, not ordinary passive invulnerability.

The exact number of returned fireballs for a volley remains a runtime/tick-order question. ANCHOR should model the intent directly and use a bounded retaliation budget rather than accidentally spawning one counter entity for every zeroed hit.

## 6. Gate F — rolling damage budget per time window

### Kriemhild Gretchen

State:
- `superArmor`;
- `armorValue`.

Damage handling:
- fire damage rejected;
- many source-less hits rejected;
- self damage rejected;
- a single incoming hit is capped at 10;
- if current window's `armorValue + hit >10`, accepted amount is reduced so the total reaches at most 10;
- accepted amount is added into `armorValue`.

Living update:
- superArmor counts down;
- when its window expires:
  - timer is reset to20;
  - `armorValue=0`.

Net result:
**roughly one-second damage budget of 10 total**, rather than one hit per second.

This is materially different from Walpurgis:
- many tiny projectiles can contribute until the 10-point budget is filled;
- one large attack can consume the whole budget;
- extra hits in the same window become zero.

This is an excellent boss anti-burst primitive for a multi-hit combat system.

Modern abstraction:
`RollingDamageBudget(windowTicks≈20, maxDamage=10)`.

### Redundant legacy condition

Kriemhild also tests a condition equivalent to:
`superArmor != 0 && armorValue > 10`.

But the same method clamps admitted cumulative damage so `armorValue` reaches at most 10 through the observed path. The explicit `>10` branch is therefore structurally redundant/unreachable under this damage-update logic.

The effective mechanic is the rolling 10-damage budget, not that branch.

## 7. Gate G — faction/source inversion

### Homulilly servants

If a Homulilly servant is attacked by another `EntityHomulillyServant`:
- it heals by the incoming amount;
- returns false.

### Homulilly Nutcracker

If attacker is an `EntityHomulillyServant`:
- heals 1;
- rejects damage.

This is not merely friendly-fire immunity. It is:
**same-faction attack → healing conversion**.

### Servant Oktavia / Corno Forte / Rosso Fantasma

These reject damage from their own master.

Rosso Fantasma additionally:
- any other positive damage kills the clone immediately;
- returns false rather than using ordinary HP damage.

That is a one-hit **disposable clone gate**.

## 8. Gate H — allowed-source whitelist

### Grief Seed entity

Server-side damage is rejected unless attacker entity is:
- EntityPlayer; or
- EntityGarnetBase.

Environmental/source-less attacks therefore do not work through this override.

### Wheel

Damage is rejected unless `DamageSource.getEntity()` is an EntityLivingBase.

This makes the Wheel immune to many environmental/non-living damage sources.

Technique:
**attacker-category whitelist**.

## 9. Defensive side effects can use pre-mitigation damage

Sayaka:

while Rebellion, if incoming `par2 >5`:
- adds Soul Gem corruption;
- then delegates into shared base damage/protection.

So corruption checks the original incoming amount before shared 60% non-player protection.

This establishes a useful distinction:
- **trigger amount**;
- **final applied amount**.

A modern combat pipeline should make that explicit.

## 10. Source identity changes which gates execute

Several defenses explicitly exclude `EntityPlayer` attackers:
- Homura transformed teleport defense;
- Kirika dodge;
- Kyouko guard/dodge;
- Garnet protection filter.

Therefore the same nominal projectile can behave differently depending on who fired it:

### player-fired Garnet projectile
- `DamageSource.getEntity()` is player;
- magical-girl percentage protection does not run;
- multiple NPC-special dodge/guard branches do not run.

### magical-girl-fired projectile
- attacker is EntityMahoShojo;
- percentage protection may run;
- Kyouko/Kirika/Homura non-player defense branches can run;
- EasyMode same-owner magical-girl friendly-fire rejection can run.

This is a major part of legacy balance.

## 11. Interaction matrix with projectile i-frame reset

| Defense | Does projectile `hurtResistantTime=0` bypass it? | Why |
| --- | --- | --- |
| vanilla recent-hit i-frame | YES | reset occurs before vanilla attack handling |
| Garnet % protection | NO | reduction occurs before superclass |
| Madoka/Homura UF reject | NO | explicit early return false |
| Homura teleport evade | NO | early cancel |
| Kirika dodge | NO | early cancel |
| Kyouko guard/dodge | NO | custom pre-super logic |
| Walpurgis superArmor | NO | separate local field |
| Nutcracker superArmor | NO | separate local field |
| Kriemhild damage budget | NO | separate rolling accumulator |
| Grief Seed source whitelist | NO | explicit source rejection |
| Wheel source whitelist | NO | explicit source rejection |
| same-owner EasyMode | NO | explicit friendly-fire rejection |
| normal unmodified vanilla mob | YES | no custom gate before vanilla cooldown |

This explains the architecture:
**Garnet removes vanilla's broad global multi-hit limiter, then QB reintroduces intentional local limits where character/boss design needs them.**

## 12. Recommended ANCHOR damage pipeline

Do not emulate the legacy behavior as scattered direct field writes.

Recommended explicit stages:

1. **Attack identity**
   - encounter id;
   - attack/volley id;
   - projectile id;
   - shooter UUID/entity;
   - owner UUID;
   - damage type.

2. **Admission**
   - faction/friendly-fire;
   - source whitelist;
   - absolute form immunity.

3. **Reactive defense**
   - guard;
   - dodge;
   - teleport evade/counter;
   - clone interception.

4. **Mitigation**
   - percentage protection;
   - armor/damage-type rules.

5. **Boss gate**
   - per-hit cap;
   - super-armor;
   - rolling window budget.

6. **Multi-hit policy**
   - whether vanilla invulnerability can be bypassed;
   - per-volley hit cap;
   - per-target local cooldown.

7. **Apply damage**
   - use normal Forge/Minecraft damage events where possible.

8. **Side effects**
   - knockback;
   - fire;
   - resource/corruption;
   - counterattack;
   - stats/kill credit.

This provides the same expressive power without mutating global combat semantics unpredictably.

## 13. Suggested reusable contracts

Keep independent:

- `DanmakuHitPolicy`
- `PercentProtectionGate`
- `AbsoluteFormInvulnerability`
- `ReactiveDodgeGate`
- `TeleportCounterGate`
- `PerHitDamageCap`
- `TimedSuperArmor`
- `RollingDamageBudget`
- `FactionDamageConversion`
- `AllowedAttackerGate`
- `DisposableCloneDefense`
- `DefenseSideEffect`

Characters and bosses should compose these rather than inherit one giant combat base.

## 14. LAB cases

For each target type, replay an identical deterministic projectile volley:
- vanilla Zombie;
- transformed Madoka;
- Homura MS/Rebellion/UF;
- Kyouko MS/Rebellion;
- Kirika MS;
- Sayaka Rebellion;
- Walpurgis;
- Nutcracker;
- Kriemhild;
- Grief Seed;
- Wheel;
- Rosso Fantasma.

Run with:
- player shooter;
- owned magical-girl shooter;
- hostile/non-owner Garnet shooter;
- fire side effect on/off.

Capture:
- raw damage;
- post-protection damage;
- accepted/rejected reason;
- invulnerability timer;
- custom armor/budget state;
- resource side effects;
- DamageSource identity;
- kill attribution.

This will let the 1.20.1 reconstruction preserve the **damage contract**, not merely projectile visuals.
