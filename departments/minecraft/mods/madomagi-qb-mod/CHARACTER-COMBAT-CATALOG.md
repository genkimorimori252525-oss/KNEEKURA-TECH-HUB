# QB-MOD 1.6.4.082 — Character combat catalog

Primary evidence: supplied QB-MOD.v.1.6.4.082 archive, SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`.

This document records player-facing attack behavior as implemented in the shipped Java source. It is a LEGACY/COMPARATIVE track catalog; direct 1.20.1 Forge portability is not implied.

## Shared dispatcher

`EntityMahoShojo` exposes three combat methods and the shared AI selects them by distance:

- `shortRangeAttack(target, tick)`
- `middleRangeAttack(target, tick)`
- `longRangeAttack(target, tick)`

Special Rebellion / Ultimate goals can completely replace the shared dispatcher.

Technique: **distance band → weapon/posture → burst pattern → action tick → Soul Gem cost**, with form-specific AI allowed to override the whole loop.

---

## Madoka

Source:
- `entity/passive/EntityMadoka.java`
- `entity/passive/EntityMadokaAIUltimate.java`
- `entity/projectile/EntityLightArrow*.java`

### Normal transformed combat

**Short range**
- fires 5 Light Arrows in one action;
- speed 3.6, inaccuracy 60;
- each receives +1 Punch;
- Soul Gem +1;
- 20-tick cooldown.

This is not a precision shot. The very large inaccuracy value makes it a close-range radial/scatter pressure pattern.

**Middle range**
- one Light Arrow per action;
- speed 1.6, inaccuracy 6;
- +5 Power;
- 3-tick spacing for seven rapid-fire continuation steps, then 10-tick recovery;
- Soul Gem is charged at burst end.

Technique: **fast sustained precision burst with resource cost paid per completed burst rather than per projectile**.

**Long range**
- four Light Arrows are emitted per action;
- speed 1.6 normally, 4.8 against IGarnetEnemyFlying/Ghast/Dragon/Wither;
- inaccuracy 12, +3 Power;
- repeated over five burst calls before 15-tick recovery: up to 20 arrows per complete sequence;
- Soul Gem +1 at burst end.

Technique: **explicit anti-air projectile-speed adaptation without changing the nominal attack band**.

### Ultimate Form

`EntityMadokaAIUltimate` makes Madoka fly and aim upward.

Every 5 ticks:
- launches 3 `EntityLightArrow3` vertically with heading vector (0, 20, 0);
- marks those arrows `checkEnemy`, causing autonomous target acquisition after launch;
- if a live attack target exists, launches one additional LightArrow3 associated with that target, also vertically.

This produces a **launch upward → acquire/turn → rain/homing strike** pattern rather than a direct bow shot.

The targeted LightArrow3 additionally receives a damage bonus and, on target impact, first reduces current target HP to roughly 95% of its previous value (floor, minimum 1) before normal impact damage. This is a percentage-health pressure mechanic and must not be copied blindly to ANCHOR boss combat.

---

## Homura

Source:
- `entity/passive/EntityHomura.java`
- `entity/passive/EntityHomuraAIRebellion.java`
- `entity/passive/EntityHomuraAIUltimate.java`

### Normal transformed combat

**Short range — handgun burst**
- Garnet bullets, speed 1.0, inaccuracy 1.2;
- +5 Power;
- repeated with 5-tick spacing through an 8-step burst;
- Soul Gem +1 at burst end;
- 20-tick recovery.

**Middle range — assault rifle**
- Garnet bullets, speed 1.6, inaccuracy 12;
- +2 Power;
- 2-tick spacing through a 31-step burst;
- Soul Gem +1 at burst end;
- 20-tick recovery.

Technique: **weapon identity is encoded mainly by cadence/spread/damage parameters on one shared projectile base**.

**Long range — teleport + planted TNT**
- chooses a position inside/around the target bounding space;
- attempts up to 64 random teleports around Homura;
- after successful teleport, primes TNT at the selected target position;
- fuse is shortened from vanilla using `fuse / 8 + random + random`;
- TNT inherits the target's current motion vector.

Against Walpurgisnacht a special branch:
- fuse forced to 1;
- repeated at 1-tick cadence up to a 16-step sequence;
- launches a firework rocket from Homura toward Walpurgis as presentation/aim cue;
- long recovery of 100 ticks after the sequence.

Technique: **movement trick and delayed-area attack are coupled into one combat action**.

### Rebellion

`EntityHomuraAIRebellion`:
- enables flight;
- movement is target vector plus a continuously changing sine/cosine perturbation;
- velocity is capped near 0.8;
- every 15 ticks, if line-of-sight exists, emits 8 `EntityLightArrow2` homing arrows;
- +10 Power bonus;
- close collision additionally performs melee and random knockback;
- Soul Gem +1 per ranged volley.

Technique: **analytic oscillatory pursuit + homing volley**, distinct from path navigation.

### Ultimate Form

`EntityHomuraAIUltimate` is unusually direct:
- flies while tracking one target;
- repeatedly attempts melee;
- a successful hit also cuts target current HP to ~95%, minimum 1;
- after prolonged inability to damage the target, target HP is forced to 1 and an explosion is created;
- after a still longer threshold, target HP is set to 0.

This is effectively an **execution/escalation mechanic**, implemented through direct health mutation. The gameplay concept can be studied, but ANCHOR should replace direct `setHealth` kill logic with a scoped, rule-aware damage system.

---

## Sayaka

Source:
- `entity/passive/EntitySayaka.java`
- `entity/passive/EntitySayakaAIRebellion.java`
- `entity/passive/EntitySayakaAIUltimate.java`
- `entity/projectile/EntityCutlass.java`

### Normal transformed combat

Sayaka uses a **blade stock / recall-and-throw** mechanism.

At the start of every range method she first scans for `EntityCutlass` within 3 blocks:
- if one exists, that world Cutlass entity is removed;
- a new Cutlass projectile is fired at the current target;
- flying targets use higher projectile speed.

If no stored Cutlass is available:

**Short**
- normal melee when in collision range.

**Middle**
- directly accelerates Sayaka toward the target at 0.5 × target displacement;
- then melees when in collision range.

**Long**
- when navigator has no path and Sayaka is grounded, spawns 5 Cutlass entities around her in a ring-like random-angle distribution;
- these become the stock consumed by later `checkCutlass` calls;
- Soul Gem +1.

Technique: **deploy physical weapon props → later consume props into active projectiles**. This is highly reusable for magical weapon staging.

### Rebellion

- full 3D flight pursuit;
- target vector receives small random offsets;
- velocity is additive and distance-dependent;
- melee triggers random 3D knockback;
- 20-tick attack cadence;
- Soul Gem +1 on hit.

### Ultimate

Movement and melee pattern remain similar to Rebellion, but Ultimate continuously calls `canSummon/doSummon`.

Sayaka's summon is `EntityServantOktavia`:
- 40 HP, 20 attack;
- movementSpeed attribute 0, but custom flying AI directly sets position/movement;
- despawns if master leaves Ultimate Form;
- summon costs Soul Gem +5.

Technique: **form-bound servant whose lifetime contract is tied to the master's state rather than an independent timer**.

---

## Mami

Source:
- `entity/passive/EntityMami.java`
- `entity/projectile/EntityMusket.java`
- Garnet bullet base

### Short range

- melee hit;
- launches target strongly backward;
- sends `Gambe d'oro!`;
- Soul Gem +1.

### Musket staging

`checkMusket()` searches for nearby `EntityMusket` world entities and removes one if found.

This means the visible musket entities are not merely decorations: they are a **stored attack token**.

### Middle range

If a staged Musket exists:
- consume one Musket;
- immediately fire a low-spread Garnet bullet.

If none exists and Mami is grounded:
- create 4 Musket entities around herself at random radial angles;
- Soul Gem +1;
- sends `Danza del Magic Bullet!`.

If airborne:
- direct bullet shot with a smaller damage bonus and flame enchant bonus.

Technique: **deploy gun props first, then consume them on future AI cycles to fire**.

### Long range

Conditional finisher logic:

If target HP <10:
- target max HP >30 → critical Garnet bullet, very low inaccuracy, `Tiro Finale!`, Soul Gem +1, 30-tick recovery;
- because Garnet bullets inherit `EntityGarnetThrowable`, that critical flag creates a **strength-6 explosion on entity impact** (or strength 4 on block impact) before/alongside the normal projectile damage path;
- otherwise stronger direct shot, `Tiro!`.

So `Tiro Finale!` is not merely a higher-critical-chance bullet. In the shipped Garnet substrate, it is an **explosive execution/finisher round**.

If target HP >=10:
- use one staged Musket if available;
- otherwise, grounded Mami deploys **12 Muskets** around herself and announces `Danza del Magic Bullet!`;
- airborne fallback is a direct higher-power bullet.

Technique: **target-health-aware finisher plus staged weapon-array presentation**.

---

## Kyouko

Source:
- `entity/passive/EntityKyouko.java`
- `entity/passive/EntityKyoukoAIRebellion.java`
- `entity/passive/EntityRossoFantasma*.java`
- `entity/projectile/EntitySpear*.java`

### Normal transformed combat

**Short**
- melee;
- randomized knockback vector;
- Soul Gem +1.

**Middle**
- directly sets own velocity to 0.5 × displacement toward target;
- effectively a spear/lunge gap closer;
- on contact, performs the same melee/knockback.

**Long**
- fires four `EntitySpear` projectiles per attack;
- speed 2.0 or 6.0 against flying targets;
- repeats as a multi-step burst;
- inherits weapon Sharpness/Smite/Bane, Knockback and Fire Aspect into projectile stats.

Technique: **melee enchantments projected into thrown-weapon entities**.

### Rebellion

`EntityKyoukoAIRebellion` retains pathfinding but switches attacks according to path state:
- if navigator has a path → short melee;
- no path and target <25 sq distance → middle lunge;
- no path and farther → long spear attack.

Additionally:
- `while (canSummon()) doSummon()` immediately fills the servant allowance;
- Kyouko allows up to 3 `EntityRossoFantasma`.

Rosso Fantasma:
- 1 HP clones;
- copy the master's held item;
- disappear when Rebellion ends;
- any positive damage kills the clone;
- use independent pursuit/attack;
- if no path at long distance, their attack AI directly relocates the clone to the target position.

Technique: **state-bound combat clones as expendable pressure units**.

---

## Kirika

Source:
- `entity/passive/EntityKirika.java`
- `entity/projectile/EntityClaw.java`

Kirika's defining mechanic is **debuff-first pursuit**.

Short/middle:
- if target lacks Slowness, applies Slowness for 300 ticks and Weakness II for 300 ticks;
- short attacks in melee range;
- middle range directly accelerates Kirika at 1.25 × displacement toward target before melee;
- Soul Gem +1 on hit.

Long:
- applies stronger Slowness II for 100 ticks if absent;
- fires three `EntityClaw` projectiles;
- speed 2.0 or 6.0 against flying targets;
- inherits melee enchantment effects into projectile damage/knockback/fire;
- burst cadence tracked by `rapidFire`.

Technique: **control effect is applied before hit confirmation**, making crowd-control part of target acquisition/pressure rather than projectile impact.

---

## Yuri

Source:
- `entity/passive/EntityYuri.java`
- `entity/passive/EntityCornoForte.java`

### Shared summon branch

At every attack band, Yuri checks `canSummon()` before her normal attack. If ready:
- summons `EntityCornoForte`;
- servant persists only while Yuri remains transformed;
- Soul Gem +1.

Corno Forte:
- 10 HP, 7 attack;
- movement speed 0.2;
- sprint state is derived from move-helper speed;
- sprinting collision adds knockback.

Technique: **attack-band-independent opportunistic summon inserted before normal attack selection**.

### Short

- melee knockback plus handgun shot;
- handgun burst repeats on a 6-tick cadence;
- Soul Gem charged at burst end.

### Middle

- repeated Garnet bullet fire;
- speed 1.6, inaccuracy 9;
- +6 Power;
- 6-tick cadence.

### Long

First tries `attackDestroy(target)`:
- targets blocks two levels below enemy;
- performs connected-block search;
- converts selected terrain positions to stationary primed TNT;
- if successful, Soul Gem +1 and 80-tick recovery.

If no terrain attack succeeds:
- falls back to the middle-style gun burst, with higher projectile speed against flying targets.

Technique: **terrain attack is a conditional primary long-range action with ranged projectile fallback**.

---

## Cross-character reusable patterns

Keep these as separate techniques:

1. burst state with resource payment at burst boundary;
2. anti-air speed adaptation;
3. staged world-prop weapon arrays;
4. deploy-now / consume-later projectile stock;
5. path-state-dependent attack selection;
6. direct velocity lunge;
7. analytic oscillatory flight;
8. target-health-aware finisher;
9. form-bound servants;
10. expendable combat clones;
11. conditional terrain-to-explosive attack;
12. homing projectile rain;
13. percentage-health pressure / execution escalation;
14. debuff-before-hit target pressure.

Do not create one universal “magical girl AI” from these. Their value is the ability to recombine independent techniques.