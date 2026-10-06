# Five Difficulties X1 Preservation Port — P4 Sakuya Watch / StopWatch exact item & visual contract

Date: 2026-10-07

Canonical X1 archive:
`SHA-256 6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`

## Primary source receipts

| Source | SHA-256 |
| --- | --- |
| `sources/java/thKaguyaMod/item/ItemSakuyaWatch.java` | `6e4b88a6ec59134e4de46218edfbea77c05d2d46e0c3961e35e41e0ac121b185` |
| `sources/java/thKaguyaMod/item/ItemSakuyaStopWatch.java` | `d16ef5bd2be35eabc8cbe8321c37ba8085c6049bc3025c87467b88b9756ea5f8` |
| `sources/java/thKaguyaMod/entity/item/EntitySakuyaWatch.java` | `738964897deeb1b2ee30767e032d13274f142825693f5e1995b89d88d3aaac01` |
| `sources/java/thKaguyaMod/entity/item/EntitySakuyaStopWatch.java` | `ac43880e034654931f4c7ccc9ee9e3170ce57792b8306a664ea22f8f55ebed49` |
| `sources/java/thKaguyaMod/client/render/RenderPrivateSquare.java` | `4aa2615f354ec31932abdd09a2abf95f955748106ab7483c30377ddd6563732f` |
| `sources/java/thKaguyaMod/client/render/RenderSakuyaStopWatch.java` | `89765e36eb02bd54407f76a48d885858ac038b892e1dcc95f1ffb7a87ee1ef08` |
| `sources/java/thKaguyaMod/client/model/ModelPrivateSquare.java` | `ff27b64ad25216eb8725f5c8cf2d3cfcb6841b988b8276be090a3b882720a9f9` |

## Watch item UX

`ItemSakuyaWatch`:
- stack size 1;
- old creative tab: Misc;
- texture key: `thkaguyamod:sakuyaWatch`;
- metadata/damage 0 = HALF mode;
- metadata/damage 1 = FULL STOP mode;
- metadata 1 glints; metadata 0 does not.

### Sneak-right-click mode toggle

Before activation, if:
- player is sneaking;
- `player.ticksExisted % 2 == 0`;

then item damage toggles:
- 0 → 1;
- 1 → 0;

and no field is spawned.

The tick parity is a debounce artifact from the old item implementation.

### Charge / activation

Max use duration:
- mode 0 HALF: 20 ticks;
- mode 1 FULL STOP: 48 ticks.

Use animation:
- bow action.

Creative player:
- non-sneak right-click activates immediately;
- mode 0 → persistent `TIME_HALF`;
- mode 1 → persistent `TIME_STOP`;
- item is not consumed.

Survival:
- food level must be >0;
- full charge is required;
- mode 0 → `TIME_HALF_WITH_LIMIT`;
- mode 1 → `TIME_STOP_WITH_LIMIT`;
- one Watch item is consumed on successful field creation.

Incomplete charge:
- no time field;
- source contains a second mode-toggle branch if the player is sneaking, but ordinary initial sneak-right-click already returns before starting use.

## Watch item return lifecycle

`EntitySakuyaWatch` finishes through `THKaguyaLib.itemEffectFinish(..., sakuya_watch)` for normal Watch modes.

For a non-creative player:
- one Watch is returned to inventory;
- if inventory insert fails, it is dropped at controller position.

Critical X1 detail:
- this overload does **not** pass a damage value;
- returned Watch is metadata/damage **0**.

Therefore using a survival FULL STOP Watch (metadata 1) and finishing it returns a Watch reset to **HALF mode**.

Creative player:
- controller simply disappears;
- no duplicate item is returned because the Watch was never consumed.

Spell-card Watch:
- does not return an item.

StopWatch:
- does not return itself after use.

## Watch duplicate precheck

Before spawning Watch:
- search an AABB expanded by 20 blocks around the player;
- if any `EntitySakuyaWatch` exists, activation fails.

StopWatch precheck:
- rejects when either Watch or StopWatch exists inside the same 20-block AABB.

After creation, P3's 40-block controller-overlap rule resolves broader conflicts.

## StopWatch item UX

`ItemSakuyaStopWatch`:
- stack size 1;
- old creative tab: Misc;
- texture key: `thkaguyamod:SakuyaStopWatch`;
- immediate right-click activation;
- no charge;
- full-stop field;
- non-creative consumes one item;
- creative does not consume;
- no return lifecycle.

## Controller model

Watch and StopWatch use the same `ModelPrivateSquare`.

Legacy model texture size: 64×32.

Parts:

### watchBase
- texture offset: (0,0)
- box: (-6,-6,-2)
- dimensions: 12×12×4

### watchCenter
- texture offset: (28,14)
- box: (-8,-8,-1)
- dimensions: 16×16×2

### watchHandle
- texture offset: (32,0)
- box: (-4,8,0)
- dimensions: 8×6×0

### watchCover
- texture offset: (48,16)
- box: (-8,-8,0)
- dimensions: 16×16×0
- rotation point: (0,-16,-4)
- X rotation: π/6

Renderer applies:
- global scale 0.3;
- Y rotation `180 - renderYaw + ticksExisted*7`;
- model render scale 0.0625.

Watch/StopWatch differ by controller texture, not model geometry.

## Controller textures

### Watch item icon
- path: `assets/thkaguyamod/textures/items/sakuyaWatch.png`
- 16×16 indexed PNG
- SHA-256:
  `589e080353f2f1d56ec6af6547bc3cfbb3802de89e7797c03a2251083e8d0c8e`

### Watch controller
- path: `assets/thkaguyamod/textures/SakuyaWatchTexture.png`
- 64×32 indexed PNG
- SHA-256:
  `b55d8af1138f2b7f5e3841afe7d5aecff78d57122f57ecb7a29af1036f76ff30`

### StopWatch item icon
- path: `assets/thkaguyamod/textures/items/SakuyaStopWatch.png`
- 16×16 indexed PNG
- SHA-256:
  `ac6144bc483951782cbcf94cdc3339f07fbc1f49507a323264ee27a5f922e285`

### StopWatch controller
- path: `assets/thkaguyamod/textures/SakuyaStopWatchTexture.png`
- 64×32 indexed PNG
- SHA-256:
  `9c6b567304210c30b67d14dc925d058dc3eb5c961aae8918aee84bb7239955bd`

### Dark field texture
- path: `assets/thkaguyamod/textures/DarkTexture.png`
- 64×32 PNG
- SHA-256:
  `c0b1a2f92f0b3f366cdfcecf212de161eb853fd987d2790bd7d943b4dcde0d05`

Original bytes stay private/local and are imported only after canonical archive/hash verification.

## Dark field presentation

Both Watch and StopWatch renderers contain the same dark field effect.

Render state:
- outer renderer scale 0.3;
- culling disabled;
- depth writes disabled during dark pass;
- depth function LEQUAL;
- blending enabled;
- blend function:
  `ONE_MINUS_DST_COLOR / ZERO`;
- texture: DarkTexture;
- after dark pass, depth writes restored and culling restored.

Field mesh size:
`size = min(ticksExisted * 12, 240)`

Because the whole renderer is scaled by 0.3, the visible maximum mesh scale is correspondingly transformed by that global matrix.

The old renderer calculates an alpha fade after tick 20 but passes constant alpha 1.0 to `renderDark`, so that local alpha variable has no active effect.

`renderDark` builds a spherical/ellipsoidal mesh:
- 18 angular divisions around Z;
- 9 depth/latitude divisions;
- quads between adjacent rings.

Config gate:
`THKaguyaConfig.useTimeStopEffect`.

P4 should preserve the effect as an enabled private-preservation default unless a later config surface is added.

## Controller spin

After the dark pass:
- bind Watch or StopWatch controller texture;
- rotate Y:
  `180 - renderYaw + ticksExisted * 7`;
- render the same four-part clock model.

## P4 implementation boundary

P4 should:
- provide usable Watch and StopWatch items;
- preserve FULL/HALF mode state and glint;
- preserve 20/48 charge durations;
- preserve creative immediate activation;
- preserve survival consumption and Watch return-to-mode-0 behavior;
- render synced P3 controller using exact model/texture transform;
- import canonical item/controller/Dark textures through private SHA-verified overlay tooling.

P4 does not need to implement Murdering Doll or all Sakuya spell cards.
