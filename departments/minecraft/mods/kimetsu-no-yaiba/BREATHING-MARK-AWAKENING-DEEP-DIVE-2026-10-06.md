# Kimetsu no Yaiba ver3 — Breathing / Mark / Awakening Deep Dive — 2026-10-06

## 1. Scope

This is a second-pass deep dive over the uploaded ver3 JAR, focused on:

- Breathing technique selection/execution
- representative form timing and movement
- Demon Slayer Mark
- Transparent World
- Yoriichi awakening/effect
- Crimson Red Blade
- mastery/unlock progression
- shared cooldown / swing-readiness modifiers

Pinned binary:

`KimetsunoYaiba-ver3-forge-1.20.1.jar`

SHA-256:

`b4af6e8a9d5926c5fea212a5e237e61f1e8095a5be23eca9b8294258a3b466b6`

There is no pinned official source repository for ver3, so all implementation claims below are based
on JAR bytecode/resources.

Evidence labels:

- **DIRECT_OBSERVATION** — bytecode/resource fact
- **AUTHOR_CLAIM** — public release/project text
- **INFERENCE** — engineering interpretation
- **UNKNOWN** — not established

---

# 2. The progression graph

The relevant advancement JSONs are all `minecraft:impossible` and are granted by Procedures.

The current graph is:

```text
strongest
   |
receive_20_damage
   |
receive_40_damage
   |
receive_60_damage
   |
receive_80_damage
   |
receive_100_damage
   |
demon_slayer_mark
   |
breathing_20
   |
breathing_40
   |
breathing_60
   |
breathing_80
   |
breathing_100
   |
transparent_world
```

Separate branch:

```text
demon_kill_count_50
   |
crimson_red_nichirin_blade
```

This means the mod treats:

- Mark as a survivability/awakening milestone
- breathing mastery as post-Mark practice
- Transparent World as post-mastery
- Crimson Red Blade as a separate combat-achievement branch

## 2.1 Display names do not equal internal thresholds

`WhenEntityTakesDamageProcedure.execute`

The persistent counter is:

`PlayerVariables.player_receiveDamage`

The actual bytecode thresholds are:

| Advancement | Actual accumulated damage threshold |
|---|---:|
| receive_20_damage | 50 |
| receive_40_damage | 100 |
| receive_60_damage | 200 |
| receive_80_damage | 400 |
| receive_100_damage | 800 |

These values are **DIRECT_OBSERVATION** from bytecode.

The apparent mismatch between advancement name and actual threshold is not explained in the JAR.

---

# 3. Player Demon Slayer Mark unlock

## 3.1 Prerequisite

`WhenEntityTakesDamageProcedure`

Damage accumulation only runs when:

- player is a ServerPlayer
- `strongest` is complete
- `receive_100_damage` is not complete

After receive_100_damage becomes complete, a later qualifying damage path can advance to Mark
unlock.

## 3.2 Unlock action

The same Procedure:

- grants `kimetsunoyaiba:demon_slayer_mark`
- applies `POTION_DEMON_SLAYER_MARK`
- duration: **3000 ticks**
- amplifier: 0

Therefore the advancement unlock and first awakening are coupled.

## 3.3 Incoming-damage modifier

While Demon Slayer Mark effect is active, the incoming-damage path multiplies its local damage
amount by:

`0.9`

So level-0 Mark provides an explicit 10% reduction in this Procedure's damage calculation path.

This is independent from the later cooldown/level bonuses.

---

# 4. Mark activation key

Input path:

```text
client key
 -> KeyDemonSlayerMarkMessage
 -> server
 -> KeyDemonSlayerMarkOnKeyPressedProcedure
```

The Procedure requires the persistent `demon_slayer_mark` advancement.

## 4.1 Mark currently absent

Apply:

- Demon Slayer Mark
- duration: **6000 ticks**
- amplifier 0

The key is therefore a re-awakening action after the permanent advancement unlock.

## 4.2 Tanjiro Nichirin variants

When the held mainhand matches the Tanjiro Nichirin variants, the same activation also applies:

- `POTION_YORICHI`
- duration: **3000 ticks**
- amplifier 0

## 4.3 Yoriichi sword

When the held mainhand is the Yoriichi sword:

- `POTION_YORICHI`
- duration: **6000 ticks**
- amplifier 0

Thus sword identity changes the awakening package.

## 4.4 Mark already active

The key does **not** simply toggle Mark off.

If:

- Mark is already active
- `crimson_red_nichirin_blade` advancement is complete

the Procedure attempts to promote a valid Nichirin blade in mainhand/offhand to:

- `CRIMSON_RED_BLADE`
- level **2**

This makes one input key context-sensitive:

```text
not marked:
  awaken

marked + red-blade unlock:
  weapon enhancement
```

---

# 5. Mark presentation/style

`PotionDemonSlayerMarkPotionStartedappliedProcedure`

The mark's visual identity is inferred from current entity/weapon conditions.

Observed branches include:

- Tomioka / Tomioka Nichirin -> Water mark head item path
- Shinazugawa / Shinazugawa Nichirin -> Wind mark head item path
- Muichirou / Tokito Nichirin -> replace the Muichirou hair/helmet with mark variant

The architecture does not expose a strongly typed:

`MarkStyle.WATER / WIND / MIST / ...`

Instead presentation is reconstructed from:

- concrete entity class
- held item
- existing head equipment

**INFERENCE:** a typed MarkStyle value would be easier to synchronize/debug and would separate
cosmetic identity from inventory heuristics.

---

# 6. Mark active effect: Regeneration

`PotionDemonSlayerMarkOnEffectActiveTickProcedure.execute`

The Procedure checks vanilla:

- `MobEffects.f_19605_`

Minecraft 1.20.1 mapping:
- **REGENERATION**

If the entity does not already have it, the code applies:

- Regeneration
- duration: `Integer.MAX_VALUE`
- amplifier: 0

This is effectively persistent on ordinary gameplay timescales.

## 6.1 Expiry cleanup

`PotionDemonSlayerMarkPotionExpiresProcedure`

The observed expiry code is concerned with character/head presentation, including Tanjiro head
restoration.

It does **not** remove the long-duration Regeneration.

A bounded JAR reference search found no Mark-specific Regeneration cleanup path.

Therefore:

**DIRECT_OBSERVATION**

> A Mark activation can install a MAX_INT Regeneration effect that survives the Mark's normal
> expiration unless some unrelated system later removes/replaces it.

Whether this is intended is **UNKNOWN / likely-design-risk inference**.

No runtime reproduction was performed.

---

# 7. NPC Hashira awakening

Player unlock is advancement-driven.

NPC Hashira use a different policy.

`ActiveHashiraProcedure.execute`

Named Hashira branches include:

- Tomioka
- Shinazugawa
- Iguro
- Muichirou
- Kanroji
- Himejima

When the awakening condition is reached (notably below roughly half health in the observed path),
the Procedure can apply:

- Demon Slayer Mark
- duration: `Integer.MAX_VALUE`
- amplifier 0

and a long-lived vanilla Strength effect.

This makes NPC awakening combat-state-driven rather than progression-driven.

Conceptually:

```text
Player:
  unlock progression -> key activation

NPC Hashira:
  combat health threshold -> automatic awakening
```

Keeping those two **activation policies** separate while sharing the same **modifier set** is a
good reusable model.

---

# 8. Effective level modifier

`GetLevelProcedure.execute`

Base:

- `PlayerVariables.PlayerLevel`

Then:

## Demon Slayer Mark

Adds:

`2 * (markAmplifier + 1)`

At amplifier 0:

- **+2 effective levels**

## Yoriichi effect

Adds:

`2 * (yoriichiAmplifier + 1)`

At amplifier 0:

- **+2 effective levels**

Therefore a level-0 Mark + level-0 Yoriichi effect contributes:

- **+4 effective levels**

This is one reason the awakening state can affect many downstream systems without every Breath form
having an explicit Mark check.

---

# 9. Shared cooldown modifiers

`CalculateCooldownTimeProcedure.execute`

Base cooldown:

`max(item.cooltime, item.select_cooltime)`

Then several global modifiers are applied.

## 9.1 Strength

If vanilla Strength is active:

```text
cooldown /= 1 + min(amplifier, 10) * 0.025
```

Important implementation detail:

- this uses the raw amplifier
- not amplifier + 1

Therefore Strength I (amplifier 0) provides **zero cooldown reduction** in this exact formula.

## 9.2 Hashira Training — Mist

If the corresponding advancement is present:

`cooldown *= 0.9`

## 9.3 Transparent World

For each:

`amplifier + 1`

iteration:

`cooldown *= 0.9`

At amplifier 0:

- 10% reduction

## 9.4 Demon Slayer Mark

Same iterative rule:

`cooldown *= 0.9`

for each `amplifier + 1`.

At amplifier 0:

- 10% reduction

## 9.5 Combined level-0 Mark + Transparent World

```text
0.9 * 0.9 = 0.81
```

So before other modifiers:

- cooldown becomes **81%**
- equivalent to a **19% reduction**

## 9.6 Modifier-level inconsistency

Strength uses:

`amplifier`

Mark/Transparent use:

`amplifier + 1`

This is an implementation inconsistency.

A typed modifier system should decide whether "level 1" means amplifier 0 or an explicit level 1
before formulas are written.

---

# 10. Swing/readiness modifier

`TestSwingItemProcedure.execute`

The Procedure builds an internal readiness budget.

Observed contributions:

## Strength

`+(amplifier + 1)`

## Demon Slayer Mark

`+(amplifier + 1)`

## Yoriichi

`+(amplifier + 1)`

## Transparent World

`+2 * (amplifier + 1)`

It then compares this budget against remaining `COOLTIME_2` duration.

Thus Transparent World is deliberately weighted more strongly in this readiness path than Mark or
Yoriichi.

The same Procedure also checks:

- existing `skill`
- `breathes`
- `demon_art`
- numeric opcode remainder ranges

before allowing a swing.

This is another example of a useful centralized gate implemented through hard-coded numeric
protocols.

---

# 11. Breathing mastery

`PlayerAttackTimesProcedure.execute`

The usage counter:

`PlayerVariables.player_usedBreathingNum`

does **not** always increment.

The observed gate requires:

- player has Demon Slayer Mark advancement
- breathing_100 is not already complete

Then a recognized attack increments the counter.

Milestones:

- 20
- 40
- 60
- 80
- 100

grant the corresponding `breathing_*` advancements.

Therefore the progression order is intentional in code:

```text
unlock Mark first
 -> then practice Breathing
 -> reach 100-use mastery
```

This is not merely an advancement-parent visual relationship.

---

# 12. Transparent World unlock

Advancement:

`transparent_world.json`

Parent:

`breathing_100`

Trigger:
`minecraft:impossible`

Actual unlock is in:

`PlayerAttackTimesProcedure`

Once `breathing_100` is already complete, a later qualifying attack path checks Transparent World.

If the advancement is not complete:

- grant `transparent_world`
- apply `POTION_TRANSPARENT_WORLD`
- duration: **30 ticks**
- amplifier 0

Because milestone-grant branches exit to the Procedure end, the 100th-count call does not appear to
be the same path that performs the Transparent World grant; a subsequent recognized attack reaches
the already-`breathing_100` path.

---

# 13. Transparent World active behavior

Unlike Demon Slayer Mark, `PotionTransparentWorldMobEffect` does not contain a large active-tick
combat Procedure.

Observed gameplay consumers include:

- `CalculateCooldownTimeProcedure`
- `TestSwingItemProcedure`
- Transparent World overlay
- selected high-tier NPC AI paths
- Compass Needle logic

## 13.1 Cooldown

Level-0:
- x0.9 cooldown

## 13.2 Swing readiness

Level-0:
- +2 readiness-budget contribution

## 13.3 HUD

`OverlayTransparentWorldDisplayOverlayIngameProcedure`

shows the Transparent World overlay only while the MobEffect is present.

## 13.4 Player duration anomaly

Bounded reference analysis found the player unlock path applying Transparent World for **30 ticks**.

Other player-facing references test/consume the effect, but no recurring player re-activation path
was found in the bounded search.

Once the advancement is complete, the unlock branch is not normally entered again.

Therefore current static behavior is:

```text
persistent advancement unlock
       |
one 30-tick effect application
       |
effect expires
```

unless another external path applies the effect.

This behavior is **DIRECT_OBSERVATION** from the bounded JAR call graph.

Whether it is intended is **UNKNOWN**.

Given that cooldown, swing logic and HUD require the active effect, it is a strong candidate for a
missing activation/reapply path, but that is **INFERENCE**, not a reproduced bug.

---

# 14. Yoriichi awakening layer

`POTION_YORICHI` is separate from Mark and Transparent World.

## Activation through Mark key

- Tanjiro Nichirin path: 3000 ticks
- Yoriichi sword path: 6000 ticks

## Effective level

`GetLevelProcedure`:

- +2 per amplifier+1

## Swing readiness

`TestSwingItemProcedure`:

- +1 per amplifier+1

## Startup behavior

`PotionYorichiPotionStartedappliedProcedure` includes:

- short vanilla Blindness
- awakening sound/visual behavior
- character-specific command/presentation logic
- Tanjiro head presentation changes in applicable paths

## Active tick

`PotionYorichiOnPotionActiveTickProcedure` is a larger combat/sensing procedure.

It checks held weapon/art categories and performs extra combat-space logic, including nearby
entity/projectile interaction paths.

This makes Yoriichi a distinct elite combat mode, not a cosmetic alias of Mark.

---

# 15. Crimson Red Blade

Persistent unlock:

`crimson_red_nichirin_blade`

is a separate advancement branch.

When Mark is already active, the Mark key can install/upgrade:

- `CRIMSON_RED_BLADE`
- level 2

on a valid Nichirin blade.

## 15.1 Active combat effect

`ActiveRedSwordProcedure.execute`

Requirements:

- weapon has Crimson Red Blade enchant
- target persistent `oni=true`
- target is not `TanjiroDemonEntity`

Then apply:

`REGENERATION_INHIBITION`

Duration:

```text
600 + 300 * max(enchantLevel - 5, 0)
```

Amplifier:

`enchantLevel`

At the normal level-2 Mark-key upgrade:

- duration = 600 ticks
- amplifier = 2

This is a very clean conceptual effect:

> red blade does not need to rewrite every attack's base damage; it attaches an anti-regeneration
> status to demon targets.

---

# 16. Representative Breathing execution grammar

The concrete forms differ substantially, but their generated runtime follows a shared grammar.

```text
counter update
    |
animation setup
    |
movement / helper actor / sampled positions
    |
write shared attack context:
  Damage
  Range
  knockback
  projectile_type
  effect
    |
DoDamage2
    |
particles / sound / block interaction
    |
counter termination
    |
breathes = 0
```

This is the real common "Breathing engine".

---

# 17. Water Breathing examples

## 17.1 Tenth Form / Constant Flux

`BreathesMizu10Procedure`

Observed:

- uses multiple counters
- drives Water particles/animation
- spawns `CONSTANT_FLUX` helper entity
- copies provenance through `SetRangedAmmoProcedure`
- invokes `DoDamage2Procedure`
- writes attack context including:
  - Range around 4 in observed damage phases
  - projectile_type=2 in observed phase
- projectile_type=2 maps to deflection behavior in the common attack kernel

The form is therefore a composite:

```text
owner animation
 + helper actor
 + repeated area attack
 + projectile deflection
```

## 17.2 Eleventh Form / Nagi

`BreathesNagiProcedure`

Observed:

- manipulates body movement during the active state
- creates circular particle geometry around the user
- writes:
  - Range=7
  - knockback=0.7
  - effect=4
  - projectile_type=1
- calls `DoDamage2`

projectile_type=1 means nearby non-strong projectiles can be discarded by the attack kernel.

**Design interpretation:**

Nagi is implemented as a defensive **local field**, not as a separately simulated shield object.

---

# 18. Thunder Breathing example — Thunderclap and Flash

`BreathesHekirekiIssenProcedure`

Observed phase characteristics:

- increments `cnt1`
- early phase briefly applies extremely high Slowness, acting as charge/pose lock
- periodically drives animation
- computes/uses stored directional power components
- active movement sets body delta movement to approximately:
  - `x_power * 2`
  - `y_power * 2`
  - `z_power * 2`
- spatial damage is sampled through `DoDamage2`
- representative damage phase writes:
  - `Damage = 23 * (1 + StrengthAmplifier / 3)`
  - Range=3
  - effect=4
- particles include Lightning / Thunder-specific effects
- termination is governed by counters and `breathes=0`

This is a clear:

```text
charge lock
 -> burst movement
 -> repeated sampled hit volume
 -> exit
```

rather than one vanilla melee swing.

---

# 19. Flame Breathing example — Shiranui

`BreathesShiranuiProcedure`

It uses the same general charge/move/damage framework but with Flame-specific:

- animation opcodes
- particle effects
- timing
- movement values
- Damage/Range
- swing/projectile flags

A representative attack segment writes base Damage around 19 before Strength scaling.

The important result is architectural:

> Thunder and Flame are not separate combat engines.
> They are different temporal/movement programs feeding the same attack kernel.

---

# 20. Mist Breathing example — Seventh Form

`BreathesKasumi7AttackProcedure`

Observed dependencies:

- `SwingKasumiProcedure`
- `PlayAnimationProcedure`
- `DoDamage2Procedure`
- forward power helpers

It carries its own state/counters and opcode 407.

This is an example where:

- a style-specific visual/swing helper
- plus a shared damage kernel

produce the form identity.

---

# 21. Sun Breathing — 13th Form as a program

`BreathesHi13Procedure`

This is one of the strongest reusable findings.

It does not implement a new hit pattern directly.

It uses `cnt4` as a program counter:

| cnt4 | Delegate |
|---:|---|
| 0 | Hi1 |
| 1 | Hi2 |
| 2 | Hi3 |
| 3 | Hi4 |
| 4 | Hi5 |
| 5 | Hi6 |
| 6 | Hi7 |
| 7 | Hi8 |
| 8 | Hi9 |
| 9 | Hi10 |
| 10 | Hi11 |
| 11 | Hi12 |

If a delegated form completes and clears `breathes`:

1. reset `cnt1/cnt2/cnt3`
2. increment `cnt4`
3. set `breathes=1213`
4. next tick delegates the next form

After the final step, the root state clears.

This is effectively:

```text
TechniqueSequence [
  Form1,
  Form2,
  ...
  Form12
]
```

implemented through persistent numeric state.

A typed sequence/combo executor would preserve this excellent composition idea while eliminating
magic-number counters.

---

# 22. Stone Breathing — detached weapon program

`BreathesIwa1Procedure`
`BreathesIwa5Procedure`

Both demonstrate:

- animation
- counters
- `HIMEJIMA_WEAPONS` helper creation
- `SetRangedAmmoProcedure`
- DoDamage2
- BlockDestroy2
- form-specific geometry/timing

This is an important category separate from direct body-dash forms.

The technique is a coordinated program between:

- owner
- detached weapon visual/position actor
- shared attack kernel

---

# 23. Moon Breathing — sampled spatial volumes

Representative:
`BreathesTsuki16Procedure`

Observed:

- Moon particle families
- animation
- repeated spatial sampling
- DoDamage2
- BlockDestroy2
- Range around 5 in observed hit section
- Damage around `21 * (1 + StrengthAmplifier/3)`
- knockback=1
- projectile_type=1
- counter-based exit

This shows that a "ranged sword technique" need not be an actual projectile entity.

Some forms are authored as repeated **world-space AoE samples** along an intended slash geometry.

---

# 24. Technique taxonomy from the JAR

The form implementations can be grouped by execution primitive.

## BODY_MOTION

User body becomes the attack trajectory.

Examples:
- Thunderclap and Flash
- Shiranui-like dash forms

## LOCAL_FIELD

Attack is an area around the user.

Example:
- Nagi

## SAMPLED_SLASH_VOLUME

Procedure computes several world positions and applies the shared kernel.

Example:
- high Moon forms

## HELPER_ACTOR

A detached Entity represents weapon/attack geometry.

Examples:
- Stone weapon
- Constant Flux helper

## MOBILE_AOE_PROJECTILE

Projectile itself calls DoDamage2 every tick.

Examples:
- Moon slash bullets

## TECHNIQUE_SEQUENCE

One high-level form delegates to existing forms.

Example:
- Sun 13th Form

This taxonomy is more reusable than organizing code only by lore style.

---

# 25. Recommended typed reconstruction

## TechniqueId

No raw doubles such as 1601/1213 in gameplay logic.

```text
TechniqueId.STONE_1
TechniqueId.SUN_13
TechniqueId.WATER_11
```

A legacy numeric adapter can exist only for compatibility.

## TechniqueRuntime

```text
TechniqueRuntime {
  technique
  phase
  phaseTick
  localCounters
  targetSnapshot
  helperActors
}
```

Transient data should not live in persistent NBT unless save/reload continuity is explicitly
required.

## TechniqueProgram

```text
TechniqueProgram {
  enter()
  tick()
  exit()
  interrupt()
}
```

## TechniqueSequence

```text
TechniqueSequence<FormStep>
```

for Sun 13 / combo moves.

## AttackContext

```text
AttackContext {
  owner
  technique
  shape
  center
  damage
  knockback
  targetPolicy
  guardPolicy
  projectileInteraction
  effects
  blockInteraction
}
```

## AwakeningState

```text
AwakeningState {
  markUnlocked
  markActive
  markStyle
  transparentWorldUnlocked
  transparentWorldActive
  yoriichiState
  crimsonBladeUnlocked
}
```

This separates permanent progression from transient combat activation.

## CombatModifierSet

Centralized declarative modifiers:

```text
damageTakenMultiplier
effectiveLevelBonus
cooldownMultiplier
swingReadinessBonus
regeneration
specialSenses
```

Forms consume the resulting modifier set instead of querying every MobEffect themselves.

---

# 26. Strongest reusable findings

1. Player and NPC share the same concrete form executors.
2. Style identity is mostly a different temporal/movement program over common combat primitives.
3. DoDamage2 is the correct conceptual center; it should become a typed AttackContext kernel.
4. Sun 13 demonstrates composition of techniques into a higher-order sequence.
5. Stone demonstrates detached weapon actors with owner authority.
6. Mark/Transparent/Yoriichi are best treated as global combat modifiers, not form-specific forks.
7. Progression unlock and temporary activation are different state dimensions.
8. Crimson Red Blade expresses anti-demon regeneration pressure as a status effect rather than
   duplicating damage logic.

---

# 27. Current ver3 anomalies / improvement targets

## 27.1 Player Mark leaves MAX_INT Regeneration

Static evidence:
yes.

Mark-expiry cleanup:
not found.

Runtime reproduction:
not performed.

## 27.2 Player Transparent World is only applied for 30 ticks at unlock

Persistent advancement:
yes.

Bounded recurring activation path:
not found.

Runtime intent:
unknown.

## 27.3 Strength cooldown level semantics

Strength I has amplifier 0, but cooldown formula uses raw amplifier.

Result:
no Strength-I cooldown reduction from that path.

Mark/Transparent use amplifier+1.

## 27.4 Mark style inferred indirectly

Entity type / sword / head inventory chooses visual mark presentation.

Typed style state:
not found.

## 27.5 Magic-number skill protocol

Breathing/Blood Art classification depends on numeric ranges and operations such as `%100`.

## 27.6 Persistent scratch data

Technique timers and attack parameters share Entity persistent NBT.

## 27.7 Fake-damage animation event

Already documented in the whole-target report.

## 27.8 Stone AI no-op range branch

Already documented in the opcode map / whole-target report.

---

# 28. Source locators

All locators refer to the pinned uploaded JAR.

Primary classes:

- `net.mcreator.kimetsunoyaiba.procedures.WhenEntityTakesDamageProcedure`
- `...KeyDemonSlayerMarkOnKeyPressedProcedure`
- `...PotionDemonSlayerMarkOnEffectActiveTickProcedure`
- `...PotionDemonSlayerMarkPotionStartedappliedProcedure`
- `...PotionDemonSlayerMarkPotionExpiresProcedure`
- `...PlayerAttackTimesProcedure`
- `...CalculateCooldownTimeProcedure`
- `...GetLevelProcedure`
- `...TestSwingItemProcedure`
- `...ActiveHashiraProcedure`
- `...ActiveRedSwordProcedure`
- `...PotionYorichiPotionStartedappliedProcedure`
- `...PotionYorichiOnPotionActiveTickProcedure`
- `...BreathesMizu10Procedure`
- `...BreathesNagiProcedure`
- `...BreathesHekirekiIssenProcedure`
- `...BreathesShiranuiProcedure`
- `...BreathesKasumi7AttackProcedure`
- `...BreathesHi13Procedure`
- `...BreathesIwa1Procedure`
- `...BreathesIwa5Procedure`
- `...BreathesTsuki16Procedure`

Advancement resources:

- `data/kimetsunoyaiba/advancements/demon_slayer_mark.json`
- `.../transparent_world.json`
- `.../breathing_20.json`
- `.../breathing_40.json`
- `.../breathing_60.json`
- `.../breathing_80.json`
- `.../breathing_100.json`
- `.../receive_20_damage.json`
- `.../receive_40_damage.json`
- `.../receive_60_damage.json`
- `.../receive_80_damage.json`
- `.../receive_100_damage.json`
- `.../crimson_red_nichirin_blade.json`
