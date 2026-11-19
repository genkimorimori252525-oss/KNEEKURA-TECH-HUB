# Domain Expansion clash and simultaneous cut-in

## Lifecycle

DomainexpantionMobEffect is the lifecycle hook.

- effect added -> Domain_expansion_startProcedure
- every active tick -> DomainexpansiontickupdateProcedure
- effect removed -> Domain_effect_releaseProcedure

Domain start initializes:
- DOMAINHP = 100
- DOMAINBATTLEAMOUNT = 0
- DOMAINTICK = 0
- Domain_battle_lose = false
- barrier_damage = 0

It scans other living Domain Expansion users in an AABB expanded by 50 blocks and stores a primary opponent UUID in Domain_battle_uuid.

## Dedicated Domain HP

Domain durability is independent from ordinary health.

### Damage from normal combat

Attackhit1Procedure calls DomainbattleProcedure(target, damage_amount) when the target owns Domain Expansion.

Resolution:
- damage >= 120 -> remove Domain Expansion immediately
- player owner -> DOMAINHP -= damage / 8
- non-player owner -> DOMAINHP -= damage / 14

The domain/barrier layer is integrated into the ordinary combat pipeline.

### Active domain-vs-domain pressure

During a clash the tick procedure:
- subtracts opponent Domain Expansion amplifier + 1
- adds own Domain Expansion amplifier + 1
- caps own DOMAINHP at 100

Observed elimination conditions include:
- current DOMAINHP <= 2 -> remove current domain
- opponent DOMAINHP <= 10 -> remove opponent domain
- opponent HP exceeds current HP by 50 or more -> remove weaker current domain

The amplifier acts as a continuous refinement/strength input rather than a one-shot winner lookup.

## Winner/loser handoff

On effect release, Domain_effect_releaseProcedure:
- marks the ending owner Domain_battle_lose=true
- resets nearby contest/tick state
- may set the surviving user Domain_battle_win=true
- can retain the winning domain instead of ordinary teardown
- otherwise schedules progressive barrier cleanup
- applies post-domain cooldown/burnout logic

## Health-based domain failure

DomainbrokenProcedure removes Domain Expansion when the owner is dead or falls to about 20% max health or lower.

## Sure-hit scan performance

DomainexpansionhitProcedure registers a server-side TickHandler.

It:
1. expands evaluated radius over 20 ticks,
2. processes only the shell between previous/current radii,
3. uses coarse X/Z and Y stride in the inner region,
4. records visited BlockPos values,
5. calls DomainexpansionhitattackProcedure on selected samples.

DomaindestructionProcedure uses a similar scheduled-shell strategy for barrier teardown.

This is a strong reusable pattern for large spherical AoE.

## Simultaneous-domain cut-in

DomainCutinOverlay is client-only.

### Trigger window

A candidate has Domain Expansion and is in the early DOMAINTICK window, roughly the first 50 ticks.

The local player scans a 50-block AABB for nearby qualifying living entities.

### Participant lock

At activation:
- local user is added first,
- nearby users are sorted by distance,
- targets are locked,
- newcomers may be appended while active,
- visual rendering is capped at 3 participants.

This avoids panel order changing every frame.

### Two-way layout

For 2 users:
- diagonal depth masks
- separate procedural backgrounds
- live 3D participant models
- black/white diagonal divider bands

### Three-way layout

For 3 users:
- three panel masks
- three background palettes
- three live entity models

### Procedural background

Each panel draws a black base plus about 1,200 deterministic time-driven line elements. Panel palettes are pink/red, cyan and lime. A stable seed preserves visual identity while time drives animation.

### Depth-buffer masking

The overlay uses depth as a stencil-like panel mask:
- clear depth
- depth function ALWAYS
- disable color writes
- draw mask at chosen Z
- restore color writes
- render background/entity with LEQUAL

This permits arbitrary split shapes without requiring a stencil attachment.

### Live entity rendering

The normal EntityRenderDispatcher renders the actual LivingEntity in GUI space. Body/head rotations are temporarily normalized and then restored.

The cut-in therefore supports skins/custom models without per-character portrait assets.

## Critical limitation: three-way presentation != proven symmetric three-way solver

The cinematic supports up to three users.

However, battle state contains a singular Domain_battle_uuid and clash logic remains opponent/pair oriented with nearby scans. Static evidence does not establish one centralized fully symmetric N-way contest object.

Record separately:
- presentation cardinality: 2/3 supported
- simulation semantics: pair/opponent oriented, nearby multi-user interactions possible
