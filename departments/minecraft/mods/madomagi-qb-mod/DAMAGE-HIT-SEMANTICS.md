# QB-MOD / Garnet-MOD 1.6.4.082 — Damage / hit / i-frame semantics

Date: 2026-10-07

Primary evidence:
- Garnet-MOD SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`
- QB-MOD SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`

This subsystem is essential to reproducing the combat feel. The visible volley count is **not** enough: Garnet deliberately changes Minecraft's ordinary damage-invulnerability behavior so rapid projectile hits can all matter.

## 1. Shared projectile i-frame reset

Both Garnet projectile foundations execute this immediately before their main damage call:

`entityHit.hurtResistantTime = 0;`

Locators:
- `MCP/garnet/mods/entity/projectile/EntityGarnetArrow.java:338-417`
- `MCP/garnet/mods/entity/projectile/EntityGarnetThrowable.java:69-139`

In vanilla 1.6.4 `EntityLivingBase.attackEntityFrom`, a target with `hurtResistantTime > maxHurtResistantTime / 2` rejects an equal/lower hit and only accepts the excess of a stronger hit. A normal accepted hit resets the timer to `maxHurtResistantTime` (20).

Therefore Garnet's reset changes the contract:

**each projectile impact enters vanilla damage handling as if the ordinary recent-hit cooldown had already expired.**

Practical consequence:
- Madoka burst arrows;
- Homura bullet streams;
- Kyouko spear volleys;
- Kirika claw volleys;
- LightArrow homing storms;
- Mami bullets;

are not expected to collapse into one effective hit merely because multiple projectiles arrive inside the normal hurt-resistance window.

This is one of the most important recovered combat primitives in the entire framework.

## 2. This does not bypass every defense

The reset occurs **before calling the target's `attackEntityFrom`**, but a target can still reject/reshape damage in its own override before the vanilla cooldown gate.

Examples:

### Walpurgisnacht
Uses its own field:
- valid incoming damage is capped to 1;
- `superArmor=20` after a valid hit;
- while `superArmor !=0`, later damage is forced to 0/rejected/countered.

So projectile `hurtResistantTime=0` does **not** remove Walpurgis's custom 20-tick boss gate.

### Homulilly Nutcracker
Likewise:
- damage >=1 becomes 1;
- independent `superArmor=20`;
- servant-origin damage heals/rejects.

Again the projectile reset does not defeat the local boss gate.

### Homura / Madoka Ultimate
Character-specific `attackEntityFrom` can return false before the base damage pipeline:
- Homura UF rejects incoming damage;
- Madoka UF rejects incoming damage.

No i-frame reset can force damage through an explicit entity override returning false.

### Kyouko / Kirika
Character-specific guard/dodge logic executes before base damage:
- Kyouko can guard, dodge or consume Rosso Fantasma-related defense;
- Kirika has a random dodge branch while transformed.

The important separation is:

`projectile i-frame bypass` ≠ `invulnerability/guard/super-armor bypass`.

## 3. EntityGarnetArrow damage contract

Impact damage:

`ceil(projectile speed magnitude × getDamage(target))`

Default base damage:
`2.0`.

Critical Arrow state:
- adds random extra direct damage;
- does not create the Throwable-style critical explosion.

Other Arrow behavior:
- burning projectile sets hit entity on fire for 5 seconds;
- successful hit can apply configured knockback;
- successful living hit increments arrow-count visual state;
- shooter is ignored for collision only during the first 5 air ticks;
- unsuccessful damage causes the projectile to reverse at 10% velocity instead of dying.

DamageSource:
- no shooter → `causeThrownDamage(projectile, projectile)`;
- shooter present → `causeThrownDamage(projectile, shootingEntity)`.

This means the attacker exposed through `DamageSource.getEntity()` is normally the actual shooter entity.

## 4. EntityGarnetThrowable damage contract

Impact direct damage:

`ceil(projectile speed magnitude × getDamage(target) / 2)`

Default base damage:
`2.0`.

On entity hit, order is:

1. compute direct damage;
2. apply fire if burning;
3. **if critical, create strength-6 block-damaging explosion at projectile position**;
4. set `entityHit.hurtResistantTime=0`;
5. try thrown-damage hit;
6. if that failed and target is not `EntityGarnetBase`, try mob-damage hit;
7. if that also failed and thrower is an enabled `EntityGarnetTameable`, try player-damage attributed to its owner;
8. apply knockback on successful paths;
9. emit poof particles / impact sound;
10. kill projectile server-side.

This is a **DamageSource fallback ladder**, not normal ownership attribution.

## 5. DamageSource fallback ladder

First attempt:

`DamageSource.causeThrownDamage(projectile, thrower)`

If rejected and target is **not** an `EntityGarnetBase`:

Second attempt:

`DamageSource.causeMobDamage(thrower)`

If rejected again and thrower is an enabled Garnet tameable:

Third attempt:

`DamageSource.causePlayerDamage(thrower.owner)`

Implications:

- ordinary successful NPC projectile damage is normally attributed to the NPC thrower, not its owner;
- owner/player attribution is a fallback after two rejected source shapes;
- Garnet-derived targets do **not** receive the mob/player fallback ladder at all;
- target code that branches on source type can therefore produce different results from the same projectile after an initial rejection.

This is powerful but difficult to reason about. It should not be copied literally to ANCHOR.

Recommended 1.20.1 contract:
- choose one authoritative damage source/type at attack creation;
- carry `owner UUID`, `shooter entity`, `attack id` and `projectile id` separately;
- do not retry the same impact under unrelated damage-source categories simply to force acceptance.

## 6. Friendly-fire interaction

`EntityMahoShojo.attackEntityFrom` in EasyMode rejects damage when:
- `DamageSource.getEntity()` is another EntityMahoShojo;
- target is enabled;
- both magical girls resolve to the same owner.

Because Garnet projectiles normally expose the shooter as `DamageSource.getEntity()`, the first thrown-damage attempt participates in this rule.

For Throwable impacts against Garnet targets, the fallback ladder is disabled by the `instanceof EntityGarnetBase` check, so an EasyMode rejection is not then reclassified as owner-player damage.

This is an important emergent compatibility between:
- projectile source attribution;
- Garnet class boundary;
- QB friendly-fire policy.

## 7. Magical-girl protection is attacker-type asymmetric

`EntityGarnetBase.attackEntityFrom` applies `getProtectStrength()` only when:
- attacker entity is **not** a player;
- DamageSource is **not** fire damage.

Formula:

`floor(incoming × (100 - protectionPercent) / 100)`.

Examples of form protection:
- Homura MS 15%;
- Homura Rebellion 90%;
- Homura UF 100% before her separate UF invulnerability override;
- Madoka MS 10%;
- Madoka UF 100%;
- Mami MS 20%;
- Sayaka MS 30%;
- Sayaka Rebellion/UF 60%;
- Kyouko Rebellion 20%;
- Yuri MS 20%.

Consequences:
- NPC-fired projectile direct hits normally count as non-player attacker damage and are reduced by form protection;
- player-fired projectiles are not reduced by this specific protection formula;
- burn damage is a separate fire DamageSource and bypasses this protection rule;
- projectile i-frame reset still allows repeated **post-protection** hits to land unless another defense rejects them.

The protection system is therefore not “armor” in the generic sense. It is a **source-class-conditioned percentage filter**.

## 8. Mami Tiro Finale is a compound impact

`EntityMami.longRangeAttack` calls:

`mamiShot(target, 1.6F, 0.3F, 0, 1, 0, true)`

when:
- target health <10;
- target max health >30.

The last argument marks the Garnet Bullet critical.

For `EntityGarnetThrowable`, critical means:
- **strength-6 block-damaging explosion is created before direct projectile damage**.

Then the impacted entity's `hurtResistantTime` is reset to zero and direct bullet damage is attempted.

Therefore Tiro Finale is statically a **compound explosion + direct-hit attack**, not merely a bullet with a random critical-damage multiplier.

The ordering matters:
- explosion can damage the target and surroundings first;
- the target's ordinary hurt cooldown from that explosion is then explicitly cleared;
- the direct bullet can still enter damage handling immediately afterward.

This is a high-value finding for any faithful Mami reconstruction.

## 9. Spear2 amplifies one impact into six i-frame-resetting children

`EntitySpear2.onImpact`:
- spawns six `EntitySpear` children;
- then calls its own GarnetThrowable base impact.

The children are GarnetArrow-derived and therefore each independently resets ordinary hurt resistance when they later hit.

Thus Kyouko's player Spear2 has two layers:
1. carrier impact;
2. six secondary projectiles whose later impacts are individually eligible as fresh hits.

This is not just visual fan-out. The damage contract explicitly supports multi-hit follow-through.

## 10. LightArrow2/3 and target lock

LightArrow2:
- after delayed target acquisition, steers every update;
- ignores entity impacts that are not its selected target;
- when selected target is hit, uses the GarnetThrowable i-frame-reset pipeline.

LightArrow3:
- first mutates selected target HP toward 95% of its current value;
- then delegates to LightArrow2/GarnetThrowable impact;
- therefore its direct standard damage follows immediately after the percentage-health mutation with the ordinary cooldown cleared.

This creates a two-stage hit:
`health transform → standard projectile hit`.

Modern reconstruction should not use direct `setHealth`; use an explicit rule-aware execute/percentage-damage contract.

## 11. Fire / knockback / hit feedback are tied to successful standard damage

Both projectile bases can propagate:
- burning;
- knockback;
- impact sounds;
- visual particles.

However exact sequencing differs:
- fire is applied before the direct `attackEntityFrom`;
- knockback is conditional on successful damage paths;
- Throwable critical explosion occurs before direct damage;
- Arrow unsuccessful hits ricochet/reverse instead of simply disappearing.

These details matter when building an equivalent combat feel.

## 12. Why this matters for danmaku reconstruction

If a modern implementation reproduces:
- projectile count;
- speed;
- spread;
- homing;

but leaves ordinary Minecraft i-frames untouched, many QB/Garnet volleys will deal dramatically fewer effective hits than the legacy design.

Conversely, globally setting every target's invulnerability timer to zero would also be wrong because:
- vanilla combat balance changes;
- unrelated MOD damage becomes affected;
- custom boss super-armor/guards need their own rules;
- multiple projectiles from one attack may need per-attack caps.

Recommended ANCHOR abstraction:

`DanmakuHitPolicy`

Fields/concepts:
- attack/volley ID;
- projectile ID;
- intended per-target hit cooldown;
- max hits per target per volley;
- whether vanilla i-frame bypass is allowed;
- boss/guard/super-armor interaction;
- owner/shooter attribution;
- damage type;
- knockback/fire/explosion side effects.

The goal is to preserve **multi-hit semantics locally**, not remove Minecraft i-frames globally.

## 13. Static test cases for LAB

1. 8 Homura bullets hitting one vanilla Zombie inside 10 ticks.
2. 20 Madoka long-range arrows converging on one target.
3. 24 Kyouko Spears from one long burst.
4. Spear2 carrier + six children on one large target.
5. LightArrow2 swarm with same target.
6. same volleys against:
   - vanilla LivingEntity;
   - transformed magical girl;
   - Rebellion Homura;
   - Walpurgis;
   - Nutcracker.
7. Mami Tiro Finale:
   - direct target damage;
   - explosion damage;
   - direct hit after explosion;
   - nearby collateral;
   - block destruction.
8. EasyMode same-owner magical-girl projectile friendly fire.
9. player-fired vs NPC-fired projectile against protected magical-girl forms.

Metrics:
- accepted damage events;
- rejected damage events;
- health delta;
- source identity/type;
- invulnerability timer before/after;
- boss super-armor state;
- knockback/fire application;
- explosion collateral.

This should become part of the future LAB trajectory/combat oracle, not merely a renderer test.
