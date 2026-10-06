# QB-MOD 1.6.4.082 — Rebellion-era state machine and .080→.082 delta leads

Date: 2026-10-07

Primary implementation evidence:
- QB-MOD 1.6.4.082 archive SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`.

Historical/community material is reconnaissance only. Exact .080 code has not yet been recovered.

## 1. Rebellion is a first-class shared form

`EntityMahoShojo` uses synchronized form byte 20:

- 0 = Normal;
- 1 = transformed magical girl;
- 2 = Rebellion;
- 3 = Ultimate Form.

Rebellion is therefore not only a character-specific AI or renderer variant. It participates in the common form state machine.

`setRebellion()`:
- writes form = 2;
- reapplies character attributes;
- dismounts;
- clears path;
- emits owner chat text `Revellion Time!`;
- plays a click sound.

The legacy message spelling is preserved as implementation evidence; do not normalize it when matching logs/source.

## 2. Which characters can enter Rebellion

The base class enables Rebellion only when `getRebellionItemId() > 0`.

Confirmed 1.6.4.082 characters:

| Character | Trigger item | HP threshold | Dedicated Rebellion AI |
| --- | --- | ---: | --- |
| Homura | Madoka Ribbon | 12 | EntityHomuraAIRebellion |
| Sayaka | Sayaka Hair Clip | 8 (base default) | EntitySayakaAIRebellion |
| Kyouko | Kyouko Ribbon | 8 (base default) | EntityKyoukoAIRebellion |
| Madoka | none | — | no |
| Mami | none | — | no |
| Kirika | none | — | no |
| Yuri | none | — | no |

The form is therefore deliberately selective rather than universal.

## 3. Automatic trigger from the five-slot NPC inventory

While in ordinary transformed form, server-side:

1. entity must have an attack target;
2. character must support Rebellion;
3. internal inventory must contain its Rebellion item;
4. current HP must be <= character threshold;
5. item is consumed;
6. transform timer resets;
7. Rebellion begins.

This turns the visible five-slot inventory into a **conditional form-resource controller**:
- player can pre-load a transformation catalyst;
- NPC consumes it automatically only under combat/HP conditions.

Technique:
**inventory-resident catalyst + health threshold + combat presence → emergency alternate combat form**.

## 4. Manual trigger

Player interaction also contains a Rebellion branch:
- current form must be ordinary transformed;
- held item must equal the character's Rebellion item;
- health must satisfy the same threshold;
- item is consumed unless creative;
- `setRebellion()` is called.

The same transition therefore supports both:
- autonomous preparation through internal inventory;
- direct player intervention.

ANCHOR should keep one server-side transition rule and expose multiple validated request sources rather than duplicate conditions.

## 5. Rebellion lifetime / mode contract

Server living update while Rebellion:

- if there is no attack target, `transformTime++`;
- if tactical mode is not Free, force Free;
- otherwise, once `transformTime > 1000`, return to Normal.

At 20 TPS, 1000 idle ticks is roughly 50 seconds.

Important nuance:
- target presence does **not** decrement `transformTime`;
- unlike ordinary transformed form, Rebellion idle time can accumulate across multiple quiet windows during one Rebellion session.

So the actual invariant is closer to:
**cumulative no-target time budget**, not “50 seconds since last combat” and not “50 continuous idle seconds”.

This should be preserved or consciously redesigned on ANCHOR.

## 6. Ordinary transformation lifetime differs

Ordinary transformed form:

- no target → `transformTime++`;
- active target → if timer >0, `transformTime--`;
- timer >500 → return to Normal.

This is a bidirectional activity meter:
- idleness charges toward de-transformation;
- combat drains that accumulated idle budget.

Rebellion intentionally or accidentally uses a different one-way idle accumulator.

## 7. Ultimate Form lifetime differs again

Ultimate Form:

- no target → `transformTime++`;
- force fire immunity;
- force Follow mode;
- if Soul Gem corruption >0, cleanse by 1;
- only once those earlier conditions are settled and `transformTime >1500`, finish UF and kill the entity.

At 20 TPS, 1500 accumulated idle ticks is roughly 75 seconds.

Because target presence does not reduce `transformTime`, UF also uses cumulative no-target time.

The `else-if` chain means the finish check is reached only after:
- fire immunity is already established;
- Follow mode is established;
- Soul Gem corruption is zero.

Technique:
**form expiration gated behind state normalization and resource cleanup**, not merely a timer.

## 8. Character-specific Rebellion combat identity

### Homura

Rebellion:
- 3D flight;
- target pursuit perturbed by sine/cosine functions;
- velocity capped around 0.8;
- every 15 ticks with line-of-sight, emits 8 homing `EntityLightArrow2`;
- melee collision remains possible.

This is the MOD's strongest **oscillatory flight + homing volley** implementation.

### Sayaka

Rebellion:
- 3D flight pursuit;
- random target-vector offsets;
- additive distance-dependent motion;
- melee with random 3D knockback;
- extremely fast healing through Sayaka's form-dependent heal frequency.

### Kyouko

Rebellion:
- retains short/mid/long attack vocabulary;
- chooses band partly from navigator/path state;
- fills up to three Rosso Fantasma clone slots;
- clones are 1-HP expendable pressure units tied to Kyouko remaining in Rebellion.

Thus “Rebellion” is a common lifecycle state but **not a shared combat template**.

## 9. .080-era guide conflict: Homura UF

A contemporary guide explicitly tied to the 2013-11-04 1.6.4.080 update describes Homura Ultimate Form as:
- unable to use time magic;
- able to fly;
- continuously fires spread homing arrows.

In the supplied .082 source:

### EntityHomuraAIUltimate
- enables flight;
- looks at target;
- repeatedly uses direct melee;
- successful hits reduce current target HP toward 95%;
- after prolonged failure, target is forced to 1 HP + small explosion;
- after a longer threshold, target HP is set to 0.

### EntityHomuraAIRebellion
- enables flight;
- oscillatory movement;
- fires 8 homing LightArrow2 projectiles every 15 ticks.

Therefore the old guide's UF description resembles the .082 **Rebellion** combat implementation much more closely than the .082 Ultimate implementation.

Interpretation state: **strong version-delta hypothesis, not proven code history**.

Possible explanations:
1. post-.080 update moved/redesigned Homura's homing-flight behavior into the new Rebellion form;
2. the guide was not updated when behavior changed;
3. terminology in the guide lagged behind development.

Only recovery of .080 source/binary can distinguish these precisely.

## 10. Archive-member chronology around Rebellion content

ZIP member timestamps are not public release timestamps, but selected Java members show a concentrated late-December / early-January editing window:

| Source member | ZIP timestamp |
| --- | --- |
| EntitySayakaAIUltimate.java | 2013-12-23 21:46:12 |
| EntitySayakaAIRebellion.java | 2013-12-23 23:02:20 |
| EntityKyoukoAIRebellion.java | 2014-01-01 02:19:50 |
| EntityHomuraAIRebellion.java | 2014-01-03 20:57:14 |
| EntityHomuraAIUltimate.java | 2014-01-04 04:05:48 |
| EntityMahoShojo.java | 2014-01-03 17:46:42 |

The compiled class set is then heavily timestamped at 2014-01-04 15:04:38.

This is consistent with active Rebellion-era code work after the confirmed November .080 update.

Do not infer file creation date from texture timestamps: several Rebellion texture files carry much older timestamps, showing that archive-member times can reflect reused/edit-history metadata.

## 11. Homulilly / Nutcracker chronology in the same snapshot

Selected source timestamps:

| Source member | ZIP timestamp |
| --- | --- |
| EntityHomulillyAIAttack.java | 2013-12-29 11:10:00 |
| ModelHomulillyNutcracker.java | 2013-12-31 02:59:24 |
| Liese AI / model work | 2014-01-01 |
| Lilia / Lotte / Luiselotte / Clara model/servant work | 2014-01-02 |
| EntityHomulillyNutcracker.java | 2014-01-03 22:12:00 |
| EntityHomulilly.java | 2014-01-03 22:25:28 |
| Liese/Lilia/Luiselotte/Lotte/Clara entity source | 2014-01-03 evening |

This cluster is consistent with a large late development pass on the Rebellion/Homulilly ecosystem.

Again: archive timestamps support chronology inside this snapshot; they are not a substitute for a VCS history.

## 12. Player-facing confirmation that the new systems shipped

Later gameplay-index material documents:
- fighting Homulilly repeatedly;
- Homulilly producing many servants;
- distance/ranged combat being effective against Homulilly;
- a dedicated “research” episode sending magical girls in **Reb state** against Homulilly;
- Oktavia battles with large numbers of Wheel hazards.

These reports align with the .082 source architecture:
- Homulilly/Nutcracker family ecosystem;
- Rebellion state;
- Oktavia Wheel spawning.

They materially reduce the chance that these major systems are merely unreachable/dead source, while still remaining secondary behavior evidence.

## 13. ANCHOR lesson

Preserve two levels separately:

### Common form lifecycle
- eligibility;
- catalyst;
- threshold;
- synchronized form state;
- tactical mode contract;
- lifetime/exit policy.

### Character combat package
- movement controller;
- attack primitives;
- summons/clones;
- attributes/healing;
- presentation.

Do **not** implement Rebellion as one universal AI. The legacy design itself already demonstrates that the useful abstraction is a shared lifecycle with heterogeneous combat composition.
