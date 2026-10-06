# QB-MOD 1.6.4.082 — Model animation / state-readability analysis

Date: 2026-10-07

Primary evidence: supplied QB-MOD archive SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`.

The legacy renderer has no modern animation controller, keyframe timeline or shader graph. Instead, many models compute pose directly from:
- entity age/ticks;
- walk phase;
- head yaw/pitch;
- synchronized combat/form state;
- boss health.

That makes the model code valuable as a **state-to-pose mapping catalogue**.

## 1. Walpurgisnacht — persistent mechanical motion

`ModelWalpurgisnacht.setLivingAnimations` uses entity age:

- arm sway:
  `sin(age * 0.015) * 0.3`;
- secondary oscillation:
  `sin(age * 0.02) * 0.1`;
- four gear layers rotate continuously with different signed rates:
  - +0.0035π × age;
  - -0.0043π × age;
  - +0.005π × age;
  - +0.003π × age.

The silhouette therefore never becomes fully static even when the boss is not attacking.

### Health-linked shaft pose

`EntityWalpurgisnacht.getShaftRotation()` returns a value derived from health ratio.

`RenderWalpurgisnacht.handleRotationFloat` forwards it into the model.

The model then drives Shaft Z rotation from that value and adds a small age oscillation outside a bounded angle window.

Technique:
**boss health is encoded directly into a large model-part pose**, separate from the boss bar.

Modern reconstruction should preserve the semantic mapping:
`health / phase → major silhouette parameter`,
not the literal old RenderLiving parameter plumbing.

## 2. Homulilly — layered idle motion

`ModelHomulilly`:
- rotates the top hat continuously with age;
- wings oscillate from `sin(age * 0.08) * 0.1`;
- robe panels, hair segments and fingers derive multiple secondary motions from the same small oscillator;
- chained finger segments use squared oscillator terms for different response curves.

Technique:
**one low-frequency driver fans out through a hierarchy with different gains/signs**, producing coherent idle motion cheaply.

This is a useful alternative to independent random animation on every appendage.

## 3. Homulilly Nutcracker — synchronized combat state changes model behavior

Server entity:
- DataWatcher 18 stores `Fighting`;
- after a 100-tick timer, presence of an attack target toggles Fighting true;
- absence of a target later toggles it false;
- state also changes movement/fall handling and expands vertical collision destruction.

At nominal 20 TPS, this is roughly a **5-second delayed combat-state transition**.

Model:
- continuously animates hair and finger joints;
- when `getFighting() == false`, left/right ribbon chains sway with independent sine frequencies;
- when `getFighting() == true`, ribbon segments instead become functions of entity head yaw/pitch with piecewise yaw ranges.

This means Fighting changes both:
1. simulation behavior;
2. the visual relationship between head aim and ribbon posture.

Technique:
**one synchronized combat-phase bit drives mechanics and a distinct silhouette language**.

That is stronger than playing an unrelated client-only combat animation.

## 4. Charlotte second form — chained body follows head direction

`ModelCharlotte2`:
- head follows pitch/yaw;
- body segment 2 bends opposite the head at ~50%;
- middle segments receive ~20% of swapped head-axis contribution plus idle sine;
- later segments bend in opposite directions at ~30%.

Technique:
**head-look values propagate down a segmented body with attenuated/opposed transforms**.

This creates snake/worm-like follow-through without a dedicated inverse-kinematics system.

## 5. Oktavia — idle and locomotion are blended mathematically

`ModelOktavia` constructs tail motion as:

`idleCos * (1 - limbSwingAmount) + walkCos * limbSwingAmount`.

So:
- when stationary, slow age-based oscillation dominates;
- as locomotion amplitude increases, walk-cycle motion replaces it.

The result then drives:
- multiple tail segments with different gains/signs;
- cape/mantle pitch through `abs(var3)`;
- secondary arm-chain motion from another slow oscillator.

Technique:
**analytic idle↔locomotion blend using movement amplitude as interpolation weight**.

This is conceptually similar to a modern animation blend tree.

## 6. Wheel — animation speed is directly age-driven

`ModelWheel.main.rotateAngleX = ageInTicks * 0.1`.

The kinetic hazard is therefore visually identified by constant spin regardless of pathfinding limb cycle.

Technique:
**projectile-like Mob uses absolute age rotation rather than walk animation**.

## 7. QB/JB — command/movement state changes full posture

`ModelQB` / `ModelJB` keep an internal pose selector.

Living animation reads entity state:
- sneaking;
- sprinting;
- Standby mode;
- default movement.

Examples:
- Standby changes body angle, head/tail anchor positions and folds the legs;
- Sprinting lifts/aligns tail and uses a distinct gait branch;
- Sneaking shifts body/head anchor points.

This is a direct example of:
**companion command state → recognizable whole-body pose**.

The Standby mode is therefore communicated by both particles/text from the control system and the animal's posture itself.

## 8. Familiar idle vocabulary

Several minor models use related low-cost motion primitives:

- Anthony / Adelbert:
  - wing/ear/head appendages oscillate with slow sine;
  - locomotion uses cosine limb cycles.
- Gertrud:
  - multiple leg segments combine walk cosine with several slower age sine frequencies.
- Pyotr:
  - ear/tail oscillation tied to age and locomotion.
- Corno Forte:
  - ears use idle sine;
  - four legs use paired cosine gait;
  - tail is derived from squared cosine, producing a different waveform.
- Yuri:
  - twin tails move from slow sine;
  - Yuri MS additionally keeps the left arm in an aimed-gun pose and couples a spoon/skirt part to leg motion.
- Sayaka MS:
  - cloak pitch combines `abs(walk cosine)` with slow idle sine.

Technique:
**small shared trigonometric vocabulary, recombined per silhouette**.

## 9. Form/state renderer boundaries

`RenderMahoShojo`:
- Normal → normal model;
- transformed → MS model;
- Rebellion → Rebellion model;
- Ultimate → UF model;
- independent posture bit → `aimedBow`.

`RenderCharlotte`:
- second-form bit changes both model and scale;
- first form = 0.5×;
- second form = 5×.

So the legacy presentation stack already separates:
- form/phase selection;
- continuous pose;
- weapon posture;
- scale.

Modern animation should keep those four responsibilities distinct.

## 10. Modern reusable primitives

Keep independently:

1. age-driven ambient oscillation;
2. multi-rate mechanical gear rotation;
3. health-driven major pose;
4. one oscillator distributed through a model hierarchy;
5. combat-phase bit changing pose family;
6. head-aim propagated down chained body segments;
7. idle/walk analytic blend using movement amplitude;
8. absolute-age spin for kinetic hazards;
9. command mode → full-body posture;
10. form → model family;
11. posture → weapon pose;
12. phase → model + scale discontinuity.

For 1.20.1 these can be represented through a modern animation library, custom model math or state machines. The important recovered technology is **which gameplay state should be legible in the silhouette**, not the legacy GL/ModelBase API.