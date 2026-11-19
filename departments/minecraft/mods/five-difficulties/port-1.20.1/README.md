# Five Difficulties X1 Preservation Port — Minecraft 1.20.1 Forge

Status: **P15 complete — spell cards, danmaku-weapon items, bonus items, config and the danmaku / laser crafting tables on top of every shot / laser form; see PORT-ROADMAP.md**.

Target:
- Minecraft 1.20.1
- Forge 47.4.6
- Java 17
- private preservation/research use

Fidelity oracle:
- 五つの難題MOD+ ver2.90.1.X1-1.7.10
- Roundabout is only a donor/reference for modern time-stop machinery.

## Build boundary

This directory intentionally keeps the implementation source tree but does not vendor the Forge MDK or Gradle wrapper binaries.

CI/validation overlays:

`port-1.20.1/src`

onto the exact official Forge 1.20.1-47.4.6 MDK used elsewhere by KNEEKURA-TECH-HUB.

This follows the existing Hub validation convention and keeps third-party/build artifacts out of Git history.

## Source split

`src/main/java/dev/kneekura/fivedifficulties/core/**`

Pure Java:
- no Minecraft or Forge imports;
- deterministic legacy shot/laser/pattern contracts;
- Sakuya time-stop policy/state;
- runnable with plain Java 17 regression tests.

`src/main/java/dev/kneekura/fivedifficulties/forge/**`

Forge 1.20.1 boundary:
- @Mod bootstrap;
- DeferredRegister boundary;
- network channel boundary;
- Minecraft Entity/ServerLevel adapters for the pure time-stop core.

Current port still deliberately defers broad content expansion: the 35 spell cards, Master Spark, generalized THShot/laser runtime, most X1 recipes/mobs/items, and all bullet batching remain later gates.

## Validation order

1. compile/run pure Java core regression;
2. compile/package source against exact Forge MDK;
3. only then add real X1 oracle-backed content.

No Minecraft runtime claim is made by a compile-only pass.


## P1 evidence contracts

P1 adds a strict evidence bridge to the earlier exact X1 analysis (PR #93):

- canonical core artifact SHA-256 `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`;
- red Homing Amulet normal/focus behavior contract;
- Sakuya Watch/StopWatch mode/range/duration contract;
- explicit unresolved fields/categories so missing raw/runtime evidence is never guessed.

These contracts are pure Java and do not yet make the original textures/items/renderers available in-game.


## P2 live preservation path

Canonical X1 was reacquired byte-for-byte and the first live 1.20.1 preservation path is now implemented:

- red Homing Amulet item;
- exact normal/focus fan geometry;
- exact static homing contract;
- X1-style logical collision sweep;
- live EntityType/projectile;
- two-pass legacy-style renderer;
- private SHA-verified original texture overlay.

See:
- `P2-CANONICAL-X1-REACQUISITION.md`
- `P2-HOMING-AMULET-EXACT.md`
- `IMPLEMENTATION-CHECKPOINT-P2.md`

Latest validated Forge compile: GitHub Actions run `37521984099` — SUCCESS.

Next preservation gate is Sakuya time-stop parity, not mass content expansion.


## P3 Sakuya time-domain machinery

Canonical X1 Watch/StopWatch source was re-read directly.

P3 now provides:
- exact X1 40-block AABB field policy;
- source/item-frame/painting/mount exclusions;
- two-tick new-entity grace;
- FULL_STOP and deterministic HALF_SPEED modes;
- synced transient controller entity;
- per-Level controller index;
- ServerLevel entity/passenger tick interception;
- ServerPlayer simulation/input/movement interception;
- ClientLevel tick cancellation;
- same-owner movable-spell callback boundary;
- Mixin packaging checks in exact Forge 47.4.6 CI.

X1 does **not** freeze blocks, fluids, BlockEntities, particles, animated textures, chunks or world day time, so those Roundabout capabilities stay disabled.

Latest validated P3 run: `37527522708` — SUCCESS.

See:
- `P3-SAKUYA-TIMESTOP-EXACT.md`
- `IMPLEMENTATION-CHECKPOINT-P3.md`

Next gate: usable Sakuya Watch/StopWatch items plus bounded Minecraft runtime verification.


## P4 usable Sakuya Watch / StopWatch

P4 connects the P3 time-domain machinery to real player items.

Implemented:
- mode-0 HALF / mode-1 FULL Sakuya Watch state;
- X1 20/48-tick charge behavior;
- creative immediate persistent activation;
- survival limited activation and item consumption;
- fresh mode-0 Watch return after limited Watch finishes;
- immediate disposable StopWatch;
- exact four-part Watch controller model;
- X1 +7°/tick controller spin;
- expanding dark-field mesh and legacy blend contract;
- SHA-verified private asset overlay for Watch / StopWatch item and controller textures.

Latest validated P4 compile/package: GitHub Actions run `37531317629` — SUCCESS.

See:
- `P4-SAKUYA-WATCH-VISUAL-ITEM-EXACT.md`
- `IMPLEMENTATION-CHECKPOINT-P4.md`

Next gate is bounded **runtime** verification of the current Homing + Sakuya vertical slice before broader content expansion.


## P5 bounded dedicated-server runtime

The preservation slice now has a real Minecraft runtime receipt, not only a compile receipt.

Latest successful P5 run:
- GitHub Actions `37533730730`;
- head `dac041fab79744f18fddd54e6d37db8c286920c1`;
- dedicated server reached `Done (1.927s)!`;
- runtime marker:
  `FIVE_DIFFICULTIES_P5_RUNTIME_SMOKE_PASS serverVersion=1.20.1 dedicated=true`;
- final verdict:
  `P5_DEDICATED_SERVER_RUNTIME_PASS`.

The runtime self-check verifies actual Forge registry objects/entity factories plus representative X1 FULL/HALF/source/new-entity-grace policy after server startup.

P5 also repaired two harness/resource defects:
- invalid assumption that `EntityType#getBaseClass()` exposes the concrete entity class;
- malformed language JSON caused by a literal trailing `\\n`.

See:
- `IMPLEMENTATION-CHECKPOINT-P5.md`

The next gate is **world-mutating server-side runtime testing** of Homing movement/hits and Sakuya FULL/HALF behavior. Client rendering parity remains separate.


## P6 world-mutating runtime scenario

P6 upgrades the current vertical slice from startup-only runtime evidence to actual world behavior.

Latest hardened run:
- GitHub Actions `37535774768`;
- head `f4a570b014ca7dcad1e324c7cc535c3e5274c150`;
- SUCCESS.

Real-server receipts:
- FULL_STOP: target tick count remained 4 → 4 during the bounded freeze window;
- HALF_SPEED: target advanced by 3 ticks in the bounded half-rate window;
- red Homing Amulet: live projectile hit a 20-HP target for the canonical 5 damage (20 → 15) after 11 scenario ticks;
- final marker: `P6_WORLD_RUNTIME_PASS`.

See:
- `IMPLEMENTATION-CHECKPOINT-P6.md`

The next gate is **client-integrated visual/runtime parity** with the private canonical X1 texture overlay, followed by connected-client item interaction testing.


## P7 client visual evidence

The inherited P7 GUI smoke printed PASS while its frame was blank for the Homing
primitive and the dark field. P7 now adds an in-world client smoke with pixel
assertions; live amulets render as flat X1 sprites and the Watch field colour-inverts
the scene as in X1.

See `IMPLEMENTATION-CHECKPOINT-P7.md`.

Local client runs (need the private overlay, so not in CI):

    FIVE_DIFFICULTIES_P7_WORLD_SMOKE=1 ./gradlew runClient
    FIVE_DIFFICULTIES_P7_CLIENT_SMOKE=1 ./gradlew runClient

P8 followed: see below.


## P8 generic THShot backend (Phase A)

One entity per legacy shot, literal X1 numbers: `X1ShotMotion` (pure movement kernel),
`X1ShotPatterns` (all six THShotLib emission helpers), `THShotEntity` (X1 hit/impact/damage),
`THShotRenderer` (normal sprite forms + delay light) and six `ItemTHShot` items with X1 NBT.

Live positions match the pure kernel exactly; end time, hit damage and all six item patterns
pass on a dedicated server; the shot grid and item icons were checked in a real client.

See `IMPLEMENTATION-CHECKPOINT-P8.md`.

P9 followed: see below.



## P9 all shot forms and special shots

Every RenderTHShot form (incl. the silver-knife model), the X1 special shots (homing, diffusion,
fall, bound, fire, explosion, wind), all 19 shot items, and the Homing Amulet item rewired to the
literal X1 THShot amulets plus its Diffusion variant.

**Correction to P2:** X1 ItemHomingAmulet fires EntityTHShot amulets, not EntityHomingAmulet
(which belongs to the Houtou item). See `IMPLEMENTATION-CHECKPOINT-P9.md`.

Next gate: lasers (EntityTHLaser / THSetLaser) and the ISpecialShot registry, then spell cards.


## P10 lasers

Laser A / B entities, every laser emitter, the laser renderer (normal, Gungnir, Laevateinn, Master
Spark beam), the three laser items and the special-shot registry. See
`IMPLEMENTATION-CHECKPOINT-P10.md` and `PORT-ROADMAP.md`.


## P11 spell cards

Spell-card declaration (level cost, look-ray target, enemy-danmaku clear), the card entity, its
magic circle, the shot material bonus, one item per card and 30 of the 35 X1 cards. The other five
need their own entities (P12). See `IMPLEMENTATION-CHECKPOINT-P11.md` and `PORT-ROADMAP.md`.


## P12 spell-card entities

The five cards that spawn their own entities: Musou Fuuin, Master Spark (Mini Hakkero), Satuzin Doll
(spell-card time stop), Hikouchuu Nest (gaps) and Fafrotskies (nuclear shot, Hanabeeper). All 35 X1
cards are registered. See `IMPLEMENTATION-CHECKPOINT-P12.md` and `PORT-ROADMAP.md`.


## P13 danmaku-weapon items

Mini Hakkero (explosive Master Spark, 32 fire charges), Nuclear Control Rod (charge, fire, recoil) and
Dragon Neck Jewel (thrown, bursts into lasers and lights). See `IMPLEMENTATION-CHECKPOINT-P13.md`.


## P14 bonus items and config

Power / point / bomb / extend items and their dropped bonus entity, player power (shot damage), the
extend that saves a dying player, bombs paying for spell cards, and X1's config. See
`IMPLEMENTATION-CHECKPOINT-P14.md`.


## P15 crafting tables

The danmaku and laser crafting tables (block, menu, screen) with X1's arithmetic as a tested pure core.
See `IMPLEMENTATION-CHECKPOINT-P15.md`.
