# Five Difficulties X1 Preservation Port — P4 implementation checkpoint

Date: 2026-10-07

Branch:
`jolly/five-difficulties-1201-port-p4-2026-10-07`

Parent:
`jolly/five-difficulties-1201-port-p3-2026-10-07`

Status: **P4 COMPLETE — Sakuya Watch / StopWatch are player-usable and their canonical controller presentation is Forge-compiled**

## Scope

P4 turns the P3 time-domain machinery into a player-facing X1-preservation path.

Implemented:
- Sakuya Watch item;
- StopWatch item;
- HALF / FULL mode selection;
- X1 charge and activation semantics;
- survival consume + Watch return lifecycle;
- disposable StopWatch lifecycle;
- synced P3 controller start;
- canonical Watch/StopWatch model and textures through private asset overlay;
- canonical expanding dark time-field visual.

This checkpoint is compile/package validated. It is **not yet a claim of in-game visual/runtime parity**.

## Canonical Watch item behavior

### Mode state

Modern implementation stores the old metadata-equivalent state in item NBT:

- mode 0 = HALF;
- mode 1 = FULL STOP.

Mode 1 glints, matching the old metadata-1 item.

Sneak-right-click toggles the mode when the player's age parity matches the old debounce behavior.

### Charge

- HALF: 20 ticks;
- FULL STOP: 48 ticks;
- use animation: BOW.

Creative:
- non-sneak use activates immediately;
- HALF / FULL are persistent controllers;
- item is not consumed.

Survival:
- requires food >0;
- requires full charge;
- HALF starts the exact-static 161-processing-update limited field;
- FULL starts the exact-static 101-processing-update limited field;
- item is consumed only when controller creation succeeds.

## Watch return behavior

A consumed survival Watch returns when the limited Watch controller finishes.

The canonical X1 overload returns a fresh Watch without preserving metadata.

P4 therefore returns:
- one fresh Sakuya Watch;
- default mode 0 = HALF.

Return target:
1. source player's inventory when possible;
2. otherwise an ItemEntity at the controller location.

Persistent creative Watch:
- item was never consumed;
- no returned duplicate.

Spell-card controller:
- no Watch return.

## StopWatch

P4 StopWatch:
- activates immediately;
- FULL STOP;
- exact-static 40 processing updates;
- non-creative consumes one item;
- creative does not consume;
- never returns itself.

The duplicate-precheck preserves the X1 distinction:
- Watch item precheck blocks another Watch controller inside the 20-block AABB;
- StopWatch item precheck blocks either Watch or StopWatch controller in that AABB.

Controller overlap still resolves wider 40-block conflicts.

## Canonical controller presentation

### Model

P4 reconstructs the X1 `ModelPrivateSquare` as a modern model layer.

Four parts:
- watchBase;
- watchCenter;
- watchHandle;
- watchCover.

The original 64×32 UV layout and the watch-cover π/6 hinge are preserved.

### Transform

Controller renderer:
- global scale 0.3;
- Y rotation `180 - renderYaw + age*7`;
- Watch / StopWatch select different controller textures.

### Dark field

The X1 dark effect is recreated from the old renderer geometry:
- dark texture;
- 18 angular subdivisions;
- 9 latitude/depth subdivisions;
- size `min(age*12,240)`;
- blend `ONE_MINUS_DST_COLOR / ZERO`;
- depth writes disabled during the pass;
- culling disabled during the pass.

The old source's unused alpha-fade variable is not promoted into a new effect.

## Canonical private assets

The public TECH-HUB repository still contains **no original X1 PNG bytes**.

`tools/import-private-x1-assets.py` now imports and verifies:

- Sakuya Watch item icon
  - SHA-256 `589e080353f2f1d56ec6af6547bc3cfbb3802de89e7797c03a2251083e8d0c8e`
- Watch controller texture
  - SHA-256 `b55d8af1138f2b7f5e3841afe7d5aecff78d57122f57ecb7a29af1036f76ff30`
- StopWatch item icon
  - SHA-256 `ac6144bc483951782cbcf94cdc3339f07fbc1f49507a323264ee27a5f922e285`
- StopWatch controller texture
  - SHA-256 `9c6b567304210c30b67d14dc925d058dc3eb5c961aae8918aee84bb7239955bd`
- DarkTexture
  - SHA-256 `c0b1a2f92f0b3f366cdfcecf212de161eb853fd987d2790bd7d943b4dcde0d05`

The importer accepts only the verified canonical outer bundle or canonical X1 inner archive and checks each copied asset hash.

## Registration / UX

Registered:
- `five_difficulties_port:sakuya_watch`;
- `five_difficulties_port:sakuya_stopwatch`.

Modern creative placement:
- Tools & Utilities.

JA/EN item names and generated item-model JSONs are present.

## Verification

Latest P4 GitHub Actions validation:

- run **37531317629**
- head `d9e0bbdf3f2fd7576e43b97b88112127a8aa77ff`
- conclusion: **SUCCESS**

Verified:
- all pure Java preservation regressions: PASS;
- exact official Forge 1.20.1-47.4.6 MDK SHA verification: PASS;
- Mixin-enabled `compileJava jar`: PASS;
- Mixin manifest/config/refmap packaging checks: PASS;
- controller model/renderer and both usable items compile in the real MDK;
- bounded evidence artifact retention: PASS.

## Known runtime-unverified surfaces

Still not claimed:
- Minecraft client launch with the private PNG overlay;
- actual right-click/charge/watch-return behavior in a running world;
- dark-field visual parity screenshots;
- two-player multiplayer stop behavior;
- arbitrary modded-entity compatibility;
- passenger/vehicle edge behavior under live networking;
- same-owner Murdering Doll exception in an actual spell card;
- Sakuya knife placement/release workflow;
- X1 sound parity beyond current click placeholder.

## Next gate — P5 bounded runtime smoke

Before porting more Five Difficulties content, P5 should prove the current vertical slice in a real Minecraft process:

1. assemble a private runtime resources overlay from the canonical X1 archive;
2. start a bounded Forge 1.20.1 server/client or GameTest-compatible runtime;
3. verify mod + Mixins load without startup errors;
4. verify Homing Amulet normal/focus entity spawn;
5. verify Watch HALF / FULL activation and controller expiry;
6. verify StopWatch activation;
7. verify frozen mob/projectile vs source-player exception;
8. capture screenshots / logs for controller dark field and item models if a client run is available.

Only after that runtime gate should the port expand to Murdering Doll, Sakuya knives, Master Spark or the full spell-card catalog.
