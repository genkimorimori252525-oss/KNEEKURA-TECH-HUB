# P2 — Red Homing Amulet exact X1 contract

Evidence:
canonical X1 archive SHA-256
`6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`.

## Item fire contract

Source: `sources/java/thKaguyaMod/item/ItemHomingAmulet.java`.

Normal red:
- `ShotData.shot(FORM_AMULET, RED, 0.4F, 5.0F, 0, 90, HOMING01)`
- first/limit speed 0.7
- acceleration 0
- gravity zero
- 5-way
- total wide angle 100°
- spawn distance 0.5
- base angle 0

Shift/focus red:
- `ShotData.shot(FORM_AMULET, RED, 1.0F, 8.0F, 0, 90, HOMING01)`
- first/limit speed 0.7
- acceleration 0
- gravity zero
- 2-way
- total wide angle 20°
- spawn distance 0.5
- base angle 0

Numeric constants:
- `FORM_AMULET = 27`
- `RED = 0`
- `HOMING01 = 10`

## Exact fan geometry

Source: `THShotLib.createWideShot`.

Algorithm:
1. normalize/look vector supplied by player;
2. derive legacy yaw/pitch;
3. build a rotation axis with `getVecFromAngle(-yaw, -pitch + 90)`;
4. start at `-wideAngle / 2 + baseAngle`;
5. increment by `wideAngle / (way - 1)`;
6. rotate aim vector around the axis with the legacy Rodrigues matrix;
7. spawn at `origin + direction * distance`.

For a level +Z aim:
- normal offsets: `-50,-25,0,+25,+50` degrees;
- focused offsets: `-10,+10` degrees.

The X direction sign follows the legacy rotation-axis convention; P2 regression locks this.

## Homing behavior

Source: `EntityHomingAmulet.specialMotion`.

Red Homing Amulet:
- searches an approximately 24-block expanded local volume;
- only living entities are candidates;
- excludes animals, villagers, source, user and dead targets;
- rejects targets blocked by the legacy ray trace;
- target ranking is not pure nearest-distance:
  `distance * halfAbsSin(angleSpanRadians)`;
- selected target direction is compared against current shot vector;
- turn magnitude is clamped to ±4° per tick;
- turn axis is the cross product of current and target direction;
- server updates motion/angle after steering.

## Logical size vs visual size

The ShotData `size` is applied to `Entity.setSize(size,size)` and collision checks.

Therefore:
- normal logical/hit size: 0.4;
- focused logical/hit size: 1.0.

But `RenderHomingAmulet` does **not** use that logical size for the red visual.

Red visual:
- first-pass scale: 0.5;
- same scale for normal and focused red shots.

This distinction is required to avoid incorrectly rendering the focused red shot 2.5× larger.

## Exact visual contract

Source:
`sources/java/thKaguyaMod/client/render/shot/RenderHomingAmulet.java`.

Shot texture:
- source path: `assets/thkaguyamod/textures/shot/HomingAmulet.png`
- 64×32 indexed PNG
- SHA-256:
  `badfeba690c2dee69ddb38c9f3a0fe538643ca1d439121e95959fd7dfb93b4d9`

Item icon:
- source path: `assets/thkaguyamod/textures/items/homingAmulet.png`
- 32×32 indexed PNG
- SHA-256:
  `650f71239534ef521bea3e1e29893ed1cb8302721854c44d0536b76be02f5773`

Renderer:
- uses only the left half of the 64×32 shot texture: U 0..0.5, V 0..1;
- disables lighting;
- enables blending;
- disables culling;
- blend factors: `ONE / ONE_MINUS_SRC_COLOR`;
- rotates X by `-rotationPitch`;
- rotates Y by `180 - animationCount*23`;
- draws one untinted quad at 0.5 scale for red;
- then multiplies the matrix again by 0.55 and draws a red tint:
  `(255,25,25,0.6)`;
- effective second-pass scale relative to unscaled quad is 0.275.

## Asset handling

The original PNG bytes are available again from the verified historical Drive bundle, but are **not committed to the public TECH-HUB repository**.

P2 live implementation should use a private/local asset-import helper that verifies the canonical archive SHA and texture SHA before copying the PNG into a local resource overlay.
