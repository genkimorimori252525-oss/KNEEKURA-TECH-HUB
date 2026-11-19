# NON-SPELL COMBAT ATLAS — 五つの難題MOD+ X1

Status: **ORIGINAL_SOURCE / ORIGINAL_BINARY static analysis; runtime NOT_RUN**

Scope: combat/visual mechanics that are not implemented primarily by an active `THSpellCard.spellcard_main()` timeline.

This includes weapon skills, charge entities, projectile controllers, defense/counter tools, time manipulation, portals and item-hosted attacks.

## Evidence boundary

- X1 bundled `sources/java/` and distributed class inventory are implementation authority.
- Bundled manual pages are period context only.
- Some items call `checkSpellCardDeclaration`; if the actual attack is item/entity-hosted, it is documented here and not attributed to an empty spell-card class.
- Static trajectory/effect descriptions are source-backed. Runtime feel remains NOT_RUN.

---

## 1. 楼観剣 — Roukanken

**Type:** melee / charge mobility / bullet CUT

### Charge movement

Right-use stores bow-like charge. On release while grounded, forward horizontal speed scales up to about **6.0**.

During sufficiently fast movement, the sword scans the swept movement volume.

### Living target effect

- ordinary living target: **8 damage**
- undead: **16 damage**

Direct melee also has an undead-specific extra-damage path.

### Bullet interaction

Non-laser `EntityTHShot` can be cut.

The original bullet dies and the cut point emits **three small white fragments** using the original shot form and reduced size.

**Interaction verb:** `CUT = destroy hostile bullet -> visual fragments`

Lasers are explicitly excluded.

---

## 2. 白楼剣 — Hakurouken

**Type:** counter / bullet REFLECT / mobility brake

### Reflect stance

Crouch-use creates `EntityHakurouReflecter` for about **20 ticks**.

A hostile non-laser `EntityTHShot` crossing the plane is:

1. consumed;
2. replaced with a player-owned AQUA SCALE shot;
3. relaunched along the reflector-facing direction.

Reflected shot profile:

- damage: **3**
- first speed: **0.3**
- limit speed: **0.7**
- acceleration: **0.05**

Lasers are not reflectable.

### Ground brake / reversal

Normal use while moving on the ground applies about **1.5** counter-impulse against current horizontal motion.

**Interaction verb:** `REFLECT = hostile bullet -> owned countershot`

---

## 3. 楼観旋風刃 — Roukan Senpuuzin

**Type:** passive proximity slash

While held, a roughly **1.5-block expanded** region is scanned for living targets.

- ordinary: **8**
- undead: **16**

The source still contains a bullet-cut block resembling Roukanken, but that entire block is commented out.

**X1 boundary:** active behavior is auto-slash; automatic bullet cutting is dormant code.

---

## 4. 龍の頸の玉 — Dragon Neck Jewel

**Type:** impact cluster / laser bloom

Normal use launches one jewel. Sneaking launches a **five-angle fan**.

On impact, the jewel becomes a small fireworks-like battle effect:

- **5 LaserA rays**, spaced by **72 degrees**, using five colors;
- **10 randomized upward light shots** with small gravity/velocity variation.

This is a reusable **single carrier -> mixed laser/projectile bloom** design.

---

## 5. 蓬莱の玉の枝 — Hourai Jeweled Branch

**Type:** charge-scaled rainbow shell

Charge determines the effective way count, roughly **10–24** after the internal division.

### Normal release

Three rainbow pearl ring layers around the aim axis:

- full way count;
- half count;
- one-third count.

Shots begin around **0.6** and accelerate toward **2.0**.

### Sneak release

Builds repeated full-circle layers with different speeds, creating a multi-velocity all-around shell.

The weapon changes **topology and density with charge**, not merely damage.

---

## 6. ホーミングアミュレット / 拡散アミュレット

### Homing variant

Fast mode:

- 5 shots;
- 100-degree wide spread;
- red amulets.

Focused/sneak mode:

- 2 shots;
- 20-degree spread;
- larger/higher-damage amulets.

`HOMING01` performs about **4 degrees/tick** bounded steering.

### Diffusion variant

Two blue carriers decelerate from **0.5** toward zero.

At end of life each carrier becomes three sphere layers:

- 20 shots at 0.6;
- 16 shots at 0.4 -> 0.6;
- 8 shots at 0.2 -> 0.6.

A small gravity vector derives from the user's look direction.

**Pattern:** `carrier -> timed spherical diffusion`

---

## 7. 博麗のお祓い棒 + 陰陽玉

**Type:** held growth / pinball projectile

Right-use creates `EntityOnmyoudama` in front of the user.

While use is held:

- projectile remains attached to aim;
- size grows from about **0.3** to **3.0**.

On release:

- launch speed becomes about **0.5**;
- shot damage becomes **size × 6**.

Entity collision reverses heading and retains about **80%** of motion.

It is permitted to become dangerous to the user after a short grace and carries return/bounce semantics.

**Pattern:** `hold and grow -> release -> large ricochet projectile`

---

## 8. 早苗のお祓い棒

**Type:** quick wind attack / long ritual charge

### Quick release (<30 ticks)

Creates `EntitySanaeWind`.

- damage scales with player experience;
- endurance scales with experience and clamps to roughly 15–120;
- uses `WIND01`.

The projectile's trajectory is coupled to the user's actual movement. Sneaking can force downward gravity behavior.

### Long hold

`EntityMiracleCircle` renders chained pentagram stages. Every ~30 ticks a new stage can be produced.

Hold time + player level can charge Miracle Fruit / Fafurotskies / Youryoku Spoiler / Moses Miracle / Yasaka no Kamikaze spell-card items and repair the rod.

This is a strong example of **visible ritual telegraph -> resource unlock**.

---

## 9. エイジャの赤石

**Type:** environment-charge laser

A front-attached `EntityAjaRedStoneEffect` samples actual **block light value** every tick and accumulates it.

When use ends:

`damage = floor(accumulatedLight / 40)`, capped at **30**.

Laser parameters derive from the stored damage:

- width = damage × 0.01;
- length = damage × 0.3;
- damage = stored damage;
- lifetime = 60.

Against undead:

- target is ignited;
- `damageRate` doubles;
- smoke/fizz effects spawn.

**Pattern:** `environmental light -> stored power -> beam geometry + damage`

---

## 10. ミニ八卦炉

**Type:** independent beam controller / Master Spark

Using the item creates `EntityMiniHakkero`, which in turn creates a persistent `LaserB`.

Non-spell item route:

- width: **4.2**
- length: **40**
- damage: **8**
- delay: **30**
- lifetime: **120**
- special: `EXPLOSION01`

The controller remains a separate entity and later returns the item.

`EXPLOSION01` gives the beam explosive impact semantics.

**Pattern:** `item input -> controller entity -> persistent beam entity`

---

## 11. 核制御棒 — Nuclear Control Rod

**Type:** held growing projectile / recoil / explosion risk

A `EntityNuclearShot` remains in front of the player while charging.

While held:

- follows current aim;
- size grows from about **0.3** toward **6.0**;
- damage continuously becomes **size × 8**.

If the user switches away from the rod before release, the projectile **explodes at its current size**.

On release:

- projectile becomes free;
- acceleration becomes **0.2**;
- the user receives recoil opposite aim, up to about **4.0**.

When colliding with hostile THShots, the two projectiles subtract each other's shotDamage instead of merely using a binary cancel.

**Pattern:** `visible growing charge -> launch + recoil`

---

## 12. 幽香の日傘 — Yuuka Parasol

**Type:** radial flower danmaku / melee knockback / mobility stance

### Charged release

Outer layer:

- **45** red/yellow SCALE shots;
- radial horizontal component;
- upward component;
- light downward gravity.

Inner layer:

- roughly **11** shots;
- smaller radius/vertical profile.

`SPECIAL_FLOWER_LAND` can place matching flowers when shots hit grass.

### Melee

Target receives strong directional knockback plus **7 damage**.

### Deployed parasol

Sneak-use can create a persistent `EntityYuukaParasol` attached to the player. Its modes modify movement, including fall suppression/slow-fall behavior.

The weapon unifies **danmaku, world painting and movement stance**.

---

## 13. 幽々子の扇 — Yuyuko Fan

**Type:** butterfly danmaku / rare execute

Normal release creates two mirrored accelerating butterfly fans.

Sneak release creates several circular speed layers with opposite offsets/colors.

Melee special:

if target has less than 20 HP and the hit-state condition is satisfied, there is a **5%** chance to:

- heal the user by target's remaining health;
- deal **4444** damage to target.

---

## 14. 天狗の団扇 — Tengu Fan

**Type:** charged wind projectile

Release creates one AQUA `FORM_WIND` shot using `WIND01`.

Speed scales with hold time, reaching roughly **3.43** at its cap.

`WIND01`:

- applies large motion impulse;
- adds strong upward lift;
- doubles damage when target is already airborne.

The real threat is **position displacement**, not only HP loss.

---

## 15. 魂魄の松明 / Soul Torch

**Type:** persistent seeker

Use creates **3** purple PHANTOM shots.

- initial speed: 0.01
- limit: 0.4
- acceleration: 0.03
- lifetime: 480

Every tick `SPECIAL_SOULTORCH` calls `homing(16°)`, far stronger than normal homing amulets.

Its special block-hit handler prevents ordinary deletion.

**Pattern:** long-lived, high-turn-rate pursuit projectiles.

---

## 16. 銀のナイフ — Silver Knife

**Type:** physical projectile / time-aware trail weapon

Unlike generic THShots, knives are physical long-lived entities that can stick.

Common behavior:

- initial velocity from player's look;
- damping and gravity;
- can remain embedded for very long periods;
- time-stop-aware restoration avoids unintended motion advancement while stopped.

Color-specific state is important.

Green knives can create **white delayed knife traces** along their flight path.

White knives begin with a **-30 tick delay** and are deleted after wall contact.

The knife system therefore supports **material projectile persistence + delayed temporal trails**.

---

## 17. レーヴァテイン — Laevateinn

**Type:** melee fire + attached beam blade

Melee sets the target on fire.

Right-use creates attached red `LaserB`:

- width 0.6
- length 20.8
- damage 7
- lifetime 30
- special FIRE

Normal vs sneak use changes the blade orientation, producing horizontal/vertical beam-sword presentation.

---

## 18. 神槍「スピア・ザ・グングニル」 item-hosted attack

The item performs spell declaration check for **ID27**, but the active registered `THSC_Spear_the_Gungnir` class has no `spellcard_main()`.

The actual attack is created by the item:

- `LaserA`
- GUNGNIR laser type
- red
- width 1.0
- length 10
- damage 14
- lifetime 120
- special `GUNGNIR`

The special rotates/grows the beam and emits secondary rings.

**Boundary lesson:** spell declaration does not imply spell-card class owns the effect.

---

## 19. 緋想の剣 — item-hosted 「全人類の緋想天」

The item checks spell declaration **ID7**.

It spawns:

- one main `EntityHisou` with num=8;
- seven afterimage entities.

The main entity follows the player for about **100 ticks** and once per tick emits a narrow randomized set of red `FORM_KISHITU` shots with `SPECIAL_HISOUTEN01`.

The afterimages carry the sword presentation while the main entity owns the repeating bullet source.

This is why the registered ID7 spell-card class can be behavior-empty while the visible technique still exists.

---

## 20. 霊撃札 — Spiritual Strike Talisman

**Type:** expanding purge + repulsion

The effect lasts only a few ticks, but its effective radius grows by **4 blocks per tick**.

Within radius:

- hostile living entities are pushed radially outward and upward;
- force scales with remaining radius-distance margin;
- animals/villagers are excluded from the hostile knockback condition;
- `EntityTHShot` receives `shotFinishBonus()`.

**Interaction verb:** `PURGE = area clear bullets + repel enemies`

---

## 21. 咲夜の懐中時計 / ストップウォッチ

**Type:** time-domain manipulation

### Sakuya Watch

Creates a **40-block** control field.

Modes include:

- full stop;
- half speed;
- spell-card stop;
- bounded full stop: about **100 ticks**;
- bounded half speed: about **160 ticks**.

Spell-card stop ends around **60 ticks**.

Persistent noncreative full-stop/half-speed modes consume exhaustion.

Implementation is state rollback/compensation per entity, not scheduler suspension.

### StopWatch

A disposable short time stop lasting about **40 ticks**, also over a 40-block field.

### Exception contract

`EntitySpellCard.canMoveInTimeStop` + `specialProcessInTimeStop()` allow selected spell behavior to progress during stopped time.

---

## 22. 呪いのデコイ人形

**Type:** aggro field

Creates a stationary 40HP `EntityCursedDecoyDoll`.

- lifetime up to ~180 ticks;
- scans a 40-block area;
- redirects creature attack/revenge targets to the doll.

This is battlefield control through **AI-target mutation**, not direct damage.

---

## 23. 神子の宝剣

**Type:** information visualization

Charge release determines scan radius up to **50 blocks**.

It selects the nearest **10 living entities**.

For each:

- spawns a colored `EntityDivineSpirit` at eye position;
- color depends on entity category/attribute;
- reports direction, vertical relation and distance to the player.

Divine spirits last up to about **300 ticks** and themselves orient/move toward nearby players.

The weapon creates **combat information as visible world entities**.

---

## 24. スキマ / Gap

**Type:** actor teleport + bullet trajectory redirect

Portal pairs can teleport actors.

For `EntityTHShot`:

- position changes to exit;
- speed magnitude is preserved;
- heading is recomputed from portal entrance/exit angle relation;
- shot's cached motion is updated.

Therefore existing danmaku can be routed through portal geometry.

**Interaction verb:** `REDIRECT = preserve bullet identity/speed, change position + heading`

Direct warp portals are short-lived (~24 ticks).

---

## 25. 金閣寺の一枚天井

**Type:** physical falling attack

The item launches a large ceiling entity upward:

- normal vertical power: about 0.7;
- sneak: about 1.0.

When falling onto another entity, damage scales with downward movement:

`damage ≈ int(yMove × 40) + 2`

The world-object trajectory itself is the weapon.

---

## 26. 死神の鎌 — Death Scythe

**Type:** ray-selected push/pull

Uses a roughly **16-block** view ray to pick a target.

It then adds or subtracts about **0.6 × look vector** from target motion depending on mode/sneak state.

This is direct kinematic battlefield control without a projectile.

---

## 27. 悔悟の棒 — Remorse Rod

**Type:** threshold HP rewrite

When active and target is above 75% max health:

- target HP is set directly to **75%**;
- rod becomes spent.

Black dye re-inks/reactivates it.

Glow indicates active state.

---

## 28. 火鼠の皮衣

**Type:** fire-state manipulation

- melee ignites target for **20 seconds**;
- right use extinguishes user;
- armor tick continuously extinguishes wearer;
- carries Fire Protection V.

---

## 29. 御柱

**Type:** heavy melee weapon

Melee adds random **5–22** damage.

Every inventory tick:

- horizontal player motion ×0.9;
- positive vertical motion ×0.9.

The item models weight as an always-on mobility penalty.

---

## 30. 毘沙門天の宝塔 — Houtou

**X1 status: apparent attack is dormant**

The class contains substantial historical laser/homing code, but those paths are commented out.

Live `onItemRightClick`:

- computes some vectors/locals;
- has `shot = null`;
- never spawns the commented laser/amulet effects;
- plays a sound.

Do not describe it as an active laser weapon for this X1 artifact.

---

## 31. Additional mobility / utility effects

### Marisa Broom

Creates a rideable broom entity with client input-driven 3D movement. This is primarily mobility, not danmaku.

### Kappa Cap

Armor movement effect can multiply motion in water and clamps maximum speed; durability reacts to water use.

### Wall-pass / Gap Folding Umbrella

Teleport/mobility items manipulate player position/portal entities rather than projectile damage. They are kept as movement technology, not counted as bullet attacks.

---

# Cross-item pattern summary

The strongest non-spell pattern families are:

1. **charge object becomes projectile** — Onmyoudama, NuclearShot;
2. **charge object produces another effect** — AjaRedStoneEffect -> LaserA;
3. **controller + beam** — MiniHakkero -> LaserB;
4. **carrier -> child bloom** — Dragon Neck Jewel, Diffusion Amulet;
5. **bullet defense/counter** — Roukanken, Hakurouken, Spiritual Strike;
6. **trajectory manipulation** — Sukima;
7. **world-state manipulation** — time stop, decoy aggro;
8. **environment-driven power** — ambient light, falling velocity;
9. **physical persistent projectile** — Silver Knife, Kinkakuji;
10. **visual combat information** — Miko Sword + Divine Spirits.
