# QB-MOD 1.6.4.082 — Attack telegraph / VFX / readability catalog

Date: 2026-10-07

Primary evidence:
- QB-MOD archive SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD archive SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

Purpose: separate **player-visible attack communication** from the underlying damage/AI systems.

The most useful lesson from this old MOD is not shader technology. It often turns combat state into visible world objects, model-state discontinuities, sound cues and environmental changes, so presentation and mechanics share the same state.

---

## 1. Mami — staged Musket array is both telegraph and ammunition

Source:
- `entity/passive/EntityMami.java:132-228,259-270`
- `client/renderer/RenderMusket.java`

When no nearby Musket token is available:

### middle range
- Mami places **4 EntityMusket** instances around herself;
- angular positions are sampled around a full 2π ring;
- they are placed near eye height;
- she announces `Danza del Magic Bullet!`.

### long range
- same pattern but **12 Muskets**.

On a later attack:
- `checkMusket()` searches within ±3;
- kills one visible Musket entity;
- a real Garnet bullet is immediately fired.

The visible Musket therefore communicates actual future attack stock. It is not decorative particle spam.

Renderer:
- uses a 32×32 RGBA Musket texture;
- renders as a simple two-sided flat plane;
- scales length more than width/height;
- arrow-shake can visibly wobble the prop.

### Reusable technique

**mechanical charge stock rendered directly in world space**

This is stronger than a separate charge bar because:
- spatial count is readable;
- stock can be destroyed/removed by the same state transition that fires;
- no duplicated “visual count” must be synchronized.

ANCHOR opportunity:
- preserve the world-prop stock contract;
- optionally animate deployment with a short outward/easing motion;
- keep server-authoritative stock count;
- avoid creating a heavyweight full Mob entity if an interaction-light projectile/display entity is sufficient.

---

## 2. Sayaka — deployed Cutlasses form a readable reserve

Source:
- `EntitySayaka.java:261-343`
- `RenderCutlass.java`

At long range, when no nearby Cutlass exists and pathing is idle:
- spawns **5 EntityCutlass** instances around Sayaka in angular positions;
- they remain as visible world entities.

Later:
- `checkCutlass(target)` removes one nearby Cutlass;
- constructs a new targeted Cutlass projectile;
- plays bow sound;
- launches it at the target.

This is the same deploy-now / consume-later idea as Mami, but with a different combat role.

### Readability value

A player can infer:
- whether Sayaka currently has ranged stock;
- how many conversions remain;
- that “floating weapon props” are not merely decoration.

This is an important design primitive for future KNEEKURA characters:
**telegraph by exposing internal attack resources physically**.

---

## 3. Homura teleport — source-to-destination trail and dual sound

Source:
- `EntityHomura.java:238-281`

A successful teleport emits:
- **128 portal particles** sampled along the line from old to new position;
- randomized small velocities;
- Enderman portal sound at the old coordinate;
- the same portal sound on Homura at the new coordinate.

This gives two simultaneous signals:
1. spatial trail communicating where she moved;
2. sound at both endpoints reinforcing disappearance/reappearance.

Technique:
**movement discontinuity visualized as a sampled transition path**, not only a particle burst at destination.

ANCHOR:
- fewer particles can achieve the same communication if a trail/ribbon particle is available;
- source and destination sounds should remain spatialized;
- movement must remain server-authoritative.

---

## 4. Homura vs Walpurgis — firework as attack vector cue

Source:
- `EntityHomura.java:337-386`

Normal long-range TNT:
- teleport;
- plant TNT at target-space coordinate;
- play `random.fuse`;
- TNT inherits target motion.

Against Walpurgisnacht:
- TNT fuse becomes 1;
- Homura also spawns a firework rocket at herself;
- rocket velocity is normalized toward Walpurgis;
- attack can repeat every tick across the special rapid sequence.

The firework is not the actual damage payload. It functions as **parallel presentation for a very fast explosive attack**.

Technique:
**damage object and readability object can be separate entities sharing one attack event**.

This is useful for modern spectacle:
- server can own a compact damage primitive;
- client-visible tracer/beam/firework can communicate direction without being the authoritative damage collider.

---

## 5. Magical-girl form transition — synchronized state, instant model/texture discontinuity

Source:
- `EntityMahoShojo.java:516-590`
- `RenderMahoShojo.java`
- character texture selectors

Form transitions emit:
- owner chat text:
  - `Transformation!`
  - `Revellion Time!`
  - `Ultimate Form!`
  - `Finish Transformation!`
- `random.click` sound at eye height;
- synchronized form byte changes;
- renderer then selects the form-specific model;
- texture selection changes independently from the same form state.

There is no large bespoke transform particle sequence in this snapshot. The dominant readability is an **instant silhouette/texture replacement plus text/sound cue**.

Technique:
**authoritative state transition drives presentation directly**, with no separate “transformation animation state” needed.

ANCHOR improvement:
- keep form state authoritative;
- add a short transition presentation state only if desired;
- never let a client animation determine when combat attributes actually change.

---

## 6. Soul Gem corruption warning — two-step particle escalation

Source:
- `EntityMahoShojo.java:165-175`

At corruption >=52:
- one red-dust particle stream is emitted around the body.

At >=58:
- a second, slightly wider/higher red-dust emission is added.

At >=64:
- witch transformation logic begins.

Thus the danger ladder is:

`no warning → local red warning → denser/wider warning → terminal transformation`.

Technique:
**resource threshold is communicated continuously on the actor before the terminal state**.

This is preferable to surprising the player with an untelegraphed corruption failure.

---

## 7. Grief Seed incubation — countdown density becomes the timer display

Source:
- `EntityGriefSeed.java:138-179`

Countdown starts/progresses only while a player is within 16 blocks.

Client presentation:
- countdown <1000 and divisible by 5 → periodic red-dust particle;
- countdown <500 → an additional red-dust particle every update;
- countdown <100 → another particle every update with randomized velocity.

The particle system is therefore effectively an **analog countdown UI**:
- sparse;
- dense;
- agitated immediately before hatch.

No numeric HUD is required.

Technique:
**hazard imminence encoded as VFX frequency/amplitude**.

ANCHOR can preserve the threshold semantics while replacing literal red-dust particles with a richer but still monotonic visual language.

---

## 8. Prickle — projectile becomes an embedded summoning telegraph

Source:
- `EntityPrickle.java:49-78`
- `RenderPrickle.java`

Prickle renderer:
- uses 16 planes rotated by 22.5°;
- overall cross-section scale is much larger than simple LightArrow/Cutlass planes;
- gives it a dense radial/spiky silhouette.

Behavior:
1. projectile is fired by Walpurgis;
2. it embeds in terrain;
3. remains there;
4. after >20 in-ground ticks, creates Shadow Puella Magi at its position;
5. spawned Shadow emits vanilla explosion particle;
6. Prickle disappears.

The embedded projectile is therefore a **one-second-ish physical spawn marker** at 20 TPS.

Technique:
**projectile lifecycle itself is the summoning telegraph**:
`incoming shot → visible embedded seed → delayed minion`.

This is a high-value boss primitive because the player can potentially read where future pressure will appear.

ANCHOR improvement:
- make the embedded phase visually distinct from the flying phase;
- add a growing pulse/ring during the 20-tick arm window if stronger counterplay is desired;
- keep encounter ownership for cleanup.

---

## 9. Light Arrow — cheap luminous projectile rather than heavy model

Source:
- `RenderLightArrow.java`

Renderer:
- aligns to projectile yaw/pitch;
- crossed-plane/quad geometry rather than a 3D model;
- translucent alpha 128;
- four side-plane rotations;
- brightness color oscillates with `sin((tickLight + partial)/2)`;
- uses projectile lightmap brightness.

This creates a pulsing magical projectile at very low geometry complexity.

Technique:
**low-poly billboard/plane projectile + luminance modulation**.

Modern relevance:
- excellent candidate for danmaku where hundreds of bullets may exist;
- collision simulation and visual representation can remain separate;
- a modern shader is optional rather than mandatory.

---

## 10. Fire Lance / Spear / Musket / Cutlass use silhouette-specific plane counts

Legacy projectile renderers do not all use one generic visual.

Examples:
- Musket / Cutlass: two-sided plane;
- Spear / Spear2: elongated two-sided plane, ~3× longitudinal scale;
- Fire Lance: six planes around the projectile at 60° steps;
- Prickle: sixteen planes at 22.5° steps;
- Light Arrow: central/end quads plus four rotated side planes.

This produces distinct cross-sections and perceived volume while reusing the same basic Tessellator approach.

Technique:
**projectile class readability through plane topology, not only texture color**.

For a future effects library, expose:
- axial length;
- radius;
- radial plane count;
- alpha/emissive;
- spin/pulse rate;
as data rather than writing one renderer class per projectile.

---

## 11. Charlotte — phase telegraph through a deliberate 10× scale discontinuity

Source:
- `RenderCharlotte.java:25-55`

First form:
- modelNormal;
- renderer scale 0.5×.

Second form:
- modelSecond;
- renderer scale 5×.

The scale ratio alone is **10×**, before considering the different model geometry.

Technique:
**boss phase transition communicates itself through silhouette + scale discontinuity**.

This is extremely readable and costs no particle budget.

The second-form entity state also changes world interaction/combat behavior, so the visual change is mechanically meaningful.

---

## 12. Walpurgis — encounter presentation is multi-layered

### 12.1 arrival announcement

Source `EntityWalpurgisnacht.java:200-225`.

When the actual spawn gate succeeds, every player receives:

`!!!! Walpurgis Night HAS COME !!!!`

The announcement occurs at encounter admission, not simply registry spawn declaration.

### 12.2 global storm/night ambience

Every 100 ticks server-side:
- rain time reset;
- thunder time reset;
- raining true;
- thundering true;
- overworld time forced to 23200.

This is technically invasive, but presentation-wise it makes the **world itself become the boss telegraph**.

Technique to preserve:
**encounter ambience layer**.

Implementation to replace:
global irreversible/shared world mutation.

### 12.3 continuously moving mechanical silhouette

`ModelWalpurgisnacht.setLivingAnimations`:
- arms sway on a low-frequency sine;
- multiple gear layers rotate continuously at different signed speeds.

The boss is visually alive even without an attack animation.

### 12.4 health-linked shaft angle

Entity:
`getShaftRotation() = -(health / maxHealth) * π`.

Renderer returns that value through `handleRotationFloat`, and ModelWalpurgisnacht uses the corresponding animation parameter to set Shaft rotation.

Therefore health is reflected in the boss's large mechanical silhouette, not only in the boss bar.

Technique:
**health value drives model pose directly**.

### 12.5 projectile identity

- Flame Lance and Prickle each play bow sound at fire time.
- Their render silhouettes differ substantially.
- attack timers are independent.

Weakness:
there is little explicit **pre-fire** wind-up in these methods; the sound and projectile appear at launch time.

ANCHOR improvement:
- keep independent weapon timers;
- add a short server-synchronized charge cue/pose for high-damage or minion-seeding volleys;
- do not rely solely on projectile emergence for dodge readability.

### 12.6 death celebration

On death:
- global player message `Congratulations!!!!!!!!`;
- during death updates, one randomly configured firework is spawned each update around the boss in a roughly 10-block area;
- firework color has two random dye colors;
- explosion type 0–2;
- Flicker and Trail randomized;
- Flight randomized.

Technique:
**boss death window is a timed presentation phase rather than one instantaneous particle burst**.

---

## 13. Companion command mode is visually coded

Garnet source:
`EntityGarnetTameable.changeMode()`.

Every mode setter:
- sends owner text;
- plays click sound.

Mode transition also emits one particle:
- Standby → Satellite: `happyVillager`;
- Standby/Satellite → Free: `note`;
- Free → Follow: `heart`;
- Follow/other → Standby: `spell`.

Technique:
**command state uses redundant feedback channels: text + sound + semantic particle**.

This is a good accessibility/readability pattern even though the exact 1.6.4 particle vocabulary is primitive.

---

## 14. Sayaka Ultimate — movement state leaves an environmental visual trace

Source:
`EntitySayaka.java:130-161`.

While Ultimate Form is flying:
- collision can destroy nearby non-protected blocks;
- a `note` particle is emitted around Sayaka each update.

This makes the special movement state continuously visible, separate from attack events.

Technique:
**persistent form aura tied to movement/state rather than a one-shot transform effect**.

---

## 15. Presentation taxonomy recovered

Independent primitives:

1. visible attack stock — Mami Musket / Sayaka Cutlass;
2. source-to-destination teleport trail;
3. parallel tracer/presentation entity — Homura firework;
4. form-driven model/texture discontinuity;
5. threshold-based corruption aura;
6. VFX-density countdown;
7. embedded projectile as delayed-spawn marker;
8. pulsing emissive-looking crossed-plane projectile;
9. radial-plane count as projectile silhouette language;
10. model+scale phase break;
11. world ambience as encounter layer;
12. health-driven model pose;
13. sustained death-celebration window;
14. text + sound + semantic particle command feedback;
15. persistent state aura.

Do not collapse these into one “special effects system.” They communicate different kinds of state.

---

## 16. Modernization rules for 1.20.1 Forge

### Preserve exactly at the design level
- state and presentation share one authoritative source;
- visible stock corresponds to real attack stock;
- escalation has monotonic visual language;
- summons have location/time telegraphs;
- boss phases have unmistakable silhouettes;
- damage simulation and cosmetic tracer may be separate.

### Rewrite implementation
- GL11/Tessellator → PoseStack / modern render types or chosen animation/effects framework;
- global weather/time changes → scoped/reversible encounter ambience;
- raw world entities for purely cosmetic effects → client visual entities/particles where possible;
- per-projectile renderer classes → data-driven visual profiles where semantics permit;
- boss-bar update through renderer → server BossEvent;
- network/form transitions remain server-authoritative.

### Recommended LAB observations
For each recovered attack, record:
- wind-up duration;
- first visible cue;
- cue-to-damage delay;
- projectile speed;
- active duration;
- screen/world occupancy;
- sound cue;
- counterplay window;
- spawned entity count;
- cleanup lifetime.

The static source can recover the mechanics, but exact perceived timing/readability should be verified in a bounded 1.6.4 runtime or recreated in the 1.20.1 LAB before calling the presentation equivalent.
